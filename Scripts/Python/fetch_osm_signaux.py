"""Telecharge les signaux OSM (railway=signal, railway=buffer_stop, railway=derail...) le long de V1 pour la phase 1 (Overpass, cases de 0,04 deg).
Sortie : GeographicData/Raw/osm_signaux_phase1.json {id: {lon, lat, tags}}. Source de niveau 2 (collaborative)."""
import json, os, time, requests
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
V = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"), encoding="utf-8"))
v1 = [v for v in V if v["code_voie"] == "420000-1-V1"][0]["geo_shape"]["geometry"]["coordinates"]
step = 0.04; cells = sorted({(int(p[0] // step), int(p[1] // step)) for p in v1 if 0.17 < p[0] < 0.835 and 47.99 < p[1] < 48.34})
URLS = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]; out = {}
for (cx, cy) in cells:
    b = (cy * step - 0.003, cx * step - 0.003, (cy + 1) * step + 0.003, (cx + 1) * step + 0.003)
    q = '[out:json][timeout:90];node["railway"~"^(signal|buffer_stop|derail|railway_crossing)$"](%.4f,%.4f,%.4f,%.4f);out;' % b
    for attempt in range(6):
        try:
            r = requests.post(URLS[attempt % 2], data={"data": q}, headers={"User-Agent": "TSC-route-builder/1.0"}, timeout=120)
            if r.status_code == 200: break
        except Exception: pass
        time.sleep(5)
    else: raise SystemExit("echec case %s" % ((cx, cy),))
    for e in r.json()["elements"]: out[e["id"]] = {"lon": e["lon"], "lat": e["lat"], "tags": e.get("tags", {})}
    time.sleep(1.5)
json.dump(out, open(os.path.join(ROOT, "GeographicData", "Raw", "osm_signaux_phase1.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(cells), "cases,", len(out), "objets")
