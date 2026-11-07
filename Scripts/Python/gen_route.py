"""Generateur de route TSC a partir des voies officielles SNCF V1/V2 (ligne 420000).

Usage : python gen_route.py <pk_debut> <pk_fin> <nom>
Sortie : Route/Exports/<nom>/<GUID>/ (route "libre", pretes a copier dans Content/Routes).
Modeles (non versionnes) : copie de la route TestTraK dans Tests/Phase1/serz_test/.
Valide en jeu (2026-11-07) : voies + terrain + MixMap sur 2 km. Le reste est a valider (voir history.md).
"""
import sys, os, re, json, math, copy, uuid, shutil, subprocess, struct
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import requests
from lxml import etree
from scipy.spatial import cKDTree
from shapely.geometry import shape
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tsc_coords as C
import curvefit as CF

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TPL = os.path.join(ROOT, "Tests", "Phase1", "serz_test")
CACHE = os.path.join(ROOT, "GeographicData", "Elevation", "dem_cache_%s_%s" % (C.LAT0, C.LON0))
SERZ = r"D:\Programmes\Steam\steamapps\common\RailWorks\serz.exe"
D = "http://www.kuju.com/TnT/2003/Delta"
TILE, GRID, CELL = 1024.0, 128, 8.0
TRACKS = ["420000-1-V1", "420000-1-V2"]
MARS = os.path.join(ROOT, "Tests", "Phase1", "marseille")   # modeles extraits du DLC Marseille-Avignon (extract_templates.py)
H_CONTACT, H_MESS = 5.8176, 7.0885   # hauteurs au-dessus du rail relevees sur la cat?naire du DLC (fil de contact, porteur)
TRACK_BP = ("DTG", "LGVMedSouth", r"RailNetwork\Track\track01_conc.xml")
PRELOAD = [("DTG", "LGVMedSouth")]   # assets francais (DLC Marseille-Avignon) : dependance externe, jamais copiee
TRACK_RULE = ("DTG", "LGVMedSouth", r"RailNetwork\TrackRules\LGVMedSouth_Track_Rule.xml")
_SETS = {  # variantes de voie pour les essais d'affichage : nom -> (blueprint, regle, produits a precharger en plus)
    "testtrak": (("RSC", "TestTraK", r"RailNetwork\Track\oxfo_padd_track01.xml"), None, []),
    "kuju": (("Kuju", "RailSimulator", r"RailNetwork\Track\oxfo_padd_track01.xml"), None, [("Kuju", "RailSimulator")]),
    "academy": (("DTG", "Academy", r"RailNetwork\Track\track01_conc.xml"), None, [("DTG", "Academy")]),
    "hh": (("RSC", "HamburgHannover", r"RailNetwork\Track\HH_Track_Concrete01.xml"), None, [("RSC", "HamburgHannover")]),
}
if os.environ.get("TRACK_BP") in _SETS:
    TRACK_BP, TRACK_RULE, _extra = _SETS[os.environ["TRACK_BP"]]; PRELOAD = PRELOAD + _extra
TO93 = Transformer.from_crs(4326, 2154, always_xy=True)

# ---------------------------------------------------------------- XML
def q(e): return etree.QName(e).localname
def ff(v): return "%.8g" % v
def strip_alt(e):
    for x in e.iter(): x.attrib.pop("{%s}alt_encoding" % D, None)
def set_guid(cguid, g):
    b = uuid.UUID(str(g)).bytes_le
    es = cguid.findall(".//{*}UUID/{*}e")
    es[0].text, es[1].text = str(int.from_bytes(b[:8], "little")), str(int.from_bytes(b[8:], "little"))
    cguid.find("{*}DevString").text = str(g)
def renumber(root, start):
    k = "{%s}id" % D
    for e in root.iter():
        if k in e.attrib: e.attrib[k] = str(start); start += 1
def set_far(fc, m):
    t = math.floor(m / TILE); u = min(m - t * TILE, TILE - 1e-4)
    fc.find(".//{*}RouteCoordinate//{*}Distance").text = str(int(t)); fc.find(".//{*}TileCoordinate//{*}Distance").text = ff(u)
def write_xml(root, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s = etree.tostring(root, xml_declaration=True, encoding="utf-8", pretty_print=True).decode("utf-8")
    s = re.sub(r'<([\w\-:]+)((?:\s[^<>]*?)?cDeltaString[^<>]*?)\s*/>', r'<\1\2></\1>', s)  # serz veut <X ..></X>
    open(path, "w", encoding="utf-8", newline="\n").write(s)
def to_bin(xml_path, bin_path):
    os.makedirs(os.path.dirname(bin_path), exist_ok=True)
    r = subprocess.run([SERZ, xml_path, "/bin:" + bin_path], capture_output=True, text=True)
    if "Conversion complete" not in r.stdout: raise RuntimeError("serz : %s %s" % (r.stdout, r.stderr))

# ---------------------------------------------------------------- donnees SNCF
def load_tracks():
    p = os.path.join(ROOT, "GeographicData", "Raw", "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json")
    V = json.load(open(p, encoding="utf-8")); out = {}
    for code in TRACKS:
        v = [x for x in V if x["code_voie"] == code][0]
        xy = np.array([C.lonlat_to_xz(lo, la) for lo, la in shape(v["geo_shape"]["geometry"]).coords])
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
        pk0 = int(v["pk_debut_r"].split("+")[0]) + int(v["pk_debut_r"].split("+")[1]) / 1000
        out[code] = (xy, d, pk0)
    return out
def load_vmax():
    p = os.path.join(ROOT, "GeographicData", "Raw", "sncf", "vitesse-maximale-nominale-sur-ligne_420000.json")
    pk = lambda s: int(s.split("+")[0]) + int(s.split("+")[1]) / 1000
    return [(pk(r["pkd"]), pk(r["pkf"]), int(r["v_max"])) for r in json.load(open(p, encoding="utf-8")) if r["pkd"] and r["pkf"]]
def vmax_at(tab, pk):
    return next((v for a, b, v in tab if a <= pk <= b), 100)

def load_stations(pk_a, pk_b):
    """gares voyageurs de la ligne 420000 dans [pk_a, pk_b] : (nom, pk, x, z, demi-longueur de quai en m)"""
    pk = lambda s: int(s.split("+")[0]) + int(s.split("+")[1]) / 1000
    G_ = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "liste-des-gares_420000.json"), encoding="utf-8")); out = []
    for g in G_:
        if g["code_ligne"] == "420000" and g["voyageurs"] == "O" and pk_a <= pk(g["pk"]) <= pk_b:
            x, z = C.lonlat_to_xz(g["x_wgs84"], g["y_wgs84"]); big = g["libelle"] in ("Le Mans", "Nogent-le-Rotrou", "La Fert?-Bernard")
            out.append((g["libelle"], pk(g["pk"]), x, z, 200.0 if g["libelle"] == "Le Mans" else (150.0 if big else 100.0)))
    return out

# ---------------------------------------------------------------- MNT IGN (une requete par tuile, en cache)
def _wms(x0, y0, x1, y1, res=4.0):
    w, h = int(math.ceil((x1 - x0) / res)), int(math.ceil((y1 - y0) / res))
    for k in range(5):
        try:
            r = requests.get("https://data.geopf.fr/wms-r", params={"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
                "LAYERS": "ELEVATION.ELEVATIONGRIDCOVERAGE", "STYLES": "", "FORMAT": "image/x-bil;bits=32", "CRS": "EPSG:2154",
                "BBOX": "%f,%f,%f,%f" % (x0, y0, x1, y1), "WIDTH": w, "HEIGHT": h}, headers={"User-Agent": "TSC-line-project/0.1"}, timeout=120)
            r.raise_for_status()
            if len(r.content) == w * h * 4: return np.frombuffer(r.content, "<f4").reshape(h, w).copy()
        except Exception:
            if k == 4: raise
    raise RuntimeError("MNT inattendu")
def dem_tile(t):
    """altitudes du sol (128x128, ligne=Z, colonne=X) d'une tuile ; cache disque"""
    f = os.path.join(CACHE, "%+d_%+d.npy" % t)
    if os.path.exists(f): return np.load(f)
    gx = t[0] * TILE + np.arange(GRID) * CELL; gz = t[1] * TILE + np.arange(GRID) * CELL
    XX, ZZ = np.meshgrid(gx, gz)
    lon, lat = C.xz_to_lonlat(XX.ravel(), ZZ.ravel()); X, Y = TO93.transform(lon, lat)
    x0, x1, y0, y1 = X.min() - 20, X.max() + 20, Y.min() - 20, Y.max() + 20
    a = _wms(x0, y0, x1, y1); res = 4.0; h, w = a.shape
    fx = (X - x0) / res - 0.5; fy = (y0 + h * res - Y) / res - 0.5
    i0 = np.clip(np.floor(fx).astype(int), 0, w - 2); j0 = np.clip(np.floor(fy).astype(int), 0, h - 2)
    tx_, ty_ = np.clip(fx - i0, 0, 1), np.clip(fy - j0, 0, 1)
    a = np.where(a < -1000, np.nan, a)
    z = (a[j0, i0] * (1 - tx_) * (1 - ty_) + a[j0, i0 + 1] * tx_ * (1 - ty_) + a[j0 + 1, i0] * (1 - tx_) * ty_ + a[j0 + 1, i0 + 1] * tx_ * ty_)
    z = z.reshape(GRID, GRID).astype("<f4"); os.makedirs(CACHE, exist_ok=True); np.save(f, z); return z
def dem_point(xs, zs, cache):
    """altitude du sol en des points arbitraires (m) a partir des tuiles en cache"""
    out = np.empty(len(xs))
    for i, (x, z) in enumerate(zip(xs, zs)):
        t = (math.floor(x / TILE), math.floor(z / TILE)); a = cache[t]
        u = min(max((x - t[0] * TILE) / CELL, 0), GRID - 1.001); v = min(max((z - t[1] * TILE) / CELL, 0), GRID - 1.001)
        i0, j0 = int(u), int(v); fu, fv = u - i0, v - j0
        out[i] = a[j0, i0] * (1 - fu) * (1 - fv) + a[j0, i0 + 1] * fu * (1 - fv) + a[j0 + 1, i0] * (1 - fu) * fv + a[j0 + 1, i0 + 1] * fu * fv
    return out

def smooth_profile(step, z, med_m=300.0, avg_m=200.0, max_grad=0.015):
    """profil de voie : mediane + moyenne glissantes, pente limitee (la voie n'est pas le sol)"""
    def roll(a, n, f):
        n = max(3, int(n / step) | 1); p = n // 2
        ap = np.r_[np.full(p, a[0]), a, np.full(p, a[-1])]
        return np.array([f(ap[i:i + n]) for i in range(len(a))])
    z2 = roll(roll(z, med_m, np.median), avg_m, np.mean)
    for _ in range(3):
        for i in range(1, len(z2)): z2[i] = min(max(z2[i], z2[i - 1] - max_grad * step), z2[i - 1] + max_grad * step)
        for i in range(len(z2) - 2, -1, -1): z2[i] = min(max(z2[i], z2[i + 1] - max_grad * step), z2[i + 1] + max_grad * step)
    return z2

def set_bp(abs_bp, provider, product, bpid):
    abs_bp.find(".//{*}Provider").text = provider; abs_bp.find(".//{*}Product").text = product; abs_bp.find("{*}BlueprintID").text = bpid

def spans_for(segs, L):
    """travees de cat?naire le long d'un ruban : (s_debut, s_fin), plus courtes en courbe"""
    cum = np.cumsum([0.0] + [s["len"] for s in segs])
    def at(s):
        j = min(int(np.searchsorted(cum, s, side="right")) - 1, len(segs) - 1); x, z, th = pos_on(segs[j], s - cum[j]); return x, z, abs(segs[j]["k"])
    out = []; s = 0.0
    while s < L - 0.5:
        k = at(s)[2]; span = float(np.clip(math.sqrt(2.0 / max(k, 1e-6)), 20.0, 45.0)); e = min(s + span, L)
        if L - e < 12.0: e = L
        out.append((s, e, at(s)[:2], at(e)[:2])); s = e
    return out

# ---------------------------------------------------------------- courbes / tuiles
def pos_on(seg, u):
    th = math.atan2(seg["tz"], seg["tx"]); k = seg["k"]
    if k == 0: return seg["x"] + seg["tx"] * u, seg["z"] + seg["tz"] * u, th
    return seg["x"] + (math.sin(th + k * u) - math.sin(th)) / k, seg["z"] - (math.cos(th + k * u) - math.cos(th)) / k, th + k * u
def split_tiles(segs):
    out = []
    for g in segs:
        L = g["len"]; us = np.r_[np.arange(0, L, 1.0), L]; cuts = []; prev = None
        for u in us:
            x, z, _ = pos_on(g, u); key = (math.floor(x / TILE), math.floor(z / TILE))
            if prev is not None and key != prev[1]:
                lo, hi = prev[0], u
                for _ in range(40):
                    mid = (lo + hi) / 2; xm, zm, _ = pos_on(g, mid)
                    if (math.floor(xm / TILE), math.floor(zm / TILE)) == prev[1]: lo = mid
                    else: hi = mid
                cuts.append(hi)
            prev = (u, key)
        edges = [0.0] + [c for c in cuts if 1e-3 < c < L - 1e-3] + [L]
        for a, b in zip(edges, edges[1:]):
            x, z, th = pos_on(g, a)
            out.append({"type": g["type"], "x": x, "z": z, "tx": math.cos(th), "tz": math.sin(th), "len": b - a, "k": g["k"]})
    return out
def tile_of(s):
    x, z, _ = pos_on(s, s["len"] / 2); return math.floor(x / TILE), math.floor(z / TILE)

# ---------------------------------------------------------------- binaires terrain / MixMap sans serz (en-tete du jeu conserve)
def patch_tile_bin(tpl_bytes, xo, yo, tx, ty, blob_off, blob):
    b = bytearray(tpl_bytes); struct.pack_into("<i", b, xo, tx); struct.pack_into("<i", b, yo, ty)
    b[blob_off:blob_off + len(blob)] = blob; return bytes(b)

# ---------------------------------------------------------------- generation
def main(pk_a, pk_b, name):
    tr = load_tracks(); vtab = load_vmax()
    tracks = {}
    for code, (xy, d, pk0) in tr.items():
        a = np.searchsorted(d, (pk_a - pk0) * 1000); b = np.searchsorted(d, (pk_b - pk0) * 1000)
        P = xy[a:b + 1]
        segs = split_tiles(CF.fit_ls(P, straight_k=1e-7, min_len=25.0, tol=0.002, lam=4000.0)); tracks[code] = {"segs": segs, "pk0": pk_a}   # moindres carres : pas de zigzag de courbure
        rb = []
        for s in segs:
            t = tile_of(s)
            if rb and rb[-1]["tile"] == t: rb[-1]["segs"].append(s)
            else: rb.append({"tile": t, "segs": [s]})
        tracks[code]["ribbons"] = rb
        print(code, len(segs), "segments,", len(rb), "rubans")

    # tuiles terrain : tuiles de voie + 1 anneau
    vt = {r["tile"] for t in tracks.values() for r in t["ribbons"]}
    tiles = {(x + i, z + j) for x, z in vt for i in (-1, 0, 1) for j in (-1, 0, 1)}
    todo = [t for t in tiles if not os.path.exists(os.path.join(CACHE, "%+d_%+d.npy" % t))]
    print(len(tiles), "tuiles terrain,", len(todo), "MNT a telecharger")
    with ThreadPoolExecutor(6) as ex: list(ex.map(dem_tile, todo))
    cache = {t: dem_tile(t) for t in tiles}

    # profil de voie (par chainage) et points denses pour le couloir
    dense_xy, dense_z = [], []
    for code, t in tracks.items():
        pts = []
        for g in t["segs"]:
            n = max(2, int(g["len"] / 5.0) + 1)
            pts += [pos_on(g, u)[:2] for u in np.linspace(0, g["len"], n)]
        P5 = np.array(pts); s5 = np.r_[0, np.cumsum(np.hypot(*np.diff(P5, axis=0).T))]
        # re-echantillonnage regulier a 5 m
        sr = np.arange(0, s5[-1], 5.0); Pr = np.c_[np.interp(sr, s5, P5[:, 0]), np.interp(sr, s5, P5[:, 1])]
        zr = smooth_profile(5.0, dem_point(Pr[:, 0], Pr[:, 1], cache))
        t["prof"] = (sr, zr)
        dense_xy.append(Pr); dense_z.append(zr)
    # V2 reprend la hauteur de V1 quand les deux voies sont voisines (meme plateforme), fondu entre 6 et 12 m
    d12, i12 = cKDTree(dense_xy[0]).query(dense_xy[1]); w = np.clip((12.0 - d12) / 6.0, 0, 1)
    dense_z[1] = w * dense_z[0][i12] + (1 - w) * dense_z[1]; v2 = list(tracks)[1]; tracks[v2]["prof"] = (tracks[v2]["prof"][0], dense_z[1])
    dxy = np.vstack(dense_xy); dz = np.concatenate(dense_z); kd = cKDTree(dxy)

    out = os.path.join(ROOT, "Route", "Exports", name); shutil.rmtree(out, ignore_errors=True)
    stage = os.path.join(out, "_xml")
    route_guid = uuid.uuid5(uuid.NAMESPACE_URL, "tsc-line-project/" + name); rdir = os.path.join(out, str(route_guid))

    # ---- Tracks.xml
    root = etree.parse(os.path.join(TPL, "Tracks.xml")).getroot(); net = root[0][0]; rc = net[1][0]
    rib_c = rc.find("{*}Ribbon"); node_c = rc.find("{*}Node"); rib_tpl = copy.deepcopy(rib_c[0]); node1 = node2 = None
    for n in node_c:
        cons = n.findall(".//{*}Network-cNetworkNode-sRConnection"); pat = n.find(".//{*}PatternRef//{*}Pattern")
        nil = len(pat) and q(pat[0]) == "nil"
        if len(cons) == 1 and node1 is None and nil: node1 = copy.deepcopy(n)
        if len(cons) == 2 and node2 is None and nil: node2 = copy.deepcopy(n)
    for c in list(rib_c): rib_c.remove(c)
    for c in list(node_c): node_c.remove(c)
    set_guid(net.find("{*}NetworkID/{*}cGUID"), uuid.uuid5(route_guid, "network"))
    tpl_tile = etree.parse(os.path.join(TPL, "tile.xml")).getroot()
    tpl_cont = tpl_tile.find(".//{*}Network-cNetworkRibbonUnstreamed-cCurveContainerUnstreamed")
    str_tpl = copy.deepcopy([c for c in tpl_cont.find("{*}Curve") if q(c) == "cCurveStraight"][0])
    arc_tpl = copy.deepcopy([c for c in tpl_cont.find("{*}Curve") if q(c) == "cCurveArc"][0])

    def node(tpl, links):
        nd = copy.deepcopy(tpl); strip_alt(nd)
        for c, (g, end) in zip(nd.findall(".//{*}Network-cNetworkNode-sRConnection"), links):
            set_guid(c.find("{*}_id/{*}cGUID"), g); c.find("{*}_end/{*}cNormFloat/{*}Position").text = str(end)
        return nd

    tile_recs, loft_recs, pole_recs = {}, {}, {}
    loft_cat = etree.parse(os.path.join(MARS, "loft_cat.xml")).getroot(); loft_wire = etree.parse(os.path.join(MARS, "loft_wire.xml")).getroot()
    loft_net = re.search(r"DevString[^>]*>([0-9a-f\-]{36})<", open(os.path.join(TPL, "lofts.xml"), encoding="utf-8").read()).group(1)
    for code, t in tracks.items():
        sr, zr = t["prof"]; cum = 0.0; guids = []
        for ri, rb in enumerate(t["ribbons"]):
            rid = uuid.uuid5(route_guid, "%s-ribbon-%d" % (code, ri)); guids.append(rid)
            L = sum(s["len"] for s in rb["segs"])
            P2 = np.array([pos_on(s, u)[:2] for s in rb["segs"] for u in (0, s["len"] / 2, s["len"])])
            bl = P2.min(axis=0); ext = P2.max(axis=0) - bl
            ss = np.linspace(0, L, int(L / 20) + 2); zs = np.interp(cum + ss, sr, zr)
            vm = vmax_at(vtab, pk_a + (cum + L / 2) / 1000.0); cum_start = cum; cum += L
            rib = copy.deepcopy(rib_tpl); strip_alt(rib)
            rib.find("{*}_length").text = ff(L); set_guid(rib.find("{*}RibbonID/{*}cGUID"), rid)
            hc = rib.find("{*}Height"); hk = copy.deepcopy(hc[0])
            for h in list(hc): hc.remove(h)
            for sp, zz in zip(ss, zs):
                h = copy.deepcopy(hk); h.find("{*}_position").text = ff(sp); h.find("{*}_height").text = ff(float(zz)); h.find("{*}_manual").text = "0"; hc.append(h)
            rv = rib.find("{*}RouteVector")
            rv.find("{*}cRouteVector2/{*}X/{*}cRouteCoordinate/{*}Distance").text = str(math.floor(bl[0] / TILE))
            rv.find("{*}cRouteVector2/{*}Z/{*}cRouteCoordinate/{*}Distance").text = str(math.floor(bl[1] / TILE))
            rib.find("{*}RBottomLeft").text = "%s %s" % (ff(bl[0] - math.floor(bl[0] / TILE) * TILE), ff(bl[1] - math.floor(bl[1] / TILE) * TILE))
            rib.find("{*}RExtents").text = "%s %s" % (ff(ext[0]), ff(ext[1]))
            pc = rib.find(".//{*}Network-cPropertyContainer")
            for prop in pc.findall("{*}Property"):
                for inner in list(prop):
                    kind = q(inner)
                    if kind == "Network-cTrackMarkerProperty": prop.remove(inner); continue
                    if inner.find("{*}_start") is not None: inner.find("{*}_start").text = "0"; inner.find("{*}_end").text = ff(L)
                    if kind == "Network-cTrackNetworkSpeedLimit":
                        for k in ("Primary", "Secondary"): inner.find(".//{*}" + k).text = str(vm)
                    if kind == "Network-cTrackNetworkTrackRule" and TRACK_RULE:
                        tr_ = inner.find(".//{*}TrackRule")
                        for c_ in list(tr_): tr_.remove(c_)
                        ab = etree.SubElement(tr_, "iBlueprintLibrary-cAbsoluteBlueprintID"); bs = etree.SubElement(ab, "BlueprintSetID"); st = etree.SubElement(bs, "iBlueprintLibrary-cBlueprintSetID")
                        for nme, val in (("Provider", TRACK_RULE[0]), ("Product", TRACK_RULE[1])): e_ = etree.SubElement(st, nme); e_.set("{%s}type" % D, "cDeltaString"); e_.text = val
                        e_ = etree.SubElement(ab, "BlueprintID"); e_.set("{%s}type" % D, "cDeltaString"); e_.text = TRACK_RULE[2]
                    if kind == "Network-cSectionGenericProperties":
                        set_bp(inner.find("{*}BlueprintID/{*}iBlueprintLibrary-cAbsoluteBlueprintID"), *TRACK_BP)
                        set_bp(inner.find("{*}ElectrificationBlueprintID/{*}iBlueprintLibrary-cAbsoluteBlueprintID"), "", "", "")
            rib_c.append(rib)
            cont = copy.deepcopy(tpl_cont); set_guid(cont.findall(".//{*}Network-cNetworkRibbon-cCurveContainer-cID")[0].find("{*}RibbonID/{*}cGUID"), rid)
            cur = cont.find("{*}Curve")
            for c in list(cur): cur.remove(c)
            for s in rb["segs"]:
                el = copy.deepcopy(str_tpl if s["k"] == 0 else arc_tpl); strip_alt(el)
                el.find("{*}Length").text = ff(s["len"])
                set_far(el.find("{*}StartPos/{*}cFarVector2/{*}X/{*}cFarCoordinate"), s["x"]); set_far(el.find("{*}StartPos/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), s["z"])
                el.find("{*}StartTangent").text = "%.7f %.7f" % (s["tx"], s["tz"])
                if s["k"] != 0:
                    el.find("{*}Curvature").text = ff(abs(s["k"])); el.find("{*}CurveSign").text = "-1" if s["k"] > 0 else "1"
                cur.append(el)
            tile_recs.setdefault(rb["tile"], []).append(cont)
            for si, (s0, s1, p0, p1) in enumerate(spans_for(rb["segs"], L)):
                ch = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                if ch < 1.0: continue
                tx_, tz_ = (p1[0] - p0[0]) / ch, (p1[1] - p0[1]) / ch
                h0, h1 = float(np.interp(cum_start + s0, sr, zr)), float(np.interp(cum_start + s1, sr, zr))
                pole_recs.setdefault(rb["tile"], []).append((code, si, p0[0], p0[1], h0, math.atan2(tz_, tx_)))
                for k_, (tpl, dh) in enumerate(((loft_cat, H_CONTACT), (loft_wire, H_MESS))):
                    lid = uuid.uuid5(route_guid, "%s-%d-%.2f-%d" % (code, ri, s0, k_)); lr = copy.deepcopy(tpl); strip_alt(lr)
                    lr.find("{*}_length").text = ff(ch); set_guid(lr.find("{*}RibbonID/{*}cGUID"), lid)
                    hc2 = lr.find("{*}Height"); hk2 = copy.deepcopy(hc2[0])
                    for h in list(hc2): hc2.remove(h)
                    for sp, zz in ((0.0, h0 + dh), (ch, h1 + dh)):
                        h = copy.deepcopy(hk2); h.find("{*}_position").text = ff(sp); h.find("{*}_height").text = ff(zz); h.find("{*}_manual").text = "0"; hc2.append(h)
                    bx, bz = min(p0[0], p1[0]), min(p0[1], p1[1])
                    lr.find("{*}RouteVector/{*}cRouteVector2/{*}X/{*}cRouteCoordinate/{*}Distance").text = str(math.floor(bx / TILE))
                    lr.find("{*}RouteVector/{*}cRouteVector2/{*}Z/{*}cRouteCoordinate/{*}Distance").text = str(math.floor(bz / TILE))
                    lr.find("{*}RBottomLeft").text = "%s %s" % (ff(bx - math.floor(bx / TILE) * TILE), ff(bz - math.floor(bz / TILE) * TILE))
                    lr.find("{*}RExtents").text = "%s %s" % (ff(abs(p1[0] - p0[0])), ff(abs(p1[1] - p0[1])))
                    set_guid(lr.find(".//{*}Network-cNetworkRibbon-cCurveContainer-cID/{*}RibbonID/{*}cGUID"), lid)
                    cc = lr.find(".//{*}cCurveCatenary"); cc.find("{*}Length").text = ff(ch)
                    set_far(cc.find("{*}StartPos/{*}cFarVector2/{*}X/{*}cFarCoordinate"), p0[0]); set_far(cc.find("{*}StartPos/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), p0[1])
                    cc.find("{*}StartTangent").text = "%.7f %.7f" % (tx_, tz_)
                    for nme in ("StartOffsetA", "EndOffsetA"): cc.find("{*}" + nme).text = "0.0000000 0.0000000 0.0000000 0.0000000"
                    if k_ == 0:   # fil de contact : decalage (zigzag +-0,116 m, 0,32 m sous la hauteur nominale) releve sur le DLC ; le porteur reste a zero
                        sg0, sg1 = (1 if si % 2 == 0 else -1), (1 if si % 2 == 1 else -1)
                        cc.find("{*}StartOffsetB").text = "%.7f -0.3175888 %.7f 0.0000000" % (-0.0077515 * sg0, 0.1163101 * sg0)
                        cc.find("{*}EndOffsetB").text = "%.7f -0.3175888 %.7f 0.0000000" % (-0.0077515 * sg1, 0.1163101 * sg1)
                    else:
                        for nme in ("StartOffsetB", "EndOffsetB"): cc.find("{*}" + nme).text = "0.0000000 0.0000000 0.0000000 0.0000000"
                    set_guid(lr.find("{*}_parent_id/{*}cGUID"), loft_net)
                    for inner in lr.findall(".//{*}Network-cSectionGenericProperties"): inner.find("{*}_start").text = "0"; inner.find("{*}_end").text = ff(ch)
                    loft_recs.setdefault(rb["tile"], []).append(lr)
        node_c.append(node(node1, [(guids[0], 0)]))
        for i in range(len(guids) - 1): node_c.append(node(node2, [(guids[i], 1), (guids[i + 1], 0)]))
        node_c.append(node(node1, [(guids[-1], 1)]))
    renumber(root, 800000000)
    write_xml(root, os.path.join(stage, "Tracks.xml")); to_bin(os.path.join(stage, "Tracks.xml"), os.path.join(rdir, "Networks", "Tracks.bin"))

    def conv_tile(item):
        (tx, tz), conts = item
        doc = copy.deepcopy(tpl_tile); rec = doc.find("{*}Record")
        for c in list(rec): rec.remove(c)
        for cont in conts: rec.append(cont)
        renumber(doc, 810000000); nm = C.tile_name(tx, tz)
        write_xml(doc, os.path.join(stage, "tt", nm + ".xml")); to_bin(os.path.join(stage, "tt", nm + ".xml"), os.path.join(rdir, "Networks", "Track Tiles", nm + ".bin"))
    with ThreadPoolExecutor(6) as ex: list(ex.map(conv_tile, tile_recs.items()))
    # ---- quais (gares) : lofts de l'auteur Armand (assets fournis par l'utilisateur, dependance externe) paralleles a chaque voie, cote exterieur.
    # Section en travers : sommet a y=0, corps jusqu'a y=-1,25 m, largeur centree sur l'axe du ruban -> axe a (1,67 + largeur/2) m de la voie, sommet a +0,55 m.
    QUAI_W = {"QuaiAIX": 3.0, "QuaiArc": 4.0, "QuaiBourk": 3.05, "QuaiMcd": 2.5, "QuaiMetz": 3.0, "QuaiMorez": 5.0, "QuaiPLM": 2.5, "QuaiRev": 4.0}
    PLT_PROD = os.environ.get("PLT_PROD", "QuaiPLM"); STATION_PROD = {"Nogent-le-Rotrou": "QuaiRev", "Le Mans": "QuaiRev"}   # choix utilisateur : Rev (4 m) aux deux grandes gares, PLM (2,5 m) ailleurs
    PLT_TOP = 0.55; PLT_EDGE = 1.67; n_plat = 0
    pl_str = etree.parse(os.path.join(MARS, "pltfm_str.xml")).getroot(); pl_arc = etree.parse(os.path.join(MARS, "pltfm_arc.xml")).getroot()
    c_str = copy.deepcopy(pl_str.find(".//{*}Curve")[0]); c_arc = copy.deepcopy(pl_arc.find(".//{*}Curve")[0]); used_prod = set()
    def plat(i, code, a_, b_, outer, prod, tag):
        nonlocal n_plat
        Pr, zr = dense_xy[i], dense_z[i]; wdt = QUAI_W[prod]; used_prod.add(prod)
        seg = Pr[a_:b_ + 1]; zs = zr[a_:b_ + 1]
        tv = Pr[a_ + 1:b_ + 2] - Pr[a_ - 1:b_]; tv = tv / np.hypot(tv[:, 0], tv[:, 1])[:, None]; nv = np.c_[-tv[:, 1], tv[:, 0]]
        P_off = seg + outer * (PLT_EDGE + wdt / 2) * nv
        segs_p = split_tiles(CF.fit_ls(P_off, straight_k=1e-7, min_len=25.0, tol=0.002, lam=4000.0)); grp = []
        for s_ in segs_p:
            t_ = tile_of(s_)
            if grp and grp[-1][0] == t_: grp[-1][1].append(s_)
            else: grp.append((t_, [s_]))
        Ltot = sum(s_["len"] for s_ in segs_p); cum_p = 0.0
        for gi, (tl, ss_) in enumerate(grp):
            Lr = sum(s_["len"] for s_ in ss_); lid = uuid.uuid5(route_guid, "quai-%s-%s-%d" % (tag, code, gi)); lr = copy.deepcopy(pl_str); strip_alt(lr)
            lr.find("{*}_length").text = ff(Lr); set_guid(lr.find("{*}RibbonID/{*}cGUID"), lid)
            hc3 = lr.find("{*}Height"); hk3 = copy.deepcopy(hc3[0])
            for h in list(hc3): hc3.remove(h)
            for sp in np.r_[np.arange(0, Lr, 25.0), Lr]:
                h = copy.deepcopy(hk3); h.find("{*}_position").text = ff(sp); h.find("{*}_height").text = ff(float(np.interp((cum_p + sp) / max(Ltot, 1e-6), np.linspace(0, 1, len(zs)), zs)) + PLT_TOP); h.find("{*}_manual").text = "0"; hc3.append(h)
            B_ = np.array([pos_on(s_, u_)[:2] for s_ in ss_ for u_ in (0, s_["len"] / 2, s_["len"])]); bl = B_.min(axis=0); ex_ = B_.max(axis=0) - bl
            lr.find("{*}RouteVector/{*}cRouteVector2/{*}X/{*}cRouteCoordinate/{*}Distance").text = str(math.floor(bl[0] / TILE)); lr.find("{*}RouteVector/{*}cRouteVector2/{*}Z/{*}cRouteCoordinate/{*}Distance").text = str(math.floor(bl[1] / TILE))
            lr.find("{*}RBottomLeft").text = "%s %s" % (ff(bl[0] - math.floor(bl[0] / TILE) * TILE), ff(bl[1] - math.floor(bl[1] / TILE) * TILE)); lr.find("{*}RExtents").text = "%s %s" % (ff(ex_[0]), ff(ex_[1]))
            set_guid(lr.find(".//{*}Network-cNetworkRibbon-cCurveContainer-cID/{*}RibbonID/{*}cGUID"), lid)
            cur_ = lr.find(".//{*}Curve")
            for c_ in list(cur_): cur_.remove(c_)
            for s_ in ss_:
                el = copy.deepcopy(c_str if s_["k"] == 0 else c_arc); strip_alt(el); el.find("{*}Length").text = ff(s_["len"])
                set_far(el.find("{*}StartPos/{*}cFarVector2/{*}X/{*}cFarCoordinate"), s_["x"]); set_far(el.find("{*}StartPos/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), s_["z"])
                el.find("{*}StartTangent").text = "%.7f %.7f" % (s_["tx"], s_["tz"])
                if s_["k"] != 0: el.find("{*}Curvature").text = ff(abs(s_["k"])); el.find("{*}CurveSign").text = "-1" if s_["k"] > 0 else "1"
                cur_.append(el)
            set_guid(lr.find("{*}_parent_id/{*}cGUID"), loft_net)
            for inner in lr.findall(".//{*}Network-cSectionGenericProperties"):
                inner.find("{*}_start").text = "0"; inner.find("{*}_end").text = ff(Lr); set_bp(inner.find("{*}BlueprintID/{*}iBlueprintLibrary-cAbsoluteBlueprintID"), "Armand", prod, "Loft section blueprint1.xml")
            loft_recs.setdefault(tl, []).append(lr); cum_p += Lr; n_plat += 1
    def outer_side(i, j):
        Pr = dense_xy[i]; dd, jj = cKDTree(dense_xy[1 - i]).query(Pr[j]); t_ = Pr[min(j + 1, len(Pr) - 1)] - Pr[max(j - 1, 0)]; t_ = t_ / np.hypot(*t_)
        if dd < 15.0: wv = dense_xy[1 - i][jj] - Pr[j]; return -1.0 if (t_[0] * wv[1] - t_[1] * wv[0]) > 0 else 1.0
        return 1.0 if i == 0 else -1.0
    if os.environ.get("PLT_TEST"):   # banc d'essai : tous les modeles de quai l'un apres l'autre (50 m + 12 m) le long de V1, a partir de l'origine
        j0 = int(np.argmin(np.hypot(dense_xy[0][:, 0], dense_xy[0][:, 1]))); step = int(62 / 5)
        for n_, prod in enumerate(sorted(QUAI_W)):
            a_ = j0 + n_ * step; plat(0, list(tracks)[0], a_, a_ + int(50 / 5), outer_side(0, a_), prod, "test-" + prod)
    else:
        for (sname, spk, sx, sz, half) in load_stations(pk_a, pk_b):
            for i, code in enumerate(tracks):
                Pr = dense_xy[i]; j = int(np.argmin(np.hypot(Pr[:, 0] - sx, Pr[:, 1] - sz)))
                plat(i, code, max(j - int(half / 5), 1), min(j + int(half / 5), len(Pr) - 2), outer_side(i, j), STATION_PROD.get(sname, PLT_PROD), sname)
    print(n_plat, "rubans de quai")
    for prod in sorted(used_prod): PRELOAD.append(("Armand", prod))
    skel = etree.parse(os.path.join(MARS, "loft_container.xml")).getroot()
    loft_node = etree.parse(os.path.join(MARS, "loft_node.xml")).getroot()
    def conv_loft(item):
        (tx, tz), lrs = item
        doc = copy.deepcopy(skel); rc2 = doc.find(".//{*}Network-cRibbonContainerStreamed/{*}Ribbon")
        nc2 = doc.find(".//{*}Network-cRibbonContainerStreamed/{*}Node")
        for lr in lrs:
            rc2.append(lr); rid_ = lr.find("{*}RibbonID/{*}cGUID")
            for end in (0, 1):   # le DLC relie chaque travee par deux noeuds a une connexion (sinon le jeu ignore le ruban)
                nd = copy.deepcopy(loft_node); strip_alt(nd)
                set_guid(nd.find(".//{*}Network-cNetworkNode-sRConnection/{*}_id/{*}cGUID"), rid_.find("{*}DevString").text)
                nd.find(".//{*}_end/{*}cNormFloat/{*}Position").text = str(end)
                nd.find("{*}RouteVector/{*}cRouteVector2/{*}X/{*}cRouteCoordinate/{*}Distance").text = str(tx)
                nd.find("{*}RouteVector/{*}cRouteVector2/{*}Z/{*}cRouteCoordinate/{*}Distance").text = str(tz)
                nc2.append(nd)
        renumber(doc, 820000000); nm = C.tile_name(tx, tz)
        write_xml(doc, os.path.join(stage, "loft", nm + ".xml")); to_bin(os.path.join(stage, "loft", nm + ".xml"), os.path.join(rdir, "Networks", "Loft Tiles", nm + ".bin"))
    with ThreadPoolExecutor(6) as ex: list(ex.map(conv_loft, loft_recs.items()))

    # ---- poteaux : entites de Scenery (Pull/Push alternes, a gauche de V1, a droite de V2), base a la hauteur de voie
    sc_skel = etree.parse(os.path.join(MARS, "scenery_container.xml")).getroot()
    POLE_KIND = os.environ.get("POLE_KIND", "single"); ORI = float(os.environ.get("ORI_FLIP", "-1"))   # single : poteau d'axe (origine sur la voie, comme le DLC ; ORI_FLIP=-1 valide en jeu le 2026-11-07) ; med : poteau median ? H ? (deux montants)
    pre_ = "pole1_" if POLE_KIND == "single" else "pole_"
    pole_tpl = {"Pull": etree.parse(os.path.join(MARS, pre_ + "Pull.xml")).getroot(), "Push": etree.parse(os.path.join(MARS, pre_ + "Push.xml")).getroot()}
    POLE_D = float(os.environ.get("POLE_D", "2.8"))   # distance axe de voie -> poteau (DLC : 2,0 a 3,4 m) ; poteaux a l'exterieur des deux voies (V1 a gauche, V2 a droite)
    by_tile = {}
    kd_other = {code: cKDTree(dense_xy[1 - i]) for i, code in enumerate(tracks)}   # voie voisine : le poteau se met du cote oppose (V1/V2 s'inversent dans les gares)
    other_xy = {code: dense_xy[1 - i] for i, code in enumerate(tracks)}
    for plist in pole_recs.values():
        for (code, si, x, z, h, phi) in plist:
            nx, nz = -math.sin(phi), math.cos(phi)
            dd, jj = kd_other[code].query((x, z)); left = code.endswith("V1")
            if dd < 15.0:
                wx, wz = other_xy[code][jj][0] - x, other_xy[code][jj][1] - z
                left = (math.cos(phi) * wz - math.sin(phi) * wx) < 0   # voisine a droite -> poteau a gauche
            if POLE_KIND == "single":   # origine sur l'axe : le cote du poteau est porte par l'orientation du modele
                by_tile.setdefault((math.floor(x / TILE), math.floor(z / TILE)), []).append((code, si, x, z, h, phi + ORI * (math.pi / 2 if left else -math.pi / 2))); continue
            px, pz = (x + POLE_D * nx, z + POLE_D * nz) if left else (x - POLE_D * nx, z - POLE_D * nz)
            # l'axe +X de l'objet doit pointer vers la voie (releve sur les poteaux ? HPost Med ? du DLC)
            by_tile.setdefault((math.floor(px / TILE), math.floor(pz / TILE)), []).append((code, si, px, pz, h, phi - math.pi / 2 if left else phi + math.pi / 2))
    # objets de decor (batiments, panneaux...) : Route/Configuration/objects.json ; position par PK de V1 + decalage lateral (gauche > 0) + cap relatif
    obj_by_tile = {}; obj_tpl = None
    ofile = os.path.join(ROOT, "Route", "Configuration", "objects.json")
    if os.path.exists(ofile) and os.path.exists(os.path.join(MARS, "obj_template.xml")):
        obj_tpl = etree.parse(os.path.join(MARS, "obj_template.xml")).getroot()
        for ob in json.load(open(ofile, encoding="utf-8-sig")):
            if not (pk_a <= ob["pk"] <= pk_b): continue
            Pr, zr = dense_xy[0], dense_z[0]; sr0 = tracks[list(tracks)[0]]["prof"][0]
            # PK -> point de V1 : distance cumulee le long de la voie ajustee depuis pk_a
            idx = min(max(int((ob["pk"] - pk_a) * 1000 / 5.0), 1), len(Pr) - 2)
            tv_ = Pr[idx + 1] - Pr[idx - 1]; tv_ = tv_ / np.hypot(*tv_); nv_ = np.array([-tv_[1], tv_[0]]); phi_ = math.atan2(tv_[1], tv_[0])
            px_, pz_ = Pr[idx] + ob.get("lateral", 0.0) * nv_
            psi_ = phi_ + math.radians(ob.get("heading_deg", 0.0))
            obj_by_tile.setdefault((math.floor(px_ / TILE), math.floor(pz_ / TILE)), []).append((ob, px_, pz_, float(zr[idx]) + ob.get("dz", 0.0), psi_))
    for k_ in obj_by_tile: by_tile.setdefault(k_, [])
    def conv_scen(item):
        (tx, tz), poles = item
        doc = copy.deepcopy(sc_skel); rec_ = doc[0]
        for (ob, x, z, h, psi) in obj_by_tile.get((tx, tz), []):
            ent = copy.deepcopy(obj_tpl); strip_alt(ent); prov, prod, bid = ob["blueprint"]
            ab = ent.find("{*}BlueprintID/{*}iBlueprintLibrary-cAbsoluteBlueprintID"); set_bp(ab, prov, prod, bid)
            m = ent.find(".//{*}cFarMatrix"); m.find("{*}Height").text = ff(h)
            m.find("{*}RXAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (math.cos(psi), math.sin(psi)); m.find("{*}RYAxis").text = "0.0000000 1.0000000 0.0000000 0.0000000"; m.find("{*}RZAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (-math.sin(psi), math.cos(psi))
            set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}X/{*}cFarCoordinate"), x); set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), z)
            key = "obj-%s-%.2f-%.2f" % (bid, x, z); set_guid(ent.find("{*}EntityID/{*}cGUID"), uuid.uuid5(route_guid, key))
            nm_ = ent.find("{*}Name")
            if nm_ is not None: nm_.text = ob.get("name", bid)
            rec_.append(ent)
            if prov + "/" + prod not in [a + "/" + b for a, b in PRELOAD]: PRELOAD.append((prov, prod))
        for (code, si, x, z, h, psi) in poles:
            ent = copy.deepcopy(pole_tpl["Pull" if si % 2 == 0 else "Push"]); strip_alt(ent)
            m = ent.find(".//{*}cFarMatrix"); m.find("{*}Height").text = ff(h)
            m.find("{*}RXAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (math.cos(psi), math.sin(psi))
            m.find("{*}RYAxis").text = "0.0000000 1.0000000 0.0000000 0.0000000"
            m.find("{*}RZAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (-math.sin(psi), math.cos(psi))
            set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}X/{*}cFarCoordinate"), x); set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), z)
            key = "%s-%.2f-%.2f" % (code, x, z)
            set_guid(ent.find(".//{*}Network-cGantryComponent/{*}GUID/{*}cGUID"), uuid.uuid5(route_guid, "g" + key)); set_guid(ent.find("{*}EntityID/{*}cGUID"), uuid.uuid5(route_guid, "e" + key))
            rec_.append(ent)
        renumber(doc, 840000000); nm = C.tile_name(tx, tz)
        write_xml(doc, os.path.join(stage, "scen", nm + ".xml")); to_bin(os.path.join(stage, "scen", nm + ".xml"), os.path.join(rdir, "Scenery", nm + ".bin"))
    with ThreadPoolExecutor(6) as ex: list(ex.map(conv_scen, by_tile.items()))

    # ---- terrain + MixMap : patch binaire direct des modeles du jeu (pas de serz)
    ter_tpl = open(os.path.join(TPL, "extracted", "Terrain", "+000000+000000.bin"), "rb").read()
    mix_tpl = open(os.path.join(TPL, "extracted", "MixMap", "+000000+000000.bin"), "rb").read()
    os.makedirs(os.path.join(rdir, "Terrain"), exist_ok=True); os.makedirs(os.path.join(rdir, "MixMap"), exist_ok=True)
    def conv_ter(t):
        tx, tz = t; H = cache[t].copy()
        H = np.nan_to_num(H, nan=float(np.nanmean(H)) if np.isfinite(np.nanmean(H)) else 0.0)
        gx = tx * TILE + np.arange(GRID) * CELL; gz = tz * TILE + np.arange(GRID) * CELL
        XX, ZZ = np.meshgrid(gx, gz); dist, idx = kd.query(np.c_[XX.ravel(), ZZ.ravel()], distance_upper_bound=14.0)
        ok = np.isfinite(dist); th = np.where(ok, dz[np.minimum(idx, len(dz) - 1)], 0).reshape(GRID, GRID); dist = np.where(ok, dist, 99.0).reshape(GRID, GRID)
        w = np.clip((14.0 - dist) / 9.0, 0, 1)   # 1 jusqu'a 5 m de l'axe, 0 a 14 m
        H = np.where(dist < 14.0, H * (1 - w) + (th - 0.25) * w, H).astype("<f4")
        nm = C.tile_name(tx, tz)
        open(os.path.join(rdir, "Terrain", nm + ".bin"), "wb").write(patch_tile_bin(ter_tpl, 116, 131, tx, tz, len(ter_tpl) - 12 - 65536, H.tobytes()))
        open(os.path.join(rdir, "MixMap", nm + ".bin"), "wb").write(patch_tile_bin(mix_tpl, 111, 130, tx, tz, len(mix_tpl) - 12 - 98304, mix_tpl[len(mix_tpl) - 12 - 98304:len(mix_tpl) - 12]))
    with ThreadPoolExecutor(6) as ex: list(ex.map(conv_ter, sorted(tiles)))

    # ---- fichiers generaux
    os.makedirs(os.path.join(rdir, "Networks"), exist_ok=True)
    for f in ("Lofts.bin", "Roads.bin"): shutil.copy(os.path.join(TPL, "extracted", "Networks", f), os.path.join(rdir, "Networks", f))
    shutil.copytree(os.path.join(TPL, "extracted", "RouteInformation"), os.path.join(rdir, "RouteInformation"))
    for f in os.listdir(os.path.join(TPL, "extracted")):
        if f.endswith(".lan"): shutil.copy(os.path.join(TPL, "extracted", f), rdir)
    r = etree.parse(os.path.join(MARS if os.environ.get("ROUTE_BASE", "dlc") == "dlc" else TPL, "RouteProperties.xml")).getroot()   # ROUTE_BASE=dlc (defaut, valide en jeu) : modele de route du DLC ; ROUTE_BASE=testtrak pour les essais (ciel, meteo, terrain, preload DTG)
    set_guid(r.find("{*}ID/{*}cGUID"), route_guid); r.find(".//{*}DisplayName//{*}English").text = name
    o = r.find(".//{*}Origin"); o.find(".//{*}Lat").text = "%.4f" % C.LAT0; o.find(".//{*}Long").text = "%.4f" % C.LON0; strip_alt(o)
    pre = r.find(".//{*}RBlueprintSetPreLoad")   # "Object Set Filter" : produits dont les blueprints sont charges par l'editeur
    have = {(e_.find("{*}Provider").text, e_.find("{*}Product").text) for e_ in pre}
    for prov, prod in PRELOAD:
        if (prov, prod) in have: continue
        e_ = copy.deepcopy(pre[0]); e_.find("{*}Provider").text, e_.find("{*}Product").text = prov, prod; pre.append(e_); have.add((prov, prod))
    renumber(r, 830000000)
    write_xml(r, os.path.join(rdir, "RouteProperties.xml"))
    summ = {"travees_cat": sum(len(v) for v in loft_recs.values()), "poteaux": sum(len(v) for v in pole_recs.values()), "route_guid": str(route_guid), "pk": [pk_a, pk_b], "voies": {k: len(v["ribbons"]) for k, v in tracks.items()}, "tuiles_voie": len(tile_recs), "tuiles_terrain": len(tiles)}
    json.dump(summ, open(os.path.join(out, "summary.json"), "w"), indent=1); print(json.dumps(summ)); print("route :", rdir)

if __name__ == "__main__":
    main(float(sys.argv[1]), float(sys.argv[2]), sys.argv[3])
