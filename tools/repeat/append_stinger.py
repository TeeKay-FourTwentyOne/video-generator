#!/usr/bin/env python3
"""Append REPEAT's stinger while preserving the existing main picture and mix.

append_stinger.py sound|join WORKSPACE RECIPE
The private recipe records all source hashes, frame ranges and output paths.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from sound import RATE, audio, filter_audio


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pcm_sha(samples):
    return hashlib.sha256(samples.astype('<f4').tobytes()).hexdigest()


def local(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Path escapes workspace')
    return path


def write_wav(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-n', '-f', 'f32le', '-ar', str(RATE),
                    '-ac', '2', '-i', 'pipe:0', '-c:a', 'pcm_s24le', str(path)],
                   input=samples.astype('<f4').tobytes(), check=True)


def make_sound(root, spec):
    fps = spec['fps']
    if RATE % fps:
        raise ValueError('Frame rate must divide the sample rate')
    spf = RATE // fps
    base_path = local(root, spec['base']['audio'])
    if sha(base_path) != spec['base']['audioSha256']:
        raise ValueError('Base soundtrack changed')
    base = audio(base_path)
    if len(base) != spec['base']['frames'] * spf:
        raise ValueError('Base soundtrack length differs from its frame count')
    tail_frames = spec['stinger']['frames'] + spec['stinger']['blackFrames']
    voice = np.zeros((tail_frames * spf, 2), dtype=np.float32)
    impacts = np.zeros_like(voice)
    v = spec['voice']
    selected = base[v['inFrame'] * spf:(v['inFrame'] + v['frames']) * spf].copy()
    at = v['atFrame'] * spf
    if at + len(selected) > spec['stinger']['frames'] * spf:
        raise ValueError('The pleasant line must finish before final black')
    voice[at:at + len(selected)] = selected
    # Short damped body and skin-contact noise. No music or additional voice.
    rng = np.random.default_rng(spec['foleySeed'])
    for cue in spec['impacts']:
        count = int(0.22 * RATE)
        t = np.arange(count) / RATE
        attack = 1 - np.exp(-t / 0.0013)
        body = np.sin(2 * np.pi * 74 * t) * np.exp(-t / 0.040)
        body += 0.34 * np.sin(2 * np.pi * 163 * t) * np.exp(-t / 0.018)
        noise = rng.normal(0, 1, count) * np.exp(-t / 0.012)
        mono = (body + 0.19 * noise) * attack
        stereo = np.column_stack((mono, mono * 0.86)).astype(np.float32)
        stereo = filter_audio(stereo, 'highpass=f=35,lowpass=f=1400')[:count]
        stereo *= (10 ** (cue['peakDbfs'] / 20)) / np.max(np.abs(stereo))
        stereo[-240:] *= np.linspace(1, 0, 240)[:, None]
        at = cue['frame'] * spf
        if at < 0 or at + len(stereo) > spec['stinger']['frames'] * spf:
            raise ValueError('Impact does not fit the visible stinger')
        impacts[at:at + len(stereo)] += stereo
    tail = voice + impacts
    if np.max(np.abs(tail)) > 10 ** (-1.5 / 20):
        raise ValueError('Tail exceeds the peak ceiling; reduce only the impacts')
    full = np.concatenate((base, tail))
    outputs = {'voice': voice, 'impacts': impacts, 'tailAudio': tail, 'audio': full}
    for key in outputs:
        if local(root, spec['outputs'][key]).exists():
            raise FileExistsError(spec['outputs'][key])
    for key, samples in outputs.items():
        write_wav(local(root, spec['outputs'][key]), samples)
    reread = audio(local(root, spec['outputs']['audio']))
    if not np.array_equal(base, reread[:len(base)]):
        raise ValueError('Prepared main soundtrack changed')
    report = {'toolSha256': sha(__file__), 'baseAudioSha256': sha(base_path), 'basePcmSha256': pcm_sha(base),
              'preservedPrefixPcmSha256': pcm_sha(reread[:len(base)]),
              'baseSamplesPreserved': len(base), 'voiceSelectedPcmSha256': pcm_sha(selected),
              'voiceSource': v, 'impacts': spec['impacts'], 'foleySeed': spec['foleySeed'],
              'realTimeListening': 'not-claimed',
              'outputs': {key: {'path': spec['outputs'][key],
                               'sha256': sha(local(root, spec['outputs'][key]))}
                          for key in outputs}}
    local(root, spec['outputs']['audio']).with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'baseSamplesPreserved': len(base), 'tailFrames': tail_frames,
                      'totalFrames': spec['base']['frames'] + tail_frames}))


def frame_hashes(path, count):
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-an',
                             '-frames:v', str(count), '-f', 'framemd5', 'pipe:1'],
                            check=True, capture_output=True, text=True)
    return [line.split(',')[-1].strip() for line in result.stdout.splitlines()
            if line and not line.startswith('#')]


def join(root, spec):
    base = local(root, spec['base']['film'])
    tail = local(root, spec['stinger']['picture'])
    if sha(base) != spec['base']['sha256'] or sha(tail) != spec['stinger']['pictureSha256']:
        raise ValueError('Picture source changed')
    output = local(root, spec['outputs']['film'])
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    listing = output.parent / 'concat-picture.txt'
    quote = lambda p: str(p).replace("'", "'\\''")
    listing.write_text(f"file '{quote(base)}'\nduration {spec['base']['frames'] / spec['fps']:.12f}\n"
                       f"file '{quote(tail)}'\n")
    frames = spec['base']['frames'] + spec['stinger']['frames'] + spec['stinger']['blackFrames']
    subprocess.run(['ffmpeg', '-v', 'error', '-n', '-f', 'concat', '-safe', '0',
                    '-i', str(listing), '-i', str(local(root, spec['outputs']['audio'])),
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '192k', '-ar', '48000', '-t', str(frames / spec['fps']),
                    '-movflags', '+faststart', str(output)], check=True)
    before, after = frame_hashes(base, spec['base']['frames']), frame_hashes(output, frames)
    if len(before) != spec['base']['frames'] or before != after[:len(before)]:
        raise ValueError('Decoded main picture changed')
    tail_before = frame_hashes(tail, spec['stinger']['frames'] + spec['stinger']['blackFrames'])
    if len(after) != frames or tail_before != after[len(before):]:
        raise ValueError('Tail frame sequence changed during the join')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-f', 'null', '-'], check=True)
    report = {'toolSha256': sha(__file__), 'baseFilmSha256': sha(base), 'tailPictureSha256': sha(tail),
              'outputSha256': sha(output), 'frames': frames, 'fps': spec['fps'],
              'preservedMainFrames': len(before), 'decodedMainFramesIdentical': True,
              'decodedTailFramesIdentical': True,
              'fullDecode': True, 'mainPictureReencoded': False,
              'frameHashesSha256': hashlib.sha256('\n'.join(before).encode()).hexdigest()}
    (output.parent / 'append-preservation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['sound', 'join'])
    parser.add_argument('workspace')
    parser.add_argument('recipe')
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    spec = json.loads(local(root, args.recipe).read_text())
    (make_sound if args.command == 'sound' else join)(root, spec)
