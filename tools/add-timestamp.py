#!/usr/bin/env python3
"""
add-timestamp.py — burn a frame-accurate timecode into a video's corner.

Given test.mp4 it writes test_debug.mp4 (same folder) with a running
HH:MM:SS.mmm timestamp in the bottom-right corner. The time shown for each
frame is frame_index / fps, so it is exact and deterministic — read it straight
off a paused frame.

Why PIL instead of ffmpeg drawtext: the local ffmpeg build has no libfreetype,
so drawtext/ass are unavailable. We rasterize the timecode with PIL into a tiny
per-frame overlay sprite and composite it with ffmpeg's overlay filter. The
video frames themselves never pass through Python, so it stays fast.

Usage:
  tools/add-timestamp.py INPUT.mp4 [OUTPUT.mp4] [options]

Options:
  --suffix STR     Output name suffix when OUTPUT is omitted (default: _debug)
  --pos CORNER     br | bl | tr | tl  (default: br)
  --fontsize N     Override auto font size (default: ~height/40, min 18)
  --pad N          Margin from the frame edge in px (default: ~fontsize*0.4)
  --frame          Also show the frame number, e.g. "00:00:01.233  f37"
  --no-box         Skip the translucent background box (outline only)
  --opacity F      Background box opacity 0..1 (default: 0.55)
  --crf N          x264 quality, lower = better (default: 18)
  --preset NAME    x264 preset (default: medium)
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/System/Library/Fonts/Supplemental/Andale Mono.ttf",
    "/System/Library/Fonts/SFNSMono.ttf",
]


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def ffprobe(args):
    return subprocess.run(
        ["ffprobe", "-v", "error", *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    die("no usable monospace font found (looked in /System/Library/Fonts)")


def parse_rate(r):
    """'30000/1001' -> (float, original_string)."""
    if not r or r in ("0/0", "N/A"):
        return 30.0, "30"
    if "/" in r:
        num, den = r.split("/")
        den = float(den) or 1.0
        return float(num) / den, r
    return float(r), r


def probe(path):
    w, h = ffprobe([
        "-select_streams", "v:0", "-show_entries", "stream=width,height",
        "-of", "csv=p=0", path,
    ]).split(",")
    r_raw = ffprobe([
        "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
        "-of", "csv=p=0", path,
    ])
    fps, fps_str = parse_rate(r_raw)
    nb = ffprobe([
        "-select_streams", "v:0", "-show_entries", "stream=nb_frames",
        "-of", "csv=p=0", path,
    ])
    if nb.isdigit() and int(nb) > 0:
        frames = int(nb)
    else:
        dur = ffprobe([
            "-show_entries", "format=duration", "-of", "csv=p=0", path,
        ])
        frames = round(float(dur) * fps)
    has_audio = bool(ffprobe([
        "-select_streams", "a:0", "-show_entries", "stream=index",
        "-of", "csv=p=0", path,
    ]))
    return int(w), int(h), fps, fps_str, frames, has_audio


def fmt_timecode(frame_idx, fps):
    total_ms = round(frame_idx * 1000.0 / fps)
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--suffix", default="_debug")
    ap.add_argument("--pos", default="br", choices=["br", "bl", "tr", "tl"])
    ap.add_argument("--fontsize", type=int, default=0)
    ap.add_argument("--pad", type=int, default=-1)
    ap.add_argument("--frame", action="store_true")
    ap.add_argument("--no-box", dest="box", action="store_false")
    ap.add_argument("--opacity", type=float, default=0.55)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    args = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        die("ffmpeg/ffprobe not found on PATH")

    src = Path(args.input)
    if not src.is_file():
        die(f"input not found: {src}")

    out = Path(args.output) if args.output else \
        src.with_name(f"{src.stem}{args.suffix}{src.suffix}")
    if out.resolve() == src.resolve():
        die("output path is the same as input; choose a different name")

    W, H, fps, fps_str, n_frames, has_audio = probe(str(src))
    if n_frames <= 0:
        die("could not determine frame count")

    fontsize = args.fontsize if args.fontsize > 0 else max(18, round(H / 40))
    pad = args.pad if args.pad >= 0 else max(6, round(fontsize * 0.4))
    inner = max(4, round(fontsize * 0.3))           # padding inside the box
    stroke = max(1, fontsize // 18)
    font = load_font(fontsize)

    if n_frames > 30000:
        print(f"warning: {n_frames} frames — overlay generation may be slow.",
              file=sys.stderr)

    # Sprite size: constant because the timecode is fixed-width and monospaced.
    sample = fmt_timecode(0, fps) + ("  f000000" if args.frame else "")
    dummy = Image.new("RGBA", (8, 8))
    bbox = ImageDraw.Draw(dummy).textbbox(
        (0, 0), sample, font=font, stroke_width=stroke)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    box_w, box_h = tw + 2 * inner, th + 2 * inner

    tmp = Path(tempfile.mkdtemp(prefix="ts_overlay_"))
    try:
        print(f">> {src.name}: {W}x{H} @ {fps_str} fps, {n_frames} frames "
              f"-> {out.name}", file=sys.stderr)
        # Render one transparent sprite per frame (plus a small tail buffer so
        # the overlay never runs short and freezes on the last clip frames).
        box_rgba = (0, 0, 0, round(max(0.0, min(1.0, args.opacity)) * 255))
        for i in range(n_frames + 5):
            img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            if args.box:
                d.rectangle([0, 0, box_w - 1, box_h - 1], fill=box_rgba)
            text = fmt_timecode(i, fps)
            if args.frame:
                text += f"  f{i}"
            d.text((inner - bbox[0], inner - bbox[1]), text, font=font,
                   fill=(255, 255, 255, 255), stroke_width=stroke,
                   stroke_fill=(0, 0, 0, 255))
            img.save(tmp / f"ts_{i:06d}.png")
            if i and i % 500 == 0:
                print(f"   rendered {i}/{n_frames} overlay frames",
                      file=sys.stderr)

        if args.pos == "br":
            xy = f"x=W-w-{pad}:y=H-h-{pad}"
        elif args.pos == "bl":
            xy = f"x={pad}:y=H-h-{pad}"
        elif args.pos == "tr":
            xy = f"x=W-w-{pad}:y={pad}"
        else:  # tl
            xy = f"x={pad}:y={pad}"

        cmd = [
            "ffmpeg", "-y", "-hide_banner",
            "-i", str(src),
            "-framerate", fps_str, "-start_number", "0",
            "-i", str(tmp / "ts_%06d.png"),
            # shortest=1 so the (intentionally longer) sprite track never
            # extends the video past its real end.
            "-filter_complex", f"[0:v][1:v]overlay={xy}:format=auto:shortest=1[v]",
            "-map", "[v]",
        ]
        if has_audio:
            cmd += ["-map", "0:a?", "-c:a", "copy"]
        cmd += [
            "-c:v", "libx264", "-crf", str(args.crf), "-preset", args.preset,
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(out),
        ]
        subprocess.run(cmd, check=True)
        print(f">> done: {out}", file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
