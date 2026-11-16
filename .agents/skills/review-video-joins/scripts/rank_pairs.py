#!/usr/bin/env python3
"""Rank hash-bound, bounded source-frame pairs; no edit or acceptance decision.

rank_pairs.py WORKSPACE RECIPE.json NEW_OUTPUT_DIRECTORY
Recipe and output paths are relative to WORKSPACE. See tools-and-evidence.md.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def local(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Path escapes workspace')
    return path


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}')
    return value


def run(args):
    return subprocess.run(args, check=True, capture_output=True).stdout


def source(root, item, width):
    path = local(root, item['path'])
    if not re.fullmatch(r'[0-9a-f]{64}', item['sha256']) or digest(path) != item['sha256']:
        raise ValueError('Source hash mismatch')
    start = integer(item['startFrame'], 0, 100000000, 'startFrame')
    end = integer(item['endFrameExclusive'], start + 1, start + 240, 'endFrameExclusive')
    probe = json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,avg_frame_rate',
        '-of', 'json', str(path)]))['streams'][0]
    height = max(1, round(width * probe['height'] / probe['width']))
    raw = run(['ffmpeg', '-v', 'error', '-i', str(path), '-an', '-vf',
        f'select=between(n\\,{start}\\,{end - 1}),scale={width}:{height}:flags=area',
        '-fps_mode', 'passthrough', '-pix_fmt', 'rgb24', '-f', 'rawvideo', 'pipe:1'])
    if len(raw) != (end - start) * height * width * 3:
        raise ValueError('Requested range did not decode to the exact frame count')
    rgb = np.frombuffer(raw, dtype=np.uint8).reshape(end - start, height, width, 3)
    gray = np.array([cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY),
                                    (5, 5), 1.0) for f in rgb], dtype=np.float32)
    return rgb, gray, probe


def weights(spec, shape):
    height, width = shape
    regions = spec.get('regions')
    if regions is None:
        return np.ones(shape, np.float32) / (height * width)
    result = np.zeros(shape, np.float32)
    for region in regions:
        box, weight = region['box'], region['weight']
        if (len(box) != 4 or not all(isinstance(v, (int, float)) and np.isfinite(v) for v in box)
                or not 0 <= box[0] < box[2] <= 1 or not 0 <= box[1] < box[3] <= 1
                or not isinstance(weight, (int, float)) or not np.isfinite(weight) or weight <= 0):
            raise ValueError('Invalid normalized region or weight')
        x0, y0, x1, y1 = box
        result[int(y0 * height):int(np.ceil(y1 * height)),
               int(x0 * width):int(np.ceil(x1 * width))] += weight
    if not result.sum() > 0:
        raise ValueError('Regions have no weight')
    return result / result.sum()


def rank(root, recipe, output):
    if output.exists():
        raise FileExistsError(output)
    spec = json.loads(recipe.read_text())
    width = integer(spec.get('proxyWidth', 270), 64, 540, 'proxyWidth')
    top = integer(spec.get('top', 6), 1, 12, 'top')
    separation = integer(spec.get('separation', 7), 1, 240, 'separation')
    ar, a, ap = source(root, spec['from'], width)
    br, b, bp = source(root, spec['to'], width)
    if (ap['width'], ap['height']) != (bp['width'], bp['height']):
        raise ValueError('Sources require matching rasters; prepare explicit derivatives')
    mask = weights(spec, a.shape[1:])
    rows = []
    for ai, frame in enumerate(a):
        scores = np.sum(np.abs(b - frame) * mask, axis=(1, 2))
        rows.extend((float(score), ai, bi) for bi, score in enumerate(scores))
    selected = []
    for score, ai, bi in sorted(rows):
        if all(abs(ai - r['fromOffset']) + abs(bi - r['toOffset']) >= separation for r in selected):
            selected.append({'fromFrame': spec['from']['startFrame'] + ai,
                'toFrame': spec['to']['startFrame'] + bi, 'score': score,
                'fromOffset': ai, 'toOffset': bi})
        if len(selected) == top:
            break
    output.mkdir(parents=True, exist_ok=False)
    height = a.shape[1]
    board = Image.new('RGB', (width * len(selected), (height + 34) * 2), '#1a1a1a')
    draw = ImageDraw.Draw(board)
    for col, row in enumerate(selected):
        for side, frames, offset, name, key in [(0, ar, 'fromOffset', 'A', 'fromFrame'),
                                               (1, br, 'toOffset', 'B', 'toFrame')]:
            x, y = col * width, side * (height + 34)
            board.paste(Image.fromarray(frames[row[offset]]), (x, y))
            draw.text((x + 4, y + height + 3),
                      f"{name} F{row[key]} | delta {row['score']:.3f}", fill='white')
    board.save(output / 'candidates.png')
    receipt = {'schemaVersion': 1, 'recipeSha256': digest(recipe), 'toolSha256': digest(Path(__file__)),
        'method': 'Weighted absolute grayscale difference; Gaussian 5x5 sigma 1; ranking only',
        'proxy': {'width': width, 'height': height}, 'regions': spec.get('regions'),
        'sources': {'from': spec['from'], 'to': spec['to']},
        'sourceProbes': {'from': ap, 'to': bp}, 'pairsCompared': len(rows), 'candidates': selected,
        'artisticApproval': False, 'normalSpeedReview': 'pending', 'audioProcessed': False}
    (output / 'ranking.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'output': str(output.relative_to(root)), 'pairsCompared': len(rows),
                      'candidates': len(selected), 'artisticApproval': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace'); parser.add_argument('recipe'); parser.add_argument('output')
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    rank(workspace, local(workspace, args.recipe), local(workspace, args.output))
