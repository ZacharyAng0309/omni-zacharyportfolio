#!/usr/bin/env python3
"""
Likeness Companion v4 Pixar-Anime Production Pipeline (`zachary_companion.glb`).

Concept-First 1:6 Pixar-Anime Hero Pipeline:
- Uses `artifacts/companion-v4-anime/hd_bust_v4_anime.glb` (native 1024-res TRELLIS.2 3D sculpt
  from user-approved `02_hd_bust_glasses_off.png`) at 1:6 head-to-body proportions (`head_h ≈ 0.258m`),
  preserving 100% native 3D sculpted eyelids, arched brows, layered bangs, warm nose, calm friendly
  smile, and zero 2D face photo projection stickers.
- Couples seamlessly into the watertight manifold A-pose body (`raw_companion.glb`) via Bake-Before-Sink
  collar roll-in plus an object-space garment cleanup pass: spotless matte obsidian-black overshirt and
  trousers, crisp off-white crew tee, clean dark/white sneakers, and skin-matched hands/wrists.
- Fits sleek single-bridge brushed-bronze thin-wire rounded-panto spectacles (`SM_Companion_Glasses`)
  dynamically anchored to post-align eye/bridge/ear/temple contours.
- Retains the exact 19-bone `CompanionArmature`, deterministic skinning with rigid Head/glasses lock,
  and 4 baked Blender 5.2 Slotted NLA clips strictly under the <= 3.0 MB WebGL budget.
"""

from __future__ import annotations

import argparse
from collections import deque
import json
import math
import os
import struct
import sys
import tempfile
import numpy as np
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector


def _find_project_root() -> str:
    cur = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(cur, "package.json")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


PROJECT_ROOT = _find_project_root()
RAW_BODY_GLB = os.path.join(
    PROJECT_ROOT, "artifacts", "companion-v2-likeness", "raw_companion.glb"
)
HD_BUST_GLB = os.path.join(
    PROJECT_ROOT, "artifacts", "companion-v4-anime", "hd_bust_v4_anime.glb"
)
V4_WORK_DIR = os.path.join(PROJECT_ROOT, "artifacts", "companion-v4-anime")
CONCEPT_BUST_PNG = os.path.join(V4_WORK_DIR, "02_hd_bust_glasses_off.png")
FACE_CHECK_PNG = os.path.join(V4_WORK_DIR, "v4_anime_face_checkpoint.png")
OUT_GLB_PATH = os.path.join(PROJECT_ROOT, "public", "models", "zachary_companion.glb")

TARGET_HEIGHT = 1.620
TARGET_HEAD_HEIGHT = 0.258  # ~1:6.3 Pixar-anime head-to-body ratio (crown ~1.628m, chin ~1.370m)

# Default warm Pixar-anime peach skin & warm espresso-brown hair (refined for v4.1)
DEFAULT_SKIN_SRGB = np.array([0.805, 0.630, 0.560], dtype=np.float32)
TARGET_HAIR_SRGB = np.array([0.155, 0.120, 0.102], dtype=np.float32)


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for lgt in list(bpy.data.lights):
        bpy.data.lights.remove(lgt)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge1 == edge0:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def srgb_to_linear(c: tuple[float, float, float]) -> tuple[float, float, float]:
    out = []
    for ch in c:
        out.append(ch / 12.92 if ch <= 0.04045 else ((ch + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2])


def resize_np_bilinear(src: np.ndarray, new_h: int, new_w: int) -> np.ndarray:
    h, w, _ = src.shape
    if (h, w) == (new_h, new_w):
        return src.copy()
    ys = np.linspace(0.0, h - 1.0, new_h, dtype=np.float32)
    xs = np.linspace(0.0, w - 1.0, new_w, dtype=np.float32)
    y0 = np.floor(ys).astype(np.int32)
    x0 = np.floor(xs).astype(np.int32)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    fy = (ys - y0)[:, None, None]
    fx = (xs - x0)[None, :, None]
    return (
        src[y0[:, None], x0[None, :], :] * (1.0 - fy) * (1.0 - fx)
        + src[y0[:, None], x1[None, :], :] * (1.0 - fy) * fx
        + src[y1[:, None], x0[None, :], :] * fy * (1.0 - fx)
        + src[y1[:, None], x1[None, :], :] * fy * fx
    )


def box_blur_2d(img: np.ndarray, radius: int, passes: int = 2) -> np.ndarray:
    """Fast separable box blur using numpy cumulative sums (approximates Gaussian cleanly)."""
    out = img.astype(np.float32, copy=True)
    h, w = out.shape[:2]
    for _ in range(passes):
        pad = np.pad(out, ((0, 0), (radius, radius), (0, 0)), mode="edge")
        cs = np.cumsum(pad, axis=1, dtype=np.float64)
        out = ((cs[:, 2 * radius :, :] - np.concatenate([np.zeros((h, 1, out.shape[2])), cs[:, : w - 1, :]], axis=1)) / (2 * radius + 1)).astype(np.float32)
        pad = np.pad(out, ((radius, radius), (0, 0), (0, 0)), mode="edge")
        cs = np.cumsum(pad, axis=0, dtype=np.float64)
        out = ((cs[2 * radius :, :, :] - np.concatenate([np.zeros((1, w, out.shape[2])), cs[: h - 1, :, :]], axis=0)) / (2 * radius + 1)).astype(np.float32)
    return out


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def import_glb_as_single_mesh(path: str, name: str, img_prefix: str) -> tuple[bpy.types.Object, bpy.types.Image]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing GLB: {path}")

    existing_objs = set(bpy.data.objects)
    existing_imgs = set(bpy.data.images)
    bpy.ops.import_scene.gltf(filepath=path)
    new_objs = [o for o in bpy.data.objects if o not in existing_objs]
    new_imgs = [im for im in bpy.data.images if im not in existing_imgs]

    meshes = [o for o in new_objs if o.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No meshes in {path}")

    for m in meshes:
        mw = m.matrix_world.copy()
        m.parent = None
        m.matrix_world = Matrix.Identity(4)
        m.data.transform(mw)
        m.data.update()

    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()

    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.name = f"{name}_Mesh"

    for o in new_objs:
        if o != obj and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)

    albedo = None
    for idx, im in enumerate(new_imgs):
        im.name = f"{img_prefix}_Img_{idx}"
        if albedo is None and im.size[0] >= 512 and im.colorspace_settings.name == "sRGB":
            albedo = im
    if albedo is None:
        big = [im for im in new_imgs if im.size[0] >= 512]
        if not big:
            raise RuntimeError(f"No albedo image >= 512px in {path}")
        albedo = big[0]

    return obj, albedo


def sample_vertex_colors(mesh: bpy.types.Mesh, img: bpy.types.Image) -> np.ndarray:
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape((h, w, 4))[:, :, :3]
    uv_data = mesh.uv_layers.active.data
    v_col = np.zeros((len(mesh.vertices), 3), dtype=np.float32)
    v_cnt = np.zeros(len(mesh.vertices), dtype=np.int32)
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            u, v = uv_data[li].uv
            ix = int(np.clip((u % 1.0) * (w - 1), 0, w - 1))
            iy = int(np.clip((v % 1.0) * (h - 1), 0, h - 1))
            v_col[vi] += px[iy, ix]
            v_cnt[vi] += 1
    m = v_cnt > 0
    v_col[m] /= v_cnt[m, None]
    return v_col


# ==============================================================================
# STEP 1: IMPORT, NORMALIZE BODY & ALIGN 1:6 PIXAR-ANIME BUST + COLLAR TUCK
# ==============================================================================
def import_and_align_sources() -> tuple[
    bpy.types.Object, bpy.types.Image, bpy.types.Object, bpy.types.Image, dict[str, object], np.ndarray
]:
    from mathutils.bvhtree import BVHTree

    raw_body, raw_body_albedo = import_glb_as_single_mesh(RAW_BODY_GLB, "Raw_Body_Ref", "RawBody")

    # Normalize raw body to 1.620m centered at X=0, Y=0, feet at Z=0
    b_pts = np.array([list(v.co) for v in raw_body.data.vertices], dtype=np.float64)
    b_min = b_pts.min(axis=0)
    b_max = b_pts.max(axis=0)
    b_scale = TARGET_HEIGHT / max(1e-5, float(b_max[2] - b_min[2]))
    b_cx = 0.5 * float(b_min[0] + b_max[0])
    b_cy = 0.5 * float(b_min[1] + b_max[1])
    norm_mat = Matrix.Scale(b_scale, 4) @ Matrix.Translation(Vector((-b_cx, -b_cy, -float(b_min[2]))))
    raw_body.data.transform(norm_mat)
    raw_body.data.update()

    b_pts_n = np.array([list(v.co) for v in raw_body.data.vertices], dtype=np.float64)
    raw_vcol_init = sample_vertex_colors(raw_body.data, raw_body_albedo)
    is_raw_skin = ((raw_vcol_init[:, 0] - raw_vcol_init[:, 2]) > 0.025) & (raw_vcol_init[:, 0] > 0.36)
    raw_neck_sl = b_pts_n[(b_pts_n[:, 2] >= 1.330) & (b_pts_n[:, 2] <= 1.360) & (np.abs(b_pts_n[:, 0]) < 0.065) & is_raw_skin]
    raw_neck_cy = (
        0.5 * (float(raw_neck_sl[:, 1].min()) + float(raw_neck_sl[:, 1].max()))
        if len(raw_neck_sl) > 10
        else 0.018
    )
    print(f"Raw body normalized: verts={len(raw_body.data.vertices)}, raw_neck_cy={raw_neck_cy:.4f} (skin_pts={len(raw_neck_sl)})")

    # Import Pixar-Anime HD bust, weld UV seams, and strip TRELLIS.2's hollow interior backing shell
    hd_bust, hd_bust_albedo = import_glb_as_single_mesh(HD_BUST_GLB, "HD_Bust_High", "HDBust")
    bm_weld = bmesh.new()
    bm_weld.from_mesh(hd_bust.data)
    bmesh.ops.remove_doubles(bm_weld, verts=bm_weld.verts, dist=5e-5)
    bm_weld.faces.ensure_lookup_table()
    bvh_shell = BVHTree.FromBMesh(bm_weld)

    is_outer: dict[int, bool] = {}
    for f in bm_weld.faces:
        n = f.normal.normalized()
        fc = f.calc_center_median()
        up = Vector((0.0, 0.0, 1.0)) if abs(n.z) < 0.9 else Vector((1.0, 0.0, 0.0))
        t1 = n.cross(up).normalized()
        t2 = n.cross(t1).normalized()
        dirs = [n]
        for ring_cos, ring_sin, ph_off in ((0.866, 0.500, 0.0), (0.500, 0.866, math.pi / 6.0)):
            for k in range(6):
                ang = k * (math.pi / 3.0) + ph_off
                dirs.append((n * ring_cos + (t1 * math.cos(ang) + t2 * math.sin(ang)) * ring_sin).normalized())
        for k in range(8):
            ang = k * (math.pi / 4.0)
            dirs.append((n * 0.22 + (t1 * math.cos(ang) + t2 * math.sin(ang)) * 0.975).normalized())
        # Front-face outward normal guard (true hollow backing faces always point backward n.y > +0.15)
        if abs(fc.x) < 0.145 and fc.y < -0.165 and -0.16 < fc.z < 0.145 and n.y < 0.08:
            is_outer[f.index] = True
            continue
        escaped = False
        origin = fc + n * 0.0005
        for d in dirs:
            hit, _, _, _ = bvh_shell.ray_cast(origin, d, 5.0)
            if hit is None:
                escaped = True
                break
        is_outer[f.index] = escaped

    for _ in range(5):
        recovered = []
        for f in bm_weld.faces:
            if is_outer[f.index]:
                continue
            adj_out_all = [
                lf for e in f.edges for lf in e.link_faces
                if lf != f and is_outer[lf.index]
            ]
            adj_out_aligned = [
                lf for lf in adj_out_all
                if f.normal.dot(lf.normal) > -0.25
            ]
            if len(adj_out_all) >= 3 or len(adj_out_aligned) >= 2:
                recovered.append(f.index)
        for fi in recovered:
            is_outer[fi] = True

    inner_faces = [f for f in bm_weld.faces if not is_outer[f.index]]
    if inner_faces:
        bmesh.ops.delete(bm_weld, geom=inner_faces, context="FACES")
    bmesh.ops.delete(bm_weld, geom=[v for v in bm_weld.verts if not v.link_faces], context="VERTS")
    print(f"Stripped hollow inner backing shell: removed {len(inner_faces)} inner faces, kept {len(bm_weld.faces)} outer faces")
    bm_weld.to_mesh(hd_bust.data)
    bm_weld.free()
    hd_bust.data.update()

    bust_vcol = sample_vertex_colors(hd_bust.data, hd_bust_albedo)
    h_pts = np.array([list(v.co) for v in hd_bust.data.vertices], dtype=np.float64)
    luma_h = 0.299 * bust_vcol[:, 0] + 0.587 * bust_vcol[:, 1] + 0.114 * bust_vcol[:, 2]

    # Sample bright front cheek skin directly from hd_bust_v4_anime so body hands match face 1:1
    cheek_mask = (
        (h_pts[:, 1] < -0.175)
        & (np.abs(h_pts[:, 0]) > 0.055)
        & (np.abs(h_pts[:, 0]) < 0.145)
        & (h_pts[:, 2] > -0.05)
        & (h_pts[:, 2] < 0.07)
        & ((bust_vcol[:, 0] - bust_vcol[:, 2]) > 0.05)
        & (luma_h > 0.45)
    )
    if np.sum(cheek_mask) >= 16:
        skin_p60 = np.percentile(bust_vcol[cheek_mask], 60, axis=0).astype(np.float32)
        target_skin_srgb = np.clip(0.5 * DEFAULT_SKIN_SRGB + 0.5 * skin_p60, 0.45, 0.90).astype(np.float32)
    else:
        target_skin_srgb = DEFAULT_SKIN_SRGB.copy()
    print(f"Calibrated Pixar-Anime skin sRGB target: {np.round(target_skin_srgb, 4).tolist()}")

    # Measure raw chin-to-crown height so head sits at true 1:6 Pixar-anime proportions (~0.258m tall)
    chin_raw_pts = h_pts[(h_pts[:, 1] < -0.13) & (np.abs(h_pts[:, 0]) < 0.04) & (h_pts[:, 2] > -0.24)]
    bust_chin_z_raw = float(chin_raw_pts[:, 2].min()) if len(chin_raw_pts) else -0.155
    bust_crown_z_raw = float(h_pts[:, 2].max())
    raw_head_h = max(0.35, bust_crown_z_raw - bust_chin_z_raw)
    bust_scale = TARGET_HEAD_HEIGHT / raw_head_h
    print(f"Raw bust chin_z={bust_chin_z_raw:.4f}, crown_z={bust_crown_z_raw:.4f}, head_h={raw_head_h:.4f} -> bust_scale={bust_scale:.4f}")

    # Measure raw eye centers from open iris + sclera zone (strictly below forehead bangs Z < 0.132)
    eye_l_raw = h_pts[(h_pts[:, 1] < -0.18) & (h_pts[:, 0] > 0.045) & (h_pts[:, 0] < 0.115) & (h_pts[:, 2] > 0.085) & (h_pts[:, 2] < 0.132) & ((luma_h < 0.28) | (luma_h > 0.72))]
    eye_r_raw = h_pts[(h_pts[:, 1] < -0.18) & (h_pts[:, 0] < -0.045) & (h_pts[:, 0] > -0.115) & (h_pts[:, 2] > 0.085) & (h_pts[:, 2] < 0.132) & ((luma_h < 0.28) | (luma_h > 0.72))]
    el_med = np.median(eye_l_raw, axis=0) if len(eye_l_raw) else np.array([0.078, -0.209, 0.114])
    er_med = np.median(eye_r_raw, axis=0) if len(eye_r_raw) else np.array([-0.078, -0.209, 0.114])
    eye_mid_x_raw = 0.5 * float(el_med[0] + er_med[0])

    # Measure neck cylinder Y center in [-0.25, -0.16]
    is_skin_h = ((bust_vcol[:, 0] - bust_vcol[:, 2]) > 0.04) & (luma_h > 0.28)
    bust_neck_sl = h_pts[(h_pts[:, 2] >= -0.25) & (h_pts[:, 2] <= -0.16) & (np.abs(h_pts[:, 0]) < 0.12) & is_skin_h]
    bust_neck_cy_raw = (
        0.5 * (float(bust_neck_sl[:, 1].min()) + float(bust_neck_sl[:, 1].max()))
        if len(bust_neck_sl) > 10
        else 0.005
    )

    # Align HD bust: crown at Z=1.628m (chin ~1.370m), eyes centered on X=0, neck aligned with raw_neck_cy
    target_crown_z = 1.628
    dx = -eye_mid_x_raw * bust_scale
    dy = raw_neck_cy - bust_neck_cy_raw * bust_scale - 0.0020
    dz = target_crown_z - bust_crown_z_raw * bust_scale
    bust_mat = Matrix.Translation(Vector((dx, dy, dz))) @ Matrix.Scale(bust_scale, 4)
    hd_bust.data.transform(bust_mat)
    hd_bust.data.update()

    # Re-measure world landmarks directly on transformed HD bust
    a_pts = np.array([list(v.co) for v in hd_bust.data.vertices], dtype=np.float64)
    a_lum = luma_h
    eye_z_est = 0.5 * float(el_med[2] + er_med[2]) * bust_scale + dz

    iris_l = a_pts[(a_pts[:, 1] < -0.055) & (a_pts[:, 0] > 0.018) & (a_pts[:, 0] < 0.046) & (np.abs(a_pts[:, 2] - eye_z_est) < 0.009) & (a_lum < 0.28)]
    iris_r = a_pts[(a_pts[:, 1] < -0.055) & (a_pts[:, 0] < -0.018) & (a_pts[:, 0] > -0.046) & (np.abs(a_pts[:, 2] - eye_z_est) < 0.009) & (a_lum < 0.28)]
    eye_l_pos = Vector(np.median(iris_l, axis=0)) if len(iris_l) else Vector((float(el_med[0]) * bust_scale + dx, float(el_med[1]) * bust_scale + dy, eye_z_est))
    eye_r_pos = Vector(np.median(iris_r, axis=0)) if len(iris_r) else Vector((float(er_med[0]) * bust_scale + dx, float(er_med[1]) * bust_scale + dy, eye_z_est))
    eye_z = 0.5 * (eye_l_pos.z + eye_r_pos.z) - 0.0010  # optical center just below upper lash line
    eye_dx = 0.5 * (eye_l_pos.x - eye_r_pos.x)
    nose_x = 0.5 * (eye_l_pos.x + eye_r_pos.x)

    nose_sub = a_pts[(np.abs(a_pts[:, 0] - nose_x) < 0.010) & (a_pts[:, 2] > eye_z - 0.055) & (a_pts[:, 2] < eye_z - 0.020)]
    nose_tip = nose_sub[np.argmin(nose_sub[:, 1])] if len(nose_sub) else np.array([nose_x, float(eye_l_pos.y) - 0.024, eye_z - 0.036])
    bridge_sub = a_pts[(np.abs(a_pts[:, 0] - nose_x) < 0.008) & (np.abs(a_pts[:, 2] - eye_z) < 0.008) & (a_pts[:, 1] < -0.05)]
    bridge_y = float(bridge_sub[:, 1].min()) if len(bridge_sub) else float(eye_l_pos.y) - 0.010

    cornea_l = a_pts[(np.abs(a_pts[:, 0] - eye_l_pos.x) < 0.008) & (np.abs(a_pts[:, 2] - eye_z) < 0.007) & (a_pts[:, 1] < -0.05)]
    cornea_r = a_pts[(np.abs(a_pts[:, 0] - eye_r_pos.x) < 0.008) & (np.abs(a_pts[:, 2] - eye_z) < 0.007) & (a_pts[:, 1] < -0.05)]
    eye_front_y = float(min(
        cornea_l[:, 1].min() if len(cornea_l) else eye_l_pos.y,
        cornea_r[:, 1].min() if len(cornea_r) else eye_r_pos.y,
    ))

    # Rosy smile lips & chin bottom
    m_mask = (a_pts[:, 1] < -0.065) & (np.abs(a_pts[:, 0] - nose_x) < 0.024) & (a_pts[:, 2] >= eye_z - 0.095) & (a_pts[:, 2] <= eye_z - 0.058)
    m_col = bust_vcol[m_mask]
    m_pts = a_pts[m_mask]
    lip_sel = m_pts[((m_col[:, 0] - m_col[:, 1]) > 0.14) & (a_lum[m_mask] < 0.72)]
    mouth_z = float(np.median(lip_sel[:, 2])) if len(lip_sel) >= 6 else (eye_z - 0.076)
    chin_sub = a_pts[(np.abs(a_pts[:, 0] - nose_x) < 0.016) & (a_pts[:, 1] < -0.05) & (a_pts[:, 2] < mouth_z - 0.010) & (a_pts[:, 2] > mouth_z - 0.065)]
    chin_z = float(chin_sub[:, 2].min()) if len(chin_sub) else (bust_chin_z_raw * bust_scale + dz)

    # Measure ear helix position & outer temple width along exact front-to-ear span
    ear_l = a_pts[(a_pts[:, 2] >= eye_z - 0.032) & (a_pts[:, 2] <= eye_z + 0.020) & (a_pts[:, 1] >= -0.030) & (a_pts[:, 1] <= 0.050) & (a_pts[:, 0] > 0.065)]
    ear_r = a_pts[(a_pts[:, 2] >= eye_z - 0.032) & (a_pts[:, 2] <= eye_z + 0.020) & (a_pts[:, 1] >= -0.030) & (a_pts[:, 1] <= 0.050) & (a_pts[:, 0] < -0.065)]
    ear_top_y = float(np.median(ear_l[:, 1])) if len(ear_l) else float(eye_l_pos.y + 0.075)
    ear_top_y = min(max(ear_top_y, eye_front_y + 0.055), eye_front_y + 0.115)

    # Sample a clean mid-neck skin UV coordinate on the aligned front throat for procedural neck skirt
    neck_uv_samples: list[tuple[float, float]] = []
    uv_act = hd_bust.data.uv_layers.active.data
    verts_a = hd_bust.data.vertices
    for poly in hd_bust.data.polygons:
        for li in poly.loop_indices:
            vi = hd_bust.data.loops[li].vertex_index
            co_v = verts_a[vi].co
            vc = bust_vcol[vi]
            v_lum = float(0.299 * vc[0] + 0.587 * vc[1] + 0.114 * vc[2])
            if (
                abs(co_v.x - nose_x) < 0.018
                and co_v.y < -0.002
                and 1.338 <= co_v.z <= 1.356
                and (vc[0] - vc[2]) > 0.05
                and v_lum > 0.45
            ):
                u_val, v_val = uv_act[li].uv
                neck_uv_samples.append((float(u_val), float(v_val)))
    if neck_uv_samples:
        neck_skin_uv = (
            float(np.median([p[0] for p in neck_uv_samples])),
            float(np.median([p[1] for p in neck_uv_samples])),
        )
    else:
        neck_skin_uv = (0.5, 0.5)

    landmarks: dict[str, object] = {
        "bust_scale": bust_scale,
        "nose_x": nose_x,
        "nose_tip_y": float(nose_tip[1]),
        "nose_tip_z": float(nose_tip[2]),
        "bridge_y": bridge_y,
        "eye_front_y": eye_front_y,
        "eye_z": eye_z,
        "eye_dx": eye_dx,
        "mouth_z": mouth_z,
        "chin_z": chin_z,
        "neck_cy": raw_neck_cy,
        "ear_top_y": ear_top_y,
        "neck_skin_uv": neck_skin_uv,
    }
    print(
        f"Aligned Pixar-Anime HD Bust landmarks: { {k: round(float(v), 4) for k, v in landmarks.items() if isinstance(v, (int, float))} }, neck_skin_uv={tuple(round(x, 4) for x in neck_skin_uv)}"
    )

    # Collar-tuck trim + procedural skin neck skirt ONLY (100% pure native 3D Pixar-Anime sculpt!)
    sculpt_refine_hd_bust(hd_bust, bust_vcol, landmarks)

    # Measure temple half-width profile post-trim along exact Y span from eye plane to behind ears
    s_pts = np.array([list(v.co) for v in hd_bust.data.vertices], dtype=np.float64)
    temple_band = np.abs(s_pts[:, 2] - (eye_z + 0.0040)) < 0.0100
    y_start = eye_front_y + 0.008
    y_end = ear_top_y + 0.016
    temple_ys = [round(float(y_start + (y_end - y_start) * (k / 7.0)), 4) for k in range(8)]
    temple_profile_x: list[float] = []
    for ty in temple_ys:
        ymask = temple_band & (np.abs(s_pts[:, 1] - ty) < 0.0085)
        l_xs = np.abs(s_pts[ymask & (s_pts[:, 0] > nose_x), 0] - nose_x)
        r_xs = np.abs(s_pts[ymask & (s_pts[:, 0] < nose_x), 0] - nose_x)
        p_l = float(np.percentile(l_xs, 98)) if len(l_xs) else 0.074
        p_r = float(np.percentile(r_xs, 98)) if len(r_xs) else 0.074
        temple_profile_x.append(max(p_l, p_r))
    landmarks["temple_profile_y"] = temple_ys
    landmarks["temple_profile_x"] = temple_profile_x
    print(f"Measured Pixar-Anime temple profile: {[(round(y, 3), round(x, 4)) for y, x in zip(temple_ys, temple_profile_x)]}")

    return raw_body, raw_body_albedo, hd_bust, hd_bust_albedo, landmarks, target_skin_srgb


def sculpt_refine_hd_bust(
    hd_bust: bpy.types.Object, bust_vcol: np.ndarray, lm: dict[str, object]
) -> None:
    """
    Clean Horizontal Bisect + Procedural Pixar-Anime Neck Skirt (ZERO facial distortion!):
    - Preserves 100% of TRELLIS.2's sculpted Pixar-Anime face, eyelids, bangs, smile, and ears.
    - Trims stray outer collar flares below `chin_guard_z`, slices razor-flat at Z=1.338m via
      `bmesh.ops.bisect_plane`, and extrudes an 8-ring smooth slim neck cylinder (rx=0.0445, ry=0.0360)
      down to Z=1.278m cleanly tucked inside the analytical body collar opening.
    """
    _ = bust_vcol
    mesh = hd_bust.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    nose_x = float(lm["nose_x"])
    chin_z = float(lm["chin_z"])
    neck_cy = float(lm["neck_cy"])
    neck_skin_uv = lm.get("neck_skin_uv", (0.5, 0.5))
    uv_vec = Vector((float(neck_skin_uv[0]), float(neck_skin_uv[1])))  # type: ignore[index]

    # 1. Remove stray outer standing-collar & dangling side/rear bust flares below jawline
    # Seal occipital nape cleanly via generous rear ry_lim above 1.356m while clipping any loose dangling tips
    chin_guard_z = max(1.352, chin_z - 0.008)
    back_flare_z = min(max(chin_guard_z + 0.010, chin_z + 0.012), 1.382)
    flare_faces = []
    for f in bm.faces:
        fc = f.calc_center_median()
        if fc.z >= back_flare_z:
            continue
        if fc.z >= chin_guard_z and fc.y <= 0.025:
            continue
        if fc.y < -0.036 and fc.z >= chin_z - 0.014:
            continue
        if fc.z < 1.356:
            rx_lim = 0.045
            ry_lim = 0.050
        else:
            rx_lim = 0.047
            ry_lim = 0.064 if fc.y > neck_cy else 0.052
        if math.hypot((fc.x - nose_x) / rx_lim, (fc.y - neck_cy) / ry_lim) > 1.00:
            flare_faces.append(f)
    if flare_faces:
        bmesh.ops.delete(bm, geom=flare_faces, context="FACES")

    # 2. Razor-flat horizontal knife cut at Z_cut=1.338m (removes lower bust collar & broken white tee cleanly)
    z_cut = 1.338
    geom_all = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(
        bm,
        geom=geom_all,
        plane_co=Vector((0.0, 0.0, z_cut)),
        plane_no=Vector((0.0, 0.0, 1.0)),
        clear_inner=True,
        clear_outer=False,
    )

    # 3. Keep largest connected component (head + clean neck ring)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    visited: set[int] = set()
    comps: list[list[bmesh.types.BMVert]] = []
    for v in bm.verts:
        if v.index in visited:
            continue
        stack = [v]
        comp = []
        visited.add(v.index)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for e in cur.link_edges:
                ov = e.other_vert(cur)
                if ov.index not in visited:
                    visited.add(ov.index)
                    stack.append(ov)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    if len(comps) > 1:
        stray_verts = [v for comp in comps[1:] for v in comp]
        bmesh.ops.delete(bm, geom=stray_verts, context="VERTS")

    # 4. Find ONLY the clean horizontal bottom cut boundary edges at Z=1.338m
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    cut_bedges = [
        e for e in bm.edges
        if e.is_boundary
        and abs(e.verts[0].co.z - z_cut) < 0.0025
        and abs(e.verts[1].co.z - z_cut) < 0.0025
        and max(e.verts[0].co.y, e.verts[1].co.y) < 0.062
    ]
    assert len(cut_bedges) >= 12, f"Expected >= 12 horizontal neck cut edges at Z={z_cut}, got {len(cut_bedges)}"

    cut_verts = list({v for e in cut_bedges for v in e.verts})
    target_cx = nose_x
    target_cy = neck_cy

    # Clamp any stray wide vertex on the cut ring to a slim anatomical throat oval & smooth tangentially
    for bv in cut_verts:
        dx_c = bv.co.x - target_cx
        dy_c = bv.co.y - target_cy
        ry_cap = 0.030 if dy_c < 0.0 else 0.049
        el_c = math.hypot(dx_c / 0.0465, dy_c / ry_cap)
        if el_c > 1.0:
            bv.co.x = target_cx + dx_c / el_c
            bv.co.y = target_cy + dy_c / el_c
        bv.co.z = z_cut

    cut_set = {v.index for v in cut_verts}
    for _ in range(2):
        tan_disp: dict[int, tuple[float, float]] = {}
        for bv in cut_verts:
            nbr_xy = [e.other_vert(bv).co for e in bv.link_edges if e.other_vert(bv).index in cut_set]
            if len(nbr_xy) == 2:
                mx = 0.5 * (nbr_xy[0].x + nbr_xy[1].x)
                my = 0.5 * (nbr_xy[0].y + nbr_xy[1].y)
                tan_disp[bv.index] = ((mx - bv.co.x) * 0.45, (my - bv.co.y) * 0.45)
        for bv in cut_verts:
            if bv.index in tan_disp:
                bv.co.x += tan_disp[bv.index][0]
                bv.co.y += tan_disp[bv.index][1]

    front_cut = [v for v in cut_verts if v.co.y < 0.042] or cut_verts
    ncx = float(np.median([v.co.x for v in front_cut]))
    ncy = float(np.median([v.co.y for v in front_cut]))

    # 5. Extrude 8 smooth downward rings from Z=1.338m to Z=1.268m matching sculpted crew-neck rib collar
    rx_t, ry_front_t, ry_back_t, z_bot = 0.056, 0.058, 0.044, 1.268
    n_rings = 8
    ring_verts: dict[tuple[bmesh.types.BMVert, int], bmesh.types.BMVert] = {}
    for bv in cut_verts:
        ring_verts[(bv, 0)] = bv
        dx_n = bv.co.x - target_cx
        dy_n = bv.co.y - target_cy
        r_n = math.hypot(dx_n, dy_n)
        if r_n > 1e-4:
            ux, uy = dx_n / r_n, dy_n / r_n
            ry_use = ry_front_t if uy < 0.0 else ry_back_t
            r_ell = 1.0 / math.hypot(ux / rx_t, uy / ry_use)
            tx = target_cx + ux * r_ell
            ty = target_cy + uy * r_ell
        else:
            uy = 0.0
            tx, ty = target_cx, target_cy
        for s in range(1, n_rings + 1):
            t = s / float(n_rings)
            tx_w = smoothstep(0.0, 1.0, t)
            ty_w = (t ** 0.90) if (dy_n < 0.0) else (t * t)
            nx = bv.co.x * (1.0 - tx_w) + tx * tx_w
            ny = bv.co.y * (1.0 - ty_w) + ty * ty_w
            nz = bv.co.z * (1.0 - t) + z_bot * t
            ring_verts[(bv, s)] = bm.verts.new(Vector((nx, ny, nz)))

    uv_lay = bm.loops.layers.uv.active
    seam_ring_verts: set[bmesh.types.BMVert] = set(cut_verts)
    for e in cut_bedges:
        va, vb = e.verts[0], e.verts[1]
        for s in range(n_rings):
            v00 = ring_verts[(va, s)]
            v01 = ring_verts[(vb, s)]
            v11 = ring_verts[(vb, s + 1)]
            v10 = ring_verts[(va, s + 1)]
            if s <= 1:
                seam_ring_verts.add(v10)
                seam_ring_verts.add(v11)
            try:
                nf = bm.faces.new((v00, v01, v11, v10))
            except ValueError:
                continue
            nf.normal_update()
            fc = nf.calc_center_median()
            rad = Vector((fc.x - ncx, fc.y - ncy, 0.0))
            if rad.length > 1e-5 and nf.normal.dot(rad) < 0.0:
                nf.normal_flip()
            nf.smooth = True
            if uv_lay is not None:
                for lp in nf.loops:
                    lp[uv_lay].uv = uv_vec

    # 6. 3 light Laplacian relaxation passes strictly on top skirt seam rings s=0..2 (1.316..1.342)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    trans_verts = [
        v for v in seam_ring_verts
        if not v.is_boundary and 1.316 <= v.co.z <= 1.342
    ]
    for _ in range(3):
        disp_t: dict[int, Vector] = {}
        for v in trans_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                disp_t[v.index] = (avg - v.co) * 0.35
        for v in trans_verts:
            if v.index in disp_t:
                v.co += disp_t[v.index]
    print(f"Bisected at Z={z_cut:.3f}m ({len(cut_bedges)} cut edges, neck_c=({ncx:+.4f},{ncy:+.4f})) and extruded 8-ring skirt to Z={z_bot:.3f}m")

    assert len(bm.verts) > 12000, f"Unexpectedly small HD head mesh after collar trim: {len(bm.verts)} verts"
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    print(f"Collar-tucked Pixar-Anime HD bust: verts={len(mesh.vertices)}, polys={len(mesh.polygons)}")


# ==============================================================================
# STEP 2: SPOTLESS GARMENT CLEANUP + NATIVE PIXAR-ANIME 3-MAP FACE PBR BAKE
# ==============================================================================
def prepare_delighted_bust_albedo(hd_albedo: bpy.types.Image, skin_srgb: np.ndarray) -> bpy.types.Image:
    """
    Preserve native 3D Pixar-Anime cheek blush, nose warmth, lip rose, eye catchlights, and dark hair,
    while gently healing any tiny dark crevice speck inside skin islands & slightly lifting deep neck shadow.
    """
    w, h = hd_albedo.size
    px = np.array(hd_albedo.pixels[:], dtype=np.float32).reshape((h, w, 4))
    srgb = np.clip(px[:, :, :3], 0.0, 1.0)
    r, g, b = srgb[:, :, 0], srgb[:, :, 1], srgb[:, :, 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    warmth = r - b
    redness = r - g

    is_skin = (
        np.clip((warmth - 0.025) / 0.055, 0.0, 1.0)
        * np.clip((luma - 0.30) / 0.16, 0.0, 1.0)
        * np.clip((0.92 - luma) / 0.08, 0.0, 1.0)
        * np.clip((0.22 - redness) / 0.08, 0.0, 1.0)
    )
    blur_r = max(10, w // 64)
    skin_m3 = is_skin[:, :, None]
    num_blur = box_blur_2d(srgb * skin_m3, radius=blur_r, passes=2)
    den_blur = box_blur_2d(skin_m3, radius=blur_r, passes=2)
    low_freq = np.where(den_blur > 1e-3, num_blur / np.maximum(den_blur, 1e-3), srgb)
    lf_luma = 0.299 * low_freq[:, :, 0] + 0.587 * low_freq[:, :, 1] + 0.114 * low_freq[:, :, 2]

    # Heal tiny isolated dark crevice pinholes inside warm skin islands
    tiny_skin_den = box_blur_2d(skin_m3, radius=3, passes=1)[:, :, 0]
    speck_mask = (
        ((tiny_skin_den > 0.65) & (lf_luma > 0.38) & (luma < 0.20)).astype(np.float32)
        * np.clip((0.20 - luma) / 0.12, 0.0, 1.0)
    )
    out_rgb = srgb * (1.0 - speck_mask[:, :, None]) + np.clip(low_freq * 0.85, 0.0, 1.0) * speck_mask[:, :, None]

    # Very gentle shadow lift ONLY where skin is deeply shadowed (luma < 0.44), keeping cheek blush & highlights 100% pure
    deep_shadow_w = is_skin * np.clip((0.46 - luma) / 0.16, 0.0, 1.0) * 0.32
    lifted = np.clip(0.5 * out_rgb + 0.5 * skin_srgb[None, None, :], 0.0, 1.0)
    out_rgb = out_rgb * (1.0 - deep_shadow_w[:, :, None]) + lifted * deep_shadow_w[:, :, None]

    out_px = px.copy()
    out_px[:, :, :3] = np.clip(out_rgb, 0.0, 1.0)
    img = bpy.data.images.new("HD_Bust_PixarClean", width=w, height=h, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(np.ascontiguousarray(out_px.ravel(), dtype=np.float32))
    img.pack()
    return img


def build_clean_raw_body_shader(
    raw_uv_name: str,
    raw_body_albedo: bpy.types.Image,
    skin_srgb: np.ndarray,
) -> bpy.types.Material:
    """
    Object-space + Albedo Cloth Cleanup Shader on `raw_body`:
    Transforms raw photogrammetry outfit into spotless AAA Pixar-Anime apparel with subtle sculptural fold shading:
    - Obsidian-black overshirt & tailored trousers -> velvety matte charcoal-black [0.068, 0.071, 0.079]
    - Front crew-neck white tee (|X| < 0.145, Y < 0.04, Z in [0.80, 1.35], bright) -> crisp clean off-white [0.90, 0.905, 0.915]
    - Hands / wrists / collar skin -> matched 1:1 to `skin_srgb`
    - Sneakers -> matte charcoal uppers with crisp clean light soles
    """
    mat = bpy.data.materials.new("Mat_RawBodyEmitTemp")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    uv_node = nt.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map = raw_uv_name
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = raw_body_albedo
    nt.links.new(uv_node.outputs["UV"], tex.inputs["Vector"])

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep_co = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep_co.inputs["Vector"])

    sep_c = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tex.outputs["Color"], sep_c.inputs["Color"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(tex.outputs["Color"], bw.inputs["Color"])

    def math_op(op, a, b):
        m = nt.nodes.new("ShaderNodeMath"); m.operation = op
        if isinstance(a, (int, float)): m.inputs[0].default_value = a
        else: nt.links.new(a, m.inputs[0])
        if isinstance(b, (int, float)): m.inputs[1].default_value = b
        else: nt.links.new(b, m.inputs[1])
        return m.outputs["Value"]

    def map_range(val, f0, f1, t0, t1):
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        mr.clamp = True
        mr.inputs[1].default_value = f0
        mr.inputs[2].default_value = f1
        mr.inputs[3].default_value = t0
        mr.inputs[4].default_value = t1
        nt.links.new(val, mr.inputs[0])
        return mr.outputs["Result"]

    def mix_rgb(fac, col1, col2):
        mx = nt.nodes.new("ShaderNodeMixRGB"); mx.blend_type = "MIX"
        if isinstance(fac, (int, float)): mx.inputs["Factor"].default_value = fac
        else: nt.links.new(fac, mx.inputs["Factor"])
        if isinstance(col1, tuple):
            lin1 = srgb_to_linear(col1)
            mx.inputs["Color1"].default_value = (lin1[0], lin1[1], lin1[2], 1.0)
        else:
            nt.links.new(col1, mx.inputs["Color1"])
        if isinstance(col2, tuple):
            lin2 = srgb_to_linear(col2)
            mx.inputs["Color2"].default_value = (lin2[0], lin2[1], lin2[2], 1.0)
        else:
            nt.links.new(col2, mx.inputs["Color2"])
        return mx.outputs["Color"]

    def scale_color(col_socket, scalar_socket):
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(scalar_socket, comb.inputs["X"])
        nt.links.new(scalar_socket, comb.inputs["Y"])
        nt.links.new(scalar_socket, comb.inputs["Z"])
        mx = nt.nodes.new("ShaderNodeMixRGB"); mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        nt.links.new(col_socket, mx.inputs["Color1"])
        nt.links.new(comb.outputs["Vector"], mx.inputs["Color2"])
        return mx.outputs["Color"]

    abs_x = math_op("ABSOLUTE", sep_co.outputs["X"], 0.0)
    warmth = math_op("SUBTRACT", sep_c.outputs["Red"], sep_c.outputs["Blue"])
    luma = bw.outputs["Val"]  # Linear luma (~0.02..0.75)

    # Gentle sculptural cloth fold factor from raw luma without raw blotches
    fold_dark = map_range(luma, 0.015, 0.14, 0.80, 1.14)
    fold_light = map_range(luma, 0.08, 0.72, 0.95, 1.02)

    # Base obsidian matte suit/overshirt/trousers
    lin_suit = srgb_to_linear((0.068, 0.071, 0.080))
    c_suit_const = nt.nodes.new("ShaderNodeRGB")
    c_suit_const.outputs["Color"].default_value = (lin_suit[0], lin_suit[1], lin_suit[2], 1.0)
    c_suit = scale_color(c_suit_const.outputs["Color"], fold_dark)

    # Unified deterministic front crew-tee mask tucked strictly ~2.5mm under the sculpted matte-obsidian plackets
    # (never spills past the 28mm placket width; zero black crevices or jagged texture rips!)
    v_open_s = map_range(sep_co.outputs["Z"], 1.200, 1.312, 0.0, 1.0)
    tee_half_x = math_op("ADD", 0.0265, math_op("MULTIPLY", 0.0215, v_open_s))
    dx_tee = math_op("SUBTRACT", abs_x, tee_half_x)
    t_x = map_range(dx_tee, -0.0018, 0.0018, 1.0, 0.0)
    t_y = map_range(sep_co.outputs["Y"], 0.015, -0.005, 0.0, 1.0)
    t_z = math_op("MULTIPLY", map_range(sep_co.outputs["Z"], 0.812, 0.830, 0.0, 1.0), map_range(sep_co.outputs["Z"], 1.304, 1.316, 1.0, 0.0))
    w_tee = math_op("MULTIPLY", t_x, math_op("MULTIPLY", t_y, t_z))

    lin_tee = srgb_to_linear((0.900, 0.904, 0.916))
    c_tee_const = nt.nodes.new("ShaderNodeRGB")
    c_tee_const.outputs["Color"].default_value = (lin_tee[0], lin_tee[1], lin_tee[2], 1.0)
    c_tee = scale_color(c_tee_const.outputs["Color"], fold_light)
    cur = mix_rgb(w_tee, c_suit, c_tee)

    # Clean sneaker uppers (Z < 0.11) + crisp off-white sneaker outsoles (Z <= 0.026m above floor)
    w_shoe = map_range(sep_co.outputs["Z"], 0.088, 0.112, 1.0, 0.0)
    cur = mix_rgb(w_shoe, cur, (0.092, 0.095, 0.106))
    w_sole = map_range(sep_co.outputs["Z"], 0.023, 0.028, 1.0, 0.0)
    cur = mix_rgb(w_sole, cur, (0.85, 0.86, 0.88))

    # Skin strictly on hands/wrists (|X| > 0.33, Z in [0.68, 1.06]); zero torso/collar skin smear!
    is_warm_skin = math_op("MULTIPLY", map_range(warmth, 0.020, 0.065, 0.0, 1.0), map_range(luma, 0.11, 0.24, 0.0, 1.0))
    w_hands = math_op("MULTIPLY", map_range(abs_x, 0.33, 0.37, 0.0, 1.0), math_op("MULTIPLY", map_range(sep_co.outputs["Z"], 0.68, 0.72, 0.0, 1.0), map_range(sep_co.outputs["Z"], 1.02, 1.06, 1.0, 0.0)))
    w_skin = math_op("MULTIPLY", is_warm_skin, w_hands)

    # Preserve soft hand finger crease depth subtly modulated onto Pixar-anime skin tone
    fold_skin = map_range(luma, 0.14, 0.50, 0.86, 1.06)
    lin_skin = srgb_to_linear((float(skin_srgb[0]), float(skin_srgb[1]), float(skin_srgb[2])))
    c_skin_const = nt.nodes.new("ShaderNodeRGB")
    c_skin_const.outputs["Color"].default_value = (lin_skin[0], lin_skin[1], lin_skin[2], 1.0)
    c_skin = scale_color(c_skin_const.outputs["Color"], fold_skin)
    cur = mix_rgb(w_skin, cur, c_skin)

    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cur, emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def add_sculpted_crew_collar(
    bm: bmesh.types.BMesh,
    nose_x: float,
    neck_cy: float,
) -> None:
    """
    Append a closed, 48-segment tailored ribbed white crew-neck t-shirt collar (`material_index=0`)
    seated seamlessly between `hd_bust`'s anatomical neck skirt and `body_rem`'s front chest tee /
    standing matte-black overshirt lapels, UV-mapped into the reserved top cotton-rib strip v in [0.954, 0.994].
    """
    uv_lay = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    n_seg = 48
    rings: list[list[bmesh.types.BMVert]] = []
    profile_vs: list[list[float]] = []

    for i in range(n_seg):
        th = (2.0 * math.pi * i) / float(n_seg)
        cx = math.cos(th)
        sy = math.sin(th)  # -1 = front throat (-Y), +1 = back nape (+Y)

        rx_in = 0.0485
        ry_in = 0.0405 if sy < 0.0 else 0.0455
        x_in = nose_x + cx * rx_in
        y_in = neck_cy + sy * ry_in
        rad_dir = Vector((cx / rx_in, sy / ry_in, 0.0)).normalized()

        front_fac = (max(0.0, -sy)) ** 1.20
        thickness = 0.0052 + 0.0086 * front_fac
        if sy < 0.0:
            z_top = 1.300 + 0.020 * ((1.0 + sy) ** 1.35)
        else:
            z_top = 1.320 + 0.012 * sy

        # Smooth rounded C-profile that rolls inward cleanly into the chest tee (zero overhanging shelf!)
        sec_pts = [
            (-0.0025, -0.0210, 0.986),
            (-0.0010, -0.0070, 0.988),
            (0.0005, -0.0012, 0.984),
            (thickness * 0.45, 0.0006, 0.980),
            (thickness * 0.88, -0.0015, 0.976),
            (thickness * 1.00, -0.0055, 0.974),
            (thickness * 0.85, -0.0105, 0.972),
            (thickness * 0.48, -0.0155, 0.968),
            (-0.0005, -0.0195, 0.974),
        ]

        sec_verts: list[bmesh.types.BMVert] = []
        sec_vcoords: list[float] = []
        for r_off, dz, uv_v in sec_pts:
            pt = Vector((x_in, y_in, z_top + dz)) + rad_dir * r_off
            sec_verts.append(bm.verts.new(pt))
            sec_vcoords.append(uv_v)
        rings.append(sec_verts)
        profile_vs.append(sec_vcoords)

    n_prof = len(rings[0])
    collar_faces: list[bmesh.types.BMFace] = []
    for i in range(n_seg):
        inext = (i + 1) % n_seg
        u0 = i / float(n_seg)
        u1 = (i + 1) / float(n_seg)
        for p in range(n_prof):
            pnext = (p + 1) % n_prof
            v00 = rings[i][p]
            v10 = rings[inext][p]
            v11 = rings[inext][pnext]
            v01 = rings[i][pnext]
            try:
                f = bm.faces.new((v00, v10, v11, v01))
            except ValueError:
                continue
            f.material_index = 0
            f.smooth = True
            uvs = (
                (u0, profile_vs[i][p]),
                (u1, profile_vs[inext][p]),
                (u1, profile_vs[inext][pnext]),
                (u0, profile_vs[i][pnext]),
            )
            for lp, uv_val in zip(f.loops, uvs):
                lp[uv_lay].uv = uv_val
            collar_faces.append(f)

    if collar_faces:
        bmesh.ops.recalc_face_normals(bm, faces=collar_faces)
    print(f"Added sculpted 48-seg crew-neck rib collar: {len(collar_faces)} quads ({len(collar_faces) * 2} tris)")


def add_sculpted_overshirt_collar(
    bm: bmesh.types.BMesh,
    nose_x: float,
    neck_cy: float,
) -> None:
    """
    Append a watertight, closed 40-segment sculpted matte-obsidian folded overshirt collar (`material_index=0`)
    framing the white crew-neck rib collar and blending cleanly into `body_rem`'s front jacket lapels
    and shoulder yoke, UV-mapped into the mipmap-safe matte-obsidian strip v in [0.880, 0.904].
    """
    uv_lay = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    n_seg = 40
    rings: list[list[bmesh.types.BMVert]] = []
    profile_vs: list[list[float]] = []

    for i in range(n_seg + 1):
        s = i / float(n_seg)
        th = math.radians(-50.0 + 280.0 * s)
        cx = math.cos(th)
        sy = math.sin(th)

        end_fade = smoothstep(0.0, 0.16, s) * smoothstep(1.0, 0.84, s)
        w_end = 0.30 + 0.70 * end_fade

        rx_in = 0.0560
        ry_in = 0.0585 if sy < 0.0 else 0.0545
        x_flare = (1.0 if cx >= 0.0 else -1.0) * 0.011 * (max(0.0, -sy) ** 1.35)
        x_in = nose_x + cx * rx_in + x_flare
        y_in = neck_cy + sy * ry_in
        rad_dir = Vector((x_in - nose_x, y_in - neck_cy, 0.0)).normalized()

        if sy >= 0.0:
            z_crest = 1.336 + 0.009 * sy
        else:
            t_front = max(0.0, min(1.0, 1.0 + sy / 0.77))
            z_crest = 1.296 + 0.040 * (t_front ** 1.15)

        leaf_w = 0.014 + 0.015 * smoothstep(-0.65, 0.15, sy)
        sec_pts = [
            (-0.0020, -0.032 * w_end, 0.904),
            (-0.0005, -0.015 * w_end, 0.902),
            (0.0010, -0.002 * w_end, 0.898),
            (0.0048, 0.0016 * w_end, 0.894),
            (0.0095, -0.0016 * w_end, 0.890),
            (leaf_w * 0.78, -0.012 * w_end, 0.887),
            (leaf_w * 1.02, -0.025 * w_end, 0.884),
            (leaf_w * 0.92, -0.036 * w_end, 0.880),
            (leaf_w * 0.45, -0.040 * w_end, 0.884),
            (-0.0015, -0.038 * w_end, 0.904),
        ]

        sec_verts: list[bmesh.types.BMVert] = []
        sec_vcoords: list[float] = []
        for r_off, dz, uv_v in sec_pts:
            pt = Vector((x_in, y_in, z_crest + dz)) + rad_dir * r_off
            sec_verts.append(bm.verts.new(pt))
            sec_vcoords.append(uv_v)
        rings.append(sec_verts)
        profile_vs.append(sec_vcoords)

    n_prof = len(rings[0])
    overshirt_faces: list[bmesh.types.BMFace] = []
    for i in range(n_seg):
        u0 = i / float(n_seg)
        u1 = (i + 1) / float(n_seg)
        for p in range(n_prof):
            pnext = (p + 1) % n_prof
            v00 = rings[i][p]
            v10 = rings[i + 1][p]
            v11 = rings[i + 1][pnext]
            v01 = rings[i][pnext]
            try:
                f = bm.faces.new((v00, v10, v11, v01))
            except ValueError:
                continue
            f.material_index = 0
            f.smooth = True
            uvs = (
                (u0, profile_vs[i][p]),
                (u1, profile_vs[i + 1][p]),
                (u1, profile_vs[i + 1][pnext]),
                (u0, profile_vs[i][pnext]),
            )
            for lp, uv_val in zip(f.loops, uvs):
                lp[uv_lay].uv = uv_val
            overshirt_faces.append(f)

    for cap_verts in (rings[0], list(reversed(rings[n_seg]))):
        try:
            cf = bm.faces.new(cap_verts)
            cf.material_index = 0
            cf.smooth = True
            for lp in cf.loops:
                lp[uv_lay].uv = (0.5, 0.892)
            overshirt_faces.append(cf)
        except ValueError:
            pass

    if overshirt_faces:
        bmesh.ops.recalc_face_normals(bm, faces=overshirt_faces)
    print(f"Added sculpted 40-seg matte-obsidian overshirt collar: {len(overshirt_faces)} faces")


def placket_inner_half_x(z: float) -> float:
    """Shared deterministic vertical-to-V jacket placket opening half-width."""
    v_open = smoothstep(1.200, 1.312, z)
    return 0.024 + 0.022 * (v_open ** 1.15)


def add_sculpted_jacket_plackets(
    bm: bmesh.types.BMesh,
    nose_x: float,
) -> None:
    """
    Append BVHTree-conformed, watertight sculpted matte-obsidian jacket plackets (`material_index=0`)
    along both vertical/V-lapel borders from Z=0.832m up into `add_sculpted_overshirt_collar` (Z=1.312m),
    replacing the jagged painted black/white texture edge with crisp tailored 3D garment hems.
    """
    from mathutils.bvhtree import BVHTree

    uv_lay = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    bm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bm)

    n_seg = 48
    z_bot = 0.832
    z_top = 1.312
    total_faces = 0

    for sx in (-1.0, 1.0):
        zs = [z_bot + (z_top - z_bot) * (k / float(n_seg)) for k in range(n_seg + 1)]
        y_tees: list[float] = []
        y_raw_peaks: list[float] = []
        y_raw_mids: list[float] = []
        y_outs: list[float] = []

        def _ray_y(rx: float, fb: float, rz: float) -> float:
            ht = bvh.ray_cast(Vector((rx, -0.50, rz)), Vector((0.0, 1.0, 0.0)), 0.70)
            return ht[0].y if ht[0] is not None else fb

        for z in zs:
            xh = placket_inner_half_x(z)
            x_edge = nose_x + sx * xh
            x_tee = nose_x + sx * max(0.0, xh - 0.010)

            fb_tee = -0.095 + 0.072 * smoothstep(z_bot, z_top, z)
            fb_out = fb_tee - 0.016 * (1.0 - 0.55 * smoothstep(1.180, z_top, z))

            y_t = _ray_y(x_tee, fb_tee, z)
            y_r_in = min(
                _ray_y(x_edge + sx * dx, fb_out, z + dz)
                for dx in (-0.001, 0.000, 0.002, 0.004, 0.006, 0.008)
                for dz in (-0.004, 0.0, 0.004)
            )
            y_r_mid = min(
                _ray_y(x_edge + sx * dx, fb_out, z + dz)
                for dx in (0.008, 0.011, 0.014, 0.017, 0.020)
                for dz in (-0.004, 0.0, 0.004)
            )
            y_r_pk = min(y_r_in, y_r_mid)
            y_o = _ray_y(x_edge + sx * 0.028, y_r_mid, z)

            y_tees.append(y_t)
            y_raw_peaks.append(y_r_pk)
            y_raw_mids.append(y_r_mid)
            y_outs.append(y_o)

        y_peaks = list(y_raw_peaks)
        y_mids = list(y_raw_mids)

        for _ in range(4):
            for arr in (y_tees, y_peaks, y_mids, y_outs):
                nxt = arr.copy()
                nxt[0] = 0.75 * arr[0] + 0.25 * arr[1]
                nxt[-1] = 0.25 * arr[-2] + 0.75 * arr[-1]
                for idx in range(1, len(arr) - 1):
                    nxt[idx] = 0.25 * arr[idx - 1] + 0.50 * arr[idx] + 0.25 * arr[idx + 1]
                arr[:] = nxt

        rings: list[list[bmesh.types.BMVert]] = []
        profile_vs: list[list[float]] = []

        for k, z in enumerate(zs):
            x_edge = nose_x + sx * placket_inner_half_x(z)
            bot_taper = smoothstep(z_bot, z_bot + 0.022, z)
            top_taper = smoothstep(z_top, z_top - 0.018, z)
            clr_front = 0.0020 + 0.0018 * top_taper
            clr_mid = 0.0018 + 0.0014 * top_taper

            y_t = y_tees[k]
            y_env_pk = min(y_peaks[k], y_raw_peaks[k])
            y_env_mid = min(y_mids[k], y_raw_mids[k])
            y_o = y_outs[k]

            y_front = min(y_env_pk - clr_front, y_t - 0.0080) + 0.0035 * (1.0 - bot_taper)
            y_p5 = min(y_env_mid - clr_mid, y_front + 0.0016)
            y_hem_out = y_o + 0.0042 + 0.0025 * (1.0 - bot_taper)

            sec_pts = [
                (x_edge + sx * 0.007, max(y_t + 0.006, y_front + 0.015), 0.904),
                (x_edge + sx * 0.001, max(y_t - 0.001, y_front + 0.007), 0.902),
                (x_edge - sx * 0.001, y_front + 0.0032, 0.898),
                (x_edge, y_front + 0.0004, 0.893),
                (x_edge + sx * 0.006, y_front - 0.0006, 0.889),
                (x_edge + sx * 0.017, y_p5, 0.884),
                (x_edge + sx * 0.028, y_hem_out, 0.880),
                (x_edge + sx * 0.018, max(y_o + 0.010, y_t + 0.008), 0.904),
            ]
            ring_v = [bm.verts.new(Vector((px, py, z))) for px, py, _ in sec_pts]
            rings.append(ring_v)
            profile_vs.append([uv_v for _, _, uv_v in sec_pts])

        n_prof = len(rings[0])
        side_faces: list[bmesh.types.BMFace] = []
        for k in range(n_seg):
            u0 = k / float(n_seg)
            u1 = (k + 1) / float(n_seg)
            for p in range(n_prof):
                pnext = (p + 1) % n_prof
                v00 = rings[k][p]
                v10 = rings[k + 1][p]
                v11 = rings[k + 1][pnext]
                v01 = rings[k][pnext]
                try:
                    f = bm.faces.new((v00, v10, v11, v01))
                except ValueError:
                    continue
                f.material_index = 0
                f.smooth = True
                uvs = (
                    (u0, profile_vs[k][p]),
                    (u1, profile_vs[k + 1][p]),
                    (u1, profile_vs[k + 1][pnext]),
                    (u0, profile_vs[k][pnext]),
                )
                for lp, uv_val in zip(f.loops, uvs):
                    lp[uv_lay].uv = uv_val
                side_faces.append(f)

        for cap_verts in (rings[0], list(reversed(rings[n_seg]))):
            try:
                cf = bm.faces.new(cap_verts)
                cf.material_index = 0
                cf.smooth = True
                for lp in cf.loops:
                    lp[uv_lay].uv = (0.5, 0.892)
                side_faces.append(cf)
            except ValueError:
                pass

        if side_faces:
            bmesh.ops.recalc_face_normals(bm, faces=side_faces)
            total_faces += len(side_faces)

    print(f"Added sculpted BVHTree-conformed jacket plackets (both sides): {total_faces} faces")


def build_clean_body_and_hd_head(
    raw_body: bpy.types.Object,
    raw_body_albedo: bpy.types.Image,
    hd_bust_high: bpy.types.Object,
    hd_bust_clean: bpy.types.Image,
    concept_img: bpy.types.Image,
    lm: dict[str, object],
    skin_srgb: np.ndarray,
) -> bpy.types.Object:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = "Standard"

    raw_uv_name = raw_body.data.uv_layers.active.name
    neck_cy = float(lm["neck_cy"])
    nose_x = float(lm["nose_x"])

    body_rem = raw_body.copy()
    body_rem.data = raw_body.data.copy()
    body_rem.name = "Companion_Body_Remesh"
    scene.collection.objects.link(body_rem)

    body_rem.data.remesh_voxel_size = 0.0038
    body_rem.data.remesh_voxel_adaptivity = 0.0
    bpy.ops.object.select_all(action="DESELECT")
    body_rem.select_set(True)
    bpy.context.view_layer.objects.active = body_rem
    bpy.ops.object.voxel_remesh()

    sw = body_rem.modifiers.new(name="ShrinkwrapRaw", type="SHRINKWRAP")
    sw.target = raw_body
    sw.wrap_method = "NEAREST_SURFACEPOINT"

    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev_b0 = body_rem.evaluated_get(depsgraph)
    b0_mesh = bpy.data.meshes.new_from_object(ev_b0, preserve_all_data_layers=True, depsgraph=depsgraph)
    old_m = body_rem.data
    body_rem.modifiers.clear()
    body_rem.data = b0_mesh
    bpy.data.meshes.remove(old_m)

    # Pre-decimation analytical cavity trim + watertight anatomical shoulder-yoke press (zero torn collar flaps!)
    def crew_z(x: float, y: float) -> float:
        dx = x - nose_x
        dy = y - neck_cy
        uy = dy / max(1e-4, math.hypot(dx, dy))
        if uy < 0.0:
            return 1.292 + 0.020 * ((1.0 + uy) ** 1.25)
        return 1.312 + 0.010 * uy

    def cav_r(x: float, y: float) -> float:
        ry_cav = 0.048 if y < neck_cy else 0.046
        return math.hypot((x - nose_x) / 0.052, (y - neck_cy) / ry_cav)

    def yoke_max_z(x: float, y: float, r_v: float) -> float:
        uy = (y - neck_cy) / max(1e-4, r_v)
        return 1.312 + 0.008 * max(0.0, uy) - 0.16 * max(0.0, r_v - 0.070)

    bm_body = bmesh.new()
    bm_body.from_mesh(body_rem.data)
    bm_body.faces.ensure_lookup_table()

    del_cav_faces = []
    for f in bm_body.faces:
        fc = f.calc_center_median()
        r_fc = math.hypot(fc.x - nose_x, fc.y - neck_cy)
        in_neck_hole = cav_r(fc.x, fc.y) < 1.03 and fc.z > crew_z(fc.x, fc.y) + 0.004
        in_hidden_stump = r_fc < 0.064 and fc.y >= -0.030 and fc.z > 1.316
        if fc.z > 1.358 or in_neck_hole or in_hidden_stump:
            del_cav_faces.append(f)
    if del_cav_faces:
        bmesh.ops.delete(bm_body, geom=del_cav_faces, context="FACES")

    bm_body.verts.ensure_lookup_table()
    vis: set[int] = set()
    bcomps: list[list[bmesh.types.BMVert]] = []
    for v in bm_body.verts:
        if v.index in vis:
            continue
        st = [v]
        comp = []
        vis.add(v.index)
        while st:
            cur = st.pop()
            comp.append(cur)
            for e in cur.link_edges:
                ov = e.other_vert(cur)
                if ov.index not in vis:
                    vis.add(ov.index)
                    st.append(ov)
        bcomps.append(comp)
    bcomps.sort(key=len, reverse=True)
    if len(bcomps) > 1:
        bmesh.ops.delete(bm_body, geom=[v for c in bcomps[1:] for v in c], context="VERTS")

    # Smoothly press any standing photogrammetry collar flaps down onto the watertight shoulder yoke,
    # and roll the inner cavity rim cleanly inside the sculpted white crew collar
    bm_body.verts.ensure_lookup_table()
    for v in bm_body.verts:
        cr = cav_r(v.co.x, v.co.y)
        cz = crew_z(v.co.x, v.co.y)
        r_v = math.hypot(v.co.x - nose_x, v.co.y - neck_cy)
        if cr < 1.05 and v.co.z > cz - 0.012:
            tuck_w = smoothstep(1.05, 0.86, cr) * smoothstep(cz - 0.012, cz + 0.004, v.co.z)
            if tuck_w > 1e-3 and r_v > 1e-4:
                r_t = r_v * (1.0 - 0.22 * tuck_w)
                v.co.x = nose_x + ((v.co.x - nose_x) / r_v) * r_t
                v.co.y = neck_cy + ((v.co.y - neck_cy) / r_v) * r_t
                v.co.z -= 0.011 * tuck_w
        if abs(v.co.x - nose_x) < 0.048 and v.co.y < -0.032 and 1.270 <= v.co.z <= 1.315:
            flat_w = smoothstep(1.270, 1.288, v.co.z) * smoothstep(0.048, 0.020, abs(v.co.x - nose_x))
            v.co.y = v.co.y * (1.0 - 0.72 * flat_w) + max(v.co.y, -0.031) * (0.72 * flat_w)
        if 0.056 <= r_v <= 0.116 and v.co.y >= -0.042:
            ymz = yoke_max_z(v.co.x, v.co.y, r_v)
            if v.co.z > ymz - 0.006:
                press_w = smoothstep(0.116, 0.095, r_v) * smoothstep(-0.042, -0.018, v.co.y) * smoothstep(ymz - 0.006, ymz + 0.008, v.co.z)
                v.co.z = v.co.z * (1.0 - press_w) + min(v.co.z, ymz) * press_w

    # Targeted volume-preserving Taubin smoothing (12 passes) on full front white tee & watertight shoulder yoke
    bm_body.verts.ensure_lookup_table()
    bm_body.edges.ensure_lookup_table()
    fair_verts: list[bmesh.types.BMVert] = []
    for v in bm_body.verts:
        co = v.co
        r_co = math.hypot(co.x - nose_x, co.y - neck_cy)
        in_chest_tee = abs(co.x - nose_x) < 0.048 and co.y < -0.015 and 0.835 <= co.z <= 1.308
        in_collar_base = 1.285 <= co.z <= 1.335 and r_co < 0.118
        if in_chest_tee or in_collar_base:
            fair_verts.append(v)

    for _ in range(12):
        for factor in (0.40, -0.38):
            disp: dict[int, Vector] = {}
            for v in fair_verts:
                if v.is_boundary:
                    b_nbrs = [e.other_vert(v).co for e in v.link_edges if e.other_vert(v).is_boundary]
                    if len(b_nbrs) == 2:
                        avg = 0.5 * (b_nbrs[0] + b_nbrs[1])
                        disp[v.index] = (avg - v.co) * (0.30 * abs(factor))
                else:
                    nbrs = [e.other_vert(v).co for e in v.link_edges]
                    if nbrs:
                        avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                        disp[v.index] = (avg - v.co) * factor
            for v in fair_verts:
                if v.index in disp:
                    v.co += disp[v.index]

    bm_body.to_mesh(body_rem.data)
    bm_body.free()
    body_rem.data.update()

    # Collar & front placket protected decimation: keep smooth torso opening & shoulder density
    tri_rem = sum(max(1, len(p.vertices) - 2) for p in body_rem.data.polygons)
    vg_prot = body_rem.vertex_groups.new(name="Collar_Protect")
    prot_vert_set: set[int] = set()
    for v in body_rem.data.vertices:
        wz = smoothstep(1.205, 1.230, v.co.z) * smoothstep(1.370, 1.352, v.co.z)
        wx = smoothstep(0.105, 0.080, abs(v.co.x - nose_x))
        collar_wp = wz * wx * 0.35

        wz_pl = smoothstep(0.815, 0.840, v.co.z) * smoothstep(1.370, 1.352, v.co.z)
        wx_pl = smoothstep(0.068, 0.052, abs(v.co.x - nose_x))
        wy_pl = smoothstep(0.010, -0.025, v.co.y)
        wp = max(collar_wp, wz_pl * wx_pl * wy_pl * 0.25)

        if wp > 1e-4:
            vg_prot.add([v.index], wp, "REPLACE")
            if wp >= 0.20:
                prot_vert_set.add(v.index)
    prot_tris = sum(
        max(1, len(p.vertices) - 2)
        for p in body_rem.data.polygons
        if any(vi in prot_vert_set for vi in p.vertices)
    )
    unprot_tris = max(1, tri_rem - prot_tris)
    dec_ratio = min(1.0, 17000.0 / float(max(1, tri_rem)))

    dec_b = body_rem.modifiers.new(name="DecimateBody", type="DECIMATE")
    dec_b.decimate_type = "COLLAPSE"
    dec_b.vertex_group = "Collar_Protect"
    dec_b.invert_vertex_group = True
    dec_b.ratio = dec_ratio
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev_bd = body_rem.evaluated_get(depsgraph)
    body_dec_mesh = bpy.data.meshes.new_from_object(ev_bd, preserve_all_data_layers=True, depsgraph=depsgraph)
    old_m = body_rem.data
    body_rem.modifiers.clear()
    body_rem.data = body_dec_mesh
    bpy.data.meshes.remove(old_m)
    body_rem.vertex_groups.clear()

    tri_body_dec = sum(max(1, len(p.vertices) - 2) for p in body_rem.data.polygons)
    print(f"Collar-protected body decimate: pre={tri_rem}, prot={prot_tris}, unprot={unprot_tris}, ratio={dec_ratio:.3f} -> post={tri_body_dec} tris")

    for p in body_rem.data.polygons:
        p.use_smooth = True
    body_rem.data.update()

    while len(body_rem.data.uv_layers) > 0:
        body_rem.data.uv_layers.remove(body_rem.data.uv_layers[0])
    uv_b = body_rem.data.uv_layers.new(name="UVMap")
    uv_b.active = True
    uv_b.active_render = True

    bpy.ops.object.select_all(action="DESELECT")
    body_rem.select_set(True)
    bpy.context.view_layer.objects.active = body_rem
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(62.0), island_margin=0.012)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Reserve mipmap-safe atlas bands v in [0.856, 0.936] (obsidian collar/plackets) and [0.936, 1.000] (white crew collar)
    bm_b_uv = bmesh.new()
    bm_b_uv.from_mesh(body_rem.data)
    b_uv_lay = bm_b_uv.loops.layers.uv.active
    if b_uv_lay is not None:
        for f in bm_b_uv.faces:
            for lp in f.loops:
                lp[b_uv_lay].uv.y *= 0.840
    bm_b_uv.to_mesh(body_rem.data)
    bm_b_uv.free()
    body_rem.data.update()

    mat_raw_emit = build_clean_raw_body_shader(raw_uv_name, raw_body_albedo, skin_srgb)
    raw_body.data.materials.clear()
    raw_body.data.materials.append(mat_raw_emit)

    baked_body_img = bpy.data.images.new("Companion_Body_Baked", width=1024, height=1024, alpha=False)
    baked_body_img.colorspace_settings.name = "sRGB"

    mat_body_bake = bpy.data.materials.new("Mat_BodyBakeTemp")
    mat_body_bake.use_nodes = True
    nt_bb = mat_body_bake.node_tree
    nt_bb.nodes.clear()
    bb_out = nt_bb.nodes.new("ShaderNodeOutputMaterial")
    bb_bsdf = nt_bb.nodes.new("ShaderNodeBsdfPrincipled")
    nt_bb.links.new(bb_bsdf.outputs["BSDF"], bb_out.inputs["Surface"])
    bb_target = nt_bb.nodes.new("ShaderNodeTexImage")
    bb_target.image = baked_body_img
    for n in nt_bb.nodes:
        n.select = False
    bb_target.select = True
    nt_bb.nodes.active = bb_target
    body_rem.data.materials.clear()
    body_rem.data.materials.append(mat_body_bake)

    bpy.ops.object.select_all(action="DESELECT")
    raw_body.select_set(True)
    body_rem.select_set(True)
    bpy.context.view_layer.objects.active = body_rem
    bpy.ops.object.bake(
        type="EMIT",
        use_selected_to_active=True,
        cage_extrusion=0.0028,
        max_ray_distance=0.012,
        margin=16,
        use_clear=True,
    )

    bw_img, bh_img = baked_body_img.size
    bpx = np.array(baked_body_img.pixels[:], dtype=np.float32).reshape((bh_img, bw_img, 4))
    y_heal_end = int(bh_img * 0.854)
    brgb = bpx[:y_heal_end, :, :3].copy()
    for _ in range(10):
        bluma = 0.299 * brgb[:, :, 0] + 0.587 * brgb[:, :, 1] + 0.114 * brgb[:, :, 2]
        miss = bluma < 0.035
        if not np.any(miss):
            break
        valid_m = (~miss).astype(np.float32)[:, :, None]
        blur_num = box_blur_2d(brgb * valid_m, radius=3, passes=1)
        blur_den = box_blur_2d(valid_m, radius=3, passes=1)
        healed = np.where(blur_den > 1e-3, blur_num / np.maximum(blur_den, 1e-3), brgb)
        brgb = np.where(miss[:, :, None] & (blur_den > 1e-3), healed, brgb)
    bpx[:y_heal_end, :, :3] = brgb

    u_cols = (np.arange(bw_img, dtype=np.float32) + 0.5) / float(bw_img)

    # Strip 1 [0.856, 0.936]: mipmap-safe velvety matte-obsidian overshirt collar & plackets (uv_v in [0.880, 0.904])
    y_s1_lo = int(bh_img * 0.856)
    y_s1_hi = int(bh_img * 0.936)
    v_s1 = (np.arange(y_s1_lo, y_s1_hi, dtype=np.float32) + 0.5) / float(bh_img)
    shade_s1 = np.where(
        v_s1 < 0.896,
        0.96 + 0.10 * np.clip((v_s1 - 0.876) / 0.020, 0.0, 1.0),
        1.06 - 0.18 * np.clip((v_s1 - 0.896) / 0.020, 0.0, 1.0),
    )
    weave_u = 1.0 + 0.015 * np.cos(2.0 * np.pi * 120.0 * u_cols)
    suit_base = np.array([0.068, 0.071, 0.080], dtype=np.float32)
    bpx[y_s1_lo:y_s1_hi, :, :3] = np.clip((shade_s1[:, None] * weave_u[None, :])[:, :, None] * suit_base[None, None, :], 0.0, 1.0)
    bpx[y_s1_lo:y_s1_hi, :, 3] = 1.0

    # Strip 2 [0.936, 1.000]: mipmap-safe clean ribbed off-white cotton crew-collar strip (uv_v in [0.968, 0.988])
    y_strip_lo = int(bh_img * 0.936)
    rib_u = 1.0 + 0.012 * np.cos(2.0 * np.pi * 96.0 * u_cols)
    v_rows = (np.arange(y_strip_lo, bh_img, dtype=np.float32) + 0.5) / float(bh_img)
    shade_v = np.where(
        v_rows < 0.958,
        0.955,
        np.where(
            v_rows < 0.972,
            0.955 + 0.045 * (v_rows - 0.958) / 0.014,
            np.where(
                v_rows < 0.986,
                1.000,
                1.000 - 0.070 * np.clip((v_rows - 0.986) / 0.012, 0.0, 1.0),
            ),
        ),
    )
    rib_shade = shade_v[:, None] * rib_u[None, :]
    tee_base = np.array([0.900, 0.904, 0.916], dtype=np.float32)
    bpx[y_strip_lo:bh_img, :, :3] = np.clip(rib_shade[:, :, None] * tee_base[None, None, :], 0.0, 1.0)
    bpx[y_strip_lo:bh_img, :, 3] = 1.0

    baked_body_img.pixels.foreach_set(np.ascontiguousarray(bpx.ravel(), dtype=np.float32))
    baked_body_img.pack()

    mat_body = bpy.data.materials.new("Mat_Companion_Body")
    mat_body.use_nodes = True
    nt_b = mat_body.node_tree
    nt_b.nodes.clear()
    out_b = nt_b.nodes.new("ShaderNodeOutputMaterial")
    bsdf_b = nt_b.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_b.inputs["Metallic"].default_value = 0.0
    bsdf_b.inputs["Roughness"].default_value = 0.78
    if "Specular IOR Level" in bsdf_b.inputs:
        bsdf_b.inputs["Specular IOR Level"].default_value = 0.22
    tex_b = nt_b.nodes.new("ShaderNodeTexImage")
    tex_b.image = baked_body_img
    nt_b.links.new(tex_b.outputs["Color"], bsdf_b.inputs["Base Color"])
    nt_b.links.new(bsdf_b.outputs["BSDF"], out_b.inputs["Surface"])
    body_rem.data.materials.clear()
    body_rem.data.materials.append(mat_body)
    bpy.data.materials.remove(mat_body_bake)
    bpy.data.materials.remove(mat_raw_emit)

    # Append sculpted white crew-neck collar, matte-obsidian overshirt collar,
    # and BVHTree-conformed jacket plackets onto Slot 0 (`body_rem`) — zero per-triangle sawtooth heal!
    bm_collar = bmesh.new()
    bm_collar.from_mesh(body_rem.data)
    add_sculpted_crew_collar(bm_collar, nose_x, neck_cy)
    add_sculpted_overshirt_collar(bm_collar, nose_x, neck_cy)
    add_sculpted_jacket_plackets(bm_collar, nose_x)
    bm_collar.to_mesh(body_rem.data)
    bm_collar.free()
    for p in body_rem.data.polygons:
        p.use_smooth = True
    body_rem.data.update()

    # ==================================================================
    # PART B: 17.5k-tri Retopo Pixar-Anime Head + 3-Map Bake (BaseColor / Normal / MR)
    # ==================================================================
    head_low = hd_bust_high.copy()
    head_low.data = hd_bust_high.data.copy()
    head_low.name = "Companion_Head_Retopo"
    scene.collection.objects.link(head_low)

    tri_h = sum(max(1, len(p.vertices) - 2) for p in head_low.data.polygons)
    dec_h = head_low.modifiers.new(name="DecimateHead", type="DECIMATE")
    dec_h.decimate_type = "COLLAPSE"
    dec_h.ratio = min(1.0, 17500.0 / float(max(1, tri_h)))

    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev_h = head_low.evaluated_get(depsgraph)
    head_dec_mesh = bpy.data.meshes.new_from_object(ev_h, preserve_all_data_layers=True, depsgraph=depsgraph)
    old_hm = head_low.data
    head_low.modifiers.clear()
    head_low.data = head_dec_mesh
    bpy.data.meshes.remove(old_hm)

    sw_h = head_low.modifiers.new(name="ShrinkwrapHead", type="SHRINKWRAP")
    sw_h.target = hd_bust_high
    sw_h.wrap_method = "NEAREST_SURFACEPOINT"
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev_h2 = head_low.evaluated_get(depsgraph)
    head_sw_mesh = bpy.data.meshes.new_from_object(ev_h2, preserve_all_data_layers=True, depsgraph=depsgraph)
    old_hm2 = head_low.data
    head_low.modifiers.clear()
    head_low.data = head_sw_mesh
    bpy.data.meshes.remove(old_hm2)

    for p in head_low.data.polygons:
        p.use_smooth = True
    head_low.data.update()

    while len(head_low.data.uv_layers) > 0:
        head_low.data.uv_layers.remove(head_low.data.uv_layers[0])
    uv_h = head_low.data.uv_layers.new(name="UVMap")
    uv_h.active = True
    uv_h.active_render = True

    # Hero-Priority Split UV Unwrap: give the contiguous front face/eyes/nose/mouth ~150x more texel density!
    bm_uv = bmesh.new()
    bm_uv.from_mesh(head_low.data)
    bm_uv.faces.ensure_lookup_table()
    eye_z_uv = float(lm["eye_z"])
    bridge_y_uv = float(lm["bridge_y"])

    cand_face_set: set[int] = set()
    for f in bm_uv.faces:
        f.normal_update()
        fc = f.calc_center_median()
        if (
            f.normal.y < -0.18
            and abs(fc.x - nose_x) < 0.068
            and 1.362 <= fc.z <= eye_z_uv + 0.022
            and fc.y < -0.048
            and not (fc.z > eye_z_uv + 0.009 and fc.y < bridge_y_uv - 0.005)
        ):
            cand_face_set.add(f.index)

    # Keep only the largest edge-connected component as Zone 1 (single fold-free front portrait sheet)
    seen_cf: set[int] = set()
    cf_comps: list[list[int]] = []
    for fi in cand_face_set:
        if fi in seen_cf:
            continue
        comp = []
        st = [bm_uv.faces[fi]]
        seen_cf.add(fi)
        while st:
            cur_f = st.pop()
            comp.append(cur_f.index)
            for e in cur_f.edges:
                for lf in e.link_faces:
                    if lf.index in cand_face_set and lf.index not in seen_cf:
                        seen_cf.add(lf.index)
                        st.append(lf)
        cf_comps.append(comp)
    cf_comps.sort(key=len, reverse=True)
    hero_face_indices: set[int] = set(cf_comps[0]) if cf_comps else set()
    assert len(hero_face_indices) >= 200, f"Hero front face component unexpectedly small: {len(hero_face_indices)}"
    bm_uv.free()

    bpy.ops.object.select_all(action="DESELECT")
    head_low.select_set(True)
    bpy.context.view_layer.objects.active = head_low
    bpy.ops.object.mode_set(mode="EDIT")

    # Zone 1: Unwrap Hero Front Face continuously
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action="DESELECT")
    bm_ed = bmesh.from_edit_mesh(head_low.data)
    bm_ed.faces.ensure_lookup_table()
    for f in bm_ed.faces:
        f.select_set(f.index in hero_face_indices)
    bmesh.update_edit_mesh(head_low.data, loop_triangles=False, destructive=False)
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.004)

    # Zone 2: Smart-project hair, ears, skull & neck with wider island margin to block collar/hair UV bleed
    bm_ed.faces.ensure_lookup_table()
    for f in bm_ed.faces:
        f.select_set(f.index not in hero_face_indices)
    bmesh.update_edit_mesh(head_low.data, loop_triangles=False, destructive=False)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.05)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Pack Zone 1 into [0.02..0.70, 0.04..0.96] preserving aspect ratio, Zone 2 into [0.73..0.99, 0.02..0.98]
    bm_pack = bmesh.new()
    bm_pack.from_mesh(head_low.data)
    bm_pack.faces.ensure_lookup_table()
    uv_lay_p = bm_pack.loops.layers.uv.active
    assert uv_lay_p is not None

    z1_us = [lp[uv_lay_p].uv.x for f in bm_pack.faces if f.index in hero_face_indices for lp in f.loops]
    z1_vs = [lp[uv_lay_p].uv.y for f in bm_pack.faces if f.index in hero_face_indices for lp in f.loops]
    u1_0, u1_1 = min(z1_us), max(z1_us)
    v1_0, v1_1 = min(z1_vs), max(z1_vs)
    sc1 = min((0.70 - 0.02) / max(1e-5, u1_1 - u1_0), (0.96 - 0.04) / max(1e-5, v1_1 - v1_0))
    u1_off = 0.02 + 0.5 * ((0.70 - 0.02) - (u1_1 - u1_0) * sc1)
    v1_off = 0.04 + 0.5 * ((0.96 - 0.04) - (v1_1 - v1_0) * sc1)

    z2_us = [lp[uv_lay_p].uv.x for f in bm_pack.faces if f.index not in hero_face_indices for lp in f.loops]
    z2_vs = [lp[uv_lay_p].uv.y for f in bm_pack.faces if f.index not in hero_face_indices for lp in f.loops]
    u2_0, u2_1 = min(z2_us), max(z2_us)
    v2_0, v2_1 = min(z2_vs), max(z2_vs)
    su2 = (0.99 - 0.73) / max(1e-5, u2_1 - u2_0)
    sv2 = (0.98 - 0.02) / max(1e-5, v2_1 - v2_0)

    max_u_face = 0.0
    min_u_other = 1.0
    for f in bm_pack.faces:
        if f.index in hero_face_indices:
            for lp in f.loops:
                nu = u1_off + (lp[uv_lay_p].uv.x - u1_0) * sc1
                nv = v1_off + (lp[uv_lay_p].uv.y - v1_0) * sc1
                lp[uv_lay_p].uv = Vector((nu, nv))
                max_u_face = max(max_u_face, nu)
        else:
            for lp in f.loops:
                nu = 0.73 + (lp[uv_lay_p].uv.x - u2_0) * su2
                nv = 0.02 + (lp[uv_lay_p].uv.y - v2_0) * sv2
                lp[uv_lay_p].uv = Vector((nu, nv))
                min_u_other = min(min_u_other, nu)

    assert max_u_face <= 0.705 and min_u_other >= 0.725, (
        f"UV Zone overlap detected: max_u_face={max_u_face:.4f}, min_u_other={min_u_other:.4f}"
    )

    # Audit eye UV texel area on 1024x1024
    eye_uv_area = 0.0
    for f in bm_pack.faces:
        fc = f.calc_center_median()
        if f.normal.y < 0.0 and 0.018 < fc.x < 0.046 and 1.472 < fc.z < 1.496 and fc.y < -0.065:
            pts_uv = [lp[uv_lay_p].uv for lp in f.loops]
            a = 0.0
            for i in range(len(pts_uv)):
                j = (i + 1) % len(pts_uv)
                a += pts_uv[i].x * pts_uv[j].y - pts_uv[j].x * pts_uv[i].y
            eye_uv_area += abs(a) * 0.5
    eye_equiv_px = math.sqrt(max(0.0, eye_uv_area * (1024.0 * 1024.0)))
    assert eye_equiv_px >= 60.0, f"Eye texel density too low: {eye_equiv_px:.1f} px"
    bm_pack.to_mesh(head_low.data)
    bm_pack.free()
    head_low.data.update()

    head_tris = sum(max(1, len(p.vertices) - 2) for p in head_low.data.polygons)
    print(f"Created Hero-UV Head_Low: verts={len(head_low.data.vertices)}, tris={head_tris}, hero_faces={len(hero_face_indices)}, eye_texels={eye_equiv_px:.1f}x{eye_equiv_px:.1f} px")

    baked_face_albedo = bpy.data.images.new("Zachary_Face_HD", width=1024, height=1024, alpha=False)
    baked_face_albedo.colorspace_settings.name = "sRGB"
    baked_face_normal = bpy.data.images.new("Zachary_Face_Normal", width=768, height=768, alpha=False)
    baked_face_normal.colorspace_settings.name = "Non-Color"
    baked_face_mr = bpy.data.images.new("Zachary_Face_MR", width=512, height=512, alpha=False)
    baked_face_mr.colorspace_settings.name = "Non-Color"

    mat_hl_bake = bpy.data.materials.new("Mat_HeadBakeTemp")
    mat_hl_bake.use_nodes = True
    nt_hb = mat_hl_bake.node_tree
    nt_hb.nodes.clear()
    hb_out = nt_hb.nodes.new("ShaderNodeOutputMaterial")
    hb_bsdf = nt_hb.nodes.new("ShaderNodeBsdfPrincipled")
    nt_hb.links.new(hb_bsdf.outputs["BSDF"], hb_out.inputs["Surface"])
    hb_target = nt_hb.nodes.new("ShaderNodeTexImage")
    for n in nt_hb.nodes:
        n.select = False
    hb_target.select = True
    nt_hb.nodes.active = hb_target
    head_low.data.materials.clear()
    head_low.data.materials.append(mat_hl_bake)

    # BAKE 1: Tangent-Space Normal Map
    hb_target.image = baked_face_normal
    bpy.ops.object.select_all(action="DESELECT")
    hd_bust_high.select_set(True)
    head_low.select_set(True)
    bpy.context.view_layer.objects.active = head_low
    bpy.ops.object.bake(
        type="NORMAL",
        normal_space="TANGENT",
        use_selected_to_active=True,
        cage_extrusion=0.0040,
        max_ray_distance=0.014,
        margin=8,
        use_clear=True,
    )
    baked_face_normal.pack()
    print("Baked Zachary_Face_Normal (768x768 tangent-space)")

    # BAKE 2: 100% Native 3D Pixar-Anime Albedo + Source-Locked Eye Crispness + Lower-Neck Skin Guard
    mat_hd_albedo_src = build_hd_face_albedo_bake_shader(hd_bust_high, hd_bust_clean, concept_img, lm, skin_srgb)
    hd_bust_high.data.materials.clear()
    hd_bust_high.data.materials.append(mat_hd_albedo_src)

    hb_target.image = baked_face_albedo
    bpy.ops.object.select_all(action="DESELECT")
    hd_bust_high.select_set(True)
    head_low.select_set(True)
    bpy.context.view_layer.objects.active = head_low
    bpy.ops.object.bake(
        type="EMIT",
        use_selected_to_active=True,
        cage_extrusion=0.0040,
        max_ray_distance=0.014,
        margin=8,
        use_clear=True,
    )

    fw_img, fh_img = baked_face_albedo.size
    fpx = np.array(baked_face_albedo.pixels[:], dtype=np.float32).reshape((fh_img, fw_img, 4))
    frgb = fpx[:, :, :3].copy()
    for _ in range(8):
        fluma = 0.299 * frgb[:, :, 0] + 0.587 * frgb[:, :, 1] + 0.114 * frgb[:, :, 2]
        fmiss = fluma < 1e-4
        if not np.any(fmiss):
            break
        valid_fm = (~fmiss).astype(np.float32)[:, :, None]
        blur_num = box_blur_2d(frgb * valid_fm, radius=3, passes=1)
        blur_den = box_blur_2d(valid_fm, radius=3, passes=1)
        fhealed = np.where(blur_den > 1e-3, blur_num / np.maximum(blur_den, 1e-3), frgb)
        frgb = np.where(fmiss[:, :, None] & (blur_den > 1e-3), fhealed, frgb)

    # Mesh-topology isolated 1-triangle face speck heal (zero impact on irises/lashes/brows/hair!)
    bm_heal = bmesh.new()
    bm_heal.from_mesh(head_low.data)
    bm_heal.faces.ensure_lookup_table()
    uv_lay_heal = bm_heal.loops.layers.uv.active
    n_f = len(bm_heal.faces)
    f_rgb = np.zeros((n_f, 3), dtype=np.float32)
    f_lum = np.zeros(n_f, dtype=np.float32)
    if uv_lay_heal is not None:
        for f in bm_heal.faces:
            uc = sum(lp[uv_lay_heal].uv.x for lp in f.loops) / float(len(f.loops))
            vc = sum(lp[uv_lay_heal].uv.y for lp in f.loops) / float(len(f.loops))
            ix = min(max(int((uc % 1.0) * (fw_img - 1)), 0), fw_img - 1)
            iy = min(max(int((vc % 1.0) * (fh_img - 1)), 0), fh_img - 1)
            col = frgb[iy, ix]
            f_rgb[f.index] = col
            f_lum[f.index] = float(0.299 * col[0] + 0.587 * col[1] + 0.114 * col[2])

        eye_z_lim = float(lm["eye_z"]) + 0.015
        healed_tris = 0
        for f in bm_heal.faces:
            if f_lum[f.index] >= 0.36:
                continue
            fc = f.calc_center_median()
            if f.normal.y >= -0.20 or abs(fc.x) >= 0.068 or fc.z >= eye_z_lim:
                continue
            adj_faces = [lf for e in f.edges for lf in e.link_faces if lf != f]
            skin_nbrs = [
                nf for nf in adj_faces
                if f_lum[nf.index] > 0.45 and (f_rgb[nf.index][0] - f_rgb[nf.index][2]) > 0.04
            ]
            dark_nbrs = [nf for nf in adj_faces if f_lum[nf.index] < 0.34]
            if len(skin_nbrs) >= 2 and len(dark_nbrs) == 0:
                avg_skin = np.mean([f_rgb[nf.index] for nf in skin_nbrs], axis=0)
                us = [lp[uv_lay_heal].uv.x for lp in f.loops]
                vs = [lp[uv_lay_heal].uv.y for lp in f.loops]
                u0 = max(0, int(min(us) * (fw_img - 1)) - 2)
                u1 = min(fw_img, int(max(us) * (fw_img - 1)) + 3)
                v0 = max(0, int(min(vs) * (fh_img - 1)) - 2)
                v1 = min(fh_img, int(max(vs) * (fh_img - 1)) + 3)
                patch = frgb[v0:v1, u0:u1]
                pluma = 0.299 * patch[:, :, 0] + 0.587 * patch[:, :, 1] + 0.114 * patch[:, :, 2]
                mask_p = pluma < 0.38
                if np.any(mask_p):
                    patch[mask_p] = avg_skin
                    healed_tris += 1

        # Generalized 2-pass front/side neck cluster heal against collar bleed smudges
        neck_cut_z = float(lm["chin_z"]) + 0.008
        healed_neck_clusters = 0
        for _ in range(2):
            for f in bm_heal.faces:
                if f_lum[f.index] >= 0.42:
                    continue
                fc = f.calc_center_median()
                if fc.z >= neck_cut_z or fc.y >= 0.022 or f.normal.y >= 0.30 or abs(fc.x) >= 0.062:
                    continue
                adj_faces = [lf for e in f.edges for lf in e.link_faces if lf != f]
                skin_nbrs = [
                    nf for nf in adj_faces
                    if f_lum[nf.index] > 0.44 and (f_rgb[nf.index][0] - f_rgb[nf.index][2]) > 0.03
                ]
                if skin_nbrs:
                    avg_skin = np.mean([f_rgb[nf.index] for nf in skin_nbrs], axis=0)
                    us = [lp[uv_lay_heal].uv.x for lp in f.loops]
                    vs = [lp[uv_lay_heal].uv.y for lp in f.loops]
                    u0 = max(0, int(min(us) * (fw_img - 1)) - 2)
                    u1 = min(fw_img, int(max(us) * (fw_img - 1)) + 3)
                    v0 = max(0, int(min(vs) * (fh_img - 1)) - 2)
                    v1 = min(fh_img, int(max(vs) * (fh_img - 1)) + 3)
                    patch = frgb[v0:v1, u0:u1]
                    pluma = 0.299 * patch[:, :, 0] + 0.587 * patch[:, :, 1] + 0.114 * patch[:, :, 2]
                    mask_p = pluma < 0.44
                    if np.any(mask_p):
                        patch[mask_p] = avg_skin
                        f_rgb[f.index] = avg_skin
                        f_lum[f.index] = float(0.299 * avg_skin[0] + 0.587 * avg_skin[1] + 0.114 * avg_skin[2])
                        healed_neck_clusters += 1
        print(f"Healed {healed_tris} isolated face specks and {healed_neck_clusters} front/side neck cluster patches on head_low")
    bm_heal.free()

    fpx[:, :, :3] = frgb
    baked_face_albedo.pixels.foreach_set(np.ascontiguousarray(fpx.ravel(), dtype=np.float32))
    baked_face_albedo.pack()
    print("Baked Zachary_Face_HD (1024x1024 native 3D Pixar-Anime albedo)")

    # BAKE 3: Anatomical Pixar-Anime Roughness Map
    mat_hd_mr_src = build_hd_face_mr_bake_shader(hd_bust_high, hd_bust_clean, lm)
    hd_bust_high.data.materials.clear()
    hd_bust_high.data.materials.append(mat_hd_mr_src)

    hb_target.image = baked_face_mr
    bpy.ops.object.select_all(action="DESELECT")
    hd_bust_high.select_set(True)
    head_low.select_set(True)
    bpy.context.view_layer.objects.active = head_low
    bpy.ops.object.bake(
        type="EMIT",
        use_selected_to_active=True,
        cage_extrusion=0.0040,
        max_ray_distance=0.014,
        margin=8,
        use_clear=True,
    )
    baked_face_mr.pack()
    print("Baked Zachary_Face_MR (512x512 Pixar-Anime roughness: 0.06 eyes / 0.36 lips / 0.70 hair / 0.54 skin)")

    mat_face = bpy.data.materials.new("Mat_Companion_Face")
    mat_face.use_nodes = True
    nt_f = mat_face.node_tree
    nt_f.nodes.clear()
    out_f = nt_f.nodes.new("ShaderNodeOutputMaterial")
    bsdf_f = nt_f.nodes.new("ShaderNodeBsdfPrincipled")
    if "Specular IOR Level" in bsdf_f.inputs:
        bsdf_f.inputs["Specular IOR Level"].default_value = 0.22

    tex_alb = nt_f.nodes.new("ShaderNodeTexImage"); tex_alb.image = baked_face_albedo
    tex_mr = nt_f.nodes.new("ShaderNodeTexImage"); tex_mr.image = baked_face_mr
    sep_mr = nt_f.nodes.new("ShaderNodeSeparateColor")
    tex_nrm = nt_f.nodes.new("ShaderNodeTexImage"); tex_nrm.image = baked_face_normal
    nrm_map = nt_f.nodes.new("ShaderNodeNormalMap")
    nrm_map.inputs["Strength"].default_value = 0.52

    nt_f.links.new(tex_alb.outputs["Color"], bsdf_f.inputs["Base Color"])
    nt_f.links.new(tex_mr.outputs["Color"], sep_mr.inputs["Color"])
    nt_f.links.new(sep_mr.outputs["Green"], bsdf_f.inputs["Roughness"])
    nt_f.links.new(sep_mr.outputs["Blue"], bsdf_f.inputs["Metallic"])
    nt_f.links.new(tex_nrm.outputs["Color"], nrm_map.inputs["Color"])
    nt_f.links.new(nrm_map.outputs["Normal"], bsdf_f.inputs["Normal"])
    nt_f.links.new(bsdf_f.outputs["BSDF"], out_f.inputs["Surface"])

    head_low.data.materials.clear()
    head_low.data.materials.append(mat_face)

    for tmp_obj in (raw_body, hd_bust_high):
        m_ref = tmp_obj.data
        bpy.data.objects.remove(tmp_obj, do_unlink=True)
        bpy.data.meshes.remove(m_ref)
    for tmp_mat in (mat_hl_bake, mat_hd_albedo_src, mat_hd_mr_src):
        bpy.data.materials.remove(tmp_mat)
    for im in list(bpy.data.images):
        if im not in (baked_body_img, baked_face_albedo, baked_face_normal, baked_face_mr):
            if im.users == 0:
                bpy.data.images.remove(im)

    # Join body_rem (Slot 0: Mat_Companion_Body) + head_low (Slot 1: Mat_Companion_Face)
    bpy.ops.object.select_all(action="DESELECT")
    head_low.select_set(True)
    body_rem.select_set(True)
    bpy.context.view_layer.objects.active = body_rem
    bpy.ops.object.join()

    body = body_rem
    body.name = "SM_Companion_Body"
    body.data.name = "SM_Companion_Body_Mesh"
    assert len(body.data.materials) == 2, f"Expected 2 materials on SM_Companion_Body, got {[m.name for m in body.data.materials]}"
    joined_tris = sum(max(1, len(p.vertices) - 2) for p in body.data.polygons)
    print(f"Joined SM_Companion_Body: verts={len(body.data.vertices)}, tris={joined_tris}, mats={[m.name for m in body.data.materials]}")
    return body


def build_hd_face_albedo_bake_shader(
    hd_obj: bpy.types.Object,
    hd_clean: bpy.types.Image,
    concept_img: bpy.types.Image,
    lm: dict[str, object],
    skin_srgb: np.ndarray,
) -> bpy.types.Material:
    """
    Combines 360-degree native TRELLIS.2 Pixar-Anime Albedo with landmark-locked high-res eye
    crispness (`02_hd_bust_glasses_off.png`) strictly inside the two orbital eye ellipses (zero face sticker!),
    plus nostril shadow softening and the lower-neck skin guard.
    """
    mat = bpy.data.materials.new("Mat_HDBustAlbedoSrc")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    uv_orig = nt.nodes.new("ShaderNodeUVMap")
    uv_orig.uv_map = hd_obj.data.uv_layers.active.name
    tex_bust = nt.nodes.new("ShaderNodeTexImage")
    tex_bust.image = hd_clean
    nt.links.new(uv_orig.outputs["UV"], tex_bust.inputs["Vector"])

    tc = nt.nodes.new("ShaderNodeTexCoord")
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep_co = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep_co.inputs["Vector"])
    nt.links.new(geom.outputs["Normal"], sep_n.inputs["Vector"])

    def math_op(op, a, b):
        m = nt.nodes.new("ShaderNodeMath"); m.operation = op
        if isinstance(a, (int, float)): m.inputs[0].default_value = a
        else: nt.links.new(a, m.inputs[0])
        if isinstance(b, (int, float)): m.inputs[1].default_value = b
        else: nt.links.new(b, m.inputs[1])
        return m.outputs["Value"]

    def map_range(val, f0, f1, t0, t1):
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        mr.clamp = True
        mr.inputs[1].default_value = f0
        mr.inputs[2].default_value = f1
        mr.inputs[3].default_value = t0
        mr.inputs[4].default_value = t1
        nt.links.new(val, mr.inputs[0])
        return mr.outputs["Result"]

    nose_x = float(lm["nose_x"])
    nose_tip_z = float(lm["nose_tip_z"])
    eye_front_y = float(lm["eye_front_y"])
    eye_z = float(lm["eye_z"])
    eye_dx = float(lm["eye_dx"])

    # Landmark-locked orthographic UV projection onto originating concept portrait `02_hd_bust_glasses_off.png`
    u_mid = 0.49854
    v_mid = 0.58398
    ipd_uv = 0.16113
    uv_scale = ipd_uv / max(1e-4, 2.0 * eye_dx)

    dx_n = math_op("SUBTRACT", sep_co.outputs["X"], nose_x)
    abs_dx_e = math_op("ABSOLUTE", dx_n, 0.0)
    u_eye = math_op("ADD", u_mid, math_op("MULTIPLY", dx_n, uv_scale))
    v_eye = math_op("ADD", v_mid, math_op("MULTIPLY", math_op("SUBTRACT", sep_co.outputs["Z"], eye_z - 0.0008), uv_scale))
    comb_eye_uv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u_eye, comb_eye_uv.inputs["X"])
    nt.links.new(v_eye, comb_eye_uv.inputs["Y"])

    tex_concept = nt.nodes.new("ShaderNodeTexImage")
    tex_concept.image = concept_img
    tex_concept.extension = "EXTEND"
    nt.links.new(comb_eye_uv.outputs["Vector"], tex_concept.inputs["Vector"])

    # Strict dual-eye orbital ellipse mask (irises, pupils, catchlights, sclera & upper lashes ONLY!)
    ex_n = math_op("DIVIDE", math_op("SUBTRACT", abs_dx_e, eye_dx), 0.0155)
    ez_n = math_op("DIVIDE", math_op("SUBTRACT", sep_co.outputs["Z"], eye_z - 0.0004), 0.0085)
    e_r2 = math_op("ADD", math_op("MULTIPLY", ex_n, ex_n), math_op("MULTIPLY", ez_n, ez_n))
    w_eye_orb = map_range(e_r2, 1.00, 0.42, 0.0, 1.0)
    w_eye_y = map_range(sep_co.outputs["Y"], -0.064, -0.072, 0.0, 1.0)
    w_eye_ny = map_range(sep_n.outputs["Y"], -0.20, -0.45, 0.0, 1.0)
    w_eye_src = math_op("MULTIPLY", w_eye_orb, math_op("MULTIPLY", w_eye_y, w_eye_ny))

    mix_eye = nt.nodes.new("ShaderNodeMixRGB"); mix_eye.blend_type = "MIX"
    nt.links.new(w_eye_src, mix_eye.inputs["Factor"])
    nt.links.new(tex_bust.outputs["Color"], mix_eye.inputs["Color1"])
    nt.links.new(tex_concept.outputs["Color"], mix_eye.inputs["Color2"])

    bw_bust = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(mix_eye.outputs["Color"], bw_bust.inputs["Color"])

    # Soften harsh dark nostril-hole pixels strictly inside nostril box (covering Y=-0.078 nostril wings!)
    abs_dx_n = math_op("ABSOLUTE", math_op("SUBTRACT", sep_co.outputs["X"], nose_x), 0.0)
    nos_x = map_range(abs_dx_n, 0.015, 0.022, 1.0, 0.0)
    nos_z = math_op(
        "MULTIPLY",
        map_range(sep_co.outputs["Z"], nose_tip_z - 0.012, nose_tip_z - 0.008, 0.0, 1.0),
        map_range(sep_co.outputs["Z"], nose_tip_z + 0.004, nose_tip_z + 0.008, 1.0, 0.0),
    )
    nos_y = map_range(sep_co.outputs["Y"], eye_front_y + 0.012, eye_front_y + 0.002, 0.0, 1.0)
    nos_dark = map_range(bw_bust.outputs["Val"], 0.03, 0.16, 1.0, 0.0)
    w_nostril = math_op("MULTIPLY", math_op("MULTIPLY", nos_x, nos_z), math_op("MULTIPLY", nos_y, math_op("MULTIPLY", nos_dark, 0.82)))

    mix_nostril = nt.nodes.new("ShaderNodeMixRGB"); mix_nostril.blend_type = "MIX"
    nt.links.new(w_nostril, mix_nostril.inputs["Factor"])
    nt.links.new(mix_eye.outputs["Color"], mix_nostril.inputs["Color1"])
    lin_nos = srgb_to_linear((float(skin_srgb[0] * 0.64), float(skin_srgb[1] * 0.58), float(skin_srgb[2] * 0.55)))
    mix_nostril.inputs["Color2"].default_value = (lin_nos[0], lin_nos[1], lin_nos[2], 1.0)

    # Lower-neck skin blend on procedural neck skirt & splice seam (Z=1.310..1.350) with subtle collar AO
    neck_bot_w = map_range(sep_co.outputs["Z"], 1.310, 1.350, 1.0, 0.0)
    front_neck_y = map_range(sep_co.outputs["Y"], 0.034, 0.052, 1.0, 0.0)
    w_guard = math_op("MULTIPLY", neck_bot_w, front_neck_y)

    neck_ao_t = map_range(sep_co.outputs["Z"], 1.294, 1.326, 0.0, 1.0)
    mix_neck_tone = nt.nodes.new("ShaderNodeMixRGB"); mix_neck_tone.blend_type = "MIX"
    nt.links.new(neck_ao_t, mix_neck_tone.inputs["Factor"])
    lin_neck_lo = srgb_to_linear((float(skin_srgb[0] * 0.855), float(skin_srgb[1] * 0.825), float(skin_srgb[2] * 0.815)))
    lin_neck_hi = srgb_to_linear((float(skin_srgb[0] * 0.905), float(skin_srgb[1] * 0.880), float(skin_srgb[2] * 0.870)))
    mix_neck_tone.inputs["Color1"].default_value = (lin_neck_lo[0], lin_neck_lo[1], lin_neck_lo[2], 1.0)
    mix_neck_tone.inputs["Color2"].default_value = (lin_neck_hi[0], lin_neck_hi[1], lin_neck_hi[2], 1.0)

    mix_neck = nt.nodes.new("ShaderNodeMixRGB"); mix_neck.blend_type = "MIX"
    nt.links.new(w_guard, mix_neck.inputs["Factor"])
    nt.links.new(mix_nostril.outputs["Color"], mix_neck.inputs["Color1"])
    nt.links.new(mix_neck_tone.outputs["Color"], mix_neck.inputs["Color2"])

    # Warm espresso-brown hair grading using TARGET_HAIR_SRGB [0.155, 0.120, 0.102] (excluding ears/eyes/neck)
    w_dark_hair = map_range(bw_bust.outputs["Val"], 0.08, 0.22, 1.0, 0.0)
    w_hair_z = map_range(sep_co.outputs["Z"], eye_z + 0.010, eye_z + 0.026, 0.0, 1.0)
    w_hair_y = map_range(sep_co.outputs["Y"], -0.045, -0.015, 0.0, 1.0)
    w_ear_zone = math_op(
        "MULTIPLY",
        map_range(abs_dx_e, 0.054, 0.062, 0.0, 1.0),
        math_op(
            "MULTIPLY",
            map_range(sep_co.outputs["Z"], eye_z + 0.014, eye_z + 0.004, 0.0, 1.0),
            map_range(sep_co.outputs["Y"], 0.025, 0.012, 0.0, 1.0),
        ),
    )
    w_safe_mask = math_op(
        "MULTIPLY",
        math_op("MULTIPLY", math_op("SUBTRACT", 1.0, w_eye_src), math_op("SUBTRACT", 1.0, w_guard)),
        math_op("SUBTRACT", 1.0, w_ear_zone),
    )
    w_hair = math_op(
        "MULTIPLY",
        math_op("MULTIPLY", w_dark_hair, math_op("MAXIMUM", w_hair_z, w_hair_y)),
        math_op("MULTIPLY", w_safe_mask, 0.82),
    )

    hair_shade = map_range(bw_bust.outputs["Val"], 0.02, 0.20, 0.72, 1.24)
    lin_hair = srgb_to_linear((float(TARGET_HAIR_SRGB[0]), float(TARGET_HAIR_SRGB[1]), float(TARGET_HAIR_SRGB[2])))
    hair_const = nt.nodes.new("ShaderNodeRGB")
    hair_const.outputs["Color"].default_value = (lin_hair[0], lin_hair[1], lin_hair[2], 1.0)
    mix_hair_shade = nt.nodes.new("ShaderNodeMixRGB"); mix_hair_shade.blend_type = "MULTIPLY"
    mix_hair_shade.inputs["Factor"].default_value = 1.0
    nt.links.new(hair_const.outputs["Color"], mix_hair_shade.inputs["Color1"])
    comb_shade = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(hair_shade, comb_shade.inputs["X"])
    nt.links.new(hair_shade, comb_shade.inputs["Y"])
    nt.links.new(hair_shade, comb_shade.inputs["Z"])
    nt.links.new(comb_shade.outputs["Vector"], mix_hair_shade.inputs["Color2"])

    mix_hair = nt.nodes.new("ShaderNodeMixRGB"); mix_hair.blend_type = "MIX"
    nt.links.new(w_hair, mix_hair.inputs["Factor"])
    nt.links.new(mix_neck.outputs["Color"], mix_hair.inputs["Color1"])
    nt.links.new(mix_hair_shade.outputs["Color"], mix_hair.inputs["Color2"])

    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_hair.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def build_hd_face_mr_bake_shader(
    hd_obj: bpy.types.Object,
    hd_clean: bpy.types.Image,
    lm: dict[str, object],
) -> bpy.types.Material:
    """
    Outputs packed MetallicRoughness texture via EMIT: R=0, G=Roughness, B=0.0 (Metallic).
    - Pixar-Anime Eyes / Corneas: Roughness = 0.06 (alive glossy specular catchlights!)
    - Lips: Roughness = 0.36
    - Hair: Roughness = 0.70 (soft natural satin matte)
    - Skin: Roughness = 0.54 (creamy satin Pixar matte)
    - Eyebrows: Roughness = 0.68
    """
    mat = bpy.data.materials.new("Mat_HDBustMRSrc")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    uv_orig = nt.nodes.new("ShaderNodeUVMap")
    uv_orig.uv_map = hd_obj.data.uv_layers.active.name
    tex_bust = nt.nodes.new("ShaderNodeTexImage"); tex_bust.image = hd_clean
    nt.links.new(uv_orig.outputs["UV"], tex_bust.inputs["Vector"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(tex_bust.outputs["Color"], bw.inputs["Color"])

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep_co = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep_co.inputs["Vector"])

    nose_x = float(lm["nose_x"])
    eye_z = float(lm["eye_z"])
    eye_dx = float(lm["eye_dx"])
    mouth_z = float(lm["mouth_z"])

    def math_op(op, a, b):
        m = nt.nodes.new("ShaderNodeMath"); m.operation = op
        if isinstance(a, (int, float)): m.inputs[0].default_value = a
        else: nt.links.new(a, m.inputs[0])
        if isinstance(b, (int, float)): m.inputs[1].default_value = b
        else: nt.links.new(b, m.inputs[1])
        return m.outputs["Value"]

    def map_range(val, f0, f1, t0, t1):
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        mr.clamp = True
        mr.inputs[1].default_value = f0
        mr.inputs[2].default_value = f1
        mr.inputs[3].default_value = t0
        mr.inputs[4].default_value = t1
        nt.links.new(val, mr.inputs[0])
        return mr.outputs["Result"]

    def mix_float(fac, a, b):
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "FLOAT"
        nt.links.new(fac, mx.inputs[0])
        if isinstance(a, (int, float)): mx.inputs[2].default_value = a
        else: nt.links.new(a, mx.inputs[2])
        if isinstance(b, (int, float)): mx.inputs[3].default_value = b
        else: nt.links.new(b, mx.inputs[3])
        return mx.outputs[0]

    w_dark = map_range(bw.outputs["Val"], 0.08, 0.20, 1.0, 0.0)
    w_hair_z = map_range(sep_co.outputs["Z"], eye_z + 0.010, eye_z + 0.026, 0.0, 1.0)
    w_hair_y = map_range(sep_co.outputs["Y"], -0.045, -0.015, 0.0, 1.0)
    w_hair = math_op("MULTIPLY", w_dark, math_op("MAXIMUM", w_hair_z, w_hair_y))

    r_val = mix_float(w_hair, 0.54, 0.70)

    neg_py = math_op("MULTIPLY", sep_co.outputs["Y"], -1.0)
    w_front_y = map_range(neg_py, 0.052, 0.075, 0.0, 1.0)
    abs_dx = math_op("ABSOLUTE", math_op("SUBTRACT", sep_co.outputs["X"], nose_x), 0.0)

    w_brow_z = math_op("MULTIPLY", map_range(sep_co.outputs["Z"], eye_z + 0.011, eye_z + 0.017, 0.0, 1.0),
                                   map_range(sep_co.outputs["Z"], eye_z + 0.026, eye_z + 0.034, 1.0, 0.0))
    w_brow_x = math_op("MULTIPLY", map_range(abs_dx, 0.006, 0.014, 0.0, 1.0),
                                   map_range(abs_dx, 0.050, 0.064, 1.0, 0.0))
    w_brow = math_op("MULTIPLY", math_op("MULTIPLY", w_brow_z, w_brow_x), math_op("MULTIPLY", w_front_y, w_dark))
    r_val = mix_float(w_brow, r_val, 0.68)

    # Lips soft satin
    lx_n = math_op("DIVIDE", abs_dx, 0.022)
    lz_n = math_op("DIVIDE", math_op("SUBTRACT", sep_co.outputs["Z"], mouth_z), 0.009)
    l_r2 = math_op("ADD", math_op("MULTIPLY", lx_n, lx_n), math_op("MULTIPLY", lz_n, lz_n))
    w_lip = math_op("MULTIPLY", map_range(l_r2, 0.35, 1.0, 1.0, 0.0), w_front_y)
    r_val = mix_float(w_lip, r_val, 0.36)

    # Pixar-Anime eye globes (wider & taller iris catchlights!)
    ex_n = math_op("DIVIDE", math_op("SUBTRACT", abs_dx, eye_dx), 0.0165)
    ez_n = math_op("DIVIDE", math_op("SUBTRACT", sep_co.outputs["Z"], eye_z), 0.0085)
    e_r2 = math_op("ADD", math_op("MULTIPLY", ex_n, ex_n), math_op("MULTIPLY", ez_n, ez_n))
    w_eye_gloss = math_op("MULTIPLY", map_range(e_r2, 0.35, 1.0, 1.0, 0.0), w_front_y)
    r_val = mix_float(w_eye_gloss, r_val, 0.06)

    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value = 0.0
    nt.links.new(r_val, comb.inputs["Green"])
    comb.inputs["Blue"].default_value = 0.0

    emit = nt.nodes.new("ShaderNodeEmission"); emit.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(comb.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


# ==============================================================================
# STEP 3: FITTED BRUSHED-BRONZE ROUND-PANTO SPECTACLES (`SM_Companion_Glasses`)
# ==============================================================================
def make_pbr_mat(
    name: str,
    srgb_color: tuple[float, float, float],
    *,
    alpha: float = 1.0,
    metallic: float = 0.0,
    roughness: float = 0.5,
    coat_weight: float = 0.0,
    coat_roughness: float = 0.1,
    ior: float = 1.46,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    lin = srgb_to_linear(srgb_color)
    bsdf.inputs["Base Color"].default_value = (lin[0], lin[1], lin[2], alpha)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Alpha"].default_value = alpha
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat_weight
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = coat_roughness
    if alpha < 0.99 and hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    return mat


def append_bm(dst: bmesh.types.BMesh, src: bmesh.types.BMesh, *, location=(0.0, 0.0, 0.0), mat_idx: int = 0) -> None:
    loc_v = Vector(location)
    vmap = {sv: dst.verts.new(sv.co + loc_v) for sv in src.verts}
    for sf in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in sf.verts])
            nf.material_index = mat_idx
            nf.smooth = True
        except ValueError:
            pass


def sweep_tube(bm: bmesh.types.BMesh, pts: list[tuple[Vector, float]], segments: int = 10, mat_idx: int = 0) -> None:
    rings = []
    n = len(pts)
    for i, (p, rad) in enumerate(pts):
        if i == 0:
            tan = (pts[1][0] - p).normalized()
        elif i == n - 1:
            tan = (p - pts[i - 1][0]).normalized()
        else:
            tan = (pts[i + 1][0] - pts[i - 1][0]).normalized()
        up = Vector((0.0, 0.0, 1.0)) if abs(tan.z) < 0.9 else Vector((1.0, 0.0, 0.0))
        bx = tan.cross(up).normalized()
        by = tan.cross(bx).normalized()
        ring = []
        for s in range(segments):
            ang = (2.0 * math.pi * s) / segments
            ring.append(bm.verts.new(p + bx * (math.cos(ang) * rad) + by * (math.sin(ang) * rad)))
        rings.append(ring)

    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        for s in range(segments):
            sn = (s + 1) % segments
            f = bm.faces.new((r0[s], r0[sn], r1[sn], r1[s]))
            f.material_index = mat_idx
            f.smooth = True

    if rings:
        for cap, rev in ((rings[0], True), (rings[-1], False)):
            f = bm.faces.new(list(reversed(cap)) if rev else cap)
            f.material_index = mat_idx
            f.smooth = True


def panto_offset(theta: float, rx: float, rz_top: float, rz_bot: float) -> tuple[float, float]:
    """Modern thin-wire rounded-panto lens contour with gently softened upper brow bar."""
    st = math.sin(theta)
    ct = math.cos(theta)
    if st >= 0.0:
        rz = rz_top * (1.0 - 0.10 * (st ** 2))
        rx_mod = rx * (1.0 + 0.06 * st * (1.0 - st))
    else:
        rz = rz_bot * (1.0 - 0.03 * (st ** 4))
        rx_mod = rx * (1.0 - 0.03 * (abs(st) ** 1.8))
    return ct * rx_mod, st * rz


def build_fitted_glasses(lm: dict[str, object]) -> bpy.types.Object:
    mat_metal = make_pbr_mat(
        "Mat_Companion_GlassesMetal",
        (0.30, 0.25, 0.21),
        metallic=0.88,
        roughness=0.22,
        coat_weight=0.15,
        coat_roughness=0.08,
    )
    mat_lens = make_pbr_mat(
        "Mat_Companion_GlassesLens",
        (0.96, 0.98, 1.0),
        alpha=0.018,
        metallic=0.0,
        roughness=0.04,
        coat_weight=0.04,
        coat_roughness=0.05,
        ior=1.08,
    )
    if "Specular IOR Level" in mat_lens.node_tree.nodes["Principled BSDF"].inputs:
        mat_lens.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.08
    mat_pad = make_pbr_mat(
        "Mat_Companion_GlassesPad",
        (0.14, 0.14, 0.15),
        metallic=0.0,
        roughness=0.55,
    )

    nose_x = float(lm["nose_x"])
    eye_z = float(lm["eye_z"]) - 0.0010
    eye_dx = float(lm["eye_dx"]) * 1.04
    bridge_y = float(lm["bridge_y"])
    eye_front_y = float(lm["eye_front_y"])
    ear_y = float(lm["ear_top_y"])

    # Anchor lens plane strictly ahead of BOTH sculpted eyeballs & nose bridge; wider/lower clear of brows
    lens_y = min(bridge_y - 0.0055, eye_front_y - 0.0095)
    rx = max(0.0268, eye_dx * 0.87)
    rz_top = rx * 0.69
    rz_bot = rx * 0.88
    wire_r = 0.00084

    t_ys = list(lm["temple_profile_y"])
    t_xs = list(lm["temple_profile_x"])

    def _temple_x_at(yq: float, min_x: float) -> float:
        return max(min_x, float(np.interp(yq, t_ys, t_xs)))

    wire_r_temple = 0.00098
    bm = bmesh.new()
    rim_segs = 44
    tube_segs = 10

    for sx in (-1.0, 1.0):
        cx = nose_x + sx * eye_dx
        rim_rings: list[list[bmesh.types.BMVert]] = []
        for s in range(rim_segs):
            th = (2.0 * math.pi * s) / rim_segs
            ox, oz = panto_offset(th, rx, rz_top, rz_bot)
            wrap_y = 0.0024 * max(0.0, (sx * ox) / rx) ** 2
            ring_c = Vector((cx + ox, lens_y + wrap_y, eye_z + oz))
            rad_dir = Vector((ox, 0.0, oz)).normalized()
            fwd_dir = Vector((0.0, -1.0, 0.0))
            ring = []
            for ts in range(tube_segs):
                a = (2.0 * math.pi * ts) / tube_segs
                pt = ring_c + rad_dir * (math.cos(a) * wire_r) + fwd_dir * (math.sin(a) * wire_r * 1.15)
                ring.append(bm.verts.new(pt))
            rim_rings.append(ring)

        for s in range(rim_segs):
            sn = (s + 1) % rim_segs
            for ts in range(tube_segs):
                tsn = (ts + 1) % tube_segs
                f = bm.faces.new((rim_rings[s][ts], rim_rings[sn][ts], rim_rings[sn][tsn], rim_rings[s][tsn]))
                f.material_index = 0
                f.smooth = True

        # Optical lens disc
        lring = []
        for s in range(rim_segs):
            th = (2.0 * math.pi * s) / rim_segs
            ox, oz = panto_offset(th, rx - 0.0005, rz_top - 0.0005, rz_bot - 0.0005)
            wrap_y = 0.0024 * max(0.0, (sx * ox) / rx) ** 2
            lring.append(bm.verts.new((cx + ox, lens_y + wrap_y, eye_z + oz)))
        fl = bm.faces.new(list(reversed(lring)))
        fl.material_index = 1
        fl.smooth = True

        # Nose pad wires & pads kissing bridge
        inner_rim_x = cx - sx * (rx - 0.0018)
        pad_pts = [
            (Vector((inner_rim_x, lens_y + 0.0012, eye_z + 0.0020)), 0.00062),
            (Vector((nose_x + sx * 0.0080, bridge_y + 0.0012, eye_z - 0.0006)), 0.00062),
        ]
        sweep_tube(bm, pad_pts, segments=6, mat_idx=0)
        pbm = bmesh.new()
        bmesh.ops.create_cube(pbm, size=1.0)
        bmesh.ops.subdivide_edges(pbm, edges=list(pbm.edges), cuts=2, use_grid_fill=True)
        for pv in pbm.verts:
            q = pv.co.normalized()
            pv.co = Vector((q.x * 0.0010, q.y * 0.0016, q.z * 0.0034))
        append_bm(
            bm,
            pbm,
            location=(nose_x + sx * 0.0080, bridge_y + 0.0014, eye_z - 0.0010),
            mat_idx=2,
        )
        pbm.free()

        # Contour-hugging temple arms interpolated cleanly over the ears
        outer_x = cx + sx * (rx + 0.0002)
        temple_z = eye_z + 0.0042
        x_endpiece = abs(outer_x - nose_x)
        y_span_0 = lens_y + 0.008
        y_span_1 = ear_y
        yq1 = y_span_0 + 0.25 * (y_span_1 - y_span_0)
        yq2 = y_span_0 + 0.50 * (y_span_1 - y_span_0)
        yq3 = y_span_0 + 0.75 * (y_span_1 - y_span_0)
        yq4 = y_span_1

        x_front = min(x_endpiece + 0.0022, _temple_x_at(y_span_0, x_endpiece + 0.0004))
        x_t1 = min(x_endpiece + 0.0018, _temple_x_at(yq1, x_endpiece - 0.0002))
        x_t2 = x_endpiece - 0.0004
        x_t3 = x_endpiece - 0.0012
        x_t4 = x_endpiece - 0.0020
        x_ear = x_endpiece - 0.0028

        wing_pts = [
            (Vector((outer_x, lens_y + 0.0024, temple_z)), 0.00105),
            (Vector((nose_x + sx * (x_endpiece + 0.0005), lens_y + 0.0038, temple_z)), 0.00102),
            (Vector((nose_x + sx * x_front, y_span_0, temple_z - 0.0002)), wire_r_temple),
            (Vector((nose_x + sx * x_t1, yq1, temple_z - 0.0004)), wire_r_temple),
            (Vector((nose_x + sx * x_t2, yq2, temple_z - 0.0007)), wire_r_temple),
            (Vector((nose_x + sx * x_t3, yq3, temple_z - 0.0011)), wire_r_temple),
            (Vector((nose_x + sx * x_t4, yq4 - 0.003, temple_z - 0.0020)), wire_r_temple),
            (Vector((nose_x + sx * x_ear, ear_y + 0.007, temple_z - 0.0046)), wire_r_temple),
            (Vector((nose_x + sx * (x_ear - 0.0032), ear_y + 0.019, temple_z - 0.0165)), 0.00102),
        ]
        sweep_tube(bm, wing_pts, segments=8, mat_idx=0)

    # Single arched center bridge connecting both rims (clean single-bridge Pixar-anime style)
    bridge_x0 = nose_x - (eye_dx - rx + 0.0004)
    bridge_x1 = nose_x + (eye_dx - rx + 0.0004)
    bridge_pts = []
    for k in range(7):
        t = k / 6.0
        bx = bridge_x0 + t * (bridge_x1 - bridge_x0)
        arch = math.sin(t * math.pi)
        bridge_pts.append((Vector((bx, lens_y - arch * 0.0010, eye_z + 0.0072 + arch * 0.0020)), 0.00090))
    sweep_tube(bm, bridge_pts, segments=8, mat_idx=0)

    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    gmesh = bpy.data.meshes.new("SM_Companion_Glasses")
    bm.to_mesh(gmesh)
    bm.free()
    for p in gmesh.polygons:
        p.use_smooth = True
    gmesh.update()

    gobj = bpy.data.objects.new("SM_Companion_Glasses", gmesh)
    gmesh.materials.append(mat_metal)
    gmesh.materials.append(mat_lens)
    gmesh.materials.append(mat_pad)
    bpy.context.scene.collection.objects.link(gobj)
    return gobj


# ==============================================================================
# STEP 4: CHECKPOINT 1 — 6-PANEL PIXAR-ANIME FACE & COLLAR VISUAL AUDIT
# ==============================================================================
def render_v4_face_checkpoint(body: bpy.types.Object, glasses_obj: bpy.types.Object, lm: dict[str, object]) -> None:
    scene = bpy.context.scene
    world = bpy.data.worlds.new("V4FaceCheckWorld")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.09, 0.10, 0.12, 1.0)
        bg.inputs["Strength"].default_value = 0.85

    eye_z = float(lm["eye_z"])
    tgt_z = eye_z - 0.025

    def add_area(name: str, loc: tuple[float, float, float], tgt: tuple[float, float, float], energy: float, size: float, color=(1.0, 1.0, 1.0)):
        ld = bpy.data.lights.new(name=name, type="AREA")
        ld.energy = energy
        ld.size = size
        ld.color = color
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        look_at(lo, Vector(tgt))
        scene.collection.objects.link(lo)

    add_area("Key", (0.85, -1.60, 1.80), (0.0, 0.0, tgt_z), 105.0, 1.1, (1.0, 0.96, 0.92))
    add_area("Fill", (-1.05, -1.50, 1.48), (0.0, 0.0, tgt_z), 52.0, 1.4, (0.86, 0.92, 1.0))
    add_area("Rim", (-0.50, 1.45, 1.85), (0.0, 0.0, tgt_z), 85.0, 1.2, (1.0, 0.88, 0.72))
    add_area("EyeCatch", (0.18, -1.45, eye_z + 0.08), (0.0, 0.0, eye_z), 14.0, 0.14, (1.0, 0.99, 0.97))

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 28
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"

    cam_d = bpy.data.cameras.new("FaceCheckCam")
    cam_d.lens = 78.0
    cam_o = bpy.data.objects.new("FaceCheckCam", cam_d)
    scene.collection.objects.link(cam_o)
    scene.camera = cam_o
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.image_settings.file_format = "PNG"

    clay_mat = bpy.data.materials.new("V4ClayInspect")
    clay_mat.use_nodes = True
    clay_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.56, 0.54, 0.52, 1.0)
    clay_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.54
    orig_mats = list(body.data.materials)

    panels: list[np.ndarray] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        def render_shot(label: str, use_clay: bool, show_glasses: bool, loc: tuple[float, float, float], tgt: tuple[float, float, float]) -> np.ndarray:
            for slot_i in range(len(orig_mats)):
                body.data.materials[slot_i] = clay_mat if use_clay else orig_mats[slot_i]
            glasses_obj.hide_render = not show_glasses
            cam_o.location = Vector(loc)
            look_at(cam_o, Vector(tgt))
            p = os.path.join(tmpdir, f"{label}.png")
            scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(p, check_existing=False)
            arr = np.empty(512 * 512 * 4, dtype=np.float32)
            im.pixels.foreach_get(arr)
            bpy.data.images.remove(im)
            return arr.reshape((512, 512, 4))

        tgt = (0.0, -0.02, tgt_z)
        panels.append(render_shot("1_clay_front", True, False, (0.0, -0.72, tgt_z + 0.02), tgt))
        panels.append(render_shot("2_clay_34", True, False, (-0.38, -0.60, tgt_z + 0.03), tgt))
        panels.append(render_shot("3_side_glasses", False, True, (-0.72, -0.04, tgt_z + 0.02), (0.0, 0.0, tgt_z)))
        panels.append(render_shot("4_front_bare", False, False, (0.0, -0.72, tgt_z + 0.02), tgt))
        panels.append(render_shot("5_front_glasses", False, True, (0.0, -0.78, tgt_z + 0.01), (0.0, -0.02, tgt_z - 0.02)))
        panels.append(render_shot("6_34_glasses", False, True, (-0.40, -0.68, tgt_z + 0.02), (0.0, -0.02, tgt_z - 0.02)))

    for slot_i in range(len(orig_mats)):
        body.data.materials[slot_i] = orig_mats[slot_i]
    glasses_obj.hide_render = False

    sheet = np.zeros((1024, 1536, 4), dtype=np.float32)
    for i in range(3):
        sheet[512:1024, i * 512 : (i + 1) * 512] = panels[i]
        sheet[0:512, i * 512 : (i + 1) * 512] = panels[3 + i]

    os.makedirs(os.path.dirname(FACE_CHECK_PNG), exist_ok=True)
    out_im = bpy.data.images.new("V4FaceCheckSheet", width=1536, height=1024, alpha=True)
    out_im.pixels.foreach_set(sheet.ravel())
    out_im.filepath_raw = FACE_CHECK_PNG
    out_im.file_format = "PNG"
    out_im.save()
    bpy.data.images.remove(out_im)
    print(f"Saved v4 Pixar-Anime checkpoint sheet: {FACE_CHECK_PNG}")


# ==============================================================================
# STEP 5: 19-BONE RIG, DETERMINISTIC SKINNING & 4 SLOTTED NLA CLIPS
# ==============================================================================
def measure_skeleton_landmarks(body: bpy.types.Object) -> dict[str, Vector | float]:
    pts = np.array([list(v.co) for v in body.data.vertices], dtype=np.float64)

    def slice_med(cond, fallback):
        sub = pts[cond]
        if len(sub) < 4:
            return Vector(fallback)
        return Vector((float(np.median(sub[:, 0])), float(np.median(sub[:, 1])), float(np.median(sub[:, 2]))))

    def arm_chain(sx: float):
        sh = slice_med((np.abs(pts[:, 0] - sx * 0.18) < 0.020) & (pts[:, 2] > 1.08) & (pts[:, 2] < 1.32), (sx * 0.18, 0.04, 1.18))
        el = slice_med((np.abs(pts[:, 0] - sx * 0.33) < 0.020) & (pts[:, 2] > 0.90) & (pts[:, 2] < 1.18), (sx * 0.33, 0.02, 1.03))
        wr = slice_med((np.abs(pts[:, 0] - sx * 0.45) < 0.020) & (pts[:, 2] > 0.78) & (pts[:, 2] < 1.04), (sx * 0.45, -0.01, 0.89))
        hd_tip = slice_med((np.abs(pts[:, 0] - sx * 0.51) < 0.020) & (pts[:, 2] > 0.72) & (pts[:, 2] < 0.92), (sx * 0.52, -0.04, 0.80))
        return sh, el, wr, hd_tip

    def leg_chain(sx: float):
        hip = Vector((sx * 0.095, 0.010, 0.785))
        knee = slice_med((np.abs(pts[:, 2] - 0.43) < 0.022) & (pts[:, 0] * sx > 0.02), (sx * 0.108, 0.030, 0.43))
        ankle = slice_med((np.abs(pts[:, 2] - 0.10) < 0.020) & (pts[:, 0] * sx > 0.02), (sx * 0.112, 0.032, 0.10))
        return hip, knee, ankle

    l_sh, l_el, l_wr, l_tip = arm_chain(1.0)
    r_sh, r_el, r_wr, r_tip = arm_chain(-1.0)
    l_hip, l_knee, l_ank = leg_chain(1.0)
    r_hip, r_knee, r_ank = leg_chain(-1.0)

    arm_vec = l_el - l_sh
    bind_drop_deg = math.degrees(math.atan2(max(0.01, -arm_vec.z), max(0.01, abs(arm_vec.x))))

    return {
        "l_sh": l_sh, "l_el": l_el, "l_wr": l_wr, "l_tip": l_tip,
        "r_sh": r_sh, "r_el": r_el, "r_wr": r_wr, "r_tip": r_tip,
        "l_hip": l_hip, "l_knee": l_knee, "l_ank": l_ank,
        "r_hip": r_hip, "r_knee": r_knee, "r_ank": r_ank,
        "bind_drop_deg": bind_drop_deg,
    }


def build_armature(sk: dict[str, Vector | float]) -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("CompanionRig")
    arm_obj = bpy.data.objects.new("CompanionArmature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)

    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def add_b(name: str, head: Vector | tuple, tail: Vector | tuple, parent=None, connected: bool = False):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.roll = 0.0
        if parent is not None:
            b.parent = parent
            b.use_connect = connected
        return b

    hips = add_b("Hips", (0.0, 0.01, 0.785), (0.0, 0.01, 0.915))
    spine = add_b("Spine", (0.0, 0.01, 0.915), (0.0, 0.01, 1.075), hips, connected=True)
    spine1 = add_b("Spine1", (0.0, 0.01, 1.075), (0.0, 0.01, 1.255), spine, connected=True)
    neck = add_b("Neck", (0.0, 0.01, 1.255), (0.0, 0.005, 1.350), spine1, connected=True)
    add_b("Head", (0.0, 0.005, 1.350), (0.0, 0.00, 1.585), neck, connected=True)

    for side, sx, key in (("Left", 1.0, "l"), ("Right", -1.0, "r")):
        sh_p, el_p, wr_p, tip_p = sk[f"{key}_sh"], sk[f"{key}_el"], sk[f"{key}_wr"], sk[f"{key}_tip"]
        sh_b = add_b(f"{side}Shoulder", (sx * 0.048, 0.015, 1.215), sh_p, spine1)
        arm_b = add_b(f"{side}Arm", sh_p, el_p, sh_b, connected=True)
        fore_b = add_b(f"{side}ForeArm", el_p, wr_p, arm_b, connected=True)
        add_b(f"{side}Hand", wr_p, tip_p, fore_b, connected=True)

        hip_p, knee_p, ank_p = sk[f"{key}_hip"], sk[f"{key}_knee"], sk[f"{key}_ank"]
        up_b = add_b(f"{side}UpLeg", hip_p, knee_p, hips)
        leg_b = add_b(f"{side}Leg", knee_p, ank_p, up_b, connected=True)
        add_b(f"{side}Foot", ank_p, (ank_p.x, ank_p.y - 0.11, 0.02), leg_b, connected=True)

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def point_seg_dist(p: Vector, a: Vector, b: Vector) -> float:
    ab = b - a
    denom = ab.length_squared
    if denom < 1e-8:
        return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / denom))
    return (p - (a + ab * t)).length


def assign_body_weights_and_facial_lock(
    body: bpy.types.Object, arm_obj: bpy.types.Object, sk: dict[str, Vector | float]
) -> None:
    if body.parent != arm_obj:
        body.parent = arm_obj
    for mod in list(body.modifiers):
        if mod.type == "ARMATURE":
            body.modifiers.remove(mod)
    mod = body.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    mod.use_vertex_groups = True

    body.vertex_groups.clear()
    vg_map = {b.name: body.vertex_groups.new(name=b.name) for b in arm_obj.data.bones}

    l_sh, l_el, l_wr, l_tip = sk["l_sh"], sk["l_el"], sk["l_wr"], sk["l_tip"]
    r_sh, r_el, r_wr, r_tip = sk["r_sh"], sk["r_el"], sk["r_wr"], sk["r_tip"]
    l_knee, l_ank = sk["l_knee"], sk["l_ank"]
    r_knee, r_ank = sk["r_knee"], sk["r_ank"]

    def arm_weights(co: Vector, side: str) -> dict[str, float]:
        sh, el, wr, tip = (l_sh, l_el, l_wr, l_tip) if side == "Left" else (r_sh, r_el, r_wr, r_tip)
        sh_in = Vector(((1.0 if side == "Left" else -1.0) * 0.048, 0.015, 1.215))
        d_sh = (el - sh).normalized()
        u_arm = (co - sh).dot(d_sh) / max(1e-4, (el - sh).length)
        d_fore = (wr - el).normalized()
        u_fore = (co - el).dot(d_fore) / max(1e-4, (wr - el).length)
        d_hand = (tip - wr).normalized()
        u_hand = (co - wr).dot(d_hand)

        if co.x * (1.0 if side == "Left" else -1.0) < abs(sh.x) - 0.01:
            t_sh = smoothstep(abs(sh_in.x), abs(sh.x), abs(co.x))
            return {"Spine1": 1.0 - t_sh * 0.65, f"{side}Shoulder": t_sh * 0.65}
        if u_arm < 0.10:
            t = smoothstep(-0.18, 0.14, u_arm)
            return {f"{side}Shoulder": 1.0 - t, f"{side}Arm": t}
        if u_arm < 0.86:
            return {f"{side}Arm": 1.0}
        if u_fore < 0.18:
            t = smoothstep(-0.22, 0.18, u_fore)
            return {f"{side}Arm": 1.0 - t, f"{side}ForeArm": t}
        if u_hand < -0.015:
            return {f"{side}ForeArm": 1.0}
        t_h = smoothstep(-0.015, 0.015, u_hand)
        return {f"{side}ForeArm": 1.0 - t_h, f"{side}Hand": t_h}

    def torso_weights(co: Vector) -> dict[str, float]:
        z = co.z
        if z >= 1.365:
            return {"Head": 1.0}
        if z >= 1.330:
            t = smoothstep(1.330, 1.365, z)
            return {"Neck": 1.0 - t, "Head": t}
        if z >= 1.255:
            t = smoothstep(1.255, 1.330, z)
            return {"Spine1": 1.0 - t, "Neck": t}
        if z >= 1.075:
            return {"Spine1": 1.0}
        if z >= 0.915:
            t = smoothstep(0.955, 1.075, z)
            return {"Spine": 1.0 - t, "Spine1": t}
        t = smoothstep(0.790, 0.915, z)
        return {"Hips": 1.0 - t, "Spine": t}

    def leg_weights(co: Vector) -> dict[str, float]:
        z = co.z
        if z >= 0.785:
            return {"Hips": 1.0}
        t_r = 0.0 if co.x >= 0.0 else 1.0
        if z > 0.640 and abs(co.x) < 0.025:
            t_r = smoothstep(0.025, -0.025, co.x)
        t_l = 1.0 - t_r
        knee_z = 0.5 * (l_knee.z + r_knee.z)
        ank_z = 0.5 * (l_ank.z + r_ank.z)

        out: dict[str, float] = {}
        for side, w_side in (("Left", t_l), ("Right", t_r)):
            if w_side <= 1e-4:
                continue
            if z >= 0.700:
                t_up = smoothstep(0.785, 0.700, z)
                out["Hips"] = out.get("Hips", 0.0) + (1.0 - t_up) * w_side
                out[f"{side}UpLeg"] = out.get(f"{side}UpLeg", 0.0) + t_up * w_side
            elif z >= knee_z + 0.050:
                out[f"{side}UpLeg"] = out.get(f"{side}UpLeg", 0.0) + w_side
            elif z >= knee_z - 0.050:
                t_kn = smoothstep(knee_z + 0.050, knee_z - 0.050, z)
                out[f"{side}UpLeg"] = out.get(f"{side}UpLeg", 0.0) + (1.0 - t_kn) * w_side
                out[f"{side}Leg"] = out.get(f"{side}Leg", 0.0) + t_kn * w_side
            elif z >= ank_z + 0.025:
                out[f"{side}Leg"] = out.get(f"{side}Leg", 0.0) + w_side
            elif z >= ank_z - 0.025:
                t_ft = smoothstep(ank_z + 0.025, ank_z - 0.025, z)
                out[f"{side}Leg"] = out.get(f"{side}Leg", 0.0) + (1.0 - t_ft) * w_side
                out[f"{side}Foot"] = out.get(f"{side}Foot", 0.0) + t_ft * w_side
            else:
                out[f"{side}Foot"] = out.get(f"{side}Foot", 0.0) + w_side
        return out

    locked_head = 0
    for v in body.data.vertices:
        co = v.co
        if co.z >= 1.365:
            vg_map["Head"].add([v.index], 1.0, "REPLACE")
            locked_head += 1
            continue

        d_arm_l = min(point_seg_dist(co, l_sh, l_el), point_seg_dist(co, l_el, l_wr), point_seg_dist(co, l_wr, l_tip))
        d_arm_r = min(point_seg_dist(co, r_sh, r_el), point_seg_dist(co, r_el, r_wr), point_seg_dist(co, r_wr, r_tip))
        d_arm = min(d_arm_l, d_arm_r)

        if co.z >= 0.550 and abs(co.x) > 0.225:
            merged = arm_weights(co, "Left" if co.x > 0.0 else "Right")
        elif co.z >= 0.680 and abs(co.x) > 0.155 and d_arm < 0.155:
            side = "Left" if d_arm_l <= d_arm_r else "Right"
            w_limb = smoothstep(0.155, 0.225, abs(co.x)) * smoothstep(0.155, 0.085, d_arm)
            t_w = torso_weights(co) if co.z >= 0.785 else leg_weights(co)
            a_w = arm_weights(co, side)
            merged: dict[str, float] = {}
            for k, w in t_w.items():
                merged[k] = merged.get(k, 0.0) + w * (1.0 - w_limb)
            for k, w in a_w.items():
                merged[k] = merged.get(k, 0.0) + w * w_limb
        elif co.z >= 0.785:
            merged = torso_weights(co)
        else:
            merged = leg_weights(co)

        total = sum(max(0.0, w) for w in merged.values())
        if total <= 1e-6:
            merged = {"Hips": 1.0}
            total = 1.0
        for bn, w in merged.items():
            nw = max(0.0, w) / total
            if nw > 1e-4:
                vg_map[bn].add([v.index], nw, "REPLACE")

    print(f"Skinning complete: verts={len(body.data.vertices)}, locked_head={locked_head}")


def bind_glasses_rigidly(glasses_obj: bpy.types.Object, arm_obj: bpy.types.Object) -> None:
    vg = glasses_obj.vertex_groups.new(name="Head")
    vg.add([v.index for v in glasses_obj.data.vertices], 1.0, "REPLACE")
    glasses_obj.parent = arm_obj
    mod = glasses_obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    mod.use_vertex_groups = True


def create_slotted_nla_action(arm_obj: bpy.types.Object, name: str, frame_end: int, keyframe_fn) -> None:
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    act = bpy.data.actions.new(name)
    slot = act.slots.new(id_type="OBJECT", name=arm_obj.name)
    arm_obj.animation_data.action = act
    arm_obj.animation_data.action_slot = slot
    keyframe_fn(arm_obj, frame_end)

    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot)
            if cb:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "BEZIER"
                        kp.handle_left_type = "AUTO_CLAMPED"
                        kp.handle_right_type = "AUTO_CLAMPED"

    track = arm_obj.animation_data.nla_tracks.new()
    track.name = name
    nla_strip = track.strips.new(name, 1, act)
    nla_strip.action_frame_start = 1.0
    nla_strip.action_frame_end = float(frame_end)
    nla_strip.action_slot = slot
    nla_strip.use_auto_blend = False
    track.mute = True
    arm_obj.animation_data.action = None


def key_pose(arm_obj: bpy.types.Object, frame: int, world_rots_deg: dict[str, tuple[float, float, float]], hips_world_offset=(0.0, 0.0, 0.0)) -> None:
    bpy.context.scene.frame_set(frame)
    for b in arm_obj.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        b.location = (0.0, 0.0, 0.0)

    def apply_rec(pbone, parent_w: Matrix):
        w_euler = Euler(tuple(math.radians(a) for a in world_rots_deg.get(pbone.name, (0.0, 0.0, 0.0))), "XYZ").to_matrix()
        rest_loc = pbone.bone.matrix_local.to_3x3()
        rest_inv = pbone.parent.bone.matrix_local.to_3x3().inverted() if pbone.parent else Matrix.Identity(3)
        rel_rest = rest_inv @ rest_loc
        target_w = w_euler @ rest_loc
        local_rot = (parent_w @ rel_rest).inverted() @ target_w
        pbone.rotation_quaternion = local_rot.to_quaternion()
        pbone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if pbone.name == "Hips":
            pbone.location = Vector(hips_world_offset)
            pbone.keyframe_insert(data_path="location", frame=frame)
        cur_w = parent_w @ rel_rest @ local_rot
        for ch in pbone.children:
            apply_rec(ch, cur_w)

    for root in arm_obj.pose.bones:
        if root.parent is None:
            apply_rec(root, Matrix.Identity(3))


def author_animations(arm_obj: bpy.types.Object, bind_drop_deg: float) -> None:
    rest_drop = max(24.0, 74.0 - bind_drop_deg)

    def anim_idle(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 19, 37, 55, 73):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            br = math.sin(ph)
            sw = math.sin(ph * 0.5)
            rots = {
                "Hips": (0.0, 0.0, sw * 1.8),
                "Spine": (br * 1.4, 0.0, sw * 1.2),
                "Spine1": (br * 1.8, 0.0, -sw * 0.8),
                "Neck": (-br * 0.6, 0.0, -sw * 0.6),
                "Head": (1.8 - br * 0.8, -1.6 + sw * 0.9, 1.2),
                "LeftShoulder": (-br * 0.5, 4.0, 0.0),
                "LeftArm": (-2.0, rest_drop + br * 1.0, 1.5),
                "LeftForeArm": (-12.0, rest_drop - 6.0, 3.0),
                "LeftHand": (-9.0, rest_drop - 10.0, 4.0),
                "RightShoulder": (-br * 0.5, -4.0, 0.0),
                "RightArm": (-2.0, -(rest_drop + br * 1.0), -1.5),
                "RightForeArm": (-12.0, -(rest_drop - 6.0), -3.0),
                "RightHand": (-9.0, -(rest_drop - 10.0), -4.0),
                "LeftUpLeg": (-1.0, 1.0, 0.0),
                "LeftLeg": (2.0, 0.0, 0.0),
                "LeftFoot": (0.0, 0.0, 2.0),
                "RightUpLeg": (1.0, -0.5, 0.0),
                "RightLeg": (2.0, 0.0, 0.0),
                "RightFoot": (0.0, 0.0, -2.0),
            }
            key_pose(arm, f, rots, hips_world_offset=(0.002, 0.0, br * 0.003))

    create_slotted_nla_action(arm_obj, "Idle_Breathing", 73, anim_idle)

    def anim_walk(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 4, 7, 10, 13, 16, 19, 22, 25):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            s = math.sin(ph)
            c = math.cos(ph)
            bounce = math.cos(2.0 * ph)

            l_thigh_x = -s * 22.0
            r_thigh_x = s * 22.0
            l_knee_flex = max(4.0, 36.0 * math.sin(ph + 0.55) if math.sin(ph + 0.55) > 0 else 5.0)
            r_knee_flex = max(4.0, 36.0 * math.sin(ph + math.pi + 0.55) if math.sin(ph + math.pi + 0.55) > 0 else 5.0)
            l_shin_x = l_thigh_x + l_knee_flex
            r_shin_x = r_thigh_x + r_knee_flex
            l_foot_x = l_thigh_x * 0.25 + c * 8.0
            r_foot_x = r_thigh_x * 0.25 - c * 8.0

            l_arm_x = s * 17.0 - 2.0
            r_arm_x = -s * 17.0 - 2.0
            walk_drop = max(12.0, rest_drop - 2.0)

            rots = {
                "Hips": (-2.0, c * 1.6, -s * 4.2),
                "Spine": (-2.0, -c * 1.0, -s * 1.8),
                "Spine1": (-2.5, -c * 1.2, s * 4.0),
                "Neck": (0.0, 0.0, s * 1.4),
                "Head": (2.0, 0.0, s * 1.4),
                "LeftShoulder": (0.0, 3.0, s * 2.0),
                "LeftArm": (l_arm_x, walk_drop, 0.0),
                "LeftForeArm": (l_arm_x - 18.0 - max(0.0, -s) * 8.0, walk_drop - 5.0, 3.0),
                "LeftHand": (l_arm_x - 16.0, walk_drop - 9.0, 4.0),
                "RightShoulder": (0.0, -3.0, s * 2.0),
                "RightArm": (r_arm_x, -walk_drop, 0.0),
                "RightForeArm": (r_arm_x - 18.0 - max(0.0, s) * 8.0, -(walk_drop - 5.0), -3.0),
                "RightHand": (r_arm_x - 16.0, -(walk_drop - 9.0), -4.0),
                "LeftUpLeg": (l_thigh_x, 0.0, -s * 2.0),
                "LeftLeg": (l_shin_x, 0.0, 0.0),
                "LeftFoot": (l_foot_x, 0.0, 0.0),
                "RightUpLeg": (r_thigh_x, 0.0, -s * 2.0),
                "RightLeg": (r_shin_x, 0.0, 0.0),
                "RightFoot": (r_foot_x, 0.0, 0.0),
            }
            z_bob = 0.004 + bounce * 0.014
            key_pose(arm, f, rots, hips_world_offset=(c * 0.009, 0.0, z_bob))

    create_slotted_nla_action(arm_obj, "Walk_Forward", 25, anim_walk)

    def anim_present(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 13, 25, 37, 49):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            hold = 0.72 + 0.28 * (0.5 - 0.5 * math.cos(ph))
            rots = {
                "Hips": (0.0, 0.0, -4.0 * hold),
                "Spine": (1.0, 0.0, -6.0 * hold),
                "Spine1": (2.0, 0.0, -9.0 * hold),
                "Neck": (0.0, 0.0, -4.0 * hold),
                "Head": (2.2, -1.5 * hold, -2.5 * hold),
                "LeftShoulder": (0.0, 4.0, 0.0),
                "LeftArm": (-3.0, rest_drop, 2.0),
                "LeftForeArm": (-14.0, rest_drop - 6.0, 3.0),
                "LeftHand": (-12.0, rest_drop - 10.0, 4.0),
                "RightShoulder": (0.0, 3.0 * hold, -3.0 * hold),
                "RightArm": (-36.0 * hold, 6.0 * hold - rest_drop * (1.0 - hold), -10.0 * hold),
                "RightForeArm": (-74.0 * hold, 4.0 * hold - (rest_drop - 6.0) * (1.0 - hold), -8.0 * hold),
                "RightHand": (-68.0 * hold, 4.0 * hold, 20.0 * hold),
                "LeftUpLeg": (-1.0, 1.0, 0.0),
                "LeftLeg": (2.0, 0.0, 0.0),
                "LeftFoot": (0.0, 0.0, 2.0),
                "RightUpLeg": (1.0, -0.5, 0.0),
                "RightLeg": (2.0, 0.0, 0.0),
                "RightFoot": (0.0, 0.0, -3.0),
            }
            key_pose(arm, f, rots, hips_world_offset=(0.0, 0.0, 0.002 * hold))

    create_slotted_nla_action(arm_obj, "Gesture_Present", 49, anim_present)

    def anim_greet(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 13, 25, 37, 49):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            lift = 0.5 - 0.5 * math.cos(ph)
            wave = math.sin(ph * 2.0) * 7.0 * lift
            rots = {
                "Hips": (0.0, 0.0, 3.0 * lift),
                "Spine": (1.0, 0.0, 4.0 * lift),
                "Spine1": (2.0, 0.0, 5.0 * lift),
                "Neck": (-1.0, 0.0, 2.0 * lift),
                "Head": (-4.0 * lift + 1.8, -1.6 + 2.5 * lift, 0.8),
                "LeftShoulder": (0.0, -3.0 * lift + 4.0 * (1.0 - lift), 0.0),
                "LeftArm": (-40.0 * lift - 3.0, -6.0 * lift + rest_drop * (1.0 - lift), 10.0 * lift),
                "LeftForeArm": (-94.0 * lift - 12.0 * (1.0 - lift), 8.0 + wave, 12.0 * lift),
                "LeftHand": (-96.0 * lift - 10.0 * (1.0 - lift), 6.0 + wave * 1.2, -16.0 * lift),
                "RightShoulder": (0.0, -4.0, 0.0),
                "RightArm": (-3.0, -rest_drop, -2.0),
                "RightForeArm": (-12.0, -(rest_drop - 6.0), -3.0),
                "RightHand": (-10.0, -(rest_drop - 10.0), -4.0),
                "LeftUpLeg": (0.0, 1.0, 0.0),
                "LeftLeg": (1.5, 0.0, 0.0),
                "LeftFoot": (0.0, 0.0, 2.0),
                "RightUpLeg": (0.0, -1.0, 0.0),
                "RightLeg": (1.5, 0.0, 0.0),
                "RightFoot": (0.0, 0.0, -2.0),
            }
            key_pose(arm, f, rots)

    create_slotted_nla_action(arm_obj, "Turn_Greet", 49, anim_greet)


def _glb_image_byte_lengths(glb_path: str) -> list[int]:
    with open(glb_path, "rb") as f:
        data = f.read()
    magic, _version, _length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, f"Invalid GLB magic in {glb_path}"
    json_len, json_type = struct.unpack_from("<II", data, 12)
    assert json_type == 0x4E4F534A, "First GLB chunk must be JSON"
    glb_json = json.loads(data[20 : 20 + json_len].decode("utf-8"))
    bvs = glb_json.get("bufferViews", [])
    return [
        int(bvs[img["bufferView"]].get("byteLength", 0))
        for img in glb_json.get("images", [])
        if "bufferView" in img and 0 <= int(img["bufferView"]) < len(bvs)
    ]


def add_facial_shape_keys(body: bpy.types.Object, lm: dict[str, object]) -> None:
    """Add Basis + eyeBlinkLeft/Right + mouthSmileLeft/Right morph targets onto SM_Companion_Body."""
    mesh = body.data
    if mesh.shape_keys is None:
        body.shape_key_add(name="Basis", from_mix=False)

    nose_x = float(lm["nose_x"])
    eye_z = float(lm["eye_z"])
    eye_dx = float(lm["eye_dx"])
    eye_front_y = float(lm["eye_front_y"])
    mouth_z = float(lm["mouth_z"])

    def _sstep(edge0: float, edge1: float, x: float) -> float:
        if abs(edge1 - edge0) < 1e-8:
            return 1.0 if x >= edge1 else 0.0
        t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3.0 - 2.0 * t)

    base_coords = [v.co.copy() for v in mesh.vertices]

    for key_name, sx in (("eyeBlinkLeft", 1.0), ("eyeBlinkRight", -1.0)):
        kb = body.shape_key_add(name=key_name, from_mix=False)
        cx = nose_x + sx * eye_dx
        for i, co in enumerate(base_coords):
            if co.y > eye_front_y + 0.022 or abs(co.x - cx) >= 0.021:
                kb.data[i].co = co
                continue
            ux = (co.x - cx) / 0.020
            horiz = _sstep(1.0, 0.08, ux * ux)
            dz = co.z - eye_z
            up_bell = _sstep(-0.002, 0.004, dz) * _sstep(0.015, 0.005, dz)
            lo_bell = _sstep(-0.008, -0.004, dz) * _sstep(-0.0005, -0.0035, dz)
            new_z = co.z - 0.0072 * horiz * up_bell + 0.0018 * horiz * lo_bell
            new_y = co.y + 0.0010 * horiz * up_bell
            kb.data[i].co = Vector((co.x, new_y, new_z))

    for key_name, sx in (("mouthSmileLeft", 1.0), ("mouthSmileRight", -1.0)):
        kb = body.shape_key_add(name=key_name, from_mix=False)
        cx = nose_x + sx * 0.019
        for i, co in enumerate(base_coords):
            side_offset = sx * (co.x - nose_x)
            if (
                co.y > eye_front_y + 0.026
                or side_offset <= 0.001
                or co.z > mouth_z + 0.015
                or co.z < mouth_z - 0.016
            ):
                kb.data[i].co = co
                continue
            dx = (co.x - cx) / 0.022
            dz = (co.z - mouth_z) / 0.015
            rad = _sstep(1.0, 0.0, dx * dx + dz * dz) * _sstep(0.001, 0.012, side_offset)
            kb.data[i].co = Vector((co.x + sx * 0.0020 * rad, co.y + 0.0018 * rad, co.z + 0.0038 * rad))

    mesh.update()
    print(f"Added facial shape keys to SM_Companion_Body: {[kb.name for kb in mesh.shape_keys.key_blocks]}")


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--face-check-only", action="store_true")
    parser.add_argument("--out-glb", default=OUT_GLB_PATH)
    args = parser.parse_args(argv)

    clear_scene()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.scene.render.fps = 24

    raw_body, raw_body_albedo, hd_bust, hd_bust_albedo, landmarks, skin_srgb = import_and_align_sources()
    hd_bust_clean = prepare_delighted_bust_albedo(hd_bust_albedo, skin_srgb)
    concept_img = bpy.data.images.load(CONCEPT_BUST_PNG, check_existing=False)
    concept_img.colorspace_settings.name = "sRGB"
    concept_img.pack()

    body = build_clean_body_and_hd_head(
        raw_body, raw_body_albedo, hd_bust, hd_bust_clean, concept_img, landmarks, skin_srgb
    )
    add_facial_shape_keys(body, landmarks)
    glasses = build_fitted_glasses(landmarks)

    if args.face_check_only:
        render_v4_face_checkpoint(body, glasses, landmarks)
        return

    sk_landmarks = measure_skeleton_landmarks(body)
    arm_obj = build_armature(sk_landmarks)
    assign_body_weights_and_facial_lock(body, arm_obj, sk_landmarks)
    bind_glasses_rigidly(glasses, arm_obj)
    author_animations(arm_obj, float(sk_landmarks["bind_drop_deg"]))

    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)

    out_path = os.path.abspath(args.out_glb)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    size_bytes = 0
    img_sizes: list[int] = []
    for quality in (88, 82, 76, 70):
        bpy.ops.export_scene.gltf(
            filepath=out_path,
            export_format="GLB",
            export_yup=True,
            export_apply=False,
            export_materials="EXPORT",
            export_image_format="WEBP",
            export_image_quality=quality,
            export_meshopt_compression_enable=True,
            export_meshopt_extension="EXT_meshopt_compression",
            export_skins=True,
            export_morph=True,
            export_animations=True,
            export_animation_mode="NLA_TRACKS",
            export_nla_strips=True,
        )
        size_bytes = os.path.getsize(out_path)
        img_sizes = _glb_image_byte_lengths(out_path)
        max_img = max(img_sizes, default=0)
        print(
            f"Exported {out_path} (webp_q={quality}, meshopt): {size_bytes} bytes ({size_bytes / 1024:.1f} KB), "
            f"images={[round(s / 1024, 1) for s in img_sizes]} KB"
        )
        if size_bytes <= 3 * 1024 * 1024 and max_img <= 100 * 1024:
            break
    assert size_bytes <= 3.0 * 1024 * 1024, f"Companion GLB exceeds 3.0 MB limit: {size_bytes}"
    assert max(img_sizes, default=0) <= 100 * 1024, f"Embedded WebP image exceeds 100 KB limit: {img_sizes}"


if __name__ == "__main__":
    main()
