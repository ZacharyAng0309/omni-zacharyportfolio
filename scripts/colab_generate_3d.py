#!/usr/bin/env python3
"""
Local Windows Orchestrator for Google Colab GPU 3D Generation (`ZacharyPortfolio`).

Wraps `google-colab-cli` to:
1. Check Colab Compute Unit (CCU) usage before provisioning.
2. Spin up an L4 (default for 3D) / T4 (smoke) / A100 (high-res hero) Colab runtime.
3. Upload `colab_remote_3d_worker.py` and input turnaround/concept images.
4. Run `TRELLIS.2-4B` or `Hunyuan3D-2(mv)` remotely with optional Drive weight caching.
5. Download `raw_output.glb` + `manifest.json` into `projects/ZacharyPortfolio/artifacts/<run-name>/`.
6. ALWAYS stop the Colab VM in a `finally:` block (unless `--keep` is set) to protect the 200 CCU/month budget.

Never prints or logs `HF_TOKEN` or OAuth secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
WORKER_SCRIPT = SCRIPT_DIR / "colab_remote_3d_worker.py"
DEFAULT_FRONT = PROJECT_ROOT / "artifacts" / "companion-v2-likeness" / "multiview" / "01_front.png"
ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts"


def run_colab(
    colab_args: list[str],
    *,
    dry_run: bool = False,
    check: bool = True,
    capture: bool = False,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str] | None:
    cmd = ["colab", *colab_args]
    # Redact any env secret values in console logs
    safe_display = [
        (a.split("=", 1)[0] + "=<REDACTED>" if ("TOKEN=" in a or "KEY=" in a or "SECRET=" in a) else a)
        for a in cmd
    ]
    print(f"[colab-orchestrator] $ {' '.join(safe_display)}", flush=True)
    if dry_run:
        return None
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        input=stdin_text,
        capture_output=capture,
    )


def ensure_colab_cli(dry_run: bool) -> None:
    if shutil.which("colab") is None and not dry_run:
        raise RuntimeError(
            "Google Colab CLI (`colab`) not found on PATH. Install it via:\n"
            "  uv tool install google-colab-cli\n"
            "Then authenticate once via:\n"
            "  colab --auth oauth2 sessions"
        )


def build_remote_exec_code(
    *,
    mode: str,
    remote_worker: str,
    remote_front: str,
    remote_side: str,
    remote_back: str,
    remote_glb: str,
    remote_manifest: str,
    seed: int,
    resolution: str,
    decimation: int,
    texture_size: int,
    drive_cache: str,
    hf_token_env_present: bool,
) -> str:
    worker_args = [
        sys.executable if False else "python3",
        remote_worker,
        "--mode",
        mode,
        "--input",
        remote_front,
        "--output",
        remote_glb,
        "--manifest",
        remote_manifest,
        "--seed",
        str(seed),
        "--resolution",
        resolution,
        "--decimation",
        str(decimation),
        "--texture-size",
        str(texture_size),
    ]
    if remote_side:
        worker_args.extend(["--side-input", remote_side])
    if remote_back:
        worker_args.extend(["--back-input", remote_back])
    if drive_cache:
        worker_args.extend(["--drive-cache", drive_cache])

    args_json = json.dumps(worker_args)
    return (
        "import os, subprocess, sys\n"
        f"cmd = {args_json}\n"
        "cmd[0] = sys.executable\n"
        "env = os.environ.copy()\n"
        f"# HF_TOKEN forwarded via runtime env if configured: {hf_token_env_present}\n"
        "proc = subprocess.run(cmd, env=env)\n"
        "if proc.returncode != 0:\n"
        "    raise SystemExit(proc.returncode)\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ZacharyPortfolio 3D GPU generation on Google Colab with auto-teardown CCU protection."
    )
    parser.add_argument("--mode", choices=["smoke", "trellis2", "hunyuan3d", "hunyuan3d-mv"], default="smoke")
    parser.add_argument("--gpu", choices=["T4", "L4", "A100", "H100"], default="L4")
    parser.add_argument("--high-mem", action="store_true", help="Request high-RAM shape (ignored for L4).")
    parser.add_argument("--input", type=Path, default=DEFAULT_FRONT, help="Front view / concept PNG.")
    parser.add_argument("--side-input", type=Path, default=None, help="Optional side view PNG for hunyuan3d-mv.")
    parser.add_argument("--back-input", type=Path, default=None, help="Optional back view PNG for hunyuan3d-mv.")
    parser.add_argument("--run-name", default="", help="Output artifact directory name under artifacts/.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resolution", default="1024", help="TRELLIS.2 resolution preset (512, 1024, 1024_cascade, 1536_cascade).")
    parser.add_argument("--decimation", type=int, default=80000, help="Raw GLB decimation target before Blender cleanup.")
    parser.add_argument("--texture-size", type=int, default=2048, help="PBR texture resolution (1024 or 2048).")
    parser.add_argument("--drive-cache", action="store_true", help="Mount Google Drive and cache HF weights in MyDrive/omni_colab_cache.")
    parser.add_argument("--keep", action="store_true", help="Keep Colab VM alive after run (WARNING: continues consuming CCUs).")
    parser.add_argument("--session", default="", help="Optional custom Colab session name.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned Colab CLI actions without provisioning a VM.")
    args = parser.parse_args()

    ensure_colab_cli(args.dry_run)

    if not WORKER_SCRIPT.exists():
        raise FileNotFoundError(f"Missing remote worker script: {WORKER_SCRIPT}")

    if args.mode != "smoke" and not args.input.exists():
        raise FileNotFoundError(f"Input image not found: {args.input}")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"colab-{args.mode}-{timestamp}"
    session_name = args.session or f"omni-portfolio-{args.mode}-{timestamp}"
    out_dir = ARTIFACTS_ROOT / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    remote_root = "/content/omni_job"
    remote_worker = f"{remote_root}/colab_remote_3d_worker.py"
    remote_front = f"{remote_root}/input_front{args.input.suffix or '.png'}"
    remote_side = f"{remote_root}/input_side{args.side_input.suffix}" if args.side_input else ""
    remote_back = f"{remote_root}/input_back{args.back_input.suffix}" if args.back_input else ""
    remote_glb = f"{remote_root}/raw_output.glb"
    remote_manifest = f"{remote_root}/manifest.json"
    drive_cache_path = "/content/drive/MyDrive/omni_colab_cache" if args.drive_cache else ""

    print(f"[colab-orchestrator] Mode={args.mode} | GPU={args.gpu} | Output={out_dir}", flush=True)

    # 1. Inspect current CCU balance before allocating GPU
    run_colab(["usage"], dry_run=args.dry_run, check=False)

    # 2. Provision Colab runtime
    new_cmd = ["new", "--session", session_name, "--gpu", args.gpu]
    if args.high_mem:
        new_cmd.append("--high-mem")
    run_colab(new_cmd, dry_run=args.dry_run)

    try:
        # 3. Optional Google Drive mount for persistent HF model cache
        if args.drive_cache:
            run_colab(["drivemount", "-s", session_name, "/content/drive"], dry_run=args.dry_run, check=False)

        # 4. Create remote job directory & upload worker + inputs
        run_colab(
            ["exec", "-s", session_name],
            dry_run=args.dry_run,
            stdin_text=f"import pathlib; pathlib.Path({remote_root!r}).mkdir(parents=True, exist_ok=True)\n",
        )
        run_colab(["upload", "-s", session_name, str(WORKER_SCRIPT), remote_worker], dry_run=args.dry_run)

        if args.mode != "smoke":
            run_colab(["upload", "-s", session_name, str(args.input), remote_front], dry_run=args.dry_run)
            if args.side_input and args.side_input.exists():
                run_colab(["upload", "-s", session_name, str(args.side_input), remote_side], dry_run=args.dry_run)
            if args.back_input and args.back_input.exists():
                run_colab(["upload", "-s", session_name, str(args.back_input), remote_back], dry_run=args.dry_run)

        # 5. Execute remote GPU worker (disable idle timeout for model downloads & 3D inference)
        hf_token = os.environ.get("HF_TOKEN", "").strip()
        exec_code = build_remote_exec_code(
            mode=args.mode,
            remote_worker=remote_worker,
            remote_front=remote_front,
            remote_side=remote_side,
            remote_back=remote_back,
            remote_glb=remote_glb,
            remote_manifest=remote_manifest,
            seed=args.seed,
            resolution=args.resolution,
            decimation=args.decimation,
            texture_size=args.texture_size,
            drive_cache=drive_cache_path,
            hf_token_env_present=bool(hf_token),
        )
        exec_cmd = ["exec", "-s", session_name, "--timeout", "0"]
        if hf_token:
            exec_cmd.extend(["--env", f"HF_TOKEN={hf_token}"])
        run_colab(exec_cmd, dry_run=args.dry_run, stdin_text=exec_code)

        # 7. Pull manifest and GLB back to local workspace
        local_manifest = out_dir / "manifest.json"
        run_colab(["download", "-s", session_name, remote_manifest, str(local_manifest)], dry_run=args.dry_run)

        if args.mode != "smoke":
            local_glb = out_dir / "raw_output.glb"
            run_colab(["download", "-s", session_name, remote_glb, str(local_glb)], dry_run=args.dry_run)
            print(
                f"\n[colab-orchestrator] Staging GLB saved to: {local_glb}\n"
                "Next step (Blender 5.2 governance & rigging):\n"
                "  Inspect with `node projects/ZacharyPortfolio/scripts/inspect_glb.mjs` or\n"
                "  rig/bake via `projects/ZacharyPortfolio/scripts/rig_likeness_companion.py`.",
                flush=True,
            )
        else:
            print(f"\n[colab-orchestrator] Smoke test manifest saved to: {local_manifest}", flush=True)
    finally:
        if args.keep:
            print(
                f"[colab-orchestrator] --keep set. Session `{session_name}` remains active. "
                f"Stop it manually with: colab stop -s {shlex.quote(session_name)}",
                flush=True,
            )
        else:
            print(f"[colab-orchestrator] Auto-stopping session `{session_name}` to preserve CCUs...", flush=True)
            run_colab(["stop", "-s", session_name], dry_run=args.dry_run, check=False)


if __name__ == "__main__":
    main()
