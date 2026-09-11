"""Isolate the hair by region-growing INSIDE the painting's own black contour lines.

Beckmann's heavy black outlines are a gift here: the head silhouette and the hairline
are both closed dark strokes, so a flood fill seeded in the hair is bounded by the
drawing itself — no ellipse guessing, no bleeding into the warm dune behind her.
"""
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
im = Image.open('options/B_deck.png').convert('RGB'); W, H = im.size
X0, X1 = int(0.275*W), int(0.395*W)
Y0, Y1 = int(0.275*H), int(0.475*H)
roi = im.crop((X0, Y0, X1, Y1))
a = np.asarray(roi, dtype=np.float32)
h, w = a.shape[:2]
r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
mx = a.max(axis=2)

# Passable = hair-ish paint: not a black contour, not the pale face planes, warm.
barrier_dark  = mx < 78          # black contour strokes
barrier_light = mx > 226         # white/cream face + rail
warm          = (r - b) > 22
# The hairline stroke is not fully closed — the ochre cheek shading runs straight
# into the hair. Guard the face interior explicitly so a leak cannot cross into it.
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
nx_, ny_ = xx/w, yy/h
face_guard = (((nx_-0.60)/0.30)**2 + ((ny_-0.70)/0.32)**2) <= 1.0

passable = (~barrier_dark) & (~barrier_light) & warm & (~face_guard)

lab, n = ndimage.label(passable)
print('components:', n)

# Seeds placed inside the hair masses (normalised ROI coords), read off hair_roi.png
seeds = [(0.52,0.20), (0.42,0.24), (0.62,0.22), (0.30,0.32), (0.24,0.45),
         (0.22,0.60), (0.28,0.72), (0.72,0.30), (0.78,0.42), (0.36,0.17)]
keep = set()
for nx, ny in seeds:
    l = lab[int(ny*h), int(nx*w)]
    if l: keep.add(l)
print('seed components kept:', sorted(keep))

mask = np.isin(lab, list(keep)).astype(np.float32)
# close pinholes where a stroke of highlight broke the region
mask = ndimage.binary_closing(mask > 0.5, structure=np.ones((9,9))).astype(np.float32)
mask = ndimage.binary_fill_holes(mask > 0.5).astype(np.float32)
# drop anything that leaked as a thin thread
mask = ndimage.binary_opening(mask > 0.5, structure=np.ones((5,5))).astype(np.float32)
print('coverage: %.1f%%' % (100*mask.mean()))

soft = np.asarray(Image.fromarray((mask*255).astype(np.uint8))
                  .filter(ImageFilter.GaussianBlur(2.5)), dtype=np.float32)/255.0
np.save('scratch/hair_mask2.npy', soft)

vis = a.copy()
vis[:,:,0] = np.clip(vis[:,:,0]*(1-soft) + 255*soft, 0, 255)
vis[:,:,2] = np.clip(vis[:,:,2]*(1-soft) + 255*soft, 0, 255)
Image.fromarray(vis.astype(np.uint8)).save('scratch/hair_mask2_vis.png')
