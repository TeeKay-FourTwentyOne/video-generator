#!/bin/bash
# last-frame.sh — extract the TRUE last frame of a video. The one correct form.
#
#   tools/last-frame.sh input.mp4 out.png
#
# Why this exists: the recipe that circulated in TECHNIQUES.md combined
# `-sseof` with `-frames:v 1`, and `-frames:v 1` OVERRIDES `-update 1` —
# it stops after the FIRST frame inside the sseof window, i.e. a frame
# ~1-12 frames before the end, not the last one. With `-update 1` alone,
# ffmpeg keeps overwriting the output until the stream ends, so the file
# holds the final frame. Verified 2026-08-17 by md5 against
# select=eq(n,N-1): correct form matches exactly; adding -frames:v 1 does not.
#
# Always extract from the RAW generator mp4 — never after normalize-clip,
# which re-encodes and can rescale/crop, so the frame won't match what a
# continuation generation must reproduce.
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "usage: last-frame.sh input.mp4 out.png" >&2
  exit 2
fi

ffmpeg -y -v error -sseof -0.5 -i "$1" -update 1 "$2"

if [ ! -s "$2" ]; then
  echo "last-frame.sh: FAILED — no output written for $1" >&2
  exit 1
fi
