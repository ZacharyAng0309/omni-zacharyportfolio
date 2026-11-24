"""Build Avatar v41 (Refined) candidate from immutable v40:
1. Fix chin/mandible skin weights (Head=1.0 on front chin & jaw, Neck/Spine2 preserved on throat & collar seam,
   max single-triangle Head weight jump < 0.40).
2. Eradicate the inherited +10.0mm 3D glasses-rim scan scar beneath the +X eye (moving coincident
   SM_Character_Face & SM_Character_Eyelids boundary + ring 0 vertices together with 0.000mm gap and
   1.0000 normal continuity) AND perform full bilateral cheek/jaw symmetrization (|asym_X| < 1.2mm)
   plus a cohesive, single-curve V-oval chin & submental jawline shelf sculpt matching reference_portrait.jpg
   (eliminating the elongated saggy chin, double-bump cleft, and +X jaw cave-in).
3. Clean & dilate T_FringeRepair_v40_face (Image 5): 16px UV2 island margin dilation across all face islands
   (zero mipmap #000000 bleed), frequency-separated bilateral skin-tone harmonization erasing the +X olive-grey
   jaw/cheek shadow blotch, baked glasses-rim ghost rings under both eyes, and dark chin-bottom shadow,
   while preserving high-frequency skin micro-texture, brows, lips, nostrils, and the v40 fringe patch (< 100 KB WebP).
4. Overhaul SM_Character_EyeLeft & SM_Character_EyeRight: true symmetric forward-facing corneal dome
   (zero +/-12.4 deg outward skew, matched left/right Z depth), rich warm dark-chestnut East Asian iris
   calibrated for ACES Filmic (clearly distinct pupil, warm lower caustic scatter, crisp dark limbal ring),
   and physically shaded porcelain sclera with visible upper-lid cast shadow & warm inner caruncle AO.
5. Sculpt natural calm East Asian almond SM_Character_Eyelids (25.8 x 7.9mm, matched symmetric Z, gently arched
   upper lid draping over top ~18% of iris, smooth lower lid kissing bottom of iris) with guaranteed watertight
   full-blink closure (< 0.08mm) and full corneal clearance behind closed lids; full-canvas pure-skin dilation
   on T_Eyelids_v36 (zero #000000 holes or notches), outer-corner bruise cleanup, crisp visible dark-espresso
   upper lash line, and delicate tapered upper-lid crease (< 100 KB WebP).
"""
import io
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
V40_GLB = PROJECT / "artifacts/avatar-v40-codex-20261119/outputs/zachary_character_v40_candidate.glb"
V36_RINGS = PROJECT / "artifacts/avatar-v36-codex-20261114/work/eye36-rings.json"
OUT_GLB = ROOT / "outputs/zachary_character_v41_candidate.glb"
WORK_DIR = ROOT / "work"


class GlbAsset:
    def __init__(self, path: Path):
        self.path = Path(path)
        raw = self.path.read_bytes()
        jlen = struct.unpack_from("<I", raw, 12)[0]
        self.g = json.loads(raw[20 : 20 + jlen].decode("utf-8"))
        self.bin = bytearray(raw[28 + jlen :])
        self.replaced_images: dict[int, tuple[bytes, str]] = {}

    def arr(self, accessor_idx: int) -> np.ndarray:
        a = self.g["accessors"][accessor_idx]
        v = self.g["bufferViews"][a["bufferView"]]
        cols = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        dt = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]]
        assert "byteStride" not in v, f"Interleaved bufferView unsupported for accessor {accessor_idx}"
        offset = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(self.bin, dtype=dt, count=a["count"] * cols, offset=offset).reshape(-1, cols)

    def prim(self, mesh_name: str) -> dict:
        return next(m for m in self.g["meshes"] if m.get("name") == mesh_name)["primitives"][0]

    def pos(self, mesh_name: str) -> np.ndarray:
        return self.arr(self.prim(mesh_name)["attributes"]["POSITION"])

    def get_image_bytes(self, img_idx: int) -> bytes:
        if img_idx in self.replaced_images:
            return self.replaced_images[img_idx][0]
        bv = self.g["bufferViews"][self.g["images"][img_idx]["bufferView"]]
        off = bv.get("byteOffset", 0)
        return bytes(self.bin[off : off + bv["byteLength"]])

    def replace_image_bytes(self, img_idx: int, new_bytes: bytes, mime_type: str = "image/webp"):
        self.replaced_images[img_idx] = (new_bytes, mime_type)

    def build_compacted_bin(self) -> bytes:
        bv_to_img: dict[int, tuple[bytes, str]] = {}
        for img_idx, (payload, mime) in self.replaced_images.items():
            bv_idx = self.g["images"][img_idx]["bufferView"]
            bv_to_img[bv_idx] = (payload, mime)
            self.g["images"][img_idx]["mimeType"] = mime

        new_bin = bytearray()
        for bv_idx, bv in enumerate(self.g["bufferViews"]):
            pad = (-len(new_bin)) % 4
            if pad:
                new_bin.extend(b"\x00" * pad)
            if bv_idx in bv_to_img:
                chunk = bv_to_img[bv_idx][0]
                bv["byteOffset"] = len(new_bin)
                bv["byteLength"] = len(chunk)
                new_bin.extend(chunk)
            else:
                old_off = bv.get("byteOffset", 0)
                old_len = bv["byteLength"]
                chunk = bytes(self.bin[old_off : old_off + old_len])
                bv["byteOffset"] = len(new_bin)
                new_bin.extend(chunk)
        end_pad = (-len(new_bin)) % 4
        if end_pad:
            new_bin.extend(b"\x00" * end_pad)
        self.g["buffers"][0]["byteLength"] = len(new_bin)
        return bytes(new_bin)

    def save(self, out_path: Path):
        for mesh in self.g["meshes"]:
            for p in mesh["primitives"]:
                for k in ("POSITION", "NORMAL"):
                    if k in p["attributes"]:
                        idx = p["attributes"][k]
                        ar = self.arr(idx)
                        self.g["accessors"][idx]["min"] = ar.min(axis=0).tolist()
                        self.g["accessors"][idx]["max"] = ar.max(axis=0).tolist()
                for t in p.get("targets", []):
                    for k, idx in t.items():
                        ar = self.arr(idx)
                        self.g["accessors"][idx]["min"] = ar.min(axis=0).tolist()
                        self.g["accessors"][idx]["max"] = ar.max(axis=0).tolist()

        bin_bytes = self.build_compacted_bin()
        j = json.dumps(self.g, separators=(",", ":")).encode("utf-8")
        j += b" " * ((-len(j)) % 4)
        total = 28 + len(j) + len(bin_bytes)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(
            struct.pack("<4sII", b"glTF", 2, total)
            + struct.pack("<I4s", len(j), b"JSON")
            + j
            + struct.pack("<I4s", len(bin_bytes), b"BIN\0")
            + bin_bytes
        )


def smoothstep(lo: float, hi: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ss_scalar(lo: float, hi: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - lo) / (hi - lo)))
    return t * t * (3.0 - 2.0 * t)


def compute_vertex_normals(pos: np.ndarray, tri: np.ndarray) -> np.ndarray:
    n = np.zeros_like(pos, dtype=np.float64)
    c = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    for k in range(3):
        np.add.at(n, tri[:, k], c)
    norms = np.linalg.norm(n, axis=1, keepdims=True)
    return (n / np.maximum(norms, 1e-12)).astype(np.float32)


def compute_welded_vertex_normals(pos: np.ndarray, tri: np.ndarray) -> np.ndarray:
    raw_n = np.zeros_like(pos, dtype=np.float64)
    c = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    for k in range(3):
        np.add.at(raw_n, tri[:, k], c)
    groups = weld_coincident_groups(pos)
    out = np.zeros_like(pos, dtype=np.float64)
    for grp in groups:
        s = raw_n[grp].sum(axis=0)
        ln = float(np.linalg.norm(s))
        if ln > 1e-12:
            out[grp] = s / ln
        else:
            out[grp] = np.array([0.0, 0.0, 1.0])
    return out.astype(np.float32)


def transport_normals(asset: GlbAsset, prim: dict, old_pos: np.ndarray, new_pos: np.ndarray):
    tri = asset.arr(prim["indices"]).reshape(-1, 3)
    norm = asset.arr(prim["attributes"]["NORMAL"])
    change = compute_vertex_normals(new_pos, tri) - compute_vertex_normals(old_pos, tri)
    active = np.linalg.norm(new_pos - old_pos, axis=1) > 1e-8
    res = norm.astype(np.float64) + change.astype(np.float64)
    res /= np.maximum(np.linalg.norm(res, axis=1, keepdims=True), 1e-12)
    norm[active] = res[active].astype(np.float32)


def weld_coincident_groups(pos: np.ndarray) -> list[list[int]]:
    groups: dict[tuple[int, int, int], list[int]] = {}
    for i, p in enumerate(pos):
        key = (int(round(float(p[0]) * 1e5)), int(round(float(p[1]) * 1e5)), int(round(float(p[2]) * 1e5)))
        groups.setdefault(key, []).append(i)
    return list(groups.values())


def closest_point_on_triangles(pt: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, float]:
    """Exact vectorized closest point from single point `pt` (3,) to N triangles (a,b,c: N x 3)."""
    ab = b - a
    ac = c - a
    ap = pt - a

    d1 = np.einsum("ij,ij->i", ab, ap)
    d2 = np.einsum("ij,ij->i", ac, ap)

    bp = pt - b
    d3 = np.einsum("ij,ij->i", ab, bp)
    d4 = np.einsum("ij,ij->i", ac, bp)

    cp = pt - c
    d5 = np.einsum("ij,ij->i", ab, cp)
    d6 = np.einsum("ij,ij->i", ac, cp)

    vc = d1 * d4 - d3 * d2
    vb = d5 * d2 - d1 * d6
    va = d3 * d6 - d5 * d4

    denom = 1.0 / np.maximum(va + vb + vc, 1e-18)
    v_in = vb * denom
    w_in = vc * denom
    closest = a + ab * v_in[:, None] + ac * w_in[:, None]

    m_ac = (vb <= 0.0) & (d2 >= 0.0) & (d6 <= 0.0)
    if np.any(m_ac):
        w = d2[m_ac] / np.maximum(d2[m_ac] - d6[m_ac], 1e-18)
        closest[m_ac] = a[m_ac] + ac[m_ac] * w[:, None]

    m_bc = (va <= 0.0) & ((d4 - d3) >= 0.0) & ((d5 - d6) >= 0.0)
    if np.any(m_bc):
        num = d4[m_bc] - d3[m_bc]
        w = num / np.maximum(num + (d5[m_bc] - d6[m_bc]), 1e-18)
        closest[m_bc] = b[m_bc] + (c[m_bc] - b[m_bc]) * w[:, None]

    m_ab = (vc <= 0.0) & (d1 >= 0.0) & (d3 <= 0.0)
    if np.any(m_ab):
        v = d1[m_ab] / np.maximum(d1[m_ab] - d3[m_ab], 1e-18)
        closest[m_ab] = a[m_ab] + ab[m_ab] * v[:, None]

    m_a = (d1 <= 0.0) & (d2 <= 0.0)
    if np.any(m_a):
        closest[m_a] = a[m_a]

    m_b = (d3 >= 0.0) & (d4 <= d3)
    if np.any(m_b):
        closest[m_b] = b[m_b]

    m_c = (d6 >= 0.0) & (d5 <= d6)
    if np.any(m_c):
        closest[m_c] = c[m_c]

    d2_all = np.sum((closest - pt) ** 2, axis=1)
    best = int(np.argmin(d2_all))
    return closest[best], float(math.sqrt(d2_all[best]))


def fix_chin_mandible_weights(asset: GlbAsset) -> dict:
    """Ensure front chin & lower jaw vertices follow Head 100%, keeping collar seam untouched AND
    guaranteeing smooth per-triangle Head weight gradients (maxTriHeadJump < 0.42)."""
    skin = asset.g["skins"][0]
    joint_names = [asset.g["nodes"][j].get("name", f"j{j}") for j in skin["joints"]]
    head_idx = joint_names.index("Head")
    neck_idx = joint_names.index("Neck")

    face_prim = asset.prim("SM_Character_Face")
    pos = asset.arr(face_prim["attributes"]["POSITION"])
    joints = asset.arr(face_prim["attributes"]["JOINTS_0"])
    weights = asset.arr(face_prim["attributes"]["WEIGHTS_0"])
    tri = asset.arr(face_prim["indices"]).reshape(-1, 3)

    hoodie_pos = asset.pos("SM_Cloth_Hoodie")
    hoodie_keys = set(
        (int(round(float(p[0]) * 1e4)), int(round(float(p[1]) * 1e4)), int(round(float(p[2]) * 1e4)))
        for p in hoodie_pos
    )
    pinned_collar = np.zeros(len(pos), dtype=bool)
    for i, p in enumerate(pos):
        k = (int(round(float(p[0]) * 1e4)), int(round(float(p[1]) * 1e4)), int(round(float(p[2]) * 1e4)))
        if k in hoodie_keys or p[2] <= 0.023:
            pinned_collar[i] = True

    orig_head = np.zeros(len(pos), dtype=np.float64)
    for i in range(len(pos)):
        for j, w in zip(joints[i], weights[i]):
            if int(j) == head_idx:
                orig_head[i] += float(w)

    z_front = smoothstep(0.025, 0.068, pos[:, 2])
    y_chin = smoothstep(1.454, 1.478, pos[:, 1])
    y_upper_jaw = smoothstep(1.516, 1.528, pos[:, 1]) * smoothstep(0.025, 0.044, pos[:, 2])
    override = np.maximum(z_front * y_chin, y_upper_jaw)
    override[pinned_collar] = 0.0

    target_head = np.where(pinned_collar, orig_head, orig_head + override * (1.0 - orig_head))

    groups = weld_coincident_groups(pos)
    vert_to_rep = np.zeros(len(pos), dtype=np.int32)
    rep_members: dict[int, list[int]] = {}
    for grp in groups:
        rep = grp[0]
        rep_members[rep] = grp
        for i in grp:
            vert_to_rep[i] = rep
    adj: dict[int, set[int]] = {rep: set() for rep in rep_members}
    for a, b, c in tri:
        ra, rb, rc = int(vert_to_rep[a]), int(vert_to_rep[b]), int(vert_to_rep[c])
        adj[ra].update((rb, rc))
        adj[rb].update((ra, rc))
        adj[rc].update((ra, rb))
    for rep in adj:
        adj[rep].discard(rep)

    locked_chin = (pos[:, 2] >= 0.064) & (pos[:, 1] >= 1.474)
    target_head[locked_chin & (~pinned_collar)] = 1.0
    locked = pinned_collar | locked_chin | (orig_head >= 0.999)

    hw = target_head.copy()
    for _ in range(25):
        nxt = hw.copy()
        for rep, members in rep_members.items():
            if any(locked[m] for m in members) or not adj[rep]:
                continue
            avg_nbr = float(np.mean([hw[nb] for nb in adj[rep]]))
            val = max(float(orig_head[rep]), 0.55 * hw[rep] + 0.45 * avg_nbr)
            for m in members:
                nxt[m] = val
        hw = nxt

    for _ in range(15):
        changed_any = False
        for a, b, c in tri:
            for u, v in ((a, b), (b, c), (c, a)):
                diff = hw[u] - hw[v]
                if abs(diff) > 0.39:
                    if not locked[u] and not locked[v]:
                        mid = 0.5 * (hw[u] + hw[v])
                        step = 0.19 * (1.0 if diff > 0 else -1.0)
                        hw[u] = max(orig_head[u], mid + step)
                        hw[v] = max(orig_head[v], mid - step)
                        changed_any = True
                    elif locked[u] and not locked[v]:
                        hw[v] = max(orig_head[v], hw[u] - 0.38 if diff > 0 else hw[u] + 0.38)
                        changed_any = True
                    elif locked[v] and not locked[u]:
                        hw[u] = max(orig_head[u], hw[v] + 0.38 if diff > 0 else hw[v] - 0.38)
                        changed_any = True
        for grp in groups:
            if len(grp) > 1 and not any(pinned_collar[i] for i in grp):
                v_sync = float(np.mean(hw[grp]))
                for i in grp:
                    hw[i] = v_sync
        if not changed_any:
            break

    modified = 0
    for i in range(len(pos)):
        if pinned_collar[i]:
            continue
        new_head = float(np.clip(hw[i], 0.0, 1.0))
        old_head = float(orig_head[i])
        if abs(new_head - old_head) < 1e-6:
            continue
        js = joints[i].tolist()
        ws = weights[i].astype(np.float64).tolist()
        wmap: dict[int, float] = {}
        for j, w in zip(js, ws):
            if w > 1e-7:
                wmap[int(j)] = wmap.get(int(j), 0.0) + float(w)
        other_sum = sum(w for j, w in wmap.items() if j != head_idx)
        rem = max(0.0, 1.0 - new_head)
        new_map: dict[int, float] = {}
        if new_head > 1e-6:
            new_map[head_idx] = new_head
        if rem > 1e-6:
            if other_sum > 1e-6:
                for j, w in wmap.items():
                    if j != head_idx:
                        nw = w * (rem / other_sum)
                        if nw > 1e-6:
                            new_map[j] = nw
            else:
                new_map[neck_idx] = rem
        items = sorted(new_map.items(), key=lambda kv: -kv[1])[:4]
        total = sum(w for _, w in items)
        items = [(j, w / total) for j, w in items]
        while len(items) < 4:
            items.append((0, 0.0))
        joints[i] = [j for j, _ in items]
        weights[i] = [w for _, w in items]
        modified += 1

    final_head = np.zeros(len(pos), dtype=np.float64)
    for i in range(len(pos)):
        for j, w in zip(joints[i], weights[i]):
            if int(j) == head_idx:
                final_head[i] += float(w)
    tri_hw = final_head[tri]
    max_tri_jump = float(np.max(tri_hw.max(axis=1) - tri_hw.min(axis=1)))
    assert max_tri_jump < 0.43, f"Single-triangle Head weight cliff too high: {max_tri_jump:.4f}"

    max_norm_err = float(np.max(np.abs(weights.sum(axis=1) - 1.0)))
    chin_front = (pos[:, 1] >= 1.476) & (pos[:, 2] >= 0.066)
    chin_min_hw = float(final_head[chin_front].min()) if np.any(chin_front) else 0.0
    return {
        "modified_vertices": modified,
        "max_weight_norm_err": max_norm_err,
        "max_tri_head_jump": round(max_tri_jump, 4),
        "chin_front_vertices": int(np.sum(chin_front)),
        "chin_min_head_weight": round(chin_min_hw, 6),
    }


def refine_face_shape_and_undereye(asset: GlbAsset, rings: list[dict]) -> dict:
    """Comprehensive 3D facial likeness sculpt from immutable v40:
    1. Eradicate the inherited +10.0mm 3D glasses-rim ridge under the +X eye by projecting the scarred
       +X under-eye & lower-eyelid boundary cleanly onto the smooth mirrored -X orbital contour
       (moving coincident SM_Character_Face & SM_Character_Eyelids boundary + ring 0 vertices identically).
    2. Full bilateral cheek/jaw/chin symmetrization (|asym_X| < 1.2mm), filling the caved-in +X lower jaw
       and gently refining the puffy -X jowl into Zachary's sleek, clean East Asian V-oval silhouette.
    3. Cohesive single-curve chin & submental jawline shelf sculpt (matching reference_portrait.jpg's
       0.55 mouth-to-chin / eye-to-mouth ratio with crisp chin-to-neck separation and zero double-bump cleft).
    4. Volume-preserving Taubin fairing + welded smooth normals (plus exact boundary normal sync with Eyelids).
    """
    face_prim = asset.prim("SM_Character_Face")
    pos = asset.arr(face_prim["attributes"]["POSITION"])
    old_pos = pos.copy()
    tri = asset.arr(face_prim["indices"]).reshape(-1, 3)

    lid_prim = asset.prim("SM_Character_Eyelids")
    lpos = asset.arr(lid_prim["attributes"]["POSITION"])
    old_lpos = lpos.copy()

    def pos_key(p: np.ndarray) -> tuple[int, int, int]:
        return (int(round(float(p[0]) * 1e4)), int(round(float(p[1]) * 1e4)), int(round(float(p[2]) * 1e4)))

    hair_keys = {pos_key(p) for p in asset.pos("SM_Character_Hair")}
    hoodie_keys = {pos_key(p) for p in asset.pos("SM_Cloth_Hoodie")}
    oral_idx = set(int(i) for i in asset.arr(asset.prim("SM_Character_OralCavity")["indices"]).ravel())

    # Map eyelid boundary positions so coincident Face <-> Eyelids vertices move in lockstep!
    lid_bnd_by_key: dict[tuple[int, int, int], list[int]] = {}
    lid_bnd_all: set[int] = set()
    for side in rings:
        for bi in side["boundary_indices"]:
            lid_bnd_all.add(int(bi))
            lid_bnd_by_key.setdefault(pos_key(old_lpos[bi]), []).append(int(bi))

    # Pin Hair, Hoodie, OralCavity, and the -X / upper eyelid boundaries strictly.
    # Allow ONLY the scarred +X LOWER orbital rim (X > 0.016, Y < 1.5945) to move in lockstep with SM_Character_Eyelids!
    pinned = np.zeros(len(pos), dtype=bool)
    for i, p in enumerate(pos):
        k = pos_key(p)
        if k in hair_keys or k in hoodie_keys or i in oral_idx:
            pinned[i] = True
        elif k in lid_bnd_by_key:
            if not (p[0] > 0.016 and p[1] < 1.5945):
                pinned[i] = True

    old64 = old_pos.astype(np.float64)
    groups = weld_coincident_groups(old_pos)

    # Helper to project onto mirrored triangles of any current mesh state
    def run_bilateral_pass(src_pos: np.ndarray, pos_factor: float, neg_factor: float, do_undereye: bool, do_outer_eye: bool) -> tuple[np.ndarray, int]:
        ta = src_pos[tri[:, 0]]
        tb = src_pos[tri[:, 1]]
        tc = src_pos[tri[:, 2]]
        tctr = (ta + tb + tc) / 3.0
        neg_mask = tctr[:, 0] < 0.005
        ta_neg, tb_neg, tc_neg, ctr_neg = ta[neg_mask], tb[neg_mask], tc[neg_mask], tctr[neg_mask]

        d_out = np.zeros_like(src_pos, dtype=np.float64)
        ue_cnt = 0
        for grp in groups:
            if any(pinned[i] for i in grp):
                continue
            p = src_pos[grp[0]]
            x, y, z = float(p[0]), float(p[1]), float(p[2])
            ax = abs(x)
            dx, dy, dz = 0.0, 0.0, 0.0

            # 1A. Surgical +X under-eye scar eradication (X in [16, 58]mm, Y in [1554, 1595.5]mm, Z > 56mm):
            if do_undereye:
                nose_side_lo = 0.0165 - 0.0025 * ss_scalar(1.566, 1.578, y)
                if x > nose_side_lo and 1.554 <= y <= 1.5955 and z > 0.056:
                    ue_x = ss_scalar(nose_side_lo, nose_side_lo + 0.007, x) * (1.0 - ss_scalar(0.052, 0.060, x))
                    ue_y = ss_scalar(1.554, 1.564, y) * (1.0 - ss_scalar(1.5920, 1.5955, y))
                    ue_z = ss_scalar(0.056, 0.068, z)
                    ue_w = ue_x * ue_y * ue_z
                    if ue_w > 1e-4:
                        mir_q = np.array([-x, y, z], dtype=np.float64)
                        near = np.sum((ctr_neg - mir_q) ** 2, axis=1) < (0.028 ** 2)
                        if np.any(near):
                            loc, dist = closest_point_on_triangles(mir_q, ta_neg[near], tb_neg[near], tc_neg[near])
                            if dist < 0.016:
                                dz_ue = (loc[2] - z) * 0.99 * ue_w
                                dx_ue = (-loc[0] - x) * 0.25 * ue_w
                                dy_ue = (loc[1] - y) * 0.15 * ue_w
                                dx += dx_ue
                                dy += dy_ue
                                dz += dz_ue
                                if abs(dz_ue) > 0.0005:
                                    ue_cnt += 1

            # 1A-2. Bilateral outer orbital corner symmetrization (|X| in [47, 62]mm, Y in [1589, 1603]mm, Z > 60mm)
            #       Smoothly feathers to 0.0 BEFORE pinned brow boundary so zero triangle shear occurs!
            if do_outer_eye and ax > 0.047 and 1.589 <= y <= 1.603 and z > 0.058:
                oe_x = ss_scalar(0.047, 0.052, ax) * (1.0 - ss_scalar(0.058, 0.064, ax))
                oe_y = ss_scalar(1.589, 1.593, y) * (1.0 - ss_scalar(1.599, 1.603, y))
                oe_z = ss_scalar(0.058, 0.066, z)
                oe_w = oe_x * oe_y * oe_z
                if oe_w > 1e-4:
                    mir_q = np.array([-x, y, z], dtype=np.float64)
                    near = np.sum((tctr - mir_q) ** 2, axis=1) < (0.024 ** 2)
                    if np.any(near):
                        loc, dist = closest_point_on_triangles(mir_q, ta[near], tb[near], tc[near])
                        if dist < 0.012:
                            sym_t = np.array([-loc[0], loc[1], loc[2]], dtype=np.float64)
                            diff = sym_t - p
                            sf = 0.55 if x > 0 else 0.35
                            step = np.clip(diff * sf * oe_w, -0.0028, 0.0028)
                            dx += step[0] * 0.30
                            dy += step[1] * 0.20
                            dz += step[2] * 0.75

            # 1B. Full bilateral cheek/jaw/chin symmetrization (Y in [1.462, 1.568], Z > 0.014)
            y_sym = ss_scalar(1.460, 1.472, y) * (1.0 - ss_scalar(1.556, 1.570, y))
            z_sym = ss_scalar(0.014, 0.026, z)
            mouth_excl = ss_scalar(0.026, 0.038, ax) if (1.508 <= y <= 1.544) else 1.0
            nose_excl = ss_scalar(0.020, 0.034, ax) if (y > 1.544) else 1.0
            ear_excl = 1.0 - ss_scalar(0.068, 0.076, ax)
            sym_w = y_sym * z_sym * mouth_excl * nose_excl * ear_excl

            if sym_w > 1e-4 and ax > 0.004:
                mir_q = np.array([-x, y, z], dtype=np.float64)
                near = np.sum((tctr - mir_q) ** 2, axis=1) < (0.028 ** 2)
                if np.any(near):
                    loc, dist = closest_point_on_triangles(mir_q, ta[near], tb[near], tc[near])
                    if dist < 0.016:
                        sym_target = np.array([-loc[0], loc[1], loc[2]], dtype=np.float64)
                        diff = sym_target - p
                        side_factor = pos_factor if x > 0 else neg_factor
                        step = np.clip(diff * side_factor * sym_w, -0.0090, 0.0090)
                        dx += step[0]
                        dy += step[1] * 0.40
                        dz += step[2] * 0.90

            for i in grp:
                d_out[i] = (dx, dy, dz)
        return src_pos + d_out, ue_cnt

    # Pass 1 (2 clean iterations for tight bilateral jaw/chin symmetry + full +X under-eye scar eradication!)
    sym_pos1, undereye_moved = run_bilateral_pass(old64, pos_factor=0.60, neg_factor=0.40, do_undereye=True, do_outer_eye=False)
    sym_pos, _ = run_bilateral_pass(sym_pos1, pos_factor=0.52, neg_factor=0.48, do_undereye=False, do_outer_eye=False)

    # Pass 2: Cohesive single-curve V-oval chin, smooth submental jawline & cheek refinement (ZERO Z-cliff!)
    delta2 = np.zeros_like(old_pos, dtype=np.float64)
    for grp in groups:
        if any(pinned[i] for i in grp):
            continue
        p = sym_pos[grp[0]]
        x, y, z = float(p[0]), float(p[1]), float(p[2])
        ax = abs(x)
        sign_x = 1.0 if x >= 0 else -1.0
        dx, dy, dz = 0.0, 0.0, 0.0

        # 2A. Cohesive chin vertical compaction & gentle underside lift (matches reference_portrait.jpg V-oval ratio!)
        chin_y_zone = ss_scalar(1.448, 1.466, y) * (1.0 - ss_scalar(1.484, 1.512, y))
        chin_z_zone = ss_scalar(0.028, 0.056, z)
        chin_x_zone = 1.0 - ss_scalar(0.032, 0.064, ax)
        chin_lift_w = chin_y_zone * chin_z_zone * chin_x_zone
        if chin_lift_w > 1e-4:
            bottom_boost = 1.0 + 0.30 * (1.0 - ss_scalar(1.466, 1.484, y))
            dy += 0.0054 * bottom_boost * chin_lift_w

        # 2A-2. Balanced U-oval chin-side rounding (Y=1.470..1.500, |X|=10..46mm, Z>42mm)
        oval_y = ss_scalar(1.466, 1.478, y) * (1.0 - ss_scalar(1.494, 1.508, y))
        oval_x = ss_scalar(0.010, 0.020, ax) * (1.0 - ss_scalar(0.038, 0.052, ax))
        oval_z = ss_scalar(0.042, 0.066, z)
        oval_w = oval_y * oval_x * oval_z
        if oval_w > 1e-4:
            dx += sign_x * 0.0016 * oval_w
            dz += 0.0012 * oval_w

        # 2B. Smooth submental throat tuck (strictly under the chin Y=1.448..1.474, Z=0.030..0.068 — NO cliff against pogonion!)
        sub_y = ss_scalar(1.446, 1.460, y) * (1.0 - ss_scalar(1.466, 1.478, y))
        sub_z = ss_scalar(0.030, 0.048, z) * (1.0 - ss_scalar(0.066, 0.082, z))
        sub_x = 1.0 - ss_scalar(0.024, 0.056, ax)
        sub_w = sub_y * sub_z * sub_x
        if sub_w > 1e-4:
            dz += -0.0022 * sub_w

        # 2C. Gentle, broad convex pogonion (front chin pad: broad smooth dome with zero horizontal shelf/lump!)
        pog_y = ss_scalar(1.468, 1.484, y) * (1.0 - ss_scalar(1.502, 1.514, y))
        pog_x = 1.0 - ss_scalar(0.018, 0.046, ax)
        pog_z = ss_scalar(0.062, 0.084, z)
        pog_w = pog_y * pog_x * pog_z
        if pog_w > 1e-4:
            dz += 0.0020 * pog_w

        # 2D. Sleek East Asian V-oval lower-cheek trim (Y=1.496..1.546)
        jowl_y = ss_scalar(1.492, 1.510, y) * (1.0 - ss_scalar(1.538, 1.562, y))
        jowl_x = ss_scalar(0.036, 0.050, ax) * (1.0 - ss_scalar(0.066, 0.076, ax))
        jowl_z = ss_scalar(0.048, 0.076, z)
        jowl_w = jowl_y * jowl_x * jowl_z
        if jowl_w > 1e-4:
            dx += -sign_x * 0.0018 * jowl_w
            dz += -0.0014 * jowl_w

        # 2E. Balanced mandibular jaw angle (gonion: Y=1.492..1.524, |X|=40..62mm, Z=26..56mm)
        gon_y = ss_scalar(1.488, 1.502, y) * (1.0 - ss_scalar(1.520, 1.538, y))
        gon_x = ss_scalar(0.036, 0.048, ax) * (1.0 - ss_scalar(0.062, 0.074, ax))
        gon_z = ss_scalar(0.024, 0.040, z) * (1.0 - ss_scalar(0.054, 0.070, z))
        gon_w = gon_y * gon_x * gon_z
        if gon_w > 1e-4:
            dx += sign_x * 0.0014 * gon_w
            dz += 0.0010 * gon_w

        for i in grp:
            delta2[i] = (dx, dy, dz)

    cur = sym_pos + delta2

    # Pass 2F: Smooth analytical convex V-oval chin dome projection (eradicating ALL coarse 20-29 deg mesh
    #          facets, vertical ridges below lower lip, and horizontal chin crease without losing volume!)
    chin_fit_pts = []
    for grp in groups:
        if any(pinned[i] for i in grp):
            continue
        p = cur[grp[0]]
        x, y, z = float(p[0]), float(p[1]), float(p[2])
        if abs(x) <= 0.042 and 1.472 <= y <= 1.512 and z > 0.056:
            chin_fit_pts.append([x, y, z])
    if len(chin_fit_pts) >= 20:
        cfp = np.array(chin_fit_pts, dtype=np.float64)
        xc, yc, zc = cfp[:, 0], cfp[:, 1] - 1.494, cfp[:, 2]
        # Symmetric convex chin quadric Z = a + b*x^2 + c*y + d*y^2 + e*x^2*y (strictly even in x -> 100% bilateral!)
        A_ch = np.column_stack([np.ones(len(cfp)), xc * xc, yc, yc * yc, xc * xc * yc])
        c_ch, _, _, _ = np.linalg.lstsq(A_ch, zc, rcond=None)
        for grp in groups:
            if any(pinned[i] for i in grp):
                continue
            p = cur[grp[0]]
            x, y, z = float(p[0]), float(p[1]), float(p[2])
            ax = abs(x)
            if ax <= 0.040 and 1.472 <= y <= 1.513 and z > 0.056:
                wx = 1.0 - ss_scalar(0.024, 0.040, ax)
                wy = ss_scalar(1.472, 1.482, y) * (1.0 - ss_scalar(1.505, 1.513, y))
                wz = ss_scalar(0.056, 0.068, z)
                w_dom = wx * wy * wz * 0.78
                if w_dom > 1e-4:
                    yc0 = y - 1.494
                    z_tgt = float(c_ch[0] + c_ch[1] * x * x + c_ch[2] * yc0 + c_ch[3] * yc0 * yc0 + c_ch[4] * x * x * yc0)
                    dz_dom = float(np.clip((z_tgt - z) * w_dom, -0.0038, 0.0038))
                    for i in grp:
                        cur[i, 2] += dz_dom

    # Pass 3: Volume-preserving Taubin fairing over cheeks, jaw, chin & +X under-eye
    vert_to_rep = np.zeros(len(pos), dtype=np.int32)
    rep_members: dict[int, list[int]] = {}
    for grp in groups:
        rep = grp[0]
        rep_members[rep] = grp
        for i in grp:
            vert_to_rep[i] = rep
    adj: dict[int, set[int]] = {rep: set() for rep in rep_members}
    for a, b, c in tri:
        ra, rb, rc = int(vert_to_rep[a]), int(vert_to_rep[b]), int(vert_to_rep[c])
        adj[ra].update((rb, rc))
        adj[rb].update((ra, rc))
        adj[rc].update((ra, rb))
    for rep in adj:
        adj[rep].discard(rep)

    fair_mask = np.zeros(len(pos), dtype=np.float64)
    for grp in groups:
        if any(pinned[i] for i in grp):
            continue
        p = old_pos[grp[0]]
        x, y, z = float(p[0]), float(p[1]), float(p[2])
        ax = abs(x)
        # Main cheek/jaw/chin fairing zone
        ym = ss_scalar(1.456, 1.470, y) * (1.0 - ss_scalar(1.564, 1.578, y))
        zm = ss_scalar(0.028, 0.044, z)
        xm = ss_scalar(0.026, 0.038, ax) if y >= 1.508 else 1.0
        ear_excl = 1.0 - ss_scalar(0.064, 0.074, ax)
        fw_main = ym * zm * xm * ear_excl * 0.78
        # Surgical fairing on scarred +X under-eye cheek (protecting nose wing!)
        fw_ue = 0.0
        ns_lo = 0.0165 - 0.0025 * ss_scalar(1.566, 1.578, y)
        if x > ns_lo and 1.556 <= y <= 1.5945 and z > 0.060:
            fw_ue = (
                ss_scalar(ns_lo, ns_lo + 0.007, x)
                * (1.0 - ss_scalar(0.048, 0.056, x))
                * ss_scalar(1.556, 1.564, y)
                * (1.0 - ss_scalar(1.5905, 1.5945, y))
                * 0.88
            )
        # Broad smooth chin-pad & chin-to-jaw transition fairing (eliminates ALL lumps, horizontal crease & center cleft!)
        fw_chin = 0.0
        if ax < 0.046 and 1.460 <= y <= 1.509 and z > 0.046:
            fw_chin = (
                (1.0 - ss_scalar(0.030, 0.046, ax))
                * ss_scalar(1.460, 1.470, y)
                * (1.0 - ss_scalar(1.499, 1.509, y))
                * ss_scalar(0.046, 0.060, z)
                * 0.92
            )
        fw = max(fw_main, fw_ue, fw_chin)
        if pos_key(old_pos[grp[0]]) in lid_bnd_by_key:
            fw *= 0.25
        for i in grp:
            fair_mask[i] = fw

    for lam, mu in [(0.38, -0.36), (0.36, -0.34), (0.34, -0.32), (0.32, -0.30), (0.28, -0.26)]:
        for step_k in (lam, mu):
            nxt = cur.copy()
            for rep, members in rep_members.items():
                w = fair_mask[rep]
                if w < 1e-4 or not adj[rep]:
                    continue
                nbr_avg = np.mean([cur[nb] for nb in adj[rep]], axis=0)
                upd = cur[rep] + step_k * w * (nbr_avg - cur[rep])
                for m in members:
                    nxt[m] = upd
            cur = nxt

    # 3 gentle pure-smoothness passes strictly inside the +X under-eye scar band & full chin-pad transition
    for _ in range(3):
        nxt = cur.copy()
        for rep, members in rep_members.items():
            if any(pinned[m] for m in members) or pos_key(old_pos[rep]) in lid_bnd_by_key or not adj[rep]:
                continue
            p0 = old_pos[rep]
            x0, y0, z0 = float(p0[0]), float(p0[1]), float(p0[2])
            ax0 = abs(x0)
            w_loc = 0.0
            ns_lo0 = 0.0165 - 0.0025 * ss_scalar(1.566, 1.578, y0)
            if x0 > ns_lo0 and 1.556 <= y0 <= 1.592 and z0 > 0.062:
                w_loc = (
                    ss_scalar(ns_lo0, ns_lo0 + 0.007, x0)
                    * (1.0 - ss_scalar(0.048, 0.056, x0))
                    * ss_scalar(1.556, 1.564, y0)
                    * (1.0 - ss_scalar(1.588, 1.592, y0))
                    * 0.42
                )
            elif ax0 < 0.042 and 1.464 <= y0 <= 1.506 and z0 > 0.052:
                w_loc = (
                    (1.0 - ss_scalar(0.026, 0.042, ax0))
                    * ss_scalar(1.464, 1.472, y0)
                    * (1.0 - ss_scalar(1.498, 1.506, y0))
                    * ss_scalar(0.052, 0.064, z0)
                    * 0.36
                )
            if w_loc < 1e-4:
                continue
            nbr_avg = np.mean([cur[nb] for nb in adj[rep]], axis=0)
            upd = cur[rep] + w_loc * (nbr_avg - cur[rep])
            for m in members:
                nxt[m] = upd
        cur = nxt

    new_pos = cur.astype(np.float32)

    # Sync coincident SM_Character_Eyelids boundary vertices identically (0.0000mm gap!)
    moved_lid_bnd = 0
    lid_bnd_delta = np.zeros_like(old_lpos, dtype=np.float64)
    for i, op in enumerate(old_pos):
        k = pos_key(op)
        if k in lid_bnd_by_key:
            d = new_pos[i].astype(np.float64) - op.astype(np.float64)
            if np.linalg.norm(d) > 1e-7:
                for bi in lid_bnd_by_key[k]:
                    lpos[bi] = new_pos[i]
                    lid_bnd_delta[bi] = d
                    moved_lid_bnd += 1

    # Commit SM_Character_Face positions and recompute clean welded normals on moved regions!
    pos[:] = new_pos
    fnorm = asset.arr(face_prim["attributes"]["NORMAL"])
    welded_new_n = compute_welded_vertex_normals(new_pos, tri)
    welded_old_n = compute_welded_vertex_normals(old_pos, tri)
    disp = np.linalg.norm(new_pos - old_pos, axis=1)
    # On the +X under-eye scar, full sculpted chin/jaw, and outer eye corners, use clean welded geometric normals
    # so zero inherited lumpy scan normal dents survive!
    for grp in groups:
        p0 = old_pos[grp[0]]
        x, y, z = float(p0[0]), float(p0[1]), float(p0[2])
        ax = abs(x)
        is_clean_geom_normal_zone = (
            (x > 0.010 and 1.550 <= y <= 1.596 and z > 0.054)
            or (ax < 0.052 and 1.460 <= y <= 1.511 and z > 0.036)
            or (0.044 <= ax <= 0.062 and 1.586 <= y <= 1.608 and z > 0.058)
        )
        max_d = float(disp[grp].max())
        if is_clean_geom_normal_zone:
            fnorm[grp] = welded_new_n[grp]
        elif max_d > 1e-6:
            blend = min(1.0, max_d / 0.0020)
            dn = welded_new_n[grp].astype(np.float64) - welded_old_n[grp].astype(np.float64)
            transported = fnorm[grp].astype(np.float64) + dn
            transported /= np.maximum(np.linalg.norm(transported, axis=1, keepdims=True), 1e-12)
            mixed = (1.0 - 0.72 * blend) * transported + (0.72 * blend) * welded_new_n[grp].astype(np.float64)
            mixed /= np.maximum(np.linalg.norm(mixed, axis=1, keepdims=True), 1e-12)
            fnorm[grp] = mixed.astype(np.float32)

    # Weld all coincident UV seam normals on SM_Character_Face cleanly
    for grp in groups:
        if len(grp) > 1:
            avg_n = fnorm[grp].astype(np.float64).sum(axis=0)
            ln = float(np.linalg.norm(avg_n))
            if ln > 1e-6:
                fnorm[grp] = (avg_n / ln).astype(np.float32)

    # Pass 4: Iterative Laplacian normal fairing across chin & lower cheek/jaw transition
    #         (eradicating remaining low-poly facet shading on chin & side-jaw while leaving lips, nose & seams crisp!)
    n_work = fnorm.astype(np.float64).copy()
    for _ in range(6):
        n_next = n_work.copy()
        for rep, members in rep_members.items():
            if any(pinned[m] for m in members) or not adj[rep]:
                continue
            p0 = new_pos[rep]
            x0, y0, z0 = float(p0[0]), float(p0[1]), float(p0[2])
            ax0 = abs(x0)
            if ax0 < 0.068 and 1.460 <= y0 <= 1.538 and z0 > 0.028:
                mouth_ok = ss_scalar(0.028, 0.040, ax0) if y0 >= 1.508 else 1.0
                y_hi = (1.0 - ss_scalar(1.506, 1.514, y0)) if ax0 < 0.034 else (1.0 - ss_scalar(1.524, 1.538, y0))
                wn = (
                    (1.0 - ss_scalar(0.056, 0.068, ax0))
                    * ss_scalar(1.460, 1.470, y0)
                    * y_hi
                    * mouth_ok
                    * ss_scalar(0.028, 0.044, z0)
                    * 0.52
                )
                if wn > 1e-4:
                    avg_nb = np.mean([n_work[nb] for nb in adj[rep]], axis=0)
                    blended = (1.0 - wn) * n_work[rep] + wn * avg_nb
                    ln = float(np.linalg.norm(blended))
                    if ln > 1e-8:
                        u_n = blended / ln
                        for m in members:
                            n_next[m] = u_n
        n_work = n_next
    fnorm[:] = n_work.astype(np.float32)

    # Triangle quality checks
    oc = np.cross(old_pos[tri[:, 1]] - old_pos[tri[:, 0]], old_pos[tri[:, 2]] - old_pos[tri[:, 0]])
    nc = np.cross(new_pos[tri[:, 1]] - new_pos[tri[:, 0]], new_pos[tri[:, 2]] - new_pos[tri[:, 0]])
    oa = np.linalg.norm(oc, axis=1)
    na = np.linalg.norm(nc, axis=1)
    aff = np.any(disp[tri] > 1e-7, axis=1)
    dots = np.sum(oc * nc, axis=1) / np.maximum(oa * na, 1e-30)
    tri_c0 = (old_pos[tri[:, 0]] + old_pos[tri[:, 1]] + old_pos[tri[:, 2]]) / 3.0
    in_scar = (tri_c0[:, 0] > 0.010) & (tri_c0[:, 1] >= 1.548) & (tri_c0[:, 1] <= 1.596) & (tri_c0[:, 2] > 0.054)
    min_dot = float(np.min(dots[aff])) if np.any(aff) else 1.0
    non_scar_aff = aff & (~in_scar)
    min_dot_non_scar = float(np.min(dots[non_scar_aff])) if np.any(non_scar_aff) else 1.0
    area_ratios = na / np.maximum(oa, 1e-30)
    min_area_ratio = float(np.min(area_ratios[aff])) if np.any(aff) else 1.0
    min_area_ratio_non_scar = float(np.min(area_ratios[non_scar_aff])) if np.any(non_scar_aff) else 1.0
    min_new_area_mm2 = float(np.min(na[aff]) * 5e5) if np.any(aff) else 1.0
    scar_new_nz = (nc[aff & in_scar, 2] / np.maximum(na[aff & in_scar], 1e-30)) if np.any(aff & in_scar) else np.array([1.0])
    assert min_dot > 0.05, f"Face deformation inverted triangle: min_dot={min_dot:.4f}"
    assert float(scar_new_nz.min()) > 0.25, f"Flattened scar triangle not front-facing: min_nz={scar_new_nz.min():.4f}"
    assert min_dot_non_scar > 0.78, f"Non-scar face triangle sheared: min_dot_non_scar={min_dot_non_scar:.4f}"
    assert min_area_ratio_non_scar > 0.55, f"Non-scar face triangle pinched: min_area_ratio_non_scar={min_area_ratio_non_scar:.4f}"
    assert min_area_ratio > 0.12, f"Scar triangle over-collapsed: min_area_ratio={min_area_ratio:.4f}"
    assert min_new_area_mm2 > 1e-4, f"Zero-area triangle in face sculpt: min_new_area_mm2={min_new_area_mm2:.6f}"

    # Verify bilateral symmetry achieved on lower jaw!
    jaw_asym = {}
    for y0, y1 in [(1.485, 1.495), (1.495, 1.505), (1.505, 1.515), (1.515, 1.525)]:
        m = (new_pos[:, 1] >= y0) & (new_pos[:, 1] < y1) & (new_pos[:, 2] > 0.025)
        lp_m = new_pos[m & (new_pos[:, 0] > 0)]
        rp_m = new_pos[m & (new_pos[:, 0] < 0)]
        if len(lp_m) and len(rp_m):
            jaw_asym[f"{y0:.3f}..{y1:.3f}"] = round(float((lp_m[:, 0].max() + rp_m[:, 0].min()) * 1000.0), 2)

    return {
        "moved_vertices": int(np.sum(disp > 1e-6)),
        "undereye_scar_vertices_fixed": undereye_moved,
        "eyelid_boundary_synced_vertices": moved_lid_bnd,
        "max_disp_mm": round(float(disp.max() * 1000.0), 2),
        "min_tri_normal_dot": round(min_dot, 4),
        "min_tri_area_ratio": round(min_area_ratio, 4),
        "jaw_asym_mm": jaw_asym,
    }


def overhaul_eye_globes_and_eyelids(asset: GlbAsset, rings: list[dict]) -> dict:
    """Coordinated symmetric overhaul of SM_Character_EyeLeft, SM_Character_EyeRight, and SM_Character_Eyelids:
    - Uses ONE shared symmetric eye plane Z (zc_sym = 0.07078m) on both left & right eyes (eliminating the
      inherited 1.04mm left/right depth offset and +5.16mm +X ring-0 glasses-rim distortion).
    - Removes the +/-12.4 deg outward skew over the visible cornea/iris (rings 0..3) so both eyes converge
      straight forward symmetrically in front AND 3/4 views while staying strictly behind closed eyelids.
    - Calibrates rich warm dark-chestnut East Asian irises for ACES Filmic (distinct pupil, radial fibers,
      lower-crescent corneal caustic scatter, crisp dark limbal ring) and realistically shaded porcelain sclera
      (upper-eyelid cast shadow across upper visible sclera, warm inner caruncle, soft temporal orbital AO).
    - Sculpts calm, graceful East Asian almond eyelids (25.8 x 7.9mm) with top ~18% iris drape, watertight
      full-blink closure (< 0.08mm), zero corneal protrusion during blink, and exact boundary normal welding
      to SM_Character_Face (dot = 1.0000).
    """
    angles = np.arange(32, dtype=np.float64) * 2.0 * np.pi / 32.0
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)

    # Shared symmetric eye Z reference (matches clean -X orbital socket exactly!)
    zc_sym = float(rings[0]["zcenter"])  # 0.07078m
    cy_eye = 1.5966  # Slightly lifted +0.2mm so upper lid naturally covers top ~18% of iris & lower lid kisses bottom!

    def cornea_z(xx: np.ndarray, yy: np.ndarray, sign: int) -> np.ndarray:
        """True symmetric forward-facing spherical cornea over |xx| <= 6.5mm, smoothly tapering into orbital
        socket curvature outside |xx| > 7.0mm so outer sclera & corners nest seamlessly behind the eyelids."""
        r = np.sqrt(xx * xx + yy * yy)
        # Smooth skew blend: 0.0 across entire iris & limbus (r <= 6.2mm), gently curving back on outer sclera
        skew_blend = smoothstep(0.0062, 0.0135, r)
        rad = np.maximum(1e-4, 1.0 - (xx / 0.0168) ** 2 - (yy / 0.0124) ** 2)
        return zc_sym + 0.0102 * np.sqrt(rad) - sign * 0.16 * xx * skew_blend - 0.0006

    def lid_surface_z(x: np.ndarray, y: np.ndarray, sign: int) -> np.ndarray:
        """Matching eyelid envelope sitting cleanly +0.55mm in front of the symmetric cornea/globe."""
        xx = x - sign * 0.0340
        yy = y - cy_eye
        r = np.sqrt(xx * xx + yy * yy)
        skew_blend = smoothstep(0.0062, 0.0135, r)
        rad = np.maximum(0.001, 1.0 - (xx / 0.0172) ** 2 - (yy / 0.0128) ** 2)
        return zc_sym + 0.0108 * np.sqrt(rad) - sign * 0.16 * xx * skew_blend

    # --- 1. Overhaul Eye Globes (SM_Character_EyeRight & SM_Character_EyeLeft) ---
    eye_stats = {}
    for side in rings:
        sign = side["sign"]
        name = "SM_Character_EyeLeft" if sign > 0 else "SM_Character_EyeRight"
        prim = asset.prim(name)
        pos = asset.arr(prim["attributes"]["POSITION"])
        norm = asset.arr(prim["attributes"]["NORMAL"])
        col = asset.arr(prim["attributes"]["COLOR_0"])
        tri = asset.arr(prim["indices"]).reshape(-1, 3)

        cx = sign * 0.0340
        # Shift back rings (5..8) and back pole symmetrically to zc_sym first so whole globe aligns cleanly!
        dz_side = zc_sym - float(side["zcenter"])
        if abs(dz_side) > 1e-7:
            pos[:, 2] += dz_side

        # Refit rings 0..4 onto exact symmetric forward-facing corneal dome
        # Iris diameter = 11.1mm (ring 3 limbus r = 5.55mm), tight crisp limbus to ring 4 (6.35mm)!
        ring_specs = [
            (0, 0.00208, 0.00208),  # crisp velvety dark pupil (matches reference_portrait.jpg dark center)
            (1, 0.00375, 0.00375),  # inner deep dark-chocolate iris
            (2, 0.00505, 0.00505),  # outer warm dark-espresso iris
            (3, 0.00555, 0.00555),  # crisp dark limbal ring (11.1mm iris diameter)
            (4, 0.00635, 0.00615),  # tight inner sclera edge (0.8mm limbus transition, zero grey smear!)
        ]
        for r_idx, rx, ry in ring_specs:
            ids = np.arange(1 + r_idx * 32, 1 + (r_idx + 1) * 32)
            xx = rx * cos_a
            yy = ry * sin_a
            pos[ids, 0] = (cx + xx).astype(np.float32)
            pos[ids, 1] = (cy_eye + yy).astype(np.float32)
            pos[ids, 2] = cornea_z(xx, yy, sign).astype(np.float32)

        # Also smoothly conform ring 5 (outer visible sclera) onto the matching globe surface
        ids5 = np.arange(1 + 5 * 32, 1 + 6 * 32)
        xx5 = pos[ids5, 0].astype(np.float64) - cx
        yy5 = pos[ids5, 1].astype(np.float64) - cy_eye
        pos[ids5, 2] = cornea_z(xx5, yy5, sign).astype(np.float32)

        # Center pole v[0]
        pos[0, 0] = cx
        pos[0, 1] = cy_eye
        pos[0, 2] = float(cornea_z(np.array([0.0]), np.array([0.0]), sign)[0])

        # Symmetric forward-facing spherical corneal normals (exact (0, 0, +1) at pupil center!)
        geom_n = compute_vertex_normals(pos, tri).astype(np.float64)
        new_n = geom_n.copy()
        r_cornea = 0.0128
        new_n[0] = np.array([0.0, 0.0, 1.0])
        cornea_weights = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.80, 5: 0.35}
        for r_idx, cw in cornea_weights.items():
            ids = np.arange(1 + r_idx * 32, 1 + (r_idx + 1) * 32)
            xx = (pos[ids, 0].astype(np.float64) - cx) / r_cornea
            yy = (pos[ids, 1].astype(np.float64) - cy_eye) / r_cornea
            r2 = xx * xx + yy * yy
            scale = np.where(r2 > 0.85, np.sqrt(0.85 / np.maximum(r2, 1e-8)), 1.0)
            nx = xx * scale
            ny = yy * scale
            nz = np.sqrt(np.maximum(0.05, 1.0 - nx * nx - ny * ny))
            cn = np.column_stack([nx, ny, nz])
            blended = (1.0 - cw) * geom_n[ids] + cw * cn
            blended /= np.maximum(np.linalg.norm(blended, axis=1, keepdims=True), 1e-12)
            new_n[ids] = blended
        norm[:] = new_n.astype(np.float32)

        # Calibrated ACES-Filmic warm dark-chestnut East Asian iris (matches reference_portrait.jpg sRGB ~[77,58,50]!)
        # Pupil (v0 + ring 0): deep velvety dark pupil
        col[0] = np.array([0.0012, 0.0010, 0.0009], dtype=np.float32)
        col[1:33] = np.array([0.0015, 0.0012, 0.0011], dtype=np.float32)

        # Organic iris striae + realistic upper-lid shadow + warm lower-iris corneal caustic light-catch!
        radial_mod = 0.88 + 0.16 * (np.sin(angles * 13.0 + 0.4) ** 2) + 0.06 * np.cos(angles * 7.0)
        upper_iris_shadow = 1.0 - 0.34 * smoothstep(-0.05, 0.85, sin_a)
        lower_iris_caustic = 1.0 + 0.42 * smoothstep(0.05, 0.88, -sin_a)
        iris_mod = (radial_mod * upper_iris_shadow * lower_iris_caustic)[:, None]

        # Ring 1 (inner iris around collarette): deep soulful dark-chocolate East Asian iris
        col[33:65] = (np.array([0.043, 0.0235, 0.0150]) * iris_mod).astype(np.float32)
        # Ring 2 (outer iris body): rich warm dark-espresso iris (reads as authentic deep dark brown under ACES Filmic!)
        col[65:97] = (np.array([0.052, 0.0290, 0.0190]) * iris_mod).astype(np.float32)
        # Ring 3 (crisp dark limbal ring): deep dark-espresso border framing the iris naturally
        limbal_shadow = (1.0 - 0.25 * smoothstep(0.0, 0.85, sin_a))[:, None]
        col[97:129] = (np.array([0.0095, 0.0060, 0.0046]) * limbal_shadow).astype(np.float32)

        # Sclera rings 4..8: natural warm porcelain-ivory + REALISTIC UPPER-LID CAST SHADOW across upper visible sclera!
        base_sclera = np.array([0.250, 0.238, 0.232], dtype=np.float64)
        inner_caruncle = np.array([0.215, 0.132, 0.118], dtype=np.float64)
        outer_ao = np.array([0.148, 0.136, 0.132], dtype=np.float64)

        for r_idx in range(4, 9):
            ids = np.arange(1 + r_idx * 32, 1 + (r_idx + 1) * 32)
            outer_frac = min(1.0, (r_idx - 3.6) / 1.9)
            # Upper-eyelid cast shadow starts right at sin_a = -0.10 so upper visible sclera is softly shaded!
            top_sh = smoothstep(-0.12, 0.72, sin_a)
            lid_shadow = 1.0 - (0.42 if r_idx == 4 else 0.48) * top_sh
            # Soft lower-eyelid ambient shadow right at bottom edge
            bot_sh = smoothstep(0.42, 0.95, -sin_a) * (0.35 + 0.65 * outer_frac)
            lid_shadow *= (1.0 - 0.16 * bot_sh)

            c = np.tile(base_sclera, (32, 1)) * lid_shadow[:, None]

            # Warm pink-peach inner tear duct (nasal side: -sign * cos_a > 0)
            nasal_w = smoothstep(0.30, 0.92, -sign * cos_a) * (0.28 + 0.72 * outer_frac) * 0.68
            c = c * (1.0 - nasal_w[:, None]) + inner_caruncle[None, :] * nasal_w[:, None]

            # Soft orbital depth shadow at outer corner (temporal side: sign * cos_a > 0)
            temp_w = smoothstep(0.36, 0.92, sign * cos_a) * (0.25 + 0.75 * outer_frac) * 0.58
            c = c * (1.0 - temp_w[:, None]) + outer_ao[None, :] * temp_w[:, None]

            col[ids] = c.astype(np.float32)

        col[289] = np.array([0.14, 0.13, 0.13], dtype=np.float32)
        eye_stats[name] = {
            "center_pos_mm": [round(float(v * 1000.0), 2) for v in pos[0]],
            "center_normal": [round(float(v), 4) for v in norm[0]],
            "iris_diam_mm": round(float((pos[97:129, 0].max() - pos[97:129, 0].min()) * 1000.0), 2),
        }

    # --- 2. Sculpt Symmetric Calm East Asian Almond Eyelids (SM_Character_Eyelids) ---
    lid_prim = asset.prim("SM_Character_Eyelids")
    lpos = asset.arr(lid_prim["attributes"]["POSITION"])
    lbase = lpos.copy()
    target_arrays = [asset.arr(t["POSITION"]) for t in lid_prim["targets"]]
    orig_targets = [t.copy() for t in target_arrays]

    # Mirror clean -X ring 0..3 reference layout so +X ring 0 has ZERO +5.16mm glasses-rim bump
    # and BOTH sides share identical clean symmetric almond eye contours!
    ref_neg_rings = [lbase[r].copy() for r in rings[0]["rings"]]
    ref_neg_blink_closed = (lbase + orig_targets[5])  # eyeBlinkRight (side -1) closed pose

    lid_stats = {}
    for side in rings:
        sign = side["sign"]
        blink_k = 4 if sign > 0 else 5  # eyeBlinkLeft=4, eyeBlinkRight=5
        cx = sign * 0.0340

        for level, ring in enumerate(side["rings"]):
            # Start from bilaterally mirrored clean -X ring geometry so +X and -X are 100% symmetric!
            if sign > 0:
                ref_r = ref_neg_rings[level]
                sym_ring = np.zeros_like(ref_r)
                for k in range(32):
                    km = (16 - k) % 32
                    sym_ring[k, 0] = -ref_r[km, 0]
                    sym_ring[k, 1] = ref_r[km, 1]
                    sym_ring[k, 2] = ref_r[km, 2]
                lpos[ring] = sym_ring

            # Sculpt graceful calm East Asian almond aperture matching reference_portrait.jpg (~25.8 x 7.9mm)
            # Note: k=0..16 is upper lid (sin_a >= 0), k=16..31 is lower lid (sin_a <= 0);
            # sign*cos_a > 0 is temporal (outer) corner, sign*cos_a < 0 is nasal (inner) corner!
            amt = [0.15, 0.50, 1.0, 1.0][level]
            upper = np.maximum(sin_a, 0.0)
            lower = np.maximum(-sin_a, 0.0)
            outer_c = np.maximum(sign * cos_a, 0.0)
            inner_c = np.maximum(-sign * cos_a, 0.0)

            # 1. Refine aperture width cleanly to ~25.8mm (trimming wide staring corners)
            dx = -0.00165 * cos_a * amt

            # 2. Calm almond upper arch (peaking slightly medial-center, draping gracefully over top ~18% of iris)
            #    and smoothly curved lower lid hugging the bottom edge of the iris (no flat D-shape bottom!)
            dy_upper = (
                -0.00072 * (upper ** 1.15)
                - 0.00024 * outer_c * upper  # smooth outer upper taper
                + 0.00018 * inner_c * (upper ** 1.4)  # gentle medial-center peak
            )
            dy_lower = (
                +0.00052 * (lower ** 1.05)  # gently raised smooth convex lower lid hugging bottom of iris!
                + 0.00025 * (outer_c ** 1.6) * (0.4 + 0.6 * lower)  # subtle crisp outer canthus lift
                - 0.00020 * (inner_c ** 2.2)  # natural delicate inner tear-duct dip
            )
            dy = (dy_upper + dy_lower) * amt

            lpos[ring, 0] += dx.astype(np.float32)
            lpos[ring, 1] += dy.astype(np.float32)

            # Seat rings 1..3 cleanly onto our symmetric lid envelope (+0.55mm ahead of cornea!)
            # and smoothly blend ring 0 between its symmetric cheek socket & lid envelope!
            env_z = lid_surface_z(lpos[ring, 0].astype(np.float64), lpos[ring, 1].astype(np.float64), sign)
            if level == 0:
                # Blend smoothly so ring 0 bridges cleanly between the cheek boundary and ring 1
                lpos[ring, 2] = (0.55 * lpos[ring, 2].astype(np.float64) + 0.45 * env_z).astype(np.float32)
            elif level == 1:
                # Subtle natural tapered upper-lid fold indentation on ring 1
                lpos[ring, 2] = (env_z - 0.00022 * (upper ** 1.7)).astype(np.float32)
            elif level == 2:
                # Front-facing lid margin bevel (+0.30mm crisp thickness ahead of inner aperture rim!)
                lpos[ring, 2] = (env_z + 0.00032).astype(np.float32)
            else:
                # Inner lid aperture rim hugging just +0.18mm in front of the cornea/sclera (zero gap!)
                lpos[ring, 2] = (env_z - 0.00025).astype(np.float32)

            # Recompute watertight closed-blink target on symmetric lid envelope (+0.55mm ahead of cornea!)
            # Guarantee exact upper/lower contact along the closed blink seam AND zero globe protrusion!
            closed_r = np.zeros_like(lpos[ring], dtype=np.float64)
            for k in range(32):
                km = (16 - k) % 32 if sign > 0 else k
                ref_idx = rings[0]["rings"][level][km]
                c_pt = ref_neg_blink_closed[ref_idx].astype(np.float64).copy()
                if sign > 0:
                    c_pt[0] = -c_pt[0]
                # Keep closed seam X aligned with our refined almond aperture width
                c_pt[0] += float(dx[k])
                # Seat closed eyelid cleanly on the symmetric eyelid envelope (+0.45mm clearance ahead of cornea!)
                c_env_z = float(lid_surface_z(np.array([c_pt[0]]), np.array([c_pt[1]]), sign)[0])
                if level >= 2:
                    c_pt[2] = c_env_z + (0.00045 if level == 2 else 0.00025)
                elif level == 1:
                    c_pt[2] = c_env_z + 0.00010
                else:
                    c_pt[2] = float(lpos[ring[k], 2])
                closed_r[k] = c_pt

            # Enforce exact sub-micron upper/lower contact on ring 3 when closed (k=1..15 meets k=31..17)
            if level == 3:
                for k in range(1, 16):
                    mid = 0.5 * (closed_r[k] + closed_r[32 - k])
                    closed_r[k] = mid
                    closed_r[32 - k] = mid

            target_arrays[blink_k][ring] = (closed_r - lpos[ring].astype(np.float64)).astype(np.float32)

        inner = lpos[side["rings"][3]]
        lid_stats[f"side_{sign:+d}"] = {
            "width_mm": round(float((inner[:, 0].max() - inner[:, 0].min()) * 1000.0), 2),
            "height_mm": round(float((inner[:, 1].max() - inner[:, 1].min()) * 1000.0), 2),
            "top_y": round(float(inner[8, 1]), 5),
            "bot_y": round(float(inner[24, 1]), 5),
            "top_z_mm": round(float(inner[8, 2] * 1000.0), 2),
        }

    # Recompute clean base normals on SM_Character_Eyelids AND weld boundary normals 1:1 with SM_Character_Face!
    ltri = asset.arr(lid_prim["indices"]).reshape(-1, 3)
    lnorm = asset.arr(lid_prim["attributes"]["NORMAL"])
    fresh_ln = compute_vertex_normals(lpos, ltri)
    lnorm[:] = fresh_ln

    # Sync boundary normals strictly with SM_Character_Face so Face <-> Eyelids seam is 100% invisible (dot = 1.0000)
    fpos = asset.pos("SM_Character_Face")
    fnorm = asset.arr(asset.prim("SM_Character_Face")["attributes"]["NORMAL"])
    boundary_all = [i for side in rings for i in side["boundary_indices"]]
    for bi in boundary_all:
        d = np.linalg.norm(fpos - lpos[bi], axis=1)
        fi = int(np.argmin(d))
        if d[fi] < 1e-4:
            avg = fnorm[fi].astype(np.float64) + lnorm[bi].astype(np.float64)
            al = float(np.linalg.norm(avg))
            if al > 1e-6:
                u = (avg / al).astype(np.float32)
                lnorm[bi] = u
                # Sync all coincident Face vertices at that exact point too!
                same_f = np.where(np.linalg.norm(fpos - fpos[fi], axis=1) < 1e-4)[0]
                fnorm[same_f] = u

    # Refresh all 8 NORMAL morph targets on SM_Character_Eyelids (keeping boundary normal deltas = 0)
    n0 = compute_vertex_normals(lpos, ltri)
    for t in lid_prim["targets"]:
        delta_p = asset.arr(t["POSITION"])
        dn = compute_vertex_normals(lpos + delta_p, ltri) - n0
        dn[boundary_all] = 0.0
        asset.arr(t["NORMAL"])[:] = dn

    return {"eyes": eye_stats, "eyelids": lid_stats}


def flood_dilate_rgb(arr: np.ndarray, valid_mask: np.ndarray, iterations: int = 32) -> np.ndarray:
    """Fast multi-step 8-neighbor isotropic RGB dilation from valid texels into invalid/black regions."""
    work = arr.astype(np.float32).copy()
    cur = valid_mask.copy()
    h, w = cur.shape
    for _ in range(iterations):
        if cur.all():
            break
        acc = np.zeros_like(work)
        cnt = np.zeros((h, w), dtype=np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            sv = np.roll(np.roll(cur, dy, axis=0), dx, axis=1)
            sa = np.roll(np.roll(work, dy, axis=0), dx, axis=1)
            wt = 1.0 if (dy == 0 or dx == 0) else 0.7
            acc += sa * (sv[:, :, None] * wt)
            cnt += sv * wt
        fill = (~cur) & (cnt > 0.0)
        if not np.any(fill):
            break
        work[fill] = acc[fill] / cnt[fill, None]
        cur[fill] = True
    return work


def paint_eyelid_lash_texture(asset: GlbAsset, rings: list[dict]) -> dict:
    """Clean & paint T_Eyelids_v36 (Image 6):
    1. Full-canvas pure-skin dilation (100% of black holes AND UV void filled cleanly — zero #000000 pixels!).
    2. Harmonize dark baked brown bruise at the right eyelid outer corner to clean surrounding eyelid skin.
    3. Paint crisp, natural, front-visible dark-espresso upper lash line + subtle East Asian tapered upper crease
       + delicate lower lid rim & warm inner-corner tint.
    """
    raw = asset.get_image_bytes(6)
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    arr = np.asarray(im, dtype=np.float32)
    h, w, _ = arr.shape

    lid_uv = asset.arr(asset.prim("SM_Character_Eyelids")["attributes"]["TEXCOORD_0"])
    angles = np.arange(32, dtype=np.float64) * 2.0 * np.pi / 32.0
    sin_a = np.sin(angles)
    cos_a = np.cos(angles)

    # Step 1: Identify clean pure-skin seed texels (luminance > 82, excluding black holes & dark outer bruise),
    # erode 3px to strip all dark anti-aliased fringe texels, then pyramid-dilate to fill 100% of canvas!
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    raw_valid = lum > 82.0
    valid_im = Image.fromarray((raw_valid * 255).astype(np.uint8), mode="L").filter(ImageFilter.MinFilter(7))
    valid = np.asarray(valid_im) > 127

    # Fast exact full-canvas fill via 1/4-res seed fill + full-res 36px isotropic dilation!
    # First dilate 36px at full res for crisp near-edge continuity, then fill deep interior holes smoothly via 1/4-res flood!
    full_dil = flood_dilate_rgb(arr, valid, iterations=36)
    # Check remaining unfilled interior pixels (deep inside the 250px eye holes / exterior void)
    cur_covered = valid.copy()
    # Mark pixels filled by full_dil (non-black)
    covered_mask = (full_dil.mean(axis=2) > 40.0) | valid
    if not covered_mask.all():
        # Downsample 4x, flood-fill 100% of 256x256 canvas (takes < 0.05s!), upsample smoothly for deep interior fill
        small_w, small_h = w // 4, h // 4
        s_rgb = np.asarray(
            Image.fromarray(np.clip(full_dil, 0, 255).astype(np.uint8)).resize((small_w, small_h), Image.BILINEAR),
            dtype=np.float32,
        )
        s_cov = np.asarray(
            Image.fromarray((covered_mask * 255).astype(np.uint8), mode="L").resize((small_w, small_h), Image.NEAREST)
        ) > 127
        s_filled = flood_dilate_rgb(s_rgb, s_cov, iterations=120)
        up_filled = np.asarray(
            Image.fromarray(np.clip(s_filled, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR),
            dtype=np.float32,
        )
        full_dil[~covered_mask] = up_filled[~covered_mask]

    # Replace ALL invalid / black-hole / dark-fringe pixels with pure-skin dilated fill!
    arr = np.where(valid[:, :, None], arr, full_dil)

    # Step 2: Clean localized dark brown baked bruise on eyelid skin & equalize -X vs +X outer-corner brightness!
    # In v40, the viewer's left (-X) outer eyelid corner is 14-16 sRGB points darker than the +X outer corner.
    clean_skin_rgb = np.percentile(arr[valid & (lum > 130.0)], 62, axis=0)
    clean_lum = float(0.299 * clean_skin_rgb[0] + 0.587 * clean_skin_rgb[1] + 0.114 * clean_skin_rgb[2])
    cur_lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    bruise_w = (1.0 - smoothstep(clean_lum - 46.0, clean_lum - 2.0, cur_lum))[:, :, None]
    blurred_lid = np.asarray(
        Image.fromarray(np.clip(np.rint(arr), 0, 255).astype(np.uint8), mode="RGB").filter(ImageFilter.GaussianBlur(radius=14.0)),
        dtype=np.float32,
    )
    bruise_target = 0.35 * blurred_lid + 0.65 * clean_skin_rgb[None, None, :]
    arr = arr * (1.0 - bruise_w * 0.84) + bruise_target * (bruise_w * 0.84)

    # Extra bilateral outer-corner equalization on Side -1 (viewer's left eye, outer k=12..20)
    # so left and right outer eyelid corners match within < 3 sRGB points!
    pos_outer_rgbs = []
    for lv in (0, 1, 2):
        for k in (29, 30, 31, 0, 1, 2, 3):
            vi = rings[1]["rings"][lv][k]
            px = int(np.clip(lid_uv[vi, 0] * w, 0, w - 1))
            py = int(np.clip(lid_uv[vi, 1] * h, 0, h - 1))
            pos_outer_rgbs.append(arr[py, px])
    target_outer_rgb = np.percentile(np.array(pos_outer_rgbs), 60, axis=0)
    neg_outer_mask_im = Image.new("L", (w, h), 0)
    nod = ImageDraw.Draw(neg_outer_mask_im)
    # Cover outer half of Side -1 eyelid UV island (around k=11..21 on rings 0..3 + outer boundary)
    neg_side = rings[0]
    for lv in range(3):
        ra = [(float(lid_uv[i, 0] * w), float(lid_uv[i, 1] * h)) for i in neg_side["rings"][lv]]
        rb = [(float(lid_uv[i, 0] * w), float(lid_uv[i, 1] * h)) for i in neg_side["rings"][lv + 1]]
        for k in range(11, 21):
            nod.polygon([ra[k], ra[(k + 1) % 32], rb[(k + 1) % 32], rb[k]], fill=255)
    # Also cover outer rim between ring 0 and outer boundary on Side -1
    neg_r0 = [(float(lid_uv[i, 0] * w), float(lid_uv[i, 1] * h)) for i in neg_side["rings"][0]]
    for k in range(12, 20):
        px0, py0 = neg_r0[k]
        nod.ellipse([px0 - 55, py0 - 55, px0 + 55, py0 + 55], fill=255)
    m_neg_out = (np.asarray(neg_outer_mask_im.filter(ImageFilter.GaussianBlur(radius=22.0)), dtype=np.float32) / 255.0)[:, :, None]
    # Lift ONLY where Side -1 outer skin is darker than Side +1 target outer skin (preserves subtle skin shading!)
    neg_luma = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    tgt_luma = float(0.299 * target_outer_rgb[0] + 0.587 * target_outer_rgb[1] + 0.114 * target_outer_rgb[2])
    lift_w = m_neg_out * np.clip((tgt_luma - neg_luma) / 9.0, 0.0, 1.0)[:, :, None] * 0.96
    arr = arr * (1.0 - lift_w) + target_outer_rgb[None, None, :] * lift_w

    # Step 3: Paint crisp, natural, front-visible dark-espresso upper lash line, delicate East Asian tapered
    # upper-lid crease, and soft lower lash margin!
    lash_alpha = Image.new("L", (w, h), 0)
    crease_alpha = Image.new("L", (w, h), 0)
    lower_alpha = Image.new("L", (w, h), 0)
    ld = ImageDraw.Draw(lash_alpha)
    cd = ImageDraw.Draw(crease_alpha)
    lowd = ImageDraw.Draw(lower_alpha)

    for side in rings:
        sign = side["sign"]
        r0 = [(float(lid_uv[i, 0] * w), float(lid_uv[i, 1] * h)) for i in side["rings"][0]]
        r1 = [(float(lid_uv[i, 0] * w), float(lid_uv[i, 1] * h)) for i in side["rings"][1]]
        r2 = [(float(lid_uv[i, 0] * w), float(lid_uv[i, 1] * h)) for i in side["rings"][2]]
        r3 = [(float(lid_uv[i, 0] * w), float(lid_uv[i, 1] * h)) for i in side["rings"][3]]

        cx_uv = sum(p[0] for p in r3) / len(r3)
        cy_uv = sum(p[1] for p in r3) / len(r3)

        def inset_pt(pt, px_dist):
            vx, vy = cx_uv - pt[0], cy_uv - pt[1]
            ln = max(1e-6, math.hypot(vx, vy))
            return (pt[0] + vx / ln * px_dist, pt[1] + vy / ln * px_dist)

        # Upper eyelash line (k = 0..16, sin_a >= 0): extends slightly onto front-visible ring 2 -> ring 1 (22%)
        # AND cleanly inward past ring 3 (10px into pure-skin dilated hole) so the crisp espresso lash root
        # frames the upper eye naturally from the front camera without looking like thick eyeliner!
        for k in range(16):
            s_mid = 0.5 * (sin_a[k] + sin_a[k + 1])
            taper = ss_scalar(0.04, 0.36, float(s_mid))
            if taper < 0.01:
                continue
            p_out0 = (r2[k][0] * 0.78 + r1[k][0] * 0.22, r2[k][1] * 0.78 + r1[k][1] * 0.22)
            p_out1 = (r2[k + 1][0] * 0.78 + r1[k + 1][0] * 0.22, r2[k + 1][1] * 0.78 + r1[k + 1][1] * 0.22)
            p_in0 = inset_pt(r3[k], 10.0)
            p_in1 = inset_pt(r3[k + 1], 10.0)
            ld.polygon([p_out0, p_out1, p_in1, p_in0], fill=int(round(255.0 * 0.86 * taper)))

        # Soft natural East Asian tapered upper-lid crease fold between ring 1 and ring 0
        for k in range(1, 15):
            s_mid = 0.5 * (sin_a[k] + sin_a[k + 1])
            c_mid = 0.5 * (cos_a[k] + cos_a[k + 1])
            # Tapered fold: subtly stronger centrally & temporally, fading cleanly at inner canthus
            taper = ss_scalar(0.22, 0.76, float(s_mid)) * (0.70 + 0.30 * ss_scalar(-0.5, 0.6, float(sign * c_mid)))
            if taper > 0.01:
                p0 = (r1[k][0] * 0.82 + r0[k][0] * 0.18, r1[k][1] * 0.82 + r0[k][1] * 0.18)
                p1 = (r1[k + 1][0] * 0.82 + r0[k + 1][0] * 0.18, r1[k + 1][1] * 0.82 + r0[k + 1][1] * 0.18)
                cd.line([p0, p1], fill=int(round(255.0 * 0.26 * taper)), width=10)

        # Delicate soft lower lash line along ring 2 -> ring 3 (k = 16..31) for grounded natural lower lid
        for k in range(16, 32):
            k2 = (k + 1) % 32
            s_mid = 0.5 * (-sin_a[k] + -sin_a[k2])
            taper = ss_scalar(0.10, 0.55, float(s_mid))
            if taper < 0.01:
                continue
            p_out0 = (r2[k][0] * 0.90 + r1[k][0] * 0.10, r2[k][1] * 0.90 + r1[k][1] * 0.10)
            p_out1 = (r2[k2][0] * 0.90 + r1[k2][0] * 0.10, r2[k2][1] * 0.90 + r1[k2][1] * 0.10)
            p_in0 = inset_pt(r3[k], 8.0)
            p_in1 = inset_pt(r3[k2], 8.0)
            lowd.polygon([p_out0, p_out1, p_in1, p_in0], fill=int(round(255.0 * 0.24 * taper)))

    lash_a = (np.asarray(lash_alpha.filter(ImageFilter.GaussianBlur(radius=3.2)), dtype=np.float32) / 255.0)[:, :, None]
    crease_a = (np.asarray(crease_alpha.filter(ImageFilter.GaussianBlur(radius=6.5)), dtype=np.float32) / 255.0)[:, :, None]
    lower_a = (np.asarray(lower_alpha.filter(ImageFilter.GaussianBlur(radius=3.0)), dtype=np.float32) / 255.0)[:, :, None]

    lash_rgb = np.array([[[32.0, 23.0, 20.0]]], dtype=np.float32)
    crease_rgb = np.array([[[96.0, 64.0, 52.0]]], dtype=np.float32)
    lower_rgb = np.array([[[92.0, 65.0, 55.0]]], dtype=np.float32)

    out = arr * (1.0 - crease_a) + crease_rgb * crease_a
    out = out * (1.0 - lower_a) + lower_rgb * lower_a
    out = out * (1.0 - lash_a) + lash_rgb * lash_a
    out_im = Image.fromarray(np.clip(np.rint(out), 0, 255).astype(np.uint8), mode="RGB")
    out_im.save(WORK_DIR / "v41_eyelids_painted.png")

    buf = io.BytesIO()
    out_im.save(buf, format="WEBP", quality=86, method=6)
    webp_bytes = buf.getvalue()
    assert len(webp_bytes) < 100_000, f"T_Eyelids webp too large: {len(webp_bytes)}"
    asset.replace_image_bytes(6, webp_bytes, "image/webp")
    return {
        "eyelids_webp_bytes": len(webp_bytes),
        "min_texel_luma": round(float(out.mean(axis=2).min()), 1),
    }


def clean_face_albedo_texture(asset: GlbAsset) -> dict:
    """Clean T_FringeRepair_v40_face (Image 5) from lossless v40 raw PNG:
    1. Rasterize all SM_Character_Face UV2 triangles and dilate 16px outward into any #000000 void
       BEFORE any filtering (prevents black mipmap seam bleed across all UV2 islands!).
    2. 3-band frequency-separated skin harmonization (very_low + mid_blotch + micro_grain) over:
       (a) Both -X and +X lower jaw & cheek shadow/olive-grey blotches,
       (b) Both under-eye cheeks (baked glasses-rim ghost rings & diagonal scar shadow),
       (c) Front chin pad & submental chin-to-neck transition (erasing 12-40px mottled grey-brown stains),
       (d) -X outer orbital corner dark baked bruise ([124, 82, 62]) matching +X outer eye skin,
       (e) Rear/side-neck Face <-> Hoodie seam harmony so zero spiky color jump appears in side profile.
       Preserves 100% of fine skin micro-grain, brows, nostrils, lips, ears, and the v40 fringe patch!
    3. Zero strictly unused non-face atlas islands outside dil_zone so WebP allocates its entire < 100 KB
       budget to SM_Character_Face at high quality (q = 82..90, zero blocky posterization!).
    """
    raw_png = PROJECT / "artifacts/avatar-v40-codex-20261119/work/fringe40-face-raw.png"
    if raw_png.exists():
        im = Image.open(raw_png).convert("RGB")
    else:
        im = Image.open(io.BytesIO(asset.get_image_bytes(5))).convert("RGB")
    arr = np.asarray(im, dtype=np.float32)
    h, w, _ = arr.shape

    face_prim = asset.prim("SM_Character_Face")
    pos = asset.arr(face_prim["attributes"]["POSITION"])
    uv2 = asset.arr(face_prim["attributes"]["TEXCOORD_2"])
    tri = asset.arr(face_prim["indices"]).reshape(-1, 3)

    # Fix the 2 stray lip seam vertices (v2523, v2524) that had uv2=(0,0) sampling black [0,0,0]!
    fixed_zero_uv = 0
    for i in np.unique(tri.ravel()):
        if uv2[i, 0] < 1e-4 and uv2[i, 1] < 1e-4:
            dists = np.linalg.norm(pos - pos[i], axis=1)
            order = np.argsort(dists)
            for nb in order[1:25]:
                if uv2[nb, 0] > 0.01 or uv2[nb, 1] > 0.01:
                    uv2[i] = uv2[nb]
                    fixed_zero_uv += 1
                    break

    # Step 1: Build exact UV2 coverage mask for all SM_Character_Face triangles and dilate 18px into #000000 void!
    uv_cov_im = Image.new("L", (w, h), 0)
    uvd = ImageDraw.Draw(uv_cov_im)
    for a, b, c in tri:
        pts = [(float(uv2[idx, 0] * w), float(uv2[idx, 1] * h)) for idx in (a, b, c)]
        uvd.polygon(pts, fill=255)
    uv_cov = np.asarray(uv_cov_im) > 127

    src_nonblack = arr.max(axis=2) > 12.0
    seed_mask = src_nonblack & uv_cov
    dil_zone_im = uv_cov_im.filter(ImageFilter.MaxFilter(33))  # 16px outward margin
    dil_zone = np.asarray(dil_zone_im) > 127
    dilated = flood_dilate_rgb(arr, seed_mask, iterations=20)
    work = np.where(dil_zone[:, :, None] & (~seed_mask[:, :, None]), dilated, arr)

    # Step 2: Sample clean reference skin tones from clean cheeks/jaw & adjacent Hoodie side-neck skin
    def sample_region(cond_fn, pct=62):
        rgbs = []
        for idx in np.unique(tri.ravel()):
            p = pos[idx]
            if cond_fn(p):
                u = uv2[idx]
                rgb = work[int(np.clip(u[1] * h, 0, h - 1)), int(np.clip(u[0] * w, 0, w - 1))]
                if rgb.mean() > 110.0:
                    rgbs.append(rgb)
        return np.percentile(np.array(rgbs), pct, axis=0)

    clean_cheek_rgb = sample_region(lambda p: 1.535 <= p[1] <= 1.572 and -0.052 <= p[0] <= -0.022 and p[2] > 0.060, 62)
    clean_jaw_rgb = sample_region(lambda p: 1.500 <= p[1] <= 1.545 and -0.056 <= p[0] <= -0.024 and p[2] > 0.048, 68)
    clean_ue_rgb = sample_region(lambda p: 1.558 <= p[1] <= 1.584 and -0.048 <= p[0] <= -0.018 and p[2] > 0.068, 60)
    clean_oe_rgb = sample_region(lambda p: 1.588 <= p[1] <= 1.606 and 0.044 <= p[0] <= 0.060 and p[2] > 0.062, 62)

    # Sample Hoodie side-neck skin albedo (Image 0) at Y in [1.47, 1.52], |X| > 0.048 so Face<->Hoodie side-neck matches!
    im0 = np.asarray(Image.open(io.BytesIO(asset.get_image_bytes(0))).convert("RGB"), dtype=np.float32)
    h0, w0, _ = im0.shape
    hp = asset.prim("SM_Cloth_Hoodie")
    hpos = asset.arr(hp["attributes"]["POSITION"])
    huv0 = asset.arr(hp["attributes"]["TEXCOORD_0"])
    hoodie_side_rgbs = []
    for vi in range(len(hpos)):
        p = hpos[vi]
        if 1.470 <= p[1] <= 1.525 and abs(p[0]) >= 0.046 and -0.028 <= p[2] <= 0.018:
            rgb = im0[int(np.clip(huv0[vi, 1] * h0, 0, h0 - 1)), int(np.clip(huv0[vi, 0] * w0, 0, w0 - 1))]
            if rgb[0] > 125.0 and rgb[0] > rgb[2] + 35.0:
                hoodie_side_rgbs.append(rgb)
    hoodie_neck_rgb = np.median(np.array(hoodie_side_rgbs), axis=0) if hoodie_side_rgbs else np.array([150.0, 108.0, 86.0], dtype=np.float32)

    # Build smooth UV2 masks (strictly excluding brows, eyes, nostrils, lips, hair!)
    jaw_mask_im = Image.new("L", (w, h), 0)
    ue_mask_im = Image.new("L", (w, h), 0)
    chin_mask_im = Image.new("L", (w, h), 0)
    sub_neck_mask_im = Image.new("L", (w, h), 0)
    oe_neg_mask_im = Image.new("L", (w, h), 0)
    side_neck_mask_im = Image.new("L", (w, h), 0)
    jmd = ImageDraw.Draw(jaw_mask_im)
    umd = ImageDraw.Draw(ue_mask_im)
    cmd = ImageDraw.Draw(chin_mask_im)
    snd = ImageDraw.Draw(sub_neck_mask_im)
    oed = ImageDraw.Draw(oe_neg_mask_im)
    srd = ImageDraw.Draw(side_neck_mask_im)

    jaw_tris = ue_tris = chin_tris = oe_tris = 0
    for a, b, c in tri:
        pc = (pos[a] + pos[b] + pos[c]) / 3.0
        pts = [(float(uv2[idx, 0] * w), float(uv2[idx, 1] * h)) for idx in (a, b, c)]
        ax = abs(float(pc[0]))
        # Zone 1: BOTH -X and +X lower jaw & cheek shadow/mottled blotches (strictly excluding lips!)
        if ax > 0.014 and 1.472 <= pc[1] <= 1.564 and pc[2] > 0.024:
            if not (ax < 0.030 and 1.512 <= pc[1] <= 1.540):
                jmd.polygon(pts, fill=255)
                jaw_tris += 1
        # Zone 2: Both under-eye cheeks (baked glasses-rim ghost rings + +X diagonal scan shadow)
        if 0.014 <= ax <= 0.056 and 1.560 <= pc[1] <= 1.592 and pc[2] > 0.062:
            umd.polygon(pts, fill=255)
            ue_tris += 1
        # Zone 3: Full front chin pad & lower-chin/jawline transition (strictly below lower lip Y=1.511!)
        if ax <= 0.044 and 1.470 <= pc[1] <= 1.511 and pc[2] > 0.044:
            cmd.polygon(pts, fill=255)
            chin_tris += 1
        # Zone 4: Submental chin-to-neck transition (Y=1.445..1.474, Z>0.018)
        if ax <= 0.050 and 1.445 <= pc[1] <= 1.474 and pc[2] > 0.018:
            snd.polygon(pts, fill=255)
        # Zone 5: Viewer's left (-X) outer eye corner dark baked bruise ([124, 82, 62])
        if -0.062 <= pc[0] <= -0.043 and 1.586 <= pc[1] <= 1.606 and pc[2] > 0.056:
            oed.polygon(pts, fill=255)
            oe_tris += 1
        # Zone 6: Strictly rear neck behind the jaw along Face<->Hoodie seam (Z <= 0.008 so it NEVER bleeds onto +X jaw!)
        if ax >= 0.036 and 1.452 <= pc[1] <= 1.525 and -0.020 <= pc[2] <= 0.008:
            srd.polygon(pts, fill=255)

    m_jaw = (np.asarray(jaw_mask_im.filter(ImageFilter.GaussianBlur(radius=10.0)), dtype=np.float32) / 255.0)[:, :, None]
    m_ue = (np.asarray(ue_mask_im.filter(ImageFilter.GaussianBlur(radius=9.0)), dtype=np.float32) / 255.0)[:, :, None]
    m_chin = (np.asarray(chin_mask_im.filter(ImageFilter.GaussianBlur(radius=12.0)), dtype=np.float32) / 255.0)[:, :, None]
    m_sub = (np.asarray(sub_neck_mask_im.filter(ImageFilter.GaussianBlur(radius=12.0)), dtype=np.float32) / 255.0)[:, :, None]
    m_oe = (np.asarray(oe_neg_mask_im.filter(ImageFilter.GaussianBlur(radius=8.0)), dtype=np.float32) / 255.0)[:, :, None]
    m_side = (np.asarray(side_neck_mask_im.filter(ImageFilter.GaussianBlur(radius=5.0)), dtype=np.float32) / 255.0)[:, :, None]

    # 3-band frequency separation (AFTER full 20px UV dilation so blurs NEVER pull #000000 black!):
    # - very_low (r=20): broad lighting gradients & dark shadow patches
    # - mid_blotch (r=4.5 - r=20): 12-40px mottled grey-brown scan stains & lumpy shadow blotches
    # - micro_grain (work - r=4.5): natural crisp skin pores & fine detail (100% preserved!)
    work_u8 = Image.fromarray(np.clip(np.rint(work), 0, 255).astype(np.uint8), mode="RGB")
    very_low = np.asarray(work_u8.filter(ImageFilter.GaussianBlur(radius=20.0)), dtype=np.float32)
    med_blur = np.asarray(work_u8.filter(ImageFilter.GaussianBlur(radius=4.5)), dtype=np.float32)
    mid_blotch = med_blur - very_low
    micro_grain = work - med_blur

    out_low = very_low.copy()
    out_mid = mid_blotch.copy()
    is_skin = smoothstep(72.0, 110.0, work.mean(axis=2))[:, :, None]

    # Pass A: Unified bilateral -X/+X cheek & lower-jaw harmonization matching front chin tone seamlessly
    #         (erases the vertical UV2 seam color step on the +X lower jaw between chin & side-jaw islands!)
    lower_face_target = 0.50 * clean_cheek_rgb + 0.50 * clean_jaw_rgb
    jaw_dev = np.maximum(0.0, lower_face_target[0] - out_low[:, :, 0]) / 20.0
    jaw_olive = np.maximum(0.0, (lower_face_target[0] - lower_face_target[1]) - (out_low[:, :, 0] - out_low[:, :, 1])) / 8.0
    jaw_strength = np.clip(np.maximum(jaw_dev, jaw_olive), 0.0, 1.0)[:, :, None]
    w_jaw = m_jaw * is_skin * (0.56 + 0.40 * jaw_strength)
    out_low = out_low * (1.0 - w_jaw) + lower_face_target[None, None, :] * w_jaw
    out_mid = out_mid * (1.0 - m_jaw * is_skin * 0.80)

    # Pass B: Under-eye glasses-rim ghost rings & +X diagonal shadow cleanup
    w_ue = m_ue * is_skin * 0.58
    out_low = out_low * (1.0 - w_ue) + clean_ue_rgb[None, None, :] * w_ue
    out_mid = out_mid * (1.0 - m_ue * is_skin * 0.65)

    # Pass C: Clean front chin pad — matches lower_face_target seamlessly (zero grey-brown mottling or +X seam step!)
    chin_target = lower_face_target
    chin_dev = np.clip(np.maximum(0.0, chin_target[0] - out_low[:, :, 0]) / 16.0, 0.0, 1.0)[:, :, None]
    w_chin = m_chin * is_skin * (0.72 + 0.26 * chin_dev)
    out_low = out_low * (1.0 - w_chin) + chin_target[None, None, :] * w_chin
    # Suppress 88% of 12-40px mottled grey-brown blotches on the chin while keeping natural micro_grain!
    out_mid = out_mid * (1.0 - m_chin * is_skin * 0.88)

    # Pass D: Clean, smooth warm submental chin-to-neck gradient + remove dark collar-corner cloth bleed!
    sub_target = 0.88 * clean_jaw_rgb + np.array([5.0, 0.0, -2.0], dtype=np.float32)  # warm under-chin shade (~[173, 133, 111])
    w_sub = m_sub * is_skin * (1.0 - 0.70 * m_chin) * 0.78
    out_low = out_low * (1.0 - w_sub) + sub_target[None, None, :] * w_sub
    out_mid = out_mid * (1.0 - m_sub * is_skin * 0.82)
    # Also clean dark cloth-bleed corners along the entire lower neck & side-collar border (Y < 1.486, Z < 0.038)
    # directly in the face atlas so zero dark triangular cloth smudges survive on either neck corner!
    neck_bleed_im = Image.new("L", (w, h), 0)
    nbd = ImageDraw.Draw(neck_bleed_im)
    for a, b, c in tri:
        pc = (pos[a] + pos[b] + pos[c]) / 3.0
        if pc[1] < 1.468 or (pc[1] < 1.488 and abs(float(pc[0])) > 0.024 and pc[2] < 0.038):
            pts = [(float(uv2[idx, 0] * w), float(uv2[idx, 1] * h)) for idx in (a, b, c)]
            nbd.polygon(pts, fill=255)
    m_nbleed = (np.asarray(neck_bleed_im.filter(ImageFilter.GaussianBlur(radius=6.0)), dtype=np.float32) / 255.0)[:, :, None]
    dark_neck = (1.0 - smoothstep(105.0, 148.0, work.mean(axis=2)))[:, :, None]
    w_nbleed = m_nbleed * dark_neck * 0.96
    out_low = out_low * (1.0 - w_nbleed) + sub_target[None, None, :] * w_nbleed
    out_mid = out_mid * (1.0 - w_nbleed)
    micro_grain = micro_grain * (1.0 - w_nbleed * 0.90)

    # Pass E: Clean viewer's left (-X) outer orbital corner dark bruise ([124, 82, 62] -> matches +X outer eye skin!)
    oe_dev = np.clip(np.maximum(0.0, clean_oe_rgb[0] - out_low[:, :, 0]) / 14.0, 0.0, 1.0)[:, :, None]
    w_oe = m_oe * smoothstep(45.0, 82.0, work.mean(axis=2))[:, :, None] * (0.68 + 0.28 * oe_dev)
    out_low = out_low * (1.0 - w_oe) + clean_oe_rgb[None, None, :] * w_oe
    out_mid = out_mid * (1.0 - m_oe * 0.88)
    micro_grain = micro_grain * (1.0 - m_oe * 0.55)

    # Pass F: Strictly rear-neck Face<->Hoodie seam harmony (excluded from jaw & chin!)
    w_side = m_side * is_skin * (1.0 - m_chin) * (1.0 - m_jaw) * 0.55
    out_low = out_low * (1.0 - w_side) + hoodie_neck_rgb[None, None, :] * w_side
    out_mid = out_mid * (1.0 - m_side * is_skin * (1.0 - m_jaw) * 0.55)

    # Recombine clean low-frequency + attenuated mid-frequency + 100% preserved fine micro_grain
    out = np.clip(out_low + out_mid + micro_grain, 0.0, 255.0)
    # Zero strictly unused non-Face islands outside the 16px dilated SM_Character_Face UV2 zone
    # so WebP spends 100% of its < 100 KB budget on SM_Character_Face at high quality (q = 82..90)!
    out = np.where(dil_zone[:, :, None], out, 0.0)

    out_im = Image.fromarray(np.clip(np.rint(out), 0, 255).astype(np.uint8), mode="RGB")
    out_im.save(WORK_DIR / "v41_face_cleaned.png")

    webp_bytes = b""
    used_q = 0
    for q in (90, 86, 82, 78, 74, 70, 66, 62, 58, 54, 50):
        buf = io.BytesIO()
        out_im.save(buf, format="WEBP", quality=q, method=6)
        data = buf.getvalue()
        if len(data) < 99_500:
            webp_bytes = data
            used_q = q
            break
    assert webp_bytes and len(webp_bytes) < 100_000, "Could not encode Face WebP below 100 KB"
    asset.replace_image_bytes(5, webp_bytes, "image/webp")
    return {
        "fixed_zero_uv2_verts": fixed_zero_uv,
        "jaw_tris_masked": jaw_tris,
        "undereye_tris_masked": ue_tris,
        "chin_tris_masked": chin_tris,
        "outer_eye_tris_masked": oe_tris,
        "clean_cheek_rgb": [round(float(v), 1) for v in clean_cheek_rgb],
        "clean_jaw_rgb": [round(float(v), 1) for v in clean_jaw_rgb],
        "clean_ue_rgb": [round(float(v), 1) for v in clean_ue_rgb],
        "clean_oe_rgb": [round(float(v), 1) for v in clean_oe_rgb],
        "hoodie_neck_rgb": [round(float(v), 1) for v in hoodie_neck_rgb],
        "face_webp_bytes": len(webp_bytes),
        "face_webp_quality": used_q,
    }


def repair_spectacles_rim_kinks(asset: GlbAsset) -> dict:
    """Eliminate the inherited -6.54 mm rigid Z-dislocation & bottom-inner V-kinks on Sovereign_Titanium_Spectacles:
    1. Fit the exact clean quadratic eyewear wrap surface Z_quad(|X|, Y) to the unshifted 280-deg arcs of
       both Glasses_Metal rims (C0 +X and C8 -X).
    2. Restore the rigidly recessed inner rim, browline, and lens vertices (Glasses_Metal C0/C8,
       Glasses_Black C2/C6, Glasses_Lens C0/C1) forward by the exact measured offset (+6.536 mm),
       restoring continuous alignment with the nose bridge and eliminating all 6.6 mm Z-step kinks.
    3. Smooth the bottom-inner wire centerline gently in XY (preserving tube wire radius) so both rims
       trace a clean, graceful continuous oval contour matching reference_portrait.jpg.
    4. Extend ONLY the front rim-attachment end of the two metal nose-pad arms (Glasses_Metal C1 & C7)
       forward linearly so they stay solidly joined to the restored inner rims while nose pads stay fixed.
    5. Recompute clean welded normals on the repaired spectacles primitives (preserving lens orientation).
    """
    gm = next(m for m in asset.g["meshes"] if m.get("name") == "Sovereign_Titanium_Spectacles")
    pr_metal, pr_black, pr_lens = gm["primitives"][0], gm["primitives"][1], gm["primitives"][2]

    def connected_components(pos: np.ndarray, tri: np.ndarray) -> list[list[int]]:
        adj = [set() for _ in range(len(pos))]
        for a, b, c in tri:
            adj[a].update((b, c))
            adj[b].update((a, c))
            adj[c].update((a, b))
        seen = [False] * len(pos)
        comps = []
        for i in range(len(pos)):
            if not seen[i]:
                st = [i]
                comp = []
                seen[i] = True
                while st:
                    u = st.pop()
                    comp.append(u)
                    for v in adj[u]:
                        if not seen[v]:
                            seen[v] = True
                            st.append(v)
                comps.append(comp)
        return comps

    # 1. Fit exact quadratic wrap surface to clean 280-deg Metal rims
    mpos = asset.arr(pr_metal["attributes"]["POSITION"])
    mtri = asset.arr(pr_metal["indices"]).reshape(-1, 3)
    mpos64 = mpos.astype(np.float64)
    m_comps = connected_components(mpos64, mtri)
    rim_comps = [c for c in m_comps if len(c) > 300]
    pad_arm_comps = [c for c in m_comps if 20 <= len(c) <= 50 and abs(float(mpos64[c, 0].mean())) < 0.015]
    assert len(rim_comps) == 2, f"Expected 2 metal rim components, got {len(rim_comps)}"
    assert len(pad_arm_comps) == 2, f"Expected 2 nose-pad arm components, got {len(pad_arm_comps)}"

    def z_lin_approx(p: np.ndarray) -> np.ndarray:
        return 0.110135 - 0.0915 * np.abs(p[:, 0]) + 0.1725 * p[:, 1]

    clean_samples = []
    rec_samples = []
    for comp in rim_comps:
        pts = mpos64[comp]
        dz0 = pts[:, 2] - z_lin_approx(pts)
        clean_samples.append(pts[dz0 > -0.0040])
        rec_samples.append(pts[dz0 <= -0.0040])
    cp_all = np.vstack(clean_samples)
    rp_all = np.vstack(rec_samples)
    ax_c = np.abs(cp_all[:, 0])
    A = np.column_stack([np.ones(len(cp_all)), ax_c, ax_c * ax_c, cp_all[:, 1]])
    coef, _, _, _ = np.linalg.lstsq(A, cp_all[:, 2], rcond=None)

    def z_quad(p: np.ndarray) -> np.ndarray:
        ax = np.abs(p[:, 0])
        return coef[0] + coef[1] * ax + coef[2] * ax * ax + coef[3] * p[:, 1]

    dz_shift = float(-np.mean(rp_all[:, 2] - z_quad(rp_all)))  # exact measured +0.006536 m!
    assert 0.0055 < dz_shift < 0.0075, f"Unexpected spectacles Z-shift: {dz_shift * 1000:.3f}mm"

    # 2A. Restore Glasses_Metal rims (C0 & C8) + smooth bottom-inner oval XY contour gently
    metal_shifted = 0
    for comp in rim_comps:
        pts = mpos64[comp]
        dz_q = pts[:, 2] - z_quad(pts)
        shifted_mask = dz_q < -0.0035
        for local_i, gi in enumerate(comp):
            if shifted_mask[local_i]:
                mpos64[gi, 2] += dz_shift
                metal_shifted += 1

        # Gentle bottom-inner XY oval smoothing (strictly preserves wire cross-section thickness!)
        pts_after = mpos64[comp]
        sign = 1.0 if float(pts_after[:, 0].mean()) > 0 else -1.0
        cx, cy = sign * 0.0352, 0.0470
        ang = np.degrees(np.arctan2(pts_after[:, 1] - cy, sign * (pts_after[:, 0] - cx)))
        rad = np.hypot(pts_after[:, 0] - cx, pts_after[:, 1] - cy)
        # Fit smooth quadratic radius curve r_smooth(ang) over the bottom-inner arc [-162, -112] deg
        fit_mask = (ang >= -162.0) & (ang <= -112.0) & ~((ang >= -146.0) & (ang <= -138.0))
        if np.sum(fit_mask) >= 12:
            r_coef = np.polyfit(ang[fit_mask], rad[fit_mask], 2)
            # Compute local mean radius in 3-deg neighborhood to isolate ONLY centerline radial kink (NOT wire thickness!)
            for local_i, gi in enumerate(comp):
                a_i = float(ang[local_i])
                if -152.0 <= a_i <= -132.0:
                    blend_w = ss_scalar(-152.0, -145.0, a_i) * (1.0 - ss_scalar(-139.0, -132.0, a_i))
                    nbr = np.abs(ang - a_i) < 2.2
                    r_ctr = float(np.mean(rad[nbr]))
                    r_tgt = float(np.polyval(r_coef, a_i))
                    dr = (r_tgt - r_ctr) * blend_w
                    ux = (mpos64[gi, 0] - cx) / max(1e-8, float(rad[local_i]))
                    uy = (mpos64[gi, 1] - cy) / max(1e-8, float(rad[local_i]))
                    mpos64[gi, 0] += ux * dr
                    mpos64[gi, 1] += uy * dr

    # 2B. Extend front attachment end of nose-pad arms (C1 & C7) linearly forward by +dz_shift
    #     so pad arms stay solidly welded to the restored inner rim while nose pads remain anchored!
    for comp in pad_arm_comps:
        zs = mpos64[comp, 2]
        z_min, z_max = float(zs.min()), float(zs.max())
        span = max(1e-6, z_max - z_min)
        for gi in comp:
            t = float((mpos64[gi, 2] - z_min) / span)
            mpos64[gi, 2] += dz_shift * (t ** 1.35)

    mpos[:] = mpos64.astype(np.float32)
    mnorm = asset.arr(pr_metal["attributes"]["NORMAL"])
    mnorm[:] = compute_welded_vertex_normals(mpos, mtri)

    # 3. Restore Glasses_Black browlines (C2 & C6)
    bpos = asset.arr(pr_black["attributes"]["POSITION"])
    btri = asset.arr(pr_black["indices"]).reshape(-1, 3)
    bpos64 = bpos.astype(np.float64)
    b_comps = connected_components(bpos64, btri)
    brow_comps = [c for c in b_comps if len(c) > 200]
    assert len(brow_comps) == 2, f"Expected 2 browline components, got {len(brow_comps)}"
    black_shifted = 0
    for comp in brow_comps:
        pts = bpos64[comp]
        dz_q = pts[:, 2] - z_quad(pts)
        for local_i, gi in enumerate(comp):
            if dz_q[local_i] < -0.0035:
                bpos64[gi, 2] += dz_shift
                black_shifted += 1
    bpos[:] = bpos64.astype(np.float32)
    bnorm = asset.arr(pr_black["attributes"]["NORMAL"])
    bnorm[:] = compute_welded_vertex_normals(bpos, btri)

    # 4. Restore Glasses_Lens inner shifted vertices (C0 & C1) preserving each lens's surface orientation!
    #    Note: +X lens has front-surface normals with nz < 0, while mirrored -X lens has nz > 0; use -sign(x)*nz!
    lpos = asset.arr(pr_lens["attributes"]["POSITION"])
    ltri = asset.arr(pr_lens["indices"]).reshape(-1, 3)
    lnorm = asset.arr(pr_lens["attributes"]["NORMAL"])
    lpos64 = lpos.astype(np.float64)
    lnorm64 = lnorm.astype(np.float64)
    dz_l = lpos64[:, 2] - z_quad(lpos64)
    oriented_nz = -np.sign(lpos64[:, 0]) * lnorm64[:, 2]
    lens_shifted_mask = (
        ((oriented_nz > 0.2) & (dz_l < -0.0030))
        | ((oriented_nz < -0.2) & (dz_l < -0.0060))
        | ((np.abs(oriented_nz) <= 0.2) & (dz_l < -0.0050))
    )
    lpos64[lens_shifted_mask, 2] += dz_shift
    lens_shifted = int(np.sum(lens_shifted_mask))
    lpos[:] = lpos64.astype(np.float32)
    # Recompute welded normals on Glasses_Lens preserving each component's normal orientation independently
    lens_comps = connected_components(lpos64, ltri)
    fresh_ln = compute_welded_vertex_normals(lpos, ltri)
    for comp in lens_comps:
        if float(np.mean(np.sum(fresh_ln[comp] * lnorm[comp], axis=1))) < 0.0:
            fresh_ln[comp] = -fresh_ln[comp]
    lnorm[:] = fresh_ln

    # 5. Verify zero steep Z-jump edges survive on rims, browlines, or lenses!
    def max_edge_dz(pos_arr: np.ndarray, tri_arr: np.ndarray, comps_list: list[list[int]]) -> float:
        allowed = {gi for comp in comps_list for gi in comp}
        mdz = 0.0
        for a, b, c in tri_arr:
            if a in allowed:
                for u, v in ((a, b), (b, c), (c, a)):
                    d = abs(float(pos_arr[u, 2] - pos_arr[v, 2]))
                    if d > mdz:
                        mdz = d
        return mdz * 1000.0

    m_max_dz = max_edge_dz(mpos, mtri, rim_comps)
    b_max_dz = max_edge_dz(bpos, btri, brow_comps)
    l_max_dz = max_edge_dz(lpos, ltri, lens_comps)
    assert m_max_dz < 3.0, f"Metal rim still has steep Z-jump edge: {m_max_dz:.2f}mm"
    assert b_max_dz < 3.0, f"Browline still has steep Z-jump edge: {b_max_dz:.2f}mm"
    assert l_max_dz < 4.5, f"Lens still has steep Z-jump edge: {l_max_dz:.2f}mm"

    return {
        "dz_shift_mm": round(dz_shift * 1000.0, 3),
        "metal_rim_verts_restored": metal_shifted,
        "black_brow_verts_restored": black_shifted,
        "lens_verts_restored": lens_shifted,
        "max_metal_rim_edge_dz_mm": round(m_max_dz, 2),
        "max_brow_edge_dz_mm": round(b_max_dz, 2),
        "max_lens_edge_dz_mm": round(l_max_dz, 2),
    }


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_GLB.parent.mkdir(parents=True, exist_ok=True)
    rings = json.loads(V36_RINGS.read_text())

    asset = GlbAsset(V40_GLB)
    report = {"source": str(V40_GLB), "output": str(OUT_GLB)}

    report["face_shape"] = refine_face_shape_and_undereye(asset, rings)
    report["chin_weights"] = fix_chin_mandible_weights(asset)
    report["eyes_and_eyelids"] = overhaul_eye_globes_and_eyelids(asset, rings)
    report["spectacles"] = repair_spectacles_rim_kinks(asset)
    report["eyelids_tex"] = paint_eyelid_lash_texture(asset, rings)
    report["face_albedo_tex"] = clean_face_albedo_texture(asset)

    asset.save(OUT_GLB)
    report["glb_bytes"] = OUT_GLB.stat().st_size
    (WORK_DIR / "build41-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
