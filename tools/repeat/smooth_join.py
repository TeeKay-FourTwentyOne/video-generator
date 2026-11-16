#!/usr/bin/env python3
"""Render short bidirectional optical-flow bridges between reviewed source frames.

smooth_join.py WORKSPACE RECIPE OUTPUT.mp4
The output packs the bridges consecutively. Native performances and audio are
not retimed; the editor places these few in-between frames in silent gaps.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

WIDTH, HEIGHT = 1080, 1920


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Path escapes workspace')
    return path


def endpoint(root, item):
    cli = Path(__file__).resolve().parents[1] / 'production' / 'clips.mjs'
    resolved = subprocess.run(['node', str(cli), 'resolve', item['clipId']],
                              check=True, capture_output=True, text=True)
    source = cli.parents[2] / json.loads(resolved.stdout)['path']
    if sha(source) != item['sha256']:
        raise ValueError('Source hash mismatch')
    if not isinstance(item['frame'], int) or item['frame'] < 0:
        raise ValueError('Invalid endpoint frame')
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-an',
                             '-vf', f"select=eq(n\\,{item['frame']}),scale={WIDTH}:{HEIGHT}",
                             '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', 'pipe:1'],
                            check=True, capture_output=True)
    return np.frombuffer(result.stdout, dtype=np.uint8).reshape(HEIGHT, WIDTH, 3)


def render(root, recipe, output):
    spec = json.loads(recipe.read_text())
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    flow_size = (540, 960)
    yy, xx = np.mgrid[:HEIGHT, :WIDTH].astype(np.float32)
    receipt = {'recipeSha256': sha(recipe), 'toolSha256': sha(__file__),
               'method': 'OpenCV DIS bidirectional dense flow, endpoint warps and linear blend',
               'flowSize': list(flow_size), 'fps': spec['fps'], 'bridges': [],
               'audioProcessed': False, 'artisticApproval': False}
    log = output.with_suffix('.encode.log').open('wb')
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-n', '-f', 'rawvideo',
        '-pix_fmt', 'rgb24', '-s', f'{WIDTH}x{HEIGHT}', '-r', str(spec['fps']), '-i', 'pipe:0',
        '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '0', '-pix_fmt', 'yuv420p',
        '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
        '-movflags', '+faststart', str(output)], stdin=subprocess.PIPE, stderr=log)
    at = 0
    try:
        for item in spec['bridges']:
            n = item['frames']
            if not isinstance(n, int) or not 1 <= n <= 12:
                raise ValueError('Bridge must contain 1 to 12 frames')
            a, b = endpoint(root, item['from']), endpoint(root, item['to'])
            ga, gb = [cv2.cvtColor(cv2.resize(x, flow_size, interpolation=cv2.INTER_AREA),
                                  cv2.COLOR_RGB2GRAY) for x in (a, b)]
            dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
            ab = cv2.resize(dis.calc(ga, gb, None), (WIDTH, HEIGHT)) * 2
            ba = cv2.resize(dis.calc(gb, ga, None), (WIDTH, HEIGHT)) * 2
            for j in range(n):
                t = (j + 1) / (n + 1)
                wa = cv2.remap(a, xx - t * ab[..., 0], yy - t * ab[..., 1],
                               cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
                wb = cv2.remap(b, xx - (1 - t) * ba[..., 0], yy - (1 - t) * ba[..., 1],
                               cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
                frame = np.clip(np.rint(wa.astype(np.float32) * (1 - t) +
                                       wb.astype(np.float32) * t), 0, 255).astype(np.uint8)
                enc.stdin.write(frame.tobytes())
            receipt['bridges'].append({**item, 'inFrame': at,
                'fromRgbSha256': hashlib.sha256(a.tobytes()).hexdigest(),
                'toRgbSha256': hashlib.sha256(b.tobytes()).hexdigest()})
            at += n
            print(json.dumps({'bridge': item['id'], 'frames': n, 'totalFrames': at}), flush=True)
        enc.stdin.close()
        if enc.wait() != 0:
            raise RuntimeError('Bridge encode failed')
    except BaseException:
        enc.kill()
        raise
    finally:
        log.close()
    receipt.update({'frames': at, 'outputSha256': sha(output)})
    output.with_suffix('.recipe-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace'); p.add_argument('recipe'); p.add_argument('output')
    args = p.parse_args(); root = Path(args.workspace).resolve()
    render(root, local(root, args.recipe), local(root, args.output))
