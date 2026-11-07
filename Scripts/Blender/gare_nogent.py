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
    t["PierreBlanche"] = tex_blocks((0.86, 0.83, 0.74), 0.015, 8, 3, 2, (0.70, 0.67, 0.60))
    t["Brique"] = tex_blocks((0.55, 0.22, 0.16), 0.035, 16, 8, 2, (0.62, 0.58, 0.52))
    sl = tex_blocks((0.20, 0.22, 0.26), 0.02, 16, 6, 1, (0.12, 0.13, 0.16)); t["Ardoise"] = sl
    t["Crepi"] = np.full((S, S, 3), (0.88, 0.84, 0.72)) + noise(S, S, 0.015, 3)[..., None]
    g = np.full((S, S, 3), (0.20, 0.26, 0.32)); g[:S // 2, :] += 0.07; g[:, S // 2 - 3:S // 2 + 3] = (0.78, 0.76, 0.70); g[S // 3 - 3:S // 3 + 3, :] = (0.78, 0.76, 0.70); g[2 * S // 3 - 3:2 * S // 3 + 3, :] = (0.78, 0.76, 0.70)
    t["Vitrage"] = g
    t["Fer"] = np.full((S, S, 3), (0.10, 0.20, 0.17)) + noise(S, S, 0.01)[..., None]
    d = np.full((S, S, 3), (0.34, 0.20, 0.12)) + noise(S, S, 0.015, 2)[..., None]; d[:, ::32] *= 0.7; t["Porte"] = d
    t["Zinc"] = np.full((S, S, 3), (0.42, 0.45, 0.47)) + noise(S, S, 0.015, 1)[..., None]
    t["Beton"] = np.full((S, S, 3), (0.62, 0.62, 0.60)) + noise(S, S, 0.03, 2)[..., None]
    s = np.full((S, S, 3), 0.95); s[:6] = s[-6:] = 0.05; s[:, :6] = s[:, -6:] = 0.05; t["Panneau"] = s
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
             "Fer": "Fer", "Porte": "Porte", "Zinc": "Zinc", "Beton": "Beton", "Panneau": "Panneau", "Noir": "Noir"}
    mats = {k: new_mat(k, imgs[v]) for k, v in names.items()}
    mats["Pierre"] = mats["PierreBlanche"]
    B = Builder({k: v for k, v in mats.items() if k != "Pierre"}); B.mats = mats; B.names = [k for k in mats if k != "Pierre"]
    B.names = list(names)
    B.mats = {k: mats[k] for k in names}
    # ---- soubassement et murs
    # aile gauche (X −19,5 → −5,5), pavillon (−5,5 → 5,5), aile droite (5,5 → 15)
    B.box(-19.5, -5.5, 0, 7.0, 0, 4.4, "Crepi", 3.0)                 # aile gauche : enduit clair sous la marquise
    B.box(-5.5, 5.5, 0, 9.0, 0, 6.8, "Moellon", 2.0)                 # pavillon central : moellons
    B.box(5.5, 15.0, 0, 7.5, 0, 4.6, "Moellon", 2.0)                 # aile droite : moellons
    # chaînes d'angle en pierre blanche
    for x in (-5.5, 5.5):
        B.box(x - 0.35, x + 0.35, -0.06, 0.0, 0.0, 6.9, "PierreBlanche", 2.0)
    B.box(14.65, 15.05, -0.06, 0.0, 0.0, 4.7, "PierreBlanche", 2.0)
    # bandeau et corniche
    B.box(-19.5, 15.0, -0.12, 0.0, 4.2, 4.5, "PierreBlanche", 2.0)
    B.box(-5.5, 5.5, -0.12, 0.0, 6.4, 6.9, "PierreBlanche", 2.0)
    # plinth
    B.box(-19.5, 15.0, -0.1, 0.0, 0.0, 0.5, "Beton", 2.0)
    # ---- toits
    B.hip_roof(-19.5, -5.5, 0, 7.0, 4.4, 2.0, over=0.6, mat="Ardoise")
    B.hip_roof(-5.5, 5.5, 0, 9.0, 6.8, 3.2, over=0.6, mat="Ardoise")
    B.hip_roof(5.5, 15.0, 0, 7.5, 4.6, 2.2, over=0.5, mat="Ardoise")
    # souches de cheminée en brique sur le pavillon
    B.box(-3.2, -2.4, 3.0, 3.8, 8.6, 11.0, "Brique", 1.0); B.box(2.2, 3.0, 3.0, 3.8, 8.6, 11.0, "Brique", 1.0)
    # lucarnes en pierre sur la croupe façade (avant-corps)
    B.box(-1.6, -0.2, -0.2, 0.8, 6.9, 8.6, "PierreBlanche", 1.5); B.box(0.2, 1.6, -0.2, 0.8, 6.9, 8.6, "PierreBlanche", 1.5)
    # ---- ouvertures : pavillon (rez cintré + étage), aile gauche (portes + fenêtres), aile droite (grandes baies cintrées briques)
    for cx in (-3.6, 0.0, 3.6):
        B.window(cx, 0.0, 1.0, 1.1, 2.4, True); B.window(cx, 0.0, 4.2, 1.0, 1.8, False)
    for cx in (-17.5, -14.5, -11.5, -8.5):
        B.window(cx, 0.0, 0.9, 1.2, 2.6, True)
    B.arch(-19.5 + 0.0, 0.0, 0.0, 0.01, 0.01, "Noir")  if False else None
    for cx in (8.5, 12.0):
        B.window(cx, 0.0, 0.9, 1.6, 2.9, True, frame="Brique")
    # portes (aile gauche)
    B.arch(-13.0, -0.04, 0.0, 1.4, 2.8, "Porte", off=0.04)
    # panneau du nom de la gare sur la façade, côté droit
    B.box(5.9, 11.1, -0.18, -0.10, 3.8, 4.2, "Panneau", 2.0)
    # ---- marquise en fer : poteaux (0,15 m) tous les 3,6 m, toit incliné en zinc
    xs = np.arange(-19.0, 5.6, 3.6)
    for x in xs:
        B.box(x - 0.08, x + 0.08, -3.1, -2.95, 0.0, 3.5, "Fer", 1.0)
    B.box(-19.5, 6.0, -3.2, -2.9, 3.4, 3.55, "Fer", 1.0)
    pts = [Vector((-19.5, 0.0, 4.15)), Vector((6.0, 0.0, 4.15)), Vector((6.0, -3.4, 3.55)), Vector((-19.5, -3.4, 3.55))]
    B.face(pts, "Zinc", 2.0); B.face(list(reversed(pts)), "Zinc", 2.0)
    # ---- bancs bleus sous la marquise (deux)
    for x in (-9.0, -3.0): B.box(x - 0.9, x + 0.9, -2.2, -1.8, 0.0, 0.45, "Fer", 1.0)
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
