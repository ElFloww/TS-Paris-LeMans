"""Telecharge les quais OSM (railway=platform, public_transport=platform, railway=platform_edge) autour des 9 gares voyageurs de la phase 1.
Sortie : GeographicData/Raw/osm_quais_phase1.json  {id: {type, tags, geometry:[[lon,lat]...]}}. Source de niveau 2 (collaborative)."""
import json, os, time, requests
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
G = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "liste-des-gares_420000.json"), encoding="utf-8")); out = {}
pk = lambda s: int(s.split("+")[0]) + int(s.split("+")[1]) / 1000
for g in G:
    if g["code_ligne"] == "420000" and g["voyageurs"] == "O" and 146 <= pk(g["pk"]) <= 213:
        lo, la = g["x_wgs84"], g["y_wgs84"]; b = (la - 0.006, lo - 0.012, la + 0.006, lo + 0.012)   # ~1,3 km sur 0,9 km
        q = '[out:json][timeout:60];(way["railway"~"^(platform|platform_edge)$"](%.4f,%.4f,%.4f,%.4f);way["public_transport"="platform"](%.4f,%.4f,%.4f,%.4f);relation["public_transport"="platform"](%.4f,%.4f,%.4f,%.4f););out tags geom;' % (b + b + b)
        for attempt in range(6):
            try:
                r = requests.post(["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"][attempt % 2], data={"data": q}, headers={"User-Agent": "TSC-route-builder/1.0"}, timeout=90)
                if r.status_code == 200: break
            except Exception: pass
            time.sleep(5)
        for e in r.json()["elements"]:
            geom = [[p["lon"], p["lat"]] for p in e.get("geometry", [])]
            if geom: out["%s%d" % (e["type"][0], e["id"])] = {"station": g["libelle"], "tags": e.get("tags", {}), "geometry": geom}
        time.sleep(1.5)
json.dump(out, open(os.path.join(ROOT, "GeographicData", "Raw", "osm_quais_phase1.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(out), "objets quai")
