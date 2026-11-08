"""Vegetation BD TOPO (zone_de_vegetation) a moins de 120 m de V1, phase 1 (PK 147,1-212,0).
Sorties :
  GeographicData/Processed/layers/vegetation.json  (polygones lon/lat + x,z, meta source)
  Tests/Phase1/previews/ortho/ortho_<PK>.jpg       (orthophoto IGN 600 m x 600 m)
  Tests/Phase1/previews/ortho/ortho_<PK>_veg.png   (orthophoto + contours vegetation)
Cache WFS/WMS : GeographicData/Raw/bdtopo_vegetation/ et fichiers existants reutilises (idempotent).
Statistiques bande 100 m imprimees sur la sortie standard."""
import json, os, sys, math, time, urllib.request
from pyproj import Transformer
from shapely.geometry import shape, LineString, Point, box
from shapely.ops import transform as sh_transform, unary_union
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPoly, Patch
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import tsc_coords as C

RAW = os.path.join(ROOT, "GeographicData", "Raw")
CACHE = os.path.join(RAW, "bdtopo_vegetation")
OUT_JSON = os.path.join(ROOT, "GeographicData", "Processed", "layers", "vegetation.json")
ORTHO = os.path.join(ROOT, "Tests", "Phase1", "previews", "ortho")
UA = {"User-Agent": "TSC-route-builder/1.0"}
PKS = [150, 160, 170, 180, 195, 205]
R_SEARCH = 120.0     # m, vegetation retenue
R_BAND = 100.0       # m de part et d'autre de V1 pour les statistiques
LAYER = "BDTOPO_V3:zone_de_vegetation"
WFS = ("https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=%s"
       "&OUTPUTFORMAT=application/json&COUNT=1000&STARTINDEX=%d&BBOX=%s,%s,%s,%s,EPSG:4326")
WMS = ("https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=ORTHOIMAGERY.ORTHOPHOTOS"
       "&STYLES=&CRS=EPSG:2154&BBOX=%s,%s,%s,%s&WIDTH=1000&HEIGHT=1000&FORMAT=image/jpeg")
T = Transformer.from_crs(4326, 2154, always_xy=True)     # WGS84 -> Lambert-93
TI = Transformer.from_crs(2154, 4326, always_xy=True)
_last = [0.0]
FAILS = []


def http_get(url):
    """Requete avec User-Agent, >= 0,2 s entre requetes, 3 essais."""
    for k in range(3):
        wait = 0.2 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except Exception as e:
            if k == 2:
                raise
            time.sleep(2 * (k + 1))


def tr(g, t):
    return sh_transform(lambda x, y, z=None: t.transform(x, y), g)


def phase_line(code):
    """Points lon/lat de la voie `code` dans l'emprise phase 1 (filtre du brief)."""
    V = json.load(open(os.path.join(RAW, "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"),
                       encoding="utf-8"))
    c = [v for v in V if v["code_voie"] == code][0]["geo_shape"]["geometry"]["coordinates"]
    idx = [i for i, p in enumerate(c) if 0.17 < p[0] < 0.835 and 47.99 < p[1] < 48.34]
    gaps = sum(1 for a, b in zip(idx, idx[1:]) if b - a > 1)
    return [c[i] for i in idx], gaps


def mapc(c):
    if isinstance(c[0], (list, tuple)):
        return [mapc(x) for x in c]
    x, z = C.lonlat_to_xz(c[0], c[1])
    return [round(x, 2), round(z, 2)]


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(ORTHO, exist_ok=True)

    v1, gaps1 = phase_line("420000-1-V1")
    v2, gaps2 = phase_line("420000-1-V2")
    print(f"V1 : {len(v1)} pts, trous dans la sequence filtree : {gaps1} ; V2 : {len(v2)} pts, trous : {gaps2}")
    L1 = LineString([T.transform(lon, lat) for lon, lat in v1])
    L2 = LineString([T.transform(lon, lat) for lon, lat in v2])
    print(f"Longueur L93 V1 phase 1 : {L1.length:.0f} m (PK 147,1-212,0 = 64 900 m)")

    # ---- cases 0,02 deg le long de V1 (meme methode que fetch_bdtopo_voies.py, sans sous-echantillonnage)
    step = 0.02
    corr = L1.buffer(R_SEARCH + 60, cap_style=2)
    lons = [p[0] for p in v1]; lats = [p[1] for p in v1]
    cells = []
    for i in range(math.floor(min(lons) / step), math.ceil(max(lons) / step)):
        for j in range(math.floor(min(lats) / step), math.ceil(max(lats) / step)):
            if tr(box(i * step, j * step, (i + 1) * step, (j + 1) * step), T).intersects(corr):
                cells.append((i, j))
    print(f"Cases interrogees : {len(cells)}")

    feats = {}
    for i, j in cells:
        fn = os.path.join(CACHE, f"cell_{i}_{j}.json")
        if os.path.exists(fn):
            cf = json.load(open(fn, encoding="utf-8"))["features"]
        else:
            bb = (i * step - 0.0005, j * step - 0.0005, (i + 1) * step + 0.0005, (j + 1) * step + 0.0005)
            cf, start = [], 0
            try:
                while True:
                    body, _ = http_get(WFS % (LAYER, start, "%.6f" % bb[0], "%.6f" % bb[1], "%.6f" % bb[2], "%.6f" % bb[3]))
                    d = json.loads(body.decode("utf-8"))
                    got = d.get("features", [])
                    cf += got
                    if len(got) < 1000 or start > 50000:
                        break
                    start += 1000
            except Exception as e:
                FAILS.append(f"cell {i},{j}: {e}")
                continue
            json.dump({"bbox": bb, "features": cf}, open(fn, "w", encoding="utf-8"))
        for f in cf:
            feats.setdefault(f["id"], f)
    print(f"Entites uniques recues : {len(feats)} ; echecs cases : {len(FAILS)}")

    # ---- garde < 120 m de V1
    kept = []
    for fid, f in feats.items():
        g = tr(shape(f["geometry"]), T)
        if not g.is_valid:
            g = g.buffer(0)
        d = g.distance(L1)
        if d < R_SEARCH:
            kept.append((fid, f, g, d))
    print(f"Polygones < {R_SEARCH:.0f} m de V1 : {len(kept)}")

    out = []
    for fid, f, g, d in sorted(kept, key=lambda k: k[3]):
        ll = shape(f["geometry"]).centroid
        cx, cz = C.lonlat_to_xz(ll.x, ll.y)
        p = f["properties"]
        out.append({
            "id": fid, "cleabs": p.get("cleabs"), "nature": p.get("nature"),
            "date_d_apparition": p.get("date_d_apparition"),
            "precision_planimetrique": p.get("precision_planimetrique"),
            "dist_V1_m": round(d, 1), "aire_m2": round(g.area, 1),
            "x": round(cx, 2), "z": round(cz, 2),
            "geometry_lonlat": f["geometry"],
            "geometry_xz": {"type": f["geometry"]["type"], "coordinates": mapc(f["geometry"]["coordinates"])},
        })
    meta = {
        "description": "Zones de vegetation BD TOPO a moins de 120 m de V1 (phase 1 Nogent-Le Mans)",
        "source": "IGN BD TOPO V3, couche BDTOPO_V3:zone_de_vegetation, WFS Geoplateforme (data.geopf.fr)",
        "licence": "Licence ouverte IGN (Etalab) selon la fiche IGN : a verifier",
        "date_recuperation": "2026-11-08",
        "crs_source": "EPSG:4326 (lon/lat) ; calcul des distances en EPSG:2154",
        "coords_locales": "C.lonlat_to_xz (Scripts/Python/tsc_coords.py), champs x,z",
        "rayon_m": R_SEARCH, "axe": "420000-1-V1 (filtre lon 0.17-0.835, lat 47.99-48.34)",
        "cases_0_02deg": len(cells), "echecs": FAILS, "n_polygones": len(out),
    }
    json.dump({"meta": meta, "features": out}, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False)
    print("Ecrit :", OUT_JSON)

    # ---- statistiques bande 100 m
    band = L1.buffer(R_BAND, cap_style=2)
    band_area = band.area
    area_nat, n_band_nat, n_all_nat = {}, {}, {}
    inters = []
    for fid, f, g, d in kept:
        nat = f["properties"].get("nature")
        n_all_nat[nat] = n_all_nat.get(nat, 0) + 1
        it = g.intersection(band)
        if it.area > 0:
            area_nat[nat] = area_nat.get(nat, 0.0) + it.area
            n_band_nat[nat] = n_band_nat.get(nat, 0) + 1
            inters.append(it)
    union_area = unary_union(inters).area if inters else 0.0
    print(f"\nBande +/-{R_BAND:.0f} m : aire {band_area:.0f} m2 ; couverte par vegetation (union) {union_area:.0f} m2 "
          f"= {100 * union_area / band_area:.2f} %")
    print(f"{'nature':32s} {'polyg. <120m':>12s} {'polyg. bande':>12s} {'aire bande m2':>14s} {'% bande':>8s}")
    for nat in sorted(area_nat, key=lambda k: -area_nat[k]):
        print(f"{str(nat):32s} {n_all_nat[nat]:12d} {n_band_nat[nat]:12d} {area_nat[nat]:14.0f} "
              f"{100 * area_nat[nat] / band_area:8.2f}")
    for nat in n_all_nat:
        if nat not in area_nat:
            print(f"{str(nat):32s} {n_all_nat[nat]:12d} {0:12d} {0:14.0f} {0:8.2f}")
    print(f"Somme des aires par nature : {100 * sum(area_nat.values()) / band_area:.2f} % (peut depasser l'union si chevauchement)")

    # ---- orthophotos de controle
    stations = {}
    sl = json.load(open(os.path.join(RAW, "sncf", "liste-des-gares_420000.json"), encoding="utf-8"))
    for s in sl:
        if s["libelle"] in ("Nogent-le-Rotrou", "Le Mans") or "Connerr" in s["libelle"]:
            pk = float(s["pk"].replace("+", ".")); stations[s["libelle"]] = (pk, s["x_l93"], s["y_l93"])
    print("\nCalibrage PK (position le long de V1 depuis son debut) :")
    implied = []
    for name, (pk, x, y) in stations.items():
        sdist = L1.project(Point(x, y))
        implied.append(pk - sdist / 1000)
        print(f"  {name:20s} PK {pk:.3f} ; distance projetee {sdist:.0f} m ; debut implicite PK {pk - sdist / 1000:.3f}")
    pk0_cal = sum(implied) / len(implied)   # debut de V1 calibre sur les gares (PK 147,1 nominal = non retenu, voir rapport)
    print(f"  Debut V1 calibre (moyenne des gares) : PK {pk0_cal:.3f} ; distance = (PK - {pk0_cal:.3f}) x 1000 m")

    summary = {}
    for pk in PKS:
        d_along = (pk - pk0_cal) * 1000
        p = L1.interpolate(d_along)
        x0, y0 = p.x, p.y
        bxmin, bymin, bxmax, bymax = x0 - 300, y0 - 300, x0 + 300, y0 + 300
        fn = os.path.join(ORTHO, f"ortho_{pk}.jpg")
        if not os.path.exists(fn):
            body, ctype = http_get(WMS % ("%.1f" % bxmin, "%.1f" % bymin, "%.1f" % bxmax, "%.1f" % bymax))
            if not ctype.startswith("image/"):
                raise RuntimeError(f"WMS PK {pk} : reponse {ctype} : {body[:300]!r}")
            open(fn, "wb").write(body)
        img = plt.imread(fn)
        print(f"\nPK {pk} : centre L93 ({x0:.0f},{y0:.0f}), image {img.shape}, ecart-type pixels {img.std():.3f}")

        ext = box(bxmin, bymin, bxmax, bymax)
        nat_in = {}
        fig, ax = plt.subplots(figsize=(8.6, 8.6), dpi=110)
        ax.imshow(img, extent=(bxmin, bxmax, bymin, bymax), origin="upper")
        palette = {"Haie": "#ff9800", "Forêt fermée de feuillus": "#2e7d32", "Forêt fermée de conifères": "#004d40",
                   "Forêt fermée mixte": "#8bc34a", "Bois": "#7cb342", "Peupleraie": "#fdd835",
                   "Lande ligneuse": "#8d6e63", "Verger": "#ec407a", "Vigne": "#ab47bc", "Prairie": "#29b6f6"}
        extra = iter(["#e53935", "#00acc1", "#5e35b1", "#6d4c41", "#c0ca33"])
        by_nat = {}
        for fid, f, g, d in kept:
            it = g.intersection(ext)
            if it.is_empty or it.area <= 0:
                continue
            nat = f["properties"].get("nature")
            nat_in[nat] = nat_in.get(nat, [0, 0.0])
            nat_in[nat][0] += 1; nat_in[nat][1] += it.area
            by_nat.setdefault(nat, [])
            for gg in (it.geoms if hasattr(it, "geoms") else [it]):
                if gg.geom_type == "Polygon":
                    by_nat[nat].append(MplPoly(np.array(gg.exterior.coords), closed=True))
        handles = []
        for nat, patches in by_nat.items():
            col = palette.get(nat) or next(extra)
            ax.add_collection(PatchCollection(patches, facecolor=col, edgecolor=col, alpha=0.35, linewidth=0.8))
            handles.append(Patch(facecolor=col, edgecolor=col, alpha=0.5, label=str(nat)))
        for line, lab, ls in ((L1, "V1", "-"), (L2, "V2", "--")):
            xs, ys = line.xy
            ax.plot(xs, ys, color="red", lw=2, ls=ls)
            handles.append(Line2D([0], [0], color="red", lw=2, ls="-" if lab == "V1" else "--", label=lab))
        ax.set_xlim(bxmin, bxmax); ax.set_ylim(bymin, bymax)
        ax.set_aspect("equal")
        ax.set_xlabel("Lambert-93 X (m)"); ax.set_ylabel("Lambert-93 Y (m)")
        ax.set_title(f"PK {pk} - orthophoto IGN + vegetation BD TOPO (120 m)", fontsize=11)
        ax.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.9)
        fig.tight_layout()
        fig.savefig(os.path.join(ORTHO, f"ortho_{pk}_veg.png"))
        plt.close(fig)
        summary[pk] = {k: {"polygones": v[0], "aire_m2": round(v[1])} for k, v in nat_in.items()}
        print("  natures dans l'extrait 600 m :", summary[pk] or "aucune")

    print("\nFichiers image crees :", len(PKS) * 2)
    if FAILS:
        print("Echecs :", FAILS)


if __name__ == "__main__":
    main()
