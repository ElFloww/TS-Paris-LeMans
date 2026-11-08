"""Phase 1 (PK 147-212), ligne 420000 : routes BD TOPO a moins de 150 m de V1, croisements route / voies V1-V2 classes.
Entrees : Raw/bdtopo_routes_phase1.json (cache), Raw/bdtopo_voies_phase1.json, Raw/sncf/*.json,
          Raw/osm_pn_phase1.json (facultatif : cache OSM, sinon tentative Overpass unique par endpoint).
Sorties : Processed/layers/routes_150m.json, Processed/layers/croisements_routes.json, Raw/osm_pn_phase1.json si Overpass repond.
Rapport sur stdout. PK = projection sur V1 complete + 1.186 km."""
import json, math, os, re, sys, time
from collections import Counter, defaultdict
import numpy as np
import requests
from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, Point

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import tsc_coords as C  # noqa: E402

RAW = os.path.join(ROOT, "GeographicData", "Raw")
SNCF = os.path.join(RAW, "sncf")
LAYERS = os.path.join(ROOT, "GeographicData", "Processed", "layers")
os.makedirs(LAYERS, exist_ok=True)
UA = {"User-Agent": "TSC-route-builder/1.0"}
PAUSE = 0.2
WFS = "https://data.geopf.fr/wfs/ows"
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
PK_DEBUT_V1 = 1.186  # PK du debut de la polyligne V1 complete (SNCF)
PK_MIN, PK_MAX = 147.0, 212.3
TO_L93 = Transformer.from_crs(4326, 2154, always_xy=True)
TO_WGS = Transformer.from_crs(2154, 4326, always_xy=True)


def log(*a):
    print(*a, flush=True)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, o):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False)


def get(url):
    """GET avec User-Agent, pause de 0,2 s apres chaque requete, 3 essais."""
    last = None
    for k in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=180)
            time.sleep(PAUSE)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
            time.sleep(3 + 3 * k)
    raise last


def voie_geom(code):
    """Coordonnees lon/lat completes de la voie SNCF (non filtrees)."""
    V = load(os.path.join(SNCF, "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"))
    v = [v for v in V if v["code_voie"] == code][0]
    return v["geo_shape"]["geometry"]["coordinates"]


def voie_pts(code):
    """Points de la voie limites a l'emprise phase 1 (lon 0.17-0.835, lat 47.99-48.34)."""
    return [p for p in voie_geom(code) if 0.17 < p[0] < 0.835 and 47.99 < p[1] < 48.34]


def line_l93(pts):
    xs, ys = TO_L93.transform([p[0] for p in pts], [p[1] for p in pts])
    return LineString(list(zip(xs, ys)))


def cells(pts, size):
    return sorted({(math.floor(p[0] / size), math.floor(p[1] / size)) for p in pts})


def parts(geom):
    """Liste de polylignes (coordonnees lon/lat) d'un LineString ou MultiLineString GeoJSON."""
    if geom and geom.get("type") == "LineString":
        return [geom["coordinates"]]
    if geom and geom.get("type") == "MultiLineString":
        return geom["coordinates"]
    return []


def fetch_routes_raw(v1pts):
    cache = os.path.join(RAW, "bdtopo_routes_phase1.json")
    if os.path.exists(cache):
        log("cache BD TOPO troncon_de_route :", cache)
        return load(cache)["features"]
    raise SystemExit("cache bdtopo_routes_phase1.json absent : relance interdite par la consigne, arret")


def build_routes(feats, v1):
    out = []
    for f in feats:
        ps = [p for p in parts(f.get("geometry")) if len(p) >= 2]
        if not ps:
            continue
        lines = [line_l93(p) for p in ps]
        geom = lines[0] if len(lines) == 1 else MultiLineString([list(l.coords) for l in lines])
        if geom.distance(v1) > 150:
            continue
        lonlat = [[p[0], p[1]] for part in ps for p in part]
        pr = f.get("properties", {})
        pos = pr.get("position_par_rapport_au_sol")
        out.append({
            "id": f.get("id"), "nature": pr.get("nature"), "importance": pr.get("importance"),
            "largeur_de_chaussee": pr.get("largeur_de_chaussee"), "nombre_de_voies": pr.get("nombre_de_voies"),
            "sens_de_circulation": pr.get("sens_de_circulation"),
            "position_par_rapport_au_sol": int(pos) if pos not in (None, "") else None,
            "etat_de_l_objet": pr.get("etat_de_l_objet"), "nom": pr.get("nom_1_gauche"),
            "lonlat": [[round(lo, 7), round(la, 7)] for lo, la in lonlat],
            "xz": [[round(v, 2) for v in C.lonlat_to_xz(lo, la)] for lo, la in lonlat],
            "_geom": geom,
        })
    return out


OSM_TPL = '[out:json][timeout:90];node["railway"~"^(level_crossing|crossing)$"]({s},{w},{n},{e});out;'


def fetch_osm(v1pts):
    """Cache s'il existe, sinon au plus 2 essais (un par endpoint, 20 s entre eux). None si indisponible."""
    cache = os.path.join(RAW, "osm_pn_phase1.json")
    if os.path.exists(cache):
        log("cache OSM passages a niveau :", cache)
        return load(cache)
    boxes = []
    for ix, iy in cells(v1pts, 0.04):
        lon0, lat0 = ix * 0.04, iy * 0.04
        boxes.append((round(lat0 - 0.003, 6), round(lon0 - 0.003, 6), round(lat0 + 0.043, 6), round(lon0 + 0.043, 6)))
    for k, ep in enumerate(OVERPASS):
        els, cases = {}, []
        try:
            for bb in boxes:
                r = requests.post(ep, data={"data": OSM_TPL.format(s=bb[0], w=bb[1], n=bb[2], e=bb[3])},
                                  headers=UA, timeout=150)
                time.sleep(PAUSE)
                r.raise_for_status()
                d = r.json()
                for el in d.get("elements", []):
                    els[el["id"]] = el
                cases.append({"bbox_s_w_n_e": list(bb), "nb_noeuds": len(d.get("elements", []))})
            out = {"source": "OpenStreetMap via Overpass API", "licence": "ODbL, contributeurs OpenStreetMap",
                   "endpoint": ep, "requete": OSM_TPL, "date_telechargement": time.strftime("%Y-%m-%d"),
                   "cases": cases, "elements": list(els.values())}
            save(cache, out)
            log(f"OSM : {len(els)} noeuds railway=level_crossing/crossing, {len(cases)} cases, endpoint {ep}")
            return out
        except (requests.RequestException, ValueError) as e:
            log(f"  OSM echec {ep} : {type(e).__name__} {str(e)[:120]}")
            if k == 0:
                time.sleep(20)
    log("OSM indisponible : continue SANS OSM (aucun fichier cache ecrit)")
    return None


def sncf_pts(fname, kind):
    out = []
    for p in load(os.path.join(SNCF, fname)):
        pk = pk_km(p.get("pk"))
        if p.get("rg_troncon") != 1 or pk is None or not 147 <= pk <= 212:
            continue
        lon, lat = p.get("x_wgs84"), p.get("y_wgs84")
        if lon is None or lat is None:
            continue
        x, y = TO_L93.transform(lon, lat)
        out.append({"kind": kind,
                    "id": p.get("id_if") if kind == "pn" else f"pont-{p.get('idreseau')}",
                    "libelle": p.get("libelle"), "type": p.get("mnemo") if kind == "pn" else None,
                    "obstacle": p.get("obstacle"), "pk_km": round(pk, 3),
                    "lon": lon, "lat": lat, "x_l93": x, "y_l93": y})
    return out


def pk_km(s):
    m = re.fullmatch(r"\s*(\d+)\+(\d+)\s*", s or "")
    return int(m[1]) + int(m[2]) / 1000 if m else None


def arr(lst, xk="x_l93", yk="y_l93"):
    return np.array([[p[xk], p[yk]] for p in lst]) if lst else np.empty((0, 2))


def nearest(x, y, a, r):
    """Index du point le plus proche si <= r (sinon None), et distance minimale."""
    if len(a) == 0:
        return None, math.inf
    d = np.hypot(a[:, 0] - x, a[:, 1] - y)
    i = int(d.argmin())
    return (i if d[i] <= r else None), float(d[i])


def crossing_points(g):
    """Points d'intersection ; (points, nombre de chevauchements lineaires ramenes a un point)."""
    if g.geom_type == "Point":
        return [g], 0
    if g.geom_type == "MultiPoint":
        return list(g.geoms), 0
    if g.geom_type == "GeometryCollection":
        pts, ov = [], 0
        for h in g.geoms:
            a, b = crossing_points(h)
            pts += a
            ov += b
        return pts, ov
    return [g.representative_point()], 1


def main():
    V1 = voie_pts("420000-1-V1")
    V2 = voie_pts("420000-1-V2")
    v1, v2 = line_l93(V1), line_l93(V2)
    v1_full = line_l93(voie_geom("420000-1-V1"))
    log(f"V1 : {len(V1)} points, V2 : {len(V2)} points (emprise phase 1), V1 complete : {v1_full.length/1000:.3f} km")

    def pk_of(P):
        return v1_full.project(P) / 1000 + PK_DEBUT_V1

    routes = build_routes(fetch_routes_raw(V1), v1)
    save(os.path.join(LAYERS, "routes_150m.json"),
         [{k: v for k, v in r.items() if not k.startswith("_")} for r in routes])
    log(f"Routes BD TOPO a <= 150 m de V1 : {len(routes)}")
    route_by_id = {r["id"]: r for r in routes}

    osm = fetch_osm(V1)
    pn_all = sncf_pts("liste-des-passages-a-niveau_420000.json", "pn")
    pont_all = sncf_pts("liste-des-ponts-route_420000.json", "pont")
    log(f"SNCF PK 147-212 : {len(pn_all)} PN, {len(pont_all)} ponts-route")

    # Controle de la formule PK sur les PK SNCF a <= 150 m de V1
    refs = [p for p in pn_all + pont_all if v1.distance(Point(p["x_l93"], p["y_l93"])) <= 150]
    ecarts = np.array([p["pk_km"] - pk_of(Point(p["x_l93"], p["y_l93"])) for p in refs])
    if len(ecarts):
        log(f"Controle PK (formule V1 complete + {PK_DEBUT_V1}) : {len(refs)} PN/ponts a <= 150 m, "
            f"ecart median {np.median(ecarts):+.3f} km, ecart max {np.abs(ecarts).max():.3f} km")

    osm_nodes = []
    if osm:
        for el in osm["elements"]:
            x, y = TO_L93.transform(el["lon"], el["lat"])
            tags = el.get("tags", {})
            osm_nodes.append({"id": el["id"], "lon": el["lon"], "lat": el["lat"], "x_l93": x, "y_l93": y,
                              "name": tags.get("name") or tags.get("ref"),
                              "type": "osm:" + tags.get("railway", "?") +
                                      (":" + tags["level_crossing"] if "level_crossing" in tags else "")})
    osm_lc = [n for n in osm_nodes if n["type"].startswith("osm:level_crossing")]

    # Position par rapport au sol des troncons de voie ferree BD TOPO
    rail1 = []
    for f in load(os.path.join(RAW, "bdtopo_voies_phase1.json"))["features"]:
        raw = f["properties"].get("position_par_rapport_au_sol")
        if raw in (None, "") or int(raw) != 1:
            continue
        for p in parts(f.get("geometry")):
            if len(p) >= 2:
                rail1.append(line_l93(p))
    rail1_g = MultiLineString([list(l.coords) for l in rail1]) if rail1 else None
    log(f"Voies ferrees BD TOPO position 1 : {len(rail1)} troncons")

    pn_arr, lc_arr, pont_arr = arr(pn_all), arr(osm_lc), arr(pont_all)
    crossings, cxy = [], []
    overlaps = 0
    for r in routes:
        for voie, vl in (("V1", v1), ("V2", v2)):
            inter = r["_geom"].intersection(vl)
            if inter.is_empty:
                continue
            pts, ov = crossing_points(inter)
            overlaps += ov
            for P in pts:
                pk = round(pk_of(P), 3)
                if not PK_MIN <= pk <= PK_MAX:
                    continue
                x, y = P.x, P.y
                lon, lat = TO_WGS.transform(x, y)
                xl, zl = C.lonlat_to_xz(lon, lat)
                ipn, _ = nearest(x, y, pn_arr, 40)
                ilc, _ = nearest(x, y, lc_arr, 25)
                ipont, _ = nearest(x, y, pont_arr, 40)
                d1 = rail1_g.distance(P) if rail1_g else math.inf
                pos = r["position_par_rapport_au_sol"]
                sncf_pn, osm_n, pont = ipn is not None, ilc is not None, ipont is not None

                if sncf_pn or osm_n:
                    cls = "passage_a_niveau"
                elif pos == 1 or pont:
                    cls = "pont_route"
                elif pos == -1 or d1 <= 30:
                    cls = "passage_inferieur"
                else:
                    cls = "inconnu"

                pn_id = pn_type = pn_nom = None
                if sncf_pn:
                    pn_id, pn_type, pn_nom = pn_all[ipn]["id"], pn_all[ipn]["type"], pn_all[ipn]["libelle"]
                elif osm_n:
                    o = osm_lc[ilc]
                    pn_id, pn_type, pn_nom = f"osm-{o['id']}", o["type"], o["name"]
                # haute : PN SNCF confirme par OSM, ou par un pont-route SNCF concordant
                confiance = "haute" if cls == "passage_a_niveau" and sncf_pn and (osm_n or pont) else "moyenne"

                crossings.append({
                    "id": f"CX-{len(crossings) + 1:04d}", "lon": round(lon, 7), "lat": round(lat, 7),
                    "x": round(xl, 2), "z": round(zl, 2), "route_id": r["id"], "route_nature": r["nature"],
                    "route_largeur": r["largeur_de_chaussee"], "route_importance": r["importance"],
                    "route_nom": r["nom"], "classification": cls, "pn_id": pn_id, "pn_nom": pn_nom,
                    "pn_type": pn_type, "voie": voie, "pk_approx": pk, "confiance": confiance,
                })
                cxy.append((x, y, cls, r["id"], pn_id))

    out = {"meta": {
        "osm_disponible": osm is not None,
        "sources": [
            "IGN BD TOPO V3 troncon_de_route (Geoplateforme WFS) : routes",
            "IGN BD TOPO troncon de voie ferree position_par_rapport_au_sol (bdtopo_voies_phase1.json)",
            "SNCF Reseau fichier-de-formes-des-voies-du-reseau-ferre-national (ligne 420000, V1/V2)",
            "SNCF Reseau liste-des-passages-a-niveau (ligne 420000)",
            "SNCF Reseau liste-des-ponts-route (ligne 420000)",
            "OpenStreetMap via Overpass (railway=level_crossing) : " + ("oui" if osm else "non disponible"),
        ],
        "pk": f"PK = projection sur V1 complete (SNCF) / 1000 + {PK_DEBUT_V1}, garde {PK_MIN}-{PK_MAX}",
        "nombre": len(crossings)}, "croisements": crossings}
    save(os.path.join(LAYERS, "croisements_routes.json"), out)

    # ---- Rapport ----
    cnt = Counter(c["classification"] for c in crossings)
    log(f"\nCroisements route/voie : {len(crossings)} (routes distinctes : "
        f"{len({c['route_id'] for c in crossings})}, chevauchements ramenes a un point : {overlaps})")
    for k in ("passage_a_niveau", "pont_route", "passage_inferieur", "inconnu"):
        log(f"  {k:18s} {cnt.get(k, 0)}")
    log("  confiance haute :", sum(c["confiance"] == "haute" for c in crossings))
    log(f"OSM disponible : {osm is not None}")

    # 18 PN de pn_phase1.json
    pn18 = load(os.path.join(LAYERS, "pn_phase1.json"))
    cxy_a = np.array([(x, y) for x, y, *_ in cxy]) if cxy else np.empty((0, 2))
    trouves, sans_route = 0, []
    for p in pn18:
        x, y = TO_L93.transform(p["lon"], p["lat"])
        P = Point(x, y)
        near = cxy_a.size and bool((np.hypot(cxy_a[:, 0] - x, cxy_a[:, 1] - y) <= 40).any())
        cls_pn = [c for c in cxy if c[4] == p.get("id") and c[2] == "passage_a_niveau"]
        trouves += bool(near)
        dmin = min((rt["_geom"].distance(P) for rt in routes), default=math.inf)
        if dmin > 40:
            sans_route.append((p["nom"], p["pk"], round(dmin, 1), bool(near), len(cls_pn)))
    log(f"\nPN de pn_phase1.json (18) : {trouves} retrouves par un croisement a <= 40 m")
    log(f"PN sans route a <= 40 m : {len(sans_route)}")
    for nom, pk, dmin, near, ncls in sans_route:
        log(f"  {nom} PK {pk} : route la plus proche {dmin} m, croisement a <= 40 m : {near}, "
            f"classe PN pour ce PN : {ncls}")

    # Routes sans classification
    by_route = defaultdict(set)
    for c in crossings:
        by_route[c["route_id"]].add(c["classification"])
    inc_routes = [rid for rid, s in by_route.items() if s == {"inconnu"}]
    chem = re.compile(r"chemin|sentier|piste|escalier", re.I)
    nat_imp, nat_chem = Counter(), Counter()
    for rid in inc_routes:
        nat = route_by_id[rid]["nature"]
        (nat_chem if chem.search(nat or "") else nat_imp)[nat] += 1
    log(f"\nRoutes croisant V1/V2 (PK 147-212) : {len(by_route)}, dont toutes les croisements 'inconnu' : {len(inc_routes)}")
    log(f"  importantes (natures) : {sum(nat_imp.values())} -> {dict(nat_imp)}")
    log(f"  chemins/sentiers : {sum(nat_chem.values())} -> {dict(nat_chem)}")
    unk_pts = [c for c in crossings if c["classification"] == "inconnu"]
    log(f"Points 'inconnu' : {len(unk_pts)} sur {len(crossings)}")


if __name__ == "__main__":
    main()
