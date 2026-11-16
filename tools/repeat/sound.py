#!/usr/bin/env python3
"""Build REPEAT's frame-addressed soundtrack from its own native voice samples.

The recipe lists tracks with source, inFrame, frames, atFrame, gainDb and an
optional effect: heavy or light. No voice generation or external service.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

RATE = 48000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audio(path):
    result = subprocess.run([
        'ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ar', str(RATE),
        '-ac', '2', '-f', 'f32le', 'pipe:1',
    ], check=True, capture_output=True)
    return np.frombuffer(result.stdout, dtype='<f4').reshape(-1, 2).copy()


def filter_audio(samples, filters):
    result = subprocess.run([
        'ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(RATE), '-ac', '2',
        '-i', 'pipe:0', '-af', filters, '-f', 'f32le', 'pipe:1',
    ], input=samples.astype('<f4').tobytes(), check=True, capture_output=True)
    return np.frombuffer(result.stdout, dtype='<f4').reshape(-1, 2).copy()


def distort(samples, effect):
    """Keep word timing while progressively removing the artificial treatment."""
    if not effect:
        return samples.copy()
    t = np.arange(len(samples)) / RATE
    rms = np.sqrt(np.mean(samples ** 2))
    if effect == 'heavy':
        # Broken narrow-band ring modulation, coarse digital steps, brief dropouts.
        carrier = (0.28 + 0.72 * np.sin(2 * np.pi * 53 * t))[:, None]
        crushed = np.round(np.clip(samples * 4, -1, 1) * 15) / 15
        result = filter_audio(crushed * carrier, 'highpass=f=180,lowpass=f=2300')
        result = result[:len(samples)]
        gate = np.ones(len(result))
        for start in (0.24, 0.53, 0.91, 1.24, 1.61):
            a, b = int(start * RATE), int((start + 0.023) * RATE)
            gate[a:b] = 0.12
        result *= gate[:, None]
    elif effect == 'light':
        result = filter_audio(samples, 'highpass=f=100,lowpass=f=6500')[:len(samples)]
        result *= (0.965 + 0.035 * np.sin(2 * np.pi * 79 * t[:len(result)]))[:, None]
        delay = int(0.008 * RATE)
        result[delay:] += 0.12 * samples[:len(result) - delay]
    else:
        raise ValueError(f'Unknown effect: {effect}')
    out_rms = np.sqrt(np.mean(result ** 2))
    if out_rms > 0:
        result *= rms / out_rms
    return result


def build(workspace, recipe_path, output):
    workspace, recipe_path, output = map(Path, (workspace, recipe_path, output))
    if output.exists():
        raise FileExistsError(output)
    spec = json.loads(recipe_path.read_text())
    fps, frames = spec['fps'], spec['frames']
    if RATE % fps:
        raise ValueError('Frame rate must divide the 48 kHz sample rate')
    spf = RATE // fps
    mix = np.zeros((frames * spf, 2), dtype=np.float64)
    cache, evidence = {}, []
    for index, track in enumerate(spec['tracks']):
        if track.get('clipId'):
            cli = Path(__file__).resolve().parents[1] / 'production' / 'clips.mjs'
            result = subprocess.run(['node', str(cli), 'resolve', track['clipId']], capture_output=True, text=True, check=True)
            source = cli.parents[2] / json.loads(result.stdout)['path']
        else:
            source = workspace / track['source']
        if source not in cache:
            cache[source] = (audio(source), sha(source))
        raw, digest = cache[source]
        if track.get('sha256') and track['sha256'] != digest:
            raise ValueError(f'Source changed: {track.get("clipId", track.get("source"))}')
        start, length = track['inFrame'] * spf, track['frames'] * spf
        segment = raw[start:start + length].copy()
        if len(segment) != length:
            raise ValueError(f'Track {index} exceeds its source')
        input_pcm = hashlib.sha256(segment.astype('<f4').tobytes()).hexdigest()
        segment = distort(segment, track.get('effect'))
        segment *= 10 ** (track.get('gainDb', 0) / 20)
        fade = int(track.get('fadeMs', 0) * RATE / 1000)
        if fade:
            fade = min(fade, len(segment) // 2)
            segment[:fade] *= np.linspace(0, 1, fade)[:, None]
            segment[-fade:] *= np.linspace(1, 0, fade)[:, None]
        at = track['atFrame'] * spf
        if at + len(segment) > len(mix):
            raise ValueError(f'Track {index} exceeds the edit')
        mix[at:at + len(segment)] += segment
        evidence.append({**track, 'sourceSha256': digest, 'inputPcmSha256': input_pcm,
                         'preparedPcmSha256': hashlib.sha256(segment.astype('<f4').tobytes()).hexdigest()})
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(RATE), '-ac', '2',
        '-i', 'pipe:0', '-c:a', 'pcm_s24le', '-n', str(output),
    ], input=mix.astype('<f4').tobytes(), check=True)
    report = {'recipeSha256': sha(recipe_path), 'recipe': str(recipe_path.name),
              'frames': frames, 'fps': fps, 'sampleRate': RATE, 'samples': len(mix),
              'outputSha256': sha(output), 'tracks': evidence,
              'realTimeListening': 'not-claimed'}
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'frames': frames, 'tracks': len(evidence)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace')
    parser.add_argument('recipe')
    parser.add_argument('output')
    args = parser.parse_args()
    build(args.workspace, args.recipe, args.output)
