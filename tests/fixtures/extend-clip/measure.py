#!/usr/bin/env python3
"""measure.py — cycle-2 anchor-binding measurements for one B arm.

Usage: measure.py B.mp4 conditioning.png A.mp4 A_end_index out.json

Reports:
  1. B[0] vs conditioning PNG: gray MAE (native res) + RGB PSNR (ffmpeg psnr
     filter). Read MAE against the ~0.05 codec-noise floor (a lossless
     round-trip of the anchor through libx264 CRF-equivalent lands there).
  2. seam-check --pair A:A_end B:K for K in 0..12 (photometric RATIO,
     VELOCITY_RATIO, B-head series) — the head-trim sweep.
All from the RAW mp4; nothing is normalized first.
"""
import json
import re
import subprocess
import sys

import numpy as np


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=False, **kw)


def gray_frame0(path, width, height):
    p = run(["ffmpeg", "-v", "error", "-i", path,
             "-vf", f"select=eq(n\\,0),scale={width}:{height},format=gray",
             "-vsync", "0", "-frames:v", "1",
             "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    if p.returncode != 0:
        sys.exit(f"ffmpeg gray decode failed on {path}: {p.stderr.decode()}")
    return np.frombuffer(p.stdout, dtype=np.uint8).astype(np.float64)


def probe(path):
    p = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
             "-of", "json", path])
    s = json.loads(p.stdout)["streams"][0]
    return int(s["width"]), int(s["height"]), s["r_frame_rate"], int(s["nb_frames"])


def rgb_psnr(b_mp4, png, w, h):
    # B frame 0 vs the conditioning PNG, both at B's native raster.
    p = run(["ffmpeg", "-v", "info", "-i", b_mp4, "-i", png,
             "-filter_complex",
             f"[0:v]select=eq(n\\,0),format=rgb24[b];"
             f"[1:v]scale={w}:{h},format=rgb24[a];"
             f"[b][a]psnr", "-frames:v", "1", "-f", "null", "-"])
    m = re.search(rb"average:([0-9.]+|inf)", p.stderr)
    return float(m.group(1)) if m and m.group(1) != b"inf" else float("inf")


def main():
    b_mp4, png, a_mp4, a_end, out_json = sys.argv[1:6]
    a_end = int(a_end)
    w, h, fps, nb = probe(b_mp4)
    g_b = gray_frame0(b_mp4, w, h)
    g_a = gray_frame0(png, w, h)
    mae = float(np.abs(g_b - g_a).mean())
    mse = float(((g_b - g_a) ** 2).mean())
    psnr_gray = float("inf") if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)
    psnr = rgb_psnr(b_mp4, png, w, h)

    sweep = []
    for k in range(0, 13):
        p = run(["python3", "tools/seam-check.py", "--pair",
                 f"{a_mp4}:{a_end}", f"{b_mp4}:{k}", "--json"])
        try:
            d = json.loads(p.stdout)
        except json.JSONDecodeError:
            sys.exit(f"seam-check failed at B:{k}: {p.stderr.decode()}")
        sweep.append({"b_start": k, "ratio": d["ratio"],
                      "velocity_ratio": d["velocity_ratio"],
                      "branch": d["branch"], "fail": d["fail"],
                      "photometric_fail": d["photometric_fail"],
                      "kinematic_fail": d["kinematic_fail"]})
        if k == 0:
            head = d["b_head_deltas"]

    result = {
        "b_clip": b_mp4, "conditioning_png": png,
        "a_clip": a_mp4, "a_end_index": a_end,
        "b_specs": {"width": w, "height": h, "fps": fps, "nb_frames": nb},
        "frame0_vs_anchor": {"gray_mae": round(mae, 3),
                             "gray_psnr_db": round(psnr_gray, 2),
                             "rgb_psnr_db": round(psnr, 2),
                             "noise_floor_note":
                             "codec round-trip floor ~0.05 gray MAE"},
        "b_head_deltas_at_k0": head,
        "head_trim_sweep": sweep,
    }
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result["frame0_vs_anchor"], indent=2))
    passes = [s["b_start"] for s in sweep if not s["fail"]]
    print(f"sweep pass windows (b_start): {passes or 'NONE'}")


if __name__ == "__main__":
    main()
