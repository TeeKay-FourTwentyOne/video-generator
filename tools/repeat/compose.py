#!/usr/bin/env python3
"""Frame-exact REPEAT picture and sound-driven interface, with source receipts.

compose.py WORKSPACE RECIPE OUTPUT.mp4
Recipe: fps, frames, audio, segments and ui. Black segments omit source. All media
paths are workspace relative. No retiming, frame holds or external services.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from render_ui import WIDTH, HEIGHT, PANEL_Y, interface


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def resolve(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Recipe path escapes workspace')
    return path


def read_exact(pipe, size):
    out = bytearray()
    while len(out) < size:
        chunk = pipe.read(size - len(out))
        if not chunk:
            raise EOFError('Source decoded fewer frames than the edit requires')
        out.extend(chunk)
    return bytes(out)


def segment_source(root, segment):
    if segment.get('clipId'):
        cli = Path(__file__).resolve().parents[1] / 'production' / 'clips.mjs'
        result = subprocess.run(['node', str(cli), 'resolve', segment['clipId']],
                                capture_output=True, text=True, check=True)
        return cli.parents[2] / json.loads(result.stdout)['path']
    return resolve(root, segment['source']) if segment.get('source') else None


def compose(root, recipe, output):
    root = Path(root).resolve()
    recipe, output = resolve(root, recipe), resolve(root, output)
    if output.exists():
        raise FileExistsError(output)
    spec = json.loads(recipe.read_text())
    fps, frames = spec['fps'], spec['frames']
    if sum(s['frames'] for s in spec['segments']) != frames:
        raise ValueError('Segment lengths do not match the edit')
    audio = resolve(root, spec['audio'])
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio), '-ar', '48000',
                          '-ac', '1', '-f', 'f32le', 'pipe:1'], capture_output=True, check=True)
    samples = np.frombuffer(pcm.stdout, dtype='<f4')
    # Rolling 0.6-second history. Each bar is the RMS of its own 6.2 ms interval.
    window = 28800
    edges = np.linspace(0, window, 98).astype(int)
    square = np.concatenate(([0.0], np.cumsum(samples.astype(np.float64) ** 2)))
    scale = float(spec.get('waveformGain', 4.5))
    output.parent.mkdir(parents=True, exist_ok=True)
    log_path = output.with_suffix('.encode.log')
    receipt = {'recipeSha256': sha(recipe), 'audioSha256': sha(audio), 'fps': fps,
               'frames': frames, 'segments': [], 'noRetimingOrHeldFrames': True}
    with log_path.open('wb') as log:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-n', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
              '-s', f'{WIDTH}x{HEIGHT}', '-r', str(fps), '-i', 'pipe:0', '-an',
              '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p',
              '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
              '-movflags', '+faststart', str(output)], stdin=subprocess.PIPE, stderr=log)
        at = 0
        try:
            for segment in spec['segments']:
                source = segment_source(root, segment)
                digest = sha(source) if source else None
                if source and segment.get('sha256') != digest:
                    raise ValueError(f'Source changed: {segment.get("clipId", segment.get("source"))}')
                start, length = segment.get('inFrame', 0), segment['frames']
                dec = None
                if source:
                    filters = [f'trim=start_frame={start}:end_frame={start+length}', 'setpts=PTS-STARTPTS']
                    crop = segment.get('crop')
                    if crop:
                        if not all(isinstance(crop.get(k), int) for k in ('x', 'y', 'width', 'height')):
                            raise ValueError('Crop values must be integer pixels')
                        if min(crop['x'], crop['y']) < 0 or min(crop['width'], crop['height']) <= 0:
                            raise ValueError('Invalid crop bounds')
                        if crop['width'] * HEIGHT != crop['height'] * WIDTH:
                            raise ValueError('The crop must preserve the portrait aspect ratio')
                        filters.append(f"crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']}")
                    filters += [f'scale={WIDTH}:{HEIGHT}:flags=lanczos', 'setsar=1']
                    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(source), '-an',
                        '-vf', ','.join(filters),
                        '-frames:v', str(length), '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'],
                        stdout=subprocess.PIPE, stderr=log)
                for j in range(length):
                    f = at + j
                    frame = Image.frombytes('RGB', (WIDTH, HEIGHT), read_exact(dec.stdout, WIDTH*HEIGHT*3)) if dec else Image.new('RGB', (WIDTH, HEIGHT), 'black')
                    state = next((x for x in spec['ui'] if x['startFrame'] <= f < x['endFrameExclusive']), None)
                    if state and source:
                        end = min(len(samples), (f + 1) * 48000 // fps)
                        indices = np.clip(end - window + edges, 0, len(samples))
                        power = (square[indices[1:]] - square[indices[:-1]]) / np.maximum(1, np.diff(indices))
                        amplitudes = np.minimum(1.0, np.sqrt(np.maximum(0, power)) * scale).tolist()
                        overlay = interface(state['phrase'], state.get('mode', 'read'), state.get('sample', 1),
                                            amplitudes, mic_on=state.get('micOn', True))
                        panel = overlay.crop((0, PANEL_Y, WIDTH, HEIGHT)).convert('RGB')
                        frame.paste(panel, (0, PANEL_Y))
                    enc.stdin.write(frame.tobytes())
                if dec:
                    dec.stdout.close()
                    if dec.wait() != 0:
                        raise RuntimeError('Source decode failed')
                receipt['segments'].append({**segment, 'sourceSha256': digest, 'timelineFrame': at})
                at += length
                print(json.dumps({'shot': segment['shotId'], 'renderedFrames': at}), flush=True)
            enc.stdin.close()
            if enc.wait() != 0:
                raise RuntimeError('Picture encode failed; inspect retained log')
        except BaseException:
            enc.kill()
            if 'dec' in locals() and dec and dec.poll() is None:
                dec.kill()
            raise
    for segment in receipt['segments']:
        source = segment_source(root, segment)
        if source and sha(source) != segment['sourceSha256']:
            raise ValueError('Source changed during render')
    receipt['outputSha256'] = sha(output)
    output.with_suffix('.recipe-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'output': str(output.relative_to(root)), 'sha256': receipt['outputSha256'], 'frames': frames}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace')
    parser.add_argument('recipe')
    parser.add_argument('output')
    args = parser.parse_args()
    compose(args.workspace, args.recipe, args.output)
