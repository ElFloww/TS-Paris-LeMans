"""Champs agricoles (IGN RPG 2024, WFS Geoplateforme) et zones BD TOPO (habitation, activite) dans le couloir de 250 m autour de V1, phase 1 (PK 147,1-212,0).
Sorties :
  GeographicData/Processed/layers/champs.json        (RPG.2024:parcelles_graphiques)
  GeographicData/Processed/layers/zones_urbaines.json (BDTOPO_V3:zone_d_habitation + zone_d_activite_ou_d_interet)
Caches bruts pages WFS : GeographicData/Raw/rpg/cache/ et GeographicData/Raw/bdtopo_zones/cache/ (un fichier par page, relu si present).
Methode de decoupe : cases 0,02 deg le long de V1, pagination STARTINDEX (1000), dedoublonnage par id, filtre exact en Lambert-93 (tampon 250 m).
"""
import json, math, os, sys, time, datetime
import requests
from shapely.geometry import shape, LineString
from shapely.ops import transform, unary_union
from shapely.validation import make_valid
from shapely.geometry import Polygon, MultiPolygon
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import tsc_coords as C

WFS = "https://data.geopf.fr/wfs/ows"
UA = {"User-Agent": "TSC-route-builder/1.0"}
CORRIDOR_M = 250.0
CELL = 0.02
MARGIN = 0.006          # > 250 m en lon (0,0034 deg) et en lat (0,0023 deg) : la requete couvre tout le tampon
PAGE = 1000
RPG_LAYER = "RPG.2024:parcelles_graphiques"
RPG_CODES_LAYER = "RPG.2024:codes_cultures"
ZONE_LAYERS = ["BDTOPO_V3:zone_d_habitation", "BDTOPO_V3:zone_d_activite_ou_d_interet"]
TODAY = datetime.date.today().isoformat()

RAW = os.path.join(ROOT, "GeographicData", "Raw")
OUT = os.path.join(ROOT, "GeographicData", "Processed", "layers")

to2154 = Transformer.from_crs(4326, 2154, always_xy=True)
to4326 = Transformer.from_crs(2154, 4326, always_xy=True)


def load_v1():
    V = json.load(open(os.path.join(RAW, "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"), encoding="utf-8"))
    v1 = [v for v in V if v["code_voie"] == "420000-1-V1"][0]["geo_shape"]["geometry"]["coordinates"]
    return [p[:2] for p in v1 if 0.17 <= p[0] <= 0.835 and 47.99 <= p[1] <= 48.34]


def wfs_page(layer, bbox, start, cache_dir, key):
    os.makedirs(cache_dir, exist_ok=True)
    fn = os.path.join(cache_dir, f"{key}_{start}.json")
    if os.path.exists(fn):
        return json.load(open(fn, encoding="utf-8"))
    params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": layer,
              "OUTPUTFORMAT": "application/json", "COUNT": PAGE, "STARTINDEX": start,
              "BBOX": "%f,%f,%f,%f,EPSG:4326" % bbox}
    r = requests.get(WFS, params=params, headers=UA, timeout=120)
    r.raise_for_status()
    d = r.json()
    json.dump(d, open(fn, "w", encoding="utf-8"))
    time.sleep(0.2)
    return d


def fetch_layer(layer, cells, cache_dir):
    feats = {}
    for ix, iy in cells:
        lon0, lat0 = ix * CELL, iy * CELL
        bbox = (lon0 - MARGIN, lat0 - MARGIN, lon0 + CELL + MARGIN, lat0 + CELL + MARGIN)
        start = 0
        while True:
            d = wfs_page(layer, bbox, start, cache_dir, f"{ix}_{iy}")
            for f in d["features"]:
                feats[f["id"]] = f
            if len(d["features"]) < PAGE:
                break
            start += PAGE
    return feats


def poly_only(g):
    # make_valid peut rendre une collection avec lignes/points : on garde la partie surfacique
    parts = [p for p in getattr(g, 'geoms', [g]) if p.geom_type in ('Polygon', 'MultiPolygon')]
    return unary_union(parts) if parts else g


def filter_corridor(feats, line, corridor):
    out = []
    for f in feats.values():
        g = poly_only(make_valid(transform(to2154.transform, shape(f["geometry"]))))   # shapely: polygones IGN parfois invalides (auto-intersections)
        if not g.intersects(corridor):
            continue
        out.append((f, g, g.distance(line)))
    return out


def xz_rings(geom_ll):
    polys = [geom_ll] if geom_ll.geom_type == "Polygon" else list(geom_ll.geoms)
    res = []
    for p in polys:
        rings = [p.exterior] + list(p.interiors)
        res.append([[[round(C.lonlat_to_xz(x, y)[0], 2), round(C.lonlat_to_xz(x, y)[1], 2)] for x, y in r.coords] for r in rings])
    return res


def centroid_xz(g):
    c = g.centroid
    lon, lat = to4326.transform(c.x, c.y)
    x, z = C.lonlat_to_xz(lon, lat)
    return round(x, 2), round(z, 2)


def ll_geom(g):
    from shapely.ops import transform as tr
    return tr(to4326.transform, g)


def main():
    pts = load_v1()
    line = transform(to2154.transform, LineString(pts))
    corridor = line.buffer(CORRIDOR_M)
    cells = sorted({(math.floor(lon / CELL), math.floor(lat / CELL)) for lon, lat in pts})
    print("V1 points:", len(pts), "cases:", len(cells), "longueur V1 (m):", round(line.length))

    # Codes RPG (table de reference IGN, telechargee une fois)
    codes_fn = os.path.join(RAW, "rpg", "codes_cultures_2024.json")
    if not os.path.exists(codes_fn):
        r = requests.get(WFS, params={"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": RPG_CODES_LAYER,
                                       "OUTPUTFORMAT": "application/json", "COUNT": 2000}, headers=UA, timeout=120)
        r.raise_for_status()
        open(codes_fn, "wb").write(r.content)
        time.sleep(0.2)
    libelles = {f["properties"]["code"]: f["properties"]["libelle"] for f in json.load(open(codes_fn, encoding="utf-8"))["features"]}

    # ---------- RPG ----------
    rpg_raw = fetch_layer(RPG_LAYER, cells, os.path.join(RAW, "rpg", "cache"))
    rpg = filter_corridor(rpg_raw, line, corridor)
    champs = []
    for f, g, dist in rpg:
        p = f["properties"]
        x, z = centroid_xz(g)
        champs.append({
            "id": f["id"], "id_parcel": p.get("id_parcel"),
            "code_culture": p.get("code_cultu"), "libelle_culture": libelles.get(p.get("code_cultu")),
            "groupe_culture": p.get("code_group"), "culture_d1": p.get("culture_d1"), "culture_d2": p.get("culture_d2"),
            "categorie": p.get("cat_cult_p"),
            "surface_ha": p.get("surf_parc"), "surface_geom_ha": round(g.area / 1e4, 4),
            "distance_V1_m": round(dist, 1), "x": x, "z": z,
            "geometry_lonlat": f["geometry"], "polygones_xz": xz_rings(ll_geom(g)),
        })
    assert all(c["distance_V1_m"] <= CORRIDOR_M + 1e-6 for c in champs)
    union = unary_union([g for _, g, _ in rpg]).intersection(corridor)
    couverture = union.area / corridor.area
    surf_tot = sum((c["surface_ha"] or 0) for c in champs)
    used = sorted({c["code_culture"] for c in champs if c["code_culture"]})
    groupes = {}
    for c in champs:
        k = c["groupe_culture"] if c["groupe_culture"] is not None else "inconnu"
        groupes.setdefault(k, [0, 0.0]); groupes[k][0] += 1; groupes[k][1] += c["surface_ha"] or 0
    meta_rpg = {"source": "IGN Geoplateforme, Registre Parcellaire Graphique, couche " + RPG_LAYER + " (WFS " + WFS + ")",
                "millesime": "2024 (couche RPG.2024 ; RPG.LATEST existe aussi sans annee declaree, non utilisee)",
                "tampon_m": CORRIDOR_M, "date_extraction": TODAY, "nb_parcelles": len(champs),
                "surface_totale_ha": round(surf_tot, 2), "proportion_corridor_couverte": round(couverture, 4),
                "repartition_groupe_culture": {str(k): {"parcelles": v[0], "surface_ha": round(v[1], 2)} for k, v in sorted(groupes.items(), key=lambda kv: str(kv[0]))},
                "table_codes_utilises": {k: libelles.get(k) for k in used},
                "table_codes_source": "IGN, " + RPG_CODES_LAYER}
    os.makedirs(OUT, exist_ok=True)
    json.dump({"meta": meta_rpg, "features": champs}, open(os.path.join(OUT, "champs.json"), "w", encoding="utf-8"), ensure_ascii=False)

    # ---------- BD TOPO zones ----------
    zones = []
    for layer in ZONE_LAYERS:
        cache = os.path.join(RAW, "bdtopo_zones", "cache", layer.split(":")[1])
        raw = fetch_layer(layer, cells, cache)
        kept = filter_corridor(raw, line, corridor)
        for f, g, dist in kept:
            p = f["properties"]
            x, z = centroid_xz(g)
            zones.append({"id": f["id"], "couche": layer, "cleabs": p.get("cleabs"), "categorie": p.get("categorie"),
                          "nature": p.get("nature"), "nature_detaillee": p.get("nature_detaillee"),
                          "toponyme": p.get("toponyme"), "commune": p.get("commune"),
                          "surface_m2": round(g.area, 1), "distance_V1_m": round(dist, 1), "x": x, "z": z,
                          "geometry_lonlat": f["geometry"], "polygones_xz": xz_rings(ll_geom(g))})
        print(layer, "recus:", len(raw), "gardes:", len(kept))
    assert all(z_["distance_V1_m"] <= CORRIDOR_M + 1e-6 for z_ in zones)
    meta_z = {"source": "IGN BD TOPO V3, couches " + ", ".join(ZONE_LAYERS) + " (WFS " + WFS + ")",
              "tampon_m": CORRIDOR_M, "date_extraction": TODAY, "nb_zones": len(zones),
              "nb_par_couche": {l: sum(1 for z_ in zones if z_["couche"] == l) for l in ZONE_LAYERS}}
    json.dump({"meta": meta_z, "features": zones}, open(os.path.join(OUT, "zones_urbaines.json"), "w", encoding="utf-8"), ensure_ascii=False)

    print(json.dumps({k: v for k, v in meta_rpg.items() if k not in ("table_codes_utilises",)}, ensure_ascii=False, indent=1))
    print("table codes utilises:", json.dumps(meta_rpg["table_codes_utilises"], ensure_ascii=False))
    print(json.dumps(meta_z, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
