"""Call free Hugging Face Image-to-3D Spaces via local gradio_client to generate raw_companion.glb."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any

from gradio_client import Client, handle_file
from huggingface_hub import get_token

ARTIFACT_DIR = Path(
    r"d:\omni-workstation\projects\ZacharyPortfolio\artifacts\companion-v2-likeness"
)
MV_DIR = ARTIFACT_DIR / "multiview"
FRONT_IMG = MV_DIR / "01_front.png"
THREEQ_IMG = MV_DIR / "02_threequarter.png"
SIDE_IMG = MV_DIR / "03_side.png"
BACK_IMG = MV_DIR / "04_back.png"


def summarize_api(space_id: str, api_dict: dict[str, Any]) -> None:
    print(f"\n=== API Schema for {space_id} ===")
    for group in ("named_endpoints", "unnamed_endpoints"):
        eps = api_dict.get(group, {})
        if not eps:
            continue
        print(f"  [{group}]")
        for ep_name, ep_info in eps.items():
            params = [
                f"{p.get('parameter_name') or p.get('label')}:{p.get('type', {}).get('type', '?')}(def={repr(p.get('parameter_default'))})"
                for p in ep_info.get("parameters", [])
            ]
            rets = [
                f"{r.get('label') or r.get('component')}:{r.get('type', {}).get('type', '?')}"
                for r in ep_info.get("returns", [])
            ]
            print(f"    {ep_name}({', '.join(params)}) -> [{', '.join(rets)}]")


def find_glb_in_result(obj: Any) -> Path | None:
    """Recursively locate a returned .glb / .gltf file path from a Gradio predict output."""
    if isinstance(obj, str):
        p = Path(obj)
        if p.suffix.lower() in (".glb", ".gltf") and p.exists():
            return p
    elif isinstance(obj, dict):
        for key in ("value", "path", "name", "url"):
            if key in obj:
                found = find_glb_in_result(obj[key])
                if found is not None:
                    return found
        for v in obj.values():
            found = find_glb_in_result(v)
            if found is not None:
                return found
    elif isinstance(obj, (list, tuple)):
        # Search in reverse so endpoints returning (untextured_glb, textured_glb) prefer textured_glb
        for item in reversed(obj):
            found = find_glb_in_result(item)
            if found is not None:
                return found
    return None


def find_image_in_result(obj: Any) -> Any:
    """Locate an image file/handle returned from a preprocessing step."""
    if isinstance(obj, str) and Path(obj).exists():
        return obj
    if isinstance(obj, dict):
        for k in ("path", "value", "url"):
            if k in obj and isinstance(obj[k], str) and Path(obj[k]).exists():
                return obj[k]
    if isinstance(obj, (list, tuple)):
        for item in obj:
            found = find_image_in_result(item)
            if found is not None:
                return found
    return None


def build_kwargs(
    ep_info: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    for p in ep_info.get("parameters", []):
        pname = p.get("parameter_name")
        if not pname:
            continue
        if pname in overrides:
            kwargs[pname] = overrides[pname]
        elif p.get("parameter_has_default", False):
            kwargs[pname] = p.get("parameter_default")
    return kwargs


def make_client(space_id: str) -> Client:
    hf_token = get_token()
    print(f"  HF token loaded: {bool(hf_token)}")
    return Client(space_id, token=hf_token)


def try_trellis2(out_path: Path) -> bool:
    space_id = "microsoft/TRELLIS.2"
    print(f"\n>>> Connecting to {space_id} ...")
    client = make_client(space_id)
    api = client.view_api(return_format="dict")
    summarize_api(space_id, api)

    named = api.get("named_endpoints", {})
    if "/start_session" in named:
        try:
            client.predict(api_name="/start_session")
        except Exception as exc:
            print(f"  /start_session note: {exc}")

    # Preprocess image if available
    img_input: Any = handle_file(str(FRONT_IMG))
    pre_ep = named.get("/preprocess_image")
    if pre_ep:
        pre_params = [p.get("parameter_name") for p in pre_ep.get("parameters", []) if p.get("parameter_name")]
        pre_kwargs = build_kwargs(
            pre_ep,
            {pre_params[0]: handle_file(str(FRONT_IMG))} if pre_params else {},
        )
        print(f"  Calling /preprocess_image with keys={list(pre_kwargs.keys())} ...")
        pre_res = client.predict(api_name="/preprocess_image", **pre_kwargs)
        pre_img_path = find_image_in_result(pre_res)
        if pre_img_path:
            print(f"  Preprocessed image -> {pre_img_path}")
            img_input = handle_file(str(pre_img_path))

    # Main generation step (/image_to_3d or similar)
    gen_ep_name = None
    for candidate in ("/image_to_3d", "/generate_and_extract_glb", "/run", "/generate"):
        if candidate in named:
            gen_ep_name = candidate
            break
    if gen_ep_name is None:
        raise RuntimeError(f"Could not locate TRELLIS.2 generation endpoint in {list(named.keys())}")

    gen_ep = named[gen_ep_name]
    gen_overrides: dict[str, Any] = {}
    for p in gen_ep.get("parameters", []):
        pname = p.get("parameter_name") or ""
        ptype = (p.get("type") or {}).get("type", "")
        plabel = (p.get("label") or "").lower()
        if "image" in pname.lower() or "image" in plabel or p.get("component") == "Image":
            gen_overrides[pname] = img_input
        elif pname == "seed":
            gen_overrides[pname] = 42
        elif pname == "randomize_seed":
            gen_overrides[pname] = False
        elif pname == "resolution" or "resolution" in pname.lower():
            gen_overrides[pname] = "1024"

    gen_kwargs = build_kwargs(gen_ep, gen_overrides)
    print(f"  Calling {gen_ep_name} with keys={list(gen_kwargs.keys())} ...")
    gen_res = client.predict(api_name=gen_ep_name, **gen_kwargs)
    glb_path = find_glb_in_result(gen_res)

    if glb_path is None and "/extract_glb" in named:
        ex_ep = named["/extract_glb"]
        ex_overrides: dict[str, Any] = {}
        for p in ex_ep.get("parameters", []):
            pname = p.get("parameter_name") or ""
            if "decimation" in pname.lower():
                ex_overrides[pname] = 100000
            elif "texture_size" in pname.lower():
                ex_overrides[pname] = 2048
        ex_kwargs = build_kwargs(ex_ep, ex_overrides)
        print(f"  Calling /extract_glb with keys={list(ex_kwargs.keys())} ...")
        ex_res = client.predict(api_name="/extract_glb", **ex_kwargs)
        glb_path = find_glb_in_result(ex_res)

    if glb_path is None:
        raise RuntimeError(f"TRELLIS.2 finished without returning a .glb path (res={repr(gen_res)[:400]})")

    shutil.copy2(glb_path, out_path)
    print(f"  SUCCESS: Saved {out_path} ({out_path.stat().st_size} bytes)")
    return True


def try_hunyuan_space(space_id: str, out_path: Path, use_multiview: bool = False) -> bool:
    print(f"\n>>> Connecting to {space_id} ...")
    client = make_client(space_id)
    api = client.view_api(return_format="dict")
    summarize_api(space_id, api)

    named = api.get("named_endpoints", {})
    # Look for full textured generation endpoint first
    target_ep = None
    for candidate in ("/generation_all", "/gen_shape", "/generate", "/run", "/shape_generation"):
        if candidate in named:
            target_ep = candidate
            break
    if target_ep is None:
        # Pick first endpoint returning 3D model / file
        for ep_name, ep_info in named.items():
            rets_str = str(ep_info.get("returns", [])).lower()
            if "model3d" in rets_str or "glb" in rets_str or "file" in rets_str:
                target_ep = ep_name
                break
    if target_ep is None:
        raise RuntimeError(f"No 3D generation endpoint found in {space_id}: {list(named.keys())}")

    ep_info = named[target_ep]
    has_mv = any("mv_" in (p.get("parameter_name") or "").lower() for p in ep_info.get("parameters", []))
    overrides: dict[str, Any] = {}
    for p in ep_info.get("parameters", []):
        pname = p.get("parameter_name") or ""
        plabel = (p.get("label") or "").lower()
        low = pname.lower()
        if p.get("component") == "Image" or "image" in low or "image" in plabel:
            if use_multiview and has_mv:
                if "back" in low or "back" in plabel:
                    overrides[pname] = handle_file(str(BACK_IMG))
                elif "left" in low or "left" in plabel or "side" in low:
                    overrides[pname] = handle_file(str(SIDE_IMG))
                elif "front" in low or "front" in plabel:
                    overrides[pname] = handle_file(str(FRONT_IMG))
            elif "mv" not in low:
                overrides[pname] = handle_file(str(FRONT_IMG))
        elif low == "seed":
            overrides[pname] = 42
        elif low == "randomize_seed":
            overrides[pname] = False
        elif "gen_mode" in low:
            overrides[pname] = "Turbo" if "Turbo" in str(p) else p.get("parameter_default")

    print(f"  Calling {target_ep} with params={list(overrides.keys())} ...")
    kwargs = build_kwargs(ep_info, overrides)
    res = client.predict(api_name=target_ep, **kwargs)
    print(f"  Raw result: {repr(res)[:500]}")
    glb_path = find_glb_in_result(res)
    if glb_path is None and "/on_export_click" in named and isinstance(res, (list, tuple)) and len(res) >= 2:
        f0 = find_image_in_result(res[0])
        f1 = find_image_in_result(res[1])
        if f0 and f1:
            ex_ep = named["/on_export_click"]
            ex_kwargs = build_kwargs(
                ex_ep,
                {
                    "file_out": handle_file(str(f0)),
                    "file_out2": handle_file(str(f1)),
                    "file_type": "glb",
                    "export_texture": True,
                },
            )
            print("  Calling /on_export_click -> glb ...")
            ex_res = client.predict(api_name="/on_export_click", **ex_kwargs)
            glb_path = find_glb_in_result(ex_res)
    if glb_path is None:
        raise RuntimeError(f"{space_id} returned no .glb path: {repr(res)[:400]}")

    shutil.copy2(glb_path, out_path)
    print(f"  SUCCESS: Saved {out_path} ({out_path.stat().st_size} bytes)")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spaces",
        nargs="+",
        default=["trellis2", "hunyuan21", "hunyuan2"],
        choices=["trellis2", "hunyuan21", "hunyuan2mv", "hunyuan2"],
    )
    parser.add_argument(
        "--stop-on-first",
        action="store_true",
        help="Stop after first successful GLB download",
    )
    args = parser.parse_args()

    if not FRONT_IMG.exists():
        raise FileNotFoundError(f"Missing front view PNG: {FRONT_IMG}")

    winners: list[Path] = []
    for key in args.spaces:
        try:
            if key == "trellis2":
                out = ARTIFACT_DIR / "raw_trellis2.glb"
                if try_trellis2(out):
                    winners.append(out)
            elif key == "hunyuan21":
                out = ARTIFACT_DIR / "raw_hunyuan21.glb"
                if try_hunyuan_space("tencent/Hunyuan3D-2.1", out, use_multiview=False):
                    winners.append(out)
            elif key == "hunyuan2mv":
                out = ARTIFACT_DIR / "raw_hunyuan2mv.glb"
                if try_hunyuan_space("tencent/Hunyuan3D-2mv", out, use_multiview=True):
                    winners.append(out)
            elif key == "hunyuan2":
                out = ARTIFACT_DIR / "raw_hunyuan2.glb"
                if try_hunyuan_space("tencent/Hunyuan3D-2", out, use_multiview=False):
                    winners.append(out)
        except Exception as exc:
            print(f"  FAILED {key}: {exc}")
            traceback.print_exc()

        if args.stop_on_first and winners:
            break

    if not winners:
        print("\nALL SPACES FAILED — see logs above.")
        sys.exit(2)

    companion_dst = ARTIFACT_DIR / "raw_companion.glb"
    shutil.copy2(winners[0], companion_dst)
    print(f"\nPrimary raw_companion.glb copied from {winners[0].name} ({companion_dst.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
