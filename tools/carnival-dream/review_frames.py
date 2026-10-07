#!/usr/bin/env python3
"""Build start/middle/end strips for every completed shot, without network use."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('--run', type=Path, required=True)
ap.add_argument('--frames', type=Path, required=True)
ap.add_argument('--complete', action='store_true')
args = ap.parse_args()
spec = json.loads((args.run / 'timeline.json').read_text())
dest = args.run / 'qa' / 'motion-strips'
dest.mkdir(parents=True, exist_ok=True)
previous=json.loads((dest/'manifest.json').read_text()) if (dest/'manifest.json').exists() else {}
same_source=previous.get('frame_source')==str(args.frames.resolve())
selected = []
for shot in spec['shots']:
    if not (args.frames / f"frame-{shot['end_frame']-1:05d}.png").exists():
        if args.complete:
            raise RuntimeError('Shot is incomplete: ' + shot['id'])
        continue
    numbers = [round(shot['start_frame'] + f * (shot['end_frame'] - shot['start_frame'] - 1)) for f in [.04, .50, .96]]
    selected.append((shot, numbers))
for offset in range(0, len(selected), 6):
    batch = selected[offset:offset+6]
    path = dest / f'page-{offset//6+1:02d}.jpg'
    # Completed pages need not be rewritten while a long render is running.
    batch_rows=[{'shot':s['id'],'frames':numbers} for s,numbers in batch]
    if same_source and previous.get('rows',[])[offset:offset+6]==batch_rows and path.exists() and len(batch) == 6:
        with Image.open(path) as existing:
            if existing.size == (1200, 6*252):
                continue
    sheet = Image.new('RGB', (1200, len(batch)*252), (16, 16, 23))
    d = ImageDraw.Draw(sheet)
    for row, (shot, numbers) in enumerate(batch):
        label = f"{shot['id']} | {shot['kind']} | {shot['start']:.2f}-{shot['end']:.2f}s"
        d.text((7, row*252+3), label, fill=(240, 230, 219))
        for col, number in enumerate(numbers):
            with Image.open(args.frames / f'frame-{number:05d}.png') as im:
                im = im.resize((400, 225), Image.Resampling.LANCZOS)
                sheet.paste(im, (col*400, row*252+23))
    sheet.save(path, quality=94)
manifest = {'frame_source':str(args.frames.resolve()),'shots_available': len(selected), 'shots_expected': len(spec['shots']),
            'rows': [{'shot': s['id'], 'frames': numbers} for s, numbers in selected]}
if args.complete:
    seen = set()
    for n in range(spec['frames']):
        f = args.frames / f'frame-{n:05d}.png'
        inode = f.stat().st_ino
        if inode in seen:
            continue
        with Image.open(f) as im:
            assert im.size == (1920, 1080)
            im.verify()
        seen.add(inode)
    manifest['native_png_integrity'] = 'pass'
    manifest['unique_images_checked'] = len(seen)
(dest / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'shots_available': len(selected), 'pages': (len(selected)+5)//6, 'integrity': manifest.get('native_png_integrity', 'pending completion')}))
