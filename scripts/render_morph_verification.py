"""
Facial Morph Targets & Blendshape Verification Renderer for `zachary_character.glb`.

Implements Law 8 (Soft Falloff & Anti-Muzzle), Law 9 (Strict Clearance & Zero Intersection),
and Law 18 (Test the Exported Artifact) directly on the exported production GLB.
Renders an 8-panel contact sheet auditing each blendshape at 1.0 weight:
1. Neutral Pose
2. Bilateral Smile (mouthSmileLeft: 1.0, mouthSmileRight: 1.0)
3. Mouth Open (mouthOpen: 1.0)
4. Jaw Open (jawOpen: 1.0)
5. Bilateral Blink (eyeBlinkLeft: 1.0, eyeBlinkRight: 1.0)
6. Brow Inner Up (browInnerUp: 1.0)
7. Viseme AA (viseme_aa: 1.0)
8. Keynote Expression (mouthSmileLeft: 0.7, mouthSmileRight: 0.7, browInnerUp: 0.8, eyeBlinkLeft: 0.2)
"""

from __future__ import annotations

import io
import json
import math
import os
import struct
import sys
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


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


def load_gltf_with_morphs(glb_path: str):
    with open(glb_path, "rb") as f:
        raw = f.read()
    c0_len, = struct.unpack_from("<I", raw, 12)
    gltf = json.loads(raw[20 : 20 + c0_len].decode("utf-8"))
    c1_off = 20 + c0_len
    c1_len, = struct.unpack_from("<I", raw, c1_off)
    bin_data = raw[c1_off + 8 : c1_off + 8 + c1_len]

    img_bv = gltf["bufferViews"][gltf["images"][0]["bufferView"]]
    img_off = img_bv.get("byteOffset", 0)
    webp_bytes = bytes(bin_data[img_off : img_off + img_bv["byteLength"]])
    tex_img = Image.open(io.BytesIO(webp_bytes)).convert("RGB")
    tex_arr = np.asarray(tex_img, dtype=np.float32) / 255.0

    target_names: list[str] = []
    face_mesh = next(m for m in gltf["meshes"] if m["name"] == "SM_Character_Face")
    target_names = face_mesh.get("extras", {}).get("targetNames", [])

    drawables: list[dict[str, Any]] = []
    morph_deltas: list[np.ndarray] = []

    for m in gltf["meshes"]:
        m_name = m["name"]
        for p_i, prim in enumerate(m["primitives"]):
            pos = _read_accessor(gltf, bin_data, prim["attributes"]["POSITION"]).astype(np.float32).copy()
            nrm = _read_accessor(gltf, bin_data, prim["attributes"]["NORMAL"]).astype(np.float32).copy()
            idx = _read_accessor(gltf, bin_data, prim["indices"]).astype(np.int32).reshape(-1, 3)
            uv = None
            if "TEXCOORD_0" in prim["attributes"]:
                uv = _read_accessor(gltf, bin_data, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
            if m_name == "Sovereign_Titanium_Spectacles":
                pos[:, 1] += 1.5400

            prim_morphs = []
            if "targets" in prim:
                for tgt in prim["targets"]:
                    if "POSITION" in tgt:
                        d_pos = _read_accessor(gltf, bin_data, tgt["POSITION"]).astype(np.float32)
                        prim_morphs.append(d_pos)

            drawables.append(
                {
                    "name": m_name,
                    "prim_idx": p_i,
                    "base_pos": pos.copy(),
                    "pos": pos,
                    "nrm": nrm,
                    "uv": uv,
                    "tris": idx,
                    "material": prim.get("material", 0),
                    "morph_targets": prim_morphs,
                }
            )

    return gltf, drawables, tex_arr, target_names


def apply_morph_weights(drawables: list[dict[str, Any]], target_names: list[str], weights: dict[str, float]):
    for d in drawables:
        if not d["morph_targets"]:
            d["pos"] = d["base_pos"].copy()
            continue
        accum = d["base_pos"].copy()
        for idx, t_name in enumerate(target_names):
            w = weights.get(t_name, 0.0)
            if w > 0.0 and idx < len(d["morph_targets"]):
                accum += d["morph_targets"][idx] * w
        d["pos"] = accum


def render_bust(
    drawables: list[dict[str, Any]],
    tex_arr: np.ndarray,
    yaw_deg: float = 0.0,
    pitch_deg: float = 0.0,
    width: int = 512,
    height: int = 512,
    title: str = "",
) -> Image.Image:
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    rot = np.array(
        [
            [cy, 0.0, -sy],
            [sp * sy, cp, sp * cy],
            [cp * sy, -sp, cp * cy],
        ],
        dtype=np.float32,
    )

    zbuf = np.full((height, width), -1e9, dtype=np.float32)
    fbuf = np.full((height, width, 3), 0.08, dtype=np.float32)
    yy = np.linspace(0.12, 0.05, height, dtype=np.float32)[:, None]
    fbuf[:, :, 0] = yy * 0.95
    fbuf[:, :, 1] = yy * 1.00
    fbuf[:, :, 2] = yy * 1.10

    center = (0.0, 1.575, 0.055)
    span_y = 0.280
    scale = height / span_y
    cx_w, cy_w, cz_w = center
    tex_h, tex_w, _ = tex_arr.shape

    light_key = np.array([0.40, 0.45, 0.79], dtype=np.float32)
    light_key /= np.linalg.norm(light_key)
    light_fill = np.array([-0.50, 0.25, 0.82], dtype=np.float32)
    light_fill /= np.linalg.norm(light_fill)

    for d in drawables:
        # Only render head, face, hair, hoodie collar, and glasses for bust
        if d["name"] in ("SM_Character_Hands", "SM_Cloth_Trousers", "SM_Cloth_Footwear"):
            continue

        pos_c = d["pos"] - np.array([cx_w, cy_w, cz_w], dtype=np.float32)
        p_cam = pos_c @ rot.T
        n_cam = d["nrm"] @ rot.T

        sx = (p_cam[:, 0] * scale + width * 0.5).astype(np.float32)
        sy_scr = (height * 0.5 - p_cam[:, 1] * scale).astype(np.float32)
        sz = p_cam[:, 2]

        tris = d["tris"]
        uv = d["uv"]
        mat_id = d["material"]

        for t in tris:
            i0, i1, i2 = int(t[0]), int(t[1]), int(t[2])
            x0, y0, z0 = float(sx[i0]), float(sy_scr[i0]), float(sz[i0])
            x1, y1, z1 = float(sx[i1]), float(sy_scr[i1]), float(sz[i1])
            x2, y2, z2 = float(sx[i2]), float(sy_scr[i2]), float(sz[i2])

            min_x = max(0, int(math.floor(min(x0, x1, x2))))
            max_x = min(width - 1, int(math.ceil(max(x0, x1, x2))))
            min_y = max(0, int(math.floor(min(y0, y1, y2))))
            max_y = min(height - 1, int(math.ceil(max(y0, y1, y2))))
            if min_x > max_x or min_y > max_y:
                continue

            denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(denom) < 1e-5:
                continue

            v01_c = p_cam[i1] - p_cam[i0]
            v02_c = p_cam[i2] - p_cam[i0]
            fn_z = float(v01_c[0] * v02_c[1] - v01_c[1] * v02_c[0])
            if fn_z <= 0.0 and mat_id != 8:
                continue

            n_tri = (n_cam[i0] + n_cam[i1] + n_cam[i2]) / 3.0
            n_len = float(np.linalg.norm(n_tri))
            if n_len > 1e-6:
                n_tri /= n_len
            if n_tri[2] < 0.0:
                n_tri = -n_tri

            ndotl_k = max(0.0, float(np.dot(n_tri, light_key)))
            ndotl_f = max(0.0, float(np.dot(n_tri, light_fill)))
            shade = 0.52 + 0.42 * ndotl_k + 0.16 * ndotl_f
            spec = 0.14 * (max(0.0, float(n_tri[2])) ** 16) if mat_id in (0, 1, 6) else 0.0

            inv_d = 1.0 / denom
            py_grid, px_grid = np.mgrid[min_y : max_y + 1, min_x : max_x + 1]
            px = px_grid.astype(np.float32) + 0.5
            py = py_grid.astype(np.float32) + 0.5

            w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) * inv_d
            w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) * inv_d
            w2 = 1.0 - w0 - w1

            inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
            if not np.any(inside):
                continue

            z_pix = w0 * z0 + w1 * z1 + w2 * z2
            sub_z = zbuf[min_y : max_y + 1, min_x : max_x + 1]
            vis = inside & (z_pix >= sub_z)
            if np.any(vis):
                if uv is not None:
                    u_pix = w0 * float(uv[i0, 0]) + w1 * float(uv[i1, 0]) + w2 * float(uv[i2, 0])
                    v_pix = w0 * float(uv[i0, 1]) + w1 * float(uv[i1, 1]) + w2 * float(uv[i2, 1])
                    tx_arr = np.clip((u_pix[vis] * (tex_w - 1)).astype(np.int32), 0, tex_w - 1)
                    ty_arr = np.clip((v_pix[vis] * (tex_h - 1)).astype(np.int32), 0, tex_h - 1)
                    base_cols = tex_arr[ty_arr, tx_arr]
                    cols = np.clip(base_cols * shade + spec, 0.0, 1.0)
                elif mat_id == 6:
                    cols = np.clip(np.array([0.72, 0.76, 0.82], dtype=np.float32) * shade + spec, 0.0, 1.0)
                elif mat_id == 7:
                    cols = np.clip(np.array([0.14, 0.14, 0.16], dtype=np.float32) * shade + spec, 0.0, 1.0)
                else:
                    cols = np.clip(np.array([0.85, 0.93, 0.98], dtype=np.float32) * shade + spec, 0.0, 1.0)

                sub_f = fbuf[min_y : max_y + 1, min_x : max_x + 1]
                if mat_id == 8:
                    sub_f[vis] = sub_f[vis] * 0.88 + cols * 0.12
                else:
                    sub_z[vis] = z_pix[vis]
                    sub_f[vis] = cols

    img = Image.fromarray(np.clip(fbuf * 255.0, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)
    if title:
        draw.rectangle([(8, 8), (width - 8, 34)], fill=(12, 16, 24))
        draw.text((14, 13), title, fill=(235, 242, 255))
    return img


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    glb_path = os.path.join(root, "public", "models", "zachary_character.glb")
    out_dir = os.path.join(root, "screenshots")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "zachary_facial_morphs_qa_sheet.png")

    print(f"Loading GLB: {glb_path}")
    gltf, drawables, tex_arr, target_names = load_gltf_with_morphs(glb_path)
    print(f"Morph target names: {target_names}")

    test_cases = [
        ("1. Neutral Baseline", {}),
        ("2. Bilateral Smile (Left & Right 1.0)", {"mouthSmileLeft": 1.0, "mouthSmileRight": 1.0}),
        ("3. Mouth Open (1.0)", {"mouthOpen": 1.0}),
        ("4. Jaw Open (1.0)", {"jawOpen": 1.0}),
        ("5. Bilateral Blink (Left & Right 1.0)", {"eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0}),
        ("6. Brow Inner Up (1.0)", {"browInnerUp": 1.0}),
        ("7. Viseme AA (Speech 1.0)", {"viseme_aa": 1.0}),
        ("8. Expressive Keynote (Smile 0.7 + Brow 0.8)", {"mouthSmileLeft": 0.7, "mouthSmileRight": 0.7, "browInnerUp": 0.8}),
    ]

    p_w, p_h = 440, 440
    cols, rows = 4, 2
    sheet = Image.new("RGB", (cols * p_w, rows * p_h), (8, 10, 14))

    for idx, (title, weights) in enumerate(test_cases):
        print(f"Rendering panel {idx + 1}/8: {title}")
        apply_morph_weights(drawables, target_names, weights)
        panel = render_bust(drawables, tex_arr, yaw_deg=10.0, pitch_deg=-2.0, width=p_w, height=p_h, title=title)
        c = idx % cols
        r = idx // cols
        sheet.paste(panel, (c * p_w, r * p_h))

    sheet.save(out_path, format="PNG")
    print(f"[Morph QA Contact Sheet] Saved 8-panel facial expression sheet to: {out_path}")


if __name__ == "__main__":
    main()
