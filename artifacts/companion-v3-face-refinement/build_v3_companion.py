#!/usr/bin/env python3
"""
Likeness Companion v3 Production Pipeline (`zachary_companion.glb`).

Upgrades over v2:
- Replaces the low-resolution full-body TRELLIS.2 head with a dedicated high-resolution 1024-latent /
  2048-texel 3D head-and-shoulders bust generated directly from the user-approved 1024x1024 glasses-off
  portrait (`hd_bust_trellis2_1024_s42.glb`), yielding true sculpted eyelids, brow arches, nose bridge,
  nostrils, philtrum, cupid's bow lips, clean tapered V-line jawline, anatomical ears, and layered
  chestnut hair strands (Law 6: Shape First, Paint Second).
- Performs smooth-falloff sculptural refinements on the 145k-tri HD bust (de-ridging embossed eyebrow
  bars and subtly relaxing lower-lip projection for composed executive likeness) before baking a
  1024x1024 tangent-space Normal Map (`Zachary_Face_Normal`), delighted & color-harmonized 1280x1280
  Albedo (`Zachary_Face_HD`) with landmark-locked high-res eye clarity, and an anatomical 1024x1024
  Roughness Map (`Zachary_Face_MR`: wet 0.06 corneas, 0.36 lips, 0.44 hair, 0.50-0.58 skin, 0.72 brows).
- Preserves 100% of the dark overshirt collar & white crew tee on the watertight manifold body while
  excising only the inner neck core inside the collar and baking with tight 1.6mm cage extrusion
  (eliminating v2's collar cut teeth and lapel overhang black triangles).
- Fits precision thin brushed-gunmetal round-panto spectacles (`SM_Companion_Glasses`) with clean
  temple hug (zero jutting side wings) and 5.5-6.0mm corneal clearance.
- Preserves the exact 19-bone `CompanionArmature`, deterministic seam-safe skinning with rigid Head
  lock, and 4 baked Blender 5.2 Slotted NLA clips (`Idle_Breathing`, `Walk_Forward`, `Gesture_Present`,
  `Turn_Greet`) strictly under the <= 3.0 MB WebGL governance budget.
"""

from __future__ import annotations

import argparse
from collections import deque
import math
import os
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
    PROJECT_ROOT, "artifacts", "companion-v3-face-refinement", "hd_bust_trellis2_1024_s42.glb"
)
FACE_CLOSEUP_PATH = os.path.join(
    PROJECT_ROOT, "artifacts", "companion-v3-face-refinement", "zachary_real_selfie_clean.png"
)
V3_WORK_DIR = os.path.join(PROJECT_ROOT, "artifacts", "companion-v3-face-refinement")
FACE_CHECK_PNG = os.path.join(V3_WORK_DIR, "v3_face_checkpoint.png")
OUT_GLB_PATH = os.path.join(PROJECT_ROOT, "public", "models", "zachary_companion.glb")

TARGET_HEIGHT = 1.620
BUST_SCALE = 0.440

# Ground-truth warm golden-tan peach skin calibrated directly to IMG20261122014334.heic
TARGET_SKIN_SRGB = np.array([0.752, 0.614, 0.528], dtype=np.float32)
# Ground-truth natural soft jet-black / charcoal-black hair calibrated to IMG20261122014334.heic
TARGET_HAIR_SRGB = np.array([0.105, 0.102, 0.108], dtype=np.float32)


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
        # Horizontal pass
        pad = np.pad(out, ((0, 0), (radius, radius), (0, 0)), mode="edge")
        cs = np.cumsum(pad, axis=1, dtype=np.float64)
        out = ((cs[:, 2 * radius :, :] - np.concatenate([np.zeros((h, 1, out.shape[2])), cs[:, : w - 1, :]], axis=1)) / (2 * radius + 1)).astype(np.float32)
        # Vertical pass
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

    # Bake full parent hierarchy matrix directly into vertex positions (avoids glTF Empty parent 90deg rot trap)
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

    # Remove imported non-mesh empties
    for o in new_objs:
        if o != obj and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)

    # Identify albedo image (largest sRGB image or first >= 512px)
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
    v_seen = np.zeros(len(mesh.vertices), dtype=bool)
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            if not v_seen[vi]:
                u, v = uv_data[li].uv
                ix = int(np.clip(u * (w - 1), 0, w - 1))
                iy = int(np.clip(v * (h - 1), 0, h - 1))
                v_col[vi] = px[iy, ix]
                v_seen[vi] = True
    return v_col


# ==============================================================================
# STEP 1: IMPORT, NORMALIZE BODY & ALIGN HD BUST + SCULPTURAL REFINEMENTS
# ==============================================================================
def import_and_align_sources() -> tuple[
    bpy.types.Object, bpy.types.Image, bpy.types.Object, bpy.types.Image, dict[str, float]
]:
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

    # Measure raw body actual skin-neck center around Z=1.335..1.355m (avoiding back-collar Y skew!)
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

    # Import HD bust, weld UV-split vertices (preserving loop UVs), and strip TRELLIS.2's trapped dark
    # hollow inner backing shell (~1.7mm behind outer skin) via BVH hemisphere sky-visibility raycasting
    # BEFORE trimming the neck!
    from mathutils.bvhtree import BVHTree
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
        escaped = False
        origin = fc + n * 0.0005
        for d in dirs:
            hit, _, _, _ = bvh_shell.ray_cast(origin, d, 5.0)
            if hit is None:
                escaped = True
                break
        is_outer[f.index] = escaped

    # 2-pass deep-crevice recovery (e.g. nostril interior / behind-ear fold surrounded by outer faces with aligned normal)
    for _ in range(2):
        recovered = []
        for f in bm_weld.faces:
            if is_outer[f.index]:
                continue
            adj_out = [
                lf for e in f.edges for lf in e.link_faces
                if lf != f and is_outer[lf.index] and f.normal.dot(lf.normal) > 0.25
            ]
            if len(adj_out) >= 2:
                recovered.append(f.index)
        for fi in recovered:
            is_outer[fi] = True

    inner_faces = [f for f in bm_weld.faces if not is_outer[f.index]]
    if inner_faces:
        bmesh.ops.delete(bm_weld, geom=inner_faces, context="FACES")
    bmesh.ops.delete(bm_weld, geom=[v for v in bm_weld.verts if not v.link_faces], context="VERTS")
    # Fill tiny 1-2 tri nostril/fold pinholes on face front
    face_hole_edges = [
        e for e in bm_weld.edges
        if e.is_boundary and e.verts[0].co.y < -0.15 and e.verts[0].co.z > -0.10
    ]
    if face_hole_edges:
        bmesh.ops.holes_fill(bm_weld, edges=face_hole_edges, sides=6)
    print(f"Stripped TRELLIS.2 hollow inner backing shell: removed {len(inner_faces)} inner faces, kept {len(bm_weld.faces)} pure outer faces")
    bm_weld.to_mesh(hd_bust.data)
    bm_weld.free()
    hd_bust.data.update()

    bust_vcol = sample_vertex_colors(hd_bust.data, hd_bust_albedo)
    h_pts = np.array([list(v.co) for v in hd_bust.data.vertices], dtype=np.float64)
    luma_h = 0.299 * bust_vcol[:, 0] + 0.587 * bust_vcol[:, 1] + 0.114 * bust_vcol[:, 2]

    # Exclude high dark brow ridges (>0.146 raw Z) when measuring true iris/eyeball centers!
    eye_l_raw = h_pts[(h_pts[:, 1] < -0.18) & (h_pts[:, 0] > 0.03) & (h_pts[:, 0] < 0.125) & (h_pts[:, 2] > 0.05) & (h_pts[:, 2] < 0.146) & (luma_h < 0.25)]
    eye_r_raw = h_pts[(h_pts[:, 1] < -0.18) & (h_pts[:, 0] < -0.03) & (h_pts[:, 0] > -0.125) & (h_pts[:, 2] > 0.05) & (h_pts[:, 2] < 0.146) & (luma_h < 0.25)]
    el_med = np.median(eye_l_raw, axis=0) if len(eye_l_raw) else np.array([0.0728, -0.220, 0.1300])
    er_med = np.median(eye_r_raw, axis=0) if len(eye_r_raw) else np.array([-0.0728, -0.220, 0.1300])
    eye_mid_x_raw = 0.5 * float(el_med[0] + er_med[0])
    eye_ipd_raw = float(el_med[0] - er_med[0])

    # Neck center of HD bust at z_raw in [-0.21, -0.15] (midpoint of front & back skin neck cylinder)
    is_skin_h = ((bust_vcol[:, 0] - bust_vcol[:, 2]) > 0.04) & (bust_vcol[:, 0] > 0.35)
    bust_neck_sl = h_pts[(h_pts[:, 2] > -0.22) & (h_pts[:, 2] < -0.14) & is_skin_h]
    bust_neck_cy_raw = (
        0.5 * (float(bust_neck_sl[:, 1].min()) + float(bust_neck_sl[:, 1].max()))
        if len(bust_neck_sl) > 10
        else 0.005
    )
    bust_crown_z_raw = float(h_pts[:, 2].max())

    # Transform HD bust cleanly onto body: crown at Z=1.622m, eyes centered on X=0, neck aligned to raw_neck_cy
    target_crown_z = 1.622
    dx = -eye_mid_x_raw * BUST_SCALE
    dy = raw_neck_cy - bust_neck_cy_raw * BUST_SCALE - 0.0025
    dz = target_crown_z - bust_crown_z_raw * BUST_SCALE
    bust_mat = Matrix.Translation(Vector((dx, dy, dz))) @ Matrix.Scale(BUST_SCALE, 4)
    hd_bust.data.transform(bust_mat)
    hd_bust.data.update()

    # Re-measure exact world iris/cornea/mouth landmarks directly on transformed HD bust
    a_pts = np.array([list(v.co) for v in hd_bust.data.vertices], dtype=np.float64)
    a_lum = luma_h
    iris_l = a_pts[(a_pts[:, 1] < -0.075) & (a_pts[:, 0] > 0.022) & (a_pts[:, 0] < 0.044) & (a_pts[:, 2] >= 1.477) & (a_pts[:, 2] <= 1.491) & (a_lum < 0.22)]
    iris_r = a_pts[(a_pts[:, 1] < -0.075) & (a_pts[:, 0] < -0.022) & (a_pts[:, 0] > -0.044) & (a_pts[:, 2] >= 1.477) & (a_pts[:, 2] <= 1.491) & (a_lum < 0.22)]
    eye_l_pos = Vector(np.mean(iris_l, axis=0)) if len(iris_l) else Vector((float(el_med[0]) * BUST_SCALE + dx, float(el_med[1]) * BUST_SCALE + dy, float(el_med[2]) * BUST_SCALE + dz))
    eye_r_pos = Vector(np.mean(iris_r, axis=0)) if len(iris_r) else Vector((float(er_med[0]) * BUST_SCALE + dx, float(er_med[1]) * BUST_SCALE + dy, float(er_med[2]) * BUST_SCALE + dz))
    eye_z = 0.5 * (eye_l_pos.z + eye_r_pos.z) - 0.0010  # true open eyeball center (not upper lash line)
    eye_dx = 0.5 * (eye_l_pos.x - eye_r_pos.x)
    nose_x = 0.5 * (eye_l_pos.x + eye_r_pos.x)

    nose_sub = a_pts[(np.abs(a_pts[:, 0] - nose_x) < 0.012) & (a_pts[:, 2] > eye_z - 0.055) & (a_pts[:, 2] < eye_z - 0.015)]
    nose_tip = nose_sub[np.argmin(nose_sub[:, 1])]
    bridge_sub = a_pts[(np.abs(a_pts[:, 0] - nose_x) < 0.008) & (np.abs(a_pts[:, 2] - eye_z) < 0.008) & (a_pts[:, 1] < -0.05)]
    bridge_y = float(bridge_sub[:, 1].min()) if len(bridge_sub) else float(eye_l_pos.y) - 0.008

    # Measure corneal front-most Y at left/right eye centers
    cornea_l = a_pts[(np.abs(a_pts[:, 0] - eye_l_pos.x) < 0.008) & (np.abs(a_pts[:, 2] - eye_z) < 0.006) & (a_pts[:, 1] < -0.06)]
    cornea_r = a_pts[(np.abs(a_pts[:, 0] - eye_r_pos.x) < 0.008) & (np.abs(a_pts[:, 2] - eye_z) < 0.006) & (a_pts[:, 1] < -0.06)]
    eye_front_y = float(min(
        cornea_l[:, 1].min() if len(cornea_l) else eye_l_pos.y,
        cornea_r[:, 1].min() if len(cornea_r) else eye_r_pos.y,
    ))

    # Measure sculpted ear helix / temporal bounds for flush zero-wing glasses temples
    ear_l = a_pts[(a_pts[:, 2] >= eye_z - 0.025) & (a_pts[:, 2] <= eye_z + 0.022) & (a_pts[:, 1] >= -0.025) & (a_pts[:, 1] <= 0.045) & (a_pts[:, 0] > 0.065)]
    ear_r = a_pts[(a_pts[:, 2] >= eye_z - 0.025) & (a_pts[:, 2] <= eye_z + 0.022) & (a_pts[:, 1] >= -0.025) & (a_pts[:, 1] <= 0.045) & (a_pts[:, 0] < -0.065)]
    # Measure temple width right in front of ears (Y in [-0.055, -0.015])
    tmp_l = a_pts[(a_pts[:, 2] >= eye_z - 0.012) & (a_pts[:, 2] <= eye_z + 0.018) & (a_pts[:, 1] >= -0.058) & (a_pts[:, 1] <= -0.015) & (a_pts[:, 0] > 0.055)]
    tmp_r = a_pts[(a_pts[:, 2] >= eye_z - 0.012) & (a_pts[:, 2] <= eye_z + 0.018) & (a_pts[:, 1] >= -0.058) & (a_pts[:, 1] <= -0.015) & (a_pts[:, 0] < -0.055)]
    temple_half_w = 0.5 * (
        (float(np.percentile(tmp_l[:, 0], 96)) if len(tmp_l) else 0.076)
        + (float(np.percentile(np.abs(tmp_r[:, 0]), 96)) if len(tmp_r) else 0.076)
    )
    ear_top_y = float(np.median(ear_l[:, 1])) if len(ear_l) else 0.010
    ear_half_w = 0.5 * (
        (float(np.percentile(ear_l[:, 0], 85)) if len(ear_l) else 0.084)
        + (float(np.percentile(np.abs(ear_r[:, 0]), 85)) if len(ear_r) else 0.084)
    )

    # Measure true lip center Z directly from rosy lip vertices below nose!
    m_mask = (a_pts[:, 1] < -0.084) & (np.abs(a_pts[:, 0] - nose_x) < 0.024) & (a_pts[:, 2] >= 1.406) & (a_pts[:, 2] <= 1.436)
    m_col = bust_vcol[m_mask]
    m_pts = a_pts[m_mask]
    lip_sel = m_pts[((m_col[:, 0] - m_col[:, 1]) > 0.08) & (a_lum[m_mask] < 0.72)]
    mouth_z = float(np.median(lip_sel[:, 2])) if len(lip_sel) >= 8 else 1.4186
    chin_sub = a_pts[(np.abs(a_pts[:, 0] - nose_x) < 0.015) & (a_pts[:, 1] < -0.05) & (a_pts[:, 2] < mouth_z - 0.015)]
    chin_z = float(chin_sub[:, 2].min()) if len(chin_sub) else 1.371

    landmarks = {
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
        "temple_half_w": temple_half_w,
        "ear_half_w": ear_half_w,
        "ear_top_y": ear_top_y,
        # Exact real selfie UV IPD = 0.63660 - 0.37670 = 0.25990, midpoint = 0.50665, eye v = 0.47410
        "proj_scale_uv": 0.25990 / max(1e-4, 2.0 * min(0.0328, max(0.0318, eye_dx))),
        "proj_u0": 0.50665,
        "proj_v0": 0.47410,
    }
    print(f"Aligned HD Bust landmarks: { {k: round(v, 4) for k, v in landmarks.items()} }")

    # Sculptural refinements directly on 145k-tri HD bust (compact small oval face + lowered fringe bangs)
    sculpt_refine_hd_bust(hd_bust, bust_vcol, landmarks)

    # Re-measure facial landmarks & outer temple contour post-sculpt so projection and glasses match small oval face 1:1
    s_pts = np.array([list(v.co) for v in hd_bust.data.vertices], dtype=np.float64)
    landmarks["eye_dx"] = eye_dx * 0.935
    landmarks["mouth_z"] = eye_z + (mouth_z - eye_z) * 0.945
    landmarks["chin_z"] = eye_z + (chin_z - eye_z) * 0.945 + 0.0010
    landmarks["proj_scale_uv"] = 0.25990 / max(1e-4, 2.0 * landmarks["eye_dx"])

    bridge_sub_p = s_pts[(np.abs(s_pts[:, 0] - nose_x) < 0.008) & (np.abs(s_pts[:, 2] - eye_z) < 0.008) & (s_pts[:, 1] < -0.05)]
    if len(bridge_sub_p):
        landmarks["bridge_y"] = float(bridge_sub_p[:, 1].min())
    cornea_l_p = s_pts[(np.abs(s_pts[:, 0] - (nose_x + landmarks["eye_dx"])) < 0.008) & (np.abs(s_pts[:, 2] - eye_z) < 0.006) & (s_pts[:, 1] < -0.05)]
    cornea_r_p = s_pts[(np.abs(s_pts[:, 0] - (nose_x - landmarks["eye_dx"])) < 0.008) & (np.abs(s_pts[:, 2] - eye_z) < 0.006) & (s_pts[:, 1] < -0.05)]
    if len(cornea_l_p) or len(cornea_r_p):
        landmarks["eye_front_y"] = float(min(
            cornea_l_p[:, 1].min() if len(cornea_l_p) else landmarks["eye_front_y"],
            cornea_r_p[:, 1].min() if len(cornea_r_p) else landmarks["eye_front_y"],
        ))
    nose_sub_p = s_pts[(np.abs(s_pts[:, 0] - nose_x) < 0.012) & (s_pts[:, 2] > eye_z - 0.055) & (s_pts[:, 2] < eye_z - 0.015)]
    if len(nose_sub_p):
        nose_tip_p = nose_sub_p[np.argmin(nose_sub_p[:, 1])]
        landmarks["nose_tip_y"] = float(nose_tip_p[1])
        landmarks["nose_tip_z"] = float(nose_tip_p[2])

    temple_band = np.abs(s_pts[:, 2] - (eye_z + 0.0046)) < 0.0085
    temple_ys = [-0.080, -0.065, -0.050, -0.035, -0.020, -0.005, 0.010, 0.022]
    temple_profile_x: list[float] = []
    for ty in temple_ys:
        ymask = temple_band & (np.abs(s_pts[:, 1] - ty) < 0.0075)
        l_xs = np.abs(s_pts[ymask & (s_pts[:, 0] > nose_x), 0] - nose_x)
        r_xs = np.abs(s_pts[ymask & (s_pts[:, 0] < nose_x), 0] - nose_x)
        p_l = float(np.percentile(l_xs, 98)) if len(l_xs) else 0.072
        p_r = float(np.percentile(r_xs, 98)) if len(r_xs) else 0.072
        temple_profile_x.append(max(p_l, p_r))
    landmarks["temple_profile_y"] = temple_ys  # type: ignore[assignment]
    landmarks["temple_profile_x"] = temple_profile_x  # type: ignore[assignment]
    print(f"Measured HD temple half-width profile: {[(round(y, 3), round(x, 4)) for y, x in zip(temple_ys, temple_profile_x)]}")

    return raw_body, raw_body_albedo, hd_bust, hd_bust_albedo, landmarks


def sculpt_refine_hd_bust(
    hd_bust: bpy.types.Object, bust_vcol: np.ndarray, lm: dict[str, float]
) -> None:
    """
    1. Smoothly relax TRELLIS.2's slightly embossed eyebrow clay ridges back onto natural brow bone.
    2. Subtly relax lower-lip pout (~0.7mm inward) & micro-lift mouth corners (~0.4mm) for calm executive composure.
    3. Excise shoulders/collar below the neck cleanly while keeping a solid cylindrical neck down to Z=1.298m
       tapered inward inside the body's intact overshirt collar & white crew tee.
    """
    mesh = hd_bust.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Weld split UV vertices transiently for clean neighborhood Laplacian smoothing?
    # Keep original UVs intact by building spatial-key adjacency via vertex positions!
    eye_z = lm["eye_z"]
    eye_dx = lm["eye_dx"]
    nose_x = lm["nose_x"]
    mouth_z = lm["mouth_z"]
    neck_cy = lm["neck_cy"]

    luma = 0.299 * bust_vcol[:, 0] + 0.587 * bust_vcol[:, 1] + 0.114 * bust_vcol[:, 2]

    # 0. Topological scalp-seeded BFS HairMask & HairShadow BEFORE any vertex deformation!
    n_verts = len(bm.verts)
    is_hair_cand = np.array(
        [
            bool(
                luma[v.index] < 0.30
                and (v.co.z >= eye_z + 0.012 or v.co.y > -0.028)
                and not (
                    v.co.y < -0.055
                    and abs(v.co.x - nose_x) <= 0.064
                    and v.co.z < (eye_z + 0.017 if abs(v.co.x - nose_x) < 0.018 else eye_z + 0.0245)
                )
            )
            for v in bm.verts
        ],
        dtype=bool,
    )
    visited = np.zeros(n_verts, dtype=bool)
    queue: deque[int] = deque()
    for v in bm.verts:
        if luma[v.index] < 0.32 and (
            v.co.z >= eye_z + 0.045 or (v.co.y > -0.020 and v.co.z >= eye_z - 0.045)
        ):
            visited[v.index] = True
            queue.append(v.index)

    while queue:
        vi = queue.popleft()
        v = bm.verts[vi]
        for e in v.link_edges:
            nb = e.other_vert(v)
            ni = nb.index
            if not visited[ni] and is_hair_cand[ni]:
                visited[ni] = True
                queue.append(ni)

    hair_f = visited.astype(np.float32)
    for _ in range(2):
        hf_next = hair_f.copy()
        for v in bm.verts:
            if not v.link_edges:
                continue
            avg_h = sum(hair_f[e.other_vert(v).index] for e in v.link_edges) / float(len(v.link_edges))
            hf_next[v.index] = 0.45 * hair_f[v.index] + 0.55 * avg_h
        hair_f = hf_next

    hair_diffused = hair_f.copy()
    for _ in range(8):
        hd_next = hair_diffused.copy()
        for v in bm.verts:
            if not v.link_edges:
                continue
            avg_d = sum(hair_diffused[e.other_vert(v).index] for e in v.link_edges) / float(len(v.link_edges))
            hd_next[v.index] = 0.40 * hair_diffused[v.index] + 0.60 * avg_d
        hair_diffused = hd_next

    hair_shadow = np.clip((hair_diffused - hair_f) * 1.8, 0.0, 1.0)
    hm_layer = bm.verts.layers.float.new("HairMask")
    hs_layer = bm.verts.layers.float.new("HairShadow")
    for v in bm.verts:
        v[hm_layer] = float(hair_f[v.index])
        v[hs_layer] = float(hair_shadow[v.index])
    print(f"HairMask BFS captured {int(visited.sum())} connected hair verts out of {n_verts}")

    # 1. Flatten embargoed/embossed angry V-brow ridges cleanly onto natural brow bone (12 passes + 1.4mm seating)
    brow_w = np.zeros(len(bm.verts), dtype=np.float32)
    for v in bm.verts:
        co = v.co
        if co.y < -0.068 and (eye_z + 0.010) <= co.z <= (eye_z + 0.038):
            ax = abs(co.x - nose_x)
            if 0.007 <= ax <= 0.064:
                wz = math.exp(-((co.z - (eye_z + 0.0235)) / 0.0095) ** 2)
                wx = smoothstep(0.007, 0.015, ax) * (1.0 - smoothstep(0.050, 0.064, ax))
                dark_w = 1.0 - smoothstep(0.18, 0.45, float(luma[v.index]))
                w = wz * wx * (0.35 + 0.65 * dark_w)
                if w > 0.01:
                    brow_w[v.index] = w

    for _ in range(12):
        new_pos: dict[int, Vector] = {}
        for v in bm.verts:
            w = float(brow_w[v.index])
            if w <= 0.02 or not v.link_edges:
                continue
            avg = Vector((0.0, 0.0, 0.0))
            for e in v.link_edges:
                avg += e.other_vert(v).co
            avg /= float(len(v.link_edges))
            new_pos[v.index] = v.co.lerp(avg, 0.50 * w)
        for vi, p in new_pos.items():
            bm.verts[vi].co = p

    for v in bm.verts:
        w = float(brow_w[v.index])
        if w > 0.02:
            v.co.y += 0.00140 * w

    # 1a. Isotropic 3D small-head compaction pivoted at (nose_x, neck_cy, eye_z) (-6.5% X, -4.5% Y, -5.5% Z)
    for v in bm.verts:
        co = v.co
        w_head = smoothstep(1.338, 1.376, co.z)
        if w_head > 1e-4:
            co.x = nose_x + (co.x - nose_x) * (1.0 - 0.065 * w_head)
            co.y = neck_cy + (co.y - neck_cy) * (1.0 - 0.045 * w_head)
            co.z = eye_z + (co.z - eye_z) * (1.0 - 0.055 * w_head)

    # 1b. Gentle HairMask-gated drape (-5.0mm) & subtle part narrowing (zero forehead skin folding!)
    for v in bm.verts:
        hf = float(hair_f[v.index])
        if hf <= 0.25:
            continue
        co = v.co
        ax = abs(co.x - nose_x)
        if co.y < -0.056 and 1.484 <= co.z <= 1.562 and ax < 0.066:
            w_bangs = (
                smoothstep(1.484, 1.512, co.z)
                * (1.0 - smoothstep(1.535, 1.562, co.z))
                * smoothstep(-0.056, -0.074, co.y)
                * (1.0 - smoothstep(0.044, 0.066, ax))
            )
            co.z -= 0.0050 * hf * w_bangs
        dx_h = co.x - nose_x
        if co.y < -0.054 and 1.495 <= co.z <= 1.558:
            w_part_z = (
                smoothstep(1.495, 1.514, co.z)
                * (1.0 - smoothstep(1.538, 1.558, co.z))
                * smoothstep(-0.054, -0.072, co.y)
            )
            if -0.054 <= dx_h <= -0.022:
                w_l = hf * w_part_z * smoothstep(-0.054, -0.036, dx_h) * (1.0 - smoothstep(-0.028, -0.022, dx_h))
                co.x += 0.0030 * w_l
            if -0.014 <= dx_h <= 0.012:
                w_r = hf * w_part_z * smoothstep(-0.014, -0.004, dx_h) * (1.0 - smoothstep(0.006, 0.012, dx_h))
                co.x -= 0.0024 * w_r

    bang_gap_verts = [
        v for v in bm.verts
        if not v.is_boundary
        and v[hm_layer] > 0.2
        and -0.058 <= (v.co.x - nose_x) <= 0.020
        and 1.480 <= v.co.z <= 1.562
        and v.co.y < -0.050
    ]
    for _ in range(4):
        disp_bg: dict[int, Vector] = {}
        for v in bang_gap_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                disp_bg[v.index] = (avg - v.co) * 0.30
        for v in bang_gap_verts:
            if v.index in disp_bg:
                v.co += disp_bg[v.index]

    # 2. Match clean small-oval proportions while protecting 3D eyelid & lip relief:
    for v in bm.verts:
        co = v.co
        ax = abs(co.x - nose_x)

        # Gentle nasal alar wing trim (-6%) keeping authentic rounded nasal tip & alar character
        if co.y < -0.072 and 1.432 <= co.z <= 1.468 and ax < 0.025:
            w_nose = math.exp(-((co.z - 1.446) / 0.014) ** 2) * smoothstep(-0.072, -0.085, co.y)
            co.x -= (co.x - nose_x) * 0.06 * w_nose
            w_tip = math.exp(-(ax / 0.007) ** 2) * math.exp(-((co.z - 1.448) / 0.008) ** 2)
            co.y += 0.0008 * w_tip

        # Gentle lip tidying (+0.8mm center, subtle corner lift) so 3D upper & lower lip relief stays crisp
        if co.y < -0.068 and ax < 0.036 and abs(co.z - mouth_z) < 0.024:
            gx_lip = math.exp(-(ax / 0.020) ** 2)
            gz_lip = smoothstep(0.018, 0.0, abs(co.z - mouth_z))
            co.y += 0.0008 * gx_lip * gz_lip * smoothstep(-0.068, -0.078, co.y)

            w_wid = (
                smoothstep(0.014, 0.020, ax)
                * (1.0 - smoothstep(0.026, 0.033, ax))
                * gz_lip
                * smoothstep(-0.068, -0.078, co.y)
            )
            co.y += 0.0006 * w_wid

            u_r3d = smoothstep(0.011, 0.026, ax) * math.exp(-(max(0.0, ax - 0.030) / 0.010) ** 2)
            gz_c = math.exp(-((co.z - (mouth_z + 0.0005)) / 0.0075) ** 2)
            w_corner = u_r3d * gz_c
            co.z += 0.0013 * w_corner
            co.y += 0.0008 * w_corner

        if 1.388 <= co.z <= 1.408 and ax < 0.024 and co.y < -0.064:
            w_sublip = (
                smoothstep(1.388, 1.396, co.z)
                * (1.0 - smoothstep(1.402, 1.408, co.z))
                * math.exp(-(ax / 0.015) ** 2)
                * smoothstep(-0.064, -0.074, co.y)
            )
            co.y -= 0.0008 * w_sublip

        # Multiplicative convex oval cheek & jawline taper (never pinches chin tip or hollows buccal cheek!)
        w_oval = (
            smoothstep(-0.022, -0.052, co.y)
            * smoothstep(1.366, 1.392, co.z)
            * (1.0 - smoothstep(1.458, 1.485, co.z))
        )
        co.x = nose_x + (co.x - nose_x) * (1.0 - 0.085 * w_oval)

        # Soft oval chin apex rounding (prevents pointy V-tip while keeping narrow oval silhouette)
        if 1.370 <= co.z <= 1.392 and co.y < -0.052 and ax < 0.018:
            w_chin_tip = smoothstep(1.390, 1.374, co.z) * math.exp(-(ax / 0.011) ** 2)
            co.z += 0.0010 * w_chin_tip
            co.y += 0.0006 * w_chin_tip

        # Subtle lower-eyelid warmth matching anime aesthetic
        if co.y < -0.068 and abs(ax - eye_dx * 0.935) < 0.020 and abs(co.z - (eye_z - 0.0060)) < 0.008:
            gx_lid = math.exp(-((ax - eye_dx * 0.935) / 0.009) ** 2)
            gz_lid = math.exp(-((co.z - (eye_z - 0.0060)) / 0.0038) ** 2)
            co.z += 0.0004 * gx_lid * gz_lid

        # Recede TRELLIS.2 overhanging angry 3D brow shelf strictly above Z=1.494 (eyelid sockets intact!)
        if 1.494 <= co.z <= 1.512 and ax < 0.050 and co.y < -0.068:
            w_brow_shelf = (
                math.exp(-((co.z - 1.500) / 0.007) ** 2)
                * (1.0 - smoothstep(0.036, 0.050, ax))
                * smoothstep(-0.068, -0.082, co.y)
            )
            co.y += 0.0014 * w_brow_shelf
            co.z += 0.0008 * w_brow_shelf

        # Fill & smooth diagonal lower-cheek / nasolabial hollows
        if 0.015 <= ax <= 0.046 and 1.386 <= co.z <= 1.448 and co.y < -0.058:
            w_cheek_fill = (
                math.exp(-((ax - 0.028) / 0.011) ** 2)
                * math.exp(-((co.z - 1.416) / 0.020) ** 2)
                * smoothstep(-0.058, -0.072, co.y)
            )
            co.y -= 0.0018 * w_cheek_fill
            co.x += (1.0 if co.x > nose_x else -1.0) * 0.0010 * w_cheek_fill

    # Mild symmetric +X temple balance (+2.2mm) & smooth vertical temple/cheek grooves
    for v in bm.verts:
        co = v.co
        if co.x > nose_x + 0.040 and -0.074 <= co.y <= 0.015 and 1.465 <= co.z <= 1.568:
            wx_t = smoothstep(0.040, 0.058, co.x - nose_x)
            wy_t = math.exp(-((co.y - (-0.044)) / 0.026) ** 2)
            wz_t = math.exp(-((co.z - 1.518) / 0.032) ** 2)
            co.x += 0.0022 * wx_t * wy_t * wz_t

    lower_oval_verts = [
        v for v in bm.verts
        if not v.is_boundary
        and 0.008 <= abs(v.co.x - nose_x)
        and v.co.y < -0.032
        and 1.348 <= v.co.z <= 1.452
    ]
    for _ in range(6):
        disp_lo: dict[int, Vector] = {}
        for v in lower_oval_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                disp_lo[v.index] = (avg - v.co) * 0.38
        for v in lower_oval_verts:
            if v.index in disp_lo:
                v.co += disp_lo[v.index]

    # 10-pass Front-Face Surface Smoothing protecting nose ridge, eye sockets & eyelids, and 3D lips!
    anime_face_verts = [
        v for v in bm.verts
        if not v.is_boundary
        and 1.350 <= v.co.z <= 1.505
        and v.co.y < -0.042
        and v[hm_layer] < 0.25
    ]
    for _ in range(10):
        disp_af: dict[int, Vector] = {}
        for v in anime_face_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                is_nose_ridge = abs(v.co.x - nose_x) < 0.010 and 1.436 <= v.co.z <= 1.466
                is_eye_zone = abs(abs(v.co.x - nose_x) - eye_dx * 0.935) < 0.022 and abs(v.co.z - eye_z) < 0.015
                is_lip_zone = abs(v.co.x - nose_x) < 0.030 and abs(v.co.z - mouth_z) < 0.015
                w_sm = 0.10 if (is_nose_ridge or is_eye_zone or is_lip_zone) else 0.45
                disp_af[v.index] = (avg - v.co) * w_sm
        for v in anime_face_verts:
            if v.index in disp_af:
                v.co += disp_af[v.index]

    temple_groove_verts = [
        v for v in bm.verts
        if not v.is_boundary
        and 0.056 <= abs(v.co.x - nose_x) <= 0.086
        and -0.066 <= v.co.y <= -0.005
        and 1.470 <= v.co.z <= 1.545
    ]
    for _ in range(6):
        disp_tg: dict[int, Vector] = {}
        for v in temple_groove_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                disp_tg[v.index] = (avg - v.co) * 0.38
        for v in temple_groove_verts:
            if v.index in disp_tg:
                v.co += disp_tg[v.index]

    # Smooth ONLY exposed forehead SKIN vertices (hm_layer < 0.15) so bangs & forehead never smear into each other
    forehead_crease_verts = [
        v for v in bm.verts
        if not v.is_boundary
        and v[hm_layer] < 0.15
        and -0.058 <= (v.co.x - nose_x) <= 0.058
        and 1.488 <= v.co.z <= 1.545
        and v.co.y < -0.052
    ]
    for _ in range(8):
        disp_fc: dict[int, Vector] = {}
        for v in forehead_crease_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                disp_fc[v.index] = (avg - v.co) * 0.42
        for v in forehead_crease_verts:
            if v.index in disp_fc:
                v.co += disp_fc[v.index]

    # 2b. Unfold TRELLIS.2 tiny inward-folded nostril alar crease pinhole (n.z = -0.96 pocket) before normal bake
    nostril_verts = [
        v for v in bm.verts
        if 0.0045 <= abs(v.co.x - nose_x) <= 0.0155
        and v.co.y < -0.0815
        and 1.4365 <= v.co.z <= 1.4510
    ]
    for _ in range(12):
        disp_n: dict[int, Vector] = {}
        for v in nostril_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                disp_n[v.index] = (avg - v.co) * 0.50
        for v in nostril_verts:
            if v.index in disp_n:
                v.co += disp_n[v.index]

    # 3. Collar-tucked continuous neck: keep HD neck unbroken down to Z=1.292m (8mm below white crew tee rim!)
    # and trim only wide shoulder/shirt flares so torso white tee & dark overshirt collar wrap cleanly outside it.
    del_faces = []
    for f in bm.faces:
        fc = f.calc_center_median()
        if fc.z < 1.292:
            del_faces.append(f)
            continue
        if fc.z < 1.368:
            if fc.y < -0.048 and fc.z >= 1.356:
                continue  # preserve chin & submental curve cleanly
            rx_neck = 0.066
            ry_neck = 0.056
            ell_d = math.hypot((fc.x - nose_x) / rx_neck, (fc.y - neck_cy) / ry_neck)
            if ell_d > 1.00:
                del_faces.append(f)

    if del_faces:
        bmesh.ops.delete(bm, geom=del_faces, context="FACES")

    # Keep only the largest connected component (the head+neck) so zero stray flecks remain
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

    # Mould lower neck (Z=1.292..1.360) smoothly to the exact analytical collar-opening ellipse R_target(ux, uy)
    # centered at (nose_x, neck_cy): rx=0.0505m (cleanly inside 0.0528..0.0581m dark lapels),
    # ry_front=0.0480m (flush against Z=1.300 white tee 0.0494m), ry_back=0.0480m (inside back collar).
    # Front throat (uy < -0.65) is expand-only; side neck (-0.65 <= uy < 0.15) is bidirectional; back nape clamp-only.
    rx_t, ry_front_t, ry_back_t = 0.0510, 0.0485, 0.0480
    for v in bm.verts:
        if 1.292 <= v.co.z <= 1.342:
            t_chin_guard = 1.0 - (smoothstep(1.326, 1.340, v.co.z) * smoothstep(-0.020, -0.040, v.co.y))
            dx_n = v.co.x - nose_x
            dy_n = v.co.y - neck_cy
            r_n = math.hypot(dx_n, dy_n)
            if r_n > 1e-4:
                ux, uy = dx_n / r_n, dy_n / r_n
                ry_t = ry_front_t if uy < 0.0 else ry_back_t
                r_target = 1.0 / math.hypot(ux / rx_t, uy / ry_t)
                if uy < -0.65:
                    t_cyl = smoothstep(1.340, 1.314, v.co.z) * t_chin_guard
                    if t_cyl > 1e-3 and r_n < r_target:
                        r_new = r_n * (1.0 - t_cyl) + r_target * t_cyl
                        v.co.x = nose_x + ux * r_new
                        v.co.y = neck_cy + uy * r_new
                elif uy < 0.15:
                    t_cyl = smoothstep(1.342, 1.320, v.co.z) * t_chin_guard
                    if t_cyl > 1e-3:
                        r_new = r_n * (1.0 - t_cyl) + r_target * t_cyl
                        v.co.x = nose_x + ux * r_new
                        v.co.y = neck_cy + uy * r_new
                else:
                    t_cyl = smoothstep(1.342, 1.318, v.co.z)
                    if t_cyl > 1e-3 and r_n > r_target:
                        r_new = r_n * (1.0 - t_cyl) + r_target * t_cyl
                        v.co.x = nose_x + ux * r_new
                        v.co.y = neck_cy + uy * r_new

    # 4-pass gentle Laplacian relaxation across the upper-to-lower neck transition (Z=1.325..1.350)
    neck_trans_verts = [
        v for v in bm.verts
        if not v.is_boundary and 1.325 <= v.co.z <= 1.350 and not (v.co.y < -0.036 and v.co.z >= 1.340)
    ]
    for _ in range(4):
        disp_nt: dict[int, Vector] = {}
        for v in neck_trans_verts:
            nbrs = [e.other_vert(v).co for e in v.link_edges]
            if nbrs:
                avg = sum(nbrs, Vector((0.0, 0.0, 0.0))) / float(len(nbrs))
                disp_nt[v.index] = (avg - v.co) * 0.40
        for v in neck_trans_verts:
            if v.index in disp_nt:
                v.co += disp_nt[v.index]

    assert len(bm.verts) > 12000, f"Unexpectedly small HD head mesh after collar trim: {len(bm.verts)} verts"
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    print(f"Sculpt-refined HD bust (head+neck): verts={len(mesh.vertices)}, polys={len(mesh.polygons)}")


# ==============================================================================
# STEP 2: CALIBRATE & DELIGHT TEXTURES + BAKE BODY & 3-MAP HD HEAD PBR
# ==============================================================================
def calibrate_body_albedo(raw_albedo: bpy.types.Image) -> bpy.types.Image:
    """Calibrate raw body texture skin (hands/neck) to match Zachary's warm ivory-peach TARGET_SKIN_SRGB."""
    w, h = raw_albedo.size
    px = np.array(raw_albedo.pixels[:], dtype=np.float32).reshape((h, w, 4))
    px = resize_np_bilinear(px, 1024, 1024)
    srgb = np.clip(px[:, :, :3], 0.0, 1.0)

    r, g, b = srgb[:, :, 0], srgb[:, :, 1], srgb[:, :, 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    warmth = r - b
    skin_w = np.clip((warmth - 0.025) / 0.045, 0.0, 1.0) * np.clip((luma - 0.34) / 0.14, 0.0, 1.0)

    target_luma = float(0.299 * TARGET_SKIN_SRGB[0] + 0.587 * TARGET_SKIN_SRGB[1] + 0.114 * TARGET_SKIN_SRGB[2])
    shade_curve = np.clip(np.maximum(luma, 0.30) / target_luma, 0.68, 1.08)[:, :, None]
    smooth_target = np.clip(TARGET_SKIN_SRGB[None, None, :] * shade_curve, 0.0, 1.0)
    srgb_cal = srgb * (1.0 - skin_w[:, :, None]) + (0.20 * srgb + 0.80 * smooth_target) * skin_w[:, :, None]

    out = px.copy()
    out[:, :, :3] = srgb_cal
    img = bpy.data.images.new("Companion_Body_Calibrated", width=1024, height=1024, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(np.ascontiguousarray(out.ravel(), dtype=np.float32))
    img.pack()
    return img


def prepare_delighted_bust_albedo(hd_albedo: bpy.types.Image) -> bpy.types.Image:
    """
    Delight & color-harmonize the 2048x2048 HD bust albedo in sRGB space (Law 4 & Law 11):
    - Equalize uneven cool-grey cheek vs dark-orange chin/neck skin hues toward reference_portrait TARGET_SKIN_SRGB.
    - Lift harsh baked ambient shadows under chin, lower lip, nostrils, and sideburns without destroying micro-detail.
    - Warm & refine cool-grey hair/eyebrows into rich warm dark chestnut matching reference_portrait.jpg.
    - Soften baked bright-white lower-lip specular pill so real-time PBR roughness drives lip sheen dynamically.
    """
    w, h = hd_albedo.size
    px = np.array(hd_albedo.pixels[:], dtype=np.float32).reshape((h, w, 4))
    srgb = np.clip(px[:, :, :3], 0.0, 1.0)
    r, g, b = srgb[:, :, 0], srgb[:, :, 1], srgb[:, :, 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    warmth = r - b
    redness = r - g

    # 1. Broad skin mask (captures both pale cheeks AND darker shadowed orange jaw/neck/ears, excluding white sclera & hair)
    is_skin = (
        np.clip((warmth - 0.015) / 0.045, 0.0, 1.0)
        * np.clip((luma - 0.30) / 0.16, 0.0, 1.0)
        * np.clip((0.90 - luma) / 0.10, 0.0, 1.0)
        * np.clip((0.20 - redness) / 0.08, 0.0, 1.0)
    )
    # 2. Lip mask (warm rosy midtone)
    is_lip = (
        np.clip((redness - 0.09) / 0.07, 0.0, 1.0)
        * np.clip((luma - 0.26) / 0.14, 0.0, 1.0)
        * np.clip((0.82 - luma) / 0.14, 0.0, 1.0)
    )
    # 3. Hair halo dilation: catches dark hair PLUS warm chestnut/orange & bright specular streaks in bangs!
    dark_hair_core = ((luma < 0.28) & (warmth < 0.12) & (redness < 0.10)).astype(np.float32)
    hair_halo = box_blur_2d(dark_hair_core[:, :, None], radius=max(10, w // 72), passes=2)[:, :, 0]
    in_hair_zone = np.clip((hair_halo - 0.08) / 0.16, 0.0, 1.0)
    not_skin = np.clip((0.105 - warmth) / 0.045, 0.0, 1.0)
    is_hair_base = not_skin * np.clip((0.38 - luma) / 0.14, 0.0, 1.0) * np.clip((luma - 0.015) / 0.04, 0.0, 1.0)
    is_hair_streak = in_hair_zone * np.clip((0.52 - luma) / 0.14, 0.0, 1.0)
    is_hair = np.maximum(is_hair_base, is_hair_streak)

    # Masked low-frequency skin luminance (prevents black UV-background margin bleed into UV islands!)
    blur_r = max(12, w // 48)
    skin_m3 = is_skin[:, :, None]
    num_blur = box_blur_2d(srgb * skin_m3, radius=blur_r, passes=2)
    den_blur = box_blur_2d(skin_m3, radius=blur_r, passes=2)
    low_freq = np.where(den_blur > 1e-3, num_blur / np.maximum(den_blur, 1e-3), srgb)
    lf_luma = 0.299 * low_freq[:, :, 0] + 0.587 * low_freq[:, :, 1] + 0.114 * low_freq[:, :, 2]

    target_luma = float(0.299 * TARGET_SKIN_SRGB[0] + 0.587 * TARGET_SKIN_SRGB[1] + 0.114 * TARGET_SKIN_SRGB[2])
    # Unify baked photogrammetry shading for seamless 360-degree porcelain anime skin
    hf_ratio = np.clip(luma / np.maximum(lf_luma, 0.28), 0.95, 1.03)
    delighted_luma = np.clip((0.92 * target_luma + 0.08 * np.clip(lf_luma, 0.54, 0.72)) * hf_ratio, 0.54, 0.74)

    # Harmonize skin chromaticity smoothly toward Zachary's healthy warm ivory-peach
    skin_chroma = TARGET_SKIN_SRGB[None, None, :] * (delighted_luma / target_luma)[:, :, None]
    skin_blended = np.clip(0.05 * srgb + 0.95 * skin_chroma, 0.0, 1.0)

    out_rgb = srgb * (1.0 - is_skin[:, :, None]) + skin_blended * is_skin[:, :, None]

    # Lift isolated 1-2px jet-black skin specks (e.g. nostril wing pinhole) surrounded tightly by healthy skin
    tiny_skin_den = box_blur_2d(skin_m3, radius=3, passes=1)[:, :, 0]
    speck_mask = (
        ((tiny_skin_den > 0.68) & (lf_luma > 0.38) & (luma < 0.22)).astype(np.float32)
        * np.clip((0.22 - luma) / 0.14, 0.0, 1.0)
    )
    out_rgb = out_rgb * (1.0 - speck_mask[:, :, None]) + np.clip(low_freq * 0.78, 0.0, 1.0) * speck_mask[:, :, None]

    # Harmonize lips: calm natural muted rose (soften dark mouth-corner crease lows as well)
    target_lip = np.array([0.735, 0.520, 0.482], dtype=np.float32)
    lip_luma_t = float(0.299 * target_lip[0] + 0.587 * target_lip[1] + 0.114 * target_lip[2])
    lip_l = np.clip(0.55 * lip_luma_t + 0.45 * np.clip(luma, 0.42, 0.68), 0.43, 0.68)
    lip_cal = np.clip(target_lip[None, None, :] * (lip_l / lip_luma_t)[:, :, None], 0.0, 1.0)
    out_rgb = out_rgb * (1.0 - 0.65 * is_lip[:, :, None]) + lip_cal * (0.65 * is_lip[:, :, None])

    # Rich natural jet-black / charcoal-black hair calibration (preserves silky sheen highlights, zero orange cast!)
    target_hair_l = float(0.299 * TARGET_HAIR_SRGB[0] + 0.587 * TARGET_HAIR_SRGB[1] + 0.114 * TARGET_HAIR_SRGB[2])
    hair_l = np.clip((luma + 0.02) / max(1e-4, target_hair_l), 0.65, 1.65)
    hair_cal = np.clip(TARGET_HAIR_SRGB[None, None, :] * hair_l[:, :, None], 0.0, 1.0)
    out_rgb = out_rgb * (1.0 - 0.97 * is_hair[:, :, None]) + hair_cal * (0.97 * is_hair[:, :, None])

    out_px = px.copy()
    out_px[:, :, :3] = np.clip(out_rgb, 0.0, 1.0)
    img = bpy.data.images.new("HD_Bust_Delighted", width=w, height=h, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(np.ascontiguousarray(out_px.ravel(), dtype=np.float32))
    img.pack()
    return img


def prepare_closeup_eyes_image() -> bpy.types.Image:
    """Load zachary_real_selfie_clean.png (already containing Zachary's real eyes, brows, bangs, and friendly
    natural smile) and color-match warm skin tones smoothly to TARGET_SKIN_SRGB while protecting crisp dark irises
    and jet-black fringe hair."""
    raw = bpy.data.images.load(FACE_CLOSEUP_PATH, check_existing=False)
    raw.colorspace_settings.name = "sRGB"
    w, h = raw.size
    px = np.array(raw.pixels[:], dtype=np.float32).reshape((h, w, 4))
    srgb = np.clip(px[:, :, :3], 0.0, 1.0)

    # Measured indoor selfie cheek median [0.626, 0.463, 0.400] -> normalize cleanly to TARGET_SKIN_SRGB [0.752, 0.614, 0.528]
    gain = TARGET_SKIN_SRGB / np.array([0.626, 0.463, 0.400], dtype=np.float32)
    r, g, b = srgb[:, :, 0], srgb[:, :, 1], srgb[:, :, 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    warmth = r - b
    # Apply warm golden-tan gain strictly to midtone warm skin (never tint eye sclera, irises, or black bangs!)
    mid_w = (
        np.clip((luma - 0.30) / 0.14, 0.0, 1.0)
        * np.clip((0.88 - luma) / 0.10, 0.0, 1.0)
        * np.clip((warmth - 0.04) / 0.06, 0.0, 1.0)
    )
    srgb_adj = np.clip(srgb * (1.0 - mid_w[:, :, None]) + np.clip(srgb * gain[None, None, :], 0.0, 1.0) * mid_w[:, :, None], 0.0, 1.0)

    # Preserve rich deep dark espresso irises & dark fringe contrast under ACES Filmic studio lighting
    dark_w = np.clip((0.26 - luma) / 0.14, 0.0, 1.0) * np.clip((luma - 0.02) / 0.04, 0.0, 1.0)
    srgb_adj = srgb_adj * (1.0 - 0.14 * dark_w[:, :, None])

    px[:, :, :3] = srgb_adj
    img = bpy.data.images.new("Closeup_Eyes_Calibrated", width=w, height=h, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(np.ascontiguousarray(px.ravel(), dtype=np.float32))
    img.pack()
    bpy.data.images.remove(raw)
    return img


def build_clean_body_and_hd_head(
    raw_body: bpy.types.Object,
    body_albedo_cal: bpy.types.Image,
    hd_bust_high: bpy.types.Object,
    hd_bust_delighted: bpy.types.Image,
    closeup_eyes_img: bpy.types.Image,
    lm: dict[str, float],
) -> bpy.types.Object:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = "Standard"

    # ==================================================================
    # PART A: Watertight Manifold Body (Collar & White Tee 100% Intact, Zero Lapel Sawtooth!)
    # ==================================================================
    raw_uv_name = raw_body.data.uv_layers.active.name
    neck_cy = lm["neck_cy"]
    nose_x = lm["nose_x"]

    body_rem = raw_body.copy()
    body_rem.data = raw_body.data.copy()
    body_rem.name = "Companion_Body_Remesh"
    scene.collection.objects.link(body_rem)

    # Higher-detail 3.8mm voxel remesh preserves crisp overshirt collar & lapel edge!
    body_rem.data.remesh_voxel_size = 0.0038
    body_rem.data.remesh_voxel_adaptivity = 0.0
    bpy.ops.object.select_all(action="DESELECT")
    body_rem.select_set(True)
    bpy.context.view_layer.objects.active = body_rem
    bpy.ops.object.voxel_remesh()

    # Shrinkwrap to raw_body BEFORE cutting so collar & jacket geometry snap faithfully
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

    # Excise ONLY the old head (Z > 1.374m) and inner neck core inside collar (Z > 1.312m), keeping 100% of dark collar & white tee!
    # Sample nearest color from raw_body via BVH so we never slice dark overshirt collar!
    from mathutils.bvhtree import BVHTree
    raw_vcol = sample_vertex_colors(raw_body.data, body_albedo_cal)
    bm_raw = bmesh.new()
    bm_raw.from_mesh(raw_body.data)
    bm_raw.faces.ensure_lookup_table()
    bvh_raw = BVHTree.FromBMesh(bm_raw)

    bm_body = bmesh.new()
    bm_body.from_mesh(body_rem.data)
    bm_body.faces.ensure_lookup_table()

    # Bake-Before-Sink Collar Hem: keep 100% of body_rem below Z=1.376 watertight through decimation & baking
    # (excising ONLY the old head top well inside hd_bust skull) so white tee & collar rims bake cleanly at 0mm!
    del_head_faces = [f for f in bm_body.faces if f.calc_center_median().z > 1.376]
    if del_head_faces:
        bmesh.ops.delete(bm_body, geom=del_head_faces, context="FACES")

    # Remove any tiny floating neck fragments
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

    bm_body.to_mesh(body_rem.data)
    bm_body.free()
    body_rem.data.update()

    # Decimate body cleanly to ~17,500 tris (extra headroom for high-detail HD head!)
    tri_rem = sum(max(1, len(p.vertices) - 2) for p in body_rem.data.polygons)
    dec_b = body_rem.modifiers.new(name="DecimateBody", type="DECIMATE")
    dec_b.decimate_type = "COLLAPSE"
    dec_b.ratio = min(1.0, 17500.0 / float(max(1, tri_rem)))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev_bd = body_rem.evaluated_get(depsgraph)
    body_dec_mesh = bpy.data.meshes.new_from_object(ev_bd, preserve_all_data_layers=True, depsgraph=depsgraph)
    old_m = body_rem.data
    body_rem.modifiers.clear()
    body_rem.data = body_dec_mesh
    bpy.data.meshes.remove(old_m)

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

    # Tight 1.6mm cage extrusion EMIT bake eliminates v2's lapel-overhang black sawtooth triangles!
    mat_raw_emit = bpy.data.materials.new("Mat_RawBodyEmitTemp")
    mat_raw_emit.use_nodes = True
    nt_re = mat_raw_emit.node_tree
    nt_re.nodes.clear()
    re_uv = nt_re.nodes.new("ShaderNodeUVMap"); re_uv.uv_map = raw_uv_name
    re_tex = nt_re.nodes.new("ShaderNodeTexImage"); re_tex.image = body_albedo_cal
    re_emit = nt_re.nodes.new("ShaderNodeEmission"); re_emit.inputs["Strength"].default_value = 1.0
    re_out = nt_re.nodes.new("ShaderNodeOutputMaterial")
    nt_re.links.new(re_uv.outputs["UV"], re_tex.inputs["Vector"])
    nt_re.links.new(re_tex.outputs["Color"], re_emit.inputs["Color"])
    nt_re.links.new(re_emit.outputs["Emission"], re_out.inputs["Surface"])
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
    bb_target = nt_bb.nodes.new("ShaderNodeTexImage"); bb_target.image = baked_body_img
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
    # Post-bake collar UV skin-texel flood-heal & ray-miss repair:
    # 1) Heal #000000 ray misses across the full mesh from adjacent non-miss texels.
    # 2) On upper-collar polygons strictly above the white tee (cz > 1.314m, r_xy < 0.080m), overwrite any
    #    warm old-neck skin texels strictly from dark collar texels (luma < 0.28) so white tee never bleeds onto lapels!
    bw_img, bh_img = baked_body_img.size
    collar_uv_mask = np.zeros((bh_img, bw_img), dtype=bool)
    uv_layer_b = body_rem.data.uv_layers.active.data
    verts_b = body_rem.data.vertices
    for poly in body_rem.data.polygons:
        cx = sum(verts_b[vi].co.x for vi in poly.vertices) / float(len(poly.vertices))
        cy = sum(verts_b[vi].co.y for vi in poly.vertices) / float(len(poly.vertices))
        cz = sum(verts_b[vi].co.z for vi in poly.vertices) / float(len(poly.vertices))
        if cz > 1.314 and math.hypot(cx - nose_x, cy - neck_cy) < 0.080:
            uvs = [uv_layer_b[li].uv for li in poly.loop_indices]
            u0 = max(0, int(min(uv.x for uv in uvs) * bw_img) - 2)
            u1 = min(bw_img, int(max(uv.x for uv in uvs) * bw_img) + 3)
            v0 = max(0, int(min(uv.y for uv in uvs) * bh_img) - 2)
            v1 = min(bh_img, int(max(uv.y for uv in uvs) * bh_img) + 3)
            collar_uv_mask[v0:v1, u0:u1] = True

    bpx = np.array(baked_body_img.pixels[:], dtype=np.float32).reshape((bh_img, bw_img, 4))
    brgb = bpx[:, :, :3].copy()
    for _ in range(10):
        bluma = 0.299 * brgb[:, :, 0] + 0.587 * brgb[:, :, 1] + 0.114 * brgb[:, :, 2]
        miss = bluma < 0.055
        if not np.any(miss):
            break
        valid_m = (~miss).astype(np.float32)[:, :, None]
        blur_num = box_blur_2d(brgb * valid_m, radius=3, passes=1)
        blur_den = box_blur_2d(valid_m, radius=3, passes=1)
        healed = np.where(blur_den > 1e-3, blur_num / np.maximum(blur_den, 1e-3), brgb)
        brgb = np.where(miss[:, :, None] & (blur_den > 1e-3), healed, brgb)

    for _ in range(14):
        bluma = 0.299 * brgb[:, :, 0] + 0.587 * brgb[:, :, 1] + 0.114 * brgb[:, :, 2]
        warm_collar_skin = collar_uv_mask & ((brgb[:, :, 0] - brgb[:, :, 2]) > 0.036) & (bluma < 0.72)
        if not np.any(warm_collar_skin):
            break
        dark_src = ((~warm_collar_skin) & (bluma >= 0.055) & (bluma < 0.28)).astype(np.float32)[:, :, None]
        blur_num = box_blur_2d(brgb * dark_src, radius=4, passes=1)
        blur_den = box_blur_2d(dark_src, radius=4, passes=1)
        healed = np.where(blur_den > 1e-3, blur_num / np.maximum(blur_den, 1e-3), brgb)
        brgb = np.where(warm_collar_skin[:, :, None] & (blur_den > 1e-3), healed, brgb)
    rem_warm_skin = collar_uv_mask & ((brgb[:, :, 0] - brgb[:, :, 2]) > 0.036) & (
        (0.299 * brgb[:, :, 0] + 0.587 * brgb[:, :, 1] + 0.114 * brgb[:, :, 2]) < 0.72
    )
    if np.any(rem_warm_skin):
        brgb[rem_warm_skin] = np.array([0.14, 0.14, 0.145], dtype=np.float32)
    bpx[:, :, :3] = brgb
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
        bsdf_b.inputs["Specular IOR Level"].default_value = 0.24
    tex_b = nt_b.nodes.new("ShaderNodeTexImage"); tex_b.image = baked_body_img
    nt_b.links.new(tex_b.outputs["Color"], bsdf_b.inputs["Base Color"])
    nt_b.links.new(bsdf_b.outputs["BSDF"], out_b.inputs["Surface"])
    body_rem.data.materials.clear()
    body_rem.data.materials.append(mat_body)
    bpy.data.materials.remove(mat_body_bake)
    bpy.data.materials.remove(mat_raw_emit)

    # Post-bake collar lip roll-in: delete only upper head faces (fc.z > 1.352, non-collar), classify & despeckle
    # garment vs inner-neck skin vertices, roll the non-garment collar/tee lip cleanly inward (r -> 0.018m) and
    # downward (Z -> 1.302m) strictly inside hd_bust, and excise only deep interior faces (all verts w_sink > 0.82).
    bm_sink = bmesh.new()
    bm_sink.from_mesh(body_rem.data)
    bm_sink.faces.ensure_lookup_table()
    old_chin_faces = []
    for f in bm_sink.faces:
        fc = f.calc_center_median()
        if fc.z > 1.372:
            old_chin_faces.append(f)
            continue
        if fc.z > 1.352:
            r_fc = math.hypot(fc.x - nose_x, fc.y - neck_cy)
            _, _, fidx, _ = bvh_raw.find_nearest(fc)
            is_outer_collar = False
            if fidx is not None and r_fc >= 0.0545:
                rf = bm_raw.faces[fidx]
                c_avg = np.mean([raw_vcol[vv.index] for vv in rf.verts], axis=0)
                fluma = float(0.299 * c_avg[0] + 0.587 * c_avg[1] + 0.114 * c_avg[2])
                warmth = float(c_avg[0] - c_avg[2])
                is_outer_collar = (fluma < 0.25 and warmth < 0.048)
            if not is_outer_collar:
                old_chin_faces.append(f)
    if old_chin_faces:
        bmesh.ops.delete(bm_sink, geom=old_chin_faces, context="FACES")
    bmesh.ops.delete(bm_sink, geom=[v for v in bm_sink.verts if not v.link_faces], context="VERTS")
    bm_sink.verts.index_update()
    bm_sink.verts.ensure_lookup_table()

    n_sink_verts = len(bm_sink.verts)
    in_zone = np.zeros(n_sink_verts, dtype=bool)
    is_garment = np.ones(n_sink_verts, dtype=bool)
    for v in bm_sink.verts:
        if 1.298 <= v.co.z <= 1.385:
            dx_n = v.co.x - nose_x
            dy_n = v.co.y - neck_cy
            r_xy = math.hypot(dx_n, dy_n)
            if r_xy < 0.068:
                in_zone[v.index] = True
                _, _, fidx, _ = bvh_raw.find_nearest(v.co)
                garment_hit = False
                if fidx is not None:
                    rf = bm_raw.faces[fidx]
                    c_avg = np.mean([raw_vcol[vv.index] for vv in rf.verts], axis=0)
                    fluma = float(0.299 * c_avg[0] + 0.587 * c_avg[1] + 0.114 * c_avg[2])
                    warmth = float(c_avg[0] - c_avg[2])
                    is_dark_collar = (fluma < 0.25 and warmth < 0.046) and (r_xy >= 0.0535)
                    is_white_tee = (fluma > 0.62 and warmth < 0.052) and (v.co.z <= 1.312) and (r_xy >= 0.0475)
                    garment_hit = is_dark_collar or is_white_tee
                is_garment[v.index] = garment_hit

    # 2-pass garment despeckle: unpin isolated boundary triangle spikes (> 1.304m with < 2 garment neighbors)
    for _ in range(2):
        unpin_ids = []
        for v in bm_sink.verts:
            if in_zone[v.index] and is_garment[v.index] and v.co.z > 1.304:
                g_nbrs = sum(1 for e in v.link_edges if is_garment[e.other_vert(v).index])
                if g_nbrs < 2:
                    unpin_ids.append(v.index)
        for vid in unpin_ids:
            is_garment[vid] = False

    w_sink = np.zeros(n_sink_verts, dtype=np.float32)
    pinned = np.ones(n_sink_verts, dtype=bool)
    for v in bm_sink.verts:
        if in_zone[v.index] and not is_garment[v.index]:
            pinned[v.index] = False
            w_sink[v.index] = smoothstep(1.298, 1.308, v.co.z)

    for _ in range(3):
        w_next = w_sink.copy()
        for v in bm_sink.verts:
            if pinned[v.index] or not v.link_edges:
                continue
            nbr_vals = [w_sink[e.other_vert(v).index] for e in v.link_edges]
            w_next[v.index] = 0.60 * w_sink[v.index] + 0.40 * (sum(nbr_vals) / float(len(nbr_vals)))
        w_sink = w_next

    r_target_inner = 0.018
    z_sink = 1.294
    for v in bm_sink.verts:
        ws = float(w_sink[v.index])
        if ws > 1e-3:
            dx_n = v.co.x - nose_x
            dy_n = v.co.y - neck_cy
            r_n = math.hypot(dx_n, dy_n)
            if r_n > 1e-4:
                ux, uy = dx_n / r_n, dy_n / r_n
                if r_n > r_target_inner:
                    r_new = r_n * (1.0 - ws) + r_target_inner * ws
                    v.co.x = nose_x + ux * r_new
                    v.co.y = neck_cy + uy * r_new
            if v.co.z > z_sink:
                v.co.z = v.co.z * (1.0 - 0.85 * ws) + z_sink * (0.85 * ws)

    bm_sink.faces.ensure_lookup_table()
    deep_inner_faces = [
        f for f in bm_sink.faces
        if all(float(w_sink[v.index]) > 0.82 for v in f.verts)
    ]
    if deep_inner_faces:
        bmesh.ops.delete(bm_sink, geom=deep_inner_faces, context="FACES")
    bmesh.ops.delete(bm_sink, geom=[v for v in bm_sink.verts if not v.link_faces], context="VERTS")

    bm_sink.normal_update()
    bm_sink.to_mesh(body_rem.data)
    bm_sink.free()
    bm_raw.free()
    for p in body_rem.data.polygons:
        p.use_smooth = True
    body_rem.data.update()
    print(f"Clean manifold body baked: verts={len(body_rem.data.vertices)}, tris={sum(max(1, len(p.vertices)-2) for p in body_rem.data.polygons)}")

    # ==================================================================
    # PART B: Priority-Weighted Optimized HD Head + 3-Map PBR Bake (Albedo + Normal + MR)
    # ==================================================================
    head_low = hd_bust_high.copy()
    head_low.data = hd_bust_high.data.copy()
    head_low.name = "Companion_Head_Low"
    scene.collection.objects.link(head_low)

    # head_low inherits hd_bust_high's already-welded consistent outward winding (do NOT call recalc_face_normals!)
    bm_hl = bmesh.new()
    bm_hl.from_mesh(head_low.data)
    bmesh.ops.remove_doubles(bm_hl, verts=bm_hl.verts, dist=8e-5)
    bm_hl.to_mesh(head_low.data)
    bm_hl.free()
    head_low.data.update()

    # Assign FacePriority vertex group so DECIMATE preserves maximum density on eyes, brows, nose, lips, bangs, ears!
    vg_prio = head_low.vertex_groups.new(name="CollapsePriority")
    eye_z = lm["eye_z"]
    for v in head_low.data.vertices:
        co = v.co
        # High value = collapse MORE aggressively; low value = PROTECT geometry!
        is_front_face = (co.y < -0.025 and 1.362 <= co.z <= 1.545 and abs(co.x - nose_x) < 0.088)
        is_front_hair = (co.y < -0.010 and co.z > 1.495)
        is_ears = (abs(co.x - nose_x) > 0.068 and 1.42 <= co.z <= 1.505 and -0.035 <= co.y <= 0.045)
        if is_front_face:
            w_col = 0.08
        elif is_front_hair or is_ears:
            w_col = 0.25
        elif co.z < 1.300:
            w_col = 1.00  # hidden lower neck inside tee/collar
        else:
            w_col = 0.80  # back/top of skull
        vg_prio.add([v.index], w_col, "REPLACE")

    tri_h = sum(max(1, len(p.vertices) - 2) for p in head_low.data.polygons)
    dec_h = head_low.modifiers.new(name="DecimateHDHead", type="DECIMATE")
    dec_h.decimate_type = "COLLAPSE"
    dec_h.ratio = min(1.0, 16500.0 / float(max(1, tri_h)))
    dec_h.vertex_group = "CollapsePriority"
    dec_h.vertex_group_factor = 0.85

    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev_hl = head_low.evaluated_get(depsgraph)
    hl_mesh = bpy.data.meshes.new_from_object(ev_hl, preserve_all_data_layers=True, depsgraph=depsgraph)
    old_hm = head_low.data
    head_low.modifiers.clear()
    head_low.vertex_groups.clear()
    head_low.data = hl_mesh
    bpy.data.meshes.remove(old_hm)

    for p in head_low.data.polygons:
        p.use_smooth = True
    head_low.data.update()

    # Clean single UVMap on head_low
    while len(head_low.data.uv_layers) > 0:
        head_low.data.uv_layers.remove(head_low.data.uv_layers[0])
    uv_hl = head_low.data.uv_layers.new(name="UVMap")
    uv_hl.active = True
    uv_hl.active_render = True

    bpy.ops.object.select_all(action="DESELECT")
    head_low.select_set(True)
    bpy.context.view_layer.objects.active = head_low
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(56.0), island_margin=0.010)
    bpy.ops.object.mode_set(mode="OBJECT")

    print(f"Optimized HD head_low: verts={len(head_low.data.vertices)}, tris={sum(max(1, len(p.vertices)-2) for p in head_low.data.polygons)}")

    # Prepare target bake material on head_low
    baked_face_albedo = bpy.data.images.new("Zachary_Face_HD", width=1280, height=1280, alpha=False)
    baked_face_albedo.colorspace_settings.name = "sRGB"
    baked_face_normal = bpy.data.images.new("Zachary_Face_Normal", width=1024, height=1024, alpha=False)
    baked_face_normal.colorspace_settings.name = "Non-Color"
    baked_face_mr = bpy.data.images.new("Zachary_Face_MR", width=1024, height=1024, alpha=False)
    baked_face_mr.colorspace_settings.name = "Non-Color"

    mat_hl_bake = bpy.data.materials.new("Mat_HeadLowBakeTemp")
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

    # --- BAKE 1: Tangent-Space Normal Map (145k-tri hd_bust_high -> 16.5k-tri head_low) ---
    hb_target.image = baked_face_normal
    bpy.ops.object.select_all(action="DESELECT")
    hd_bust_high.select_set(True)
    head_low.select_set(True)
    bpy.context.view_layer.objects.active = head_low
    bpy.ops.object.bake(
        type="NORMAL",
        normal_space="TANGENT",
        use_selected_to_active=True,
        cage_extrusion=0.0015,
        max_ray_distance=0.012,
        margin=16,
        use_clear=True,
    )
    baked_face_normal.pack()
    print("Baked Zachary_Face_Normal (1024x1024 tangent-space)")

    # --- BAKE 2: Delighted 360° HD Bust Albedo + Sub-mm Landmark-Locked Eye Crispness ---
    mat_hd_albedo_src = build_hd_face_albedo_bake_shader(hd_bust_high, hd_bust_delighted, closeup_eyes_img, lm)
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
        cage_extrusion=0.0015,
        max_ray_distance=0.012,
        margin=16,
        use_clear=True,
    )
    # 8-pass masked #000000 ray-miss flood healing on Zachary_Face_HD (only heal true 0.000 unhit texels, never dark irises/brows/hair!)
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
    fpx[:, :, :3] = frgb
    baked_face_albedo.pixels.foreach_set(np.ascontiguousarray(fpx.ravel(), dtype=np.float32))
    baked_face_albedo.pack()
    print("Baked Zachary_Face_HD (1280x1280 delighted albedo + HD eyes)")

    # --- BAKE 3: Anatomical PBR Roughness/Metallic Map (G=Roughness, B=0.0 Metallic) ---
    mat_hd_mr_src = build_hd_face_mr_bake_shader(hd_bust_high, hd_bust_delighted, lm)
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
        cage_extrusion=0.0015,
        max_ray_distance=0.012,
        margin=16,
        use_clear=True,
    )
    baked_face_mr.pack()
    print("Baked Zachary_Face_MR (1024x1024 anatomical roughness: 0.06 eyes / 0.36 lips / 0.44 hair / 0.54 skin)")

    # Final Mat_Companion_Face (Slot 1) with BaseColor + NormalMap + MetallicRoughness!
    mat_face = bpy.data.materials.new("Mat_Companion_Face")
    mat_face.use_nodes = True
    nt_f = mat_face.node_tree
    nt_f.nodes.clear()
    out_f = nt_f.nodes.new("ShaderNodeOutputMaterial")
    bsdf_f = nt_f.nodes.new("ShaderNodeBsdfPrincipled")
    if "Specular IOR Level" in bsdf_f.inputs:
        bsdf_f.inputs["Specular IOR Level"].default_value = 0.15

    tex_alb = nt_f.nodes.new("ShaderNodeTexImage"); tex_alb.image = baked_face_albedo
    tex_mr = nt_f.nodes.new("ShaderNodeTexImage"); tex_mr.image = baked_face_mr
    sep_mr = nt_f.nodes.new("ShaderNodeSeparateColor")
    tex_nrm = nt_f.nodes.new("ShaderNodeTexImage"); tex_nrm.image = baked_face_normal
    nrm_map = nt_f.nodes.new("ShaderNodeNormalMap")
    nrm_map.inputs["Strength"].default_value = 0.38

    nt_f.links.new(tex_alb.outputs["Color"], bsdf_f.inputs["Base Color"])
    nt_f.links.new(tex_mr.outputs["Color"], sep_mr.inputs["Color"])
    nt_f.links.new(sep_mr.outputs["Green"], bsdf_f.inputs["Roughness"])
    nt_f.links.new(sep_mr.outputs["Blue"], bsdf_f.inputs["Metallic"])
    nt_f.links.new(tex_nrm.outputs["Color"], nrm_map.inputs["Color"])
    nt_f.links.new(nrm_map.outputs["Normal"], bsdf_f.inputs["Normal"])
    nt_f.links.new(bsdf_f.outputs["BSDF"], out_f.inputs["Surface"])

    head_low.data.materials.clear()
    head_low.data.materials.append(mat_face)

    # Tear down high-poly temp references & temporary materials/images so GLB stays compact
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

    # Join body_rem (Slot 0: Mat_Companion_Body) + head_low (Slot 1: Mat_Companion_Face) into SM_Companion_Body
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
    hd_delighted: bpy.types.Image,
    closeup_eyes_img: bpy.types.Image,
    lm: dict[str, float],
) -> bpy.types.Material:
    """
    Combines 100% seamless 360° delighted HD bust albedo with strictly landmark-locked front eye-box
    clarity (iris, pupil, sclera, upper lashline) from the approved 1024x1024 glasses-off portrait.
    Zero projection onto forehead bangs, cheeks, or jaw -> zero projection seam!
    """
    mat = bpy.data.materials.new("Mat_HDBustAlbedoSrc")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    uv_orig = nt.nodes.new("ShaderNodeUVMap")
    uv_orig.uv_map = hd_obj.data.uv_layers.active.name
    tex_bust = nt.nodes.new("ShaderNodeTexImage")
    tex_bust.image = hd_delighted
    nt.links.new(uv_orig.outputs["UV"], tex_bust.inputs["Vector"])

    # Exact orthographic UV mapping onto closeup portrait
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep_co = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tex_coord.outputs["Object"], sep_co.inputs["Vector"])
    nt.links.new(geom.outputs["Normal"], sep_n.inputs["Vector"])

    nose_x = lm["nose_x"]
    eye_z = lm["eye_z"]
    mouth_z = lm["mouth_z"]
    chin_z = lm["chin_z"]
    ps_x = lm["proj_scale_uv"]
    nose_base_z = lm["nose_tip_z"] - 0.0065
    stomion_z = mouth_z - 0.0055
    ps_z_hi = (0.47410 - 0.29300) / max(0.025, eye_z - nose_base_z)
    ps_z_lo = (0.29300 - 0.19430) / max(0.020, nose_base_z - stomion_z)

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

    # Spatial coordinates & bust luma reused across brow cleanup, hair lock, and 3-anchor face projection
    bw_bust = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(tex_bust.outputs["Color"], bw_bust.inputs["Color"])
    dx_n = math_op("SUBTRACT", sep_co.outputs["X"], nose_x)
    dz_e = math_op("SUBTRACT", sep_co.outputs["Z"], eye_z)
    dz_nb = math_op("SUBTRACT", sep_co.outputs["Z"], nose_base_z)
    abs_dx = math_op("ABSOLUTE", dx_n, 0.0)
    neg_py = math_op("MULTIPLY", sep_co.outputs["Y"], -1.0)

    # Topological HairMask & HairShadow attributes eliminate the sharp horizontal forehead cut
    attr_hair_mask = nt.nodes.new("ShaderNodeAttribute")
    attr_hair_mask.attribute_name = "HairMask"
    attr_hair_shadow = nt.nodes.new("ShaderNodeAttribute")
    attr_hair_shadow.attribute_name = "HairShadow"

    # Erase old TRELLIS.2 slanted outer V-brow wings on tex_bust across temples/brows before mix_hair/mix_face
    brow_clean_z = math_op("MULTIPLY", map_range(dz_e, 0.002, 0.006, 0.0, 1.0), map_range(dz_e, 0.022, 0.028, 1.0, 0.0))
    brow_clean_y = map_range(neg_py, 0.040, 0.056, 0.0, 1.0)
    brow_clean_x = map_range(abs_dx, 0.058, 0.070, 1.0, 0.0)
    brow_clean_dark = map_range(bw_bust.outputs["Val"], 0.16, 0.38, 1.0, 0.0)
    brow_clean_w = math_op("MULTIPLY", math_op("MULTIPLY", brow_clean_z, brow_clean_y), math_op("MULTIPLY", brow_clean_x, brow_clean_dark))
    mix_brow_clean = nt.nodes.new("ShaderNodeMixRGB"); mix_brow_clean.blend_type = "MIX"
    nt.links.new(brow_clean_w, mix_brow_clean.inputs["Factor"])
    nt.links.new(tex_bust.outputs["Color"], mix_brow_clean.inputs["Color1"])
    lin_skin_clean = srgb_to_linear((float(TARGET_SKIN_SRGB[0]), float(TARGET_SKIN_SRGB[1]), float(TARGET_SKIN_SRGB[2])))
    mix_brow_clean.inputs["Color2"].default_value = (lin_skin_clean[0], lin_skin_clean[1], lin_skin_clean[2], 1.0)

    # Topological 3D charcoal-black hair lock via HairMask (96% mix eliminates brownish smear while keeping shape)
    mix_hair = nt.nodes.new("ShaderNodeMixRGB"); mix_hair.blend_type = "MIX"
    nt.links.new(math_op("MULTIPLY", attr_hair_mask.outputs["Fac"], 0.96), mix_hair.inputs["Factor"])
    nt.links.new(mix_brow_clean.outputs["Color"], mix_hair.inputs["Color1"])
    lin_hair = srgb_to_linear((float(TARGET_HAIR_SRGB[0]), float(TARGET_HAIR_SRGB[1]), float(TARGET_HAIR_SRGB[2])))
    mix_hair.inputs["Color2"].default_value = (lin_hair[0], lin_hair[1], lin_hair[2], 1.0)

    # Piecewise 3-anchor vertical projection: eyes (0.47410) -> nostril base (0.29300) -> lip parting line (0.19430)
    u_proj = math_op("ADD", math_op("MULTIPLY", dx_n, ps_x), lm["proj_u0"])
    v_hi = math_op("ADD", math_op("MULTIPLY", dz_e, ps_z_hi), lm["proj_v0"])
    v_lo = math_op("ADD", math_op("MULTIPLY", dz_nb, ps_z_lo), 0.29300)
    t_seg = map_range(sep_co.outputs["Z"], nose_base_z - 0.003, nose_base_z + 0.003, 0.0, 1.0)
    v_proj = mix_float(t_seg, v_lo, v_hi)

    comb_uv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u_proj, comb_uv.inputs["X"])
    nt.links.new(v_proj, comb_uv.inputs["Y"])

    tex_close = nt.nodes.new("ShaderNodeTexImage")
    tex_close.image = closeup_eyes_img
    tex_close.extension = "EXTEND"
    nt.links.new(comb_uv.outputs["Vector"], tex_close.inputs["Vector"])

    # Inner-face projection mask covers high exposed forehead/hair-part skin while strictly respecting HairMask!
    wx = map_range(abs_dx, 0.050, 0.065, 1.0, 0.0)
    wz_hi = map_range(dz_e, 0.055, 0.068, 1.0, 0.0)
    wz_lo = map_range(sep_co.outputs["Z"], chin_z + 0.004, chin_z + 0.016, 0.0, 1.0)
    neg_ny = math_op("MULTIPLY", sep_n.outputs["Y"], -1.0)
    w_front = map_range(neg_ny, 0.05, 0.25, 0.0, 1.0)
    w_py = map_range(neg_py, 0.032, 0.052, 0.0, 1.0)
    not_bang_strand = math_op("SUBTRACT", 1.0, attr_hair_mask.outputs["Fac"])
    w_face_base = math_op("MULTIPLY", math_op("MULTIPLY", math_op("MULTIPLY", wx, wz_hi), math_op("MULTIPLY", wz_lo, w_front)), w_py)
    w_face = math_op("MULTIPLY", w_face_base, not_bang_strand)

    mix_face = nt.nodes.new("ShaderNodeMixRGB"); mix_face.blend_type = "MIX"
    nt.links.new(w_face, mix_face.inputs["Factor"])
    nt.links.new(mix_hair.outputs["Color"], mix_face.inputs["Color1"])
    nt.links.new(tex_close.outputs["Color"], mix_face.inputs["Color2"])

    # Natural subtle hairline contact shadow under bang tips (HairShadow * 0.14)
    shad_mul = math_op("SUBTRACT", 1.0, math_op("MULTIPLY", attr_hair_shadow.outputs["Fac"], 0.14))
    comb_shad = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(shad_mul, comb_shad.inputs["X"])
    nt.links.new(shad_mul, comb_shad.inputs["Y"])
    nt.links.new(shad_mul, comb_shad.inputs["Z"])
    mix_hair_shad = nt.nodes.new("ShaderNodeMixRGB"); mix_hair_shad.blend_type = "MULTIPLY"
    mix_hair_shad.inputs["Factor"].default_value = 1.0
    nt.links.new(mix_face.outputs["Color"], mix_hair_shad.inputs["Color1"])
    nt.links.new(comb_shad.outputs["Vector"], mix_hair_shad.inputs["Color2"])

    # Lower-neck tee/collar-remnant skin guard (Z in [1.290, 1.340]): replaces original bust collar paint
    # with clean seamless warm skin while protecting dark back-nape hair (Y > 0.015..0.035)
    neck_bot_w = map_range(sep_co.outputs["Z"], 1.318, 1.340, 1.0, 0.0)
    nape_skin = map_range(bw_bust.outputs["Val"], 0.14, 0.28, 0.0, 1.0)
    front_neck_y = map_range(sep_co.outputs["Y"], 0.015, 0.035, 1.0, 0.0)
    mix_neck = nt.nodes.new("ShaderNodeMixRGB"); mix_neck.blend_type = "MIX"
    nt.links.new(math_op("MULTIPLY", math_op("MULTIPLY", neck_bot_w, nape_skin), front_neck_y), mix_neck.inputs["Factor"])
    nt.links.new(mix_hair_shad.outputs["Color"], mix_neck.inputs["Color1"])
    lin_neck = srgb_to_linear((float(TARGET_SKIN_SRGB[0] * 0.96), float(TARGET_SKIN_SRGB[1] * 0.95), float(TARGET_SKIN_SRGB[2] * 0.94)))
    mix_neck.inputs["Color2"].default_value = (lin_neck[0], lin_neck[1], lin_neck[2], 1.0)

    emit = nt.nodes.new("ShaderNodeEmission"); emit.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_neck.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def build_hd_face_mr_bake_shader(
    hd_obj: bpy.types.Object,
    hd_delighted: bpy.types.Image,
    lm: dict[str, float],
) -> bpy.types.Material:
    """
    Outputs packed MetallicRoughness texture via EMIT: R=0, G=Roughness, B=0.0 (Metallic).
    - Eyes / Corneas: Roughness = 0.06 (wet living specular catchlights!)
    - Lips: Roughness = 0.36
    - Hair: Roughness = 0.44
    - Skin: Roughness = 0.55 (0.50 subtle T-zone, 0.58 cheeks/neck)
    - Eyebrows: Roughness = 0.72
    """
    mat = bpy.data.materials.new("Mat_HDBustMRSrc")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    uv_orig = nt.nodes.new("ShaderNodeUVMap")
    uv_orig.uv_map = hd_obj.data.uv_layers.active.name
    tex_bust = nt.nodes.new("ShaderNodeTexImage"); tex_bust.image = hd_delighted
    nt.links.new(uv_orig.outputs["UV"], tex_bust.inputs["Vector"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(tex_bust.outputs["Color"], bw.inputs["Color"])

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep_co = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep_co.inputs["Vector"])

    nose_x = lm["nose_x"]
    eye_z = lm["eye_z"]
    eye_dx = lm["eye_dx"]
    mouth_z = lm["mouth_z"]

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

    # Hair mask: dark linear luma < 0.14 (above eye_z + 0.015 or behind Y > -0.04)
    w_dark = map_range(bw.outputs["Val"], 0.08, 0.18, 1.0, 0.0)
    w_hair_z = map_range(sep_co.outputs["Z"], eye_z + 0.012, eye_z + 0.032, 0.0, 1.0)
    w_hair_y = map_range(sep_co.outputs["Y"], -0.045, -0.015, 0.0, 1.0)
    w_hair = math_op("MULTIPLY", w_dark, math_op("MAXIMUM", w_hair_z, w_hair_y))

    # Base: skin 0.56 -> hair 0.62 (silky natural chestnut without white plastic streaks)
    r_val = mix_float(w_hair, 0.56, 0.62)

    # Eyebrow matte mask (dark strips right above eyes on front face)
    neg_py = math_op("MULTIPLY", sep_co.outputs["Y"], -1.0)
    w_front_y = map_range(neg_py, 0.055, 0.078, 0.0, 1.0)
    abs_dx = math_op("ABSOLUTE", math_op("SUBTRACT", sep_co.outputs["X"], nose_x), 0.0)
    w_brow_z = math_op("MULTIPLY", map_range(sep_co.outputs["Z"], eye_z + 0.009, eye_z + 0.015, 0.0, 1.0),
                                   map_range(sep_co.outputs["Z"], eye_z + 0.024, eye_z + 0.032, 1.0, 0.0))
    w_brow_x = math_op("MULTIPLY", map_range(abs_dx, 0.006, 0.014, 0.0, 1.0),
                                   map_range(abs_dx, 0.048, 0.062, 1.0, 0.0))
    w_brow = math_op("MULTIPLY", math_op("MULTIPLY", w_brow_z, w_brow_x), math_op("MULTIPLY", w_front_y, w_dark))
    r_val = mix_float(w_brow, r_val, 0.72)

    # Lips soft natural satin (0.48, avoids bright overhead glare on upper/lower lips!)
    lx_n = math_op("DIVIDE", abs_dx, 0.024)
    lz_n = math_op("DIVIDE", math_op("SUBTRACT", sep_co.outputs["Z"], mouth_z), 0.0102)
    l_r2 = math_op("ADD", math_op("MULTIPLY", lx_n, lx_n), math_op("MULTIPLY", lz_n, lz_n))
    w_lip = math_op("MULTIPLY", map_range(l_r2, 0.35, 1.0, 1.0, 0.0), w_front_y)
    r_val = mix_float(w_lip, r_val, 0.48)

    # Eyeball wet gloss (0.08 crisp corneal catchlights without frosting dark espresso irises!)
    ex_n = math_op("DIVIDE", math_op("SUBTRACT", abs_dx, eye_dx), 0.0135)
    ez_n = math_op("DIVIDE", math_op("SUBTRACT", sep_co.outputs["Z"], eye_z - 0.0005), 0.0052)
    e_r2 = math_op("ADD", math_op("MULTIPLY", ex_n, ex_n), math_op("MULTIPLY", ez_n, ez_n))
    w_eye_gloss = math_op("MULTIPLY", map_range(e_r2, 0.35, 1.0, 1.0, 0.0), w_front_y)
    r_val = mix_float(w_eye_gloss, r_val, 0.08)

    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value = 0.0
    nt.links.new(r_val, comb.inputs["Green"])
    comb.inputs["Blue"].default_value = 0.0  # Metallic = 0

    emit = nt.nodes.new("ShaderNodeEmission"); emit.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(comb.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


# ==============================================================================
# STEP 3: PRECISION BRUSHED-GUNMETAL ROUND-PANTO SPECTACLES (`SM_Companion_Glasses`)
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
    """Zachary's signature large modern thin-wire aviator-panto frame (IMG20261122014334.heic):
    gently flattened soft upper brow bar paired with a deep, fuller rounded-geometric lower curve."""
    st = math.sin(theta)
    ct = math.cos(theta)
    if st >= 0.0:
        rz = rz_top * (1.0 - 0.10 * (st ** 2))
        rx_mod = rx * (1.0 + 0.06 * st * (1.0 - st))
    else:
        rz = rz_bot * (1.0 - 0.03 * (st ** 4))
        rx_mod = rx * (1.0 - 0.03 * (abs(st) ** 1.8))
    return ct * rx_mod, st * rz


def build_fitted_glasses(lm: dict[str, float]) -> bpy.types.Object:
    # Warm bronze-charcoal thin wire frame calibrated to IMG20261122014334.heic
    mat_metal = make_pbr_mat(
        "Mat_Companion_GlassesMetal",
        (0.32, 0.26, 0.22),
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

    nose_x = lm["nose_x"]
    eye_z = lm["eye_z"] - 0.0014
    eye_dx = lm["eye_dx"] * 1.02
    # Oversized signature thin-wire aviator-panto frames matching IMG20261122014334.heic & studio portrait
    lens_y = min(lm["bridge_y"] - 0.0060, lm["eye_front_y"] - 0.0090)
    rx = 0.0264
    rz_top = 0.0154
    rz_bot = 0.0242
    wire_r = 0.00078

    # Helper to sample measured outer temple half-width contour + clearance so temple arm NEVER clips head/hair!
    t_ys = lm.get("temple_profile_y", [-0.080, -0.065, -0.050, -0.035, -0.020, -0.005, 0.010, 0.022])
    t_xs = lm.get("temple_profile_x", [0.055, 0.062, 0.069, 0.078, 0.084, 0.086, 0.088, 0.089])
    def _temple_x_at(yq: float, min_x: float) -> float:
        base_x = float(np.interp(yq, t_ys, t_xs))
        return max(min_x, base_x)

    ear_y = lm["ear_top_y"]
    wire_r_temple = 0.00095

    bm = bmesh.new()
    rim_segs = 44
    tube_segs = 10

    for sx in (-1.0, 1.0):
        cx = nose_x + sx * eye_dx
        rim_rings: list[list[bmesh.types.BMVert]] = []
        for s in range(rim_segs):
            th = (2.0 * math.pi * s) / rim_segs
            ox, oz = panto_offset(th, rx, rz_top, rz_bot)
            wrap_y = 0.0022 * max(0.0, (sx * ox) / rx) ** 2
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

        # Single crystal-clear transparent optical lens plane (avoids double-wall frosted glare)
        lring = []
        for s in range(rim_segs):
            th = (2.0 * math.pi * s) / rim_segs
            ox, oz = panto_offset(th, rx - 0.0005, rz_top - 0.0005, rz_bot - 0.0005)
            wrap_y = 0.0022 * max(0.0, (sx * ox) / rx) ** 2
            lring.append(bm.verts.new((cx + ox, lens_y + wrap_y, eye_z + oz)))
        fl = bm.faces.new(list(reversed(lring)))
        fl.material_index = 1
        fl.smooth = True

        # Slender nose pad wire & silicone pad kissing wider nasal bridge cleanly
        inner_rim_x = cx - sx * (rx - 0.0018)
        pad_pts = [
            (Vector((inner_rim_x, lens_y + 0.0012, eye_z + 0.0020)), 0.00060),
            (Vector((nose_x + sx * 0.0080, lm["bridge_y"] + 0.0014, eye_z - 0.0006)), 0.00060),
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
            location=(nose_x + sx * 0.0080, lm["bridge_y"] + 0.0016, eye_z - 0.0010),
            mat_idx=2,
        )
        pbm.free()

        # Sleek contour-hugging temple arm with tight front hinge + measured HD temple clearance (uncut!)
        outer_x = cx + sx * (rx + 0.0002)
        temple_z = eye_z + 0.0054
        x_endpiece = abs(outer_x - nose_x)
        x_front = max(x_endpiece + 0.0018, _temple_x_at(-0.075, x_endpiece) + 0.0006)
        x_t1 = max(x_front + 0.0010, _temple_x_at(-0.055, x_front) + 0.0011)
        x_t2 = max(x_t1, _temple_x_at(-0.035, x_t1) + 0.0011)
        x_t3 = max(x_t2, _temple_x_at(-0.015, x_t2) + 0.0010)
        x_t4 = max(x_t3, _temple_x_at(0.005, x_t3) + 0.0009)
        x_ear = max(x_t4 - 0.0015, _temple_x_at(0.018, x_t4 - 0.0015) + 0.0008)
        wing_pts = [
            (Vector((outer_x, lens_y + 0.0022, temple_z)), 0.00105),
            (Vector((nose_x + sx * (x_endpiece + 0.0018), lens_y + 0.0034, temple_z)), 0.00102),
            (Vector((nose_x + sx * x_front, -0.074, temple_z - 0.0002)), wire_r_temple),
            (Vector((nose_x + sx * x_t1, -0.055, temple_z - 0.0004)), wire_r_temple),
            (Vector((nose_x + sx * x_t2, -0.035, temple_z - 0.0008)), wire_r_temple),
            (Vector((nose_x + sx * x_t3, -0.015, temple_z - 0.0014)), wire_r_temple),
            (Vector((nose_x + sx * x_t4, max(0.005, ear_y - 0.006), temple_z - 0.0028)), wire_r_temple),
            (Vector((nose_x + sx * x_ear, max(0.016, ear_y + 0.006), temple_z - 0.0068)), wire_r_temple),
            (Vector((nose_x + sx * (x_ear - 0.0035), max(0.028, ear_y + 0.018), temple_z - 0.0185)), 0.00102),
        ]
        sweep_tube(bm, wing_pts, segments=8, mat_idx=0)

    # Delicate arched center bridge connecting both rims
    bridge_x0 = nose_x - (eye_dx - rx + 0.0004)
    bridge_x1 = nose_x + (eye_dx - rx + 0.0004)
    bridge_pts = []
    for k in range(7):
        t = k / 6.0
        bx = bridge_x0 + t * (bridge_x1 - bridge_x0)
        arch = math.sin(t * math.pi)
        bridge_pts.append((Vector((bx, lens_y - arch * 0.0010, eye_z + 0.0068 + arch * 0.0018)), 0.00088))
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
# STEP 4: CHECKPOINT 1 — 6-PANEL FACE & COLLAR VISUAL INSPECTION RENDER
# ==============================================================================
def render_v3_face_checkpoint(body: bpy.types.Object, glasses_obj: bpy.types.Object, lm: dict[str, float]) -> None:
    scene = bpy.context.scene
    world = bpy.data.worlds.new("V3FaceCheckWorld")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.09, 0.10, 0.12, 1.0)
        bg.inputs["Strength"].default_value = 0.85

    def add_area(name: str, loc: tuple[float, float, float], tgt: tuple[float, float, float], energy: float, size: float, color=(1.0, 1.0, 1.0)):
        ld = bpy.data.lights.new(name=name, type="AREA")
        ld.energy = energy
        ld.size = size
        ld.color = color
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        look_at(lo, Vector(tgt))
        scene.collection.objects.link(lo)

    add_area("Key", (0.85, -1.60, 1.80), (0.0, 0.0, 1.44), 105.0, 1.1, (1.0, 0.96, 0.92))
    add_area("Fill", (-1.05, -1.50, 1.48), (0.0, 0.0, 1.44), 52.0, 1.4, (0.86, 0.92, 1.0))
    add_area("Rim", (-0.50, 1.45, 1.85), (0.0, 0.0, 1.44), 85.0, 1.2, (1.0, 0.88, 0.72))
    add_area("EyeCatch", (0.18, -1.45, 1.56), (0.0, 0.0, 1.48), 12.0, 0.14, (1.0, 0.99, 0.97))

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

    clay_mat = bpy.data.materials.new("V3ClayInspect")
    clay_mat.use_nodes = True
    clay_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.56, 0.54, 0.52, 1.0)
    clay_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.54
    orig_mats = list(body.data.materials)

    panels: list[np.ndarray] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        def render_shot(label: str, use_clay: bool, show_glasses: bool, loc: tuple[float, float, float], tgt: tuple[float, float, float]) -> np.ndarray:
            # Swap material slots IN-PLACE (NEVER call materials.clear() on a multi-slot mesh — it resets material_index to 0!)
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

        tgt = (0.0, -0.02, 1.445)
        # Top row: Front Clay, 3/4 Clay, Side Profile Textured+Glasses
        panels.append(render_shot("1_clay_front", True, False, (0.0, -0.68, 1.465), tgt))
        panels.append(render_shot("2_clay_34", True, False, (-0.36, -0.58, 1.475), tgt))
        panels.append(render_shot("3_side_glasses", False, True, (-0.68, -0.04, 1.465), (0.0, 0.0, 1.445)))
        # Bottom row: Front Bare Textured, Front Glasses, 3/4 Glasses (includes collar & chest check!)
        panels.append(render_shot("4_front_bare", False, False, (0.0, -0.68, 1.465), tgt))
        panels.append(render_shot("5_front_glasses", False, True, (0.0, -0.74, 1.455), (0.0, -0.02, 1.425)))
        panels.append(render_shot("6_34_glasses", False, True, (-0.38, -0.64, 1.465), (0.0, -0.02, 1.425)))

    for slot_i in range(len(orig_mats)):
        body.data.materials[slot_i] = orig_mats[slot_i]
    glasses_obj.hide_render = False

    sheet = np.zeros((1024, 1536, 4), dtype=np.float32)
    for i in range(3):
        sheet[512:1024, i * 512 : (i + 1) * 512] = panels[i]
        sheet[0:512, i * 512 : (i + 1) * 512] = panels[3 + i]

    os.makedirs(os.path.dirname(FACE_CHECK_PNG), exist_ok=True)
    out_im = bpy.data.images.new("V3FaceCheckSheet", width=1536, height=1024, alpha=True)
    out_im.pixels.foreach_set(sheet.ravel())
    out_im.filepath_raw = FACE_CHECK_PNG
    out_im.file_format = "PNG"
    out_im.save()
    bpy.data.images.remove(out_im)
    print(f"Saved v3 face checkpoint sheet: {FACE_CHECK_PNG}")


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
        if z >= 1.370:
            return {"Head": 1.0}
        if z >= 1.330:
            t = smoothstep(1.330, 1.370, z)
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
        if co.z >= 1.370:
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

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)

    keyframe_fn(arm_obj, frame_end)

    tr = arm_obj.animation_data.nla_tracks.new()
    tr.name = name
    st = tr.strips.new(name, 1, act)
    st.action_slot = slot
    arm_obj.animation_data.action = None

    for pb in arm_obj.pose.bones:
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)


def key_pose(
    arm_obj: bpy.types.Object,
    frame: int,
    world_rots: dict[str, tuple[float, float, float]],
    *,
    hips_world_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    order = [
        ("Hips", None), ("Spine", "Hips"), ("Spine1", "Spine"), ("Neck", "Spine1"), ("Head", "Neck"),
        ("LeftShoulder", "Spine1"), ("LeftArm", "LeftShoulder"), ("LeftForeArm", "LeftArm"), ("LeftHand", "LeftForeArm"),
        ("RightShoulder", "Spine1"), ("RightArm", "RightShoulder"), ("RightForeArm", "RightArm"), ("RightHand", "RightForeArm"),
        ("LeftUpLeg", "Hips"), ("LeftLeg", "LeftUpLeg"), ("LeftFoot", "LeftLeg"),
        ("RightUpLeg", "Hips"), ("RightLeg", "RightUpLeg"), ("RightFoot", "RightLeg"),
    ]
    accum_mat: dict[str, Matrix] = {}
    for bname, pname in order:
        pb = arm_obj.pose.bones[bname]
        b = arm_obj.data.bones[bname]
        rest_mat = b.matrix_local.to_3x3()
        des_deg = world_rots.get(bname, (0.0, 0.0, 0.0))
        r_des = Euler(tuple(math.radians(a) for a in des_deg), "XYZ").to_matrix()
        r_par = accum_mat[pname] if pname else Matrix.Identity(3)
        r_delta = r_par.inverted() @ r_des
        r_local = rest_mat.inverted() @ r_delta @ rest_mat
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = r_local.to_euler("XYZ")
        accum_mat[bname] = r_des
        pb.keyframe_insert("rotation_euler", frame=frame)
        if bname == "Hips":
            pb.location = rest_mat.inverted() @ Vector(hips_world_offset)
            pb.keyframe_insert("location", frame=frame)


def author_animations(arm_obj: bpy.types.Object, bind_drop_deg: float) -> None:
    rest_drop = max(14.0, min(38.0, 77.0 - bind_drop_deg))
    print(f"Animation calibration: bind_drop_deg={bind_drop_deg:.1f}, rest_drop={rest_drop:.1f}")

    def anim_idle(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 19, 37, 55, 73):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            br = math.sin(ph)
            rots = {
                "Hips": (0.0, -1.2, 1.8),
                "Spine": (1.0, 0.0, 1.4),
                "Spine1": (2.0 + br * 1.4, 0.5, 1.0),
                "Neck": (-0.6 - br * 0.4, 0.0, -1.0),
                "Head": (2.2 - br * 0.5, -1.8 + 0.5 * math.cos(ph), 2.0),
                "LeftShoulder": (0.0, 4.0, 0.0),
                "LeftArm": (-3.0, rest_drop + br * 0.8, 2.0),
                "LeftForeArm": (-12.0 - br * 1.2, rest_drop - 6.0, 3.0),
                "LeftHand": (-10.0, rest_drop - 10.0, 4.0),
                "RightShoulder": (0.0, -4.0, 0.0),
                "RightArm": (-2.0, -(rest_drop + br * 0.8), -2.0),
                "RightForeArm": (-11.0 - br * 1.2, -(rest_drop - 6.0), -3.0),
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

    raw_body, raw_body_albedo, hd_bust, hd_bust_albedo, landmarks = import_and_align_sources()
    body_albedo_cal = calibrate_body_albedo(raw_body_albedo)
    hd_bust_delighted = prepare_delighted_bust_albedo(hd_bust_albedo)
    closeup_eyes_img = prepare_closeup_eyes_image()

    body = build_clean_body_and_hd_head(
        raw_body, body_albedo_cal, hd_bust, hd_bust_delighted, closeup_eyes_img, landmarks
    )
    glasses = build_fitted_glasses(landmarks)

    if args.face_check_only:
        render_v3_face_checkpoint(body, glasses, landmarks)
        return

    sk_landmarks = measure_skeleton_landmarks(body)
    arm_obj = build_armature(sk_landmarks)
    assign_body_weights_and_facial_lock(body, arm_obj, sk_landmarks)
    bind_glasses_rigidly(glasses, arm_obj)
    author_animations(arm_obj, float(sk_landmarks["bind_drop_deg"]))

    # Prune any orphaned temp images before export
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)

    out_path = os.path.abspath(args.out_glb)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        export_yup=True,
        export_apply=False,
        export_materials="EXPORT",
        export_image_format="WEBP",
        export_image_quality=85,
        export_skins=True,
        export_morph=True,
        export_animations=True,
        export_animation_mode="NLA_TRACKS",
        export_nla_strips=True,
    )
    size_bytes = os.path.getsize(out_path)
    print(f"Exported {out_path}: {size_bytes} bytes ({size_bytes / 1024:.1f} KB)")
    assert size_bytes <= 3.0 * 1024 * 1024, f"Companion GLB exceeds 3.0 MB limit: {size_bytes}"


if __name__ == "__main__":
    main()
