#!/usr/bin/env python3
"""REPEAT's local interface. Source portraits remain untouched.

Preview: render_ui.py preview SOURCE OUTPUT [--font FONT]
The illustrative preview waveform is replaced by measured speech in the edit.
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920
PANEL_Y = 1450
BG = (247, 248, 247)
INK = (40, 48, 49)
MUTED = (112, 124, 125)
ACCENT = (74, 104, 111)
GREEN = (58, 133, 104)


def font_path(explicit=None):
    if explicit:
        return explicit
    for path in (
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ):
        if Path(path).is_file():
            return path
    raise RuntimeError('Provide an installed font using --font')


def interface(phrase, mode='read', sample=1, waveform=None, font=None, mic_on=True):
    """RGBA full-canvas overlay; waveform values are normalized amplitudes."""
    font = font_path(font)
    image = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((0, PANEL_Y, WIDTH, HEIGHT), fill=BG)
    d.line((60, PANEL_Y, WIDTH - 60, PANEL_Y), fill=(220, 226, 225), width=2)
    small = ImageFont.truetype(font, 23)
    label = ImageFont.truetype(font, 27)
    line = ImageFont.truetype(font, 44)
    d.text((64, 1496), 'VOICE SETUP', font=small, fill=MUTED)
    for i in range(3):
        x = 925 + 28 * i
        d.ellipse((x, 1501, x + 9, 1510), fill=ACCENT if i < sample else (211, 219, 218))
    status = {'read': 'Read aloud', 'playback': 'Playback', 'ready': 'Ready to use'}[mode]
    color = GREEN if mode == 'ready' else ACCENT
    if mode == 'ready':
        d.line((63, 1566, 71, 1574, 87, 1557), fill=GREEN, width=4)
    else:
        d.ellipse((65, 1559, 77, 1571), fill=color)
    d.text((99, 1549), status, font=label, fill=color)
    y = 1682
    d.line((65, y, WIDTH - 65, y), fill=(209, 219, 218), width=2)
    amplitudes = waveform if waveform is not None else [0.0] * 97
    count = len(amplitudes)
    for i, amplitude in enumerate(amplitudes):
        x = 65 + (WIDTH - 130) * i / max(1, count - 1)
        half = max(1.5, min(1, abs(amplitude)) * 65)
        d.rounded_rectangle((x - 2, y - half, x + 2, y + half), radius=2, fill=color)
    box = d.textbbox((0, 0), phrase, font=line)
    d.text(((WIDTH - box[2]) / 2, 1790), phrase, font=line, fill=INK)
    d.text((65, 1873), 'MIC ON' if mic_on and mode != 'ready' else 'MIC OFF', font=small, fill=MUTED)
    d.text((940, 1873), f'{sample} / 3', font=small, fill=MUTED)
    return image


def preview(source, output, font=None):
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(output)
    base = Image.open(source).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    wave = [0.6 * math.exp(-((i - 48) / 29) ** 2) *
            (0.25 + 0.75 * abs(math.sin(i * 0.71) * math.cos(i * 0.19))) for i in range(97)]
    overlay = interface('The room is quiet.', waveform=wave, font=font)
    base.paste(overlay, (0, 0), overlay)
    output.parent.mkdir(parents=True, exist_ok=True)
    base.save(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preview'])
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--font')
    args = parser.parse_args()
    preview(args.source, args.output, args.font)
