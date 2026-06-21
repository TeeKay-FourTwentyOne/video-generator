#!/bin/bash
# Composite full-hour zones + mux full audio bed -> final hour.
set -e
cd /Users/stephenpadgett/Projects/video-generator
S=data/workspace/the-other-window/scratch
F=data/workspace/the-other-window/final

echo "[composite] full-hour mirror composite (locked rect 1712,96,516,694)…"
ffmpeg -y -v error -i $S/full_fg.mp4 -i $S/full_mw.mp4 -loop 1 -i $S/glass_overlay_v2.png \
 -filter_complex "[0:v]scale=2560:1440,setsar=1[room];[1:v]scale=516:694:force_original_aspect_ratio=increase,crop=516:694,eq=brightness=-0.03:saturation=0.92,gblur=sigma=0.6,setsar=1[world];[room][world]overlay=1712:96[base];[base][2:v]overlay=0:0,format=yuv420p[out]" \
 -map "[out]" -t 3600 -r 24 -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p $S/full_silent.mp4

echo "[encode] mux audio + final params…"
ffmpeg -y -v error -i $S/full_silent.mp4 -i $S/full_bed.m4a \
 -c:v libx264 -preset slow -crf 20 -tune film -g 48 -keyint_min 48 -sc_threshold 0 \
 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest \
 $F/the_other_window_v1_1440.mp4

echo "DONE: $F/the_other_window_v1_1440.mp4"
ls -la $F/the_other_window_v1_1440.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -show_entries format=duration -of default=nw=1 $F/the_other_window_v1_1440.mp4