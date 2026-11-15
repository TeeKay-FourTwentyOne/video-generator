#!/usr/bin/env python3
"""Prepare immutable built-in image-tool requests; never submits or prices them."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare(workspace, stage, parent):
    w = Path(workspace)
    refs = [w / 'refs' / f'{parent}.png', w / 'refs' / 'M01-A.png']
    refs = list(dict.fromkeys(refs))
    instructions = {
        2: 'A second weak disturbance has passed. The upper petal opens slightly and the three displaced positions become more legible, with a few new dark interference seams.',
        3: 'The structure opens into deeper translucent overlapping folds. The central hollow seam widens; pearl-white filaments slide against displaced cyan-violet echoes. Its dimensional anatomy remains recognizable.',
        4: 'A stronger disturbance passes through the same shell. Large folds flex and interleave, opening a beautiful dark passage through the center. Coherent fine filament ridges and dark cancellation seams become stronger.',
        5: 'The next disturbance is powerful. The folded shell stretches outward around its central void, with visibly separated overlapping positions and bright concentrated ribs; more tension in the same elegant anatomy.',
        6: 'The membrane is at maximum tension just before detection. The same large folds peel outward from the central black passage, very fine filaments stretched and intense pearlescent edges. Preserve the intricate object; do not collapse it yet.'
    }
    common = f'''Use case: precise-object-edit. Film material milestone {stage} of six.
Image 1 is the selected preceding milestone and exact continuity source. Image 2, when present, is the original anatomy reference.
Preserve the same luminous folded membrane, hollow seam, large sculptural petals, pearlescent white fine filaments, restrained cyan/violet edges and occasional pale gold. Preserve pure black background, portrait composition, object center and overall scale. No typography, stars, scenery or extra objects.
Change only the state of the folds and interference: {instructions[stage]}
This is an evolving material anchor, not a camera zoom: keep the complete object visible and in the same framing. Fine, coherent light filaments and dimensional translucent optical silk, gallery-quality detail. Later motion and actual interference will be computed locally.'''
    for variant, choice in [('A', 'Let the foremost petal open gently toward the left, with a clear continuous diagonal seam.'), ('B', 'Let the foremost petal open gently toward the right, with a clear continuous curved seam.')]:
        rid = f'M{stage:02d}-{variant}'
        prompt = common + '\n' + choice
        (w / 'prompts' / f'{rid}.txt').write_text(prompt + '\n')
        snap = {'schemaVersion': 1, 'evidence': 'creation-snapshot', 'provider': 'OpenAI built-in image_gen',
                'requestId': rid, 'fingerprint': hashlib.sha256((prompt + ''.join(sha(p) for p in refs)).encode()).hexdigest(),
                'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'prompt': prompt,
                'requestedModel': None, 'model': None, 'seed': None,
                'parameters': {'transparent_background': False, 'requestedAspectRatio': '9:16'},
                'sources': [{'role': 'preceding-selected' if i == 0 else 'original-anatomy', 'sha256': sha(p), 'bytes': p.stat().st_size} for i, p in enumerate(refs)],
                'api': 'image_gen.imagegen'}
        target = w / 'operations' / f'{rid}.request.json'
        with target.open('x') as f:
            json.dump(snap, f, indent=2)
        target.chmod(0o400)
    print(json.dumps({'stage': stage, 'refs': [str(p.resolve()) for p in refs]}))


def select(workspace, stage, variant, reason):
    w = Path(workspace)
    path = w / 'selections.json'
    rows = json.loads(path.read_text()) if path.exists() else []
    if any(x['stage'] == stage for x in rows):
        raise ValueError('Selection already recorded; preserve it and make a revision separately.')
    candidates = []
    for v in ['A', 'B']:
        rid = f'M{stage:02d}-{v}'
        p = w / 'refs' / f'{rid}.png'
        snapshot = w / 'operations' / f'{rid}.request.json'
        receipt = {'requestId': rid, 'asset': str(p.relative_to(w)), 'sha256': sha(p),
                   'snapshotFileSha256': sha(snapshot), 'billing': 'not-exposed-by-built-in-tool'}
        target = w / 'operations' / f'{rid}.asset.json'
        with target.open('x') as f:
            json.dump(receipt, f, indent=2)
        candidates.append(receipt)
    rows.append({'stage': stage, 'selected': f'M{stage:02d}-{variant}', 'reason': reason,
                 'parent': rows[-1]['selected'] if rows else None, 'candidates': candidates})
    path.write_text(json.dumps(rows, indent=2) + '\n')
    status_path = Path('briefs/wavefield/status.json')
    status = json.loads(status_path.read_text())
    scene = status['scenes'][stage - 1]
    scene['status'] = 'anchored'
    scene['image'] = f'refs/M{stage:02d}-{variant}.png'
    scene['segments'][0]['status'] = 'anchored'
    status['phase'] = 'anchors'
    status['log'].append({'date': '2026-11-14', 'text': f'M{stage:02d}: selected {variant}. {reason}'})
    status_path.write_text(json.dumps(status, indent=2) + '\n')
    print(json.dumps(rows[-1], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['prepare', 'select'])
    p.add_argument('workspace')
    p.add_argument('stage', type=int)
    p.add_argument('value')
    p.add_argument('reason', nargs='?', default='')
    a = p.parse_args()
    if a.command == 'prepare':
        prepare(a.workspace, a.stage, a.value)
    else:
        select(a.workspace, a.stage, a.value, a.reason)
