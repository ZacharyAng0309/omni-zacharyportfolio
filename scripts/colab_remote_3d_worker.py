#!/usr/bin/env python3
"""
Remote Google Colab GPU Worker for ZacharyPortfolio 3D Asset & Companion v3 Pipeline.

Runs INSIDE a provisioned Google Colab VM (T4 / L4 / A100) via `colab_generate_3d.py`
or `colab-mcp`. Produces deterministic staging artifacts (`raw_output.glb` +
`manifest.json`) ready to be pulled into `projects/ZacharyPortfolio/artifacts/` and
fed into Blender 5.2 (`rig_likeness_companion.py` / prop bakes).

Supported modes:
- `smoke`: Verifies CUDA GPU, VRAM, PyTorch, disk space, and Drive cache without heavy downloads.
- `trellis2`: Runs official `microsoft/TRELLIS.2-4B` with O-Voxel PBR `.glb` export.
- `hunyuan3d-mv`: Runs `tencent/Hunyuan3D-2mv` (or single-view `Hunyuan3D-2`) with optional side/back views.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


def run_cmd(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"[worker] $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check, text=True)


def configure_cache_dirs(drive_cache_dir: str | None) -> dict[str, str]:
    cache_root = Path(drive_cache_dir) if drive_cache_dir and Path(drive_cache_dir).parent.exists() else Path("/content/omni_cache")
    cache_root.mkdir(parents=True, exist_ok=True)
    hf_home = cache_root / "huggingface"
    torch_home = cache_root / "torch"
    hf_home.mkdir(parents=True, exist_ok=True)
    torch_home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_home)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(hf_home / "hub")
    os.environ["TORCH_HOME"] = str(torch_home)
    return {
        "cache_root": str(cache_root),
        "hf_home": str(hf_home),
        "torch_home": str(torch_home),
    }


def collect_hardware_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cuda_available": False,
        "gpu_name": None,
        "vram_gb": 0.0,
        "disk_free_gb": round(shutil.disk_usage("/content").free / (1024**3), 2) if Path("/content").exists() else 0.0,
    }
    try:
        import torch  # type: ignore

        info["torch_version"] = torch.__version__
        info["cuda_version"] = torch.version.cuda
        info["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info["gpu_name"] = props.name
            info["vram_gb"] = round(props.total_memory / (1024**3), 2)
    except Exception as exc:
        info["torch_error"] = str(exc)
    return info


def inspect_glb_metrics(glb_path: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "path": str(glb_path),
        "bytes": glb_path.stat().st_size if glb_path.exists() else 0,
    }
    try:
        import trimesh  # type: ignore

        loaded = trimesh.load(str(glb_path), force="scene")
        geoms = list(loaded.geometry.values()) if hasattr(loaded, "geometry") else [loaded]
        total_verts = sum(int(len(g.vertices)) for g in geoms if hasattr(g, "vertices"))
        total_faces = sum(int(len(g.faces)) for g in geoms if hasattr(g, "faces"))
        bounds = loaded.bounds.tolist() if getattr(loaded, "bounds", None) is not None else None
        metrics.update(
            {
                "mesh_count": len(geoms),
                "vertices": total_verts,
                "triangles": total_faces,
                "bounds_min_max": bounds,
            }
        )
    except Exception as exc:
        metrics["trimesh_inspect_note"] = str(exc)
    return metrics


def ensure_trellis2_installed(repo_dir: Path) -> None:
    if not repo_dir.exists():
        run_cmd(["git", "clone", "--recursive", "https://github.com/microsoft/TRELLIS.2.git", str(repo_dir)])
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))
    try:
        import trellis2  # type: ignore  # noqa: F401
        import o_voxel  # type: ignore  # noqa: F401
        print("[worker] TRELLIS.2 and o_voxel already importable.", flush=True)
        return
    except ImportError:
        pass

    setup_script = repo_dir / "setup.sh"
    if setup_script.exists():
        run_cmd(
            ["bash", str(setup_script), "--basic", "--flash-attn", "--nvdiffrast", "--nvdiffrec", "--cumesh", "--o-voxel", "--flexgemm"],
            cwd=repo_dir,
        )
    else:
        run_cmd([sys.executable, "-m", "pip", "install", "-q", "trimesh", "pillow", "imageio", "opencv-python-headless", "huggingface_hub"])


def run_trellis2(args: argparse.Namespace, hw: dict[str, Any]) -> dict[str, Any]:
    if not hw.get("cuda_available"):
        raise RuntimeError("TRELLIS.2 requires a CUDA GPU (L4 >= 24GB or A100). Provision with --gpu L4 or --gpu A100.")
    if float(hw.get("vram_gb", 0.0)) < 20.0:
        print(
            f"[worker] WARNING: Detected {hw.get('vram_gb')} GB VRAM ({hw.get('gpu_name')}). "
            "TRELLIS.2-4B officially targets >= 24 GB VRAM (L4/A100); OOM risk on T4.",
            flush=True,
        )

    repo_dir = Path("/content/TRELLIS.2")
    ensure_trellis2_installed(repo_dir)

    import torch  # type: ignore
    from PIL import Image  # type: ignore
    from trellis2.pipelines import Trellis2ImageTo3DPipeline  # type: ignore
    import o_voxel  # type: ignore

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Missing uploaded input image: {input_path}")

    t0 = time.time()
    print("[worker] Loading microsoft/TRELLIS.2-4B pipeline...", flush=True)
    pipeline = Trellis2ImageTo3DPipeline.from_pretrained("microsoft/TRELLIS.2-4B")
    pipeline.cuda()

    image = Image.open(input_path).convert("RGBA")
    print(f"[worker] Running TRELLIS.2 inference (seed={args.seed}, pipeline_type={args.resolution})...", flush=True)

    run_kwargs: dict[str, Any] = {"seed": args.seed}
    if args.resolution in ("512", "1024", "1024_cascade", "1536_cascade"):
        run_kwargs["pipeline_type"] = args.resolution

    try:
        mesh = pipeline.run(image, **run_kwargs)[0]
    except TypeError:
        # Fallback if upstream signature omits pipeline_type on a given commit
        mesh = pipeline.run(image, seed=args.seed)[0]

    mesh.simplify(16777216)

    print(
        f"[worker] Exporting O-Voxel PBR GLB (decimation={args.decimation}, texture_size={args.texture_size})...",
        flush=True,
    )
    glb = o_voxel.postprocess.to_glb(
        vertices=mesh.vertices,
        faces=mesh.faces,
        attr_volume=mesh.attrs,
        coords=mesh.coords,
        attr_layout=mesh.layout,
        voxel_size=mesh.voxel_size,
        aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        decimation_target=args.decimation,
        texture_size=args.texture_size,
        remesh=True,
    )

    out_glb = Path(args.output)
    out_glb.parent.mkdir(parents=True, exist_ok=True)
    glb.export(str(out_glb))

    elapsed = round(time.time() - t0, 2)
    peak_vram = round(torch.cuda.max_memory_allocated() / (1024**3), 2)
    return {
        "engine": "microsoft/TRELLIS.2-4B",
        "seed": args.seed,
        "resolution": args.resolution,
        "decimation_target": args.decimation,
        "texture_size": args.texture_size,
        "elapsed_seconds": elapsed,
        "peak_vram_gb": peak_vram,
        "glb": inspect_glb_metrics(out_glb),
    }


def run_hunyuan3d(args: argparse.Namespace, hw: dict[str, Any]) -> dict[str, Any]:
    if not hw.get("cuda_available"):
        raise RuntimeError("Hunyuan3D-2 requires a CUDA GPU (L4 or A100).")

    repo_dir = Path("/content/Hunyuan3D-2")
    if not repo_dir.exists():
        run_cmd(["git", "clone", "https://github.com/Tencent/Hunyuan3D-2.git", str(repo_dir)])
        run_cmd([sys.executable, "-m", "pip", "install", "-q", "-r", str(repo_dir / "requirements.txt")])
        run_cmd([sys.executable, "-m", "pip", "install", "-q", "-e", str(repo_dir)])

    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

    import torch  # type: ignore
    from PIL import Image  # type: ignore
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline  # type: ignore
    from hy3dgen.texgen import Hunyuan3DPaintPipeline  # type: ignore

    t0 = time.time()
    use_mv = args.mode == "hunyuan3d-mv" and (args.side_input or args.back_input)
    model_id = "tencent/Hunyuan3D-2mv" if use_mv else "tencent/Hunyuan3D-2"
    subfolder = "hunyuan3d-dit-v2-mv" if use_mv else "hunyuan3d-dit-v2-0"

    print(f"[worker] Loading {model_id} ({subfolder})...", flush=True)
    shape_pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_id, subfolder=subfolder)

    if use_mv:
        views: dict[str, Any] = {"front": Image.open(args.input).convert("RGBA")}
        if args.side_input and Path(args.side_input).exists():
            views["left"] = Image.open(args.side_input).convert("RGBA")
        if args.back_input and Path(args.back_input).exists():
            views["back"] = Image.open(args.back_input).convert("RGBA")
        mesh = shape_pipe(
            image=views,
            num_inference_steps=30,
            octree_resolution=380,
            generator=torch.manual_seed(args.seed),
        )[0]
    else:
        front_img = Image.open(args.input).convert("RGBA")
        mesh = shape_pipe(
            image=front_img,
            num_inference_steps=30,
            octree_resolution=380,
            generator=torch.manual_seed(args.seed),
        )[0]

    print("[worker] Running Hunyuan3DPaintPipeline texture synthesis...", flush=True)
    tex_pipe = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
    mesh = tex_pipe(mesh, image=Image.open(args.input).convert("RGBA"))

    out_glb = Path(args.output)
    out_glb.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(out_glb))

    elapsed = round(time.time() - t0, 2)
    peak_vram = round(torch.cuda.max_memory_allocated() / (1024**3), 2)
    return {
        "engine": model_id,
        "multiview": use_mv,
        "seed": args.seed,
        "elapsed_seconds": elapsed,
        "peak_vram_gb": peak_vram,
        "glb": inspect_glb_metrics(out_glb),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Remote Colab GPU 3D worker for ZacharyPortfolio")
    parser.add_argument("--mode", choices=["smoke", "trellis2", "hunyuan3d", "hunyuan3d-mv"], default="smoke")
    parser.add_argument("--input", default="/content/omni_job/input_front.png")
    parser.add_argument("--side-input", default="")
    parser.add_argument("--back-input", default="")
    parser.add_argument("--output", default="/content/omni_job/raw_output.glb")
    parser.add_argument("--manifest", default="/content/omni_job/manifest.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resolution", default="1024")
    parser.add_argument("--decimation", type=int, default=80000)
    parser.add_argument("--texture-size", type=int, default=2048)
    parser.add_argument("--drive-cache", default="")
    args = parser.parse_args()

    cache_info = configure_cache_dirs(args.drive_cache or None)
    hw = collect_hardware_info()
    print(f"[worker] Hardware: {json.dumps(hw, indent=2)}", flush=True)

    result: dict[str, Any] = {
        "mode": args.mode,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": hw,
        "cache": cache_info,
        "status": "ok",
    }

    if args.mode == "smoke":
        result["smoke_check"] = "PASSED" if hw.get("cuda_available") else "CPU_ONLY"
    elif args.mode == "trellis2":
        result["generation"] = run_trellis2(args, hw)
    elif args.mode in ("hunyuan3d", "hunyuan3d-mv"):
        result["generation"] = run_hunyuan3d(args, hw)

    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[worker] Manifest written to {manifest_path}", flush=True)


if __name__ == "__main__":
    main()
