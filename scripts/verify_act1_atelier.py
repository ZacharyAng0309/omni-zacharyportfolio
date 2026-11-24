#!/usr/bin/env python3
"""
Independently imports `public/models/props/act1_studio.glb` into a clean factory Blender 5.2 session,
verifies structural/geometric/budget invariants, and renders a 4-panel Cycles studio inspection sheet
to `screenshots/act1_atelier_blender_review.png`.
"""
from __future__ import annotations

import math
import os
import tempfile
import numpy as np
import bpy
from mathutils import Euler, Vector


REQUIRED_NODES = [
    "SM_Island_Act1",
    "SM_Atelier_Pedestal",
    "Prop_Blueprint_Tier1",
    "Prop_Blueprint_Tier2",
    "Prop_Blueprint_Tier3",
    "SM_Core_Nucleus",
    "SM_Core_Filament",
    "SM_Gyro_Gimbal_Outer",
    "SM_Gyro_Gimbal_Inner",
]

REQUIRED_MATERIALS = [
    "Mat_Act1_ObsidianBasalt",
    "Mat_Act1_BrushedTitanium",
    "Mat_Act1_NaturalTitanium",
    "Mat_Act1_ChampagneBrass",
    "Mat_Act1_OpticalGlass",
    "Mat_Act1_WarmCove",
]


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def setup_studio_world() -> None:
    scene = bpy.context.scene
    world = bpy.data.worlds.new("AtelierStudioWorld")
    scene.world = world
    nt = world.node_tree
    nt.nodes.clear()

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.015, 0.017, 0.024, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.045, 0.048, 0.062, 1.0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.75
    out = nt.nodes.new("ShaderNodeOutputWorld")

    nt.links.new(tex_coord.outputs["Generated"], sep_xyz.inputs["Vector"])
    nt.links.new(sep_xyz.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    # Soft studio area lights around (-0.55, 0.10, 1.0)
    def add_area(name: str, loc: tuple[float, float, float], rot_deg: tuple[float, float, float], energy: float, size: float, color: tuple[float, float, float]):
        ldata = bpy.data.lights.new(name=name, type="AREA")
        ldata.energy = energy
        ldata.size = size
        ldata.color = color
        lobj = bpy.data.objects.new(name, ldata)
        lobj.location = loc
        lobj.rotation_euler = tuple(math.radians(a) for a in rot_deg)
        scene.collection.objects.link(lobj)

    add_area("KeySoftbox", (1.6, -2.2, 3.2), (55, 0, 36), energy=190.0, size=2.4, color=(1.0, 0.96, 0.90))
    add_area("CoolFill", (-3.2, -1.8, 2.1), (62, 0, -54), energy=95.0, size=2.8, color=(0.78, 0.88, 1.0))
    add_area("ChampagneRim", (-0.8, 2.8, 2.5), (-65, 0, 175), energy=140.0, size=2.0, color=(1.0, 0.85, 0.62))
    add_area("OverheadCanopy", (-0.55, 0.10, 3.8), (0, 0, 0), energy=110.0, size=3.2, color=(0.95, 0.95, 1.0))

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = rot_quat.to_euler()


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    glb_path = os.path.join(root, "public", "models", "props", "act1_studio.glb")
    out_png = os.path.join(root, "screenshots", "act1_atelier_blender_review.png")

    size_bytes = os.path.getsize(glb_path)
    assert size_bytes <= 1.5 * 1024 * 1024, f"GLB exceeds 1.5MB budget: {size_bytes}"

    clear_scene()
    bpy.ops.import_scene.gltf(filepath=glb_path)

    # Verify required nodes & materials exist
    obj_map = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    for name in REQUIRED_NODES:
        assert name in obj_map, f"Missing required node in exported GLB: {name}"

    mat_names = {m.name for m in bpy.data.materials}
    for mname in REQUIRED_MATERIALS:
        assert mname in mat_names, f"Missing required material in exported GLB: {mname}"

    # Verify finite geometry, triangle area > 0, and Z >= 0 grounding
    min_world_z = 999.0
    total_tris = 0
    for name in REQUIRED_NODES:
        o = obj_map[name]
        mesh = o.data
        mesh.calc_loop_triangles()
        tris = len(mesh.loop_triangles)
        total_tris += tris
        assert tris > 0, f"{name} has 0 triangles"
        for v in mesh.vertices:
            wp = o.matrix_world @ v.co
            assert all(math.isfinite(c) for c in wp), f"Non-finite vertex in {name}"
            if wp.z < min_world_z:
                min_world_z = wp.z
    assert min_world_z >= -1e-4, f"Un-grounded Z < 0 detected: {min_world_z}"
    print(f"GLB Verification PASSED: {len(REQUIRED_NODES)} nodes, {len(REQUIRED_MATERIALS)} materials, {total_tris} tris, minZ={min_world_z:.5f}, {size_bytes} bytes")

    setup_studio_world()
    cam_data = bpy.data.cameras.new("ReviewCam")
    cam_obj = bpy.data.objects.new("ReviewCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    scene = bpy.context.scene
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.image_settings.file_format = "PNG"

    # Give gimbals realistic horological tilt angles for initial neutral beauty inspection
    outer_g = obj_map["SM_Gyro_Gimbal_Outer"]
    inner_g = obj_map["SM_Gyro_Gimbal_Inner"]
    t1 = obj_map["Prop_Blueprint_Tier1"]
    t2 = obj_map["Prop_Blueprint_Tier2"]
    t3 = obj_map["Prop_Blueprint_Tier3"]
    nuc = obj_map["SM_Core_Nucleus"]

    outer_g.rotation_euler = Euler((math.radians(24), math.radians(-16), math.radians(10)), "XYZ")
    inner_g.rotation_euler = Euler((math.radians(-32), math.radians(28), math.radians(-18)), "XYZ")

    panels: list[np.ndarray] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        def render_view(label: str, loc: tuple[float, float, float], target: tuple[float, float, float], lens: float) -> None:
            cam_data.lens = lens
            cam_obj.location = Vector(loc)
            look_at(cam_obj, Vector(target))
            p = os.path.join(tmpdir, f"{label}.png")
            scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(p, check_existing=False)
            arr = np.empty(640 * 480 * 4, dtype=np.float32)
            img.pixels.foreach_get(arr)
            panels.append(arr.reshape((480, 640, 4)))
            bpy.data.images.remove(img)

        # 1. Front
        render_view("1_front", (-0.55, -3.55, 1.05), (-0.55, 0.10, 0.92), 45.0)
        # 2. 3/4 Hero
        render_view("2_hero", (-2.65, -2.55, 1.75), (-0.55, 0.10, 0.92), 46.0)

        # 3. Exploded Preview
        base_z1, base_z3 = t1.location.z, t3.location.z
        t1.location.z = base_z1 + 0.34
        t3.location.z = base_z3 - 0.18
        nuc.scale = Vector((1.14, 1.14, 1.14))
        outer_g.rotation_euler = Euler((math.radians(38), math.radians(42), math.radians(25)), "XYZ")
        inner_g.rotation_euler = Euler((math.radians(-48), math.radians(-30), math.radians(60)), "XYZ")
        render_view("3_exploded", (-2.65, -2.65, 1.85), (-0.55, 0.10, 1.02), 42.0)

        # Reset & render Close-Up Core
        t1.location.z = base_z1
        t3.location.z = base_z3
        nuc.scale = Vector((1.0, 1.0, 1.0))
        render_view("4_core", (-1.55, -1.35, 1.50), (-0.55, 0.10, 1.24), 58.0)

    sheet_arr = np.zeros((960, 1280, 4), dtype=np.float32)
    # Blender image buffer rows are bottom-to-top: top row = 480:960, bottom row = 0:480
    sheet_arr[480:960, 0:640] = panels[0]
    sheet_arr[480:960, 640:1280] = panels[1]
    sheet_arr[0:480, 0:640] = panels[2]
    sheet_arr[0:480, 640:1280] = panels[3]

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    sheet_img = bpy.data.images.new("AtelierReviewSheet", width=1280, height=960, alpha=True)
    sheet_img.pixels.foreach_set(sheet_arr.ravel())
    sheet_img.filepath_raw = out_png
    sheet_img.file_format = "PNG"
    sheet_img.save()
    bpy.data.images.remove(sheet_img)
    print(f"Saved 4-panel Blender verification sheet: {out_png}")


if __name__ == "__main__":
    main()
