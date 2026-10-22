#!/usr/bin/env python3
"""S7: the empty balcony still with a slow push-in and two phone screens that glow brighter while 'their' voice speaks.
Local, deterministic. usage:
  python3 recipes/phones.py STILL.png OUT.mp4 --frames 240 \
     --phone-a X,Y,RX,RY --phone-b X,Y,RX,RY  (screen centres/radii in STILL pixel coords) \
     --voice-a WAV@FRAME [--voice-a WAV@FRAME ...] --voice-b WAV@FRAME ...  (lines placed at edit frames of this shot) \
     [--zoom 1.06] [--fade-out 20] [--width 1080 --height 1920]
The glow is a soft radial sprite screen-blended over each phone; its strength is a resting level plus the RMS
envelope of the voice placed on that phone. The push-in is a centred scale from 1.0 to --zoom over the shot."""
import argparse, subprocess, numpy as np
from PIL import Image, ImageFilter
ap = argparse.ArgumentParser()
ap.add_argument('still'); ap.add_argument('out'); ap.add_argument('--frames', type=int, default=240)
ap.add_argument('--phone-a', required=True); ap.add_argument('--phone-b', required=True)
ap.add_argument('--voice-a', action='append', default=[]); ap.add_argument('--voice-b', action='append', default=[])
ap.add_argument('--zoom', type=float, default=1.06); ap.add_argument('--fade-out', type=int, default=20)
ap.add_argument('--width', type=int, default=1080); ap.add_argument('--height', type=int, default=1920)
ap.add_argument('--rest', type=float, default=0.22, help='resting glow strength 0..1')
ap.add_argument('--anchor', default='0.5,0.42', help='push-in centre as fractions of width,height')
a = ap.parse_args()
W, H, fps, N = a.width, a.height, 24, a.frames

def envelope(specs):
    """Per-frame 0..1 loudness envelope of the given WAV lines placed at their frames (smoothed, normalised)."""
    env = np.zeros(N, dtype=np.float64)
    for spec in specs:
        wav, at = spec.rsplit('@', 1); at = int(at)
        pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', wav, '-f', 'f32le', '-ac', '1', '-ar', str(fps * 100), '-'],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(pcm, dtype=np.float32)
        n = len(x) // 100
        rms = np.sqrt((x[:n * 100].reshape(n, 100) ** 2).mean(axis=1))
        if rms.max() > 0: rms = rms / rms.max()
        for i, v in enumerate(rms):
            f = at + i
            if 0 <= f < N: env[f] = max(env[f], v)
    # attack fast, release slow (about 6 frames), so the glow breathes instead of flickering
    out = np.zeros_like(env); s = 0.0
    for i, v in enumerate(env):
        s = v if v > s else s * 0.78 + v * 0.22
        out[i] = s
    return np.clip(out, 0, 1)

envA, envB = envelope(a.voice_a), envelope(a.voice_b)

src = Image.open(a.still).convert('RGB')
sw, sh = src.size
# fit the still to the output aspect by scaling to width and centre-cropping height (or the reverse)
scale = max(W / sw, H / sh)
base = src.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
bw, bh = base.size; ox, oy = (bw - W) // 2, (bh - H) // 2
base = base.crop((ox, oy, ox + W, oy + H))
def to_out(px, py):  # still pixel coords -> output coords
    return (px * scale - ox, py * scale - oy)

def sprite(cx, cy, rx, ry, colour=(205, 225, 255)):
    """Soft elliptical glow centred on the screen, about 2.6x the screen size, with a hot core."""
    pad = int(max(rx, ry) * 3.2)
    layer = Image.new('L', (W, H), 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - rx * 2.6, cy - ry * 2.6, cx + rx * 2.6, cy + ry * 2.6), fill=90)
    d.ellipse((cx - rx * 1.4, cy - ry * 1.4, cx + rx * 1.4, cy + ry * 1.4), fill=170)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(max(rx, ry) * 0.9))
    alpha = np.asarray(layer, dtype=np.float32) / 255.0
    col = np.zeros((H, W, 3), dtype=np.float32); col[..., 0], col[..., 1], col[..., 2] = colour
    return alpha, col

def parse(spec):
    x, y, rx, ry = (float(v) for v in spec.split(','))
    cx, cy = to_out(x, y); return cx, cy, rx * scale, ry * scale
glows = [(sprite(*parse(a.phone_a)), envA), (sprite(*parse(a.phone_b)), envB)]
basef = np.asarray(base, dtype=np.float32)
axf, ayf = (float(v) for v in a.anchor.split(','))

def frame(k):
    t = k / max(1, N - 1)
    img = basef.copy()
    for (alpha, col), env in glows:
        s = a.rest + (1 - a.rest) * env[k]
        aa = (alpha * s)[..., None]
        img = img + aa * (255.0 - img) * (col / 255.0)  # screen-like additive glow, tinted
    img = np.clip(img, 0, 255)
    z = 1.0 + (a.zoom - 1.0) * t
    cw, ch = W / z, H / z
    cx, cy = W * axf, H * ayf
    x0 = min(max(cx - cw * axf, 0), W - cw); y0 = min(max(cy - ch * ayf, 0), H - ch)
    im = Image.fromarray(img.astype(np.uint8)).crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
    if a.fade_out and k >= N - a.fade_out:
        fo = (N - 1 - k) / max(1, a.fade_out - 1)
        im = Image.fromarray((np.asarray(im, dtype=np.float32) * fo).astype(np.uint8))
    return np.asarray(im)

p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
for k in range(N): p.stdin.write(frame(k).tobytes())
p.stdin.close(); p.wait(); print(a.out, N, 'frames; envelope peaks A', round(float(envA.max()), 2), 'B', round(float(envB.max()), 2))
