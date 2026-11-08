"""Controle visuel des batiments BD TOPO (150 m de V1) sur 6 extraits orthophoto IGN de 500 m x 500 m.
Orthophoto : WMS-R Geoplateforme ORTHOIMAGERY.ORTHOPHOTOS (licence ouverte), cache dans GeographicData/Raw/ortho/.
Sorties : Tests/Phase1/previews/ortho/maisons_<gare>.png. Lit GeographicData/Processed/layers/batiments.json (sortie de batiments_couloir_150m.py)."""
import json, os, sys, time, urllib.request
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import LineCollection
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import batiments_couloir_150m as M   # voie_runs, proj, T (meme projection Lambert-93)

GARES = [  # (libelle exact dans liste-des-gares, slug de fichier)
    ("Nogent-le-Rotrou", "nogent_le_rotrou"),
    ("La Ferté-Bernard", "la_ferte_bernard"),
    ("Sceaux-Boësse", "sceaux_boesse"),
    ("Connerré-Beillé", "connerre_beille"),
    ("Champagné", "champagne"),
    ("Le Mans", "le_mans"),
]
DEMI = 250.0   # m : extrait de 500 m x 500 m
RAW_ORTHO = os.path.join(ROOT, "GeographicData", "Raw", "ortho"); os.makedirs(RAW_ORTHO, exist_ok=True)
OUT_DIR = os.path.join(ROOT, "Tests", "Phase1", "previews", "ortho"); os.makedirs(OUT_DIR, exist_ok=True)
WMS = ("https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=ORTHOIMAGERY.ORTHOPHOTOS"
       "&STYLES=&CRS=EPSG:2154&BBOX=%s,%s,%s,%s&WIDTH=1000&HEIGHT=1000&FORMAT=image/jpeg")
UA = "TSC-route-builder/1.0"

def gare_xy():
    G = json.load(open(os.path.join(ROOT, "GeographicData", "Raw", "sncf", "liste-des-gares_420000.json"), encoding="utf-8"))
    res = {}
    for lib, slug in GARES:
        hits = [g for g in G if g.get("libelle") == lib]
        if not hits: raise SystemExit("gare introuvable : " + lib)
        res[lib] = (slug, hits[0]["x_wgs84"], hits[0]["y_wgs84"])
    return res

def fetch_ortho(slug, bbox):
    fn = os.path.join(RAW_ORTHO, f"ortho_{slug}_500m.jpg")
    if not os.path.exists(fn):
        url = WMS % tuple(f"{v:.1f}" for v in bbox)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
            open(fn, "wb").write(r.read())
        time.sleep(0.2)
    return fn

def main():
    bat = json.load(open(os.path.join(ROOT, "GeographicData", "Processed", "layers", "batiments.json"), encoding="utf-8"))
    polys = []
    for f in bat["features"]:
        for ring in f["geometry"]["coordinates"]:
            xy = M.proj([(x, y) for x, y in ring[0]])
            polys.append((xy, f["properties"]["ferroviaire"]))
    V1 = [M.proj(r) for r in M.voie_runs("420000-1-V1")]
    V2r = M.voie_runs("420000-1-V2"); V2 = [M.proj(r) for r in V2r] if V2r else []

    for lib, (slug, lon, lat) in gare_xy().items():
        cx, cy = M.T.transform(lon, lat)
        bbox = (cx - DEMI, cy - DEMI, cx + DEMI, cy + DEMI)
        img = fetch_ortho(slug, bbox)
        fig, ax = plt.subplots(figsize=(9, 9), dpi=110)
        ax.imshow(plt.imread(img), extent=(bbox[0], bbox[2], bbox[1], bbox[3]))
        n_in = 0
        for xy, ferro in polys:
            if not any(bbox[0] - 5 < x < bbox[2] + 5 and bbox[1] - 5 < y < bbox[3] + 5 for x, y in xy): continue
            n_in += 1
            ax.add_patch(MplPolygon(xy, closed=True, fill=False, edgecolor="yellow", linewidth=0.9))
        ax.add_collection(LineCollection(V1, colors="red", linewidths=1.6))
        if V2: ax.add_collection(LineCollection(V2, colors="red", linewidths=1.0, linestyles="dashed"))
        ax.plot([cx], [cy], marker="+", color="cyan", markersize=12)
        ax.set_xlim(bbox[0], bbox[2]); ax.set_ylim(bbox[1], bbox[3]); ax.set_aspect("equal")
        ax.set_title(f"{lib} : extrait 500 m x 500 m (Lambert-93)\n"
                     f"orthophoto IGN ; contours jaunes = BD TOPO batiment < 150 m de V1 ; rouge = V1/V2", fontsize=9)
        ax.set_xlabel("X L93 (m)"); ax.set_ylabel("Y L93 (m)")
        out = os.path.join(OUT_DIR, f"maisons_{slug}.png")
        fig.tight_layout(); fig.savefig(out); plt.close(fig)
        print(lib, "->", out, "| batiments dans l'extrait :", n_in)

if __name__ == "__main__":
    main()
