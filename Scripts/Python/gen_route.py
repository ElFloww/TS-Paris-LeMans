"""Generateur de route TSC a partir des voies officielles SNCF V1/V2 (ligne 420000).

Usage : python gen_route.py <pk_debut> <pk_fin> <nom>
Sortie : Route/Exports/<nom>/<GUID>/ (route "libre", pretes a copier dans Content/Routes).
Modeles (non versionnes) : copie de la route TestTraK dans Tests/Phase1/serz_test/.
Valide en jeu (2026-11-07) : voies + terrain + MixMap sur 2 km. Le reste est a valider (voir history.md).
"""
import sys, os, re, json, math, copy, uuid, shutil, subprocess, struct, collections
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import requests
from lxml import etree
from scipy.spatial import cKDTree
from shapely.geometry import shape, LineString, Point
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tsc_coords as C
import curvefit as CF
import netbuild as NB

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
            d_ = {"type": g["type"], "x": x, "z": z, "tx": math.cos(th), "tz": math.sin(th), "len": b - a, "k": g["k"]}
            if a == 0.0 and "cut" in g: d_["cut"] = g["cut"]
            out.append(d_)
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
    polys = {}
    for code, (xy, d, pk0) in tr.items():
        a = np.searchsorted(d, (pk_a - pk0) * 1000); b = np.searchsorted(d, (pk_b - pk0) * 1000); polys[code] = {"xy": xy[a:b + 1]}
    # voies supplementaires (hors V1/V2) : SNCF VPA + BD TOPO + OSM (extra_tracks.py), rognees a la plage de PK ; sans catenaire si non electrifiees
    if not os.environ.get("NO_EXTRA"):
        import extra_tracks as ET
        v1xy, v1d, v1pk0 = tr[TRACKS[0]]; v1l = LineString(v1xy)
        for e in json.load(open(os.path.join(ROOT, "GeographicData", "Processed", "extra_tracks_phase1.json"), encoding="utf-8")):   # produit par extra_tracks.py
            P = np.array(e["xy"]); sv = np.array([v1l.project(Point(*q)) for q in P]) / 1000.0 + v1pk0
            keep = (sv >= pk_a) & (sv <= pk_b)
            if keep.sum() < 2: continue
            idx = np.where(keep)[0]; P = P[idx[0]:idx[-1] + 1]; zz = np.array(e["z"])[idx[0]:idx[-1] + 1] if "z" in e else None
            if len(P) < 2 or np.hypot(*np.diff(P[[0, -1]], axis=0)[0]) < 20: continue
            if len(P) == 2: P = np.array([P[0], (P[0] + P[1]) / 2, P[1]]); zz = np.array([zz[0], (zz[0] + zz[1]) / 2, zz[1]]) if zz is not None else None
            polys[e["id"]] = {"xy": P, "z": zz, "extra": True, "elec": e["elec"], "zsrc": bool(zz is not None and e["nature"] == "LGV"), "nature": e["nature"]}
    main_ids = list(TRACKS)
    conns = NB.find_connections({k: v["xy"] for k, v in polys.items()}, set(main_ids)) if len(polys) > 2 else []
    # altitude : deux voies ne se raccordent que si elles sont a la meme hauteur (2 m) ; sinon l'une passe au-dessus de l'autre (saut-de-mouton de Connerre)
    cl_p, cl_z = [], []
    for f_ in json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "bdtopo_voies_phase1.json"), encoding="utf-8"))["features"]:
        if f_["properties"]["nature"].startswith("Voie ferr") and f_["properties"]["nombre_de_voies"] == 2:
            for c_ in f_["geometry"]["coordinates"]: cl_p.append(C.lonlat_to_xz(*c_[:2])); cl_z.append(c_[2])
    zx_p = [q_ for v_ in polys.values() if v_.get("z") is not None for q_ in v_["xy"]]; zx_z = [z_ for v_ in polys.values() if v_.get("z") is not None for z_ in v_["z"]]
    kdc = cKDTree(np.array(cl_p)) if cl_p else None; kdx = cKDTree(np.array(zx_p)) if zx_p else None
    def z_ext(c_):   # altitude BD TOPO au point de raccord : (branche, hote), None si inconnue
        own = polys[c_["branch"]].get("z"); h_ = polys[c_["host"]]
        zb_ = float(own[0 if c_["end"] == 0 else -1]) if own is not None else (lambda r_: float(zx_z[r_[1]]) if r_[0] < 6 else None)(kdx.query(c_["p"])) if kdx else None
        if h_.get("z") is not None: zh_ = float(h_["z"][int(np.argmin(np.hypot(*(h_["xy"] - c_["p"]).T)))])
        elif c_["host"] in main_ids: zh_ = (lambda r_: float(cl_z[r_[1]]) if r_[0] < 12 else None)(kdc.query(c_["p"])) if kdc else None
        else: zh_ = None
        return zb_, zh_
    n0_ = len(conns); conns = [c_ for c_ in conns if not (lambda z_: z_[0] is not None and z_[1] is not None and abs(z_[0] - z_[1]) > 2.0)(z_ext(c_))]
    print(n0_ - len(conns), "raccords refuses : voies a des altitudes differentes (franchissements)")
    order = NB.processing_order(list(polys), main_ids, conns)
    fitted, links, cuts, cid_n, terr, perr, free_end = {}, {c: {} for c in polys}, {c: [] for c in polys}, 0, [], [], []
    for code in order:
        pe = polys[code]; P = pe["xy"]; mine = [c for c in conns if c["branch"] == code and c["host"] in fitted]
        if mine and {c["end"] for c in mine} == {1}:   # un seul bout raccorde et c'est la fin : on retourne la voie pour que le raccord soit au debut
            P = P[::-1].copy(); pe["z"] = pe["z"][::-1].copy() if pe.get("z") is not None else None
            for c in mine: c["end"] = 0
        pe["xy0"] = P.copy(); t_start = t_end = None; P_pre1 = None
        for c in sorted(mine, key=lambda c_: c_["end"]):
            F = fitted[c["host"]]; hP = polys[c["host"]]["xy"]; hl = LineString(hP); sg = 1.0
            if c["kind"] == "END":
                he = 0 if np.hypot(*(c["p"] - hP[0])) < np.hypot(*(c["p"] - hP[-1])) else 1; s_h = 0.0 if he == 0 else F.L
                x_, z_, th_ = F.at(s_h); H = np.array([x_, z_]); t = np.array([math.cos(th_), math.sin(th_)]); u_ex = -t if he == 0 else t
            else:
                he = None; s_g = hl.project(Point(*c["p"])) * F.L / max(hl.length, 1.0)
                s_h, H, th_, dd = F.locate(c["p"], s_g); H = np.array(H); t = np.array([math.cos(th_), math.sin(th_)]); sg = 1.0 if float(c["u"] @ t) >= 0 else -1.0; u_ex = sg * t
                if s_h < 4.0 or F.L - s_h < 4.0 or any(abs(s_h - q) < 4.0 for q, _ in cuts[c["host"]]): continue   # trop pres d'un bout ou d'un autre aiguillage : extremite libre
                cuts[c["host"]].append((s_h, cid_n))
            if c["end"] == 0: P, _ = NB.lead_in(P, H, u_ex); t_start = math.atan2(u_ex[1], u_ex[0])
            else: P_pre1 = P.copy(); Pr, _ = NB.lead_in(P[::-1], H, u_ex); P = Pr[::-1]; t_end = math.atan2(-u_ex[1], -u_ex[0])
            links[code][c["end"]] = {"kind": c["kind"], "host": c["host"], "cid": cid_n, "fwd": sg > 0, "host_end": he, "s_host": s_h, "xy": H, "th": math.atan2(t[1], t[0])}
            if c["kind"] == "END": links[c["host"]][he] = {"kind": "PEER"}
            cid_n += 1
        pe["xy"] = P
        Lp_ = float(np.hypot(*np.diff(P, axis=0).T).sum()); ml_ = max(6.0, min(25.0, 0.12 * Lp_)); sg_m = max(2.0, min(20.0, 0.1 * Lp_))   # voies courtes (S de communication) : segments plus courts
        segs = CF.fit_ls(P, straight_k=1e-7, min_len=ml_, tol=0.002, lam=4000.0, t_start=t_start, t_end=t_end, sigma_m=sg_m)   # moindres carres : pas de zigzag de courbure
        if t_start is not None: terr.append((abs((math.atan2(segs[0]["tz"], segs[0]["tx"]) - t_start + math.pi) % (2 * math.pi) - math.pi), code))
        if t_end is not None: _, _, th_e = NB.pos_on(segs[-1], segs[-1]["len"]); terr.append((abs((th_e - t_end + math.pi) % (2 * math.pi) - math.pi), code))
        F_ = NB.Fitted(segs); xe, ze, _ = F_.at(F_.L)
        if t_end is not None and (np.hypot(xe - P[-1][0], ze - P[-1][1]) > 0.3 or abs((NB.pos_on(segs[-1], segs[-1]["len"])[2] - t_end + math.pi) % (2 * math.pi) - math.pi) > math.radians(6.0)):   # les deux tangentes imposees sont incompatibles (S plus serre que 60 m) : le bout 1 reste libre
            lk = links[code].pop(1)
            if lk["kind"] == "END": links[lk["host"]].pop(lk["host_end"], None)
            else: cuts[lk["host"]] = [c_ for c_ in cuts[lk["host"]] if c_[1] != lk["cid"]]
            P = P_pre1; t_end = None; free_end.append(code); Lp_ = float(np.hypot(*np.diff(P, axis=0).T).sum()); ml_ = max(6.0, min(25.0, 0.12 * Lp_)); sg_m = max(2.0, min(20.0, 0.1 * Lp_))
            segs = CF.fit_ls(P, straight_k=1e-7, min_len=ml_, tol=0.002, lam=4000.0, t_start=t_start, sigma_m=sg_m); F_ = NB.Fitted(segs); xe, ze, _ = F_.at(F_.L); pe["xy"] = P
        if os.environ.get("DBG_TRACK") == code: np.save(os.path.join(os.environ["TEMP"], "dbg_P.npy"), P); np.save(os.path.join(os.environ["TEMP"], "dbg_fit.npy"), np.array([F_.at(s_)[:2] for s_ in np.arange(0, F_.L, 1.0)])); np.save(os.path.join(os.environ["TEMP"], "dbg_raw.npy"), pe["xy0"]); print("DBG", code, {e_: {k_: (v_.tolist() if hasattr(v_, "tolist") else v_) for k_, v_ in l_.items()} for e_, l_ in links[code].items()}, t_start, t_end)
        fitted[code] = F_; perr.append((float(np.hypot(xe - P[-1][0], ze - P[-1][1])) if any(e__ == 1 for e__ in links[code]) else 0.0, code))
    print(len(free_end), "raccords impossibles laisses libres :", free_end[:6]); print("ecart de position en fin de voie raccordee : max %.2f m" % max([e for e, _ in perr] + [0]), sorted([(round(e, 2), c, int(LineString(polys[c]["xy"]).length), sum(1 for l_ in links[c].values() if l_.get("kind") in ("T", "END"))) for e, c in perr if e > 0.3], reverse=True)[:12])
    tracks = {}
    for code in order:
        segs = split_tiles(NB.cut_segs(fitted[code].segs, cuts[code])); pe = polys[code]
        rb = []
        for sg_ in segs:
            tl = tile_of(sg_)
            if rb and rb[-1]["tile"] == tl and "cut" not in sg_: rb[-1]["segs"].append(sg_)
            else: rb.append({"tile": tl, "segs": [sg_]})
        tracks[code] = {"segs": segs, "pk0": pk_a, "ribbons": rb, "extra": pe.get("extra", False), "elec": pe.get("elec", True)}
    n_t = sum(1 for lk in links.values() for v in lk.values() if v.get("kind") == "T"); n_e = sum(1 for lk in links.values() for v in lk.values() if v.get("kind") == "END")
    print(len(tracks), "voies,", sum(len(t["ribbons"]) for t in tracks.values()), "rubans,", n_t, "aiguillages,", n_e, "jonctions bout a bout ; ecart de cap au depart des voies deviees : max %.2f deg" % (math.degrees(max(e for e, _ in terr)) if terr else 0) + str([(round(math.degrees(e), 1), c, int(LineString(polys[c]["xy"]).length)) for e, c in sorted(terr, reverse=True)[:6]]))

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
        pe = polys[code]
        if pe.get("zsrc"):   # voie a altitude BD TOPO (raccordement LGV, saut-de-mouton) : on garde son relief propre, pente max 3,5 %
            l0 = LineString(pe["xy0"]); c0 = np.r_[0, np.cumsum(np.hypot(*np.diff(pe["xy0"], axis=0).T))]
            zr = smooth_profile(5.0, np.interp([l0.project(Point(*q)) for q in Pr], c0, pe["z"]), med_m=40.0, avg_m=40.0, max_grad=0.035)
        else: zr = smooth_profile(5.0, dem_point(Pr[:, 0], Pr[:, 1], cache))
        t["prof"] = (sr, zr)
        dense_xy.append(Pr); dense_z.append(zr)
    # V2 reprend la hauteur de V1 quand les deux voies sont voisines (meme plateforme), fondu entre 6 et 12 m
    d12, i12 = cKDTree(dense_xy[0]).query(dense_xy[1]); w = np.clip((12.0 - d12) / 6.0, 0, 1)
    dense_z[1] = w * dense_z[0][i12] + (1 - w) * dense_z[1]; v2 = list(tracks)[1]; tracks[v2]["prof"] = (tracks[v2]["prof"][0], dense_z[1])
    kdV = cKDTree(np.vstack(dense_xy[:2])); zV = np.concatenate(dense_z[:2]); prev_xy = list(dense_xy[:2]); prev_z = list(dense_z[:2])
    for i_, code in enumerate(tracks):   # voies voisines (< 12 m) : meme plateforme, meme hauteur que la voie deja calee la plus proche (fondu 6-12 m)
        if i_ < 2 or polys[code].get("zsrc"): continue
        kdp = cKDTree(np.vstack(prev_xy)); zp = np.concatenate(prev_z)
        dm, im = kdp.query(dense_xy[i_]); w = np.clip((12.0 - dm) / 6.0, 0, 1); dense_z[i_] = w * zp[im] + (1 - w) * dense_z[i_]
        tracks[code]["prof"] = (tracks[code]["prof"][0], dense_z[i_]); prev_xy.append(dense_xy[i_]); prev_z.append(dense_z[i_])
    # raccords : a chaque aiguillage / jonction la voie rejoint exactement la hauteur de la voie mere, correction estompee sur 120 m
    for i_, code in enumerate(tracks):
        sr_, zr_ = tracks[code]["prof"]; Lr = sr_[-1]; dl = {}
        for e_, lk in links[code].items():
            if lk.get("kind") not in ("T", "END"): continue
            sr_h, zr_h = tracks[lk["host"]]["prof"]; z_h = float(np.interp(lk["s_host"] if lk["kind"] == "T" else (0.0 if lk["host_end"] == 0 else sr_h[-1]), sr_h, zr_h))
            dl[e_] = z_h - float(np.interp(0.0 if e_ == 0 else Lr, sr_, zr_))
        if len(dl) == 2 and Lr < 240.0: zr_ += dl[0] * (1 - sr_ / Lr) + dl[1] * (sr_ / Lr)        # voie courte raccordee aux deux bouts : correction lineaire
        else:
            for e_, d_ in dl.items(): zr_ += d_ * np.clip(1.0 - np.abs(sr_ - (0.0 if e_ == 0 else Lr)) / 120.0, 0, 1)
        dense_z[i_] = zr_
    # croisements sans raccordement : un franchissement exige 6,5 m de hauteur libre (caténaire comprise) ; sinon la voie du dessus (si c'est une voie supplementaire) est relevee localement
    lines_ = [LineString(a) for a in dense_xy]; codes_ = list(tracks); linked = [(lk["host"], c_, lk["xy"]) for c_, ls_ in links.items() for lk in ls_.values() if lk.get("kind") == "T"]
    n_x = n_lvl = n_ok = 0; fixed = []; unfixed = []
    for i_ in range(len(codes_)):
        for j_ in range(i_ + 1, len(codes_)):
            bi, bj = lines_[i_].bounds, lines_[j_].bounds
            if bi[0] > bj[2] or bj[0] > bi[2] or bi[1] > bj[3] or bj[1] > bi[3]: continue
            inter = lines_[i_].intersection(lines_[j_])
            if inter.is_empty: continue
            for p_ in ([inter] if inter.geom_type == "Point" else [q_ for q_ in getattr(inter, "geoms", []) if q_.geom_type == "Point"]):
                if any({a_, b_} == {codes_[i_], codes_[j_]} and math.hypot(p_.x - xy_[0], p_.y - xy_[1]) < 10.0 for a_, b_, xy_ in linked): continue
                n_x += 1; zi = float(np.interp(lines_[i_].project(p_), *tracks[codes_[i_]]["prof"])); zj = float(np.interp(lines_[j_].project(p_), *tracks[codes_[j_]]["prof"])); d_ = zi - zj
                if abs(d_) < 0.7: n_lvl += 1; continue
                if abs(d_) >= 6.5: n_ok += 1; continue
                up = i_ if d_ > 0 else j_; need = 6.5 - abs(d_)
                if not tracks[codes_[up]]["extra"]: unfixed.append((codes_[i_], codes_[j_], round(d_, 1))); continue
                sr_u, zr_u = tracks[codes_[up]]["prof"]; Wb = need / 0.025 + 30.0; sp = lines_[up].project(p_)
                wn = np.ones(len(sr_u))   # le relevage s'annule aux extremites raccordees (la voie quitte la voie mere a son niveau) : pente de montee plus forte, plafonnee ci-dessous
                for e__, lk_ in links[codes_[up]].items():
                    if lk_.get("kind") in ("T", "END", "PEER"): wn = np.minimum(wn, np.clip(np.abs(sr_u - (0.0 if e__ == 0 else sr_u[-1])) / 150.0, 0, 1))
                zr_u += need * 0.5 * (1 + np.cos(np.pi * np.clip((sr_u - sp) / Wb, -1, 1))) * wn; dense_z[up] = zr_u; fixed.append((codes_[up], round(need, 1)))
    print("croisements entre voies non raccordees : %d (au meme niveau : %d, deja a 6,5 m ou plus : %d, releves : %d, non corriges : %d)" % (n_x, n_lvl, n_ok, len(fixed), len(unfixed)), fixed[:4], unfixed[:4])
    mm = []
    for code_, lks_ in links.items():
        for e_, lk_ in lks_.items():
            if lk_.get("kind") not in ("T", "END"): continue
            sh_, zh_ = tracks[lk_["host"]]["prof"]; sb_, zb_ = tracks[code_]["prof"]
            mm.append((abs(float(np.interp(lk_["s_host"] if lk_["kind"] == "T" else (0.0 if lk_["host_end"] == 0 else sh_[-1]), sh_, zh_)) - float(np.interp(0.0 if e_ == 0 else sb_[-1], sb_, zb_))), code_, lk_["host"], lk_["kind"]))
    mm.sort(reverse=True); print("raccords : ecart de hauteur max %.3f m" % (mm[0][0] if mm else 0), mm[:3])
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
    # ---- reperes de quai : "Platform marker" (arret en gare) + "Destination marker" (scenarios) sur chaque voie a quai des gares voyageurs.
    # Nom = "<gare> Voie <n>" ; n = numero SNCF de la voie quand il existe (3, 12, 14... a Nogent), V1/V2 prennent les plus petits numeros libres de la gare.
    marks = {}; mark_names = []
    mk_tpl = {k: etree.parse(os.path.join(MARS, "marker_%s.xml" % k)).getroot() for k in ("platform",)}   # pas de repere Destination : meme nom = doublon dans la liste des quais
    def rib_at(rb, u):
        c_ = 0.0
        for sg_ in rb["segs"]:
            if u <= c_ + sg_["len"] + 1e-6 or sg_ is rb["segs"][-1]: return NB.pos_on(sg_, min(max(u - c_, 0.0), sg_["len"]))
            c_ += sg_["len"]
    for (sname, spk, sx, sz, half) in load_stations(pk_a, pk_b):
        sname = sname.replace("St-", "Saint-"); cand = {}
        for i_, code in enumerate(tracks):
            Pr = dense_xy[i_]; d_ = np.hypot(Pr[:, 0] - sx, Pr[:, 1] - sz); j_ = int(np.argmin(d_))
            if d_[j_] < 45.0: cand[code] = j_ * 5.0
        # voies a quai : V1/V2 + voies SNCF a quai connues (Le Mans : voies numerotees ; Nogent : "S" = voie SP, a confirmer) ; les voies numerotees des autres gares sont des voies de service
        PLAT_EXTRA = {"Le Mans": r"\d+", "Nogent-le-Rotrou": r"S"}; rx_ = PLAT_EXTRA.get(sname)
        num = {c_: m_.group(1) if m_.group(1) != "S" else "SP" for c_ in cand for m_ in [re.match(r"SNCF-(%s)-\d+$" % rx_, c_)] if rx_ and m_}; free = (str(n_) for n_ in range(1, 99) if str(n_) not in num.values())
        for c_ in [k_ for k_ in cand if k_ in TRACKS]: num[c_] = next(free)
        for c_, n_ in sorted(num.items(), key=lambda a_: (len(a_[1]), a_[1])):
            t_ = tracks[c_]; rl = [sum(s_["len"] for s_ in r_["segs"]) for r_ in t_["ribbons"]]; st_ = np.r_[0.0, np.cumsum(rl)]
            s0, s1 = max(cand[c_] - half, 0.0), min(cand[c_] + half, st_[-1]); ov = [max(0.0, min(s1, st_[k_ + 1]) - max(s0, st_[k_])) for k_ in range(len(rl))]; ri_ = int(np.argmax(ov))
            if ov[ri_] < 30.0: continue
            a_, b_ = max(s0, st_[ri_]) - st_[ri_], min(s1, st_[ri_ + 1]) - st_[ri_]; nm_ = "%s Voie %s" % (sname, n_)
            marks.setdefault((c_, ri_), []).append(("platform", nm_, a_, b_)); mark_names.append(nm_)
    print(len(mark_names), "reperes de quai :", mark_names)
    # ---- signaux : signalisation permanente SNCF Reseau (carres, semaphores, carres violets : voie, PK, sens C/D, cote G/D/A reels ; copie de Carto Tchoo du jeu SNCF
    # "signalisation-permanente") -> signaux BAL du DLC ; butoirs : OSM. Le signal est a gauche du sens de marche (conduite a gauche) : cote G = gauche, D = droite, A = portique.
    sigs = {}; sg_tpl = {n_: etree.parse(os.path.join(MARS, "sig_%s.xml" % n_)).getroot() for n_ in ("BAL_NfB_0", "BAL_Nf2_1", "EndOfTrack", "BAL_FE_0", "BAL_GNfB_0", "BAL_GFE_0")}
    SIG_OFF = 3.0; sfile = os.path.join(ROOT, "GeographicData", "Raw", "sncf", "signalisation-permanente_420000.json"); n_sig = collections.Counter()
    TYPE_BP = {"CARRE": ("BAL_NfB_0", "BAL_GNfB_0"), "S": ("BAL_FE_0", "BAL_GFE_0"), "CV": ("BAL_Nf2_1", "BAL_Nf2_1")}   # (poteau, portique)
    if os.path.exists(sfile) and not os.environ.get("NO_SIGNALS"):
        codes_t = list(tracks); offs = np.r_[0, np.cumsum([len(a) for a in dense_xy])]; kdS = cKDTree(dxy); v1P = dense_xy[0]; pkn = lambda s_: int(s_.split("+")[0]) + int(s_.split("+")[1]) / 1000
        def place(oid, bp, x_, z_, c_sens, side, only=None):
            d_, j_ = kdS.query((x_, z_), k=6, distance_upper_bound=14.0)
            cands = [(dd, jj) for dd, jj in zip(np.atleast_1d(d_), np.atleast_1d(j_)) if np.isfinite(dd)]
            if only: cands = [c_ for c_ in cands if int(np.searchsorted(offs, c_[1], side="right")) - 1 in only] or cands
            if not cands: return False
            _, jj = cands[0]; ti = int(np.searchsorted(offs, jj, side="right")) - 1; jl = jj - offs[ti]; Pr = dense_xy[ti]
            tt = Pr[min(jl + 1, len(Pr) - 1)] - Pr[max(jl - 1, 0)]; tt = tt / (np.hypot(*tt) or 1.0)
            km = np.hypot(*(v1P - np.array([x_, z_])).T).argmin(); t1 = v1P[min(km + 1, len(v1P) - 1)] - v1P[max(km - 1, 0)]   # sens des PK croissants (le long de V1)
            plus = (float(tt @ t1) > 0) == (c_sens == "C")
            sigs.setdefault(codes_t[ti], []).append((bp, jl * 5.0, plus, {"G": SIG_OFF, "D": -SIG_OFF}.get(side, 0.0), oid)); n_sig[bp] += 1; return True
        miss = 0
        for o_ in json.load(open(sfile, encoding="utf-8")):
            if o_["type_if"] not in TYPE_BP or not (pk_a - 0.3 <= pkn(o_["pk"]) <= pk_b + 0.3) or o_["sens"] not in ("C", "D"): continue
            x_, z_ = C.lonlat_to_xz(o_["x_wgs84"], o_["y_wgs84"]); nm_ = o_["code_voie"].split("-")[-1]
            same = {i_ for i_, c_ in enumerate(codes_t) if c_.endswith("-" + nm_) or ("-%s-" % nm_) in c_}
            if not place("sncf-%s" % o_["idreseau"], TYPE_BP[o_["type_if"]][1 if o_["position"] == "A" else 0], x_, z_, o_["sens"], o_["position"], same): miss += 1
        print("signaux SNCF non places (voie introuvable a 14 m) :", miss)
        for oid, o_ in json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "osm_signaux_phase1.json"), encoding="utf-8")).items():   # butoirs
            if o_["tags"].get("railway") != "buffer_stop": continue
            x_, z_ = C.lonlat_to_xz(o_["lon"], o_["lat"]); d_, j_ = kdS.query((x_, z_))
            if d_ > 14.0: continue
            ti = int(np.searchsorted(offs, j_, side="right")) - 1; jl = j_ - offs[ti]; code = codes_t[ti]; Lt = tracks[code]["prof"][0][-1]; s_ = jl * 5.0
            if links[code].get(0) is None and s_ < 25.0: sigs.setdefault(code, []).append(("EndOfTrack", 1.5, False, 0.0, oid)); n_sig["EndOfTrack"] += 1
            elif links[code].get(1) is None and s_ > Lt - 25.0 and code not in TRACKS: sigs.setdefault(code, []).append(("EndOfTrack", Lt - 1.5, True, 0.0, oid)); n_sig["EndOfTrack"] += 1
        print("signaux poses :", dict(n_sig))
    all_guids, turn_at = {}, {}
    for code, t in tracks.items():
        sr, zr = t["prof"]; cum = 0.0; guids = []
        for ri, rb in enumerate(t["ribbons"]):
            rid = uuid.uuid5(route_guid, "%s-ribbon-%d" % (code, ri)); guids.append(rid)
            L = sum(s["len"] for s in rb["segs"])
            P2 = np.array([pos_on(s, u)[:2] for s in rb["segs"] for u in (0, s["len"] / 2, s["len"])])
            bl = P2.min(axis=0); ext = P2.max(axis=0) - bl
            ss = np.linspace(0, L, int(L / 20) + 2); zs = np.interp(cum + ss, sr, zr)
            vm = 40 if t.get("extra") else vmax_at(vtab, pk_a + (cum + L / 2) / 1000.0); cum_start = cum; cum += L
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
            wrap = pc.find("{*}Property")
            for (kind, nm_, a_, b_) in marks.get((code, ri), []):
                mk = copy.deepcopy(mk_tpl[kind]); strip_alt(mk); x_, z_, th_ = rib_at(rb, a_); h_ = float(np.interp(cum_start + a_, sr, zr))
                mk.find("{*}_start").text = ff(a_); mk.find("{*}_end").text = ff(b_); mk.find("{*}First").text = "1"
                comp = mk.find(".//{*}Network-cTrackMarkerComponent"); comp.find("{*}DisplayName").text = nm_; comp.find("{*}LocalisedDisplayName//{*}English").text = nm_
                set_guid_key = uuid.uuid5(route_guid, "mk-%s-%s-%d-%s" % (kind, code, ri, nm_)); comp.find("{*}LocalisedDisplayName//{*}Key").text = str(set_guid_key)
                m = mk.find(".//{*}cFarMatrix"); m.find("{*}Height").text = ff(h_)
                m.find("{*}RXAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (math.cos(th_), math.sin(th_)); m.find("{*}RYAxis").text = "0.0000000 1.0000000 0.0000000 0.0000000"; m.find("{*}RZAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (-math.sin(th_), math.cos(th_))
                set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}X/{*}cFarCoordinate"), x_); set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), z_)
                set_guid(mk.find(".//{*}cOwnedEntity/{*}EntityID/{*}cGUID"), uuid.uuid5(route_guid, "mke-%s-%s-%d-%s" % (kind, code, ri, nm_))); wrap.append(mk)
            for (bp, s_, plus, lt_, oid) in sigs.get(code, []):
                if not (cum_start <= s_ < cum_start + L): continue
                a_ = s_ - cum_start; x_, z_, th_ = rib_at(rb, a_); tx_, tz_ = (math.cos(th_), math.sin(th_)) if plus else (-math.cos(th_), -math.sin(th_)); nx_, nz_ = -tz_, tx_   # sens servi ; normale gauche
                px_, pz_ = x_ + lt_ * nx_, z_ + lt_ * nz_; sp = copy.deepcopy(sg_tpl[bp]); strip_alt(sp)
                sp.find("{*}_offset").text = ff(a_); sp.find(".//{*}_dir").text = "forwards" if plus else "backwards"
                m = sp.find(".//{*}cFarMatrix"); m.find("{*}Height").text = ff(float(np.interp(cum_start + a_, sr, zr)))
                m.find("{*}RXAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (tz_, -tx_); m.find("{*}RYAxis").text = "0.0000000 1.0000000 0.0000000 0.0000000"; m.find("{*}RZAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (tx_, tz_)   # +Z = sens servi (releve sur le DLC)
                set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}X/{*}cFarCoordinate"), px_); set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), pz_)
                set_guid(sp.find(".//{*}cOwnedEntity/{*}EntityID/{*}cGUID"), uuid.uuid5(route_guid, "sig-%s" % oid)); wrap.append(sp)
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
            for si, (s0, s1, p0, p1) in enumerate(spans_for(rb["segs"], L) if t.get("elec", True) else []):
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
        all_guids[code] = guids
        for i in range(len(guids) - 1):
            cid = t["ribbons"][i + 1]["segs"][0].get("cut")
            if cid is None: node_c.append(node(node2, [(guids[i], 1), (guids[i + 1], 0)]))
            else: turn_at[cid] = (code, i)
        for e_, gi in ((0, 0), (1, -1)):
            lk = links[code].get(e_)
            if lk is None: node_c.append(node(node1, [(guids[gi], e_)]))
            elif lk["kind"] == "END":
                hg = all_guids[lk["host"]]; he = lk["host_end"]; node_c.append(node(node2, [(hg[0] if he == 0 else hg[-1], he), (guids[gi], e_)]))
    # aiguillages : noeud a 3 connexions [tige, voie directe, voie deviee] + moteur d'aiguille du DLC (modele releve dans Marseille-Avignon)
    turn_tpl = etree.parse(os.path.join(MARS, "turnout_node.xml")).getroot(); n_turn = 0
    for code, lks in links.items():
        for e_, lk in lks.items():
            if lk.get("kind") != "T": continue
            if lk["cid"] not in turn_at: print("aiguillage sans coupe :", code, lk["host"]); continue
            hc, i = turn_at[lk["cid"]]; hg = all_guids[hc]; A, B = hg[i], hg[i + 1]; br = all_guids[code][0 if e_ == 0 else -1]
            stem, straight = ((A, 1), (B, 0)) if lk["fwd"] else ((B, 0), (A, 1))
            nd = copy.deepcopy(turn_tpl); strip_alt(nd)
            for c_, (g_, end_) in zip(nd.findall(".//{*}Network-cNetworkNode-sRConnection"), [stem, straight, (br, e_)]):
                set_guid(c_.find("{*}_id/{*}cGUID"), g_); c_.find("{*}_end/{*}cNormFloat/{*}Position").text = str(end_)
            sr_h, zr_h = tracks[lk["host"]]["prof"]; m = nd.find(".//{*}cFarMatrix"); psi = lk["th"]
            m.find("{*}Height").text = ff(float(np.interp(lk["s_host"], sr_h, zr_h)))
            m.find("{*}RXAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (math.cos(psi), math.sin(psi)); m.find("{*}RYAxis").text = "0.0000000 1.0000000 0.0000000 0.0000000"; m.find("{*}RZAxis").text = "%.7f 0.0000000 %.7f 0.0000000" % (-math.sin(psi), math.cos(psi))
            set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}X/{*}cFarCoordinate"), float(lk["xy"][0])); set_far(m.find(".//{*}RFarPosition/{*}cFarVector2/{*}Z/{*}cFarCoordinate"), float(lk["xy"][1]))
            set_guid(nd.find(".//{*}Network-cTurnoutPattern//{*}EntityID/{*}cGUID"), uuid.uuid5(route_guid, "turnout-%d" % lk["cid"]))
            node_c.append(nd); n_turn += 1
    print(n_turn, "aiguillages ecrits")
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
        # quais reels : trace OSM (railway=platform) ; le quai est pose sur chaque voie dont le bord de quai (a 1,67 m + demi-largeur de l'axe) tombe dans l'emprise du quai, sur les troncons d'au moins 30 m.
        # Gares sans quai OSM (Montfort-le-Gesnois...) : ancienne regle (longueur forfaitaire autour du point de gare, V1/V2).
        import shapely
        from shapely.geometry import Polygon as _Pg
        qfile = os.path.join(ROOT, "GeographicData", "Raw", "osm_quais_phase1.json"); has_osm = set(); plat_dbg = []; offs_q = np.r_[0, np.cumsum([len(a) for a in dense_xy])]
        if os.path.exists(qfile) and not os.environ.get("NO_OSM_QUAIS"):
            for key, q_ in json.load(open(qfile, encoding="utf-8")).items():
                if q_["tags"].get("railway") != "platform": continue
                pts_ = [C.lonlat_to_xz(*c_) for c_ in q_["geometry"]]
                if len(pts_) < 2: continue
                prod = STATION_PROD.get(q_["station"], PLT_PROD); wd_ = QUAI_W[prod]
                area = (_Pg(pts_).buffer(3.0) if len(pts_) >= 4 and pts_[0] == pts_[-1] else LineString(pts_).buffer(wd_ / 2 + 1.5)); bx = area.bounds; n0 = n_plat
                cen_ = LineString(pts_).centroid
                for i, code in enumerate(tracks):
                    Pr = dense_xy[i]
                    if not (code in TRACKS or (q_["station"] == "Le Mans" and re.match(r"SNCF-\d+-", code)) or (q_["station"] == "Nogent-le-Rotrou" and code.startswith("SNCF-S-"))): continue   # voies a quai ; les autres sont des voies de service
                    if len(Pr) < 8 or Pr[:, 0].max() < bx[0] - 15 or Pr[:, 0].min() > bx[2] + 15 or Pr[:, 1].max() < bx[1] - 15 or Pr[:, 1].min() > bx[3] + 15: continue
                    tv = np.gradient(Pr, axis=0); tv = tv / (np.hypot(tv[:, 0], tv[:, 1])[:, None] + 1e-9); nv = np.c_[-tv[:, 1], tv[:, 0]]
                    jc = int(np.argmin(np.hypot(Pr[:, 0] - cen_.x, Pr[:, 1] - cen_.y))); sd = float((cen_.x - Pr[jc][0]) * nv[jc][0] + (cen_.y - Pr[jc][1]) * nv[jc][1])   # cote du quai par rapport a la voie
                    for outer in ((1.0, -1.0) if abs(sd) < 1.0 else ((1.0,) if sd > 0 else (-1.0,))):
                        Q = Pr + outer * (PLT_EDGE + wd_ / 2) * nv; ins = shapely.contains_xy(area, Q[:, 0], Q[:, 1])
                        dq_, iq_ = kd.query(Q, k=6, distance_upper_bound=3.2); own_ = (np.searchsorted(offs_q, np.minimum(iq_, len(dxy) - 1), side="right") - 1) != i
                        ins = ins & ~np.any(np.isfinite(dq_) & own_, axis=1)   # pas de quai pose sur une autre voie
                        j = 1
                        while j < len(Pr) - 2:
                            if not ins[j]: j += 1; continue
                            k = j
                            while k + 1 < len(Pr) - 2 and (ins[k + 1] or (k + 2 < len(Pr) - 2 and ins[k + 2])): k += 1
                            if k - j >= 6:
                                plat(i, code, j, k, outer, prod, "%s-%s" % (key, "L" if outer > 0 else "R")); plat_dbg.append((q_["station"], q_["tags"].get("ref"), code, "gauche" if outer > 0 else "droite", (k - j) * 5, Pr[j].tolist(), Pr[k].tolist()))
                            j = k + 1
                if n_plat > n0: has_osm.add(q_["station"])
        print("gares avec quais OSM :", sorted(has_osm)); json.dump(plat_dbg, open(os.path.join(ROOT, "Tests", "Phase1", "previews", "quais_poses.json"), "w"))
        for (sname, spk, sx, sz, half) in load_stations(pk_a, pk_b):
            if sname in has_osm: continue
            for i, code in enumerate(list(tracks)[:2]):
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
    kd_other = {code: (cKDTree(dense_xy[1 - i]) if i < 2 else kdV) for i, code in enumerate(tracks)}   # voie voisine : le poteau se met du cote oppose (V1/V2 s'inversent dans les gares)
    other_xy = {code: (dense_xy[1 - i] if i < 2 else np.vstack(dense_xy[:2])) for i, code in enumerate(tracks)}
    offs_pl = np.r_[0, np.cumsum([len(a) for a in dense_xy])]; codes_pl = list(tracks); pole_grid = set(); n_pole_skip = 0
    for plist in pole_recs.values():
        for (code, si, x, z, h, phi) in plist:
            nx, nz = -math.sin(phi), math.cos(phi)
            dd, jj = kd_other[code].query((x, z)); left = code.endswith("V1")
            if dd < 15.0:
                wx, wz = other_xy[code][jj][0] - x, other_xy[code][jj][1] - z
                left = (math.cos(phi) * wz - math.sin(phi) * wx) < 0   # voisine a droite -> poteau a gauche
            # poteau : cote libre uniquement (pas a moins de 2,7 m de l'axe d'une autre voie), jamais deux poteaux a moins de 2,5 m ; dans un faisceau etroit le poteau est omis (les fils restent tendus)
            def _free(sd_):
                bx_, bz_ = x + sd_ * POLE_D * nx, z + sd_ * POLE_D * nz; d6, i6 = kd.query((bx_, bz_), k=6, distance_upper_bound=2.7)
                return (not any(np.isfinite(a_) and codes_pl[int(np.searchsorted(offs_pl, b_, side="right")) - 1] != code for a_, b_ in zip(np.atleast_1d(d6), np.atleast_1d(i6)))), bx_, bz_
            ok_, bx, bz = _free(1.0 if left else -1.0)
            if not ok_: left = not left; ok_, bx, bz = _free(1.0 if left else -1.0)
            gk_ = (round(bx / 2.5), round(bz / 2.5))
            if not ok_ or any((gk_[0] + a_, gk_[1] + b_) in pole_grid for a_ in (-1, 0, 1) for b_ in (-1, 0, 1)): n_pole_skip += 1; continue
            pole_grid.add(gk_)
            if POLE_KIND == "single":   # origine sur l'axe : le cote du poteau est porte par l'orientation du modele
                by_tile.setdefault((math.floor(x / TILE), math.floor(z / TILE)), []).append((code, si, x, z, h, phi + ORI * (math.pi / 2 if left else -math.pi / 2))); continue
            px, pz = (x + POLE_D * nx, z + POLE_D * nz) if left else (x - POLE_D * nx, z - POLE_D * nz)
            # l'axe +X de l'objet doit pointer vers la voie (releve sur les poteaux ? HPost Med ? du DLC)
            by_tile.setdefault((math.floor(px / TILE), math.floor(pz / TILE)), []).append((code, si, px, pz, h, phi - math.pi / 2 if left else phi + math.pi / 2))
    print(n_pole_skip, "poteaux omis (faisceau etroit ou doublon)")
    if os.environ.get("DBG_POLES"):   # diagnostic : poteaux a moins de 2,2 m de l'axe d'une AUTRE voie
        offs_p = np.r_[0, np.cumsum([len(a) for a in dense_xy])]; codes_p = list(tracks); bad_p = []; tot_p = 0
        for plist_ in by_tile.values():
            for (code_, si_, x_, z_, h_, psi_) in plist_:
                tot_p += 1; d_, i_ = kd.query((x_, z_), k=6, distance_upper_bound=2.2)
                for dd_, ii_ in zip(np.atleast_1d(d_), np.atleast_1d(i_)):
                    if np.isfinite(dd_) and codes_p[int(np.searchsorted(offs_p, ii_, side="right")) - 1] != code_: bad_p.append((code_, round(float(dd_), 1))); break
        print("poteaux sur/pres d'une autre voie : %d sur %d" % (len(bad_p), tot_p), collections.Counter(c_ for c_, _ in bad_p).most_common(6))
    # objets de decor (batiments, panneaux...) : Route/Configuration/objects.json ; position par PK de V1 + decalage lateral (gauche > 0) + cap relatif
    obj_by_tile = {}; obj_tpl = None
    ofile = os.environ.get("OBJECTS_FILE") or os.path.join(ROOT, "Route", "Configuration", "objects.json")
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
    # decor en positions absolues (lon/lat) : Route/Configuration/objects_decor.json (vegetation, maisons...) ; objet ecarte a moins de `clear` m d'un axe de voie ; hauteur = relief IGN
    # (meme raccord que le terrain : plateforme de la voie sur 11,5 m, fondu jusqu'a 26 m) ; plafond par tuile (DECOR_MAX_PER_TILE, defaut 2500, echantillon deterministe)
    dfile = os.environ.get("DECOR_FILE") or os.path.join(ROOT, "Route", "Configuration", "objects_decor.json"); n_decor = n_cut = 0
    if obj_tpl is not None and os.path.exists(dfile) and not os.environ.get("NO_DECOR"):
        cap_ = int(os.environ.get("DECOR_MAX_PER_TILE", "2500")); per_tile = {}
        for ob in json.load(open(dfile, encoding="utf-8-sig")):
            x_, z_ = C.lonlat_to_xz(ob["lon"], ob["lat"]); tk = (math.floor(x_ / TILE), math.floor(z_ / TILE))
            if tk not in tiles: continue
            d_, i_ = kd.query((x_, z_), distance_upper_bound=26.0)
            if np.isfinite(d_) and d_ < ob.get("clear", 6.0): n_cut += 1; continue
            per_tile.setdefault(tk, []).append((ob, x_, z_, d_, i_))
        for tk, lst in per_tile.items():
            if len(lst) > cap_: lst = sorted(lst, key=lambda a_: hash((round(a_[1]), round(a_[2]))))[:cap_]; n_cut += 1
            for ob, x_, z_, d_, i_ in lst:
                h_ = float(dem_point(np.array([x_]), np.array([z_]), cache)[0])
                if np.isfinite(d_): w_ = min(max((26.0 - d_) / 14.5, 0.0), 1.0); h_ = h_ * (1 - w_) + (float(dz[i_]) - 0.30) * w_
                obj_by_tile.setdefault(tk, []).append((ob, x_, z_, h_ + ob.get("dz", 0.0), math.radians(ob.get("heading_deg", 0.0)))); n_decor += 1
        print(n_decor, "objets de decor poses,", n_cut, "ecartes (voie proche / plafond)")
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
    # sol : plateforme plane a (hauteur de voie - 0,30 m) sur 11,5 m autour de chaque axe (la grille fait 8 m : les 4 coins de chaque maille sous un rail sont aplanis),
    # raccordee au relief naturel sur 14,5 m de plus ; remblai limite a 8 m ; sous un pont signale par BD TOPO le sol reste au relief
    ground = dem_point(dxy[:, 0], dxy[:, 1], cache)
    bp_ = []   # ouvrages (ponts) signales par BD TOPO (position_par_rapport_au_sol = 1) : on n'y comble pas le sol
    for f_ in json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "bdtopo_voies_phase1.json"), encoding="utf-8"))["features"]:
        if f_["properties"]["position_par_rapport_au_sol"] == "1":
            L_ = LineString([C.lonlat_to_xz(*c_[:2]) for c_ in f_["geometry"]["coordinates"]]); bp_ += [L_.interpolate(u_).coords[0] for u_ in np.arange(0, L_.length + 2, 2.0)]
    near_bridge = (cKDTree(np.array(bp_)).query(dxy, distance_upper_bound=8.0)[0] < 8.0) if bp_ else np.zeros(len(dxy), bool)
    onground = ((dz - ground) <= 8.0) & ~(near_bridge & ((dz - ground) > 1.0))   # remblai jusqu'a 8 m ; pont reel : sol laisse au relief
    kdT = cKDTree(dxy[onground]); dzT = dz[onground]; R_FLAT, R_OUT = 11.5, 26.0; final_H = {}
    def conv_ter(t):
        tx, tz = t; H = cache[t].copy()
        H = np.nan_to_num(H, nan=float(np.nanmean(H)) if np.isfinite(np.nanmean(H)) else 0.0)
        gx = tx * TILE + np.arange(GRID) * CELL; gz = tz * TILE + np.arange(GRID) * CELL
        XX, ZZ = np.meshgrid(gx, gz); d4, i4 = kdT.query(np.c_[XX.ravel(), ZZ.ravel()], k=4, distance_upper_bound=R_OUT); dist = d4[:, 0]
        z4 = np.where(np.isfinite(d4) & (d4 <= dist[:, None] + 12.0), dzT[np.minimum(i4, len(dzT) - 1)], np.inf); th = np.where(np.isfinite(dist), z4.min(axis=1), 0).reshape(GRID, GRID)   # le plus bas des axes voisins (a 12 m pres)
        ok = np.isfinite(dist); dist = np.where(ok, dist, 99.0).reshape(GRID, GRID)
        w = np.clip((R_OUT - dist) / (R_OUT - R_FLAT), 0, 1)
        H = np.where(dist < R_OUT, H * (1 - w) + (th - 0.30) * w, H).astype("<f4"); final_H[t] = H
        nm = C.tile_name(tx, tz)
        open(os.path.join(rdir, "Terrain", nm + ".bin"), "wb").write(patch_tile_bin(ter_tpl, 116, 131, tx, tz, len(ter_tpl) - 12 - 65536, H.tobytes()))
        open(os.path.join(rdir, "MixMap", nm + ".bin"), "wb").write(patch_tile_bin(mix_tpl, 111, 130, tx, tz, len(mix_tpl) - 12 - 98304, mix_tpl[len(mix_tpl) - 12 - 98304:len(mix_tpl) - 12]))
    with ThreadPoolExecutor(6) as ex: list(ex.map(conv_ter, sorted(tiles)))
    # controle : le sol ne doit jamais depasser le rail (axe et bords de traverse a 1,7 m) sur les tronçons au sol
    viol = []
    for i_, code in enumerate(tracks):
        Pr_ = dense_xy[i_]; zr_ = dense_z[i_]; og = onground[sum(len(a) for a in dense_xy[:i_]):sum(len(a) for a in dense_xy[:i_ + 1])]
        if len(Pr_) < 3: continue
        tv = np.gradient(Pr_, axis=0); tv = tv / (np.hypot(tv[:, 0], tv[:, 1])[:, None] + 1e-9); nv = np.c_[-tv[:, 1], tv[:, 0]]
        for off in (-1.7, 0.0, 1.7):
            Q = Pr_ + off * nv; gh = dem_point(Q[:, 0], Q[:, 1], final_H); bad = og & (gh > zr_ - 0.12)
            if bad.any(): viol.append((code, off, int(bad.sum()), float((gh - zr_)[bad].max())))
    print("controle sol/rail : %d voies avec sol au-dessus du rail -1,2 dm (sur %d)" % (len(set(v[0] for v in viol)), len(tracks)), viol[:5])

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
