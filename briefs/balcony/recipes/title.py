#!/usr/bin/env python3
"""Render the end card as a silent 24 fps clip: black; the word BALCONY fades in and out. Local only.
usage: python3 recipes/title.py OUT.mp4 [--frames 72] [--width 1080 --height 1920]"""
import argparse, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--frames', type=int, default=72)
ap.add_argument('--width', type=int, default=1080); ap.add_argument('--height', type=int, default=1920); a = ap.parse_args()
W, H, fps = a.width, a.height, 24; SC = W / 1080
serif = '/System/Library/Fonts/Supplemental/Baskerville.ttc'
word = ImageFont.truetype(serif, round(96 * SC), index=0)
def frame(k):
    im = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    a1 = min(1, max(0, (k - 10) / 16)); fo = min(1, max(0, (a.frames - 1 - k) / 16))
    c = int(236 * a1 * fo)
    t = 'B A L C O N Y'; w = d.textlength(t, font=word); d.text(((W - w) / 2, H * 0.44), t, font=word, fill=(c, c, max(0, c - 10)))
    return np.asarray(im)
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
for k in range(a.frames): p.stdin.write(frame(k).tobytes())
p.stdin.close(); p.wait(); print(a.out, a.frames)
