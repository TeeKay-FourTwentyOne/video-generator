#!/usr/bin/env python3
"""POLISH v2: a close, held handset; keyboard excluded by camera geometry.

Uses the retained handset photograph and the original, frame-accurate interface.
No generation, retiming, audio changes or modifications to the original recipe.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw

from render import BG, EVENTS, FPS, FRAMES, H, INK, MUTED, SH, SW, W, label, rr, thumb, ui


def held_ui(t):
    """Keep the exchange exact; compact suggestions above the unseen keyboard."""
    im = ui(t)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 1244, SW, 1439), fill=(25, 30, 36))
    if 2.38 < t < 5.65:
        label(d, (500, 1304), 'terrific', 46, (209, 216, 224), 'mm')
        for x in (295, 705):
            d.line((x, 1271, x, 1334), fill=(57, 64, 74), width=2)
    elif (9.85 < t < 10.8) or (18.55 < t < 24.18) or (26.5 < t < 31.45):
        suggestion = 'In a little while?' if t < 14 else ('I’m fine.' if t < 24.18 else '👍')
        label(d, (87, 1248), 'Suggested', 23, MUTED)
        rr(d, (80, 1277, 920, 1341), (43, 51, 62), 20)
        if suggestion == '👍':
            thumb(d, 474, 1294, .43)
        else:
            label(d, (500, 1308), suggestion, 45, INK, 'mm')
        label(d, (883, 1307), '×', 31, MUTED, 'mm')
    if 19.55 <= t < 31.45:
        label(d, (500, 1361), 'Apply suggestion to send', 27, (177, 185, 195), 'mm')
    return im


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


class HeldRenderer:
    def __init__(self, workspace):
        self.workspace = workspace
        self.plate_path = workspace / 'refs/A01-phone-v1.png'
        self.plate = np.array(Image.open(self.plate_path).convert('RGB').resize((W, H), Image.Resampling.LANCZOS))
        source = np.float32([[0, 0], [SW, 0], [SW, SH], [0, SH]])
        measured = np.float32([[.187, .130], [.805, .128], [.824, .869], [.144, .869]]) * np.array([W, H], np.float32)
        self.plate_hom = cv2.getPerspectiveTransform(source, measured)
        # The warm edge belongs to the handset; the tabletop/contact shadow does not.
        outer = Image.new('L', (SW + 100, SH + 130))
        ImageDraw.Draw(outer).rounded_rectangle((15, 21, SW + 85, SH + 103), radius=109, fill=255)
        to_ui = np.float64([[1, 0, -50], [0, 1, -65], [0, 0, 1]])
        self.body_mask = cv2.warpPerspective(np.array(outer), self.plate_hom @ to_ui, (W, H), flags=cv2.INTER_CUBIC)
        self.body_mask = cv2.GaussianBlur(self.body_mask, (0, 0), .65).astype(np.float32) / 255
        screen_mask = Image.new('L', (SW, SH))
        ImageDraw.Draw(screen_mask).rounded_rectangle((0, 0, SW, SH), radius=83, fill=255)
        self.screen_mask = np.array(screen_mask)
        self.plate_blur = cv2.GaussianBlur(self.plate, (0, 0), 7).astype(np.float32)
        # A distant, defocused room field. No sharp surface under the moving phone.
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        warm = np.exp(-((xx + 150) / 760) ** 2 - ((yy - 200) / 1350) ** 2)
        cool = np.exp(-((xx - 1100) / 900) ** 2 - ((yy - 650) / 1700) ** 2)
        self.background = (np.array([13, 17, 18]) + warm[..., None] * np.array([24, 19, 12]) + cool[..., None] * np.array([1, 7, 8])).astype(np.float32)
        self.grain = np.random.default_rng(421).normal(0, .42, (H, W, 1)).astype(np.float32)
        # Receding upper edge, slight roll, near half of the handset below camera.
        self.base_hom = cv2.getPerspectiveTransform(source, np.float32([[100, 205], [950, 165], [1230, 3115], [-180, 3195]]))
        self.macro_hom = np.eye(3)
        self.macro_hom[:2] = cv2.getRotationMatrix2D((500, 1308), 2, 6.3)
        self.macro_hom[0, 2] += 40
        self.macro_hom[1, 2] -= 78
        self.geometry = []

    def movement(self, t):
        # Independent grip drift, plus damped response to actual finger contacts.
        dx = 3.7 * math.sin(t * 1.11) + 1.9 * math.sin(t * 2.31 + .7)
        dy = 4.0 * math.sin(t * .83 + .3) + 1.3 * math.sin(t * 2.67)
        angle = .20 * math.sin(t * .73) + .075 * math.sin(t * 1.91 + .8)
        for event in EVENTS:
            age = t - event['at']
            if event['kind'] in ('key', 'tap', 'send') and 0 <= age < .48:
                response = math.exp(-age * 13) * math.sin(age * 38)
                strength = 1 if event['kind'] == 'key' else 1.5
                dy += 1.7 * strength * response
                angle += .043 * strength * response
        # An almost imperceptible grip change around the final acceptance.
        dx += 3 * smoothstep((t - 29.8) / 1.2) - 3 * smoothstep((t - 32.3) / 1.1)
        return dx, dy, angle

    def camera(self, t, macro=False):
        dx, dy, angle = self.movement(t)
        m = np.eye(3)
        m[:2] = cv2.getRotationMatrix2D((W * .5, H * .92), angle, 1)
        m[0, 2] += dx
        m[1, 2] += dy
        return m @ (self.macro_hom if macro else self.base_hom)

    def audit_geometry(self, t, hom, macro):
        boundary = cv2.perspectiveTransform(np.float32([[[0, 1440], [1000, 1440]]]), hom)[0]
        # Entire keyboard rectangle lies below the image, including motion extrema.
        keyboard = cv2.perspectiveTransform(np.float32([[[0, 1440], [1000, 1440], [1000, 2000], [0, 2000]]]), hom)[0]
        if keyboard[:, 1].min() <= H + 8:
            raise RuntimeError(f'Keyboard enters camera at {t:.4f}s')
        self.geometry.append({'frame': round(t * FPS), 'macro': macro, 'keyboardMinY': round(float(keyboard[:, 1].min()), 3), 'boundary': boundary.round(3).tolist()})

    def frame(self, t):
        macro = 20.45 <= t < 22.15
        hom = self.camera(t, macro)
        self.audit_geometry(t, hom, macro)
        artwork = np.array(held_ui(t))
        if macro:
            lcd = np.repeat(np.repeat(artwork, 3, axis=0), 3, axis=1).astype(np.float32)
            for k in range(3):
                for channel in range(3):
                    lcd[:, k::3, channel] *= 1.12 if channel == k else .90
            lcd[2::3] *= .77
            out = cv2.warpPerspective(np.clip(lcd, 0, 255).astype(np.uint8), hom @ np.diag([1 / 3, 1 / 3, 1]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
            yy, xx = np.mgrid[0:H, 0:W]
            sharp = np.clip(1 - np.abs(yy - (1190 - .195 * xx)) / 1000, 0, 1)[..., None]
            out = out * sharp + cv2.GaussianBlur(out, (0, 0), 1.7) * (1 - sharp)
        else:
            transfer = hom @ np.linalg.inv(self.plate_hom)
            body = cv2.warpPerspective(self.plate, transfer, (W, H), flags=cv2.INTER_CUBIC).astype(np.float32)
            alpha = cv2.warpPerspective(self.body_mask, transfer, (W, H), flags=cv2.INTER_LINEAR)[..., None]
            screen = cv2.warpPerspective(artwork, hom, (W, H), flags=cv2.INTER_CUBIC).astype(np.float32)
            mask = cv2.warpPerspective(self.screen_mask, hom, (W, H), flags=cv2.INTER_CUBIC).astype(np.float32)[..., None] / 255
            blur = cv2.warpPerspective(self.plate_blur, transfer, (W, H), flags=cv2.INTER_LINEAR)
            surface = screen * .94 + blur * .055 + (body - blur) * .15
            foreground = body * (1 - mask) + surface * mask
            out = self.background * (1 - alpha) + foreground * alpha
        return Image.fromarray(np.clip(out + self.grain, 0, 255).astype(np.uint8))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('workspace', type=Path)
    p.add_argument('--stills', action='store_true')
    p.add_argument('--render')
    a = p.parse_args()
    r = HeldRenderer(a.workspace)
    qa = a.workspace / 'qa/held-v2'
    qa.mkdir(parents=True, exist_ok=True)
    if a.stills:
        for name, t in [('opening', 0), ('autofill', 2.7), ('terrible', 4.9), ('suggestion', 10.1), ('blocked', 20), ('macro', 21), ('thumb', 30.8), ('accepted', 31.6), ('ending', 35.5)]:
            r.frame(t).save(qa / f'{name}.png')
        print(json.dumps({'stills': str(qa)}), flush=True)
    if a.render:
        dest = a.workspace / a.render
        if dest.exists():
            raise SystemExit('Refusing to overwrite render')
        dest.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', str(dest)], stdin=subprocess.PIPE)
        r.geometry = []
        try:
            for f in range(FRAMES):
                proc.stdin.write(np.asarray(r.frame(f / FPS)).tobytes())
                if f % 120 == 0:
                    print(f'{f}/{FRAMES}', flush=True)
        finally:
            proc.stdin.close()
        if proc.wait():
            raise SystemExit('Encoder failed')
        receipt = {'frames': FRAMES, 'fps': FPS, 'width': W, 'height': H, 'output': a.render, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'plateSha256': hashlib.sha256(r.plate_path.read_bytes()).hexdigest(), 'recipeSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'interfaceRecipeSha256': hashlib.sha256(Path(__file__).with_name('render.py').read_bytes()).hexdigest(), 'keyboardLowestClearancePixels': min(x['keyboardMinY'] - H for x in r.geometry), 'cameraChecks': r.geometry, 'method': 'Retained handset isolated from its tabletop, exact local interface, oblique perspective, independent grip and contact movement, all keyboard pixels excluded geometrically; original timing.'}
        (qa / 'render.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({k: v for k, v in receipt.items() if k != 'cameraChecks'}), flush=True)


if __name__ == '__main__':
    main()
