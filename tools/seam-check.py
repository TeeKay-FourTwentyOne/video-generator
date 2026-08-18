#!/usr/bin/env python3
"""seam-check.py — two-channel gate for a join between clip A and clip B.

Made for the case where B was generated to CONTINUE A (the join point is known
a priori by construction). Reports two channels SEPARATELY, never blended:

  CHANNEL A (photometric)  RATIO = seam_delta / median(neighbour deltas)
      Catches: dropped frame, duplicate frame, hard cut, translation jump.
  CHANNEL B (kinematic)    VELOCITY_RATIO = base_b / base_a
      Catches: Veo restarting from rest — B opens at a fraction of A's tail
      velocity and ramps over ~12 frames. This stall lives in B's INTERIOR,
      not at the boundary pair, so PSNR, splice.cjs's score and anchor-drift
      are all structurally blind to it. A frozen duplicate frame scores
      PERFECT on any one-sided photometric metric; that is why the
      photometric band is two-sided and the kinematic channel exists.

Metric: mean absolute difference between adjacent frames, 8-bit grayscale,
270px-wide proxy — the exact proxy the 2026-08-17 calibration values were
measured with. (--width 540 available as a cross-check; recalibrate expected
values if you change it.)

Baseline convention (stated because it changes absolute values): neighbour
deltas are pooled from BOTH sides of the seam — every adjacent delta in the
decoded window except the seam pair itself: 11 A-side + 12 B-side deltas
("A+B combined" baseline). An A-only baseline yields different absolute
RATIOs (e.g. 1.98/1.14/1.92 vs 1.64/0.94/1.59 on the same sweep); the ARGMIN
over a sweep is invariant to the convention, the numbers are not. Calibrated
2026-08-17: --at 96 on s5bv5_swell.mp4 = seam 6.932 / median 6.267 / RATIO
1.106 with exactly this convention at 270px.

Near-static branch: when the pooled neighbour median falls below
--static-floor (default 0.5), a relative ratio is numerically meaningless
(dividing by noise), so the gate fails on ABSOLUTE seam delta instead
(--static-abs-fail, default 2.0) and reports which branch fired.

Usage:
  seam-check.py --at N file.mp4              # seam between frames N-1 and N
  seam-check.py --pair A.mp4:AI B.mp4:BI     # join A's frame AI -> B's frame BI
Options: --width 270  --json
Exit: 0 pass, 2 usage/decode error, 3 gate fail.

Windows: --at decodes frames N-12..N+12 of one file. --pair decodes A's
frames AI-11..AI (12 frames, 11 deltas) and B's frames BI..BI+12 (13 frames,
12 deltas). base_a / base_b are medians over 11 pairs each (B's 12th delta is
printed in the head series and included in the photometric baseline only).
"""
import argparse
import json
import subprocess
import sys

import numpy as np

RATIO_BAND = (0.6, 1.5)
VR_BAND = (0.5, 2.0)


def die(msg, code=2):
    print(f"seam-check: {msg}", file=sys.stderr)
    sys.exit(code)


_frame_size_cache = {}


def ffmpeg_gray_pipe(path, sel, width):
    cmd = [
        "ffmpeg", "-v", "error", "-i", path,
        "-vf", f"select={sel},scale={width}:-2,format=gray",
        "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        die(f"ffmpeg failed on {path}: {p.stderr.decode(errors='replace').strip()}")
    return p.stdout


def frame_size(path, width):
    key = (path, width)
    if key not in _frame_size_cache:
        data = ffmpeg_gray_pipe(path, r"eq(n\,0)", width)
        if not data:
            die(f"could not decode frame 0 of {path}")
        _frame_size_cache[key] = len(data)
    return _frame_size_cache[key]


def decode_frames(path, start, end, width):
    """Frames start..end inclusive (start clamped to 0) as float32 vectors."""
    start = max(0, start)
    data = ffmpeg_gray_pipe(path, rf"between(n\,{start}\,{end})", width)
    fsize = frame_size(path, width)
    if fsize == 0 or len(data) % fsize:
        die(f"decode size mismatch on {path}: {len(data)} bytes, frame={fsize}")
    n = len(data) // fsize
    return [
        np.frombuffer(data[i * fsize:(i + 1) * fsize], np.uint8).astype(np.float32)
        for i in range(n)
    ]


def delta(f1, f2):
    return float(np.mean(np.abs(f1 - f2)))


def adjacent_deltas(frames):
    return [delta(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]


def parse_pair_arg(s):
    path, _, idx = s.rpartition(":")
    if not path or not idx.isdigit():
        die(f"bad --pair argument {s!r}, want file.mp4:FRAMEINDEX")
    return path, int(idx)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?", help="video file (with --at)")
    ap.add_argument("--at", type=int, metavar="N",
                    help="seam between frames N-1 and N of VIDEO")
    ap.add_argument("--pair", nargs=2, metavar=("A.mp4:AI", "B.mp4:BI"),
                    help="join: A's frame AI (last of A) -> B's frame BI (first of B)")
    ap.add_argument("--width", type=int, default=270,
                    help="proxy width (default 270; calibration values assume 270)")
    ap.add_argument("--static-floor", type=float, default=0.5,
                    help="pooled median below this = near-static branch (default 0.5)")
    ap.add_argument("--static-abs-fail", type=float, default=2.0,
                    help="near-static branch: fail if seam delta exceeds this (default 2.0)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.at is not None:
        if not args.video:
            die("--at requires a video file argument")
        n = args.at
        if n < 2:
            die("--at needs N >= 2 to form a window")
        frames = decode_frames(args.video, n - 12, n + 12, args.width)
        n_a = n - max(0, n - 12)  # frames before the seam actually decoded
        a_frames = frames[:n_a]
        b_frames = frames[n_a:]
        label = f"--at {n} {args.video}"
    elif args.pair:
        (pa, ai), (pb, bi) = (parse_pair_arg(s) for s in args.pair)
        a_frames = decode_frames(pa, ai - 11, ai, args.width)
        b_frames = decode_frames(pb, bi, bi + 12, args.width)
        label = f"--pair {pa}:{ai} {pb}:{bi}"
    else:
        die("need --at N file.mp4 or --pair A.mp4:AI B.mp4:BI")

    if len(a_frames) < 2 or len(b_frames) < 2:
        die(f"window too small: {len(a_frames)} A-side / {len(b_frames)} B-side frames")

    a_deltas = adjacent_deltas(a_frames)          # up to 11
    b_deltas = adjacent_deltas(b_frames)          # up to 12
    seam = delta(a_frames[-1], b_frames[0])

    # A+B combined baseline: every window delta except the seam (11 A + 12 B).
    pool = a_deltas[-11:] + b_deltas[:12]
    med = float(np.median(pool))
    base_a = float(np.median(a_deltas[-11:]))
    base_b = float(np.median(b_deltas[:11]))
    head_series = b_deltas[:12]

    result = {
        "target": label,
        "width": args.width,
        "baseline_convention": "A+B combined, seam excluded, 11 A-side + 12 B-side deltas",
        "seam_delta": round(seam, 3),
        "neighbour_median": round(med, 3),
        "base_a": round(base_a, 3),
        "base_b": round(base_b, 3),
        "b_head_deltas": [round(d, 2) for d in head_series],
    }

    if med < args.static_floor:
        branch = "near-static"
        fail = seam > args.static_abs_fail
        result.update({
            "branch": branch, "ratio": None, "velocity_ratio": None,
            "abs_fail_threshold": args.static_abs_fail,
            "photometric_fail": fail, "kinematic_fail": False, "fail": fail,
        })
        if not args.json:
            print(f"seam-check {label}  (proxy {args.width}px gray, A+B combined baseline)")
            print(f"BRANCH: near-static (neighbour median {med:.3f} < "
                  f"{args.static_floor} — relative ratio meaningless; gating on "
                  f"ABSOLUTE seam delta)")
            print(f"CHANNEL A (photometric): seam_delta {seam:.3f}  "
                  f"[abs limit {args.static_abs_fail}]  "
                  f"{'FAIL' if fail else 'PASS'}")
            print(f"CHANNEL B (kinematic):   base_a {base_a:.3f}  base_b {base_b:.3f}  "
                  f"(not gated in near-static branch)")
            print(f"  B head deltas: {' '.join(f'{d:.2f}' for d in head_series)}")
    else:
        branch = "relative"
        ratio = seam / med
        vr = base_b / max(base_a, 1e-6)
        photo_fail = not (RATIO_BAND[0] <= ratio <= RATIO_BAND[1])
        kin_fail = not (VR_BAND[0] <= vr <= VR_BAND[1])
        fail = photo_fail or kin_fail
        result.update({
            "branch": branch,
            "ratio": round(ratio, 3), "velocity_ratio": round(vr, 3),
            "ratio_band": RATIO_BAND, "vr_band": VR_BAND,
            "photometric_fail": photo_fail, "kinematic_fail": kin_fail, "fail": fail,
        })
        if not args.json:
            print(f"seam-check {label}  (proxy {args.width}px gray, A+B combined baseline)")
            print(f"CHANNEL A (photometric): seam_delta {seam:.3f}  "
                  f"neighbour_median {med:.3f}  RATIO {ratio:.3f}  "
                  f"[band {RATIO_BAND[0]:.2f}-{RATIO_BAND[1]:.2f}]  "
                  f"{'FAIL' if photo_fail else 'PASS'}")
            print(f"CHANNEL B (kinematic):   base_a {base_a:.3f}  base_b {base_b:.3f}  "
                  f"VELOCITY_RATIO {vr:.3f}  "
                  f"[band {VR_BAND[0]:.2f}-{VR_BAND[1]:.2f}]  "
                  f"{'FAIL' if kin_fail else 'PASS'}")
            print(f"  B head deltas: {' '.join(f'{d:.2f}' for d in head_series)}")

    verdict_bits = []
    if result["photometric_fail"]:
        verdict_bits.append("photometric")
    if result["kinematic_fail"]:
        verdict_bits.append("kinematic")
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"VERDICT: {'FAIL (' + '+'.join(verdict_bits) + ')' if fail else 'PASS'}"
              f"  [branch: {branch}]")
    sys.exit(3 if fail else 0)


if __name__ == "__main__":
    main()
