"""Generate native 1024-resolution 3D Pixar-Anime HD bust (hd_bust_v4_anime.glb) from the
user-approved 02_hd_bust_glasses_off.png via official microsoft/TRELLIS.2 Space (primary zero-CCU)
with clean RGBA cutout export for Google Colab L4 TRELLIS.2-4B fallback.
"""

from __future__ import annotations

import argparse
from collections import deque
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any

import numpy as np
from gradio_client import Client, handle_file
from huggingface_hub import get_token
from PIL import Image, ImageFilter

PROJECT_ROOT = Path(r"d:\omni-workstation\projects\ZacharyPortfolio")
V4_DIR = PROJECT_ROOT / "artifacts" / "companion-v4-anime"
BUST_INPUT = V4_DIR / "02_hd_bust_glasses_off.png"
BUST_RGBA = V4_DIR / "02_hd_bust_glasses_off_rgba.png"
OUT_GLB = V4_DIR / "hd_bust_v4_anime.glb"


def build_clean_rgba_cutout(src_path: Path, dst_rgba_path: Path) -> Path:
    """Flood-fill background cutout from corners without touching interior white crew tee or eyes."""
    img = Image.open(src_path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    h, w, _ = arr.shape

    # Sample top-left & top-right corner studio backdrop color (#e4e6eb)
    corners = np.concatenate(
        [
            arr[0:12, 0:12].reshape(-1, 3),
            arr[0:12, w - 12 : w].reshape(-1, 3),
        ],
        axis=0,
    )
    bg_rgb = np.median(corners, axis=0)
    dist = np.linalg.norm(arr - bg_rgb[None, None, :], axis=2)

    is_bg_cand = dist < 0.085
    visited = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()

    for x in range(w):
        for y in (0, h - 1):
            if is_bg_cand[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg_cand[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))

    while q:
        cy, cx = q.popleft()
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and is_bg_cand[ny, nx]:
                visited[ny, nx] = True
                q.append((ny, nx))

    alpha = (~visited).astype(np.float32) * 255.0
    alpha_img = Image.fromarray(alpha.astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=0.8))
    alpha_arr = np.asarray(alpha_img, dtype=np.uint8)
    rgba = np.dstack([(arr * 255.0 + 0.5).clip(0, 255).astype(np.uint8), alpha_arr])
    Image.fromarray(rgba, mode="RGBA").save(dst_rgba_path, format="PNG")
    print(f"Saved clean RGBA bust cutout: {dst_rgba_path} (fg frac={float((~visited).mean()):.3f})")
    return dst_rgba_path


def find_file_with_ext(obj: Any, exts: tuple[str, ...], reverse: bool = True) -> Path | None:
    if isinstance(obj, str):
        p = Path(obj)
        if p.suffix.lower() in exts and p.exists():
            return p
    elif isinstance(obj, dict):
        for k in ("value", "path", "name", "url"):
            if k in obj:
                found = find_file_with_ext(obj[k], exts, reverse=reverse)
                if found is not None:
                    return found
        for v in obj.values():
            found = find_file_with_ext(v, exts, reverse=reverse)
            if found is not None:
                return found
    elif isinstance(obj, (list, tuple)):
        seq = reversed(obj) if reverse else obj
        for item in seq:
            found = find_file_with_ext(item, exts, reverse=reverse)
            if found is not None:
                return found
    return None


def run_trellis2_space(image_path: Path, out_glb: Path, resolution: str = "1024", seed: int = 42) -> bool:
    print(f"\n>>> [HF Space microsoft/TRELLIS.2] Generating v4 Pixar-Anime HD bust (res={resolution}, seed={seed}) ...", flush=True)
    client = Client("microsoft/TRELLIS.2", token=get_token())
    client.predict(api_name="/start_session")

    pre = client.predict(input=handle_file(str(image_path)), api_name="/preprocess_image")
    pre_path = find_file_with_ext(pre, (".png", ".webp", ".jpg"), reverse=False)
    print(f"  Preprocessed image: {pre_path}", flush=True)
    if pre_path:
        shutil.copy2(pre_path, V4_DIR / f"trellis2_preprocessed_{resolution}.png")
        img_handle = handle_file(str(pre_path))
    else:
        img_handle = handle_file(str(image_path))

    print("  Running /image_to_3d ...", flush=True)
    client.predict(
        image=img_handle,
        seed=seed,
        resolution=resolution,
        ss_guidance_strength=7.5,
        ss_guidance_rescale=0.7,
        ss_sampling_steps=16,
        ss_rescale_t=5.0,
        shape_slat_guidance_strength=7.5,
        shape_slat_guidance_rescale=0.5,
        shape_slat_sampling_steps=16,
        shape_slat_rescale_t=3.0,
        tex_slat_guidance_strength=1.5,
        tex_slat_guidance_rescale=0.0,
        tex_slat_sampling_steps=16,
        tex_slat_rescale_t=3.0,
        api_name="/image_to_3d",
    )

    print("  Running /extract_glb (decimation_target=150000, texture_size=2048) ...", flush=True)
    ex_res = client.predict(
        decimation_target=150000,
        texture_size=2048,
        api_name="/extract_glb",
    )
    glb = find_file_with_ext(ex_res, (".glb", ".gltf"), reverse=True)
    if glb is None:
        raise RuntimeError(f"TRELLIS.2 Space returned no GLB: {repr(ex_res)[:400]}")

    shutil.copy2(glb, out_glb)
    print(f"  SUCCESS: {out_glb} ({out_glb.stat().st_size} bytes)", flush=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", default="1024", choices=["512", "1024", "1536"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cutout-only", action="store_true")
    args = parser.parse_args()

    V4_DIR.mkdir(parents=True, exist_ok=True)
    if not BUST_INPUT.exists():
        raise FileNotFoundError(f"Missing v4 bust concept image: {BUST_INPUT}")

    rgba_path = build_clean_rgba_cutout(BUST_INPUT, BUST_RGBA)
    if args.cutout_only:
        return

    try:
        run_trellis2_space(rgba_path, OUT_GLB, resolution=args.resolution, seed=args.seed)
    except Exception as exc:
        print(f"  ERROR in microsoft/TRELLIS.2 Space: {exc}", flush=True)
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
