"""Signalisation permanente SNCF Reseau (jeu open data SNCF "signalisation-permanente", retire du portail) via la copie en tuiles vectorielles de Carto Tchoo
(tiles.tchoo.net/signalisation, zoom 14, tuiles le long de V1 +-1). Filtre code_ligne=420000, PK 146-213.
Sortie : GeographicData/Raw/sncf/signalisation-permanente_420000.json (liste des objets avec type_if, sens, position, pk, angle, WGS84)."""
import json, math, os, time, requests
import mapbox_vector_tile as mvt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
V = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"), encoding="utf-8"))
v1 = [v for v in V if v["code_voie"] == "420000-1-V1"][0]["geo_shape"]["geometry"]["coordinates"]
Z = 14
def tile(lon, lat):
    n = 2 ** Z; return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
tiles = set()
for lo, la in v1:
    if 0.17 < lo < 0.835 and 47.99 < la < 48.34:
        x, y = tile(lo, la); tiles |= {(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)}
out = {}
for (x, y) in sorted(tiles):
    r = requests.get("https://tiles.tchoo.net/signalisation/%d/%d/%d" % (Z, x, y), headers={"User-Agent": "TSC-route-builder/1.0"}, timeout=60)
    if r.status_code != 200 or not r.content: continue
    try: d = mvt.decode(r.content)
    except Exception: continue
    for lay in d.values():
        for f in lay["features"]:
            p = f["properties"]
            if p.get("code_ligne") == 420000: out[p.get("idreseau") or (p["x_l93"], p["y_l93"], p.get("type_if"))] = p
    time.sleep(0.15)
json.dump(list(out.values()), open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "signalisation-permanente_420000.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(tiles), "tuiles,", len(out), "objets ligne 420000")
