#!/usr/bin/env python3
"""Semis d'arbres et de buissons sur les zones de vegetation BD TOPO proches de V1/V2.

Usage : python Scripts/Python/scatter_vegetation.py [--pk 147.1 150.0] [--seed 42]

Sorties :
  Route/Configuration/objects_decor.json
  Tests/Phase1/previews/veg_candidates.txt
  Tests/Phase1/previews/veg_semis.png
Distances en Lambert-93 (EPSG:2154), sorties en WGS84 (lon/lat).
PK = distance projetee sur V1 complete (EPSG:2154) / 1000 + 1,186.
"""
import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import LineString, shape
from shapely.ops import linemerge, substring

ROOT = Path(__file__).resolve().parents[2]
VEG = ROOT / "GeographicData/Processed/layers/vegetation.json"
BAT = ROOT / "GeographicData/Processed/layers/batiments.json"
ROUTES = ROOT / "GeographicData/Processed/layers/routes_150m.json"
EAU = ROOT / "GeographicData/Processed/layers/eau.json"
INV = ROOT / "Assets/Inventory/blueprints_inventory.json"
SNCF = ROOT / "GeographicData/Raw/sncf/fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"
OUT_JSON = ROOT / "Route/Configuration/objects_decor.json"
OUT_CAND = ROOT / "Tests/Phase1/previews/veg_candidates.txt"
OUT_PNG = ROOT / "Tests/Phase1/previews/veg_semis.png"

PK_OFFSET = 1.186
RAYON_ZONE = 100.0        # zone retenue si une partie est a moins de 100 m de V1 ou V2
CAP = 3500                # cap total d'objets pour la plage
BAT_MIN = 3.0             # distance mini a un batiment
EAU_MIN = 4.0             # distance mini a un troncon hydrographique
ROUTE_MARGE = 3.0         # seuil route = largeur/2 + marge
ROUTE_INCONNUE = 5.0      # seuil si largeur inconnue
CLEAR = 6.0

# nature : (distance mini de semis en m, part d'arbres ; le reste = buissons)
PARAMS = {
    "Haie": (6.0, 0.30),
    "Lande ligneuse": (7.0, 0.0),
    "Bois": (9.0, 0.85),
    "Forêt fermée de feuillus": (9.0, 0.85),
    "Forêt fermée mixte": (9.0, 0.85),
    "Forêt fermée de conifères": (9.0, 0.85),  # traitee comme feuillus (pas de conifere retenu)
    "Forêt ouverte": (9.0, 0.85),
    "Peupleraie": (9.0, 0.85),
}

# (provider, product, chemin inventaire)
ARBRES = [
    ("DTG", "LGVMedSouth", "Scenery/Vegetation/Tree_Fieldmaple_01_Mid.bin"),
    ("DTG", "LGVMedSouth", "Scenery/Vegetation/Tree_Poplar_01_Mid.bin"),
    ("DTG", "LGVMedSouth", "Scenery/Vegetation/Tree_N_Coppice.bin"),
    ("DTG", "LGVMedSouth", "Scenery/Vegetation/NYNH_Tree_HybridPlane_01.bin"),
    ("DTG", "Academy", "Scenery/Vegetation/Black Ash_tree.bin"),
]
BUISSONS = [
    ("DTG", "LGVMedSouth", "Scenery/Vegetation/Bush_Hawthorn_mid_04.bin"),
    ("DTG", "LGVMedSouth", "Scenery/Vegetation/Bush_Misc01.bin"),
    ("DTG", "Academy", "Scenery/Vegetation/SH_Bush02.bin"),
]

RAISON_CHOIX = """CHOIX RETENUS (etape 1)
Arbres feuillus (5) :
  - Tree_Fieldmaple_01_Mid (LGVMedSouth) : erable champetre, feuillu tempere europeen.
  - Tree_Poplar_01_Mid (LGVMedSouth) : peuplier, feuillu (coherent avec les peupleraies).
  - Tree_N_Coppice (LGVMedSouth) : taillis, feuillu ; espece non precisee dans le nom.
  - NYNH_Tree_HybridPlane_01 (LGVMedSouth) : platane hybride, feuillu ; modele de parc, plausibilite rurale faible.
  - Black Ash_tree (Academy) : frene, feuillu tempere.
Buissons (3) :
  - Bush_Hawthorn_mid_04 (LGVMedSouth) : aubepine, typique des haies.
  - Bush_Misc01 (LGVMedSouth) : buisson generique ; espece non precisee.
  - SH_Bush02 (Academy) : buisson generique ; espece non precisee.

CE QUI MANQUE / LIMITES
  - Aucun chene, hetre, charme, noisetier, saule ou orme n'est nomme dans les produits DTG/LGVMedSouth, DTG/LGVRhoneAlpes, DTG/Academy : pas de feuillu tempere clairement identifiable au-dela de erable, peuplier, frene, platane.
  - Aucun conifere retenu (demande) : les zones de conifères sont semees avec les feuillus ci-dessus (ecart a la realite a noter).
  - Pas de haie nommee sans regle exclue : gen_hedge_* (RhoneAlpes) sont des modeles procedureraux de groupe, non retenus.
  - Les modeles Tree_Misc_*, 1_Tree a 3_Tree, Shrubs_* et SH_Bush01/03 ont une espece non identifiable : non retenus sauf les deux buissons ci-dessus.
"""

RAISON_ECARTS = """ECARTES
  - Noms evoquant pin, sapin/fir, palmier, cypres, olivier, conifere (ex. Tree_Pine_*, Tree_Fir_*, Fir_Tree*, DP-PineLinemixed*, Jeffrey Pine, Whitebark Pine, Mi_Tree_Pine_*).
  - Imposteurs ou groupes : Near, Far, Grp, group, billboard (ex. HSC_Near_*, Tree_Misc_Near, Tree_Sycamore_Near, Bush_Bramble_near_01, LM_Bush_GorseNear_01, *_Grp_*, Tree_grp*_*).
  - Lignes, bosquets et amas (Line, wood, cluster) : Tree_Misc_large_Line01, Tree_Misc_large_cluster01, Tree_grp3_wood*.
  - Vignes (Vineyard_Trees_*) et modeles a espece non identifiable, voir ci-dessus.
"""


def bp_id(path):
    """Chemin inventaire -> identifiant de blueprint TSC (Scenery\\Vegetation\\X.xml)."""
    assert path.endswith(".bin"), path
    return path[:-4].replace("/", "\\") + ".xml"


TR = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
TR_INV = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)


def vers_l93(geom):
    return shapely.transform(geom, lambda c: np.column_stack(TR.transform(c[:, 0], c[:, 1])))


def geom_ll(obj):
    return shapely.make_valid(shape(obj))


def charger(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ecrire_candidats(inv):
    choisis = set(ARBRES) | set(BUISSONS)
    lignes = ["VEGETATION : CANDIDATS BLUEPRINTS (DTG / LGVMedSouth, LGVRhoneAlpes, Academy)", ""]
    for produit in ("LGVMedSouth", "LGVRhoneAlpes", "Academy"):
        lignes.append(f"== DTG / {produit} ==")
        items = [i for i in inv if i["provider"] == "DTG" and i["product"] == produit
                 and i["categorie"] in ("arbre", "buisson")]
        for it in sorted(items, key=lambda i: (i["categorie"], i["path"])):
            key = ("DTG", produit, it["path"])
            marque = "CHOISI" if key in choisis else "-"
            lignes.append(f"  {it['categorie']:<8} [{marque:<6}] {it['path']}  ->  {bp_id(it['path'])}")
        lignes.append("")
    lignes.append(RAISON_CHOIX)
    lignes.append(RAISON_ECARTS)
    OUT_CAND.write_text("\n".join(lignes), encoding="utf-8")


def echantillon_poisson(poly, rmin, rng):
    """Dart throwing avec distance mini rmin dans le polygone (approximation de Poisson)."""
    minx, miny, maxx, maxy = poly.bounds
    n = int(10 * (maxx - minx) * (maxy - miny) / rmin ** 2) + 10
    cand = np.column_stack([rng.uniform(minx, maxx, n), rng.uniform(miny, maxy, n)])
    cand = cand[shapely.contains_xy(poly, cand[:, 0], cand[:, 1])]
    cell = rmin / math.sqrt(2)
    grille = {}
    acc = []
    r2 = rmin * rmin
    for x, y in cand.tolist():
        cx, cy = math.floor(x / cell), math.floor(y / cell)
        libre = True
        for i in range(cx - 2, cx + 3):
            for j in range(cy - 2, cy + 3):
                for px, py in grille.get((i, j), ()):
                    if (px - x) ** 2 + (py - y) ** 2 < r2:
                        libre = False
                        break
                if not libre:
                    break
            if not libre:
                break
        if libre:
            acc.append((x, y))
            grille.setdefault((cx, cy), []).append((x, y))
    return np.array(acc, dtype=float).reshape(-1, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pk", nargs=2, type=float, default=[147.1, 150.0])
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    pk0, pk1 = args.pk
    assert pk0 < pk1, "plage de PK invalide"

    inv = charger(INV)
    index = {("DTG", i["product"], i["path"]): i["categorie"] for i in inv if i["provider"] == "DTG"}
    for cat, lst in (("arbre", ARBRES), ("buisson", BUISSONS)):
        for bp in lst:
            assert index.get(bp) == cat, f"blueprint absent ou mauvaise categorie : {bp}"
    ecrire_candidats(inv)

    # Voies V1 / V2 (SNCF)
    sncf = charger(SNCF)

    def voie(code):
        m = [x for x in sncf if x.get("code_voie") == code]
        assert len(m) == 1, code
        g = shape(m[0]["geo_shape"]["geometry"])
        if g.geom_type == "MultiLineString":
            g = linemerge(g)
        assert g.geom_type == "LineString", code
        return vers_l93(g)

    V1 = voie("420000-1-V1")
    V2 = voie("420000-1-V2")

    def pk_de(x, y):
        return shapely.line_locate_point(V1, shapely.points(x, y)) / 1000 + PK_OFFSET

    # Zones de vegetation retenues : une partie a moins de 100 m de V1 ou V2
    veg = charger(VEG)["features"]
    zones = []
    for i, f in enumerate(veg):
        assert f["nature"] in PARAMS, f["nature"]
        zones.append((i, f["nature"], vers_l93(geom_ll(f["geometry_lonlat"]))))
    axes = shapely.STRtree([V1, V2])
    paires = axes.query([z[2] for z in zones], predicate="dwithin", distance=RAYON_ZONE)
    selection = set(paires[0].tolist())
    print(f"zones vegetation : {len(zones)} ; a moins de {RAYON_ZONE:g} m de V1/V2 : {len(selection)}")

    # Obstacles
    tree_bat = shapely.STRtree([vers_l93(geom_ll(f["geometry"])) for f in charger(BAT)["features"]])

    buffers_routes = []
    for r in charger(ROUTES):
        ll = np.asarray(r["lonlat"], dtype=float)
        xy = np.column_stack(TR.transform(ll[:, 0], ll[:, 1]))
        try:
            w = float(r["largeur_de_chaussee"])
            seuil = w / 2 + ROUTE_MARGE if math.isfinite(w) else ROUTE_INCONNUE
        except (TypeError, ValueError):
            seuil = ROUTE_INCONNUE
        buffers_routes.append(LineString(xy).buffer(seuil))
    tree_route = shapely.STRtree(buffers_routes)

    eau = charger(EAU)
    tree_surf = shapely.STRtree([vers_l93(geom_ll(s["geometrie_lonlat"])) for s in eau["surfaces"]])
    tree_tron = shapely.STRtree([vers_l93(geom_ll(t["geometrie_lonlat"])) for t in eau["troncons"]])

    # Semis par zone (graine fixe par zone)
    xs, ys, nats = [], [], []
    for i, nat, geom in zones:
        if i not in selection:
            continue
        rmin, _ = PARAMS[nat]
        pts = echantillon_poisson(geom, rmin, np.random.default_rng([args.seed, i]))
        if len(pts) == 0:
            continue
        pk = pk_de(pts[:, 0], pts[:, 1])
        pts = pts[(pk >= pk0) & (pk <= pk1)]
        xs.append(pts[:, 0])
        ys.append(pts[:, 1])
        nats += [nat] * len(pts)
    X = np.concatenate(xs) if xs else np.empty(0)
    Y = np.concatenate(ys) if ys else np.empty(0)
    NAT = np.array(nats, dtype=object)
    print(f"points candidats dans la plage PK {pk0}-{pk1} : {len(X)}")

    # Rejets (une cause par point, dans cet ordre)
    P = shapely.points(X, Y)

    def masque(tree, predicate, dist=None):
        m = np.zeros(len(X), dtype=bool)
        if len(X) == 0 or len(tree.geometries) == 0:
            return m
        p = tree.query(P, predicate=predicate) if dist is None else \
            tree.query(P, predicate=predicate, distance=dist)
        m[p[0]] = True
        return m

    rej_bat = masque(tree_bat, "dwithin", BAT_MIN)
    rej_route = masque(tree_route, "intersects")
    rej_eau = masque(tree_surf, "intersects") | masque(tree_tron, "dwithin", EAU_MIN)
    cause = np.where(rej_bat, "batiment", np.where(rej_route, "route",
                     np.where(rej_eau, "eau", "ok")))
    rejets = Counter(cause.tolist())
    print("rejets :", {k: v for k, v in rejets.items() if k != "ok"}, "; acceptes :", rejets.get("ok", 0))

    ok = np.flatnonzero(cause == "ok")
    if len(ok) > CAP:
        ok = np.sort(np.random.default_rng(args.seed).choice(ok, CAP, replace=False))
        print(f"cap {CAP} applique : echantillon deterministe")
    X, Y, NAT = X[ok], Y[ok], NAT[ok]
    n = len(X)

    # Type, blueprint, cap de direction
    rng = np.random.default_rng([args.seed, 2000000])
    p_arbre = np.array([PARAMS[k][1] for k in NAT], dtype=float)
    est_arbre = rng.random(n) < p_arbre
    ia = rng.integers(len(ARBRES), size=n)
    ib = rng.integers(len(BUISSONS), size=n)
    cap = rng.uniform(0, 360, n)
    lon, lat = TR_INV.transform(X, Y)

    objets = []
    for k in range(n):
        if est_arbre[k]:
            nom, bp = "arbre", ARBRES[ia[k]]
        else:
            nom, bp = "buisson", BUISSONS[ib[k]]
        objets.append({
            "name": nom,
            "blueprint": [bp[0], bp[1], bp_id(bp[2])],
            "lon": round(float(lon[k]), 7),
            "lat": round(float(lat[k]), 7),
            "heading_deg": round(float(cap[k]), 1),
            "clear": CLEAR,
        })
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join(json.dumps(o, ensure_ascii=False) for o in objets) + "\n]\n")

    print("objets :", Counter(o["name"] for o in objets))
    print("par nature :", Counter(NAT.tolist()))
    print("par type et nature :", Counter(zip([o["name"] for o in objets], NAT.tolist())))
    # Controle : paires d'objets a moins de 3 m (zones qui se recouvrent)
    if n:
        pp = shapely.STRtree(P[ok]).query(P[ok], predicate="dwithin", distance=3.0)
        print("paires d'objets a moins de 3 m :", int(np.sum(pp[0] < pp[1])))

    # Apercu
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    d0, d1 = max(0.0, (pk0 - PK_OFFSET) * 1000), (pk1 - PK_OFFSET) * 1000
    band = substring(V1, d0, d1)
    minx, miny, maxx, maxy = band.bounds
    pad = 150
    fig, ax = plt.subplots(figsize=(14, 9), dpi=130)
    segs = []
    for i, _, geom in zones:
        if i in selection:
            polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
            segs += [np.asarray(p.exterior.coords) for p in polys]
    ax.add_collection(LineCollection(segs, colors="gray", linewidths=0.5))
    ax.plot(*band.xy, color="red", lw=1.4, label="V1")
    ax.plot(*V2.xy, color="red", lw=1.0, ls="--", label="V2")
    ax.scatter(X[est_arbre], Y[est_arbre], s=5, c="green", label="arbre")
    ax.scatter(X[~est_arbre], Y[~est_arbre], s=5, c="orange", label="buisson")
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    ax.set_aspect("equal")
    ax.set_title(f"Semis vegetation PK {pk0}-{pk1} (seed {args.seed}) : {n} objets")
    ax.legend(loc="upper right")
    fig.savefig(OUT_PNG)
    plt.close(fig)
    print(f"ecrit : {OUT_JSON}")
    print(f"ecrit : {OUT_CAND}")
    print(f"ecrit : {OUT_PNG}")


if __name__ == "__main__":
    main()
