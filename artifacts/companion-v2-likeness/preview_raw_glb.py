"""Render a 4-panel Cycles inspection sheet and print bounds/materials for a raw GLB candidate."""

from __future__ import annotations

import math
import os
import sys
import tempfile
import numpy as np
import bpy
from mathutils import Vector


def parse_args() -> tuple[str, str]:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    base = r"d:\omni-workstation\projects\ZacharyPortfolio\artifacts\companion-v2-likeness"
    glb_path = os.path.join(base, "raw_companion.glb")
    out_png = os.path.join(base, "raw_companion_preview.png")
    i = 0
    while i < len(argv):
        if argv[i] == "--glb" and i + 1 < len(argv):
            glb_path = argv[i + 1]
            i += 2
        elif argv[i] == "--out" and i + 1 < len(argv):
            out_png = argv[i + 1]
            i += 2
        else:
            i += 1
    return glb_path, out_png


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    glb_path, out_png = parse_args()
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"Missing raw GLB: {glb_path}")

    clear_scene()
    bpy.ops.import_scene.gltf(filepath=glb_path)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    print(f"\n=== Raw GLB Report: {glb_path} ({os.path.getsize(glb_path)} bytes) ===")
    print(f"Mesh count: {len(meshes)}")
    total_verts = 0
    total_tris = 0
    for m in meshes:
        v_cnt = len(m.data.vertices)
        t_cnt = sum(max(1, len(p.vertices) - 2) for p in m.data.polygons)
        total_verts += v_cnt
        total_tris += t_cnt
        print(f"  Mesh '{m.name}': verts={v_cnt}, tris={t_cnt}, mats={[mat.name if mat else None for mat in m.data.materials]}")
    print(f"Total: verts={total_verts}, tris={total_tris}")

    for img in bpy.data.images:
        print(f"  Image '{img.name}': size={img.size[0]}x{img.size[1]}, channels={img.channels}")

    # Temporary normalization empty to inspect framing & detect facing axis cleanly
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.update()

    # Evaluate world-space mesh bounds before parenting
    min_co = Vector((1e9, 1e9, 1e9))
    max_co = Vector((-1e9, -1e9, -1e9))
    for obj in meshes:
        mw = obj.matrix_world
        for v in obj.data.vertices:
            wp = mw @ v.co
            min_co.x = min(min_co.x, wp.x)
            min_co.y = min(min_co.y, wp.y)
            min_co.z = min(min_co.z, wp.z)
            max_co.x = max(max_co.x, wp.x)
            max_co.y = max(max_co.y, wp.y)
            max_co.z = max(max_co.z, wp.z)

    print(f"Raw world bounds: X=[{min_co.x:.4f}, {max_co.x:.4f}], Y=[{min_co.y:.4f}, {max_co.y:.4f}], Z=[{min_co.z:.4f}, {max_co.z:.4f}]")

    span = max_co - min_co
    height = max(1e-4, span.z)
    scale_factor = 1.62 / height
    cx = 0.5 * (min_co.x + max_co.x)
    cy = 0.5 * (min_co.y + max_co.y)

    # Wrap root objects under PreviewRoot to inspect normalized 1.62m standing height
    root = bpy.data.objects.new("PreviewRoot", None)
    bpy.context.scene.collection.objects.link(root)
    top_objs = [o for o in bpy.data.objects if o.parent is None and o != root]
    for o in top_objs:
        o.parent = root
    root.scale = (scale_factor, scale_factor, scale_factor)
    root.location = Vector((-cx * scale_factor, -cy * scale_factor, -min_co.z * scale_factor))
    bpy.context.view_layer.update()

    # Neutral bright studio lighting so any dark artifacts or backward orientation stand out
    scene = bpy.context.scene
    world = bpy.data.worlds.new("RawPreviewWorld")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.18, 0.19, 0.21, 1.0)
        bg.inputs["Strength"].default_value = 0.85

    def add_area(name: str, loc: tuple[float, float, float], target: tuple[float, float, float], energy: float, size: float):
        ld = bpy.data.lights.new(name=name, type="AREA")
        ld.energy = energy
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        look_at(lo, Vector(target))
        scene.collection.objects.link(lo)

    add_area("Key", (1.6, -2.4, 2.0), (0, 0, 1.0), 160.0, 2.2)
    add_area("Fill", (-1.8, -2.0, 1.5), (0, 0, 1.0), 95.0, 2.2)
    add_area("BackKey", (0.5, 2.5, 1.8), (0, 0, 1.0), 140.0, 2.2)
    add_area("SideLight", (-2.4, 0.3, 1.6), (0, 0, 1.0), 110.0, 2.0)

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.image_settings.file_format = "PNG"

    panels: list[np.ndarray] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        views = [
            ("1_negY_full", (0.0, -3.1, 0.88), (0.0, 0.0, 0.81), 42.0),
            ("2_posY_full", (0.0, 3.1, 0.88), (0.0, 0.0, 0.81), 42.0),
            ("3_negY_head", (-0.18, -0.78, 1.46), (0.0, 0.0, 1.42), 68.0),
            ("4_negX_side", (-3.1, 0.0, 0.88), (0.0, 0.0, 0.81), 42.0),
        ]
        for label, loc, tgt, lens in views:
            cam_data.lens = lens
            cam_obj.location = Vector(loc)
            look_at(cam_obj, Vector(tgt))
            p = os.path.join(tmpdir, f"{label}.png")
            scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(p, check_existing=False)
            arr = np.empty(512 * 512 * 4, dtype=np.float32)
            img.pixels.foreach_get(arr)
            panels.append(arr.reshape((512, 512, 4)))
            bpy.data.images.remove(img)

    sheet = np.zeros((1024, 1024, 4), dtype=np.float32)
    sheet[512:1024, 0:512] = panels[0]
    sheet[512:1024, 512:1024] = panels[1]
    sheet[0:512, 0:512] = panels[2]
    sheet[0:512, 512:1024] = panels[3]

    out_img = bpy.data.images.new("RawPreviewSheet", width=1024, height=1024, alpha=True)
    out_img.pixels.foreach_set(sheet.ravel())
    out_img.filepath_raw = out_png
    out_img.file_format = "PNG"
    out_img.save()
    bpy.data.images.remove(out_img)
    print(f"Saved preview sheet: {out_png}")


if __name__ == "__main__":
    main()
