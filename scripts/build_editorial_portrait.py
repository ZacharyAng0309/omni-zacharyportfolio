#!/usr/bin/env python3
"""
Builds dark-studio editorial portrait asset (`public/images/zachary_editorial_portrait.webp`)
from immutable `public/images/reference_portrait.jpg` using border-connected flood-fill
matting, sub-pixel edge decontamination, and obsidian-charcoal studio grading.
"""
from __future__ import annotations

import os
from collections import deque
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def build_editorial_portrait(src_path: str, dst_path: str) -> None:
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Missing reference portrait: {src_path}")

    src_img = Image.open(src_path).convert("RGB")
    arr = np.asarray(src_img, dtype=np.float32)
    h, w, _ = arr.shape

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    chroma = max_c - min_c
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    # Border-connected flood-fill for neutral bright studio backdrop.
    # Never enters the enclosed white dress shirt collar inside the dark suit lapels.
    is_bg_candidate = (min_c >= 216.0) & (chroma <= 24.0)

    bg_mask = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()

    for x in range(w):
        if is_bg_candidate[0, x] and not bg_mask[0, x]:
            bg_mask[0, x] = True
            q.append((0, x))
        if is_bg_candidate[h - 1, x] and not bg_mask[h - 1, x]:
            bg_mask[h - 1, x] = True
            q.append((h - 1, x))
    for y in range(h):
        if is_bg_candidate[y, 0] and not bg_mask[y, 0]:
            bg_mask[y, 0] = True
            q.append((y, 0))
        if is_bg_candidate[y, w - 1] and not bg_mask[y, w - 1]:
            bg_mask[y, w - 1] = True
            q.append((y, w - 1))

    while q:
        cy, cx = q.popleft()
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w:
                if not bg_mask[ny, nx] and is_bg_candidate[ny, nx]:
                    bg_mask[ny, nx] = True
                    q.append((ny, nx))

    # Build continuous alpha matte (1 = subject, 0 = background)
    alpha = (~bg_mask).astype(np.float32)

    # Identify soft fringe zone right outside bg_mask (dilate bg_mask by ~3px)
    bg_pil = Image.fromarray((bg_mask.astype(np.uint8) * 255), mode="L")
    dilated_3 = np.asarray(bg_pil.filter(ImageFilter.MaxFilter(7)), dtype=np.float32) / 255.0
    fringe_band = (dilated_3 > 0.5) & (~bg_mask)

    # Inside the fringe band around hair/ears/shoulders, ramp alpha softly for semi-transparent light pixels
    # caused by anti-aliasing against the bright white backdrop (preserving crisp suit/collar).
    soft_alpha = np.clip((232.0 - lum) / 56.0, 0.0, 1.0)
    # Also retain saturated warm skin/ear tones in the fringe band even if bright
    warm_skin_bias = np.clip((chroma - 14.0) / 18.0, 0.0, 1.0)
    fringe_alpha = np.maximum(soft_alpha, warm_skin_bias * 0.92)
    alpha = np.where(fringe_band, np.minimum(alpha, fringe_alpha), alpha)

    # Smooth the alpha edge gently (sub-pixel feathering)
    alpha_img = Image.fromarray(np.clip(alpha * 255.0, 0, 255).astype(np.uint8), mode="L")
    alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(radius=0.85))
    alpha = np.asarray(alpha_img, dtype=np.float32) / 255.0

    # Slightly pull inward on strictly partial alpha edges so no white ring leaks onto dark canvas
    alpha = np.clip((alpha - 0.14) / 0.84, 0.0, 1.0)

    # Color decontamination on semi-transparent boundary pixels:
    # observed = a * fg + (1 - a) * 255  =>  fg = (observed - (1 - a) * 255) / a
    fg = arr.copy()
    edge_zone = (alpha > 0.02) & (alpha < 0.98)
    safe_a = np.maximum(alpha, 0.18)
    decontam = (arr - (1.0 - alpha[:, :, None]) * 248.0) / safe_a[:, :, None]
    decontam = np.clip(decontam, 0.0, 255.0)
    fg = np.where(edge_zone[:, :, None], decontam, fg)

    # Darken very residual bright fringe halo on dark hair/suit edges
    outer_halo = (alpha > 0.02) & (alpha < 0.72) & (chroma[:, :] < 20.0) & (lum[:, :] > 135.0)
    fg = np.where(outer_halo[:, :, None], fg * 0.55, fg)

    # Resize foreground + alpha to 600x800 editorial target using LANCZOS
    target_w, target_h = 600, 800
    fg_pil = Image.fromarray(np.clip(fg, 0, 255).astype(np.uint8), mode="RGB").resize(
        (target_w, target_h), Image.Resampling.LANCZOS
    )
    a_pil = Image.fromarray(np.clip(alpha * 255.0, 0, 255).astype(np.uint8), mode="L").resize(
        (target_w, target_h), Image.Resampling.LANCZOS
    )

    # Subtle editorial grading: preserve natural skin tones while giving crisp studio contrast
    fg_pil = ImageEnhance.Contrast(fg_pil).enhance(1.04)
    fg_pil = ImageEnhance.Brightness(fg_pil).enhance(0.97)

    # Build rich dark obsidian-charcoal radial studio gradient (#222026 center behind head -> #0e0d10 edges)
    yy, xx = np.mgrid[0:target_h, 0:target_w].astype(np.float32)
    nx_g = (xx / target_w - 0.50) * 1.15
    ny_g = (yy / target_h - 0.36) * 0.95
    dist = np.sqrt(nx_g * nx_g + ny_g * ny_g)
    radial = np.exp(-(dist * dist) * 2.6)

    bg_center = np.array([34.0, 32.0, 38.0], dtype=np.float32)   # #222026
    bg_edge = np.array([14.0, 13.0, 16.0], dtype=np.float32)     # #0e0d10
    studio_bg = bg_edge[None, None, :] + (bg_center - bg_edge)[None, None, :] * radial[:, :, None]

    # Subtle warm amber/champagne top-back rim vignette matching Titanium Atelier palette
    rim_dist = np.sqrt(((xx / target_w - 0.50) * 1.4) ** 2 + ((yy / target_h - 0.34) * 1.3) ** 2)
    rim_glow = np.exp(-(rim_dist * rim_dist) * 4.5) * 0.08
    studio_bg[:, :, 0] += rim_glow * 48.0
    studio_bg[:, :, 1] += rim_glow * 36.0
    studio_bg[:, :, 2] += rim_glow * 24.0

    fg_arr = np.asarray(fg_pil, dtype=np.float32)
    a_arr = (np.asarray(a_pil, dtype=np.float32) / 255.0)[:, :, None]

    comp = fg_arr * a_arr + studio_bg * (1.0 - a_arr)

    # Soft bottom studio vignette fade so suit bottom blends smoothly into glass card
    bottom_t = np.clip((yy / target_h - 0.84) / 0.16, 0.0, 1.0)
    bottom_fade = (bottom_t * bottom_t * 0.42)[:, :, None]
    comp = comp * (1.0 - bottom_fade) + bg_edge[None, None, :] * bottom_fade

    out_img = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8), mode="RGB")
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    out_img.save(dst_path, format="WEBP", quality=90, method=6)
    size_bytes = os.path.getsize(dst_path)
    print(f"Saved {dst_path}: {target_w}x{target_h}, {size_bytes} bytes")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    build_editorial_portrait(
        os.path.join(root, "public", "images", "reference_portrait.jpg"),
        os.path.join(root, "public", "images", "zachary_editorial_portrait.webp"),
    )
