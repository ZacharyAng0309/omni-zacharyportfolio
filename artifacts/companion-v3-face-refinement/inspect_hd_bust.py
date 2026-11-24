"""Render an 8-panel Blender 5.2 Cycles inspection sheet (4 clay geometry + 4 textured PBR)
for any candidate HD bust GLB so facial structure and texture can be evaluated independently.
"""
from __future__ import annotations

import math
import os
import sys
import tempfile
import numpy as np
import bpy
from mathutils import Vector


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for lgt in list(bpy.data.lights):
        bpy.data.lights.remove(lgt)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_studio() -> None:
    scene = bpy.context.scene
    world = bpy.data.worlds.new("BustInspectWorld")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.12, 0.13, 0.15, 1.0)
        bg.inputs["Strength"].default_value = 0.75

    def add_area(name: str, loc: tuple[float, float, float], tgt: tuple[float, float, float], energy: float, size: float, color=(1.0, 1.0, 1.0)):
        ld = bpy.data.lights.new(name=name, type="AREA")
        ld.energy = energy
        ld.size = size
        ld.color = color
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        look_at(lo, Vector(tgt))
        scene.collection.objects.link(lo)

    # Raking sculptural key + gentle fill + rim so every geometric ridge/dent shows clearly
    add_area("Key", (1.25, -1.65, 1.25), (0.0, 0.0, 0.0), 115.0, 0.9, (1.0, 0.97, 0.93))
    add_area("Fill", (-1.35, -1.45, 0.25), (0.0, 0.0, 0.0), 42.0, 1.5, (0.88, 0.93, 1.0))
    add_area("Rim", (-0.65, 1.55, 1.10), (0.0, 0.0, 0.0), 85.0, 1.2, (1.0, 0.92, 0.80))

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(argv) < 2:
        raise SystemExit("Usage: blender -b --factory-startup -P inspect_hd_bust.py -- <in.glb> <out.png>")
    in_glb = argv[0]
    out_png = argv[1]

    clear_scene()
    bpy.ops.import_scene.gltf(filepath=in_glb)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    assert meshes, f"No mesh in {in_glb}"

    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Normalize to unit height centered at origin for consistent inspection
    verts = obj.data.vertices
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    cx, cy, cz = 0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * (min(zs) + max(zs))
    h = max(1e-5, max(zs) - min(zs))
    sc = 1.0 / h
    for v in verts:
        v.co = Vector(((v.co.x - cx) * sc, (v.co.y - cy) * sc, (v.co.z - cz) * sc))
    obj.data.update()

    tris = sum(max(1, len(p.vertices) - 2) for p in obj.data.polygons)
    imgs_info = [(im.name, list(im.size)) for im in bpy.data.images]
    print(f"Inspect {os.path.basename(in_glb)}: verts={len(verts)}, tris={tris}, raw_dims=({max(xs)-min(xs):.3f},{max(ys)-min(ys):.3f},{h:.3f}), images={imgs_info}")

    orig_mats = list(obj.data.materials)

    # Neutral matte sculptural clay material
    clay_mat = bpy.data.materials.new("InspectClay")
    clay_mat.use_nodes = True
    bsdf = clay_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.58, 0.56, 0.54, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55

    setup_studio()
    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 75.0
    cam_o = bpy.data.objects.new("Cam", cam_d)
    bpy.context.scene.collection.objects.link(cam_o)
    bpy.context.scene.camera = cam_o

    scene = bpy.context.scene
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.image_settings.file_format = "PNG"

    tgt = Vector((0.0, 0.0, 0.06))
    views_clay = [
        ("c_front", (0.0, -1.95, 0.08)),
        ("c_34l", (-1.15, -1.55, 0.10)),
        ("c_34r", (1.15, -1.55, 0.10)),
        ("c_side", (-1.95, 0.0, 0.08)),
    ]
    views_tex = [
        ("t_front", (0.0, -1.95, 0.08)),
        ("t_34l", (-1.15, -1.55, 0.10)),
        ("t_side", (-1.95, 0.0, 0.08)),
        ("t_back", (0.0, 1.95, 0.08)),
    ]

    panels_top: list[np.ndarray] = []
    panels_bot: list[np.ndarray] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        def render_one(label: str, loc: tuple[float, float, float]) -> np.ndarray:
            cam_o.location = Vector(loc)
            look_at(cam_o, tgt)
            p = os.path.join(tmpdir, f"{label}.png")
            scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(p, check_existing=False)
            arr = np.empty(512 * 512 * 4, dtype=np.float32)
            im.pixels.foreach_get(arr)
            bpy.data.images.remove(im)
            return arr.reshape((512, 512, 4))

        # Clay row (top)
        obj.data.materials.clear()
        obj.data.materials.append(clay_mat)
        for lbl, loc in views_clay:
            panels_top.append(render_one(lbl, loc))

        # Textured row (bottom)
        obj.data.materials.clear()
        for m in orig_mats:
            obj.data.materials.append(m)
        for lbl, loc in views_tex:
            panels_bot.append(render_one(lbl, loc))

    sheet = np.zeros((1024, 2048, 4), dtype=np.float32)
    for i in range(4):
        sheet[512:1024, i * 512 : (i + 1) * 512] = panels_top[i]
        sheet[0:512, i * 512 : (i + 1) * 512] = panels_bot[i]

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    out_im = bpy.data.images.new("BustSheet", width=2048, height=1024, alpha=True)
    out_im.pixels.foreach_set(sheet.ravel())
    out_im.filepath_raw = out_png
    out_im.file_format = "PNG"
    out_im.save()
    bpy.data.images.remove(out_im)
    print(f"Saved bust inspection sheet: {out_png}")


if __name__ == "__main__":
    main()
