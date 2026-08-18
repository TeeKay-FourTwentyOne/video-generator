#!/bin/bash
# run-fixtures.sh — regenerate the five seam defect cases from clips already on
# disk and validate tools/seam-check.py against manifest.json. Fully offline,
# zero API calls, zero generation spend. Safe to run any time.
#
# Cases (all seamed at frame 96 of a 96+96 split):
#   clean    frame-exact rejoin           -> must PASS  (editing stack is neutral)
#   dup      duplicate frame at the seam  -> must FAIL  (RATIO <= 0.10; one-sided
#            PSNR-style gates score this defect as PERFECT — that is the point)
#   drop     dropped frame at the seam    -> must FAIL  (RATIO >= 1.7)
#   hardcut  unrelated clip after seam    -> must FAIL  (RATIO >= 20)
#   shift12  pure 12px translation        -> must FAIL  (geometric jump)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
BUILD="$HERE/build"
mkdir -p "$BUILD"

find_clip() {
  for p in "$REPO/data/workspace/hz-paradise/clips/$1" \
           "$REPO/data/workspace-archive/hz-paradise/clips/$1"; do
    if [ -f "$p" ]; then echo "$p"; return 0; fi
  done
  echo "run-fixtures: source clip $1 not found in workspace or workspace-archive" >&2
  return 1
}

SRC="$(find_clip s5bv5_swell.mp4)"
HC="$(find_clip s6v5_trapdoor.mp4)"

seg() { # seg <input> <select-expr> <extra-vf-or-empty> <out>
  local vf="select='$2'"
  [ -n "$3" ] && vf="$vf,$3"
  ffmpeg -y -v error -i "$1" -vf "$vf" -vsync 0 -an \
    -c:v libx264 -preset fast -crf 18 "$4"
}

join() { # concat-filter rejoin (the container-safe route; concat demuxer -c copy
         # corrupts r_frame_rate to 120/1 when audio is interleaved)
  ffmpeg -y -v error -i "$1" -i "$2" -filter_complex \
    "[0:v]setpts=PTS-STARTPTS,fps=24,settb=AVTB,setsar=1[v0];[1:v]setpts=PTS-STARTPTS,fps=24,settb=AVTB,setsar=1[v1];[v0][v1]concat=n=2:v=1:a=0[v]" \
    -map "[v]" -c:v libx264 -preset fast -crf 18 "$3"
}

echo "regenerating fixtures into $BUILD ..."
seg "$SRC" 'lt(n\,96)'  ""                                     "$BUILD/A1.mp4"
seg "$SRC" 'gte(n\,96)' ""                                     "$BUILD/seg2_clean.mp4"
seg "$SRC" 'gte(n\,95)' ""                                     "$BUILD/seg2_dup.mp4"
seg "$SRC" 'gte(n\,97)' ""                                     "$BUILD/seg2_drop.mp4"
seg "$HC"  'lt(n\,96)'  ""                                     "$BUILD/seg2_hardcut.mp4"
seg "$SRC" 'gte(n\,96)' 'pad=iw+12:ih:12:0:black,crop=1080:1920:0:0' "$BUILD/seg2_shift12.mp4"

for c in clean dup drop hardcut shift12; do
  join "$BUILD/A1.mp4" "$BUILD/seg2_$c.mp4" "$BUILD/fx_$c.mp4"
done

python3 - "$HERE" "$REPO" <<'PYEOF'
import json, subprocess, sys
here, repo = sys.argv[1], sys.argv[2]
manifest = json.load(open(f"{here}/manifest.json"))
failures = []
for case in manifest["cases"]:
    name = case["name"]
    clip = f"{here}/build/fx_{name}.mp4"
    frames = int(subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", clip],
        capture_output=True, text=True).stdout.strip())
    p = subprocess.run(
        ["python3", f"{repo}/tools/seam-check.py", "--at",
         str(manifest["seam_frame"]), clip, "--json"],
        capture_output=True, text=True)
    r = json.loads(p.stdout)
    probs = []
    if frames != case["frames"]:
        probs.append(f"frames {frames} != {case['frames']}")
    if p.returncode != case["expect_exit"]:
        probs.append(f"exit {p.returncode} != {case['expect_exit']}")
    ratio = r.get("ratio")
    if "ratio_min" in case and (ratio is None or ratio < case["ratio_min"]):
        probs.append(f"RATIO {ratio} < {case['ratio_min']}")
    if "ratio_max" in case and (ratio is None or ratio > case["ratio_max"]):
        probs.append(f"RATIO {ratio} > {case['ratio_max']}")
    status = "OK  " if not probs else "FAIL"
    print(f"{status} {name:8s} frames={frames} exit={p.returncode} "
          f"RATIO={ratio} VR={r.get('velocity_ratio')} seam={r.get('seam_delta')}"
          + ("   <-- " + "; ".join(probs) if probs else ""))
    if probs:
        failures.append(name)
if failures:
    print(f"\nFIXTURE REGRESSION: {', '.join(failures)}")
    sys.exit(1)
print("\nall 5 fixtures validated against manifest.json")
PYEOF
