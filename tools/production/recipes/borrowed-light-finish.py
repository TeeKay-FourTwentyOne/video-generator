#!/usr/bin/env python3
"""Local opening/closing polish. Requires the already-installed Pillow and FFmpeg.

Usage: python borrowed-light-finish.py WORKSPACE [--font EXISTING_FONT]
Creates new derived sources and a v2 edit; never replaces originals or v1.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser()
parser.add_argument('workspace', type=Path)
parser.add_argument('--font', type=Path)
args = parser.parse_args()
root = args.workspace
font = args.font or next((p for p in [
    Path('/System/Library/Fonts/Supplemental/Baskerville.ttc'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')
] if p.is_file()), None)
if font is None:
    raise SystemExit('Pass --font with an existing serif font; no fonts are downloaded.')
derived = root / 'edit/polish-v2'
derived.mkdir()
title = Image.new('RGBA', (1080, 1920))
draw = ImageDraw.Draw(title)
face = ImageFont.truetype(str(font), 58)
label = 'BORROWED LIGHT'
tracking = 5
width = sum(draw.textlength(ch, font=face) for ch in label) + (len(label) - 1) * tracking
x = (1080 - width) / 2
for ch in label:
    draw.text((x, 1595), ch, font=face, fill=(239, 225, 191, 255), stroke_width=0)
    x += draw.textlength(ch, font=face) + tracking
title.save(derived / 'title.png')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

records = []
for shot in ['S01', 'S06']:
    source = root / f'clips/{shot}-v1.mp4'
    output = derived / f'{shot}-polished.mp4'
    original = sha(source)
    cmd = ['ffmpeg', '-v', 'error', '-n', '-i', str(source)]
    if shot == 'S01':
        filters = 'fade=t=in:st=0:d=0.333333'
        cmd += ['-vf', filters]
    else:
        filters = '[1:v]format=rgba,fade=t=in:st=3.2:d=1:alpha=1[title];[0:v][title]overlay=0:0:shortest=1,fade=t=out:st=6.7:d=1.25[out]'
        cmd += ['-loop', '1', '-framerate', '24', '-i', str(derived / 'title.png'), '-filter_complex', filters, '-map', '[out]']
    cmd += ['-an', '-frames:v', '192', '-r', '24', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', str(output)]
    subprocess.run(cmd, check=True)
    assert sha(source) == original
    records.append({'shot': shot, 'source': str(source.relative_to(root)), 'sourceSha256': original,
                    'output': str(output.relative_to(root)), 'sha256': sha(output), 'filtergraph': filters})
edit = json.loads((root / 'edit/v1.json').read_text())
for record in records:
    segment = next(s for s in edit['segments'] if s['shotId'] == record['shot'])
    old_decision = json.loads((root / segment['decisionFile']).read_text())
    decision_path = f"qa/{record['shot']}-acceptance-v2.json"
    old_decision.update(sha256=record['sha256'], notes=old_decision['notes'] + ' Derived opening fade or final title/fade; inspect the final review export.')
    (root / decision_path).write_text(json.dumps(old_decision, indent=2) + '\n')
    segment.update(source=record['output'], sha256=record['sha256'], decisionFile=decision_path)
edit['notes'] += ' Local opening fade and final typography/fade; v1 remains available without titles.'
with (root / 'edit/v2.json').open('x') as f:
    json.dump(edit, f, indent=2)
with (derived / 'recipe.json').open('x') as f:
    json.dump({'fontFamily': 'Existing local serif font', 'fontSha256': sha(font), 'title': label, 'records': records}, f, indent=2)
print(json.dumps({'derivedSources': len(records), 'edit': 'edit/v2.json', 'paidRequests': 0}))
