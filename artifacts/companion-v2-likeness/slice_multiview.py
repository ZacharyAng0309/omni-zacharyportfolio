"""Split the approved 4-view glasses-off turnaround sheet into aligned, seamless 1024x1024 PNGs."""

from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image


ARTIFACT_DIR = Path(
    r"d:\omni-workstation\projects\ZacharyPortfolio\artifacts\companion-v2-likeness"
)
INPUT_PATH = ARTIFACT_DIR / "zachary_turnaround_4view_glasses_off.png"
OUTPUT_DIR = ARTIFACT_DIR / "multiview"
VIEW_NAMES = [
    "01_front.png",
    "02_threequarter.png",
    "03_side.png",
    "04_back.png",
]
TARGET_SIZE = 1024


def find_horizontal_components(col_active: np.ndarray, min_width: int = 40) -> list[tuple[int, int]]:
    """Find contiguous horizontal foreground intervals (x0, x1 inclusive)."""
    components: list[tuple[int, int]] = []
    in_seg = False
    start = 0
    padded = col_active.copy()
    for i in range(1, len(col_active) - 1):
        if not padded[i] and padded[i - 1] and padded[i + 1]:
            padded[i] = True
    for x, active in enumerate(padded):
        if active and not in_seg:
            in_seg = True
            start = x
        elif not active and in_seg:
            in_seg = False
            if (x - 1) - start + 1 >= min_width:
                components.append((start, x - 1))
    if in_seg:
        end = len(padded) - 1
        if end - start + 1 >= min_width:
            components.append((start, end))
    return components


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing turnaround image: {INPUT_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.open(INPUT_PATH).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)
    height, width, _ = arr.shape

    # Step 1: Detect the 4 coarse character intervals via top-wall reference comparison
    top_luma = arr[:24, :, :].mean(axis=(0, 2))[None, :]  # (1, W)
    luma = arr.mean(axis=2)
    dark_upper = luma[: int(height * 0.90), :] < (top_luma - 18.0)
    components = find_horizontal_components(dark_upper.sum(axis=0) >= 6, min_width=40)
    if len(components) != 4:
        raise RuntimeError(
            f"Expected 4 horizontal character components, found {len(components)}: {components}"
        )

    # Step 2: Locate 5 guaranteed-empty studio background vertical strips & fit 2D studio model
    strip_xs: list[int] = [
        max(0, min(components[0][0] - 12, 16)),
        (components[0][1] + components[1][0]) // 2,
        (components[1][1] + components[2][0]) // 2,
        (components[2][1] + components[3][0]) // 2,
        min(width - 1, max(components[3][1] + 12, width - 17)),
    ]
    strip_profiles = np.stack(
        [np.median(arr[:, max(0, sx - 2) : min(width, sx + 3), :], axis=1) for sx in strip_xs],
        axis=0,
    )  # (5, H, 3)

    # Smooth horizontal studio illumination across W using the 5 empty strips
    xs_grid = np.arange(width, dtype=np.float32)
    bg_2d = np.zeros_like(arr)
    for y in range(height):
        for c in range(3):
            bg_2d[y, :, c] = np.interp(xs_grid, strip_xs, strip_profiles[:, y, c])

    # Canonical clean studio vertical gradient (average of inner 3 studio strips)
    canonical_bg = np.mean(strip_profiles[1:4], axis=0)  # (H, 3)
    # Remove horizontal studio vignette ONLY where subtle, keeping foreground colors intact
    vignette_delta = bg_2d - canonical_bg[:, None, :]
    flat_arr = np.clip(arr - vignette_delta, 0.0, 255.0)
    flat_pil = Image.fromarray(flat_arr.astype(np.uint8), mode="RGB")

    # Step 3: Refine exact tight character bounding boxes inside safe gap midpoints
    diff = np.linalg.norm(flat_arr - canonical_bg[:, None, :], axis=2)
    boxes: list[tuple[int, int, int, int]] = []
    for idx in range(4):
        left_lim = 0 if idx == 0 else strip_xs[idx]
        right_lim = width - 1 if idx == 3 else strip_xs[idx + 1]
        sub_diff = diff[:, left_lim : right_lim + 1]
        # Strong foreground threshold excludes very soft ambient floor shadow (< 22)
        strong_fg = sub_diff > 22.0
        xs = np.where(strong_fg[: int(height * 0.94), :].any(axis=0))[0] + left_lim
        ys = np.where(strong_fg[: height - 12, :].any(axis=1))[0]
        if len(xs) == 0 or len(ys) == 0:
            raise RuntimeError(f"Empty refined foreground in view {idx}")
        boxes.append((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))

    global_y0 = min(b[1] for b in boxes)
    global_y1 = max(b[3] for b in boxes)
    global_h = float(global_y1 - global_y0 + 1)
    max_w = float(max(b[2] - b[0] + 1 for b in boxes))

    scale = min((TARGET_SIZE * 0.84) / global_h, (TARGET_SIZE * 0.84) / max_w)
    print(f"Source: {width}x{height}, strips={strip_xs}")
    print(f"Tight boxes: {boxes}")
    print(f"global_y=[{global_y0}, {global_y1}], scale={scale:.4f}")

    for idx, ((x0, y0, x1, y1), view_name) in enumerate(zip(boxes, VIEW_NAMES)):
        left_gap = 0 if idx == 0 else strip_xs[idx]
        right_gap = width - 1 if idx == 3 else strip_xs[idx + 1]

        src_pad_top = min(global_y0, 24)
        src_pad_bot = min(height - 1 - global_y1, 18)
        sy0 = global_y0 - src_pad_top
        sy1 = global_y1 + src_pad_bot + 1

        fig_w = x1 - x0 + 1
        pad_x = max(8, int(round(fig_w * 0.08)))
        sx0 = max(left_gap, x0 - pad_x)
        sx1 = min(right_gap + 1, x1 + pad_x + 1)

        crop = flat_pil.crop((sx0, sy0, sx1, sy1))
        crop_w, crop_h = crop.size
        resized_w = max(1, int(round(crop_w * scale)))
        resized_h = max(1, int(round(crop_h * scale)))
        crop_resized = crop.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
        crop_arr = np.asarray(crop_resized, dtype=np.float32)

        paste_y = (TARGET_SIZE - resized_h) // 2
        fig_cx_in_crop = ((x0 + x1) * 0.5 - sx0) * scale
        paste_x = int(round(TARGET_SIZE * 0.5 - fig_cx_in_crop))

        # Canvas initialized strictly to canonical empty-studio gradient (zero horizontal mismatch)
        canvas_arr = np.zeros((TARGET_SIZE, TARGET_SIZE, 3), dtype=np.float32)
        for ty in range(TARGET_SIZE):
            if ty < paste_y:
                canvas_arr[ty, :, :] = canonical_bg[sy0]
            elif ty >= paste_y + resized_h:
                canvas_arr[ty, :, :] = canonical_bg[min(height - 1, sy1 - 1)]
            else:
                src_r = int(
                    np.clip(
                        round(sy0 + (ty - paste_y) / max(1, resized_h - 1) * (sy1 - 1 - sy0)),
                        0,
                        height - 1,
                    )
                )
                canvas_arr[ty, :, :] = canonical_bg[src_r]

        # Cosine alpha feather strictly inside the empty background margin around edges
        alpha = np.ones((resized_h, resized_w, 1), dtype=np.float32)
        left_margin_px = max(2, int(round((x0 - sx0) * scale * 0.75)))
        right_margin_px = max(2, int(round((sx1 - 1 - x1) * scale * 0.75)))
        feather_l = min(14, left_margin_px)
        feather_r = min(14, right_margin_px)
        for k in range(feather_l):
            alpha[:, k, 0] = np.minimum(
                alpha[:, k, 0], 0.5 * (1.0 - np.cos(np.pi * (k + 0.5) / feather_l))
            )
        for k in range(feather_r):
            alpha[:, resized_w - 1 - k, 0] = np.minimum(
                alpha[:, resized_w - 1 - k, 0],
                0.5 * (1.0 - np.cos(np.pi * (k + 0.5) / feather_r)),
            )
        for k in range(12):
            w = 0.5 * (1.0 - np.cos(np.pi * (k + 0.5) / 12.0))
            alpha[k, :, 0] = np.minimum(alpha[k, :, 0], w)
            alpha[resized_h - 1 - k, :, 0] = np.minimum(alpha[resized_h - 1 - k, :, 0], w)

        x_dst0 = max(0, paste_x)
        x_dst1 = min(TARGET_SIZE, paste_x + resized_w)
        x_src0 = x_dst0 - paste_x
        x_src1 = x_src0 + (x_dst1 - x_dst0)

        y_dst0 = max(0, paste_y)
        y_dst1 = min(TARGET_SIZE, paste_y + resized_h)
        y_src0 = y_dst0 - paste_y
        y_src1 = y_src0 + (y_dst1 - y_dst0)

        region_bg = canvas_arr[y_dst0:y_dst1, x_dst0:x_dst1]
        region_fg = crop_arr[y_src0:y_src1, x_src0:x_src1]
        region_a = alpha[y_src0:y_src1, x_src0:x_src1]
        canvas_arr[y_dst0:y_dst1, x_dst0:x_dst1] = (
            region_fg * region_a + region_bg * (1.0 - region_a)
        )

        out_img = Image.fromarray(np.clip(canvas_arr, 0, 255).astype(np.uint8), mode="RGB")
        out_path = OUTPUT_DIR / view_name
        out_img.save(out_path, "PNG")
        print(
            f"  [{view_name}] box=({x0},{y0})..({x1},{y1}) crop=({sx0},{sy0})..({sx1},{sy1}) paste=({paste_x},{paste_y}) -> {out_path}"
        )


if __name__ == "__main__":
    main()
