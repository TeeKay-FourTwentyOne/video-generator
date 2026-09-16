#!/usr/bin/env python3
"""Verify or rebuild a compact Scary Woods production archive without overwriting it."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Archive file points outside the archive')
    return path


def verify(root):
    manifest = json.loads((root / 'archive-manifest.json').read_text())
    for item in manifest['files']:
        path = inside(root, item['path'])
        if not path.is_file() or path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError(f"Archive verification failed: {item['path']}")
    print(f"Verified {len(manifest['files'])} retained files.", flush=True)
    return json.loads((root / 'rebuild/recipe.json').read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--mode', choices=['verify', 'rebuild-1080', 'upscale-4k'], default='verify')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.archive.resolve()
    recipe = verify(root)
    if args.mode == 'verify':
        return
    if args.output is None:
        parser.error('--output is required for rendering')
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(root):
        parser.error('Choose a new output path outside the preserved archive')
    output.parent.mkdir(parents=True, exist_ok=True)
    approved = inside(root, recipe['approved1080'])
    if args.mode == 'upscale-4k':
        method = recipe.get('upscaleMethod', 'realesrgan')
        if method == 'lanczos':
            subprocess.run([
                'ffmpeg', '-hide_banner', '-nostdin', '-n', '-i', str(approved),
                '-map', '0:v:0', '-map', '0:a?', '-map', '0:s?', '-map_metadata', '0',
                '-vf', 'scale=iw*2:ih*2:flags=lanczos,setsar=1',
                '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                '-fps_mode', 'passthrough', '-c:a', 'copy', '-c:s', 'copy',
                '-movflags', '+faststart', str(output),
            ], check=True)
            return
        if method != 'realesrgan':
            parser.error('Unsupported archive upscale method')
        package = importlib.util.find_spec('realesrgan_ncnn_py')
        if package is None:
            parser.error('Use the local upscale Python environment; see the archive README')
        models = Path(package.origin).parent / 'models'
        for item in recipe['modelWeights']:
            if digest(models / item['name']) != item['sha256']:
                raise ValueError('Installed upscaler weights differ from the retained model')
        subprocess.run([sys.executable, str(inside(root, recipe['upscaler'])), str(approved),
                        str(output), '--scale', '2', '--model', '1', '--tile', '256', '--crf', '16'], check=True)
        return
    cues = json.loads(inside(root, recipe['cues']).read_text())
    command = ['ffmpeg', '-hide_banner', '-nostdin', '-n',
               '-i', str(inside(root, recipe['cleanPicture'])), '-i', str(approved)]
    for cue in cues:
        command += ['-loop', '1', '-framerate', '24', '-i',
                    str(inside(root, recipe['overlays']) / f"cue-{cue['id']:02d}.png")]
    filters, previous = [], '0:v'
    for i, cue in enumerate(cues, 2):
        start, end = (cue['startFrame'] - .25) / 24, (cue['endFrame'] - .25) / 24
        label = f'caption{i}'
        filters.append(f"[{previous}][{i}:v]overlay=0:0:enable='gte(t,{start:.9f})*lt(t,{end:.9f})':eof_action=pass[{label}]")
        previous = label
    filters.append(f'[{previous}]format=yuv420p[video]')
    command += ['-filter_complex_threads', '1', '-filter_complex', ';'.join(filters),
                '-map', '[video]', '-map', '1:a:0', '-map', '1:s?', '-frames:v', str(recipe['frames']),
                '-t', str(recipe['durationSeconds']), '-r', '24', '-c:v', 'libx264',
                '-preset', 'medium', '-crf', '17', '-threads', '4', '-c:a', 'copy', '-c:s', 'copy',
                '-map_metadata', '-1', '-movflags', '+faststart', str(output)]
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
