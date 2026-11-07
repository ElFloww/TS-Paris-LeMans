"""Controle hors-jeu du reseau d'une route generee : a chaque noeud (2 ou 3 connexions), ecart de position, de cap et de hauteur entre les rubans
qui s'y rejoignent ; aiguillages : tige oppose a la voie directe, angle de la voie deviee ; bouts libres.
Usage : python validate_network.py <dossier_route_GUID>"""
import sys, os, glob, math, subprocess, tempfile
import numpy as np
from lxml import etree
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tsc_tiles as T
SERZ = r"D:\Programmes\Steam\steamapps\common\RailWorks\serz.exe"

def main(rdir):
    tmp = tempfile.mkdtemp(prefix="valn_")
    def conv(f): subprocess.run([SERZ, f, "/xml:" + os.path.join(tmp, os.path.basename(f)[:-4] + ".xml")], capture_output=True)
    files = [os.path.join(rdir, "Networks", "Tracks.bin")] + glob.glob(os.path.join(rdir, "Networks", "Track Tiles", "*.bin"))
    with ThreadPoolExecutor(6) as ex: list(ex.map(conv, files))
    tiles = {}
    for f in glob.glob(tmp + r"\[+-]*.xml"):
        for rid, cs in T.read_tile(f): tiles[rid] = cs
    root = etree.parse(os.path.join(tmp, "Tracks.xml")).getroot()
    hts = {}
    for r in root.iter("{*}Network-cTrackRibbon"):
        rid = r.find(".//{*}RibbonID//{*}DevString").text; h = sorted((float(x.find("{*}_position").text), float(x.find("{*}_height").text)) for x in r.find("{*}Height"))
        hts[rid] = h
    def end(rid, e):   # position, cap sortant du noeud, hauteur
        cs = tiles[rid]
        if e == 0: c = cs[0]; return (c["x"], c["z"]), math.atan2(c["tz"], c["tx"]), hts[rid][0][1]
        x, z, tx, tz = T.advance(cs[-1]); return (x, z), math.atan2(-tz, -tx), hts[rid][-1][1]
    dang = lambda a, b: abs((a - b + math.pi) % (2 * math.pi) - math.pi)
    nodes = list(root.iter("{*}Network-cTrackNode")); st = {"gap": [], "z": [], "kink2": [], "stem": [], "div": [], "free": 0, "n2": 0, "n3": 0}; bad = []
    for n in nodes:
        cs = [(c.find(".//{*}DevString").text, int(float(c.find(".//{*}Position").text))) for c in n.findall(".//{*}Network-cNetworkNode-sRConnection")]
        if len(cs) == 1: st["free"] += 1; continue
        E = [end(g, e) for g, e in cs]; P = [e[0] for e in E]
        gap = max(math.hypot(P[i][0] - P[0][0], P[i][1] - P[0][1]) for i in range(len(P))); st["gap"].append(gap)
        st["z"].append(max(e[2] for e in E) - min(e[2] for e in E))
        if len(cs) == 2:
            st["n2"] += 1; st["kink2"].append(math.degrees(dang(E[0][1], E[1][1] + math.pi)))
        elif len(cs) == 3:
            st["n3"] += 1; stem = E[0][1]
            a1, a2 = dang(E[1][1], stem + math.pi), dang(E[2][1], stem + math.pi); lo, hi = sorted((a1, a2))
            st["stem"].append(math.degrees(lo)); st["div"].append(math.degrees(hi))
            if gap > 0.1 or math.degrees(lo) > 5 or math.degrees(hi) > 45: bad.append((cs[0][0][:8], round(gap, 3), round(math.degrees(lo), 1), round(math.degrees(hi), 1)))
    f = lambda a: "max %.3f / moy %.3f (n=%d)" % (max(a), sum(a) / len(a), len(a)) if a else "-"
    print("noeuds : %d a 2 connexions, %d aiguillages, %d bouts libres" % (st["n2"], st["n3"], st["free"]))
    print("ecart de position aux noeuds (m) :", f(st["gap"])); print("ecart de hauteur aux noeuds (m) :", f(st["z"]))
    print("rupture de cap noeuds a 2 connexions (deg) :", f(st["kink2"]))
    print("aiguillages : tige -> voie directe (deg) :", f(st["stem"]), "; tige -> voie deviee (deg) :", f(st["div"]))
    if bad: print("aiguillages douteux :", bad[:10])

if __name__ == "__main__": main(sys.argv[1])
