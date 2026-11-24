"""Generate dedicated high-resolution 3D head/bust candidates from the approved 1024x1024
glasses-off closeup portrait via free Hugging Face Spaces (microsoft/TRELLIS.2 & tencent/Hunyuan3D-2.1).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any

from gradio_client import Client, handle_file
from huggingface_hub import get_token

PROJECT_ROOT = Path(r"d:\omni-workstation\projects\ZacharyPortfolio")
FACE_CLOSEUP = PROJECT_ROOT / "artifacts" / "companion-v2-likeness" / "zachary_face_closeup_glasses_off.png"
OUT_DIR = PROJECT_ROOT / "artifacts" / "companion-v3-face-refinement"


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


def run_trellis2(image_path: Path, out_glb: Path, resolution: str = "1024", seed: int = 42) -> bool:
    print(f"\n>>> [TRELLIS.2] Generating HD bust (res={resolution}, seed={seed}) from {image_path.name} ...")
    client = Client("microsoft/TRELLIS.2", token=get_token())
    client.predict(api_name="/start_session")

    pre = client.predict(input=handle_file(str(image_path)), api_name="/preprocess_image")
    pre_path = find_file_with_ext(pre, (".png", ".webp", ".jpg"), reverse=False)
    print(f"  Preprocessed image: {pre_path}")
    if pre_path:
        shutil.copy2(pre_path, OUT_DIR / f"trellis2_preprocessed_{resolution}.png")
        img_handle = handle_file(str(pre_path))
    else:
        img_handle = handle_file(str(image_path))

    print("  Running /image_to_3d ...")
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

    print("  Running /extract_glb (decimation_target=150000, texture_size=2048) ...")
    ex_res = client.predict(
        decimation_target=150000,
        texture_size=2048,
        api_name="/extract_glb",
    )
    glb = find_file_with_ext(ex_res, (".glb", ".gltf"), reverse=True)
    if glb is None:
        raise RuntimeError(f"TRELLIS.2 returned no GLB: {repr(ex_res)[:400]}")

    shutil.copy2(glb, out_glb)
    print(f"  SUCCESS: {out_glb} ({out_glb.stat().st_size} bytes)")
    return True


def run_hunyuan21(image_path: Path, out_glb: Path, octree_res: int = 384, seed: int = 42) -> bool:
    print(f"\n>>> [Hunyuan3D-2.1] Generating HD bust (octree={octree_res}, seed={seed}) from {image_path.name} ...")
    client = Client("tencent/Hunyuan3D-2.1", token=get_token())

    res = client.predict(
        image=handle_file(str(image_path)),
        mv_image_front=None,
        mv_image_back=None,
        mv_image_left=None,
        mv_image_right=None,
        steps=50,
        guidance_scale=5.5,
        seed=seed,
        octree_resolution=octree_res,
        check_box_rembg=True,
        num_chunks=8000,
        randomize_seed=False,
        api_name="/generation_all",
    )
    print(f"  Raw result: {repr(res)[:400]}")
    glb = find_file_with_ext(res, (".glb", ".gltf"), reverse=True)
    if glb is None and isinstance(res, (list, tuple)) and len(res) >= 2:
        f0 = find_file_with_ext(res[0], (".glb", ".obj", ".ply", ".stl"), reverse=False)
        f1 = find_file_with_ext(res[1], (".glb", ".obj", ".ply", ".stl"), reverse=False)
        if f0 and f1:
            print(f"  Calling /on_export_click ({f0.name}, {f1.name}) ...")
            ex_res = client.predict(
                file_out=handle_file(str(f0)),
                file_out2=handle_file(str(f1)),
                file_type="glb",
                reduce_face=False,
                export_texture=True,
                target_face_num=100000,
                api_name="/on_export_click",
            )
            glb = find_file_with_ext(ex_res, (".glb", ".gltf"), reverse=True)

    if glb is None:
        raise RuntimeError(f"Hunyuan3D-2.1 returned no GLB: {repr(res)[:400]}")

    shutil.copy2(glb, out_glb)
    print(f"  SUCCESS: {out_glb} ({out_glb.stat().st_size} bytes)")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engines", nargs="+", default=["trellis2", "hunyuan21"], choices=["trellis2", "hunyuan21"])
    parser.add_argument("--resolution", default="1024", choices=["512", "1024", "1536"])
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not FACE_CLOSEUP.exists():
        raise FileNotFoundError(f"Missing closeup image: {FACE_CLOSEUP}")

    ok = 0
    for eng in args.engines:
        try:
            if eng == "trellis2":
                out = OUT_DIR / f"hd_bust_trellis2_{args.resolution}_s{args.seed}.glb"
                if run_trellis2(FACE_CLOSEUP, out, resolution=args.resolution, seed=args.seed):
                    ok += 1
            elif eng == "hunyuan21":
                out = OUT_DIR / f"hd_bust_hunyuan21_s{args.seed}.glb"
                if run_hunyuan21(FACE_CLOSEUP, out, octree_res=384, seed=args.seed):
                    ok += 1
        except Exception as exc:
            print(f"  ERROR in {eng}: {exc}")
            traceback.print_exc()

    if ok == 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
