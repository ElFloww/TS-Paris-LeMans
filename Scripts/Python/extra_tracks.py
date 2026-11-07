"""Liste des voies supplementaires de la phase 1 (hors V1/V2) : voies SNCF open data (VPA : voies d'evitement, de gare, communications)
puis voies BD TOPO IGN non couvertes par les precedentes (voies de service, voies uniques). Coordonnees locales TSC (tsc_coords).
Sortie : GeographicData/Processed/extra_tracks_phase1.json  [{id, src, nature, elec, pk, xy:[[x,z]...]}], idempotent."""
import json, os, sys
import numpy as np
from shapely.geometry import shape, LineString, MultiLineString
from shapely.ops import substring
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, HERE)
import tsc_coords as C

PK_A, PK_B = 147.1, 212.0
pk = lambda s: int(s.split("+")[0]) + int(s.split("+")[1]) / 1000
def xz(g): return LineString([C.lonlat_to_xz(*c[:2]) for c in g.coords])

def build():
    V = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"), encoding="utf-8"))
    main = {v["code_voie"]: xz(shape(v["geo_shape"]["geometry"])) for v in V if v["code_voie"] in ("420000-1-V1", "420000-1-V2")}
    v1 = main["420000-1-V1"]
    out, covered = [], list(main.values())
    for v in V:
        if v["type_voie"] == "VPL": continue
        a, b = pk(v["pk_debut_r"]), pk(v["pk_fin_r"])
        if min(a, b) < PK_A - 1.0 or max(a, b) > PK_B + 1.0: continue
        ls = xz(shape(v["geo_shape"]["geometry"]))
        if ls.distance(v1) > 600: continue
        out.append({"id": "SNCF-" + v["nom_voie"] + "-%d" % int(a * 1000), "src": "SNCF open data 420000 (formes des voies)", "nature": "voie " + v["type_voie"], "elec": True, "pk": a, "xy": [list(p) for p in ls.coords]})
        covered.append(ls)
    B = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "bdtopo_voies_phase1.json"), encoding="utf-8"))["features"]
    from shapely.ops import unary_union
    cov1 = unary_union(covered)
    for f in B:
        p = f["properties"]
        if p["etat_de_l_objet"] != "En service" or p["nature"] in ("Tramway", "Sans objet"): continue
        ls = xz(shape(f["geometry"]))
        # un troncon a 2 voies est la mediane de V1/V2 (deja posees) ; un troncon a 1 voie n'est ecarte que s'il se superpose a une voie SNCF
        r = 8.0 if p["nombre_de_voies"] == 2 else 2.5
        rest = ls.difference(cov1.buffer(r))
        parts = list(rest.geoms) if hasattr(rest, "geoms") else ([rest] if not rest.is_empty else [])
        for k, q in enumerate(parts):
            if q.length < 30 or q.geom_type != "LineString": continue
            if q.distance(v1) > 600: continue
            s = v1.project(q.centroid)
            out.append({"id": "BDT-%s-%d" % (f["id"].split(".")[-1], k), "src": "IGN BD TOPO troncon_de_voie_ferree", "nature": p["nature"], "elec": bool(p["electrifie"]), "pk": None, "xy": [list(c) for c in q.coords], "v1_s": s})
            covered.append(q)
    # OSM (niveau 2) : seulement ce que SNCF/BD TOPO ne couvrent pas (voies de garage, faisceaux) ; ecart minimal entre deux voies = 3,5 m
    op = os.path.join(ROOT, "GeographicData", "Raw", "osm_voies_phase1.json")
    if os.path.exists(op):
        cov2 = unary_union(covered).buffer(3.5)
        for wid, w in json.load(open(op, encoding="utf-8")).items():
            t = w["tags"]
            if t.get("railway") not in ("rail", "siding", "yard", "spur", "preserved") or t.get("gauge", "1435") not in ("1435", "1435;1668"): continue
            ls = xz(LineString(w["geometry"]))
            if ls.distance(v1) > 600: continue
            rest = ls.difference(cov2)
            parts = list(rest.geoms) if hasattr(rest, "geoms") else ([rest] if not rest.is_empty else [])
            for k, q in enumerate(parts):
                if q.length < 30 or q.geom_type != "LineString": continue
                out.append({"id": "OSM-%s-%d" % (wid, k), "src": "OpenStreetMap way %s" % wid, "nature": "osm " + t.get("railway", "") + " " + t.get("service", ""), "elec": t.get("electrified") in ("contact_line", "yes"), "pk": None, "xy": [list(c) for c in q.coords], "v1_s": v1.project(q.centroid)})
    return out

if __name__ == "__main__":
    o = build(); os.makedirs(os.path.join(ROOT, "GeographicData", "Processed"), exist_ok=True)
    json.dump(o, open(os.path.join(ROOT, "GeographicData", "Processed", "extra_tracks_phase1.json"), "w"), ensure_ascii=False)
    import collections
    print(len(o), collections.Counter((e["src"][:4], e["nature"], e["elec"]) for e in o))
    for e in sorted(o, key=lambda e: e.get("v1_s", 0)):
        L = LineString(e["xy"]).length
        if not e["id"].startswith("SNCF"): print(e["id"], e["nature"], "elec=%s" % e["elec"], "L=%.0f m" % L, "pos V1 s=%.0f m" % e["v1_s"])
