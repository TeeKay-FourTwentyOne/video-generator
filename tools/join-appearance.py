#!/usr/bin/env python3
"""Measure a subject's appearance on both sides of a cut.

For a cut at edit frame N this decodes frames N-1 and N at full resolution,
crops the same region from each (for example a jacket or a head of hair) and
reports mean luma, mean chroma and fine-texture energy. A same-scene cut on the
same subject should measure close on all three; a take whose anchor came back
darker, greyer or coarser shows up here before it shows up at 4K.

Fine-texture energy is the standard deviation of (luma - luma blurred by a
2-pixel Gaussian). It rises with sharpening and visible weave, and falls with
softening.

    python tools/join-appearance.py FILM.mp4 1660 --crop 0.25,0.55,0.75,0.9
    python tools/join-appearance.py FILM.mp4 1660 1881 --crop 0.3,0.1,0.7,0.3 --json

The crop is left,top,right,bottom as fractions of the frame. Pick a region the
subject fills on both sides; when the framing changes across the cut, pass
--crop-b for the incoming side. The thresholds are a prompt to look, not a
verdict: inspect the crops (--save DIR) before deciding anything.

Needs ffmpeg, NumPy and Pillow (the provisioned analysis Python has both).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter


def frame(film, index):
    """Decode one frame by index as an RGB image, exact (no seeking by time)."""
    out = subprocess.run(
        ['ffmpeg', '-nostdin', '-v', 'error', '-i', film, '-vf', f'select=eq(n\\,{index})',
         '-vsync', '0', '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
        capture_output=True, check=True).stdout
    if not out:
        raise SystemExit(f'No frame {index} in {film}')
    from io import BytesIO
    return Image.open(BytesIO(out)).convert('RGB')


def crop(image, box):
    w, h = image.size
    l, t, r, b = box
    return image.crop((round(l * w), round(t * h), round(r * w), round(b * h)))


def measure(region):
    ycc = np.asarray(region.convert('YCbCr'), dtype=np.float32)
    luma = region.convert('L')
    y = np.asarray(luma, dtype=np.float32)
    blur = np.asarray(luma.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
    return {
        'luma': round(float(ycc[..., 0].mean()), 2),
        'cb': round(float(ycc[..., 1].mean()), 2),
        'cr': round(float(ycc[..., 2].mean()), 2),
        'texture': round(float((y - blur).std()), 2),
    }


def parse_box(text):
    box = [float(v) for v in text.split(',')]
    if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
        raise argparse.ArgumentTypeError('crop is left,top,right,bottom in 0..1')
    return box


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('film')
    ap.add_argument('cuts', type=int, nargs='+', help='edit frame N of each cut (first frame of the incoming shot)')
    ap.add_argument('--crop', type=parse_box, required=True, help='region on the outgoing side (and both sides by default)')
    ap.add_argument('--crop-b', type=parse_box, help='region on the incoming side when the framing differs')
    ap.add_argument('--luma', type=float, default=6.0, help='flag a mean luma difference above this (levels of 255)')
    ap.add_argument('--chroma', type=float, default=3.0, help='flag a mean Cb or Cr difference above this')
    ap.add_argument('--texture', type=float, default=0.15, help='flag a relative texture difference above this fraction')
    ap.add_argument('--save', help='directory for the cropped regions (PNG)')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    results = []
    for n in args.cuts:
        if n < 1:
            raise SystemExit('A cut frame must be at least 1')
        a = crop(frame(args.film, n - 1), args.crop)
        b = crop(frame(args.film, n), args.crop_b or args.crop)
        if args.save:
            os.makedirs(args.save, exist_ok=True)
            a.save(os.path.join(args.save, f'cut{n}-out-f{n - 1}.png'))
            b.save(os.path.join(args.save, f'cut{n}-in-f{n}.png'))
        ma, mb = measure(a), measure(b)
        delta = {
            'luma': round(mb['luma'] - ma['luma'], 2),
            'cb': round(mb['cb'] - ma['cb'], 2),
            'cr': round(mb['cr'] - ma['cr'], 2),
            'textureRatio': round(mb['texture'] / ma['texture'], 3) if ma['texture'] else None,
        }
        flags = []
        if abs(delta['luma']) > args.luma:
            flags.append('luma')
        if max(abs(delta['cb']), abs(delta['cr'])) > args.chroma:
            flags.append('chroma')
        if delta['textureRatio'] is not None and abs(delta['textureRatio'] - 1) > args.texture:
            flags.append('texture')
        results.append({'cut': n, 'outgoing': ma, 'incoming': mb, 'delta': delta, 'look': flags})

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
    else:
        for r in results:
            a, b, d = r['outgoing'], r['incoming'], r['delta']
            print(f"cut {r['cut']}: luma {a['luma']} -> {b['luma']} ({d['luma']:+}), "
                  f"Cb {d['cb']:+}, Cr {d['cr']:+}, texture {a['texture']} -> {b['texture']} (x{d['textureRatio']})"
                  + (f"  LOOK: {', '.join(r['look'])}" if r['look'] else '  within thresholds'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
