#!/usr/bin/env python3
"""
Independently imports `public/models/zachary_companion.glb` into a clean factory Blender 5.2 session,
verifies structural/animation/rig/morph/grounding/budget invariants, and renders a 6-panel Cycles
studio inspection sheet to `screenshots/zachary_companion_blender_review.png`.
"""
from __future__ import annotations

import json
import math
import os
import struct
import tempfile
import numpy as np
import bpy
from mathutils import Vector


REQUIRED_MESHES = [
    "SM_Companion_Body",
    "SM_Companion_Glasses",
]

REQUIRED_BONES = [
    "Hips",
    "Spine",
    "Spine1",
    "Neck",
    "Head",
    "LeftShoulder",
    "LeftArm",
    "LeftForeArm",
    "LeftHand",
    "RightShoulder",
    "RightArm",
    "RightForeArm",
    "RightHand",
    "LeftUpLeg",
    "LeftLeg",
    "LeftFoot",
    "RightUpLeg",
    "RightLeg",
    "RightFoot",
]

REQUIRED_CLIPS = [
    "Idle_Breathing",
    "Walk_Forward",
    "Gesture_Present",
    "Turn_Greet",
]

REQUIRED_MATERIALS = [
    "Mat_Companion_Body",
    "Mat_Companion_Face",
    "Mat_Companion_GlassesMetal",
    "Mat_Companion_GlassesLens",
]


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)


def setup_studio() -> None:
    scene = bpy.context.scene
    world = bpy.data.worlds.new("CompanionReviewWorld")
    scene.world = world
    nt = world.node_tree
    nt.nodes.clear()

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.025, 0.028, 0.036, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.085, 0.082, 0.092, 1.0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.90
    out = nt.nodes.new("ShaderNodeOutputWorld")

    nt.links.new(tex_coord.outputs["Generated"], sep_xyz.inputs["Vector"])
    nt.links.new(sep_xyz.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    # Matte dark basalt floor disc for clear shadow & sneaker grounding check
    import bmesh
    bm_floor = bmesh.new()
    bmesh.ops.create_cone(bm_floor, cap_ends=True, cap_tris=False, segments=64, radius1=2.0, radius2=2.0, depth=0.04)
    for v in bm_floor.verts:
        v.co.z -= 0.02
    mesh_f = bpy.data.meshes.new("ReviewFloor")
    bm_floor.to_mesh(mesh_f)
    bm_floor.free()
    mat_f = bpy.data.materials.new("ReviewFloorMat")
    mat_f.use_nodes = True
    bsdf = mat_f.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.045, 0.048, 0.056, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.45
    mesh_f.materials.append(mat_f)
    floor_obj = bpy.data.objects.new("ReviewFloor", mesh_f)
    scene.collection.objects.link(floor_obj)

    def add_area(name: str, loc: tuple[float, float, float], rot_deg: tuple[float, float, float], energy: float, size: float, color: tuple[float, float, float]):
        ldata = bpy.data.lights.new(name=name, type="AREA")
        ldata.energy = energy
        ldata.size = size
        ldata.color = color
        lobj = bpy.data.objects.new(name, ldata)
        lobj.location = loc
        lobj.rotation_euler = tuple(math.radians(a) for a in rot_deg)
        scene.collection.objects.link(lobj)

    # Calibrated 4-light portrait & figurine studio matching Act 1 Sovereign Titanium Atelier
    add_area("KeySoftbox", (1.8, -2.5, 2.2), (66, 0, 34), energy=155.0, size=2.2, color=(1.0, 0.96, 0.91))
    add_area("CoolFill", (-2.6, -2.2, 1.6), (72, 0, -48), energy=78.0, size=2.4, color=(0.82, 0.90, 1.0))
    add_area("ChampagneRim", (-0.9, 2.5, 2.1), (-68, 0, 160), energy=130.0, size=1.8, color=(1.0, 0.86, 0.65))
    add_area("FrontEyeCatchlight", (0.25, -2.8, 1.55), (86, 0, 5), energy=42.0, size=0.45, color=(1.0, 0.98, 0.95))

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def set_clip_frame(arm_obj: bpy.types.Object, clip_name: str, frame: int) -> None:
    if arm_obj.animation_data is None:
        return
    # Mute all NLA tracks except target, or set active action directly from matching NLA strip
    target_act = None
    target_slot = None
    for tr in arm_obj.animation_data.nla_tracks:
        tr.mute = True
        for st in tr.strips:
            if clip_name in (tr.name, st.action.name if st.action else ""):
                target_act = st.action
                target_slot = st.action_slot
    if target_act is None:
        target_act = bpy.data.actions.get(clip_name)
    assert target_act is not None, f"Could not activate clip {clip_name}"
    arm_obj.animation_data.action = target_act
    if target_slot is not None:
        arm_obj.animation_data.action_slot = target_slot
    elif len(target_act.slots) > 0:
        arm_obj.animation_data.action_slot = target_act.slots[0]
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    glb_path = os.path.join(root, "public", "models", "zachary_companion.glb")
    out_png = os.path.join(root, "screenshots", "zachary_companion_blender_review.png")

    size_bytes = os.path.getsize(glb_path)
    assert size_bytes <= 3.0 * 1024 * 1024, f"Companion GLB exceeds 3.0MB budget: {size_bytes}"

    with open(glb_path, "rb") as f:
        glb_data = f.read()
    magic, _ver, _total_len = struct.unpack_from("<III", glb_data, 0)
    assert magic == 0x46546C67, "Invalid GLB magic"
    json_len, json_type = struct.unpack_from("<II", glb_data, 12)
    assert json_type == 0x4E4F534A, "Expected JSON chunk"
    glb_json = json.loads(glb_data[20 : 20 + json_len].decode("utf-8"))
    exts_used = set(glb_json.get("extensionsUsed", []))
    assert "EXT_meshopt_compression" in exts_used, f"Missing EXT_meshopt_compression in {exts_used}"
    bvs = glb_json.get("bufferViews", [])
    for idx, img in enumerate(glb_json.get("images", [])):
        if "bufferView" in img:
            blen = int(bvs[int(img["bufferView"])].get("byteLength", 0))
            assert blen <= 100 * 1024, f"Embedded GLB image[{idx}] exceeds 100 KB: {blen} bytes"

    clear_scene()
    bpy.ops.import_scene.gltf(filepath=glb_path)

    mesh_map = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    arm_objs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    assert len(arm_objs) >= 1, "No Armature imported from GLB"
    arm_obj = arm_objs[0]

    for mname in REQUIRED_MESHES:
        assert mname in mesh_map, f"Missing mesh node in GLB: {mname}"

    bone_names = {b.name for b in arm_obj.data.bones}
    for bname in REQUIRED_BONES:
        assert bname in bone_names, f"Missing bone in GLB: {bname}"

    mat_names = {m.name for m in bpy.data.materials}
    for mat_n in REQUIRED_MATERIALS:
        assert mat_n in mat_names, f"Missing material in GLB: {mat_n}"

    # Verify NLA / Action clips
    imported_clips = set()
    if arm_obj.animation_data:
        for tr in arm_obj.animation_data.nla_tracks:
            imported_clips.add(tr.name)
            for st in tr.strips:
                if st.action:
                    imported_clips.add(st.action.name)
    for act in bpy.data.actions:
        imported_clips.add(act.name)
    for cname in REQUIRED_CLIPS:
        assert cname in imported_clips, f"Missing animation clip in GLB: {cname} (found: {sorted(imported_clips)})"

    # Verify blink & warm smile morph targets directly on SM_Companion_Body (and optional eyelids)
    body_sk = mesh_map["SM_Companion_Body"].data.shape_keys
    assert body_sk is not None, "SM_Companion_Body missing v4.1 facial shape keys"
    body_sk_names = {kb.name for kb in body_sk.key_blocks}
    for req_morph in ("eyeBlinkLeft", "eyeBlinkRight", "mouthSmileLeft", "mouthSmileRight"):
        assert req_morph in body_sk_names, f"Missing SM_Companion_Body shape key {req_morph} in {sorted(body_sk_names)}"
    if "SM_Companion_Eyelids" in mesh_map:
        lid_sk = mesh_map["SM_Companion_Eyelids"].data.shape_keys
        assert lid_sk is not None, "SM_Companion_Eyelids missing shape keys"
        sk_names = {kb.name for kb in lid_sk.key_blocks}
        assert "eyeBlinkLeft" in sk_names and "eyeBlinkRight" in sk_names, f"Missing blink morphs: {sorted(sk_names)}"

    # Verify geometry finiteness & world bounds in Idle_Breathing frame 1
    set_clip_frame(arm_obj, "Idle_Breathing", 1)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    min_z = 999.0
    max_z = -999.0
    total_tris = 0
    for mname in REQUIRED_MESHES:
        obj = mesh_map[mname]
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        total_tris += len(me.loop_triangles)
        for v in me.vertices:
            wp = obj.matrix_world @ v.co
            assert all(math.isfinite(c) for c in wp), f"Non-finite vertex in {mname}"
            if wp.z < min_z:
                min_z = wp.z
            if wp.z > max_z:
                max_z = wp.z
        ev.to_mesh_clear()

    assert -0.025 <= min_z <= 0.025, f"Un-grounded Z min={min_z:.4f}"
    assert 1.50 <= max_z <= 1.66, f"Unexpected height Z max={max_z:.4f}"
    print(
        f"GLB Verification PASSED: {len(REQUIRED_MESHES)} meshes, {len(REQUIRED_BONES)} bones, "
        f"{len(REQUIRED_CLIPS)} clips, {total_tris} tris, Z=[{min_z:.4f}, {max_z:.4f}], {size_bytes} bytes"
    )

    setup_studio()
    cam_data = bpy.data.cameras.new("CompanionCam")
    cam_obj = bpy.data.objects.new("CompanionCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    scene = bpy.context.scene
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.image_settings.file_format = "PNG"

    panels: list[np.ndarray] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        def render_view(label: str, clip: str, frame: int, loc: tuple[float, float, float], target: tuple[float, float, float], lens: float) -> None:
            set_clip_frame(arm_obj, clip, frame)
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

        # Row 1: Front, 3/4 Hero, Side Profile (Idle_Breathing frame 1 — framed generously head-to-toe)
        render_view("1_front", "Idle_Breathing", 1, (0.0, -3.15, 0.90), (0.0, 0.0, 0.80), 42.0)
        render_view("2_hero34", "Idle_Breathing", 1, (-2.05, -2.55, 1.04), (0.0, 0.0, 0.80), 44.0)
        render_view("3_side", "Idle_Breathing", 1, (-3.10, -0.10, 0.92), (0.0, 0.0, 0.80), 44.0)
        # Row 2: Close-Up Head & Glasses, Walk Stride Mid-Frame, Present Gesture Frame
        render_view("4_head", "Idle_Breathing", 1, (-0.28, -0.74, 1.48), (0.0, -0.04, 1.445), 72.0)
        render_view("5_walk", "Walk_Forward", 7, (-2.15, -2.35, 1.00), (0.0, 0.0, 0.80), 44.0)
        render_view("6_present", "Gesture_Present", 25, (-1.65, -2.65, 1.02), (-0.08, 0.0, 0.82), 44.0)

    # Composite 3 columns x 2 rows = 1920 x 960 sheet (bottom-to-top in Blender pixels)
    sheet_arr = np.zeros((960, 1920, 4), dtype=np.float32)
    sheet_arr[480:960, 0:640] = panels[0]
    sheet_arr[480:960, 640:1280] = panels[1]
    sheet_arr[480:960, 1280:1920] = panels[2]
    sheet_arr[0:480, 0:640] = panels[3]
    sheet_arr[0:480, 640:1280] = panels[4]
    sheet_arr[0:480, 1280:1920] = panels[5]

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    sheet_img = bpy.data.images.new("CompanionReviewSheet", width=1920, height=960, alpha=True)
    sheet_img.pixels.foreach_set(sheet_arr.ravel())
    sheet_img.filepath_raw = out_png
    sheet_img.file_format = "PNG"
    sheet_img.save()
    bpy.data.images.remove(sheet_img)
    print(f"Saved 6-panel Blender verification sheet: {out_png}")


if __name__ == "__main__":
    main()
