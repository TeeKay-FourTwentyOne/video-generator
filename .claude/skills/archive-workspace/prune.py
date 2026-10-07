#!/usr/bin/env python3
"""Prune a finished workspace to its published 4K version before archiving.

Usage: python3 .claude/skills/archive-workspace/prune.py data/workspace/<slug> --published <version-folder>
       [--also <path-relative-to-workspace> ...] [--apply]

Dry run by default: prints every path it would delete with its size. With --apply it deletes
them and writes archive-prune.log at the workspace root. What it deletes:
  final/<other versions>/            every version folder except --published
  final/<published>/                  per-segment renders, the native export and lower-resolution
                                      or debug copies of the film (segment-*.mp4, film.mp4,
                                      *_1080*.mp4, *_720*.mp4, *debug*.mp4) and upscale*/**/*.mp4
  scratch/                            media (mp4 mov wav aif png jpg jpeg tif gray raw), text kept
  edit/**/*.mp4                       derived segment renders (polished clips); scores/mixes kept
  --also paths                        case-by-case extras (for example mixes that belonged only to
                                      a deleted version); each is logged
It never touches clips/, refs/, frames/, qa/, operations/, prompts/, recipes/, plans or budgets,
and it refuses to run unless the published folder holds a 4K master (*4k*.mp4).
"""
import argparse, datetime, os, sys
MEDIA = {'.mp4', '.mov', '.wav', '.aif', '.aiff', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.gray', '.raw'}
ap = argparse.ArgumentParser(); ap.add_argument('workspace'); ap.add_argument('--published', required=True)
ap.add_argument('--also', nargs='*', default=[]); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
ws = os.path.abspath(a.workspace); final = os.path.join(ws, 'final'); pub = os.path.join(final, a.published)
if not os.path.isdir(pub): sys.exit(f'published version folder not found: {pub}')
if not any('4k' in f.lower() and f.endswith('.mp4') for f in os.listdir(pub)): sys.exit('refusing: no *4k*.mp4 in the published folder')
victims = []
def add(p):
    if os.path.isfile(p): victims.append(p)
for v in sorted(os.listdir(final)):
    d = os.path.join(final, v)
    if os.path.isdir(d) and v != a.published:
        for root, _, files in os.walk(d):
            for f in files: add(os.path.join(root, f))
for root, _, files in os.walk(pub):
    for f in files:
        p = os.path.join(root, f); low = f.lower(); rel = os.path.relpath(root, pub)
        if not low.endswith('.mp4'): continue
        if rel.startswith('upscale'): add(p); continue
        if low.startswith('segment-') or low == 'film.mp4' or '_1080' in low or '_720' in low or 'debug' in low: add(p)
scratch = os.path.join(ws, 'scratch')
if os.path.isdir(scratch):
    for root, _, files in os.walk(scratch):
        for f in files:
            if os.path.splitext(f)[1].lower() in MEDIA: add(os.path.join(root, f))
edit = os.path.join(ws, 'edit')
if os.path.isdir(edit):
    for root, _, files in os.walk(edit):
        for f in files:
            if f.lower().endswith('.mp4'): add(os.path.join(root, f))
for extra in a.also:
    p = os.path.join(ws, extra)
    if not os.path.isfile(p): sys.exit(f'--also path not found: {extra}')
    add(p)
seen = set(); victims = [v for v in victims if not (v in seen or seen.add(v))]
total = 0; lines = []
for p in victims:
    s = os.path.getsize(p); total += s; lines.append(f'{s/1048576:9.1f} MB  {os.path.relpath(p, ws)}')
print('\n'.join(lines)); print(f'{"DELETE" if a.apply else "DRY RUN"}: {len(victims)} files, {total/1048576:.1f} MB, keeping final/{a.published} 4K master')
if a.apply:
    for p in victims: os.remove(p)
    for root, dirs, files in os.walk(final, topdown=False):
        for d in dirs:
            dp = os.path.join(root, d)
            if not os.listdir(dp): os.rmdir(dp)
    with open(os.path.join(ws, 'archive-prune.log'), 'a') as log:
        log.write(f'# pruned {datetime.date.today()} to final/{a.published} (published 4K); {len(victims)} files, {total/1048576:.1f} MB\n')
        log.write('\n'.join(lines) + '\n')
    print('archive-prune.log written')
