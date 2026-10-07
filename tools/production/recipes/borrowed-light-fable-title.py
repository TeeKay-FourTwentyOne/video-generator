#!/usr/bin/env python3
"""End title card for Borrowed Light: black field, warm amber serif, fade in/hold/fade out.
Local PIL + FFmpeg only; uses an installed system font, never downloads one.
Usage: python3 recipes/title.py clips/T01.mp4 [frames=72]
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
W, H, FPS = 1080, 1920, 24
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 72
FONT = '/System/Library/Fonts/Supplemental/Baskerville.ttc'
font = ImageFont.truetype(FONT, 108, index=0)
small = ImageFont.truetype(FONT, 40, index=0)
AMBER = (232, 184, 116)
def draw_tracked(d, text, y, f, fill, track):
    widths = [d.textlength(c, font=f) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill); x += w + track
with tempfile.TemporaryDirectory() as tmp:
    base = Image.new('RGB', (W, H), (0, 0, 0))
    card = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(card)
    draw_tracked(d, 'Borrowed Light', H * 0.44, font, AMBER, 6)
    for i in range(N):
        fi, fo = 16, 22
        a = min(1.0, i / fi) if i < fi else (min(1.0, (N - 1 - i) / fo) if i > N - 1 - fo else 1.0)
        a = a * a * (3 - 2 * a)
        frame = Image.blend(base, card, a)
        frame.save(os.path.join(tmp, f'f{i:04d}.png'))
    subprocess.run(['ffmpeg', '-v', 'error', '-n', '-framerate', str(FPS), '-i', os.path.join(tmp, 'f%04d.png'), '-frames:v', str(N),
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                    '-colorspace', 'bt709', '-r', str(FPS), out], check=True)
    Image.blend(base, card, 1.0).resize((270, 480)).save(out.rsplit('.', 1)[0] + '-preview.png')
print('ok', out, N)
