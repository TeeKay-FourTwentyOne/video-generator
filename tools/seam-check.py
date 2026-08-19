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

TWO MODES (2026-08-18). The original fixed band 0.60-1.50 answers "is this
join FRAME-EXACT?" — the right question for verifying an edit did not corrupt
anything. It is the WRONG question for a generative join, and the difference
is not academic: measured on real footage, 10.8% of ordinary uncut frame pairs
in s5bv5_swell.mp4 score above 1.50, and 3% score above 1.965 — the score of a
Veo continuation a human reviewer judged clearly acceptable. A fixed band is
content-blind; busy footage naturally exceeds it.

  --mode perceptual (DEFAULT)  Upper photometric bound is derived from the
      material itself: the 99th percentile of the ordinary in-clip RATIO
      distribution, floored at the strict 1.50 so it can only ever widen.
      A seam is FAIL only when it exceeds what the clip's own motion already
      does. Lower bound stays 0.60 — a freeze is wrong at any content level.
      A kinematic-only failure downgrades to MARGINAL rather than FAIL,
      because the stall has a known free repair (trim B's head to where its
      motion energy reaches A's tail).
  --mode strict                Exactly the pre-2026-08-18 behaviour, fixed
      band both channels. Use for regression fixtures and for verifying that
      a pure edit (cut/rejoin/re-encode) introduced nothing.

Usage:
  seam-check.py --at N file.mp4              # seam between frames N-1 and N
  seam-check.py --pair A.mp4:AI B.mp4:BI     # join A's frame AI -> B's frame BI
Options: --mode perceptual|strict  --width 270  --json  --profile-percentile 99
Exit: 0 pass or marginal, 2 usage/decode error, 3 gate fail.

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

# Provisional perceptual ceiling. NOT derived from theory — anchored to the
# only human verdicts this project has, both recorded 2026-08-18 on joins the
# owner watched and judged clearly acceptable ("tiny things, largely
# dismissible"):
#     join-quality  RATIO 2.020  (material's own p99: 1.354)
#     join-fast     RATIO 2.838  (material's own p99: 1.699)
# Both were statistical OUTLIERS against their own footage and were still
# dismissed, which is the whole finding: at 24fps a single-frame delta spike
# is not resolved by the eye until it is large. Human tolerance is wider than
# statistical indistinguishability, so a content-adaptive percentile alone
# does not close the gap — this constant does the rest of the work.
# TWO LABELS IS NOT A CALIBRATION. Widen or narrow as more joins are judged,
# and record each verdict here so the number keeps its provenance.
#
# PERSONAL BEST chain labels (2026-08-19, owner, six chained quality-1080p
# joins watched at 720p; scale CLEAN < DISMISSIBLE < VISIBLE < BROKEN):
#     J1  RATIO 1.035  VR 2.153  close-up stroke, quiet A-tail -> hot open
#         VISIBLE   "a pause where the movement stops then continues"
#     J2  RATIO 1.521  VR 0.515  subject large, rigid wall edge in frame
#         DISMISSIBLE/VISIBLE edge   "another pause, shorter than J1"
#     J3  RATIO 1.097  VR 3.563  pre-reveal content change — read as a HARD
#         CUT (register change + B-side restage hang; fixed by recutting onto
#         the segment's own internal cut; excluded as a gate datum)
#     J4  RATIO 1.595  VR 0.725  flood curtain
#         DISMISSIBLE   "edit almost perfect; hand briefly stops"
#     J5  RATIO 1.130  VR 1.072  whitewater churn        CLEAN  "beautiful"
#     J6  RATIO 1.446  VR 0.587  subject small/distant   CLEAN  "beautiful"
# CALIBRATION FINDING: at photometric RATIO 1.0-1.6 the eye never saw the
# photometric seam — every felt defect tracked the KINEMATIC channel as a
# perceived PAUSE, in BOTH directions of VR, scaled by subject prominence
# (VR 0.52 on a large subject read on-the-edge; VR 0.59 on a small distant
# subject read clean). Working felt-clean kinematic band for a PROMINENT
# subject: VR ~[0.7, 1.4]. The perceptual-mode downgrade of kinematic-only
# failures to MARGINAL is optimistic for close-ups — revisit as labels grow.
PERCEPTUAL_UPPER = 3.0


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


def profile_ratios(path, width, exclude=None):
    """Ordinary in-clip RATIOs for every interior frame pair of ONE clip.

    Scores each adjacent pair exactly the way the gate scores a seam — its
    delta over the median of its own +/-12 neighbours — so the resulting
    distribution is directly comparable to a seam RATIO. This is what makes
    the threshold content-aware: a shot whose own motion routinely spikes to
    2.0 cannot have a 1.9 seam that anyone can see.

    exclude: (lo, hi) frame range to skip, so a seam never pollutes the
    baseline it is about to be judged against.
    """
    frames = decode_frames(path, 0, 10 ** 6, width)
    if len(frames) < 27:
        return []
    d = adjacent_deltas(frames)
    out = []
    for i in range(12, len(d) - 12):
        if exclude and exclude[0] <= i <= exclude[1]:
            continue
        win = d[i - 12:i] + d[i + 1:i + 13]
        med = float(np.median(win))
        if med > 0:
            out.append(d[i] / med)
    return out


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
    ap.add_argument("--mode", choices=("perceptual", "strict"), default="perceptual",
                    help="perceptual (default): upper photometric bound adapts to the "
                         "material's own motion. strict: fixed 0.60-1.50 band, "
                         "pre-2026-08-18 behaviour — use for fixtures and pure edits")
    ap.add_argument("--profile-percentile", type=float, default=99.0,
                    help="perceptual mode: percentile of the clip's own RATIO "
                         "distribution used as the upper bound (default 99)")
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
        # One file holds both sides, so the seam sits inside its own profile —
        # exclude a window around it or it inflates the bound that judges it.
        profile_sources = [(args.video, (n - 13, n + 12))]
    elif args.pair:
        (pa, ai), (pb, bi) = (parse_pair_arg(s) for s in args.pair)
        a_frames = decode_frames(pa, ai - 11, ai, args.width)
        b_frames = decode_frames(pb, bi, bi + 12, args.width)
        label = f"--pair {pa}:{ai} {pb}:{bi}"
        # Separate files: no seam exists inside either, so profile both whole
        # and pool — the join has to live among the motion of both sides.
        profile_sources = [(pa, None), (pb, None)]
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

        upper = RATIO_BAND[1]
        profile_n, profile_p99 = 0, None
        if args.mode == "perceptual":
            pool_r = []
            for path, excl in profile_sources:
                pool_r.extend(profile_ratios(path, args.width, excl))
            profile_n = len(pool_r)
            if profile_n >= 40:
                profile_p99 = float(np.percentile(pool_r, args.profile_percentile))
            # Two independent reasons a seam can be invisible, so take whichever
            # is more permissive: (1) the eye does not resolve a single-frame
            # spike below PERCEPTUAL_UPPER, and (2) busy footage whose own motion
            # exceeds that constant hides even more. Floored at the strict bound
            # so material can only ever EARN tolerance, never lose it.
            upper = max(RATIO_BAND[1], PERCEPTUAL_UPPER, profile_p99 or 0.0)

        photo_fail = not (RATIO_BAND[0] <= ratio <= upper)
        kin_out = not (VR_BAND[0] <= vr <= VR_BAND[1])
        # A stall is real but repairable by trimming B's head, so in perceptual
        # mode it is a warning, not a gate failure. Photometric is the gate.
        kin_fail = kin_out if args.mode == "strict" else False
        marginal = (args.mode == "perceptual"
                    and not photo_fail
                    and (kin_out or ratio > RATIO_BAND[1]))
        fail = photo_fail or kin_fail
        result.update({
            "branch": branch, "mode": args.mode,
            "ratio": round(ratio, 3), "velocity_ratio": round(vr, 3),
            "ratio_band": [RATIO_BAND[0], round(upper, 3)], "vr_band": VR_BAND,
            "strict_ratio_band": RATIO_BAND,
            "profile_pairs": profile_n,
            "profile_p99": round(profile_p99, 3) if profile_p99 is not None else None,
            "kinematic_out_of_band": kin_out,
            "photometric_fail": photo_fail, "kinematic_fail": kin_fail,
            "marginal": marginal, "fail": fail,
        })
        if not args.json:
            print(f"seam-check {label}  (proxy {args.width}px gray, A+B combined baseline, "
                  f"mode={args.mode})")
            if args.mode == "perceptual":
                src = ("this material's own motion" if profile_p99 and profile_p99 > PERCEPTUAL_UPPER
                       else "the provisional perceptual ceiling")
                prof = (f"{profile_p99:.3f} at p{args.profile_percentile:g} over {profile_n} "
                        f"ordinary uncut pairs" if profile_p99 is not None
                        else f"unprofiled ({profile_n} pairs)")
                print(f"UPPER BOUND {upper:.2f} from {src}  "
                      f"[perceptual ceiling {PERCEPTUAL_UPPER:.2f}, material p99 {prof}, "
                      f"frame-exact {RATIO_BAND[1]:.2f}]")
            print(f"CHANNEL A (photometric): seam_delta {seam:.3f}  "
                  f"neighbour_median {med:.3f}  RATIO {ratio:.3f}  "
                  f"[band {RATIO_BAND[0]:.2f}-{upper:.2f}]  "
                  f"{'FAIL' if photo_fail else 'PASS'}")
            print(f"CHANNEL B (kinematic):   base_a {base_a:.3f}  base_b {base_b:.3f}  "
                  f"VELOCITY_RATIO {vr:.3f}  "
                  f"[band {VR_BAND[0]:.2f}-{VR_BAND[1]:.2f}]  "
                  f"{'FAIL' if kin_fail else ('WARN' if kin_out else 'PASS')}")
            print(f"  B head deltas: {' '.join(f'{d:.2f}' for d in head_series)}")
            if kin_out and args.mode == "perceptual":
                print("  → stall detected: trim B's head to where its motion energy "
                      "reaches A's tail (free repair, see extend-clip skill)")

    verdict_bits = []
    if result["photometric_fail"]:
        verdict_bits.append("photometric")
    if result["kinematic_fail"]:
        verdict_bits.append("kinematic")
    if fail:
        verdict = "FAIL (" + "+".join(verdict_bits) + ")"
    elif result.get("marginal"):
        p99 = result.get("profile_p99")
        r = result.get("ratio")
        if p99 is not None and r is not None and r <= p99:
            why = "inside this material's own natural motion"
        else:
            why = ("below the perceptual ceiling — a single-frame spike this size "
                   "is not resolved at 24fps")
        if result.get("kinematic_out_of_band"):
            why = "stall in B's opening; photometrically " + why
        verdict = f"MARGINAL (measurable, not expected to read: {why})"
    else:
        verdict = "PASS"
    result["verdict"] = verdict.split(" (")[0]
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"VERDICT: {verdict}  [branch: {branch}]")
    sys.exit(3 if fail else 0)


if __name__ == "__main__":
    main()
