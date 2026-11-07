"""Controle hors-jeu d'une route generee : relit les .bin avec serz et verifie coherence et ecart aux voies SNCF.
Usage : python validate_route.py <dossier_route_GUID>"""
import sys, os, glob, math, json, re, subprocess, tempfile, collections
import numpy as np
from lxml import etree
from shapely.geometry import LineString, Point, shape
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tsc_tiles as T, tsc_coords as C
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SERZ = r"D:\Programmes\Steam\steamapps\common\RailWorks\serz.exe"
D = "{http://www.kuju.com/TnT/2003/Delta}"

def main(rdir):
    tmp = tempfile.mkdtemp(prefix="val_")
    def conv(f): subprocess.run([SERZ, f, "/xml:" + os.path.join(tmp, os.path.basename(f)[:-4] + ".xml")], capture_output=True)
    files = [os.path.join(rdir, "Networks", "Tracks.bin")] + glob.glob(os.path.join(rdir, "Networks", "Track Tiles", "*.bin"))
    with ThreadPoolExecutor(6) as ex: list(ex.map(conv, files))
    tiles = {}
    for f in glob.glob(tmp + r"\[+-]*.xml"):
        for rid, cs in T.read_tile(f): tiles[rid] = cs
    root = etree.parse(os.path.join(tmp, "Tracks.xml")).getroot()
    rib = list(root.iter("{*}Network-cTrackRibbon")); order = [r.find(".//{*}RibbonID//{*}DevString").text for r in rib]
    print("%d rubans, %d noeuds, %d dans les tuiles, manquants %d" % (len(order), len(list(root.iter("{*}Network-cTrackNode"))), len(tiles), len(set(order) - set(tiles))))
    # jonctions : fin d'un ruban -> debut du suivant (sauf changement de voie : ecart > 50 m ignore)
    gaps = []
    for a, b in zip(order, order[1:]):
        ea = T.advance(tiles[a][-1]); sb = tiles[b][0]; g = math.hypot(ea[0] - sb["x"], ea[1] - sb["z"])
        if g < 50: gaps.append(g)
    print("jonctions entre rubans : max %.4f m (n=%d)" % (max(gaps), len(gaps)))
    pts = []; total = 0.0
    for rid in order:
        cs = tiles[rid]
        for a, b in zip(cs, cs[1:]):
            e = T.advance(a); assert math.hypot(e[0] - b["x"], e[1] - b["z"]) < 0.01, "discontinuite dans un ruban"
        for c in cs:
            total += c["len"]
            for u in np.linspace(0, c["len"], 6): pts.append(T.advance({**c, "len": u})[:2] if c["type"] == "cCurveArc" else (c["x"] + c["tx"] * u, c["z"] + c["tz"] * u))
    print("longueur totale des voies : %.1f km, %d courbes" % (total / 1000, sum(len(v) for v in tiles.values())))
    V = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json"), encoding="utf-8"))
    L = [LineString([C.lonlat_to_xz(*p) for p in shape(x["geo_shape"]["geometry"]).coords]) for x in V if x["code_voie"] in ("420000-1-V1", "420000-1-V2")]
    P = np.array(pts)[::5]; dev = np.array([min(l.distance(Point(*p)) for l in L) for p in P])
    print("ecart aux voies SNCF : max %.2f m, moyenne %.3f m, > 1 m : %d points sur %d" % (dev.max(), dev.mean(), (dev > 1).sum(), len(dev)))
    print("vitesses", sorted(collections.Counter(x.text for x in root.iter("{*}Primary")).items(), key=lambda a: int(a[0])))
    print("electrification", dict(collections.Counter(e.text for e in root.iter("{*}Electrification"))))
    bad = sum(1 for r in rib if any(abs(float(e.text) - float(r.find("{*}_length").text)) > 0.01 for e in r.iter("{*}_end")))
    print("rubans dont une propriete ne couvre pas la longueur : %d" % bad)
    hs = [float(h.find("{*}_height").text) for h in root.iter("{*}Network-iRibbon-cHeight")]; print("hauteurs de voie %.1f a %.1f m" % (min(hs), max(hs)))
    ter = sorted(glob.glob(os.path.join(rdir, "Terrain", "*.bin")))[0]; subprocess.run([SERZ, ter, "/xml:" + os.path.join(tmp, "ter.xml")], capture_output=True)
    h = etree.parse(os.path.join(tmp, "ter.xml")).getroot().find(".//{*}cHeightFieldTile")
    a = np.frombuffer(bytes.fromhex(re.sub(r"\s+", "", h.find(D + "blob").text)), "<f4")
    print("terrain %s : X %s Y %s, %d valeurs, %.1f a %.1f m ; %d tuiles terrain, %d MixMap" % (os.path.basename(ter), h.find("{*}X").text, h.find("{*}Y").text, a.size, a.min(), a.max(),
          len(glob.glob(os.path.join(rdir, "Terrain", "*.bin"))), len(glob.glob(os.path.join(rdir, "MixMap", "*.bin")))))

if __name__ == "__main__":
    main(sys.argv[1])
