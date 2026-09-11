"""Recolour only the masked hair pixels of B_deck, leaving every other pixel byte-identical.

Works in HSV so V carries the original brushwork untouched — we scale value, shift hue to
brown and ease saturation. That keeps every stroke, ridge of impasto and canvas thread
exactly where the painter put it; only the colour of those strokes changes.
"""
from PIL import Image
import numpy as np

def rgb_to_hsv(a):
    r, g, b = a[...,0], a[...,1], a[...,2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-8
    rm = nz & (mx == r); gm = nz & (mx == g) & ~rm; bm = nz & (mx == b) & ~rm & ~gm
    h[rm] = ((g-b)[rm]/d[rm]) % 6
    h[gm] = ((b-r)[gm]/d[gm]) + 2
    h[bm] = ((r-g)[bm]/d[bm]) + 4
    h = h/6.0
    s = np.where(mx > 1e-8, d/np.maximum(mx,1e-8), 0.0)
    return np.dstack([h, s, mx])

def hsv_to_rgb(a):
    h, s, v = a[...,0], a[...,1], a[...,2]
    i = np.floor(h*6.0); f = h*6.0 - i
    p_ = v*(1-s); q = v*(1-f*s); t = v*(1-(1-f)*s)
    i = (i.astype(np.int32) % 6)
    r = np.select([i==0,i==1,i==2,i==3,i==4,i==5],[v,q,p_,p_,t,v])
    g = np.select([i==0,i==1,i==2,i==3,i==4,i==5],[t,v,v,q,p_,p_])
    b = np.select([i==0,i==1,i==2,i==3,i==4,i==5],[p_,p_,t,v,v,q])
    return np.dstack([r,g,b])


Image.MAX_IMAGE_PIXELS = None
im = Image.open('options/B_deck.png').convert('RGB'); W, H = im.size
X0, X1 = int(0.275*W), int(0.395*W)
Y0, Y1 = int(0.275*H), int(0.475*H)

full = np.asarray(im, dtype=np.float32)/255.0
mask = np.load('scratch/hair_mask2.npy')          # soft, ROI-sized
roi  = full[Y0:Y1, X0:X1].copy()

hsv = rgb_to_hsv(roi)
h_, s_, v_ = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]

TARGET_H = 0.045      # ~16 deg, cool brown
V_SCALE  = 0.42       # darken; relative variation (the brushwork) is preserved
S_SCALE  = 0.80

h2 = np.full_like(h_, TARGET_H)
s2 = np.clip(s_*S_SCALE, 0, 1)
v2 = np.clip(v_*V_SCALE, 0, 1)

new = hsv_to_rgb(np.dstack([h2, s2, v2]))
m = mask[:,:,None]
roi_out = roi*(1-m) + new*m

out = full.copy()
out[Y0:Y1, X0:X1] = roi_out
res = (np.clip(out,0,1)*255).astype(np.uint8)
Image.fromarray(res).save('revisions/B_darkhair_manual.png')

# prove the untouched area is byte-identical
orig = np.asarray(im, dtype=np.uint8)
changed = (res != orig).any(axis=2)
outside = changed.copy(); outside[Y0:Y1, X0:X1] = False
print('changed pixels total: %d' % changed.sum())
print('changed pixels OUTSIDE the head ROI: %d' % outside.sum())
print('ROI changed: %.1f%% of ROI' % (100*changed[Y0:Y1,X0:X1].mean()))
