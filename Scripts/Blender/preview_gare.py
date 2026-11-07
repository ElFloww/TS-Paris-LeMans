"""Rendus Workbench (texture) du modele GareNogent : cote place et cote quai. Lance apres gare_nogent.py dans la meme session Blender."""
import bpy, math, os
from mathutils import Vector
OUT = r"E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\Tests\Phase1\previews"
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x, sc.render.resolution_y = 1400, 700
sc.world = sc.world or bpy.data.worlds.new("w"); sc.world.color = (0.55, 0.7, 0.9)
sc.render.film_transparent = False
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 24
for name, pos, tgt in (("place", (0, 38, 1.8), (0, 0, 3.2)), ("quai", (0, -30, 1.8), (0, 0, 3.0))):
    pos, tgt = Vector(pos), Vector(tgt); pos.x = -4 if name == "place" else 6
    cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "gare_" + name + ".png"); bpy.ops.render.render(write_still=True)

import json   # diagnostic : faces regardant +Y a y=10 (mur cote place du pavillon)
ob = [o for o in bpy.data.objects if o.name.startswith("GareNogent") or o.name.endswith("GareNogent")][0]
me = ob.data; r = []
for p in me.polygons:
    c = p.center
    if abs(c.y - 10.0) < 0.01 and p.normal.length > 0: r.append((round(c.x, 1), round(c.z, 1), [round(v, 2) for v in p.normal], me.materials[p.material_index].name))
json.dump({"n": len(me.polygons), "y10": r[:30], "obj": ob.name}, open(os.path.join(OUT, "dbg.json"), "w"))
