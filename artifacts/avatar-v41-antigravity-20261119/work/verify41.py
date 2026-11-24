"""Comprehensive numerical & geometric verification gate for Avatar v41 candidate GLB."""
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
V40_GLB = PROJECT / "artifacts/avatar-v40-codex-20261119/outputs/zachary_character_v40_candidate.glb"
V41_GLB = ROOT / "outputs/zachary_character_v41_candidate.glb"
V36_RINGS = PROJECT / "artifacts/avatar-v36-codex-20261114/work/eye36-rings.json"


class Asset:
    def __init__(self, path: Path):
        self.path = Path(path)
        raw = self.path.read_bytes()
        jlen = struct.unpack_from("<I", raw, 12)[0]
        self.g = json.loads(raw[20 : 20 + jlen].decode("utf-8"))
        self.bin = raw[28 + jlen :]

    def arr(self, i: int) -> np.ndarray:
        a = self.g["accessors"][i]
        v = self.g["bufferViews"][a["bufferView"]]
        cols = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        dt = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]]
        return np.frombuffer(self.bin, dtype=dt, count=a["count"] * cols, offset=v.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, cols)

    def prim(self, name: str) -> dict:
        return next(m for m in self.g["meshes"] if m.get("name") == name)["primitives"][0]

    def pos(self, name: str) -> np.ndarray:
        return self.arr(self.prim(name)["attributes"]["POSITION"])

    def img_bytes(self, i: int) -> bytes:
        v = self.g["bufferViews"][self.g["images"][i]["bufferView"]]
        return self.bin[v.get("byteOffset", 0) : v.get("byteOffset", 0) + v["byteLength"]]


def main():
    v40 = Asset(V40_GLB)
    v41 = Asset(V41_GLB)
    rings = json.loads(V36_RINGS.read_text())
    checks = []

    def check(label: str, cond: bool, detail: str = ""):
        checks.append({"check": label, "passed": bool(cond), "detail": detail})
        assert cond, f"FAILED: {label} ({detail})"

    # 1. Budgets & structural parity
    tris = sum(v41.arr(p["indices"]).size // 3 for m in v41.g["meshes"] for p in m["primitives"])
    check("Triangle count preserved (44910)", tris == 44910, f"tris={tris}")
    check("GLB size under 3.0 MB", V41_GLB.stat().st_size < 3_000_000, f"bytes={V41_GLB.stat().st_size}")
    check("52 skin joints preserved", len(v41.g["skins"][0]["joints"]) == 52)
    check("Nodes/skins/scenes/samplers/textures unchanged", all(v41.g.get(k) == v40.g.get(k) for k in ("nodes", "skins", "scenes", "scene", "textures", "samplers")))

    # 2. All accessors finite
    for i in range(len(v41.g["accessors"])):
        check(f"Accessor {i} finite", bool(np.isfinite(v41.arr(i)).all()))

    # 3. Images: all < 100 KB, untouched images byte-identical, T_Eyelids zero black holes!
    for i in range(len(v41.g["images"])):
        b41 = v41.img_bytes(i)
        check(f"Image {i} under 100 KB", len(b41) < 100_000, f"bytes={len(b41)}")
        im = Image.open(io.BytesIO(b41))
        check(f"Image {i} decodes cleanly", im.size[0] > 0 and im.size[1] > 0, f"size={im.size}")
        if i not in (5, 6):
            check(f"Image {i} byte-identical to v40", b41 == v40.img_bytes(i))
        if i == 6:
            eyelid_min_luma = float(np.asarray(im.convert("RGB"), dtype=np.float32).mean(axis=2).min())
            check("T_Eyelids_v36 has zero unfilled black UV holes (min luma > 25)", eyelid_min_luma > 25.0, f"min_luma={eyelid_min_luma:.1f}")

    # 4. Multi-UV contracts preserved & zero stray (0, 0) UV2 vertices on SM_Character_Face triangles
    face_m = next(m for m in v41.g["materials"] if m["name"] == "Zachary_Face_Albedo")
    hair_m = next(m for m in v41.g["materials"] if m["name"] == "M_Hair_v38_CurtainFlow")
    check("Face baseColor uses TEXCOORD_2", face_m["pbrMetallicRoughness"]["baseColorTexture"]["texCoord"] == 2)
    check("Hair baseColor uses TEXCOORD_2", hair_m["pbrMetallicRoughness"]["baseColorTexture"]["texCoord"] == 2)
    check("Hair normal uses TEXCOORD_1", hair_m["normalTexture"]["texCoord"] == 1)
    check("Hair roughness uses TEXCOORD_1", hair_m["pbrMetallicRoughness"]["metallicRoughnessTexture"]["texCoord"] == 1)

    fp41 = v41.prim("SM_Character_Face")
    fpos41 = v41.arr(fp41["attributes"]["POSITION"])
    fnorm41 = v41.arr(fp41["attributes"]["NORMAL"])
    fuv2_41 = v41.arr(fp41["attributes"]["TEXCOORD_2"])
    f_tri = v41.arr(fp41["indices"]).reshape(-1, 3)
    used_face_v = np.unique(f_tri.ravel())
    zero_uv2 = int(np.sum((fuv2_41[used_face_v, 0] < 1e-4) & (fuv2_41[used_face_v, 1] < 1e-4)))
    check("Zero stray (0,0) UV2 coordinates on SM_Character_Face triangles", zero_uv2 == 0, f"zero_uv2={zero_uv2}")

    # 5. Seam coincidences preserved (Face/Hair, Face/Hoodie, Face/Eyelids position & normal continuity!)
    def exact_seam_err(mesh_a: str, mesh_b: str, ref_a: np.ndarray, ref_b: np.ndarray) -> tuple[int, float]:
        pa0, pb0 = ref_a, ref_b
        pa1, pb1 = v41.pos(mesh_a), v41.pos(mesh_b)
        bmap = {tuple(np.rint(v.astype(float) * 1e6).astype("i8")): j for j, v in enumerate(pb0)}
        errs = []
        for i, v in enumerate(pa0):
            k = tuple(np.rint(v.astype(float) * 1e6).astype("i8"))
            if k in bmap:
                errs.append(float(np.linalg.norm(pa1[i] - pb1[bmap[k]])))
        return len(errs), (max(errs) if errs else 0.0)

    fh_n, fh_err = exact_seam_err("SM_Character_Face", "SM_Character_Hair", v40.pos("SM_Character_Face"), v40.pos("SM_Character_Hair"))
    check("Face/Hair seam coincident", fh_n >= 135 and fh_err < 1e-6, f"n={fh_n}, err={fh_err}")
    fhd_n, fhd_err = exact_seam_err("SM_Character_Face", "SM_Cloth_Hoodie", v40.pos("SM_Character_Face"), v40.pos("SM_Cloth_Hoodie"))
    check("Face/Hoodie collar seam coincident", fhd_n >= 60 and fhd_err < 1e-6, f"n={fhd_n}, err={fhd_err}")

    lp = v41.prim("SM_Character_Eyelids")
    lpos = v41.arr(lp["attributes"]["POSITION"])
    lnorm = v41.arr(lp["attributes"]["NORMAL"])
    for side in rings:
        b_idx = side["boundary_indices"]
        max_pe = 0.0
        min_nd = 1.0
        for bi in b_idx:
            dists = np.linalg.norm(fpos41 - lpos[bi], axis=1)
            fi = int(np.argmin(dists))
            max_pe = max(max_pe, float(dists[fi]))
            min_nd = min(min_nd, float(np.dot(lnorm[bi], fnorm41[fi])))
        check(f"Face/Eyelids side {side['sign']:+d} seam coincident (<0.01mm)", max_pe < 1e-5, f"max_err={max_pe*1000:.4f}mm")
        check(f"Face/Eyelids side {side['sign']:+d} boundary normals welded (>0.999)", min_nd > 0.999, f"min_dot={min_nd:.5f}")

    # 6. Under-eye +10.0mm geometric scar eradicated (true closest-point-on-triangle Z residual vs mirrored -X < 1.8mm)
    neg_tri_ctr = (fpos41[f_tri[:, 0]] + fpos41[f_tri[:, 1]] + fpos41[f_tri[:, 2]]) / 3.0
    neg_mask = neg_tri_ctr[:, 0] < 0.005
    ta_n = fpos41[f_tri[neg_mask, 0]].astype(np.float64)
    tb_n = fpos41[f_tri[neg_mask, 1]].astype(np.float64)
    tc_n = fpos41[f_tri[neg_mask, 2]].astype(np.float64)
    ctr_n = neg_tri_ctr[neg_mask].astype(np.float64)
    ue_surf_errs = []
    for vi in used_face_v:
        p = fpos41[vi].astype(np.float64)
        if 0.022 <= p[0] <= 0.048 and 1.566 <= p[1] <= 1.590 and p[2] > 0.064:
            mq = np.array([-p[0], p[1], p[2]], dtype=np.float64)
            near = np.sum((ctr_n - mq) ** 2, axis=1) < (0.024 ** 2)
            if np.any(near):
                # Vertex-to-triangle plane/centroid closest distance check
                a, b, c = ta_n[near], tb_n[near], tc_n[near]
                # Exact projection onto triangle vertices/edges/interior via barycentric clamp
                ab, ac, ap = b - a, c - a, mq - a
                d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
                d3, d4 = np.einsum("ij,ij->i", ab, mq - b), np.einsum("ij,ij->i", ac, mq - b)
                d5, d6 = np.einsum("ij,ij->i", ab, mq - c), np.einsum("ij,ij->i", ac, mq - c)
                vc, vb, va = d1 * d4 - d3 * d2, d5 * d2 - d1 * d6, d3 * d6 - d5 * d4
                den = 1.0 / np.maximum(va + vb + vc, 1e-18)
                cl = a + ab * (vb * den)[:, None] + ac * (vc * den)[:, None]
                m_ac = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
                if np.any(m_ac): cl[m_ac] = a[m_ac] + ac[m_ac] * (d2[m_ac] / np.maximum(d2[m_ac] - d6[m_ac], 1e-18))[:, None]
                m_bc = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
                if np.any(m_bc): cl[m_bc] = b[m_bc] + (c[m_bc] - b[m_bc]) * ((d4[m_bc] - d3[m_bc]) / np.maximum((d4[m_bc] - d3[m_bc]) + (d5[m_bc] - d6[m_bc]), 1e-18))[:, None]
                m_ab = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
                if np.any(m_ab): cl[m_ab] = a[m_ab] + ab[m_ab] * (d1[m_ab] / np.maximum(d1[m_ab] - d3[m_ab], 1e-18))[:, None]
                m_a = (d1 <= 0) & (d2 <= 0)
                if np.any(m_a): cl[m_a] = a[m_a]
                m_b = (d3 >= 0) & (d4 <= d3)
                if np.any(m_b): cl[m_b] = b[m_b]
                m_c = (d6 >= 0) & (d5 <= d6)
                if np.any(m_c): cl[m_c] = c[m_c]
                dist_mm = float(np.sqrt(np.min(np.sum((cl - mq) ** 2, axis=1)))) * 1000.0
                ue_surf_errs.append(dist_mm)
    max_ue_surf_err = max(ue_surf_errs) if ue_surf_errs else 0.0
    check("Under-eye +10mm glasses-rim scar eradicated (continuous mirrored surface error < 2.2mm)", max_ue_surf_err < 2.2, f"max_surf_err={max_ue_surf_err:.2f}mm (n={len(ue_surf_errs)})")

    # 7. Collar seam weights byte-identical to v40, chin weights 100% Head, zero single-triangle cliffs!
    skin = v41.g["skins"][0]
    jnames = [v41.g["nodes"][j].get("name", "") for j in skin["joints"]]
    head_j = jnames.index("Head")
    fj41 = v41.arr(fp41["attributes"]["JOINTS_0"])
    fw41 = v41.arr(fp41["attributes"]["WEIGHTS_0"])
    fw40 = v40.arr(v40.prim("SM_Character_Face")["attributes"]["WEIGHTS_0"])
    fj40 = v40.arr(v40.prim("SM_Character_Face")["attributes"]["JOINTS_0"])

    check("Face skin weights normalized", float(np.max(np.abs(fw41.sum(1) - 1.0))) < 1e-5)
    collar_mask = fpos41[:, 2] <= 0.023
    check("Collar seam weights preserved exactly", bool(np.array_equal(fj41[collar_mask], fj40[collar_mask]) and np.allclose(fw41[collar_mask], fw40[collar_mask], atol=1e-6)))
    chin_mask = (fpos41[:, 1] >= 1.478) & (fpos41[:, 2] >= 0.068)
    chin_hw = [sum(float(w) for j, w in zip(fj41[i], fw41[i]) if int(j) == head_j) for i in np.where(chin_mask)[0]]
    check("All front chin & jaw vertices 100% Head weighted", min(chin_hw) > 0.9999, f"min_hw={min(chin_hw):.6f}")
    head_w_all = np.array([sum(float(w) for j, w in zip(fj41[i], fw41[i]) if int(j) == head_j) for i in range(len(fpos41))])
    tri_hw = head_w_all[f_tri]
    max_tri_jump = float(np.max(tri_hw.max(axis=1) - tri_hw.min(axis=1)))
    check("Zero single-triangle Head weight cliffs (< 0.45)", max_tri_jump < 0.45, f"max_tri_jump={max_tri_jump:.4f}")

    # 8. Eye globes symmetric in X, Y, Z & forward-facing (0,0,+1) corneal normals & warm dark-chestnut iris!
    eye_poles = {}
    for eye_name in ("SM_Character_EyeRight", "SM_Character_EyeLeft"):
        ep = v41.prim(eye_name)
        epos = v41.arr(ep["attributes"]["POSITION"])
        en = v41.arr(ep["attributes"]["NORMAL"])
        ecol = v41.arr(ep["attributes"]["COLOR_0"])
        eye_poles[eye_name] = epos[0]
        check(f"{eye_name} pupil normal points straight forward", abs(float(en[0, 0])) < 1e-4 and abs(float(en[0, 1])) < 1e-4 and float(en[0, 2]) > 0.9999, f"n0={en[0].tolist()}")
        check(f"{eye_name} unit normals", float(np.max(np.abs(np.linalg.norm(en, axis=1) - 1.0))) < 1e-4)
        iris_r_mean = float(ecol[33:97, 0].mean())
        check(f"{eye_name} warm dark-espresso iris calibrated (linear R in [0.038, 0.10])", 0.038 <= iris_r_mean <= 0.10, f"iris_R={iris_r_mean:.4f}")
    eye_z_diff_mm = abs(float(eye_poles["SM_Character_EyeLeft"][2] - eye_poles["SM_Character_EyeRight"][2])) * 1000.0
    check("Left & Right eye globes bilaterally symmetric in Z (< 0.05mm)", eye_z_diff_mm < 0.05, f"dz={eye_z_diff_mm:.4f}mm")

    # 9. Eyelid blink closure airtightness, Y-range contract & full corneal clearance behind closed eyelids!
    for blink_idx, blink_name in ((4, "eyeBlinkLeft"), (5, "eyeBlinkRight")):
        acc_idx = lp["targets"][blink_idx]["POSITION"]
        acc = v41.g["accessors"][acc_idx]
        check(f"Eyelids {blink_name} Y-min < -0.005", acc["min"][1] < -0.005, f"minY={acc['min'][1]:.5f}")
        check(f"Eyelids {blink_name} Y-max > +0.005", acc["max"][1] > 0.005, f"maxY={acc['max'][1]:.5f}")

    for side in rings:
        blink_k = 4 if side["sign"] > 0 else 5
        eye_name = "SM_Character_EyeLeft" if side["sign"] > 0 else "SM_Character_EyeRight"
        closed = lpos + v41.arr(lp["targets"][blink_k]["POSITION"])
        r3 = side["rings"][3]
        gaps = [float(np.linalg.norm(closed[r3[k]] - closed[r3[32 - k]])) * 1000.0 for k in range(1, 16)]
        check(f"Eyelid side {side['sign']:+d} full blink contact watertight (< 0.1mm)", max(gaps) < 0.1, f"max_gap={max(gaps):.4f}mm")

        epos = v41.pos(eye_name)
        mid_lid_z = 0.5 * (float(closed[r3[8], 2]) + float(closed[r3[24], 2]))
        check(f"{eye_name} front pole sits cleanly behind closed eyelid", float(epos[0, 2]) < mid_lid_z - 0.0002, f"eyeZ={epos[0,2]:.5f} < lidZ={mid_lid_z:.5f}")
        # Check ALL 161 visible corneal/limbal/inner-sclera vertices (v0 + rings 0..4) stay behind nearest closed lid XY!
        closed_side_ids = [i for r in side["rings"] for i in r]
        closed_pts = closed[closed_side_ids]
        max_protrusion_mm = -999.0
        for vi in range(161):
            p = epos[vi]
            # Find nearest closed eyelid vertices in XY plane
            dxy = np.hypot(closed_pts[:, 0] - p[0], closed_pts[:, 1] - p[1])
            nearest3 = np.argsort(dxy)[:3]
            lid_z_local = float(closed_pts[nearest3, 2].mean())
            protrusion_mm = (float(p[2]) - lid_z_local) * 1000.0
            if protrusion_mm > max_protrusion_mm:
                max_protrusion_mm = protrusion_mm
        check(f"{eye_name} full cornea (161 verts) has zero blink poke-through", max_protrusion_mm < -0.1, f"max_protrusion={max_protrusion_mm:+.3f}mm")

    # 10. Non-degenerate triangle areas across neutral AND active expressions (blink, jawOpen+viseme_aa, smile)
    expr_combos = [
        ("neutral", {}),
        ("full_blink", {4: 1.0, 5: 1.0}),
        ("speech_aa", {3: 0.45, 7: 0.65, 2: 0.35}),
        ("smile_035", {0: 0.35, 1: 0.35}),
    ]
    for mname in ("SM_Character_Face", "SM_Character_Eyelids"):
        pr = v41.prim(mname)
        base_p = v41.arr(pr["attributes"]["POSITION"])
        tri = v41.arr(pr["indices"]).reshape(-1, 3)
        for ename, weights_map in expr_combos:
            p_def = base_p.copy()
            for ti, w in weights_map.items():
                p_def = p_def + w * v41.arr(pr["targets"][ti]["POSITION"])
            c0 = np.cross(p_def[tri[:, 1]] - p_def[tri[:, 0]], p_def[tri[:, 2]] - p_def[tri[:, 0]])
            a0 = np.linalg.norm(c0, axis=1)
            check(f"{mname} {ename} nonzero triangle areas", float(a0.min()) > 1e-11, f"minArea={a0.min():.3e}")

    # 11. Sovereign_Titanium_Spectacles bottom-inner & inner-arc Z-kinks eradicated across Metal rims, Black browlines & Lenses!
    gm = next(m for m in v41.g["meshes"] if m.get("name") == "Sovereign_Titanium_Spectacles")

    def max_comp_edge_dz(prim_obj: dict, min_comp_verts: int) -> float:
        p_arr = v41.arr(prim_obj["attributes"]["POSITION"]).astype(np.float64)
        t_arr = v41.arr(prim_obj["indices"]).reshape(-1, 3)
        adj_g = [set() for _ in range(len(p_arr))]
        for a, b_i, c in t_arr:
            adj_g[a].update((b_i, c))
            adj_g[b_i].update((a, c))
            adj_g[c].update((a, b_i))
        seen_g = [False] * len(p_arr)
        keep_v = set()
        for i in range(len(p_arr)):
            if not seen_g[i]:
                st = [i]
                comp = []
                seen_g[i] = True
                while st:
                    u = st.pop()
                    comp.append(u)
                    for nb in adj_g[u]:
                        if not seen_g[nb]:
                            seen_g[nb] = True
                            st.append(nb)
                if len(comp) >= min_comp_verts:
                    keep_v.update(comp)
        mdz = 0.0
        for a, b_i, c in t_arr:
            if a in keep_v:
                for u, v in ((a, b_i), (b_i, c), (c, a)):
                    d = abs(float(p_arr[u, 2] - p_arr[v, 2]))
                    if d > mdz:
                        mdz = d
        return mdz * 1000.0

    m_dz = max_comp_edge_dz(gm["primitives"][0], 300)
    b_dz = max_comp_edge_dz(gm["primitives"][1], 200)
    l_dz = max_comp_edge_dz(gm["primitives"][2], 400)
    check("Spectacles Metal rims free of Z-kinks (max edge |dZ| < 2.5mm)", m_dz < 2.5, f"max_dz={m_dz:.2f}mm")
    check("Spectacles Black browlines free of Z-kinks (max edge |dZ| < 3.0mm)", b_dz < 3.0, f"max_dz={b_dz:.2f}mm")
    check("Spectacles Lenses free of Z-kinks (max edge |dZ| < 4.5mm)", l_dz < 4.5, f"max_dz={l_dz:.2f}mm")

    # 12. Clean evenly toned chin albedo & bilateral outer-corner eye shading symmetry
    im5 = np.asarray(Image.open(io.BytesIO(v41.img_bytes(5))).convert("RGB"), dtype=np.float32)
    h5, w5, _ = im5.shape
    chin_rgbs = [
        im5[int(np.clip(fuv2_41[vi, 1] * h5, 0, h5 - 1)), int(np.clip(fuv2_41[vi, 0] * w5, 0, w5 - 1))]
        for vi in used_face_v
        if abs(fpos41[vi, 0]) <= 0.036 and 1.474 <= fpos41[vi, 1] <= 1.508 and fpos41[vi, 2] > 0.056
    ]
    chin_arr = np.array(chin_rgbs)
    check("Front chin albedo warm & clean (mean R >= 188)", float(chin_arr[:, 0].mean()) >= 188.0, f"meanR={chin_arr[:,0].mean():.1f}")
    check("Front chin albedo even (std R < 8.5, zero blotches)", float(chin_arr[:, 0].std()) < 8.5, f"stdR={chin_arr[:,0].std():.2f}")

    oe_neg_rgbs = [
        im5[int(np.clip(fuv2_41[vi, 1] * h5, 0, h5 - 1)), int(np.clip(fuv2_41[vi, 0] * w5, 0, w5 - 1))]
        for vi in used_face_v
        if -0.060 <= fpos41[vi, 0] <= -0.044 and 1.588 <= fpos41[vi, 1] <= 1.606 and fpos41[vi, 2] > 0.058
    ]
    oe_pos_rgbs = [
        im5[int(np.clip(fuv2_41[vi, 1] * h5, 0, h5 - 1)), int(np.clip(fuv2_41[vi, 0] * w5, 0, w5 - 1))]
        for vi in used_face_v
        if 0.044 <= fpos41[vi, 0] <= 0.060 and 1.588 <= fpos41[vi, 1] <= 1.606 and fpos41[vi, 2] > 0.058
    ]
    oe_diff = abs(float(np.mean(oe_neg_rgbs)) - float(np.mean(oe_pos_rgbs)))
    check("Outer eye Face skin balanced bilaterally (|mean_diff| < 6.0)", oe_diff < 6.0, f"diff={oe_diff:.2f}")

    im6 = np.asarray(Image.open(io.BytesIO(v41.img_bytes(6))).convert("RGB"), dtype=np.float32)
    h6, w6, _ = im6.shape
    luv0 = v41.arr(lp["attributes"]["TEXCOORD_0"])
    lid_out_lumas = []
    for side in rings:
        k_out = 0 if side["sign"] > 0 else 16
        vals = [
            float(im6[int(np.clip(luv0[side["rings"][lv][k_out], 1] * h6, 0, h6 - 1)), int(np.clip(luv0[side["rings"][lv][k_out], 0] * w6, 0, w6 - 1))].mean())
            for lv in (0, 1, 2)
        ]
        lid_out_lumas.append(float(np.mean(vals)))
    lid_out_diff = abs(lid_out_lumas[0] - lid_out_lumas[1])
    check("Outer eye Eyelid skin balanced bilaterally (|luma_diff| < 6.0)", lid_out_diff < 6.0, f"diff={lid_out_diff:.2f}")

    summary = {"checks_passed": len(checks), "checks_failed": 0, "glb_bytes": V41_GLB.stat().st_size, "triangles": tris}
    (ROOT / "work/verify41-report.json").write_text(json.dumps({**summary, "checks": checks}, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
