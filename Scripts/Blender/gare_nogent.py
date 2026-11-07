"""Bâtiment voyageurs de Nogent-le-Rotrou (modèle de référence : photo Commons « Gare de nogent le rotrou - panoramio.jpg »).
Exécuté dans Blender (serveur MCP) : génère textures PNG, maillage et export IGS (add-on BRIAGE).

Repère : X le long de la voie, Y perpendiculaire (façade côté quai à Y=0, corps du bâtiment vers +Y), Z vers le haut, mètres.
Dimensions estimées d'après la photo (à affiner) : pavillon central 11 x 9 m (2 niveaux + combles), aile gauche 14 x 7 m, aile droite 9,5 x 7,5 m,
marquise en fer 3,2 m côté quai sur 25 m.
"""
import bpy, bmesh, os, math, random
import numpy as np
from mathutils import Vector

NAME = "GareNogent"
SRC = r"D:\Programmes\Steam\steamapps\common\RailWorks\Source\PCLM\Gares\Scenery\Buildings"
TEX = os.path.join(SRC, "Textures", "Nogent")
os.makedirs(TEX, exist_ok=True)
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- textures procédurales (256 x 256, répétables)
def save_png(name, arr):
    h, w, _ = arr.shape
    img = bpy.data.images.new(name, w, h, alpha=False)
    a = np.clip(arr, 0, 1).astype(np.float32)
    a = np.dstack([a, np.ones((h, w, 1), np.float32)])
    img.pixels = a.ravel().tolist()
    img.filepath_raw = os.path.join(TEX, name + ".png"); img.file_format = "PNG"; img.save()
    return img

def noise(h, w, amp, scale=1):
    n = rng.normal(0, amp, (h // scale + 1, w // scale + 1))
    return np.kron(n, np.ones((scale, scale)))[:h, :w]

def tex_blocks(base, var, rows, cols, mortar, mortar_c, jitter=0.0, size=256):
    """appareil de blocs : base RGB, variation par bloc, joints"""
    a = np.zeros((size, size, 3)); bh = size // rows
    for r in range(rows):
        off = (size // cols) // 2 if r % 2 else 0
        bw = size // cols
        for c in range(cols + 1):
            x0 = c * bw - off; col = np.array(base) + rng.normal(0, var, 3) * np.array([1, 1, 1])
            xs = slice(max(x0, 0), min(x0 + bw, size)); ys = slice(r * bh, (r + 1) * bh)
            if xs.start < xs.stop: a[ys, xs] = col
    a += noise(size, size, 0.02, 2)[..., None]
    for r in range(rows): a[r * bh:r * bh + mortar] = mortar_c
    for r in range(rows):
        off = (size // cols) // 2 if r % 2 else 0
        for c in range(cols + 1):
            x = c * (size // cols) - off
            if 0 <= x < size: a[r * bh:(r + 1) * bh, x:x + mortar] = mortar_c
    return a

def make_textures():
    S = 256; t = {}
    # moellons (silex / calcaire) : cailloux irréguliers beige-gris sur joint clair
    a = np.full((S, S, 3), (0.66, 0.62, 0.55))
    for _ in range(230):
        cx, cy = rng.integers(0, S, 2); rx, ry = rng.integers(9, 20), rng.integers(7, 14); tone = rng.uniform(0.40, 0.72)
        col = np.array([tone, tone * 0.96, tone * 0.88]) + rng.normal(0, 0.02, 3)
        yy, xx = np.ogrid[:S, :S]; m = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) < 1
        a[m] = col
    t["Moellon"] = a + noise(S, S, 0.02)[..., None]
    t["PierreBlanche"] = tex_blocks((0.88, 0.84, 0.72), 0.015, 8, 3, 2, (0.70, 0.67, 0.60))
    t["Brique"] = tex_blocks((0.55, 0.22, 0.16), 0.035, 16, 8, 2, (0.62, 0.58, 0.52))
    sl = tex_blocks((0.20, 0.22, 0.26), 0.02, 16, 6, 1, (0.12, 0.13, 0.16)); t["Ardoise"] = sl
    t["Crepi"] = np.full((S, S, 3), (0.92, 0.87, 0.70)) + noise(S, S, 0.015, 3)[..., None]
    g = np.full((S, S, 3), (0.20, 0.26, 0.32)); g[:S // 2, :] += 0.07; g[:, S // 2 - 3:S // 2 + 3] = (0.78, 0.76, 0.70); g[S // 3 - 3:S // 3 + 3, :] = (0.78, 0.76, 0.70); g[2 * S // 3 - 3:2 * S // 3 + 3, :] = (0.78, 0.76, 0.70)
    t["Vitrage"] = g
    t["Fer"] = np.full((S, S, 3), (0.10, 0.20, 0.17)) + noise(S, S, 0.01)[..., None]
    d = np.full((S, S, 3), (0.34, 0.20, 0.12)) + noise(S, S, 0.015, 2)[..., None]; d[:, ::32] *= 0.7; t["Porte"] = d
    t["Zinc"] = np.full((S, S, 3), (0.42, 0.45, 0.47)) + noise(S, S, 0.015, 1)[..., None]
    t["Beton"] = np.full((S, S, 3), (0.62, 0.62, 0.60)) + noise(S, S, 0.03, 2)[..., None]
    s = np.full((S, S, 3), 0.95); s[:6] = s[-6:] = 0.05; s[:, :6] = s[:, -6:] = 0.05; t["Panneau"] = s
    t["Volet"] = np.full((S, S, 3), (0.80, 0.46, 0.36)) + noise(S, S, 0.02, 2)[..., None]
    t["Noir"] = np.full((S, S, 3), (0.05, 0.05, 0.05))
    return {k: save_png("Nogent_" + k, v) for k, v in t.items()}

# ---------------------------------------------------------------- géométrie
def new_mat(name, img):
    m = bpy.data.materials.new("N_" + name); m.use_nodes = True
    m.IgsMat.shader_name = "TexDiff"; m.IgsMat.textures[0].texture = img
    nt = m.node_tree; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    nt.links.new(tx.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m

class Builder:
    def __init__(self, mats):
        self.mats = mats; self.me = bpy.data.meshes.new(NAME); self.bm = bmesh.new(); self.names = list(mats)
        self.uv = self.bm.loops.layers.uv.new("UVMap")
    def face(self, pts, mat, scale=2.0, plane=None):
        vs = [self.bm.verts.new(p) for p in pts]
        try: f = self.bm.faces.new(vs)
        except ValueError: return None
        f.material_index = self.names.index(mat)
        n = f.normal if f.normal.length > 0 else Vector((0, 0, 1)); ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            p = l.vert.co
            u, v = (p.y, p.z) if ax == 0 else ((p.x, p.z) if ax == 1 else (p.x, p.y))
            if mat == "Ardoise" and ax == 2: u, v = p.x, p.y
            l[self.uv].uv = (u / scale, v / scale)
        return f
    def quad(self, a, b, c, d, mat, scale=2.0): return self.face([a, b, c, d], mat, scale)
    def box(self, x0, x1, y0, y1, z0, z1, mat, scale=2.0, bottom=False):
        P = lambda x, y, z: Vector((x, y, z))
        self.quad(P(x0, y0, z0), P(x0, y0, z1), P(x1, y0, z1), P(x1, y0, z0), mat, scale)            # façade (−Y)
        self.quad(P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1), P(x0, y1, z0), mat, scale)            # arrière (+Y)
        self.quad(P(x0, y1, z0), P(x0, y1, z1), P(x0, y0, z1), P(x0, y0, z0), mat, scale)            # côté −X
        self.quad(P(x1, y0, z0), P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0), mat, scale)            # côté +X
        self.quad(P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), mat, scale)            # dessus
        if bottom: self.quad(P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0), P(x0, y0, z0), mat, scale)
    def hip_roof(self, x0, x1, y0, y1, z, rise, over=0.5, ridge_len=None, mat="Ardoise"):
        """toit en croupe : base rectangulaire (débord 'over') et faîtage"""
        P = lambda x, y, zz: Vector((x, y, zz))
        X0, X1, Y0, Y1 = x0 - over, x1 + over, y0 - over, y1 + over; w = (Y1 - Y0)
        rl = ridge_len if ridge_len is not None else max((X1 - X0) - w, 0.0)
        cx = (X0 + X1) / 2; ym = (Y0 + Y1) / 2; zt = z + rise
        r0, r1 = cx - rl / 2, cx + rl / 2
        self.face([P(X0, Y0, z), P(r0, ym, zt), P(r1, ym, zt), P(X1, Y0, z)], mat, 2.5)                 # pan côté façade
        self.face([P(X1, Y1, z), P(r1, ym, zt), P(r0, ym, zt), P(X0, Y1, z)], mat, 2.5)                 # pan arrière
        self.face([P(X0, Y1, z), P(r0, ym, zt), P(X0, Y0, z)], mat, 2.5)                                # croupe gauche
        self.face([P(X1, Y0, z), P(r1, ym, zt), P(X1, Y1, z)], mat, 2.5)                                # croupe droite
    def arch(self, cx, y, z0, w, h, mat, off=0.0, seg=8):
        """ouverture cintrée plane sur la façade (normale vers −Y) : rectangle + demi-cercle"""
        r = w / 2; pts = [(cx - r, z0)]
        pts += [(cx - r, z0 + h - r)]
        pts += [(cx - r * math.cos(math.pi * i / seg), z0 + h - r + r * math.sin(math.pi * i / seg)) for i in range(1, seg)]
        pts += [(cx + r, z0 + h - r), (cx + r, z0)]
        self.face([Vector((x, y - off, z)) for (x, z) in reversed(pts)], mat, 1.0)
        # (UV : projection mètres/1 m)
    def window(self, cx, y, z0, w, h, arched, glass="Vitrage", frame="Pierre", fr=0.22):
        if arched:
            self.arch(cx, y, z0 - fr, w + 2 * fr, h + fr, "Brique", off=0.03)
            self.arch(cx, y, z0, w, h, glass, off=0.06)
        else:
            self.quad(Vector((cx - w / 2 - fr, y - 0.03, z0 - fr)), Vector((cx - w / 2 - fr, y - 0.03, z0 + h + fr)), Vector((cx + w / 2 + fr, y - 0.03, z0 + h + fr)), Vector((cx + w / 2 + fr, y - 0.03, z0 - fr)), "PierreBlanche", 2.0)
            self.quad(Vector((cx - w / 2, y - 0.06, z0)), Vector((cx - w / 2, y - 0.06, z0 + h)), Vector((cx + w / 2, y - 0.06, z0 + h)), Vector((cx + w / 2, y - 0.06, z0)), glass, 1.0)
    def finish(self):
        self.bm.normal_update(); self.bm.to_mesh(self.me); self.bm.free()
        o = bpy.data.objects.new(NAME, self.me)
        for k in self.names: self.me.materials.append(self.mats[k])
        return o

def build():
    imgs = make_textures()
    names = {"Moellon": "Moellon", "PierreBlanche": "PierreBlanche", "Brique": "Brique", "Ardoise": "Ardoise", "Crepi": "Crepi", "Vitrage": "Vitrage",
             "Fer": "Fer", "Porte": "Porte", "Zinc": "Zinc", "Beton": "Beton", "Panneau": "Panneau", "Noir": "Noir", "Volet": "Volet"}
    mats = {k: new_mat(k, imgs[v]) for k, v in names.items()}
    mats["Pierre"] = mats["PierreBlanche"]
    B = Builder({k: v for k, v in mats.items() if k != "Pierre"}); B.mats = mats; B.names = [k for k in mats if k != "Pierre"]
    B.names = list(names)
    B.mats = {k: mats[k] for k in names}
    # Repère modèle : X croît vers Paris (poser avec heading 180), façade côté voies à Y=0, corps vers +Y.
    # Emprises BD TOPO (IGN) : BV 1 niveau ~64 m (L -70..-6 m du point gare), pavillon central 2 niveaux; dimensions fines à vérifier.
    W = lambda x0, x1, d, h, mat: B.box(x0, x1, 0, d, 0, h, mat, 2.5)
    W(-6, 6, 10.0, 7.2, "Crepi")                      # pavillon central 2 niveaux, enduit crème
    W(6, 30, 8.0, 4.6, "Moellon")                     # aile côté Paris : moellons, 1 niveau
    W(-20, -6, 8.0, 4.6, "Moellon")                   # aile côté Le Mans
    W(-32, -20, 9.0, 8.4, "Brique")                   # bâtiment 2 niveaux en brique rouge
    B.box(-32, -31.9, 0, 9.0, 0, 8.4, "Brique", 1.0)
    # bandeau/soubassement rouge, chaînes d'angle en pierre
    B.box(-20, 30, -0.1, 0, 0, 0.7, "Brique", 1.0)
    B.box(-6, 6, -0.1, 0, 0.0, 0.7, "Brique", 1.0)
    for x in (-6, 6): B.box(x - 0.35, x + 0.35, -0.08, 0, 0.7, 7.2, "PierreBlanche", 1.5)
    B.box(-6.2, 6.2, -0.15, 0, 3.4, 3.7, "PierreBlanche", 1.0)
    B.box(-6.2, 6.2, -0.15, 0, 6.9, 7.3, "PierreBlanche", 1.0)
    B.box(-20, 30, -0.12, 0, 4.3, 4.6, "PierreBlanche", 1.0)
    # toitures ardoise en croupe + cheminées briques
    B.hip_roof(-6, 6, 0, 10, 7.2, 3.4, over=0.6)
    B.hip_roof(6, 30, 0, 8, 4.6, 2.4, over=0.5, ridge_len=18)
    B.hip_roof(-20, -6, 0, 8, 4.6, 2.4, over=0.5, ridge_len=8)
    B.hip_roof(-32, -20, 0, 9, 8.4, 3.2, over=0.4)
    for x in (-3.5, 3.5): B.box(x - 0.45, x + 0.45, 4.0, 4.9, 8.6, 11.2, "Brique", 1.0)
    B.box(-26.5, -25.5, 4.0, 5.0, 10.5, 12.5, "Brique", 1.0)
    # fronton central à horloge
    B.box(-1.8, 1.8, -0.2, 0.6, 7.2, 9.4, "PierreBlanche", 1.5)
    B.quad(Vector((-0.8, -0.25, 7.6)), Vector((-0.8, -0.25, 8.8)), Vector((0.8, -0.25, 8.8)), Vector((0.8, -0.25, 7.6)), "Panneau", 1.6)
    # ouvertures : pavillon (3 portes cintrées au rez, 3 fenêtres à volets saumon à l'étage), moulures rouges
    def shutters(cx, z0, w, h):
        for sgn in (-1, 1):
            xx = cx + sgn * (w / 2 + 0.28)
            B.quad(Vector((xx - 0.25, -0.1, z0)), Vector((xx - 0.25, -0.1, z0 + h)), Vector((xx + 0.25, -0.1, z0 + h)), Vector((xx + 0.25, -0.1, z0)), "Volet", 1.0)
    for cx in (-3.6, 0.0, 3.6):
        B.window(cx, 0.0, 0.8, 1.5, 2.7, True, glass="Porte"); B.window(cx, 0.0, 4.2, 1.1, 2.0, True); shutters(cx, 4.2, 1.1, 2.0)
    for cx in [3.5 * i + 11 for i in range(6)] + [-9.5, -13.0, -16.5]:
        B.window(cx, 0.0, 1.0, 1.1, 2.3, True); shutters(cx, 1.0, 1.1, 2.3)
    for cx in (-29.2, -26.0, -22.8):
        for z0 in (1.0, 5.0): B.window(cx, 0.0, z0, 1.1, 2.0, False, glass="Vitrage"); shutters(cx, z0, 1.1, 2.0)
    B.box(8, 18, -0.2, -0.12, 4.9, 5.3, "Panneau", 2.0)       # panneau NOGENT-LE-ROTROU
    # marquise métallique côté quai (aile Paris + pavillon), poteaux fer tous les 4 m
    for x in np.arange(-6.0, 30.1, 4.0): B.box(x - 0.08, x + 0.08, -3.1, -2.95, 0.0, 3.5, "Fer", 1.0)
    pts = [Vector((-6, 0.0, 4.1)), Vector((30, 0.0, 4.1)), Vector((30, -3.4, 3.55)), Vector((-6, -3.4, 3.55))]
    B.face(pts, "Zinc", 2.0); B.face(list(reversed(pts)), "Zinc", 2.0)
    o = B.finish()
    return o

def export(o):
    col = bpy.data.collections.get("TSC_" + NAME) or bpy.data.collections.new("TSC_" + NAME)
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    col.objects.link(o)
    if bpy.context.object and bpy.context.object.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    out = os.path.join(SRC, NAME + ".igs")
    bpy.ops.export_scene.igs(filepath=out, use_selection=True, target_textures_directory=os.path.join(TEX))
    return out

if __name__ == "__main__" or True:
    for ob in [x for x in bpy.data.objects if x.name.startswith(NAME)]: bpy.data.objects.remove(ob, do_unlink=True)
    obj = build()
    result_path = export(obj)
    result = {"igs": result_path, "faces": len(obj.data.polygons), "materiaux": [m.name for m in obj.data.materials]}
