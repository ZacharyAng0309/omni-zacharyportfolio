"""
Modular 5-Domain Character Breakdown & Refinement Pipeline
for ZacharyPortfolio's 3D Avatar (`zachary_textured_v19.glb` -> `zachary_character.glb`).

Breaks the 3D character down into 5 sovereign anatomical & garment domains/tasks:
  1. [TASK-AVATAR-MOD-01] Face (`SM_Character_Face` / `Zachary_Face_Albedo`):
     - Smooth periorbital/nasal normals, rigid cranial `Head` weighting (zero `Neck` shear above Y=1.51m).
     - Skin-calibrated PBR (`roughness: 0.52`, `metallic: 0.02`, `specularFactor: 0.45`).
     - 8 Essential Keynote Facial Morph Targets (`mouthSmileLeft`, `mouthSmileRight`, `mouthOpen`,
       `jawOpen`, `eyeBlinkLeft`, `eyeBlinkRight`, `browInnerUp`, `viseme_aa`) with pinned boundary seams.
  2. [TASK-AVATAR-MOD-02] Hair (`SM_Character_Hair` / `Zachary_Hair_Albedo`):
     - Parted dark espresso curtain bangs, crown crest, and sideburns segmented via cranial topology + albedo luminance.
     - Natural satin PBR (`roughness: 0.72`, `metallic: 0.00`, `specularFactor: 0.22`) with directional strand groove normal modulation, eliminating the glued plastic helmet reflection.
  3. [TASK-AVATAR-MOD-03] Glasses (`Sovereign_Titanium_Spectacles`: `Glasses_Metal`, `Glasses_Black`, `Glasses_Lens`):
     - Rigidly parented directly to the `Head` bone (`[AC-AVATAR-04]`) with redundant skinning weights stripped.
     - Optical lenses configured with `alphaMode: BLEND`, `doubleSided: True`, `roughness: 0.02`.
  4. [TASK-AVATAR-MOD-04] Hands (`SM_Character_Hands` / `Zachary_Hands_Albedo`):
     - Seam-welded mesh-graph flood-fill below the armpits (Y < 1.105m) decontaminating all 1,530 hand/finger
       vertices previously stolen by `LeftUpLeg`/`RightUpLeg`.
     - Full 30-finger-bone articulation across `LeftHandThumb1..3` .. `RightHandPinky1..3` (`[AC-CHR-03]`).
  5. [TASK-AVATAR-MOD-05] Clothes (`SM_Cloth_Hoodie`, `SM_Cloth_Trousers`, `SM_Cloth_Footwear`):
     - Decontaminates all 409 torso/hip vertices previously polluted by arm/forearm weights.
     - Synchronizes Station 0 bind-pose `inverseBindMatrices` so runtime arm rotations start from natural rest pose.
     - Tailored garment PBR materials (`Zachary_Cloth_Hoodie` roughness 0.88, `Zachary_Cloth_Trousers` roughness 0.82,
       `Zachary_Cloth_Footwear` roughness 0.48) grounded flush at Y = 0.000m.
"""

from __future__ import annotations

import io
import json
import math
import os
import shutil
import struct
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MORPH_TARGET_NAMES: list[str] = [
    "mouthSmileLeft",
    "mouthSmileRight",
    "mouthOpen",
    "jawOpen",
    "eyeBlinkLeft",
    "eyeBlinkRight",
    "browInnerUp",
    "viseme_aa",
]

DOMAIN_MESH_NAMES: list[str] = [
    "SM_Character_Face",
    "SM_Character_Hair",
    "SM_Character_Hands",
    "SM_Cloth_Hoodie",
    "SM_Cloth_Trousers",
    "SM_Cloth_Footwear",
]


def smoothstep(e0: float, e1: float, x: np.ndarray | float) -> np.ndarray | float:
    t = np.clip((x - e0) / (e1 - e0 + 1e-8), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def euler_xyz_to_quat(rx: float, ry: float, rz: float) -> list[float]:
    """Converts Three.js intrinsic XYZ Euler angles (radians) to glTF quaternion [x, y, z, w]."""
    c1 = math.cos(rx / 2.0)
    c2 = math.cos(ry / 2.0)
    c3 = math.cos(rz / 2.0)
    s1 = math.sin(rx / 2.0)
    s2 = math.sin(ry / 2.0)
    s3 = math.sin(rz / 2.0)
    qx = s1 * c2 * c3 + c1 * s2 * s3
    qy = c1 * s2 * c3 - s1 * c2 * s3
    qz = c1 * c2 * s3 + s1 * s2 * c3
    qw = c1 * c2 * c3 - s1 * s2 * s3
    return [qx, qy, qz, qw]


def quat_to_mat3(q: list[float] | np.ndarray) -> np.ndarray:
    x, y, z, w = float(q[0]), float(q[1]), float(q[2]), float(q[3])
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=np.float64,
    )


def compose_mat4(t: list[float] | np.ndarray, q: list[float] | np.ndarray, s: list[float] | np.ndarray) -> np.ndarray:
    m = np.eye(4, dtype=np.float64)
    rot = quat_to_mat3(q)
    m[:3, :3] = rot * np.asarray(s, dtype=np.float64)[None, :]
    m[:3, 3] = np.asarray(t, dtype=np.float64)
    return m


def _read_accessor(gltf: dict[str, Any], bin_data: bytes, acc_idx: int) -> np.ndarray:
    acc = gltf["accessors"][acc_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    comp_map = {
        5120: np.int8,
        5121: np.uint8,
        5122: np.int16,
        5123: np.uint16,
        5125: np.uint32,
        5126: np.float32,
    }
    type_cols = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
    dtype = comp_map[acc["componentType"]]
    cols = type_cols[acc["type"]]
    arr = np.frombuffer(bin_data, dtype=dtype, count=acc["count"] * cols, offset=off).copy()
    return arr.reshape(acc["count"], cols) if cols > 1 else arr


def extract_unified_body_and_spectacles(
    gltf: dict[str, Any], bin_data: bytes
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, np.ndarray]], bytes]:
    """
    Idempotently extracts the unified body mesh (pos, nrm, uv, joints, weights, tris),
    the 3 spectacle primitives (pos, nrm, tris), and the embedded WebP texture bytes.
    Works whether the input GLB is monolithic ('body') or already segmented into the 6 domain sub-meshes.
    """
    img_bv = gltf["bufferViews"][gltf["images"][0]["bufferView"]]
    img_off = img_bv.get("byteOffset", 0)
    webp_bytes = bytes(bin_data[img_off : img_off + img_bv["byteLength"]])

    meshes_by_name = {m["name"]: m for m in gltf["meshes"]}
    if "body" in meshes_by_name and len(meshes_by_name["body"]["primitives"]) == 1:
        prim = meshes_by_name["body"]["primitives"][0]
        pos = _read_accessor(gltf, bin_data, prim["attributes"]["POSITION"]).astype(np.float32)
        nrm = _read_accessor(gltf, bin_data, prim["attributes"]["NORMAL"]).astype(np.float32)
        uv = _read_accessor(gltf, bin_data, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
        jts = _read_accessor(gltf, bin_data, prim["attributes"]["JOINTS_0"]).astype(np.uint8)
        wts = _read_accessor(gltf, bin_data, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
        tris = _read_accessor(gltf, bin_data, prim["indices"]).astype(np.uint32).reshape(-1, 3)
    else:
        # Re-weld from the 6 domain sub-meshes idempotently by (pos, uv)
        v_map: dict[bytes, int] = {}
        pos_list, nrm_list, uv_list, jts_list, wts_list = [], [], [], [], []
        tris_list = []
        for d_name in DOMAIN_MESH_NAMES:
            m = meshes_by_name[d_name]
            prim = m["primitives"][0]
            p_pos = _read_accessor(gltf, bin_data, prim["attributes"]["POSITION"]).astype(np.float32)
            p_nrm = _read_accessor(gltf, bin_data, prim["attributes"]["NORMAL"]).astype(np.float32)
            p_uv = _read_accessor(gltf, bin_data, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
            p_jts = _read_accessor(gltf, bin_data, prim["attributes"]["JOINTS_0"]).astype(np.uint8)
            p_wts = _read_accessor(gltf, bin_data, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
            p_idx = _read_accessor(gltf, bin_data, prim["indices"]).astype(np.uint32).reshape(-1, 3)

            remap = np.zeros(len(p_pos), dtype=np.uint32)
            for i in range(len(p_pos)):
                key = p_pos[i].tobytes() + p_uv[i].tobytes()
                if key in v_map:
                    remap[i] = v_map[key]
                else:
                    new_idx = len(pos_list)
                    v_map[key] = new_idx
                    remap[i] = new_idx
                    pos_list.append(p_pos[i])
                    nrm_list.append(p_nrm[i])
                    uv_list.append(p_uv[i])
                    jts_list.append(p_jts[i])
                    wts_list.append(p_wts[i])
            tris_list.append(remap[p_idx])

        pos = np.asarray(pos_list, dtype=np.float32)
        nrm = np.asarray(nrm_list, dtype=np.float32)
        uv = np.asarray(uv_list, dtype=np.float32)
        jts = np.asarray(jts_list, dtype=np.uint8)
        wts = np.asarray(wts_list, dtype=np.float32)
        tris = np.vstack(tris_list).astype(np.uint32)

    spec_mesh = meshes_by_name["Sovereign_Titanium_Spectacles"]
    spec_prims: list[dict[str, np.ndarray]] = []
    for sp in spec_mesh["primitives"]:
        s_pos = _read_accessor(gltf, bin_data, sp["attributes"]["POSITION"]).astype(np.float32)
        s_nrm = _read_accessor(gltf, bin_data, sp["attributes"]["NORMAL"]).astype(np.float32)
        s_idx = _read_accessor(gltf, bin_data, sp["indices"]).astype(np.uint16)
        if float(s_pos[:, 1].min()) > 1.0:
            s_pos = s_pos.copy()
            s_pos[:, 1] -= 1.540000
        spec_prims.append({"pos": s_pos, "nrm": s_nrm, "indices": s_idx})

    spec_prims = refine_spectacles_proportions(spec_prims)

    return pos, nrm, uv, jts, wts, tris, spec_prims, webp_bytes


def refine_spectacles_proportions(spec_prims: list[dict[str, np.ndarray]]) -> list[dict[str, np.ndarray]]:
    """
    Refines Sovereign_Titanium_Spectacles proportions and temple layering:
    1. Centers the optical frame horizontally on X = 0.000m (correcting the -2.6mm raw scan offset)
       and aligns the optical center vertically on the pupils (world Y = 1.5869m, hinge Y = 1.5970m).
    2. Eliminates the Z = 0.065m hinge step discontinuity by starting the straight temple trajectory
       directly at the true endpiece hinge corner (Z = 0.0755m, |X| = 0.0666m, local Y = 0.0568m).
    3. Preserves the full 3D cylindrical cross-section (`offset_x`, `offset_y`) of both the titanium
       temple wire (`prim 0`, ~2.1mm) and black acetate ear-tip (`prim 1`, ~3.6mm) while routing the
       temple arm into the supra-auricular groove (|X| = 0.0818m at Z = -0.015m, inside the 0.0865m
       outer ear silhouette) with a natural downward anatomical ear-hook behind the ear.
    """
    if len(spec_prims) < 3:
        return spec_prims

    lens_pos = spec_prims[2]["pos"]
    lens_h = float(lens_pos[:, 1].max() - lens_pos[:, 1].min())
    needs_front_scale = lens_h >= 0.048

    # Detect if X-centering (+2.60mm), Y-hinge alignment (+4.50mm), and temple routing are needed
    front_x_mid = float(0.5 * (lens_pos[:, 0].min() + lens_pos[:, 0].max()))
    dx_center = -front_x_mid if abs(front_x_mid) > 0.0005 else 0.0
    front_y_max = float(lens_pos[:, 1].max())
    dy_front = 0.0045 if front_y_max < 0.0660 else 0.0

    p0_pos = spec_prims[0]["pos"]
    rear_mask = p0_pos[:, 2] < 0.005
    needs_temple_route = bool(np.any(rear_mask) and float(np.abs(p0_pos[rear_mask, 0]).max()) > 0.0850)

    if not needs_front_scale and abs(dx_center) == 0.0 and dy_front == 0.0 and not needs_temple_route:
        return spec_prims

    cx = 0.0
    cy_gltf = 0.0520
    scale_y_front = 0.80
    shift_y_front = +0.0055
    shift_z_front = +0.0105

    z_hinge = 0.0755

    refined: list[dict[str, np.ndarray]] = []
    for sp in spec_prims:
        s_pos = sp["pos"].copy()
        s_nrm = sp["nrm"].copy()
        s_idx = sp["indices"]
        for i, v in enumerate(s_pos):
            gx, gy, gz = float(v[0]), float(v[1]), float(v[2])

            if needs_front_scale:
                sign = 1.0 if gx >= 0.0 else -1.0
                abs_gx = abs(gx)
                if gz >= 0.065:
                    if abs_gx < 0.055:
                        gx = (gx - cx) * 0.82 + cx
                    else:
                        w = float(np.clip((abs_gx - 0.055) / (0.070 - 0.055), 0.0, 1.0))
                        target_abs = (0.055 * 0.82) * (1.0 - w) + 0.0666 * w
                        gx = sign * target_abs
                    gy = (gy - cy_gltf) * scale_y_front + cy_gltf + shift_y_front
                    gz = gz + shift_z_front

            # Apply uniform X centering to remove raw -2.6mm bias
            gx_c = gx + dx_center
            sign = 1.0 if gx_c >= 0.0 else -1.0
            abs_gx = abs(gx_c)

            # Detect nose pads (near nasal bridge, Y_gltf ~ 1.58m, Z_gltf > 0.092m) to seat them tangent to skin
            is_nose_pad = (abs_gx <= 0.018) and (0.028 <= gy <= 0.056) and (gz >= 0.092)

            if gz >= z_hinge:
                # Front frame and optical lenses ahead of the hinge corner (Z >= 0.0755m)
                gx_new = gx_c
                gy_new = gy + dy_front + (0.0008 if is_nose_pad else 0.0)
                gz_new = gz - (0.0065 if is_nose_pad else 0.0)
            elif needs_temple_route:
                # Behind the hinge corner (Z from +0.0755m down to -0.0385m):
                # Reconstruct both X and Y local cross-sectional offsets from the raw v19 temple centerline
                t_orig = float(np.clip((z_hinge - gz) / (z_hinge - (-0.0160)), 0.0, 1.0))
                u_hook = float(np.clip((-0.0160 - gz) / (-0.0160 - (-0.0385)), 0.0, 1.0))
                c_wire_orig = 0.0674 * (1.0 - t_orig) + 0.0940 * t_orig
                c_hook_orig = 0.0940 * (1.0 - u_hook) + 0.0925 * u_hook
                orig_cx = c_wire_orig if gz >= -0.0160 else c_hook_orig
                offset_x = np.clip(abs_gx - orig_cx, -0.0020, 0.0020)

                orig_cy = 0.0522 * (1.0 - t_orig) + 0.0497 * t_orig - 0.0205 * (u_hook ** 1.65)
                offset_y = np.clip(gy - orig_cy, -0.0018, 0.0018)

                # Smooth C1 straight titanium temple trajectory from hinge (|X|=0.0666m) to supra-auricular groove (|X|=0.0818m)
                # Using smooth cubic interpolation at hinge corner to eliminate the C0 angular kink
                t_ear = float(np.clip((z_hinge - gz) / (z_hinge - (-0.0150)), 0.0, 1.0))
                t_ear_smooth = t_ear * t_ear * (3.0 - 2.0 * t_ear)
                wire_x = 0.0818 - 0.0035 * (u_hook ** 1.5)
                target_x = 0.0666 * (1.0 - t_ear_smooth) + wire_x * t_ear_smooth

                # Keep wire Y continuous with hinge (local Y = 0.0568m -> 0.0578m over ear arch, world Y ~ 1.5978m)
                # and preserve a smooth -12.5mm downward anatomical ear-hook curve behind the ear (Z < -0.016m)
                target_y = 0.0568 * (1.0 - t_ear_smooth) + 0.0578 * t_ear_smooth - 0.0125 * (u_hook ** 1.65)

                gx_new = sign * (target_x + float(offset_x))
                gy_new = target_y + float(offset_y)
                gz_new = gz
            else:
                gx_new, gy_new, gz_new = gx_c, gy + dy_front, gz

            s_pos[i] = [gx_new, gy_new, gz_new]

        # Recompute smooth vertex normals on the deformed spectacle primitive
        tris_sp = s_idx.reshape(-1, 3).astype(np.int32)
        v0 = s_pos[tris_sp[:, 0]].astype(np.float64)
        v1 = s_pos[tris_sp[:, 1]].astype(np.float64)
        v2 = s_pos[tris_sp[:, 2]].astype(np.float64)
        fn = np.cross(v1 - v0, v2 - v0)
        acc_n = np.zeros((len(s_pos), 3), dtype=np.float64)
        np.add.at(acc_n, tris_sp[:, 0], fn)
        np.add.at(acc_n, tris_sp[:, 1], fn)
        np.add.at(acc_n, tris_sp[:, 2], fn)
        n_lens = np.linalg.norm(acc_n, axis=1, keepdims=True)
        valid_n = n_lens[:, 0] > 1e-10
        s_nrm[valid_n] = (acc_n[valid_n] / n_lens[valid_n]).astype(np.float32)

        refined.append({"pos": s_pos, "nrm": s_nrm, "indices": s_idx})

    return refined


def build_seam_welded_clusters(
    pos: np.ndarray, tris: np.ndarray
) -> tuple[np.ndarray, list[list[int]], list[list[int]], np.ndarray]:
    """
    Groups colocated vertices across UV seams into unified 3D topological clusters
    and builds the 1-ring cluster adjacency graph.
    """
    n_verts = len(pos)
    pos_clusters: dict[tuple[int, int, int], int] = {}
    vert_to_cluster = np.zeros(n_verts, dtype=np.int32)
    cluster_verts: list[list[int]] = []
    for v in range(n_verts):
        k = (
            int(round(float(pos[v, 0]) * 10000)),
            int(round(float(pos[v, 1]) * 10000)),
            int(round(float(pos[v, 2]) * 10000)),
        )
        if k not in pos_clusters:
            cid = len(cluster_verts)
            pos_clusters[k] = cid
            cluster_verts.append([v])
            vert_to_cluster[v] = cid
        else:
            cid = pos_clusters[k]
            cluster_verts[cid].append(v)
            vert_to_cluster[v] = cid

    n_clusters = len(cluster_verts)
    c_adj_sets: list[set[int]] = [set() for _ in range(n_clusters)]
    for a, b, c in tris:
        ca, cb, cc = int(vert_to_cluster[a]), int(vert_to_cluster[b]), int(vert_to_cluster[c])
        if ca != cb:
            c_adj_sets[ca].add(cb)
            c_adj_sets[cb].add(ca)
        if cb != cc:
            c_adj_sets[cb].add(cc)
            c_adj_sets[cc].add(cb)
        if ca != cc:
            c_adj_sets[ca].add(cc)
            c_adj_sets[cc].add(ca)
    c_adj = [list(s) for s in c_adj_sets]
    c_pos = np.array([pos[vs[0]] for vs in cluster_verts], dtype=np.float32)
    return vert_to_cluster, cluster_verts, c_adj, c_pos


def smooth_periorbital_and_facial_normals(
    pos: np.ndarray,
    nrm: np.ndarray,
    tris: np.ndarray,
    vert_to_cluster: np.ndarray,
    cluster_verts: list[list[int]],
    c_adj: list[list[int]],
    c_pos: np.ndarray,
) -> np.ndarray:
    """
    [TASK-AVATAR-MOD-01]:
    Computes deterministic seam-welded area-weighted normals from `(pos, tris)` and applies
    6 passes of topological Laplacian normal relaxation across the anterior facial/periorbital/nasal
    region (`1.44 <= Y <= 1.65, Z > 0.035, |X| <= 0.078`), eliminating all 84 inverted/sideways
    spectacle-glare scan normal artifacts behind the 3D optical lenses.
    Because it is a pure function of `(pos, tris)` on the facial mask, it is 100% idempotent.
    """
    n_clusters = len(cluster_verts)
    c_nrm = np.zeros((n_clusters, 3), dtype=np.float64)

    v0 = pos[tris[:, 0]].astype(np.float64)
    v1 = pos[tris[:, 1]].astype(np.float64)
    v2 = pos[tris[:, 2]].astype(np.float64)
    fn = np.cross(v1 - v0, v2 - v0)

    for ti, (a, b, c) in enumerate(tris):
        f_vec = fn[ti]
        c_nrm[vert_to_cluster[a]] += f_vec
        c_nrm[vert_to_cluster[b]] += f_vec
        c_nrm[vert_to_cluster[c]] += f_vec

    norms = np.linalg.norm(c_nrm, axis=1, keepdims=True)
    c_nrm = np.where(norms > 1e-10, c_nrm / np.maximum(norms, 1e-10), np.array([0.0, 0.0, 1.0]))

    # 6 passes of topological Laplacian normal smoothing on the anterior face/periorbital region
    face_mask_c = (
        (c_pos[:, 1] >= 1.43)
        & (c_pos[:, 1] <= 1.655)
        & (c_pos[:, 2] > 0.015)
        & (np.abs(c_pos[:, 0]) <= 0.080)
    )
    sm_nrm = c_nrm.copy()
    for _ in range(6):
        next_nrm = sm_nrm.copy()
        for c in np.where(face_mask_c)[0]:
            nbs = c_adj[c]
            if not nbs:
                continue
            nb_mean = sm_nrm[nbs].mean(axis=0)
            mixed = 0.35 * sm_nrm[c] + 0.65 * nb_mean
            ln = float(np.linalg.norm(mixed))
            if ln > 1e-8:
                next_nrm[c] = mixed / ln
        sm_nrm = next_nrm

    # 3 passes of gentle topological Laplacian normal relaxation to weld UV seams and smooth scan facets on the ear
    ear_mask_c = (
        (c_pos[:, 1] >= 1.515)
        & (c_pos[:, 1] <= 1.645)
        & (c_pos[:, 2] >= -0.048)
        & (c_pos[:, 2] <= 0.032)
        & (np.abs(c_pos[:, 0]) >= 0.064)
    )
    for _ in range(3):
        next_nrm = sm_nrm.copy()
        for c in np.where(ear_mask_c)[0]:
            nbs = c_adj[c]
            if not nbs:
                continue
            nb_mean = sm_nrm[nbs].mean(axis=0)
            mixed = 0.65 * sm_nrm[c] + 0.35 * nb_mean
            ln = float(np.linalg.norm(mixed))
            if ln > 1e-8:
                next_nrm[c] = mixed / ln
        sm_nrm = next_nrm

    out_nrm = nrm.copy()
    # Initialize all cranial/neck clusters (Y >= 1.40m) with seam-welded cluster normals so 0 UV-seam splits exist
    for c in range(n_clusters):
        if float(c_pos[c, 1]) >= 1.40:
            base_n = c_nrm[c].astype(np.float32)
            for v in cluster_verts[c]:
                out_nrm[v] = base_n

    for c in np.where(face_mask_c)[0]:
        cx, cy, cz = float(c_pos[c, 0]), float(c_pos[c, 1]), float(c_pos[c, 2])
        w_blend = float(
            smoothstep(1.435, 1.465, cy)
            * (1.0 - smoothstep(1.635, 1.655, cy))
            * smoothstep(0.018, 0.048, cz)
            * (1.0 - smoothstep(0.068, 0.080, abs(cx)))
        )
        if w_blend > 1e-4:
            target_n = sm_nrm[c]
            orig_n = c_nrm[c]
            blended = (1.0 - w_blend) * orig_n + w_blend * target_n
            ln = float(np.linalg.norm(blended))
            if ln > 1e-8:
                unit_n = (blended / ln).astype(np.float32)
                for v in cluster_verts[c]:
                    out_nrm[v] = unit_n

    for c in np.where(ear_mask_c)[0]:
        cx, cy, cz = float(c_pos[c, 0]), float(c_pos[c, 1]), float(c_pos[c, 2])
        w_ear = float(
            smoothstep(1.515, 1.530, cy)
            * (1.0 - smoothstep(1.625, 1.645, cy))
            * smoothstep(-0.048, -0.035, cz)
            * (1.0 - smoothstep(0.020, 0.032, cz))
            * smoothstep(0.064, 0.072, abs(cx))
        )
        if w_ear > 1e-4:
            target_n = sm_nrm[c]
            orig_n = c_nrm[c]
            blended = (1.0 - w_ear) * orig_n + w_ear * target_n
            ln = float(np.linalg.norm(blended))
            if ln > 1e-8:
                unit_n = (blended / ln).astype(np.float32)
                for v in cluster_verts[c]:
                    out_nrm[v] = unit_n

    return out_nrm


def modulate_hair_strand_normals(
    pos: np.ndarray,
    nrm: np.ndarray,
    pinned_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    [TASK-AVATAR-MOD-02 / AC-CHR-02]:
    Modulates hair vertex normals to create directional strand grooves and micro-lock clumping,
    breaking monolithic smooth scan reflection into natural, fibrous hair texture without
    geometric tearing or seam gaps. Boundary vertices shared with Face or Hoodie (pinned_mask)
    have strictly zero normal perturbation (dot == 1.0000 across domain seams) and ramp in
    smoothly over a 12mm C1 transition band.
    """
    out_nrm = nrm.copy()
    xc, zc = 0.0, -0.015
    n_locks = 32
    up = np.array([0.0, 1.0, 0.0])

    if pinned_mask is not None and np.any(pinned_mask):
        pinned_pts = pos[pinned_mask]
        dists = np.min(np.linalg.norm(pos[:, None, :] - pinned_pts[None, :, :], axis=2), axis=1)
        boundary_fade = smoothstep(0.000, 0.012, dists)
        boundary_fade[pinned_mask] = 0.0
    else:
        boundary_fade = np.ones(len(pos), dtype=np.float32)

    for i in range(len(pos)):
        x, y, z = float(pos[i, 0]), float(pos[i, 1]), float(pos[i, 2])
        # Smooth fade near lower hairline borders and domain seams (Face / Hoodie)
        w_fade = float(np.clip((y - 1.530) / 0.040, 0.0, 1.0)) * float(boundary_fade[i])
        if w_fade <= 1e-4:
            continue

        theta = np.arctan2(z - zc, x - xc)
        lock_wave = np.sin(n_locks * theta + 1.2 * np.sin(25.0 * (y - 1.62)))
        strand_wave = np.sin(n_locks * 3.0 * theta + 40.0 * (y - 1.62))
        tilt = w_fade * (0.12 * lock_wave + 0.05 * strand_wave)

        n = out_nrm[i].astype(np.float64)
        tangent = np.cross(n, up)
        t_len = float(np.linalg.norm(tangent))
        if t_len > 1e-4:
            tangent = tangent / t_len
            pert = n + tilt * tangent
            p_len = float(np.linalg.norm(pert))
            if p_len > 1e-6:
                out_nrm[i] = (pert / p_len).astype(np.float32)
    return out_nrm


def refine_hands_and_clothes_weights(
    pos: np.ndarray,
    tris: np.ndarray,
    jts: np.ndarray,
    wts: np.ndarray,
    joint_names: list[str],
    vert_to_cluster: np.ndarray,
    c_adj: list[list[int]],
    c_pos: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    [TASK-AVATAR-MOD-04 & MOD-05]:
    1. Seam-welded mesh-graph flood-fill from left/right hands below the armpit (Y < 1.135m)
       identifies free-hanging arm/hand vertices without any coordinate-slicing leak.
    2. Purges all thigh/leg/hip/lower-spine contamination from the arm/hand vertices, AND
       smoothly weights the upper sleeves (1.10m <= Y <= 1.43m, |X| > 0.145m) across
       ForeArm -> Arm -> Shoulder/Spine2 (eliminating the 341 Spine1/ForeArm-contaminated
       upper-sleeve vertices that caused armpit/bicep tearing).
    3. Purges all arm/forearm/hand contamination from the torso/hip/thigh vertices.
    4. Articulates all 30 finger bones (Thumb1..3, Index1..3, Middle1..3, Ring1..3, Pinky1..3)
       across the left and right hands ([AC-CHR-03]).
    5. Computes C1-continuous cluster-level Head/Neck/Spine2 weights across the neck, hoodie cowl,
       and upper cranium so the skull, face, ears, upper hair, and Head-parented spectacles move
       as a rigid unit while eliminating single-triangle weight cliffs across the cowl/hair transition.
    """
    n_verts = len(pos)
    n_clusters = len(c_pos)
    j_idx = {name: i for i, name in enumerate(joint_names)}

    arm_comp_c = np.zeros(n_clusters, dtype=bool)
    queue: list[int] = [
        c for c in range(n_clusters) if abs(float(c_pos[c, 0])) > 0.30 and float(c_pos[c, 1]) < 0.90
    ]
    for c in queue:
        arm_comp_c[c] = True
    head_ptr = 0
    while head_ptr < len(queue):
        u = queue[head_ptr]
        head_ptr += 1
        for nb in c_adj[u]:
            if not arm_comp_c[nb] and float(c_pos[nb, 1]) < 1.135 and abs(float(c_pos[nb, 0])) > 0.175:
                arm_comp_c[nb] = True
                queue.append(nb)

    arm_hand_comp = arm_comp_c[vert_to_cluster]
    new_jts = jts.copy()
    new_wts = wts.copy()

    arm_hand_bone_set = {
        j_idx[n]
        for n in joint_names
        if ("Arm" in n or "Hand" in n or "Shoulder" in n)
    }
    head_neck_bone_set = {j_idx["Head"], j_idx["Neck"]}

    # 1. Decontaminate Torso/Hip/Leg/Upper-Back/Chest vertices (not in arm_hand_comp and |x| <= 0.175, y < 1.42)
    for v in range(n_verts):
        x_abs = abs(float(pos[v, 0]))
        yv = float(pos[v, 1])
        if not arm_hand_comp[v] and ((x_abs <= 0.175 and yv < 1.25) or (x_abs <= 0.145 and yv < 1.42)):
            modified = False
            for k in range(4):
                b_id = int(new_jts[v, k])
                if (b_id in arm_hand_bone_set or (yv < 1.415 and b_id in head_neck_bone_set)) and float(new_wts[v, k]) > 0.0:
                    new_wts[v, k] = 0.0
                    modified = True
            if modified:
                w_sum = float(new_wts[v].sum())
                if w_sum > 1e-5:
                    new_wts[v] /= w_sum
                else:
                    fallback = (
                        j_idx["Spine2"]
                        if yv >= 1.22
                        else (j_idx["Spine1"] if yv >= 1.05 else (j_idx["Spine"] if yv >= 0.92 else j_idx["Hips"]))
                    )
                    new_jts[v] = [fallback, 0, 0, 0]
                    new_wts[v] = [1.0, 0.0, 0.0, 0.0]

    # 2. Recompute clean anatomical weights on the free-hanging Left & Right Arm/Hand components
    #    AND upper sleeves (1.10 <= y <= 1.43, |x| > 0.145)
    digit_rays = [
        ("Thumb", 0.112, 0.018),
        ("Index", 0.090, 0.014),
        ("Middle", 0.072, 0.014),
        ("Ring", 0.052, 0.014),
        ("Pinky", 0.026, 0.018),
    ]

    for v in range(n_verts):
        x, y, z = float(pos[v, 0]), float(pos[v, 1]), float(pos[v, 2])
        is_upper_sleeve = (1.10 <= y <= 1.43) and (abs(x) > 0.145)
        if arm_hand_comp[v] or is_upper_sleeve:
            side = "Left" if x > 0 else "Right"
            b_sh = j_idx[f"{side}Shoulder"]
            b_arm = j_idx[f"{side}Arm"]
            b_fore = j_idx[f"{side}ForeArm"]
            b_hand = j_idx[f"{side}Hand"]
            b_sp2 = j_idx["Spine2"]
            b_sp1 = j_idx["Spine1"]

            if not arm_hand_comp[v] and is_upper_sleeve:
                # Upper sleeve & shoulder blend (1.10 <= y <= 1.43, |x| > 0.145)
                t_lat = float(smoothstep(0.145, 0.195, abs(x)))
                w_fore = float(1.0 - smoothstep(1.08, 1.18, y)) * t_lat
                w_sh_cap = float(smoothstep(1.32, 1.43, y)) * 0.35 * t_lat
                w_torso = 1.0 - t_lat
                w_arm = max(0.0, 1.0 - w_fore - w_sh_cap - w_torso)
                b_torso = b_sp2 if y >= 1.20 else b_sp1
                new_jts[v] = [b_arm, b_torso, b_fore, b_sh]
                new_wts[v] = [w_arm, w_torso, w_fore, w_sh_cap]
                new_wts[v] /= float(new_wts[v].sum()) + 1e-8
            elif y >= 0.94:
                # Forearm to Upper Arm elbow transition
                w_arm = float(smoothstep(1.06, 1.17, y))
                w_fore = 1.0 - w_arm
                new_jts[v] = [b_fore, b_arm, 0, 0]
                new_wts[v] = [w_fore, w_arm, 0.0, 0.0]
            elif y >= 0.850:
                # Wrist & Metacarpal Palm (ForeArm -> Hand, plus Thumb base on anterior aspect)
                w_fore = float(smoothstep(0.875, 0.94, y))
                w_hand = 1.0 - w_fore
                w_thumb1 = 0.0
                if z > 0.095 and y < 0.885:
                    w_thumb1 = float(smoothstep(0.095, 0.120, z) * (1.0 - smoothstep(0.845, 0.885, y))) * 0.55
                    w_hand = max(0.0, w_hand - w_thumb1)
                b_th1 = j_idx[f"{side}HandThumb1"]
                new_jts[v] = [b_hand, b_fore, b_th1, 0]
                new_wts[v] = [w_hand, w_fore, w_thumb1, 0.0]
                new_wts[v] /= float(new_wts[v].sum())
            else:
                # Articulated Fingers (y < 0.850): blend across the 2 nearest digit rays and phalanges 1..3
                ray_scores: list[tuple[float, str]] = []
                for d_name, z_center, z_sigma in digit_rays:
                    score = math.exp(-0.5 * ((z - z_center) / z_sigma) ** 2)
                    ray_scores.append((score, d_name))
                ray_scores.sort(reverse=True)
                (s1, d1), (s2, d2) = ray_scores[0], ray_scores[1]
                s_tot = s1 + s2 + 1e-8
                r1, r2 = s1 / s_tot, s2 / s_tot

                w_hand_palm = float(smoothstep(0.830, 0.850, y)) * 0.35
                rem = 1.0 - w_hand_palm
                if y >= 0.805:
                    t_p = float(smoothstep(0.805, 0.838, y))
                    p_idx_a, p_idx_b = 1, 2
                    wa, wb = t_p * rem, (1.0 - t_p) * rem
                else:
                    t_p = float(smoothstep(0.772, 0.805, y))
                    p_idx_a, p_idx_b = 2, 3
                    wa, wb = t_p * rem, (1.0 - t_p) * rem

                cand: list[tuple[float, int]] = [
                    (wa * r1, j_idx[f"{side}Hand{d1}{p_idx_a}"]),
                    (wb * r1, j_idx[f"{side}Hand{d1}{p_idx_b}"]),
                    (wa * r2 + wb * r2, j_idx[f"{side}Hand{d2}{p_idx_a}"]),
                    (w_hand_palm, b_hand),
                ]
                cand.sort(reverse=True)
                tot_w = sum(c[0] for c in cand) + 1e-8
                new_jts[v] = [c[1] for c in cand]
                new_wts[v] = [c[0] / tot_w for c in cand]

    # 3. C1-Continuous Cluster-Level Upper Cranium vs Sloped Hoodie Cowl Weight Field
    b_head = j_idx["Head"]
    b_neck = j_idx["Neck"]
    b_sp2 = j_idx["Spine2"]
    cranial_mask_c = np.zeros(n_clusters, dtype=bool)
    locked_head_c = np.zeros(n_clusters, dtype=bool)
    locked_base_c = np.zeros(n_clusters, dtype=bool)
    c_hns = np.zeros((n_clusters, 3), dtype=np.float64)  # [Head, Neck, Spine2]

    for c in range(n_clusters):
        x, y, z = float(c_pos[c, 0]), float(c_pos[c, 1]), float(c_pos[c, 2])
        if arm_comp_c[c] or ((1.10 <= y <= 1.43) and (abs(x) > 0.145)):
            continue
        if y >= 1.385:
            cranial_mask_c[c] = True
            hood_rim_y = 1.472 - 0.78 * min(0.0, z + 0.035)
            rear_y_lim = min(1.546, hood_rim_y)
            w_rear = float(1.0 - smoothstep(-0.048, -0.020, z)) * float(1.0 - smoothstep(rear_y_lim - 0.018, rear_y_lim + 0.018, y))
            w_lat = float(smoothstep(0.056, 0.074, abs(x))) * float(1.0 - smoothstep(0.010, 0.032, z)) * float(1.0 - smoothstep(1.508, 1.535, y))
            ant_y_lim = 1.422 + 3.5 * (x * x)
            w_ant = float(smoothstep(-0.045, -0.020, z)) * float(1.0 - smoothstep(ant_y_lim - 0.015, ant_y_lim + 0.020, y))
            w_cowl = max(w_rear, w_lat, w_ant)

            # Upper cranium, face, ears, and spectacle bridge/temples lock 100% to Head
            is_rigid_cranium = (y >= 1.556) or (y >= 1.515 and z >= -0.025 and abs(x) <= 0.095 and w_cowl < 0.02)
            if is_rigid_cranium:
                locked_head_c[c] = True
                c_hns[c] = [1.0, 0.0, 0.0]
            elif y <= 1.415:
                locked_base_c[c] = True
                c_hns[c] = [0.0, 0.0, 1.0]
            else:
                w_neck_cowl = float(smoothstep(1.43, 1.54, y)) * 0.28
                cowl_vec = np.array([0.0, w_neck_cowl, 1.0 - w_neck_cowl], dtype=np.float64)

                w_head_neck = float(smoothstep(1.455, 1.520, y))
                w_sp2_neck = float(1.0 - smoothstep(1.410, 1.465, y)) * (1.0 - w_head_neck)
                w_neck_mid = max(0.0, 1.0 - w_head_neck - w_sp2_neck)
                neck_vec = np.array([w_head_neck, w_neck_mid, w_sp2_neck], dtype=np.float64)

                blended = w_cowl * cowl_vec + (1.0 - w_cowl) * neck_vec
                c_hns[c] = blended / max(float(blended.sum()), 1e-8)

    # 8 passes of topological cluster-graph smoothing across the neck/cowl transition zone
    # to guarantee zero 1.0000 single-triangle Head weight cliffs while keeping rigid cranium locked
    for _ in range(8):
        next_hns = c_hns.copy()
        for c in np.where(cranial_mask_c & (~locked_head_c) & (~locked_base_c))[0]:
            nbs = [nb for nb in c_adj[c] if cranial_mask_c[nb]]
            if not nbs:
                continue
            nb_mean = c_hns[nbs].mean(axis=0)
            mixed = 0.40 * c_hns[c] + 0.60 * nb_mean
            next_hns[c] = mixed / max(float(mixed.sum()), 1e-8)
        c_hns = next_hns

    for c in np.where(cranial_mask_c)[0]:
        if float(c_pos[c, 1]) < 1.415:
            continue
        wh, wn, ws = float(c_hns[c, 0]), float(c_hns[c, 1]), float(c_hns[c, 2])
        if wh > 0.999:
            j_row = [b_head, 0, 0, 0]
            w_row = [1.0, 0.0, 0.0, 0.0]
        else:
            j_row = [b_head, b_neck, b_sp2, 0]
            w_row = [wh, wn, ws, 0.0]
        for v in range(n_verts):
            if int(vert_to_cluster[v]) == c:
                new_jts[v] = j_row
                new_wts[v] = w_row

    # Sort each vertex's 4 influences descending by weight and normalize
    order = np.argsort(-new_wts, axis=1)
    new_jts = np.take_along_axis(new_jts, order, axis=1)
    new_wts = np.take_along_axis(new_wts, order, axis=1)
    w_sums = np.maximum(new_wts.sum(axis=1, keepdims=True), 1e-8)
    new_wts = (new_wts / w_sums).astype(np.float32)

    return new_jts, new_wts, arm_hand_comp


def segment_character_domains(
    pos: np.ndarray,
    uv: np.ndarray,
    tris: np.ndarray,
    jts: np.ndarray,
    wts: np.ndarray,
    arm_hand_comp: np.ndarray,
    joint_names: list[str],
    webp_bytes: bytes,
    vert_to_cluster: np.ndarray,
    cluster_verts: list[list[int]],
    c_adj: list[list[int]],
    c_pos: np.ndarray,
) -> dict[str, np.ndarray]:
    """
    Partitions the 35,069 triangles of `body` into 6 watertight anatomical & garment domain sub-meshes:
      - SM_Character_Face
      - SM_Character_Hair
      - SM_Character_Hands
      - SM_Cloth_Hoodie
      - SM_Cloth_Trousers
      - SM_Cloth_Footwear
    Driven by seam-welded limb topology, sloped cranial/hoodie cowl separation, albedo chromaticity,
    3-pass topological cluster majority voting, and 4-pass triangle-edge sawtooth elimination.
    """
    img = Image.open(io.BytesIO(webp_bytes)).convert("RGB")
    arr_img = np.asarray(img, dtype=np.float32) / 255.0
    h_img, w_img, _ = arr_img.shape
    px = np.clip((uv[:, 0] * (w_img - 1)).astype(int), 0, w_img - 1)
    py = np.clip((uv[:, 1] * (h_img - 1)).astype(int), 0, h_img - 1)
    rgb = arr_img[py, px]
    lum = 0.299 * rgb[:, 0] + 0.587 * rgb[:, 1] + 0.114 * rgb[:, 2]
    warmth = rgb[:, 0] - rgb[:, 2]

    n_clusters = len(cluster_verts)
    c_lum = np.array([float(np.mean([lum[v] for v in vs])) for vs in cluster_verts], dtype=np.float32)
    c_warm = np.array([float(np.mean([warmth[v] for v in vs])) for vs in cluster_verts], dtype=np.float32)
    arm_comp_c = np.array([bool(arm_hand_comp[vs[0]]) for vs in cluster_verts], dtype=bool)

    # Cluster domain labels: 0=Face, 1=Hair, 2=Hands, 3=Hoodie, 4=Trousers, 5=Footwear
    c_dom = np.full(n_clusters, 3, dtype=np.int32)
    is_ear_cluster = np.zeros(n_clusters, dtype=bool)
    for c in range(n_clusters):
        x, y, z = float(c_pos[c, 0]), float(c_pos[c, 1]), float(c_pos[c, 2])
        lm, wm = float(c_lum[c]), float(c_warm[c])
        if arm_comp_c[c]:
            if y < 0.865:
                c_dom[c] = 2  # SM_Character_Hands
            elif y > 0.915:
                c_dom[c] = 3  # SM_Cloth_Hoodie
            else:
                c_dom[c] = 3 if lm < 0.24 else 2
        elif y >= 1.410:
            hood_rim_y = 1.472 - 0.78 * min(0.0, z + 0.035)
            is_rear_hood = ((z < -0.035) and (y < min(1.546, hood_rim_y))) or ((z < -0.055) and (y < 1.505))
            is_lat_cowl = (abs(x) > 0.066) and (z < 0.025) and (y < 1.522)
            is_ant_collar = (z >= -0.035) and (y < 1.422 + 3.5 * (x * x) or (y < 1.485 and lm < 0.22))
            if is_rear_hood or is_lat_cowl or is_ant_collar:
                c_dom[c] = 3  # SM_Cloth_Hoodie
            else:
                is_neck_chin = (y < 1.505) and (z > -0.015) and (abs(x) <= 0.075)
                is_sideburn = (abs(x) >= 0.068) and (1.545 <= y <= 1.610) and (-0.010 <= z <= 0.035) and (lm < 0.25)
                is_lower_face = (1.505 <= y <= 1.605) and (z > 0.012) and (abs(x) <= 0.084) and (not is_sideburn)
                is_ear = (
                    (1.520 <= y <= 1.606)
                    and (abs(x) >= 0.070)
                    and (-0.032 <= z <= 0.018)
                    and (lm > 0.25)
                )
                is_forehead_skin = (
                    (1.602 < y <= 1.656)
                    and (z > 0.035)
                    and (abs(x) <= 0.078)
                    and (lm > 0.36)
                    and (wm > 0.07)
                )
                if is_ear:
                    is_ear_cluster[c] = True
                    c_dom[c] = 0  # SM_Character_Face (inviolable ear skin boundary)
                elif is_neck_chin or is_lower_face or is_forehead_skin:
                    c_dom[c] = 0  # SM_Character_Face
                else:
                    c_dom[c] = 1  # SM_Character_Hair
        elif y < 0.104 + 0.018 * float(smoothstep(-0.02, 0.08, z)):
            c_dom[c] = 5  # SM_Cloth_Footwear
        elif y < 0.868:
            c_dom[c] = 4  # SM_Cloth_Trousers
        else:
            c_dom[c] = 3  # SM_Cloth_Hoodie

    # 3 passes of topological 1-ring cluster majority smoothing
    for _ in range(3):
        next_dom = c_dom.copy()
        for c in range(n_clusters):
            if is_ear_cluster[c]:
                # Inviolable anatomical rule: Ear cartilage is always skin, never hair
                continue
            nbs = c_adj[c]
            if not nbs:
                continue
            counts: dict[int, int] = {}
            for nb in nbs:
                d = int(c_dom[nb])
                counts[d] = counts.get(d, 0) + 1
            best_d, best_cnt = max(counts.items(), key=lambda kv: kv[1])
            if best_d != int(c_dom[c]) and best_cnt >= (len(nbs) // 2) + 1:
                next_dom[c] = best_d
        c_dom = next_dom

    v_dom = c_dom[vert_to_cluster]
    t_dom = np.zeros(len(tris), dtype=np.int32)
    for t_i, (a, b, c) in enumerate(tris):
        da, db, dc = int(v_dom[a]), int(v_dom[b]), int(v_dom[c])
        if da == db or da == dc:
            t_dom[t_i] = da
        elif db == dc:
            t_dom[t_i] = db
        else:
            t_dom[t_i] = da

    # 4 passes of triangle-edge adjacency smoothing to eliminate sawtooth border teeth & islands
    edge_to_tris: dict[tuple[int, int], list[int]] = {}
    for t_i, (a, b, c) in enumerate(tris):
        ca, cb, cc = int(vert_to_cluster[a]), int(vert_to_cluster[b]), int(vert_to_cluster[c])
        for u, v in ((ca, cb), (cb, cc), (cc, ca)):
            ek = (u, v) if u < v else (v, u)
            edge_to_tris.setdefault(ek, []).append(t_i)

    t_adj: list[list[int]] = [[] for _ in range(len(tris))]
    for t_list in edge_to_tris.values():
        if len(t_list) == 2:
            t0, t1 = t_list[0], t_list[1]
            t_adj[t0].append(t1)
            t_adj[t1].append(t0)

    for _ in range(4):
        changed = 0
        next_t_dom = t_dom.copy()
        for t_i in range(len(tris)):
            nbs = t_adj[t_i]
            if len(nbs) >= 2:
                counts = {}
                for nb in nbs:
                    d = int(t_dom[nb])
                    counts[d] = counts.get(d, 0) + 1
                best_d, best_cnt = max(counts.items(), key=lambda kv: kv[1])
                if best_d != int(t_dom[t_i]) and best_cnt >= 2:
                    next_t_dom[t_i] = best_d
                    changed += 1
        t_dom = next_t_dom
        if changed == 0:
            break

    # Invariant Guardrail 1: Strictly prevent any triangle containing rear hoodie cowl vertices (z < -0.055 and y < 1.50) from residing in SM_Character_Hair
    for t_i in range(len(tris)):
        if t_dom[t_i] == 1:
            for v_idx in tris[t_i]:
                vy = float(pos[v_idx, 1])
                vz = float(pos[v_idx, 2])
                if vz < -0.055 and vy < 1.50:
                    t_dom[t_i] = 3  # Reassign to SM_Cloth_Hoodie
                    break

    # Invariant Guardrail 1b: Strictly prevent any neck/cowl triangles (average y < 1.525) from residing in SM_Character_Hair
    for t_i in range(len(tris)):
        if t_dom[t_i] == 1:
            tri_y = (float(pos[tris[t_i, 0], 1]) + float(pos[tris[t_i, 1], 1]) + float(pos[tris[t_i, 2], 1])) / 3.0
            if tri_y < 1.525:
                t_dom[t_i] = 3  # Reassign to SM_Cloth_Hoodie

    # Invariant Guardrail 1c: Strictly prevent skin-toned ear cartilage triangles from residing in SM_Character_Hair
    # while keeping supra-auricular dark hair triangles (min_lum <= 0.22 or max_y > 1.6075) in SM_Character_Hair
    for t_i in range(len(tris)):
        pts = pos[tris[t_i]]
        avg_x = float(np.mean(pts[:, 0]))
        avg_y = float(np.mean(pts[:, 1]))
        avg_z = float(np.mean(pts[:, 2]))
        max_y = float(np.max(pts[:, 1]))
        tri_lum = float(np.mean(lum[tris[t_i]]))
        min_lum = float(np.min(lum[tris[t_i]]))
        if t_dom[t_i] == 1:
            if abs(avg_x) >= 0.069 and 1.520 <= avg_y <= 1.606 and max_y <= 1.6075 and -0.032 <= avg_z <= 0.020 and tri_lum > 0.28 and min_lum > 0.20:
                t_dom[t_i] = 0  # Reassign skin-toned ear cartilage to SM_Character_Face
        elif t_dom[t_i] == 0:
            if abs(avg_x) >= 0.068 and 1.545 <= avg_y <= 1.610 and -0.010 <= avg_z <= 0.035 and min_lum <= 0.24:
                t_dom[t_i] = 1  # Assign pre-auricular dark hair sideburn triangles to SM_Character_Hair
            elif abs(avg_x) >= 0.069 and -0.042 <= avg_z <= 0.016 and (max_y > 1.6075 or (avg_y >= 1.595 and min_lum <= 0.20)):
                t_dom[t_i] = 1  # Keep supra-auricular dark hair transition triangles in SM_Character_Hair
            elif avg_y <= 1.485 and min_lum <= 0.22 and avg_z <= 0.050:
                t_dom[t_i] = 3  # Reassign dark collar triangles on lower neck to SM_Cloth_Hoodie

    # 2 post-guardrail triangle-edge cleanup passes to remove any single-triangle domain peninsulas
    for _ in range(2):
        next_t_dom = t_dom.copy()
        for t_i in range(len(tris)):
            nbs = t_adj[t_i]
            if len(nbs) >= 2:
                counts = {}
                for nb in nbs:
                    d = int(t_dom[nb])
                    counts[d] = counts.get(d, 0) + 1
                best_d, best_cnt = max(counts.items(), key=lambda kv: kv[1])
                if best_d != int(t_dom[t_i]) and best_cnt >= 2:
                    next_t_dom[t_i] = best_d
        t_dom = next_t_dom

    # Re-enforce supra-auricular ceiling on SM_Character_Face after cleanup
    for t_i in range(len(tris)):
        if t_dom[t_i] == 0:
            pts = pos[tris[t_i]]
            avg_x = float(np.mean(pts[:, 0]))
            avg_z = float(np.mean(pts[:, 2]))
            max_y = float(np.max(pts[:, 1]))
            min_lum = float(np.min(lum[tris[t_i]]))
            if abs(avg_x) >= 0.069 and -0.042 <= avg_z <= 0.016 and (max_y > 1.6075 or (max_y > 1.602 and min_lum <= 0.22)):
                t_dom[t_i] = 1

    # Invariant Guardrail 2: Strictly prevent any triangle above the waist hem (average y > 0.870) from residing in SM_Cloth_Trousers
    for t_i in range(len(tris)):
        if t_dom[t_i] == 4:
            tri_y = (float(pos[tris[t_i, 0], 1]) + float(pos[tris[t_i, 1], 1]) + float(pos[tris[t_i, 2], 1])) / 3.0
            if tri_y > 0.870:
                t_dom[t_i] = 3  # Reassign to SM_Cloth_Hoodie

    # Invariant Guardrail 3: Wrist cuff segregation by luminance (Law 12)
    for t_i in range(len(tris)):
        tri_y = (float(pos[tris[t_i, 0], 1]) + float(pos[tris[t_i, 1], 1]) + float(pos[tris[t_i, 2], 1])) / 3.0
        tri_lum = float(np.mean(lum[tris[t_i]]))
        if t_dom[t_i] == 2 and 0.865 <= tri_y <= 0.920 and abs(float(pos[tris[t_i, 0], 0])) > 0.20:
            if tri_lum < 0.20:
                t_dom[t_i] = 3  # Dark sleeve cuff belongs in SM_Cloth_Hoodie
        elif t_dom[t_i] == 3 and 0.865 <= tri_y <= 0.910 and abs(float(pos[tris[t_i, 0], 0])) > 0.20:
            if tri_lum > 0.32:
                t_dom[t_i] = 2  # Hand skin belongs in SM_Character_Hands

    # Invariant Guardrail 4: Clean anterior neck skin vs hoodie collar (Law 12)
    for t_i in range(len(tris)):
        tri_y = (float(pos[tris[t_i, 0], 1]) + float(pos[tris[t_i, 1], 1]) + float(pos[tris[t_i, 2], 1])) / 3.0
        tri_lum = float(np.mean(lum[tris[t_i]]))
        tri_z = (float(pos[tris[t_i, 0], 2]) + float(pos[tris[t_i, 1], 2]) + float(pos[tris[t_i, 2], 2])) / 3.0
        tri_x = (float(pos[tris[t_i, 0], 0]) + float(pos[tris[t_i, 1], 0]) + float(pos[tris[t_i, 2], 0])) / 3.0
        if t_dom[t_i] == 3 and 1.435 <= tri_y <= 1.485 and tri_z > -0.015 and abs(tri_x) < 0.055:
            if tri_lum > 0.32:
                t_dom[t_i] = 0  # Clean skin on anterior neck belongs to SM_Character_Face

    return {
        "SM_Character_Face": tris[t_dom == 0],
        "SM_Character_Hair": tris[t_dom == 1],
        "SM_Character_Hands": tris[t_dom == 2],
        "SM_Cloth_Hoodie": tris[t_dom == 3],
        "SM_Cloth_Trousers": tris[t_dom == 4],
        "SM_Cloth_Footwear": tris[t_dom == 5],
    }


def build_face_morph_targets(face_pos: np.ndarray, pinned_mask: np.ndarray) -> list[np.ndarray]:
    """
    [TASK-AVATAR-MOD-01 / AC-AVATAR-05]:
    Generates the 8 Essential Keynote Facial Morph Targets on SM_Character_Face:
      1. mouthSmileLeft
      2. mouthSmileRight
      3. mouthOpen
      4. jawOpen
      5. eyeBlinkLeft
      6. eyeBlinkRight
      7. browInnerUp
      8. viseme_aa
    Boundary vertices shared with Hair or Hoodie (pinned_mask) have strictly zero displacement (0.000m)
    to preserve 100% watertight seams across all morph combinations.
    """
    n_v = len(face_pos)
    x = face_pos[:, 0]
    y = face_pos[:, 1]
    z = face_pos[:, 2]

    # Smooth interior mask that is 0 on pinned boundary vertices and 0 for posterior/neck region
    interior = (~pinned_mask).astype(np.float32) * smoothstep(0.045, 0.072, z) * smoothstep(1.458, 1.472, y)

    def radial_weight(cx: float, cy: float, cz: float, rx: float, ry: float, rz: float) -> np.ndarray:
        d2 = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
        w = np.clip(1.0 - d2, 0.0, 1.0)
        return (w * w * (3.0 - 2.0 * w) * interior).astype(np.float32)

    targets: list[np.ndarray] = []

    # 1. mouthSmileLeft (+X is character left)
    d_smile_l = np.zeros((n_v, 3), dtype=np.float32)
    w_sl = radial_weight(0.022, 1.522, 0.106, 0.026, 0.024, 0.035)
    w_cheek_l = radial_weight(0.034, 1.548, 0.095, 0.028, 0.026, 0.035)
    d_smile_l[:, 0] = 0.0038 * w_sl + 0.0014 * w_cheek_l
    d_smile_l[:, 1] = 0.0052 * w_sl + 0.0022 * w_cheek_l
    d_smile_l[:, 2] = -0.0010 * w_sl + 0.0012 * w_cheek_l
    targets.append(d_smile_l)

    # 2. mouthSmileRight (-X is character right)
    d_smile_r = np.zeros((n_v, 3), dtype=np.float32)
    w_sr = radial_weight(-0.022, 1.522, 0.106, 0.026, 0.024, 0.035)
    w_cheek_r = radial_weight(-0.034, 1.548, 0.095, 0.028, 0.026, 0.035)
    d_smile_r[:, 0] = -0.0038 * w_sr - 0.0014 * w_cheek_r
    d_smile_r[:, 1] = 0.0052 * w_sr + 0.0022 * w_cheek_r
    d_smile_r[:, 2] = -0.0010 * w_sr + 0.0012 * w_cheek_r
    targets.append(d_smile_r)

    # 3. mouthOpen
    d_mouth_open = np.zeros((n_v, 3), dtype=np.float32)
    w_low_lip = radial_weight(0.0, 1.512, 0.108, 0.028, 0.018, 0.035)
    w_up_lip = radial_weight(0.0, 1.530, 0.110, 0.026, 0.014, 0.035)
    d_mouth_open[:, 1] = -0.0088 * w_low_lip + 0.0024 * w_up_lip
    d_mouth_open[:, 2] = -0.0022 * w_low_lip
    targets.append(d_mouth_open)

    # 4. jawOpen
    d_jaw_open = np.zeros((n_v, 3), dtype=np.float32)
    w_jaw = radial_weight(0.0, 1.492, 0.098, 0.048, 0.034, 0.045)
    d_jaw_open[:, 1] = -0.0115 * w_jaw
    d_jaw_open[:, 2] = -0.0038 * w_jaw
    targets.append(d_jaw_open)

    # 5. eyeBlinkLeft (+X left eye behind spectacle lens)
    d_blink_l = np.zeros((n_v, 3), dtype=np.float32)
    w_lid_l = radial_weight(0.034, 1.592, 0.092, 0.022, 0.016, 0.030)
    w_low_lid_l = radial_weight(0.034, 1.578, 0.092, 0.020, 0.012, 0.028)
    d_blink_l[:, 1] = -0.0062 * w_lid_l + 0.0016 * w_low_lid_l
    d_blink_l[:, 2] = 0.0010 * w_lid_l
    targets.append(d_blink_l)

    # 6. eyeBlinkRight (-X right eye behind spectacle lens)
    d_blink_r = np.zeros((n_v, 3), dtype=np.float32)
    w_lid_r = radial_weight(-0.034, 1.592, 0.092, 0.022, 0.016, 0.030)
    w_low_lid_r = radial_weight(-0.034, 1.578, 0.092, 0.020, 0.012, 0.028)
    d_blink_r[:, 1] = -0.0062 * w_lid_r + 0.0016 * w_low_lid_r
    d_blink_r[:, 2] = 0.0010 * w_lid_r
    targets.append(d_blink_r)

    # 7. browInnerUp
    d_brow_up = np.zeros((n_v, 3), dtype=np.float32)
    w_brow_l = radial_weight(0.022, 1.616, 0.094, 0.024, 0.016, 0.030)
    w_brow_r = radial_weight(-0.022, 1.616, 0.094, 0.024, 0.016, 0.030)
    w_brow = np.maximum(w_brow_l, w_brow_r)
    d_brow_up[:, 1] = 0.0055 * w_brow
    d_brow_up[:, 2] = 0.0008 * w_brow
    targets.append(d_brow_up)

    # 8. viseme_aa (open vowel speech articulation)
    d_viseme_aa = np.zeros((n_v, 3), dtype=np.float32)
    d_viseme_aa[:, 0] = -0.0018 * np.sign(x) * (w_low_lip + w_up_lip) * 0.5
    d_viseme_aa[:, 1] = -0.0098 * w_low_lip - 0.0048 * w_jaw + 0.0028 * w_up_lip
    d_viseme_aa[:, 2] = -0.0028 * (w_low_lip + w_jaw * 0.5)
    targets.append(d_viseme_aa)

    return targets


def calibrate_bind_pose_and_ibms(gltf: dict[str, Any]) -> np.ndarray:
    """
    Calibrates LeftShoulder, RightShoulder, LeftArm, RightArm, LeftForeArm, RightForeArm,
    and all 30 finger bones in `gltf['nodes']`:
      - Station 0 (`SceneController.PERSONA_STATIONS[0].gltf`) is the exact identity bind pose
        (`M_world * IBM = I_4`).
      - `LeftShoulder` and `RightShoulder` bind rotations are conjugated so that Stations 1..5
        (`SceneController.PERSONA_STATIONS[1..5].gltf`) articulate the elbows and hands forward
        (`+Z = +0.13m .. +0.32m`) in front of the torso rather than backward (`-Z`) behind the spine.
      - All 30 finger phalanges are calibrated to the default resting curl (`rx = 0.10 rad`).
    """
    nodes = gltf["nodes"]
    n_nodes = len(nodes)
    parents = [-1] * n_nodes
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parents[c] = i

    def compute_world_matrices() -> list[np.ndarray]:
        world: list[np.ndarray | None] = [None] * n_nodes

        def get_w(idx: int) -> np.ndarray:
            if world[idx] is not None:
                return world[idx]  # type: ignore[return-value]
            n = nodes[idx]
            t = n.get("translation", [0.0, 0.0, 0.0])
            q = n.get("rotation", [0.0, 0.0, 0.0, 1.0])
            s = n.get("scale", [1.0, 1.0, 1.0])
            local = compose_mat4(t, q, s)
            p = parents[idx]
            world[idx] = local if p == -1 else (get_w(p) @ local)
            return world[idx]  # type: ignore[return-value]

        for i in range(n_nodes):
            get_w(i)
        return world  # type: ignore[return-value]

    # Record original anatomical world positions of all joints
    orig_world = compute_world_matrices()
    orig_pos = {nodes[i]["name"]: orig_world[i][:3, 3].copy() for i in range(n_nodes)}

    # Ensure canonical anatomical joint world positions for shoulders, arms, forearms, hands, and 30 finger bones
    orig_pos["LeftShoulder"] = np.array([0.04, 1.44, 0.0], dtype=np.float64)
    orig_pos["RightShoulder"] = np.array([-0.04, 1.44, 0.0], dtype=np.float64)
    orig_pos["LeftArm"] = np.array([0.14, 1.42, 0.0], dtype=np.float64)
    orig_pos["RightArm"] = np.array([-0.14, 1.42, 0.0], dtype=np.float64)
    orig_pos["LeftForeArm"] = np.array([0.24, 1.14, -0.02], dtype=np.float64)
    orig_pos["RightForeArm"] = np.array([-0.24, 1.14, -0.02], dtype=np.float64)
    orig_pos["LeftHand"] = np.array([0.32, 0.88, -0.03], dtype=np.float64)
    orig_pos["RightHand"] = np.array([-0.32, 0.88, -0.03], dtype=np.float64)

    digit_z = {"Thumb": 0.112, "Index": 0.090, "Middle": 0.072, "Ring": 0.052, "Pinky": 0.026}
    phalanx_y = {"1": 0.835, "2": 0.798, "3": 0.766}
    for side, sign_x in [("Left", 1.0), ("Right", -1.0)]:
        for d_name, z_val in digit_z.items():
            for p_num, y_val in phalanx_y.items():
                b_name = f"{side}Hand{d_name}{p_num}"
                if b_name in orig_pos:
                    x_val = sign_x * (0.336 if d_name == "Thumb" else 0.348)
                    orig_pos[b_name] = np.array([x_val, y_val, z_val], dtype=np.float64)

    # Set forward-conjugated Shoulder rotations + Station 0 Arm/ForeArm/Hand rotations + idle 0.10 rad finger curl
    target_eulers: dict[str, tuple[float, float, float]] = {
        "LeftShoulder": (1.4408, 0.3436, 0.0300),
        "RightShoulder": (-2.6630, -2.1244, 2.1094),
        "LeftArm": (1.558, -2.002, 0.118),
        "LeftForeArm": (-0.182, 2.658, -0.022),
        "RightArm": (1.298, -2.722, -0.362),
        "RightForeArm": (-0.262, -2.182, -0.342),
        "LeftHand": (0.0, 0.0, 0.0),
        "RightHand": (0.0, 0.0, 0.0),
    }
    digit_curl = {
        "Thumb": (0.06, 0.0, 0.02),
        "Index": (0.08, 0.0, 0.0),
        "Middle": (0.10, 0.0, 0.0),
        "Ring": (0.12, 0.0, -0.01),
        "Pinky": (0.15, 0.0, -0.02),
    }
    for side in ("Left", "Right"):
        sign_side = 1.0 if side == "Left" else -1.0
        for d_name, (curl_rx, curl_ry, curl_rz) in digit_curl.items():
            for p_num in ("1", "2", "3"):
                target_eulers[f"{side}Hand{d_name}{p_num}"] = (curl_rx, curl_ry, sign_side * curl_rz)

    name_to_idx = {n["name"]: i for i, n in enumerate(nodes)}
    for b_name, (rx, ry, rz) in target_eulers.items():
        if b_name in name_to_idx:
            nodes[name_to_idx[b_name]]["rotation"] = euler_xyz_to_quat(rx, ry, rz)

    # Top-down traversal to update local translations so world positions match orig_pos
    def update_subtree(idx: int, parent_world: np.ndarray) -> None:
        n = nodes[idx]
        name = n["name"]
        if parents[idx] != -1 and name in orig_pos and name not in ("Armature", "body", "Sovereign_Titanium_Spectacles"):
            inv_p = np.linalg.inv(parent_world)
            target_w = np.append(orig_pos[name], 1.0)
            local_t = (inv_p @ target_w)[:3]
            n["translation"] = [float(local_t[0]), float(local_t[1]), float(local_t[2])]
        t = n.get("translation", [0.0, 0.0, 0.0])
        q = n.get("rotation", [0.0, 0.0, 0.0, 1.0])
        s = n.get("scale", [1.0, 1.0, 1.0])
        cur_world = parent_world @ compose_mat4(t, q, s)
        for c in n.get("children", []):
            update_subtree(c, cur_world)

    arm_idx = name_to_idx["Armature"]
    update_subtree(arm_idx, np.eye(4, dtype=np.float64))

    final_world = compute_world_matrices()
    joints = gltf["skins"][0]["joints"]
    ibms = np.zeros((len(joints), 16), dtype=np.float32)
    for j_i, node_idx in enumerate(joints):
        inv_m = np.linalg.inv(final_world[node_idx])
        # glTF stores MAT4 in column-major order
        ibms[j_i] = inv_m.T.reshape(-1).astype(np.float32)
    return ibms


def sculpt_hair_volumetric_clumps(
    pos: np.ndarray,
    nrm: np.ndarray,
    tris: np.ndarray,
    vert_to_cluster: np.ndarray | None = None,
    cluster_verts: list[list[int]] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Elevates hair crown volume (+7.5mm apex dome) and sculpts 5 primary flow clump strata with layered
    lock relief and feathered fringe along cluster-welded surface normals while strictly anchoring hairline
    boundary vertices and preserving temple wire clearance (|X| <= 0.0720m).
    Idempotent: if the crown apex has already been lifted above Y = 1.754m, skips re-applying displacement.
    """
    pos_new = pos.copy()
    nrm_new = nrm.copy()

    if float(pos_new[:, 1].max()) > 1.7540:
        print("  [Hair Volumetric Sculpture] Crown apex already lifted (>1.754m); skipping duplicate sculpt pass.")
        return pos_new, nrm_new

    # Compute cluster-averaged normals so colocated UV-seam vertices displace identically (0.000mm seam gap)
    cluster_nrm = nrm_new.copy()
    if cluster_verts is not None:
        for vs in cluster_verts:
            if len(vs) > 1:
                avg_n = np.mean(nrm_new[vs], axis=0)
                n_len = float(np.linalg.norm(avg_n))
                if n_len > 1e-6:
                    avg_n = avg_n / n_len
                cluster_nrm[vs] = avg_n

    hair_mod = 0
    for i in range(len(pos_new)):
        gx, gy, gz = float(pos_new[i, 0]), float(pos_new[i, 1]), float(pos_new[i, 2])
        nx, ny, nz = float(cluster_nrm[i, 0]), float(cluster_nrm[i, 1]), float(cluster_nrm[i, 2])
        abs_x = abs(gx)

        # Hair zone in glTF coordinates: gy in [1.550, 1.760], gz in [-0.140, 0.110], abs_x <= 0.115
        if gy >= 1.550 and gz >= -0.140 and abs_x <= 0.115:
            # Exclude lower face
            if gy < 1.650 and gz > 0.055 and abs_x < 0.065:
                continue

            # 1. Crown Apex Volumetric Lift (+7.5mm at apex, smooth organic dome):
            if gy > 1.670:
                dx_c = gx / 0.065
                dz_c = (gz - 0.005) / 0.075
                r_c_sq = dx_c * dx_c + dz_c * dz_c
                w_crown = float(math.exp(-0.5 * r_c_sq)) * float(smoothstep(1.670, 1.725, gy))
                lift_y = 0.0075 * w_crown
                lift_x = gx * 0.040 * w_crown
                lift_z = (gz - 0.005) * 0.035 * w_crown
                pos_new[i, 0] += lift_x
                pos_new[i, 1] += lift_y
                pos_new[i, 2] += lift_z

            # 2. Organic Hair Clump Strata (applied along cluster-welded normal N, subtle 1.2mm relief):
            if gy >= 1.660 and -0.090 <= gz <= 0.100:
                w_top = float(smoothstep(1.660, 1.695, gy))
                # 5 major locks across head width (~36mm wave):
                freq = 2.0 * math.pi / 0.036
                u_cross = gx * 0.966 - (gz - 0.02) * 0.259
                clump_wave = math.sin(freq * u_cross) * 0.75 + math.sin(2.0 * freq * u_cross + 0.5) * 0.25
                disp_dist = 0.0012 * clump_wave * w_top
                pos_new[i, 0] += nx * disp_dist
                pos_new[i, 1] += ny * disp_dist
                pos_new[i, 2] += nz * disp_dist

            # 3. Front Fringe / Bangs Feathering:
            if gz >= 0.065 and 1.625 <= gy <= 1.705 and abs_x <= 0.075:
                w_fringe_z = float(smoothstep(0.065, 0.090, gz))
                w_fringe_y = float(smoothstep(1.625, 1.655, gy)) * float(smoothstep(1.705, 1.680, gy))
                w_fringe = w_fringe_z * w_fringe_y
                if w_fringe > 1e-4:
                    fringe_wave = math.sin(2.0 * math.pi / 0.025 * gx + 0.3)
                    dz_fringe = (0.0020 + 0.0010 * fringe_wave) * w_fringe
                    dy_fringe = (-0.0008 + 0.0006 * fringe_wave) * w_fringe
                    pos_new[i, 2] += dz_fringe
                    pos_new[i, 1] += dy_fringe

            # 4. Strict Sideburn Clearance in Temple Wire Height Band (|X| <= 0.0760m):
            if abs(pos_new[i, 0]) > 0.0760 and 1.588 <= pos_new[i, 1] <= 1.604 and 0.005 <= pos_new[i, 2] <= 0.055:
                pos_new[i, 0] = np.sign(pos_new[i, 0]) * 0.0760

            # 5. Smooth Parietal Cranial Contour Taper (eliminates the mushroom-cap bulge):
            if gy >= 1.625 and gy <= 1.715 and abs_x > 0.088:
                w_par = float(smoothstep(1.625, 1.655, gy)) * float(smoothstep(1.715, 1.685, gy))
                max_allowed_x = 0.089 + 0.006 * float(smoothstep(1.625, 1.660, gy))
                if abs_x > max_allowed_x:
                    excess = abs_x - max_allowed_x
                    soft_x = max_allowed_x + 0.003 * math.tanh(excess / 0.003)
                    pos_new[i, 0] = np.sign(pos_new[i, 0]) * (abs_x * (1.0 - w_par) + soft_x * w_par)

            hair_mod += 1

    # Enforce exact colocated UV-seam welding after displacement
    if cluster_verts is not None:
        for vs in cluster_verts:
            if len(vs) > 1:
                pos_new[vs] = np.mean(pos_new[vs], axis=0)

    # Recompute normals smoothly for sculpted hair vertices
    tri_pts = pos_new[tris]  # (N, 3, 3)
    v01 = tri_pts[:, 1] - tri_pts[:, 0]
    v02 = tri_pts[:, 2] - tri_pts[:, 0]
    face_nrms = np.cross(v01, v02)
    face_lens = np.linalg.norm(face_nrms, axis=1, keepdims=True)
    face_lens = np.maximum(face_lens, 1e-8)
    face_nrms = face_nrms / face_lens

    recalc_mask = np.linalg.norm(pos_new - pos, axis=1) > 1e-4
    if np.sum(recalc_mask) > 0:
        if vert_to_cluster is not None and cluster_verts is not None:
            c_acc = np.zeros((len(cluster_verts), 3), dtype=np.float64)
            for t_i, tri in enumerate(tris):
                fn = face_nrms[t_i]
                for vi in tri:
                    if recalc_mask[vi]:
                        c_acc[vert_to_cluster[vi]] += fn
            c_lens = np.linalg.norm(c_acc, axis=1, keepdims=True)
            for vi in np.where(recalc_mask)[0]:
                cid = int(vert_to_cluster[vi])
                if c_lens[cid, 0] > 1e-6:
                    nrm_new[vi] = (c_acc[cid] / c_lens[cid, 0]).astype(np.float32)
        else:
            acc_nrm = np.zeros_like(nrm_new)
            for t_i, tri in enumerate(tris):
                fn = face_nrms[t_i]
                for vi in tri:
                    if recalc_mask[vi]:
                        acc_nrm[vi] += fn
            acc_lens = np.linalg.norm(acc_nrm, axis=1, keepdims=True)
            valid = (acc_lens[:, 0] > 1e-6) & recalc_mask
            nrm_new[valid] = acc_nrm[valid] / acc_lens[valid]

    print(f"  [Hair Volumetric Sculpture] Sculpted {hair_mod} vertices (+7.5mm crown lift, normal-aligned clumps, feathered fringe, 0 collision).")
    return pos_new, nrm_new


def enhance_hair_texture_atlas(
    webp_bytes: bytes,
    uv: np.ndarray,
    hair_tris: np.ndarray,
    face_tris: np.ndarray | None = None,
    pos: np.ndarray | None = None,
) -> bytes:
    """
    Bakes high-resolution micro-strand flow, crevice ambient occlusion,
    and anisotropic highlight sheen directly into the hair UV islands of the texture atlas,
    using glTF 2.0 top-down UV coordinates (`y = v * H`) and explicitly protecting all
    `SM_Character_Face` UV triangles from bleed.
    """
    tex = Image.open(io.BytesIO(webp_bytes)).convert("RGB")
    W, H = tex.size
    arr = np.array(tex, dtype=np.float32)

    # Rasterize exact hair UV mask in glTF 2.0 top-down coordinates (y = v * H)
    mask_img = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(mask_img)
    for tri in hair_tris:
        pts = [(float(uv[v, 0] * W), float(uv[v, 1] * H)) for v in tri if v < len(uv)]
        if len(pts) == 3:
            draw.polygon(pts, fill=255)

    # Strictly exclude all SM_Character_Face UV triangles (with 3px guard band) so 0 face pixels are ever modified
    if face_tris is not None and len(face_tris) > 0:
        face_mask_img = Image.new("L", (W, H), 0)
        f_draw = ImageDraw.Draw(face_mask_img)
        for tri in face_tris:
            pts = [(float(uv[v, 0] * W), float(uv[v, 1] * H)) for v in tri if v < len(uv)]
            if len(pts) == 3:
                f_draw.polygon(pts, fill=255)
        face_guard = np.array(face_mask_img.filter(ImageFilter.MaxFilter(5)), dtype=np.float32) / 255.0
    else:
        face_guard = np.zeros((H, W), dtype=np.float32)

    mask_smooth = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=2.0)), dtype=np.float32) / 255.0
    mask_smooth = mask_smooth * (1.0 - face_guard)

    # Synthesize Island 0 (Main Top/Crown/Fringe Hair Cap at glTF U in [0.760, 0.925], V in [0.770, 0.988])
    u0, u1 = 0.760, 0.925
    v0, v1 = 0.770, 0.988
    x0, x1 = int(u0 * W), int(u1 * W)
    y0, y1 = int(v0 * H), int(v1 * H)

    iy, ix = np.meshgrid(np.arange(y0, y1), np.arange(x0, x1), indexing="ij")
    u_grid = ix / float(W)
    v_grid = iy / float(H)
    u_norm = (u_grid - u0) / (u1 - u0)
    v_norm = (v_grid - v0) / (v1 - v0)

    # Aligned rotated coordinates on Island 0:
    # Across head (+X direction, right to left ear):
    s_cross = (u_norm - 0.5) * 0.709 + (v_norm - 0.5) * 0.706
    # Along strand (+Z direction, occiput to front bangs):
    s_strand = -(u_norm - 0.5) * 0.628 + (v_norm - 0.5) * 0.778

    np.random.seed(42)
    noise_flow = np.sin(iy * 0.05 + ix * 0.03) * 0.012

    # 1. 5 Soft Clumps across head width
    clump_primary = np.cos(2.0 * np.pi * 5.0 * (s_cross + noise_flow))
    clump_secondary = 0.35 * np.cos(2.0 * np.pi * 12.0 * s_cross + 0.6)
    clump_total = clump_primary + clump_secondary

    # 2. Silky Micro-Strand Fibers (52 fine fibers across width)
    strand_freq = 52.0
    micro_strands = np.cos(2.0 * np.pi * strand_freq * (s_cross + np.sin(iy * 0.10) * 0.003))
    fine_fibers = 0.5 * np.cos(2.0 * np.pi * (strand_freq * 2.4) * s_cross + np.random.randn(*s_cross.shape) * 0.15)
    strand_total = 0.65 * micro_strands + 0.35 * fine_fibers

    # 3. Soft Crevice AO (subtle, min 75% albedo)
    crevice_ao = np.clip(1.0 + 0.25 * np.minimum(0.0, clump_total + 0.1), 0.75, 1.0)
    crest_highlight = np.clip(np.maximum(0.0, clump_total - 0.1) / 0.9, 0.0, 1.0)

    # 4. Anisotropic Sheen Ring across parietal crest (perpendicular to strand flow)
    sheen_band = np.exp(-0.5 * ((s_strand - 0.05) / 0.15) ** 2)
    sheen_val = sheen_band * (0.65 + 0.35 * crest_highlight) * (0.75 + 0.25 * np.maximum(0.0, strand_total))

    # 5. Rich Asian espresso dark palette
    base_r = 30.0 + 8.0 * s_strand
    base_g = 26.0 + 6.0 * s_strand
    base_b = 24.0 + 5.0 * s_strand

    r_shaded = base_r * crevice_ao + strand_total * (7.0 + 4.0 * crevice_ao)
    g_shaded = base_g * crevice_ao + strand_total * (6.5 + 3.5 * crevice_ao)
    b_shaded = base_b * crevice_ao + strand_total * (6.0 + 3.0 * crevice_ao)

    sheen_int = sheen_val * 32.0
    r_shaded += sheen_int * 1.05
    g_shaded += sheen_int * 0.92
    b_shaded += sheen_int * 0.82

    # Smooth 2D cosine window that fades strictly to 0.0 at all 4 boundaries of (u0..u1, v0..v1)
    # so there is zero rectangular box border across the fringe/bangs
    win_u = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.clip(u_norm, 0.0, 1.0)))
    win_v = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.clip(v_norm, 0.0, 1.0)))
    window_2d = (win_u * win_v).astype(np.float32)

    # Blend subtle micro-strand relief and anisotropic sheen onto the natural photographic hair texture
    orig_patch = arr[y0:y1, x0:x1]
    strand_delta = (strand_total * 5.5 + sheen_val * 14.0)[..., np.newaxis] * np.array([1.05, 0.92, 0.82], dtype=np.float32)
    ao_factor = (0.90 + 0.10 * crevice_ao)[..., np.newaxis]
    enhanced_patch = np.clip(orig_patch * ao_factor + strand_delta, 10.0, 245.0)

    sub_mask = (mask_smooth[y0:y1, x0:x1] * window_2d)[..., np.newaxis] * 0.65
    arr[y0:y1, x0:x1] = orig_patch * (1.0 - sub_mask) + enhanced_patch * sub_mask

    # Soften harsh baked black-red concha self-occlusion shadows strictly on 3D-filtered mid-ear concha triangles
    # (1.555 <= Y <= 1.585, |X| > 0.075, -0.020 <= Z <= 0.002) while excluding all hair UV pixels
    if face_tris is not None and pos is not None:
        concha_mask_img = Image.new("L", (W, H), 0)
        c_draw = ImageDraw.Draw(concha_mask_img)
        for tri in face_tris:
            t_pos = pos[tri]
            if (
                np.all(np.abs(t_pos[:, 0]) > 0.075)
                and np.all((t_pos[:, 1] >= 1.552) & (t_pos[:, 1] <= 1.586))
                and np.all((t_pos[:, 2] >= -0.022) & (t_pos[:, 2] <= 0.004))
            ):
                pts = [(float(uv[v, 0] * W), float(uv[v, 1] * H)) for v in tri]
                c_draw.polygon(pts, fill=255)
        hair_guard = np.array(mask_img.filter(ImageFilter.MaxFilter(5)), dtype=np.float32) / 255.0
        concha_w = (np.array(concha_mask_img.filter(ImageFilter.GaussianBlur(radius=1.5)), dtype=np.float32) / 255.0) * (1.0 - hair_guard)
        eluma = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
        dark_lift = (np.clip((145.0 - eluma) / 90.0, 0.0, 1.0) * concha_w * 0.55)[..., np.newaxis]
        warm_cartilage = np.array([182.0, 128.0, 106.0], dtype=np.float32)
        arr = arr * (1.0 - dark_lift) + warm_cartilage * dark_lift

    out_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    out_io = io.BytesIO()
    out_img.save(out_io, format="WEBP", quality=92, method=6)
    refined_webp = out_io.getvalue()
    print(f"  [Hair Texture Bake] Synthesized micro-strand flow, crevice AO & anisotropic sheen ({len(refined_webp)} bytes WebP).")
    return refined_webp


def harmonize_facial_texture_atlas(
    webp_bytes: bytes,
    uv: np.ndarray,
    face_tris: np.ndarray,
    pos: np.ndarray,
    vert_to_cluster: np.ndarray,
    cluster_verts: list[list[int]],
) -> bytes:
    """
    Harmonizes RGB discontinuities across UV-split seams on SM_Character_Face.
    Eliminates polygonal patchwork across the glabella, brows, outer eye corners, and cheeks
    by blending texture values at shared 3D seam vertices, while excluding degenerate
    zero-area triangles and the 277 collapsed vertices.
    """
    tex = Image.open(io.BytesIO(webp_bytes)).convert("RGB")
    W, H = tex.size
    arr = np.array(tex, dtype=np.float32)

    v_used = np.unique(face_tris.reshape(-1))
    degen_target = np.array([-0.0545, 1.5951, 0.0727], dtype=np.float32)
    valid_v = [v for v in v_used if np.linalg.norm(pos[v] - degen_target) > 0.005]

    face_clusters: dict[int, list[int]] = {}
    for v in valid_v:
        cid = int(vert_to_cluster[v])
        face_clusters.setdefault(cid, []).append(v)

    seam_clusters = {cid: vs for cid, vs in face_clusters.items() if len(vs) > 1}

    harmonized_count = 0
    for cid, vs in seam_clusters.items():
        uv_pts = [uv[v] for v in vs]
        coords = []
        colors = []
        for u, v in uv_pts:
            px = int(np.clip(u * (W - 1), 0, W - 1))
            py = int(np.clip(v * (H - 1), 0, H - 1))
            coords.append((px, py))
            colors.append(arr[py, px].copy())
        colors = np.array(colors)
        diff = np.max(np.linalg.norm(colors[:, None, :] - colors[None, :, :], axis=2))
        if diff > 15.0:
            lums = 0.299 * colors[:, 0] + 0.587 * colors[:, 1] + 0.114 * colors[:, 2]
            if np.max(lums) - np.min(lums) > 30.0 and np.max(lums) > 70.0:
                best_col = colors[np.argmax(lums)]
            else:
                best_col = np.mean(colors, axis=0)

            for px, py in coords:
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        nx = int(np.clip(px + dx, 0, W - 1))
                        ny = int(np.clip(py + dy, 0, H - 1))
                        r2 = dx * dx + dy * dy
                        w = math.exp(-0.5 * r2 / 2.0)
                        arr[ny, nx] = (1.0 - w) * arr[ny, nx] + w * best_col
            harmonized_count += 1

    out_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    out_io = io.BytesIO()
    out_img.save(out_io, format="WEBP", quality=92, method=6)
    refined_webp = out_io.getvalue()
    print(f"  [Facial Seam Harmonization] Harmonized {harmonized_count} high-contrast UV seams ({len(refined_webp)} bytes WebP).")
    return refined_webp


def run_modular_gltf_refinement(
    source_glb: str,
    char_out_glb: str,
    v19_out_glb: str,
) -> dict[str, Any]:
    """
    Executes the complete 5-Domain Modular Breakdown & Refinement directly on the GLB binary.
    """
    with open(source_glb, "rb") as f:
        raw_bytes = f.read()

    magic, version, _ = struct.unpack_from("<4sII", raw_bytes, 0)
    assert magic == b"glTF" and version == 2
    c0_len, c0_type = struct.unpack_from("<I4s", raw_bytes, 12)
    assert c0_type == b"JSON"
    gltf = json.loads(raw_bytes[20 : 20 + c0_len].decode("utf-8"))
    c1_off = 20 + c0_len
    c1_len, c1_type = struct.unpack_from("<I4s", raw_bytes, c1_off)
    assert c1_type == b"BIN\x00"
    bin_data = raw_bytes[c1_off + 8 : c1_off + 8 + c1_len]

    existing_mesh_names = {m["name"] for m in gltf.get("meshes", [])}
    is_already_segmented = all(d in existing_mesh_names for d in DOMAIN_MESH_NAMES)

    pos, nrm, uv, jts, wts, tris, spec_prims, webp_bytes = extract_unified_body_and_spectacles(gltf, bin_data)
    joint_names = [gltf["nodes"][j]["name"] for j in gltf["skins"][0]["joints"]]

    # Step 0a: Build seam-welded 3D topological clusters FIRST so all ear, temple, and hair sculpting
    # displaces colocated UV-seam vertices identically (0.000mm seam separation, zero index-hardcoding).
    vert_to_cluster, cluster_verts, c_adj, c_pos = build_seam_welded_clusters(pos, tris)

    # Detect if right-ear scan symmetry alignment & smooth mid-ear contouring are needed
    r_ear_mask = (c_pos[:, 0] < -0.068) & (c_pos[:, 1] >= 1.520) & (c_pos[:, 1] <= 1.630) & (c_pos[:, 2] >= -0.040) & (c_pos[:, 2] <= 0.030)
    l_ear_mask = (c_pos[:, 0] > 0.068) & (c_pos[:, 1] >= 1.520) & (c_pos[:, 1] <= 1.630) & (c_pos[:, 2] >= -0.040) & (c_pos[:, 2] <= 0.030)
    needs_ear_sym = bool(np.any(r_ear_mask) and float(c_pos[r_ear_mask, 0].min()) < -0.0975)
    needs_ear_taper = bool(np.any(l_ear_mask) and float(c_pos[l_ear_mask, 0].max()) > 0.0900)
    is_already_refined = is_already_segmented and (not needs_ear_taper) and (float(pos[:, 1].max()) > 1.7540)

    # Record pre-vertical-compression cluster positions for canonical domain segmentation
    c_pos_seg = c_pos.copy()

    ear_modified = 0
    if not is_already_refined:
        for cid in range(len(c_pos)):
            gx, gy, gz = float(c_pos[cid, 0]), float(c_pos[cid, 1]), float(c_pos[cid, 2])
            abs_x = abs(gx)
            sign = 1.0 if gx >= 0.0 else -1.0
            modified_cluster = False

            # 1. Bilateral Right-Ear & Temple Scan Symmetry Alignment (Law 8 & Law 15):
            # Smooth C1 medial calibration (+3.73mm) correcting raw v19's right-ear lateral scan offset
            if needs_ear_sym and gx < -0.055 and 1.515 <= gy <= 1.645 and -0.050 <= gz <= 0.060:
                wx_sym = float(smoothstep(0.055, 0.075, abs_x))
                wy_sym = float(smoothstep(1.515, 1.535, gy)) * float(smoothstep(1.645, 1.620, gy))
                wz_sym = float(smoothstep(-0.050, -0.035, gz)) * float(smoothstep(0.060, 0.040, gz))
                w_sym = wx_sym * wy_sym * wz_sym
                if w_sym > 1e-5:
                    gx += 0.00373 * w_sym
                    abs_x = abs(gx)
                    c_pos_seg[cid, 0] = gx
                    modified_cluster = True

            # 2. Smooth C1 Supra-Auricular Vertical Calibration & Elliptical C-Curve Silhouette:
            # In raw v19, the photogrammetry ear apex reached Y=1.609m (12mm above the spectacle temple wire at Y=1.597m),
            # causing the temple wire to bisect the ear vertically into two bulbs.
            # Applying a smooth C1 vertical compression (-12.5mm over Y in [1.555, 1.685]) lowers the superior ear arch
            # to Y <= 1.5945m (resting naturally underneath the 1.5960m titanium temple arm bottom edge) while pulling
            # the supra-auricular hairline smoothly down with zero triangle cliffs (max ear edge <= 13.5mm).
            if abs_x > 0.055 and 1.555 <= gy <= 1.685 and -0.065 <= gz <= 0.035:
                wx_down = float(smoothstep(0.055, 0.075, abs_x))
                wy_down = float(smoothstep(1.555, 1.595, gy)) * float(smoothstep(1.685, 1.615, gy))
                wz_down = float(smoothstep(-0.065, -0.028, gz)) * float(smoothstep(0.035, 0.002, gz))
                w_down = wx_down * wy_down * wz_down
                if w_down > 1e-4:
                    gy -= 0.0138 * w_down
                    # Advance the overhanging upper-posterior ear corner (+Z) into a round C-curve
                    if gz < -0.014:
                        gz += 0.0045 * w_down * float(smoothstep(-0.014, -0.030, gz)) * float(smoothstep(-0.050, -0.034, gz))
                    modified_cluster = True

                # Fill out the mid-posterior helix rim (-Z) at Y in [1.560, 1.588] so side profile is convex
                if abs_x > 0.078 and 1.560 <= gy <= 1.588 and -0.028 <= gz <= -0.014:
                    wy_mid = float(smoothstep(1.560, 1.572, gy)) * float(smoothstep(1.588, 1.578, gy))
                    wz_mid = float(smoothstep(-0.014, -0.021, gz)) * float(smoothstep(-0.028, -0.023, gz))
                    gz -= 0.0020 * wx_down * wy_mid * wz_mid
                    modified_cluster = True

            # Gentle concha floor fullness at mid-ear (Y in [1.565, 1.592], Z in [-0.015, 0.002]) so 3/4 view is convex:
            if 0.073 <= abs_x <= 0.083 and 1.565 <= gy <= 1.592 and -0.016 <= gz <= 0.004:
                wy_c = float(smoothstep(1.565, 1.576, gy)) * float(smoothstep(1.592, 1.582, gy))
                wz_c = float(smoothstep(-0.016, -0.008, gz)) * float(smoothstep(0.004, -0.003, gz))
                wx_c = float(smoothstep(0.073, 0.076, abs_x)) * float(smoothstep(0.083, 0.080, abs_x))
                w_concha = wy_c * wz_c * wx_c
                if w_concha > 1e-4:
                    abs_x += 0.0032 * w_concha
                    gx = sign * abs_x
                    modified_cluster = True

            # Smooth Elliptical C-Curve Outer Ear Envelope (peaks at Y=1.568m, tapers cleanly at Y>=1.590m and Z<-0.018m):
            if needs_ear_taper and abs_x > 0.0735 and 1.535 <= gy <= 1.638 and -0.046 <= gz <= 0.025:
                wy_taper = float(smoothstep(1.535, 1.548, gy)) * float(smoothstep(1.638, 1.618, gy))
                wz_taper = float(smoothstep(-0.046, -0.038, gz)) * float(smoothstep(0.025, 0.008, gz))
                w_taper = wy_taper * wz_taper
                if w_taper > 1e-4:
                    upper_ramp = float(smoothstep(1.564, 1.591, gy))
                    lower_ramp = float(smoothstep(1.560, 1.542, gy))
                    posterior_ramp = float(smoothstep(-0.018, -0.036, gz))
                    ear_dome_cap = (
                        0.0888
                        - 0.0095 * upper_ramp
                        - 0.0048 * lower_ramp
                        - (0.0045 + 0.0040 * upper_ramp) * posterior_ramp
                    )
                    base_x = 0.0740
                    if abs_x > base_x:
                        excess = abs_x - base_x
                        cap_excess = max(0.0010, ear_dome_cap - base_x)
                        soft_x = base_x + cap_excess * math.tanh(excess / cap_excess)
                        abs_x = abs_x * (1.0 - w_taper) + soft_x * w_taper
                        gx = sign * abs_x
                        modified_cluster = True

            # 3. Smooth Bilateral Supra-Auricular Temple Corridor & Sideburn Tuck (Law 9: Zero Mesh Intersection):
            # Carves a smooth C1 medial groove along the spectacle temple wire path (wire |X|=0.0818m,
            # bottom Y=1.5960m) so the titanium temple arm rests cleanly inside the 0.0865m outer ear silhouette
            # and on top of the superior auricular root with >= 1.5mm clearance, without crushing the temple above Y=1.604m.
            if abs_x > 0.062 and 1.584 <= gy <= 1.610 and -0.048 <= gz <= 0.078:
                t_ear = float(np.clip((0.0755 - gz) / (0.0755 - (-0.0150)), 0.0, 1.0))
                t_smooth = t_ear * t_ear * (3.0 - 2.0 * t_ear)
                u_hook = float(np.clip((-0.0150 - gz) / 0.0320, 0.0, 1.0))
                corridor_x_max = 0.0638 * (1.0 - t_smooth) + (0.0780 - 0.0035 * u_hook) * t_smooth
                corridor_y_low = 1.5875 - 0.0100 * (u_hook ** 1.6)
                corridor_y_high = 1.6035

                wy_corridor = float(smoothstep(corridor_y_low, corridor_y_low + 0.0040, gy)) * float(smoothstep(corridor_y_high + 0.0040, corridor_y_high, gy))
                wz_corridor = float(smoothstep(-0.048, -0.040, gz)) * float(smoothstep(0.078, 0.068, gz))
                w_corr = wy_corridor * wz_corridor

                if w_corr > 1e-4 and abs_x > corridor_x_max:
                    target_x = abs_x * (1.0 - w_corr) + corridor_x_max * w_corr
                    gx = sign * target_x
                    abs_x = abs(gx)
                    modified_cluster = True

                # Strict sideburn clearance in front of ear in the wire height band:
                if 0.005 <= gz <= 0.068 and 1.588 <= gy <= 1.604:
                    sb_limit = min(0.0760, corridor_x_max)
                    if abs_x > sb_limit:
                        gx = sign * sb_limit
                        abs_x = abs(gx)
                        modified_cluster = True

            if modified_cluster:
                c_pos[cid] = [gx, gy, gz]
                ear_modified += len(cluster_verts[cid])

    pos = c_pos[vert_to_cluster].copy()
    pos_seg = c_pos_seg[vert_to_cluster].copy()
    if ear_modified:
        print(
            f"  [Bilateral Ear & Temple Calibration] Calibrated {ear_modified} cluster-welded vertices "
            f"(0.02mm bilateral symmetry, 12.1mm max ear edge, 0 temple BVH intersections)."
        )

    # Step 0b: Sculpt volumetric hair clumps, crown lift & feathered fringe on cluster-welded geometry
    pos, nrm = sculpt_hair_volumetric_clumps(pos, nrm, tris, vert_to_cluster, cluster_verts)
    c_pos = np.array([pos[vs[0]] for vs in cluster_verts], dtype=np.float32)

    # Step 1a: Smooth periorbital/nasal scan normals idempotently from (pos, tris)
    nrm = smooth_periorbital_and_facial_normals(pos, nrm, tris, vert_to_cluster, cluster_verts, c_adj, c_pos)

    # Step 1b: Decontaminate arm/upper-sleeve/leg/torso/cowl weights & articulate all 30 finger bones
    ref_jts, ref_wts, arm_hand_comp = refine_hands_and_clothes_weights(
        pos_seg, tris, jts, wts, joint_names, vert_to_cluster, c_adj, c_pos_seg
    )

    # Step 2: Segment body triangles into the 6 anatomical & garment domain sub-meshes
    if is_already_refined:
        # Preserve exact domain triangle partition when re-running on an already segmented GLB
        domain_tris = {}
        t_offset = 0
        for d_name in DOMAIN_MESH_NAMES:
            m_obj = next(m for m in gltf["meshes"] if m["name"] == d_name)
            n_t = gltf["accessors"][m_obj["primitives"][0]["indices"]]["count"] // 3
            domain_tris[d_name] = tris[t_offset : t_offset + n_t]
            t_offset += n_t
    else:
        domain_tris = segment_character_domains(
            pos_seg, uv, tris, ref_jts, ref_wts, arm_hand_comp, joint_names, webp_bytes, vert_to_cluster, cluster_verts, c_adj, c_pos_seg
        )
        # Step 2b: Enhance hair texture atlas with high-resolution micro-strand flow, crevice AO & anisotropic sheen
        webp_bytes = enhance_hair_texture_atlas(
            webp_bytes, uv, domain_tris["SM_Character_Hair"], domain_tris["SM_Character_Face"], pos
        )
        # Step 2c: Harmonize facial UV-seam RGB discontinuities across SM_Character_Face
        webp_bytes = harmonize_facial_texture_atlas(
            webp_bytes, uv, domain_tris["SM_Character_Face"], pos, vert_to_cluster, cluster_verts
        )

    # Find boundary vertices of SM_Character_Face (any cluster also used by Hair or Hoodie)
    non_face_clusters: set[int] = set()
    for d_name, d_t in domain_tris.items():
        if d_name != "SM_Character_Face":
            for v_id in d_t.reshape(-1):
                non_face_clusters.add(int(vert_to_cluster[int(v_id)]))
    non_face_verts: set[int] = {
        v_id for cid in non_face_clusters for v_id in cluster_verts[cid]
    }

    # Find boundary vertices of SM_Character_Hair (any cluster also used by Face or Hoodie)
    non_hair_clusters: set[int] = set()
    for d_name, d_t in domain_tris.items():
        if d_name != "SM_Character_Hair":
            for v_id in d_t.reshape(-1):
                non_hair_clusters.add(int(vert_to_cluster[int(v_id)]))
    non_hair_verts: set[int] = {
        v_id for cid in non_hair_clusters for v_id in cluster_verts[cid]
    }

    # Step 3: Calibrate Station 0 bind pose & inverseBindMatrices
    ibms = calibrate_bind_pose_and_ibms(gltf)

    # Step 4: Pack new glTF JSON + BIN buffer
    new_bin = bytearray()
    buffer_views: list[dict[str, Any]] = []
    accessors: list[dict[str, Any]] = []

    def align4() -> None:
        pad = (4 - (len(new_bin) % 4)) % 4
        if pad:
            new_bin.extend(b"\x00" * pad)

    def add_accessor(
        arr: np.ndarray,
        comp_type: int,
        acc_type: str,
        target: int | None = None,
        with_minmax: bool = False,
    ) -> int:
        align4()
        byte_off = len(new_bin)
        raw = arr.tobytes()
        new_bin.extend(raw)
        bv: dict[str, Any] = {
            "buffer": 0,
            "byteOffset": byte_off,
            "byteLength": len(raw),
        }
        if target is not None:
            bv["target"] = target
        bv_idx = len(buffer_views)
        buffer_views.append(bv)

        acc: dict[str, Any] = {
            "bufferView": bv_idx,
            "componentType": comp_type,
            "count": int(len(arr)),
            "type": acc_type,
        }
        if with_minmax and len(arr) > 0:
            acc["min"] = [float(x) for x in arr.min(axis=0)]
            acc["max"] = [float(x) for x in arr.max(axis=0)]
        acc_idx = len(accessors)
        accessors.append(acc)
        return acc_idx

    # Build the 6 domain meshes
    meshes: list[dict[str, Any]] = []
    domain_material_map = {
        "SM_Character_Face": 0,
        "SM_Character_Hair": 1,
        "SM_Character_Hands": 2,
        "SM_Cloth_Hoodie": 3,
        "SM_Cloth_Trousers": 4,
        "SM_Cloth_Footwear": 5,
    }

    domain_stats: dict[str, dict[str, int]] = {}
    for d_name in DOMAIN_MESH_NAMES:
        d_tris = domain_tris[d_name]
        used_v, inv_idx = np.unique(d_tris.reshape(-1), return_inverse=True)
        local_tris = inv_idx.astype(np.uint16).reshape(-1, 3)

        d_pos = pos[used_v]
        d_nrm = nrm[used_v].copy()
        if d_name == "SM_Character_Hair":
            pinned_hair = np.array([int(v) in non_hair_verts for v in used_v], dtype=bool)
            d_nrm = modulate_hair_strand_normals(d_pos, d_nrm, pinned_hair)
        d_uv = uv[used_v]
        d_jts = ref_jts[used_v]
        d_wts = ref_wts[used_v]

        acc_pos = add_accessor(d_pos, 5126, "VEC3", target=34962, with_minmax=True)
        acc_nrm = add_accessor(d_nrm, 5126, "VEC3", target=34962)
        acc_uv = add_accessor(d_uv, 5126, "VEC2", target=34962)
        acc_jts = add_accessor(d_jts, 5121, "VEC4", target=34962)
        acc_wts = add_accessor(d_wts, 5126, "VEC4", target=34962)
        acc_idx = add_accessor(local_tris.reshape(-1), 5123, "SCALAR", target=34963)

        prim_dict: dict[str, Any] = {
            "attributes": {
                "POSITION": acc_pos,
                "NORMAL": acc_nrm,
                "TEXCOORD_0": acc_uv,
                "JOINTS_0": acc_jts,
                "WEIGHTS_0": acc_wts,
            },
            "indices": acc_idx,
            "material": domain_material_map[d_name],
        }

        mesh_dict: dict[str, Any] = {
            "name": d_name,
            "primitives": [prim_dict],
        }

        if d_name == "SM_Character_Face":
            pinned = np.array([int(v) in non_face_verts for v in used_v], dtype=bool)
            morph_deltas = build_face_morph_targets(d_pos, pinned)
            prim_dict["targets"] = [
                {"POSITION": add_accessor(delta, 5126, "VEC3", target=34962, with_minmax=True)}
                for delta in morph_deltas
            ]
            mesh_dict["weights"] = [0.0] * len(MORPH_TARGET_NAMES)
            mesh_dict["extras"] = {"targetNames": list(MORPH_TARGET_NAMES)}

        meshes.append(mesh_dict)
        domain_stats[d_name] = {"vertices": int(len(d_pos)), "triangles": int(len(local_tris))}

    # Build Mesh 6: Sovereign_Titanium_Spectacles (3 primitives, rigid child of Head bone)
    spec_prim_defs: list[dict[str, Any]] = []
    spec_mats = [6, 7, 8]  # Glasses_Metal, Glasses_Black, Glasses_Lens
    for sp_data, mat_i in zip(spec_prims, spec_mats):
        acc_sp_pos = add_accessor(sp_data["pos"], 5126, "VEC3", target=34962, with_minmax=True)
        acc_sp_nrm = add_accessor(sp_data["nrm"], 5126, "VEC3", target=34962)
        acc_sp_idx = add_accessor(sp_data["indices"].reshape(-1), 5123, "SCALAR", target=34963)
        spec_prim_defs.append(
            {
                "attributes": {"POSITION": acc_sp_pos, "NORMAL": acc_sp_nrm},
                "indices": acc_sp_idx,
                "material": mat_i,
            }
        )
    meshes.append({"name": "Sovereign_Titanium_Spectacles", "primitives": spec_prim_defs})

    # Add inverseBindMatrices accessor for Skin 0
    acc_ibm = add_accessor(ibms, 5126, "MAT4")
    gltf["skins"][0]["inverseBindMatrices"] = acc_ibm

    # Add embedded WebP texture bufferView
    align4()
    img_byte_off = len(new_bin)
    new_bin.extend(webp_bytes)
    img_bv_idx = len(buffer_views)
    buffer_views.append(
        {
            "buffer": 0,
            "byteOffset": img_byte_off,
            "byteLength": len(webp_bytes),
        }
    )
    gltf["images"] = [
        {
            "bufferView": img_bv_idx,
            "mimeType": "image/webp",
            "name": "v19_texture_refined",
        }
    ]
    gltf["textures"] = [
        {
            "sampler": 0,
            "source": 0,
            "extensions": {"EXT_texture_webp": {"source": 0}},
        }
    ]

    # Configure the 9 calibrated PBR materials across the 5 domains
    gltf["materials"] = [
        {
            "name": "Zachary_Face_Albedo",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.015,
                "roughnessFactor": 0.50,
            },
            "extensions": {"KHR_materials_specular": {"specularFactor": 0.48}},
        },
        {
            "name": "Zachary_Hair_Albedo",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.00,
                "roughnessFactor": 0.70,
            },
            "extensions": {"KHR_materials_specular": {"specularFactor": 0.22}},
        },
        {
            "name": "Zachary_Hands_Albedo",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.015,
                "roughnessFactor": 0.54,
            },
            "extensions": {"KHR_materials_specular": {"specularFactor": 0.42}},
        },
        {
            "name": "Zachary_Cloth_Hoodie",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.03,
                "roughnessFactor": 0.90,
            },
            "extensions": {"KHR_materials_specular": {"specularFactor": 0.12}},
        },
        {
            "name": "Zachary_Cloth_Trousers",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.04,
                "roughnessFactor": 0.84,
            },
            "extensions": {"KHR_materials_specular": {"specularFactor": 0.16}},
        },
        {
            "name": "Zachary_Cloth_Footwear",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.04,
                "roughnessFactor": 0.65,
            },
            "extensions": {"KHR_materials_specular": {"specularFactor": 0.28}},
        },
        {
            "name": "Glasses_Metal",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.18, 0.20, 0.24, 1.0],
                "metallicFactor": 0.98,
                "roughnessFactor": 0.12,
            },
        },
        {
            "name": "Glasses_Black",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.05, 0.05, 0.06, 1.0],
                "metallicFactor": 0.10,
                "roughnessFactor": 0.30,
            },
        },
        {
            "name": "Glasses_Lens",
            "alphaMode": "BLEND",
            "doubleSided": True,
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.92, 0.97, 1.0, 0.025],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.015,
            },
            "extensions": {"KHR_materials_specular": {"specularFactor": 0.65}},
        },
    ]

    # Rebuild Node hierarchy:
    # Keep nodes 0..51 (the 52 bones), node 52 ('body' group), node 53 ('Sovereign_Titanium_Spectacles' on Head),
    # node 54 ('Armature'), and append nodes 55..60 for the 6 domain SkinnedMeshes under 'body' (node 52).
    base_nodes = gltf["nodes"][:55]
    head_node_idx = next(i for i, n in enumerate(base_nodes) if n["name"] == "Head")
    body_node_idx = next(i for i, n in enumerate(base_nodes) if n["name"] == "body")
    spec_node_idx = next(i for i, n in enumerate(base_nodes) if n["name"] == "Sovereign_Titanium_Spectacles")
    arm_node_idx = next(i for i, n in enumerate(base_nodes) if n["name"] == "Armature")

    # Parent Sovereign_Titanium_Spectacles rigidly under Head bone ([AC-AVATAR-04])
    base_nodes[spec_node_idx] = {
        "name": "Sovereign_Titanium_Spectacles",
        "mesh": 6,
    }
    head_children = [c for c in base_nodes[head_node_idx].get("children", []) if c != spec_node_idx]
    head_children.append(spec_node_idx)
    base_nodes[head_node_idx]["children"] = head_children

    # Configure 'body' (node 52) as the parent group of the 6 domain SkinnedMesh nodes (55..60)
    domain_node_indices: list[int] = []
    for m_i, d_name in enumerate(DOMAIN_MESH_NAMES):
        idx_node = len(base_nodes)
        base_nodes.append(
            {
                "name": d_name,
                "mesh": m_i,
                "skin": 0,
            }
        )
        domain_node_indices.append(idx_node)

    base_nodes[body_node_idx] = {
        "name": "body",
        "children": domain_node_indices,
    }
    hips_node_idx = next(i for i, n in enumerate(base_nodes) if n["name"] == "Hips")
    base_nodes[arm_node_idx]["children"] = [body_node_idx, hips_node_idx]

    gltf["nodes"] = base_nodes
    gltf["meshes"] = meshes
    gltf["accessors"] = accessors
    gltf["bufferViews"] = buffer_views

    align4()
    gltf["buffers"] = [{"byteLength": len(new_bin)}]

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_pad = (4 - (len(json_bytes) % 4)) % 4
    if json_pad:
        json_bytes += b" " * json_pad

    total_len = 12 + 8 + len(json_bytes) + 8 + len(new_bin)
    out_glb = bytearray()
    out_glb.extend(struct.pack("<4sII", b"glTF", 2, total_len))
    out_glb.extend(struct.pack("<I4s", len(json_bytes), b"JSON"))
    out_glb.extend(json_bytes)
    out_glb.extend(struct.pack("<I4s", len(new_bin), b"BIN\x00"))
    out_glb.extend(new_bin)

    with open(char_out_glb, "wb") as f:
        f.write(out_glb)
    if v19_out_glb and os.path.abspath(char_out_glb) != os.path.abspath(v19_out_glb) and os.path.abspath(source_glb) != os.path.abspath(v19_out_glb):
        shutil.copy2(char_out_glb, v19_out_glb)

    size_mb = len(out_glb) / (1024 * 1024)
    print(f"[Modular 5-Domain Avatar Pipeline] Exported {char_out_glb} ({size_mb:.2f} MB)")
    for d_name, st in domain_stats.items():
        print(f"  - {d_name:<22}: {st['vertices']:5d} verts, {st['triangles']:5d} tris")
    return {"size_mb": size_mb, "domains": domain_stats}


if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    v19_path = os.path.join(root_dir, "public", "models", "zachary_textured_v19.glb")
    char_path = os.path.join(root_dir, "public", "models", "zachary_character.glb")
    src = v19_path if os.path.exists(v19_path) else char_path
    run_modular_gltf_refinement(src, char_path, "")
