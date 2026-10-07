#!/bin/bash
# Usage: recipes/mix.sh ASTRA.mp4 CLAUDE.mp4 out.wav
set -eu
ffmpeg -v error -y -i "$1" -i "$2" -filter_complex "
[0:a]atrim=0:13.9,asetpts=PTS-STARTPTS,afade=t=out:st=13.5:d=0.4,adelay=8000|8000[a1];
[1:a]atrim=13.5:32.9167,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.4,adelay=21500|21500[a2];
[0:a]atrim=21.0:32.5,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.0,adelay=41500|41500[a3];
[a1][a2][a3]amix=inputs=3:normalize=0:dropout_transition=0,apad=whole_dur=56.5,atrim=0:56.5[out]" \
  -map "[out]" -ar 48000 -ac 2 -c:a pcm_s16le "$3"
