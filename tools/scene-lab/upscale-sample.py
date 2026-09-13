#!/usr/bin/env python3
"""Local-only frame sample comparison for the Meridian House video upscale."""
import argparse
import json
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw
from realesrgan_ncnn_py import Realesrgan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    times = [0, 11, 22]
    samples = []
    for index, seconds in enumerate(times):
        src = args.output / f"sample-{index}-source.png"
        subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-n", "-ss", str(seconds),
            "-i", str(args.input), "-frames:v", "1", str(src),
        ], check=True)
        samples.append(Image.open(src).convert("RGB"))
    # The general 4x network is tested alongside the native animation 2x network.
    timing = {}
    for name, model_id in [("animation", 0), ("general", 4)]:
        model = Realesrgan(gpuid=0, model=model_id, tilesize=256)
        started = time.monotonic()
        for index, src in enumerate(samples):
            print(f"{name}: sample {index + 1}/{len(samples)}", flush=True)
            result = model.process_pil(src)
            if result.size != (3840, 2160):
                result = result.resize((3840, 2160), Image.Resampling.LANCZOS)
            result.save(args.output / f"sample-{index}-{name}.png", compress_level=3)
        timing[name] = time.monotonic() - started
        print(f"{name}: {timing[name]:.1f}s", flush=True)
    # Native output-pixel crops, not scaled-down screenshots.
    for index, (src, center) in enumerate(zip(samples, [(960, 520), (800, 460), (1000, 580)])):
        images = [src.resize((3840, 2160), Image.Resampling.LANCZOS)]
        images += [Image.open(args.output / f"sample-{index}-{name}.png")
                   for name in ["animation", "general"]]
        x, y = center
        crop = (x * 2 - 320, y * 2 - 240, x * 2 + 320, y * 2 + 240)
        board = Image.new("RGB", (1920, 520), "#141821")
        draw = ImageDraw.Draw(board)
        for column, (img, name) in enumerate(zip(images, ["Lanczos reference", "Animation 2x", "General 4x down to 2x"])):
            draw.text((column * 640 + 16, 12), name, fill="white", font_size=20)
            board.paste(img.crop(crop), (column * 640, 40))
        board.save(args.output / f"comparison-{index}.png")
    with (args.output / "timing.json").open("x") as stream:
        json.dump(timing, stream, indent=2)


if __name__ == "__main__":
    main()
