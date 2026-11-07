"""Telecharge les troncons de voie ferree IGN BD TOPO (WFS Geoplateforme) le long de V1 pour la phase 1 (PK 147,1-212,0, tampon 600 m).
Sortie : GeographicData/Raw/bdtopo_voies_phase1.json (FeatureCollection WGS84, deduplique par id). Idempotent."""
import json, os, sys, urllib.request
from shapely.geometry import shape, LineString, box
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
V = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"), encoding="utf-8"))
v1 = [v for v in V if v["code_voie"] == "420000-1-V1"][0]["geo_shape"]["geometry"]["coordinates"]
pts = [p for p in v1 if 0.17 < p[0] < 0.835 and 47.99 < p[1] < 48.34]   # emprise phase 1 (+marge)
X = "https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:troncon_de_voie_ferree&OUTPUTFORMAT=application/json&COUNT=1000&BBOX=%s,%s,%s,%s,EPSG:4326"
feats = {}; step = 0.02; seen = set()
for p in pts[::25]:
    key = (round(p[0] / step), round(p[1] / step))
    if key in seen: continue
    seen.add(key); lon, lat = key[0] * step, key[1] * step
    b = (lon - 0.002, lat - 0.002, lon + step + 0.002, lat + step + 0.002)   # ordre lon,lat accepte par la Geoplateforme
    url = X % b
    with urllib.request.urlopen(url, timeout=60) as r: d = json.load(r)
    for f in d["features"]: feats[f["id"]] = f
buf = LineString(pts).buffer(0.0085)    # ~600 m
out = [f for f in feats.values() if shape(f["geometry"]).intersects(buf)]
json.dump({"type": "FeatureCollection", "features": out}, open(os.path.join(ROOT, "GeographicData", "Raw", "bdtopo_voies_phase1.json"), "w", encoding="utf-8"))
print(len(feats), "recus,", len(out), "gardes")
