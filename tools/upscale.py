#!/usr/bin/env python3
"""AI video upscaler using Real-ESRGAN ncnn (via realesrgan-ncnn-py).

Requires: pip install realesrgan-ncnn-py

Usage:
  python3 tools/upscale.py <input.mp4> [output.mp4] [--scale 2|3|4] [--model 0|1]
  python3 tools/upscale.py data/workspace/video.mp4                     # -> video_4x.mp4
  python3 tools/upscale.py data/workspace/video.mp4 --scale 2 --model 1 # native AI 2x
  python3 tools/upscale.py data/workspace/video.mp4 custom_output.mp4   # explicit output name

Models:
  0 = realesrgan-x4plus (general, default) — best for live action, photography
  1 = realesr-animevideov3-x2 — optimized for animation/anime

Scale logic:
  General model produces 4x; animation model produces 2x. Lanczos resizes
  to the exact requested dimensions when the native model scale differs.
  The target is a factor of the input, not a fixed resolution. For UHD 4K,
  use --scale 2 from 1080p or --scale 3 from 720p.
  From 720p (9:16): 2x=1440x2560, 3x=2160x3840, 4x=2880x5120
  From 720p (16:9): 2x=2560x1440, 3x=3840x2160, 4x=5120x2880
"""
import sys
import time
import argparse
import json
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path


# Public CLI IDs are not the IDs used by realesrgan-ncnn-py 2.0.0.
# https://github.com/Tohrusky/realesrgan-ncnn-py
MODELS = {
    0: {"name": "realesrgan-x4plus", "wrapper_id": 4, "native_scale": 4},
    1: {"name": "realesr-animevideov3-x2", "wrapper_id": 0, "native_scale": 2},
}


def run_checked(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed ({result.returncode}):\n{result.stderr[-8000:]}")
    return result


def probe(path):
    return json.loads(run_checked([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ]).stdout)


def get_video_info(video_path):
    """Get resolution, fps, and duration from video."""
    info = probe(video_path)
    stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    fps = stream["r_frame_rate"]
    if Fraction(fps) <= 0:
        raise ValueError("Invalid source frame rate")
    if Fraction(stream.get("avg_frame_rate", fps)) != Fraction(fps):
        raise ValueError("This frame-preserving helper requires a constant-frame-rate source")
    return stream["width"], stream["height"], fps, float(stream.get("duration") or info["format"]["duration"])


def encode_command(frames_dir, input_path, output_path, fps_str, crf):
    return [
        "ffmpeg", "-nostdin", "-n", "-framerate", fps_str,
        "-i", str(frames_dir / "frame_%05d.png"), "-i", str(input_path),
        "-map", "0:v:0", "-map", "1:a?", "-map_metadata", "1",
        "-c:v", "libx264", "-crf", str(crf), "-preset", "slow",
        "-pix_fmt", "yuv420p", "-vf", "setsar=1", "-fps_mode", "passthrough",
        "-c:a", "copy", "-movflags", "+faststart", str(output_path),
    ]


def main():
    parser = argparse.ArgumentParser(description="AI video upscaler using Real-ESRGAN")
    parser.add_argument("input", help="Input video path")
    parser.add_argument("output", nargs="?", help="Output video path (default: input_Nx.mp4)")
    parser.add_argument("--scale", type=int, default=4, choices=[2, 3, 4],
                        help="Final scale factor (default: 4)")
    parser.add_argument("--model", type=int, default=0, choices=[0, 1],
                        help="Model: 0=realesrgan-x4plus (general), 1=realesr-animevideov3 (anime)")
    parser.add_argument("--crf", type=int, default=18, choices=range(0, 52), metavar="0..51")
    parser.add_argument("--tile", type=int, default=0, help="ncnn tile size; 0=auto or at least 32")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        suffix = f"_{args.scale}x"
        output_path = input_path.with_stem(input_path.stem + suffix)

    if output_path == input_path or output_path.exists():
        parser.error("Refusing to overwrite an existing file; choose a new output path")
    if args.tile != 0 and args.tile < 32:
        parser.error("--tile must be 0 or at least 32")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get source info
    width, height, fps_str, duration = get_video_info(input_path)
    if not all([width, height, fps_str, duration]):
        print("Error: couldn't read video info")
        sys.exit(1)

    target_w = width * args.scale
    target_h = height * args.scale
    total_frames = round(duration * float(Fraction(fps_str)))
    model = MODELS[args.model]

    print(f"Input:  {width}x{height}, {fps_str} fps, {duration:.1f}s ({total_frames} frames)")
    print(f"Output: {target_w}x{target_h} ({args.scale}x)")
    print(f"Model:  {model['name']} (native {model['native_scale']}x; exact output sizing)")
    print()

    # Import here so --help works without the dependency
    from realesrgan_ncnn_py import Realesrgan
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        frames_src = Path(tmpdir) / "src"
        frames_up = Path(tmpdir) / "up"
        frames_src.mkdir()
        frames_up.mkdir()

        # Step 1: Extract frames
        print("Extracting frames...")
        run_checked([
            "ffmpeg", "-nostdin", "-n", "-i", str(input_path),
            "-map", "0:v:0", "-fps_mode", "passthrough",
            str(frames_src / "frame_%05d.png"),
        ])
        frames = sorted(frames_src.glob("frame_*.png"))
        total = len(frames)
        print(f"Extracted {total} frames")
        if total != total_frames:
            raise RuntimeError(f"Frame count mismatch: expected {total_frames}, extracted {total}")

        # Step 2: AI upscale, followed by exact target sizing if needed.
        print(f"AI upscaling ({total} frames)...")
        upscaler = Realesrgan(gpuid=0, model=model["wrapper_id"], tilesize=args.tile)

        start = time.time()
        for i, frame_path in enumerate(frames):
            out_path = frames_up / frame_path.name
            with Image.open(frame_path) as image:
                img = image.convert("RGB")
            result = upscaler.process_pil(img)
            expected = (width * model["native_scale"], height * model["native_scale"])
            if result.size != expected:
                raise RuntimeError(f"Unexpected model output {result.size}; expected {expected}")
            if result.size != (target_w, target_h):
                result = result.resize((target_w, target_h), Image.Resampling.LANCZOS)
            result.save(out_path, compress_level=3)
            elapsed = time.time() - start
            fps = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (total - i - 1) / fps if fps > 0 else 0
            if i == 0 or (i + 1) % 12 == 0 or i + 1 == total:
                print(f"  [{i+1}/{total}] {fps:.1f} fps, ETA: {eta/60:.1f} min", flush=True)

        print(f"\nUpscale complete in {(time.time()-start)/60:.1f} minutes")

        # Encode once and stream-copy the approved audio without a lossy remux.
        print("Reassembling video...")
        run_checked(encode_command(frames_up, input_path, output_path, fps_str, args.crf))
        output_info = probe(output_path)
        video = next(s for s in output_info["streams"] if s["codec_type"] == "video")
        if (video["width"], video["height"], int(video["nb_frames"])) != (target_w, target_h, total):
            raise RuntimeError("Final export dimensions or frame count failed verification")
        if Fraction(video["avg_frame_rate"]) != Fraction(fps_str):
            raise RuntimeError("Final export frame rate changed")

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"\nDone! {output_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
