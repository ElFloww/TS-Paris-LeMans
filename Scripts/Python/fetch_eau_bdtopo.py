"""Cours d'eau et points d'eau le long de V1 (phase 1 Nogent-le-Rotrou - Le Mans), IGN BD TOPO via WFS Geoplateforme.
Sorties :
  GeographicData/Processed/layers/eau.json               {troncons, surfaces, details}
  GeographicData/Processed/layers/eau_franchissements.json  liste de franchissements V1/V2
Cache brut : GeographicData/Raw/bdtopo_hydro/ (une case 0,02 deg par couche, non retelechargee si presente).
Source : BD TOPO (IGN) couches troncon_hydrographique, surface_hydrographique, detail_hydrographique.
Distances en Lambert-93 (EPSG:2154) ; x,z locaux via tsc_coords.lonlat_to_xz.
"""
import json, math, os, sys, time, urllib.request
from collections import Counter
from pyproj import Transformer
from shapely import force_2d
from shapely.geometry import shape, mapping, LineString, Point, MultiPoint, GeometryCollection
from shapely.ops import transform, unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import tsc_coords as C

RAW = os.path.join(ROOT, "GeographicData", "Raw"); HYD = os.path.join(RAW, "bdtopo_hydro")
LAY = os.path.join(ROOT, "GeographicData", "Processed", "layers")
os.makedirs(HYD, exist_ok=True); os.makedirs(LAY, exist_ok=True)
UA = "TSC-route-builder/1.0"
WFS = ("https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:{layer}"
       "&OUTPUTFORMAT=application/json&COUNT=1000&STARTINDEX={start}&BBOX={b0},{a0},{b1},{a1},EPSG:4326")
LAYERS = ["troncon_hydrographique", "surface_hydrographique", "detail_hydrographique"]
CELL = 0.02; MARGE = 0.006; RAYON = 300.0; RAYON_SURF_V1 = 100.0; RAYON_PONT = 30.0
PK_N, PK_LM = 148.113, 210.980          # PK officiels gares Nogent-le-Rotrou et Le Mans (liste-des-gares)

L93 = Transformer.from_crs(4326, 2154, always_xy=True)
L93_INV = Transformer.from_crs(2154, 4326, always_xy=True)


def to93(g):
    return transform(lambda xs, ys: L93.transform(xs, ys), force_2d(g))


def lonlat_to_xz_arr(xs, ys):
    out = [C.lonlat_to_xz(x, y) for x, y in zip(xs, ys)]
    return [o[0] for o in out], [o[1] for o in out]


def get_json(url):
    time.sleep(0.2)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def fetch_cell(layer, lon0, lat0):
    path = os.path.join(HYD, f"{layer}_{lon0:.2f}_{lat0:.2f}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))["features"]
    feats, start = [], 0
    while True:
        url = WFS.format(layer=layer, start=start, b0=round(lon0 - MARGE, 4), a0=round(lat0 - MARGE, 4),
                         b1=round(lon0 + CELL + MARGE, 4), a1=round(lat0 + CELL + MARGE, 4))
        got = get_json(url)["features"]
        feats += got
        if len(got) < 1000:
            break
        start += 1000
    json.dump({"layer": layer, "cell": [lon0, lat0], "url_pattern": WFS, "features": feats},
              open(path, "w", encoding="utf-8"))
    return feats


def pick(p, *keys):
    for k in keys:
        if p.get(k) not in (None, ""):
            return p[k]
    return None


def pts_of(g):
    """Points d'une intersection (les extremites si chevauchement lineaire)."""
    if g.is_empty:
        return []
    if isinstance(g, Point):
        return [g]
    if isinstance(g, MultiPoint):
        return list(g.geoms)
    if isinstance(g, LineString):
        return [Point(g.coords[0]), Point(g.coords[-1])]
    if isinstance(g, GeometryCollection) or hasattr(g, "geoms"):
        out = []
        for s in g.geoms:
            out += pts_of(s)
        return out
    return []


def main():
    V = json.load(open(os.path.join(RAW, "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"),
                       encoding="utf-8"))
    def voie(code):
        c = [v for v in V if v["code_voie"] == code][0]["geo_shape"]["geometry"]["coordinates"]
        return [p for p in c if 0.17 < p[0] < 0.835 and 47.99 < p[1] < 48.34]
    pts1, pts2 = voie("420000-1-V1"), voie("420000-1-V2")
    V1 = to93(LineString(pts1)); V2 = to93(LineString(pts2))
    gares = {g["libelle"]: g for g in json.load(open(os.path.join(RAW, "sncf", "liste-des-gares_420000.json"),
                                                     encoding="utf-8"))}
    s_n = V1.project(Point(gares["Nogent-le-Rotrou"]["x_l93"], gares["Nogent-le-Rotrou"]["y_l93"]))
    s_lm = V1.project(Point(gares["Le Mans"]["x_l93"], gares["Le Mans"]["y_l93"]))
    echelle = (PK_LM - PK_N) / ((s_lm - s_n) / 1000.0)
    print(f"ancrage PK: Nogent s={s_n:.1f} m, Le Mans s={s_lm:.1f} m, echelle={echelle:.5f} km/km")
    print(f"ecart station-V1: Nogent {V1.distance(Point(gares['Nogent-le-Rotrou']['x_l93'], gares['Nogent-le-Rotrou']['y_l93'])):.1f} m, "
          f"Le Mans {V1.distance(Point(gares['Le Mans']['x_l93'], gares['Le Mans']['y_l93'])):.1f} m")

    cells = sorted({(math.floor(lon / CELL), math.floor(lat / CELL)) for lon, lat in pts1})
    print(f"cases: {len(cells)}")
    brut = {l: {} for l in LAYERS}
    for i, j in cells:
        for layer in LAYERS:
            for f in fetch_cell(layer, round(i * CELL, 2), round(j * CELL, 2)):
                brut[layer].setdefault(f["id"], f)
    for l in LAYERS:
        print(f"{l}: {len(brut[l])} entites uniques recues")
        keys = sorted({k for f in brut[l].values() for k in f["properties"]})
        print(f"  attributs: {keys}")

    def rec(layer, f):
        p = f["properties"]; g = force_2d(shape(f["geometry"])); g93 = to93(g)
        d = {"id": f["id"], "cleabs": p.get("cleabs"),
             "nom": pick(p, "cpx_toponyme_de_cours_d_eau", "cpx_toponyme_de_plan_d_eau", "toponyme"),
             "nature": p.get("nature"), "persistance": p.get("persistance"),
             "largeur": p.get("classe_de_largeur"),
             "etat": p.get("etat_de_l_objet"), "sens_ecoulement": pick(p, "sens_de_l_ecoulement", "sens_ecoulement"),
             "distance_V1_m": round(g93.distance(V1), 1)}
        d["geometrie_lonlat"] = mapping(g)
        d["geometrie_xz"] = mapping(transform(lonlat_to_xz_arr, g))
        return d, g93

    troncons, surfaces, details = [], [], []
    geo_troncon, geo_surface = {}, {}
    for f in brut["troncon_hydrographique"].values():
        d, g93 = rec("troncon_hydrographique", f)
        if d["distance_V1_m"] <= RAYON:
            p = f["properties"]
            d["busage_indice"] = (d["nature"] in ("Conduit buse", "Ecoulement canalisé") or "canalis" in str(d["nature"]).lower()) or ("tunnel" in str(p.get("position_par_rapport_au_sol") or "").lower())
            troncons.append(d); geo_troncon[d["id"]] = g93
    for f in brut["surface_hydrographique"].values():
        d, g93 = rec("surface_hydrographique", f)
        if d["distance_V1_m"] <= RAYON:
            d["aire_m2"] = round(g93.area, 1)
            surfaces.append(d); geo_surface[d["id"]] = g93
    for f in brut["detail_hydrographique"].values():
        d, g93 = rec("detail_hydrographique", f)
        if d["distance_V1_m"] <= RAYON:
            p = f["properties"]
            d["nature_detaillee"] = p.get("nature_detaillee"); d["importance"] = p.get("importance")
            details.append(d)
    json.dump({"troncons": troncons, "surfaces": surfaces, "details": details},
              open(os.path.join(LAY, "eau.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"eau.json: {len(troncons)} troncons, {len(surfaces)} surfaces, {len(details)} details (<= {RAYON:.0f} m de V1)")

    # Ponts ferroviaires : voies BD TOPO position_par_rapport_au_sol == '1'
    bt = json.load(open(os.path.join(RAW, "bdtopo_voies_phase1.json"), encoding="utf-8"))
    sur_pont = [to93(shape(f["geometry"])) for f in bt["features"]
                if str(f["properties"].get("position_par_rapport_au_sol")) == "1"]
    pont_union = unary_union(sur_pont) if sur_pont else None
    print(f"voies BD TOPO sur pont (position 1): {len(sur_pont)}")

    franch = []
    for kind, recs, geos in (("troncon", troncons, geo_troncon), ("surface", surfaces, geo_surface)):
        for r in recs:
            g93 = geos[r["id"]]
            src = g93 if kind == "troncon" else g93.boundary
            for voie_nom, vline in (("V1", V1), ("V2", V2)):
                for k, pt in enumerate(pts_of(src.intersection(vline))):
                    lon, lat = L93_INV.transform(pt.x, pt.y)
                    x, z = C.lonlat_to_xz(lon, lat)
                    pont = pont_union is not None and pont_union.distance(pt) < RAYON_PONT
                    if pont:
                        cls = "pont_rail"
                    elif kind == "troncon" and r["busage_indice"]:
                        cls = "busé"
                    else:
                        cls = "busé_ou_inconnu"
                    franch.append({"id": f"{r['id']}:{voie_nom}:{k}", "lon": round(lon, 7), "lat": round(lat, 7),
                                   "x": round(x, 2), "z": round(z, 2), "cours_d_eau": r["nom"], "nom": r["nom"],
                                   "voie": voie_nom,
                                   "pk_approx": round(PK_N + (V1.project(pt) - s_n) / 1000.0 * echelle, 3),
                                   "classification": cls})
    json.dump(franch, open(os.path.join(LAY, "eau_franchissements.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"franchissements: {len(franch)}  " + str(dict(Counter(f['classification'] for f in franch))))

    # Controle : chaque franchissement doit etre sur V1 ou V2 (tolerance 1 m)
    assert all(min(V1.distance(Point(*to93(Point(f['lon'], f['lat'])).coords[0])),
                   V2.distance(Point(*to93(Point(f['lon'], f['lat'])).coords[0]))) < 1.0 for f in franch[:200])

    grandes = sorted(((s["aire_m2"], s["nom"], s["distance_V1_m"]) for s in surfaces
                      if s["distance_V1_m"] <= RAYON_SURF_V1), reverse=True)[:10]
    print("10 plus grandes surfaces <= 100 m de V1 (aire m2, nom, distance m):")
    for a, n, dd in grandes:
        print(f"  {a}, {n}, {dd}")
    print("noms troncons (occurrences):", Counter(t["nom"] for t in troncons).most_common(25))
    print("noms surfaces (occurrences):", Counter(s["nom"] for s in surfaces).most_common(25))
    print("natures troncons:", dict(Counter(t["nature"] for t in troncons)))
    print("natures details:", dict(Counter(d["nature"] for d in details)))


if __name__ == "__main__":
    main()
