"""Batiments BD TOPO (IGN, couche BDTOPO_V3:batiment, Geoplateforme WFS) a moins de 150 m de la voie V1
(phase 1, PK 147,1-212,0). Distance mesuree en Lambert-93 (EPSG:2154).
Sorties :
  GeographicData/Raw/bdtopo_batiment_corridor_raw.json  (cache brut WFS, non reteleche s'il existe)
  GeographicData/Processed/layers/batiments.json        (attributs, polygones lon/lat + x,z, statistiques dans metadata.stats)
Source voies : SNCF Reseau open data, fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json."""
import json, os, sys, time, urllib.request, collections
from pyproj import Transformer
from shapely import force_2d, segmentize
from shapely.geometry import shape, LineString, MultiLineString, mapping
from shapely.ops import transform as sh_transform

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import tsc_coords as C

RAW = os.path.join(ROOT, "GeographicData", "Raw")
SNCF = os.path.join(RAW, "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json")
CACHE = os.path.join(RAW, "bdtopo_batiment_corridor_raw.json")
OUT_DIR = os.path.join(ROOT, "GeographicData", "Processed", "layers"); os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "batiments.json")
LON0, LON1, LAT0, LAT1 = 0.17, 0.835, 47.99, 48.34   # emprise phase 1 (+marge), comme le projet
RAYON, RAYON_FER = 150.0, 25.0                        # m
STEP, MARGE = 0.02, 0.003                             # cases deg ; marge > 150 m en lon et en lat (0,003 deg)
UA = "TSC-route-builder/1.0"
WFS = ("https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:batiment"
       "&OUTPUTFORMAT=application/json&COUNT=1000&STARTINDEX=%d&BBOX=%s,%s,%s,%s,EPSG:4326")
T = Transformer.from_crs(4326, 2154, always_xy=True)

def proj(lonlat):
    xs, ys = T.transform([p[0] for p in lonlat], [p[1] for p in lonlat])
    return list(zip(xs, ys))

def voie_runs(code):
    """Polylignes de la voie, decoupees en troncons contigus a l'interieur de l'emprise."""
    V = json.load(open(SNCF, encoding="utf-8"))
    hits = [v for v in V if v["code_voie"] == code]
    if not hits: return None
    pts = hits[0]["geo_shape"]["geometry"]["coordinates"]
    runs, cur = [], []
    for p in pts:
        if LON0 < p[0] < LON1 and LAT0 < p[1] < LAT1: cur.append((p[0], p[1]))
        else:
            if len(cur) >= 2: runs.append(cur)
            cur = []
    if len(cur) >= 2: runs.append(cur)
    return runs

def get_json(url):
    for essai in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
                return json.load(r)
        except Exception as e:
            print("  erreur", essai + 1, e); time.sleep(2)
    raise RuntimeError("echec WFS : " + url)

def fetch_cells(cells):
    feats = {}
    for n, (i, j) in enumerate(cells):
        b = (i * STEP - MARGE, j * STEP - MARGE, (i + 1) * STEP + MARGE, (j + 1) * STEP + MARGE)
        start = 0
        while True:
            d = get_json(WFS % (start, b[0], b[1], b[2], b[3]))
            fs = d.get("features", [])
            for f in fs: feats[f["id"]] = f
            time.sleep(0.2)
            if len(fs) < 1000: break
            start += len(fs)
        if n % 20 == 0: print(f"  case {n + 1}/{len(cells)} : {len(feats)} batiments uniques")
    return list(feats.values())

def main():
    runs1 = voie_runs("420000-1-V1")
    runs2 = voie_runs("420000-1-V2")
    print("V1 troncons :", len(runs1), "; V2 :", 0 if runs2 is None else len(runs2))
    L1 = MultiLineString([proj(r) for r in runs1])
    L2 = MultiLineString([proj(r) for r in runs2]) if runs2 else None

    # cases le long de V1 et V2 (lignes densifiees a 50 m pour ne sauter aucune case)
    cells = set()
    for runs in [runs1] + ([runs2] if runs2 else []):
        for r in runs:
            ls = segmentize(LineString(proj(r)), 50.0)
            back = T.transform([p[0] for p in ls.coords], [p[1] for p in ls.coords], direction="INVERSE")
            for lon, lat in zip(*back):
                cells.add((int(lon // STEP), int(lat // STEP)))
    cells = sorted(cells)
    print("cases a interroger :", len(cells))

    if os.path.exists(CACHE):
        feats = json.load(open(CACHE, encoding="utf-8"))["features"]
        print("cache brut reutilise :", len(feats), "entites")
    else:
        feats = fetch_cells(cells)
        json.dump({"type": "FeatureCollection", "features": feats,
                   "source": "IGN BD TOPO V3 couche batiment, WFS Geoplateforme (data.geopf.fr/wfs/ows)",
                   "cases": len(cells)}, open(CACHE, "w", encoding="utf-8"))
        print("cache brut ecrit :", len(feats), "entites")

    out, compt = [], collections.Counter()
    for f in feats:
        g_ll = force_2d(shape(f["geometry"]))
        g_l = sh_transform(T.transform, g_ll)
        d1 = g_l.distance(L1)
        if d1 >= RAYON: continue
        d2 = g_l.distance(L2) if L2 is not None else None
        p = f.get("properties") or {}
        usage = p.get("usage_1")
        ferro = ("ferroviaire" in (usage or "").lower()) or d1 < RAYON_FER or (d2 is not None and d2 < RAYON_FER)
        polys = list(g_ll.geoms) if hasattr(g_ll, "geoms") else [g_ll]
        rings = [[[round(x, 8), round(y, 8)] for x, y in pg.exterior.coords] for pg in polys]
        rings_xz = [[[round(v, 2) for v in C.lonlat_to_xz(x, y)] for x, y in r] for r in rings]
        cx, cz = C.lonlat_to_xz(g_ll.centroid.x, g_ll.centroid.y)
        out.append({
            "id": f["id"], "cleabs": p.get("cleabs"), "nature": p.get("nature"),
            "usage_1": usage, "usage_2": p.get("usage_2"),
            "nombre_d_etages": p.get("nombre_d_etages"), "hauteur": p.get("hauteur"),
            "materiaux_des_murs": p.get("materiaux_des_murs"),
            "materiaux_de_la_toiture": p.get("materiaux_de_la_toiture"),
            "aire_m2": round(g_l.area, 1), "distance_v1_m": round(d1, 1),
            "distance_v2_m": None if d2 is None else round(d2, 1),
            "ferroviaire": bool(ferro),
            "x": round(cx, 2), "z": round(cz, 2),
            "polygone_lonlat": rings, "polygone_xz": rings_xz,
        })

    # statistiques
    def bin_area(a):
        for lim, lab in [(30, "<30"), (60, "30-60"), (120, "60-120"), (400, "120-400")]:
            if a < lim: return lab
        return ">400"
    def bin_h(h):
        if h is None: return "inconnu"
        for lim, lab in [(5, "<5"), (10, "5-10"), (15, "10-15"), (20, "15-20")]:
            if h < lim: return lab
        return ">=20"
    n = len(out)
    stats = {
        "total": n,
        "ferroviaire": sum(1 for o in out if o["ferroviaire"]),
        "par_usage_1": dict(collections.Counter(o["usage_1"] or "inconnu" for o in out).most_common()),
        "par_emprise_m2": dict(collections.Counter(bin_area(o["aire_m2"]) for o in out)),
        "par_hauteur_m": dict(collections.Counter(bin_h(o["hauteur"]) for o in out)),
        "distance_v1_sous_50_m": sum(1 for o in out if o["distance_v1_m"] < 50),
        "distance_v1_sous_100_m": sum(1 for o in out if o["distance_v1_m"] < 100),
        "distance_v1_sous_150_m": sum(1 for o in out if o["distance_v1_m"] < 150),
        "top10_plus_grands": [
            {"id": o["id"], "usage_1": o["usage_1"], "aire_m2": o["aire_m2"],
             "distance_v1_m": o["distance_v1_m"], "x": o["x"], "z": o["z"]}
            for o in sorted(out, key=lambda o: -o["aire_m2"])[:10]],
    }
    out.sort(key=lambda o: o["distance_v1_m"])
    doc = {"type": "FeatureCollection",
           "metadata": {
               "description": "Batiments BD TOPO a moins de 150 m de V1 (phase 1 Nogent-le-Rotrou - Le Mans)",
               "sources": ["IGN BD TOPO V3, couche batiment (Geoplateforme WFS, licence ouverte Etalab)",
                           "SNCF Reseau open data, fichier-de-formes-des-voies-du-reseau-ferre-national_420000 (V1, V2)"],
               "projection_distance": "EPSG:2154 (Lambert-93)",
               "rayon_m": RAYON, "seuil_ferroviaire_m": RAYON_FER, "cases_wfs": len(cells),
               "bdtopo_entites_brutes": len(feats),
               "stats": stats},
           "features": [{"type": "Feature", "id": o["id"], "properties": {k: v for k, v in o.items()
                         if k not in ("polygone_lonlat", "polygone_xz")},
                         "geometry": {"type": "MultiPolygon", "coordinates": [[r] for r in o["polygone_lonlat"]]},
                         "polygone_xz": o["polygone_xz"]} for o in out]}
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    print("ecrit :", OUT, os.path.getsize(OUT) // 1024, "Ko")

if __name__ == "__main__":
    main()
