#!/usr/bin/env python3
"""Print-prep upscaler for still images (Real-ESRGAN 2x + exact sizing + paint texture).

tools/upscale.py is video-only. This is the stills path, tuned for wall-art prints
of painterly images: big flat color planes and hard black contours.

Usage:
  python3 tools/upscale-image.py <input.png> [output.png] [options]

Options:
  --inches WxH     Target print size in inches, e.g. 36x24
  --dpi N          Target DPI (default 240 — ample for wall viewing distance)
  --scale N        Upscale factor when --inches is not given (default 2)
  --model 0|1      0 = realesrgan-x4plus (default), 1 = realesr-animevideov3
  --tile N         ncnn tile size, 0 = auto (default 0; try 256 if memory-bound)
  --texture N      Canvas-weave strength 0..1 (default 0.30, 0 disables)
  --grain N        Fine luminance grain strength 0..1 (default 0.18, 0 disables)
  --sharpen N      Unsharp amount on contours 0..2 (default 0.45, 0 disables)
  --no-ai          Skip Real-ESRGAN, resize with lanczos only
  --tiff           Also write a .tif alongside (flattened, for the print shop)

Why texture/grain: an AI upscaler smooths brushwork into vector-flat color, which
at 30 inches reads as plastic and can band across large fields. Reinjecting a faint
canvas weave and grain restores the paint surface and dithers the flats.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None


def _blur(arr, radius):
    """Gaussian-blur a float array via a uint8 round-trip (PIL mode 'F' can't blur)."""
    lo, hi = float(arr.min()), float(arr.max())
    span = (hi - lo) or 1.0
    u8 = ((arr - lo) / span * 255.0).clip(0, 255).astype(np.uint8)
    b = Image.fromarray(u8, mode="L").filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(b, dtype=np.float32) / 255.0 * span + lo


def canvas_weave(w, h, strength, seed=7):
    """Faint woven-linen luminance field: crossed sinusoids + irregular thread noise."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # ~4px thread pitch reads as canvas at 240dpi
    warp = np.sin(xx * (np.pi / 4.0))
    weft = np.sin(yy * (np.pi / 4.0))
    weave = (warp * weft) * 0.6 + (warp + weft) * 0.2
    # thread-thickness irregularity so it never looks like a screen door
    jitter = _blur(rng.normal(0.0, 1.0, (h, w)).astype(np.float32), 1.4)
    field = weave * 0.75 + jitter * 0.6
    field /= (np.abs(field).max() + 1e-6)
    return field * (strength * 9.0)  # in 0-255 units; deliberately subtle


def fine_grain(w, h, strength, seed=11):
    rng = np.random.default_rng(seed)
    g = _blur(rng.normal(0.0, 1.0, (h, w)).astype(np.float32), 0.5)
    g /= (np.abs(g).max() + 1e-6)
    return g * (strength * 11.0)


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("input")
    p.add_argument("output", nargs="?")
    p.add_argument("--inches")
    p.add_argument("--dpi", type=int, default=240)
    p.add_argument("--scale", type=int, default=2)
    p.add_argument("--model", type=int, default=0)
    p.add_argument("--tile", type=int, default=0)
    p.add_argument("--texture", type=float, default=0.45)
    p.add_argument("--grain", type=float, default=0.18)
    p.add_argument("--sharpen", type=float, default=0.65)
    p.add_argument("--method", default="auto",
                   choices=["auto", "lanczos", "anime", "photo"],
                   help="auto (default): lanczos below 2x net scale, else the anime model. "
                        "MEASURED: Real-ESRGAN x4plus ('photo') waxes brushwork into plastic "
                        "on painterly sources — do not use it for paintings.")
    p.add_argument("--no-ai", action="store_true")
    p.add_argument("--tiff", action="store_true")
    a = p.parse_args()

    src = Path(a.input)
    if not src.exists():
        sys.exit(f"not found: {src}")
    out = Path(a.output) if a.output else src.with_name(f"{src.stem}_print.png")

    img = Image.open(src).convert("RGB")
    w0, h0 = img.size
    print(f"Input:  {w0}x{h0}  ({src})")

    # Target pixel dimensions
    if a.inches:
        iw, ih = (float(v) for v in a.inches.lower().split("x"))
        tw, th = int(round(iw * a.dpi)), int(round(ih * a.dpi))
        print(f"Target: {iw}x{ih} in @ {a.dpi} dpi = {tw}x{th}")
    else:
        tw, th = w0 * a.scale, h0 * a.scale
        print(f"Target: {tw}x{th} ({a.scale}x)")

    # Step 1: choose an enlargement method.
    # MEASURED (2026-08-24, Beckmann deck study at 36x24in): Real-ESRGAN x4plus melts oil
    # brushwork into waxy plastic streaks — visibly worse than plain lanczos at 1.7x net.
    # The anime model preserves more but still smooths. Below ~2x, lanczos is the honest choice:
    # it keeps real bristle drag and impasto granularity at the cost of slight softness,
    # which the unsharp + canvas-weave steps below recover.
    net = tw / max(1, w0)
    method = a.method
    if method == "auto":
        method = "lanczos" if net <= 2.0 else "anime"
    if a.no_ai:
        method = "lanczos"
    print(f"  Net scale {net:.2f}x -> method: {method}")

    if method in ("anime", "photo"):
        from realesrgan_ncnn_py import Realesrgan
        model_id = 1 if method == "anime" else 0
        up = Realesrgan(gpuid=0, tilesize=a.tile, model=model_id)
        step = 0
        while img.size[0] * 2 <= tw * 1.6 and step < 3:
            step += 1
            print(f"  Real-ESRGAN 2x pass {step} ({method}): {img.size[0]}x{img.size[1]} -> "
                  f"{img.size[0]*2}x{img.size[1]*2} ...", flush=True)
            img = up.process_pil(img).convert("RGB")

    # Step 2: exact resize
    if img.size != (tw, th):
        resample = Image.LANCZOS
        print(f"  Resizing {img.size[0]}x{img.size[1]} -> {tw}x{th} (lanczos)")
        img = img.resize((tw, th), resample)

    arr = np.asarray(img, dtype=np.float32)

    # Step 3: contour sharpen (restores the black-line snap the upscaler softens)
    if a.sharpen > 0:
        print(f"  Unsharp contours (amount={a.sharpen})")
        blurred = np.asarray(
            img.filter(ImageFilter.GaussianBlur(max(1.0, min(tw, th) / 900.0))),
            dtype=np.float32,
        )
        arr = arr + (arr - blurred) * a.sharpen

    # Step 4: paint surface
    if a.texture > 0 or a.grain > 0:
        print(f"  Paint surface (texture={a.texture}, grain={a.grain})")
        field = np.zeros((th, tw), dtype=np.float32)
        if a.texture > 0:
            field += canvas_weave(tw, th, a.texture)
        if a.grain > 0:
            field += fine_grain(tw, th, a.grain)
        # Modulate: strongest in midtones, backed off in blacks and near-whites so
        # the black contour lines stay solid and highlights don't go dirty.
        lum = arr.mean(axis=2) / 255.0
        mask = np.clip(1.0 - np.abs(lum - 0.5) * 1.7, 0.15, 1.0)
        arr += (field * mask)[:, :, None]

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    final = Image.fromarray(arr)

    out.parent.mkdir(parents=True, exist_ok=True)
    final.save(out, dpi=(a.dpi, a.dpi))
    mb = out.stat().st_size / 1e6
    print(f"Wrote:  {out}  {tw}x{th}  {mb:.1f} MB  @{a.dpi}dpi")

    if a.tiff:
        tif = out.with_suffix(".tif")
        final.save(tif, dpi=(a.dpi, a.dpi), compression="tiff_lzw")
        print(f"Wrote:  {tif}  {tif.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
