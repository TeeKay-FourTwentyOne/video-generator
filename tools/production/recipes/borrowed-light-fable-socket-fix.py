#!/usr/bin/env python3
"""S06 continuity repair (deterministic, local): Veo re-lit the machine's empty chest socket
mid-take and the socket drifts as the body turns. Track the lit disc per frame by its orange
signature and paste the dark socket from frame 0 at the tracked position with luminance matching;
darken the small stray light in the far doorway. Streams frames through FFmpeg pipes.
Usage: python3 recipes/s06-fix.py clips/S06-v1.mp4 clips/S06-v1-fixed.mp4 scratch/S06-fix-proof.png
"""
import subprocess, sys, json
import numpy as np
from PIL import Image
src, dst, proof = sys.argv[1:4]
W, H, FPS = 1080, 1920, 24
SOCKET0 = (813, 1358)            # dark socket centre in frame 0
R_FULL, R_FEATHER = 44, 58       # patch radius: full inside, feathered to zero
SEARCH = (640, 1240, 960, 1470)  # x0,y0,x1,y1 region where the disc can be
DOOR = (575, 1140, 10, 18)       # stray doorway light: centre, inner radius, outer radius

def disc_mask(r_full, r_feather):
    yy, xx = np.mgrid[-r_feather:r_feather + 1, -r_feather:r_feather + 1]
    d = np.sqrt(xx ** 2 + yy ** 2)
    m = np.clip((r_feather - d) / (r_feather - r_full), 0, 1)
    return (m ** 1.5)[..., None]

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709',
                        '-color_trc', 'bt709', '-colorspace', 'bt709', dst], stdin=subprocess.PIPE)
mask = disc_mask(R_FULL, R_FEATHER)
prev = SOCKET0
door_mask = None
patch = None; ref_annulus = None
log = []; proof_tiles = []
n = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
    if n == 0:
        cx, cy = SOCKET0
        patch = f[cy - R_FEATHER:cy + R_FEATHER + 1, cx - R_FEATHER:cx + R_FEATHER + 1].copy()
        yy, xx = np.mgrid[-R_FEATHER:R_FEATHER + 1, -R_FEATHER:R_FEATHER + 1]
        ann = (np.sqrt(xx ** 2 + yy ** 2) > 48) & (np.sqrt(xx ** 2 + yy ** 2) <= 58)
        ref_annulus = patch[ann].mean()
        ref_side = f[cy - 10:cy + 11, cx - 85:cx - 65].mean()
        prev = (cx, cy)
        dx, dy, ri, ro = DOOR
        yy2, xx2 = np.mgrid[0:H, 0:W]
        dd = np.sqrt((xx2 - dx) ** 2 + (yy2 - dy) ** 2)
        door_mask = np.clip((ro - dd) / (ro - ri), 0, 1)[..., None]
    out = f.copy()
    # --- track the socket ring by gradient votes (works lit or dark) over the whole machine
    # region, with a distance prior toward the previous position and a bounded per-frame jump.
    px, py = prev
    x0, y0, x1, y1 = 620, 1230, 980, 1480
    lum = f[y0:y1, x0:x1].mean(axis=2)
    gy, gx = np.gradient(lum)
    mag = np.hypot(gx, gy)
    strong = mag > np.percentile(mag, 92)
    ys, xs = np.nonzero(strong)
    ux, uy = gx[ys, xs] / (mag[ys, xs] + 1e-6), gy[ys, xs] / (mag[ys, xs] + 1e-6)
    acc = np.zeros(lum.shape)
    for r in (27, 30, 33, 36):
        for sgn in (1, -1):
            vx = np.round(xs + sgn * r * ux).astype(int); vy = np.round(ys + sgn * r * uy).astype(int)
            ok = (vx >= 0) & (vx < acc.shape[1]) & (vy >= 0) & (vy < acc.shape[0])
            np.add.at(acc, (vy[ok], vx[ok]), mag[ys[ok], xs[ok]])
    from numpy.lib.stride_tricks import sliding_window_view
    k = 7; pad = np.pad(acc, k // 2, mode='edge')
    sm = sliding_window_view(pad, (k, k)).mean(axis=(2, 3))
    gyy, gxx = np.mgrid[0:sm.shape[0], 0:sm.shape[1]]
    prior = np.exp(-((gxx + x0 - px) ** 2 + (gyy + y0 - py) ** 2) / (2 * 45.0 ** 2))
    iy, ix = np.unravel_index(np.argmax(sm * prior), sm.shape)
    centre = (int(ix) + x0, int(iy) + y0)
    jump = float(np.hypot(centre[0] - px, centre[1] - py))
    if jump > 12:
        centre = (int(round(px + 12 * (centre[0] - px) / jump)), int(round(py + 12 * (centre[1] - py) / jump)))
    prev = centre
    cx, cy = centre
    # Paste only when the disc is actually lit: orange core inside the tracked circle refines the centre.
    yy3, xx3 = np.mgrid[cy - 45:cy + 46, cx - 45:cx + 46]
    inside = (xx3 - cx) ** 2 + (yy3 - cy) ** 2 <= 45 ** 2
    reg = f[cy - 45:cy + 46, cx - 45:cx + 46]
    core = inside & (reg[..., 0] - reg[..., 2] > 50) & (reg[..., 0] > 120) & (reg[..., 1] > 55)
    count = int(core.sum())
    lit = count > 40
    if lit:
        # strong core: refine on the lit pixels; weak (dimming) core: trust the ring detector
        if count >= 120: cy2, cx2 = int(round(yy3[core].mean())), int(round(xx3[core].mean()))
        else: cy2, cx2 = cy, cx
        region = out[cy2 - R_FEATHER:cy2 + R_FEATHER + 1, cx2 - R_FEATHER:cx2 + R_FEATHER + 1]
        if region.shape == patch.shape:
            side = out[cy2 - 10:cy2 + 11, cx2 - 85:cx2 - 65].mean()
            gain = float(np.clip(side / max(ref_side, 1), 0.8, 1.25))
            region[:] = region * (1 - mask) + np.clip(patch * gain, 0, 255) * mask
        centre = (cx2, cy2)
    # --- darken the stray doorway light
    out = out * (1 - door_mask * 0.75)
    log.append({'frame': n, 'orangeCore': count, 'lit': bool(lit), 'centre': centre})
    if n in (0, 48, 96, 144, 168, 191):
        from PIL import ImageDraw
        b = Image.fromarray(f[1150:1500, 560:1000].astype(np.uint8)); dr = ImageDraw.Draw(b)
        dr.ellipse((cx - 560 - 34, cy - 1150 - 34, cx - 560 + 34, cy - 1150 + 34), outline=(0, 255, 0), width=2)
        before = b.resize((220, 175))
        after = Image.fromarray(out[1150:1500, 560:1000].astype(np.uint8)).resize((220, 175))
        proof_tiles.append((before, after))
    enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    n += 1
enc.stdin.close(); enc.wait(); dec.wait()
sheet = Image.new('RGB', (220 * len(proof_tiles), 350))
for i, (b, a) in enumerate(proof_tiles):
    sheet.paste(b, (i * 220, 0)); sheet.paste(a, (i * 220, 175))
sheet.save(proof)
patched = [l for l in log if l['lit']]
json.dump({'frames': n, 'patchedFrames': len(patched), 'firstPatched': patched[0]['frame'] if patched else None,
           'lastPatched': patched[-1]['frame'] if patched else None, 'track': log}, open(dst.rsplit('.', 1)[0] + '.fix.json', 'w'), indent=1)
print(json.dumps({'frames': n, 'patchedFrames': len(patched), 'range': [patched[0]['frame'], patched[-1]['frame']] if patched else None}))
