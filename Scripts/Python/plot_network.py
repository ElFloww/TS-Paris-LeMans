"""Trace le reseau d'une route generee (relit les .bin) : voies en bleu, aiguillages en rouge (tige = carre).
Usage : python plot_network.py <dossier_route_GUID> <sortie.png> [xmin xmax zmin zmax]  (coordonnees locales TSC)"""
import sys, os, glob, math, subprocess, tempfile
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from lxml import etree
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tsc_tiles as T
SERZ = r"D:\Programmes\Steam\steamapps\common\RailWorks\serz.exe"
rdir, out = sys.argv[1], sys.argv[2]; box = [float(a) for a in sys.argv[3:7]] if len(sys.argv) >= 7 else None
tmp = tempfile.mkdtemp(prefix="plotn_")
def conv(f): subprocess.run([SERZ, f, "/xml:" + os.path.join(tmp, os.path.basename(f)[:-4] + ".xml")], capture_output=True)
files = [os.path.join(rdir, "Networks", "Tracks.bin")] + glob.glob(os.path.join(rdir, "Networks", "Track Tiles", "*.bin"))
with ThreadPoolExecutor(6) as ex: list(ex.map(conv, files))
tiles = {}
for f in glob.glob(tmp + r"\[+-]*.xml"):
    for rid, cs in T.read_tile(f): tiles[rid] = cs
root = etree.parse(os.path.join(tmp, "Tracks.xml")).getroot()
fig, ax = plt.subplots(figsize=(16, 10))
for rid, cs in tiles.items():
    pts = []
    for c in cs:
        for u in np.linspace(0, c["len"], max(2, int(c["len"] / 3) + 1)):
            pts.append(T.advance({**c, "len": u})[:2] if c["type"] == "cCurveArc" else (c["x"] + c["tx"] * u, c["z"] + c["tz"] * u))
    P = np.array(pts); ax.plot(P[:, 0], P[:, 1], "b-", lw=1)
for n in root.iter("{*}Network-cTrackNode"):
    cs = n.findall(".//{*}Network-cNetworkNode-sRConnection")
    if len(cs) != 3: continue
    g = cs[0].find(".//{*}DevString").text; e = int(float(cs[0].find(".//{*}Position").text)); c = tiles[g][0] if e == 0 else tiles[g][-1]
    x, z = (c["x"], c["z"]) if e == 0 else T.advance(c)[:2]; ax.plot(x, z, "rs", ms=5)
if box: ax.set_xlim(box[0], box[1]); ax.set_ylim(box[2], box[3])
ax.set_aspect(1); ax.grid(alpha=.3); plt.savefig(out, dpi=70)
