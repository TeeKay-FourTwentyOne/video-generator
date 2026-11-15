#!/usr/bin/env python3
"""Prepare an immutable lossless 4K counterpart for the maintained finisher."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

FILTER = 'scale=2160:3840:flags=lanczos+accurate_rnd+full_chroma_int:in_range=tv:out_range=tv,setsar=1'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main(workspace):
    root = Path(workspace)
    revision = root / 'revisions/v4-4k'
    source = root / 'edit/picture-v3.mp4'
    output = root / 'edit/picture-v4-4k.mp4'
    request = revision / 'upscale-request.json'
    receipt = revision / 'upscale-receipt.json'
    if any(path.exists() for path in [output, request, receipt]):
        raise ValueError('Preserve the existing upscale attempt.')
    base = json.loads((root / 'final/v4/delivery.json').read_text())
    expected_source = base['edit']['segments'][0]['sha256']
    assert sha(source) == expected_source
    args = ['ffmpeg', '-hide_banner', '-nostdin', '-n', '-i', str(source),
            '-map', '0:v:0', '-an', '-sn', '-dn', '-vf', FILTER,
            '-fps_mode', 'passthrough', '-c:v', 'libx264', '-preset', 'medium',
            '-crf', '0', '-pix_fmt', 'yuv420p', '-threads', '8',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-color_range', 'tv', '-movflags', '+faststart', str(output)]
    evidence = {'schemaVersion': 1, 'createdAt': datetime.now(timezone.utc).isoformat(),
                'source': str(source.relative_to(root)), 'sourceSha256': expected_source,
                'baseFilmSha256': base['sha256'], 'output': str(output.relative_to(root)),
                'recipeSha256': sha(__file__), 'filter': FILTER, 'argv': args,
                'ffmpegVersion': subprocess.check_output(['ffmpeg', '-version'], text=True).splitlines()[0],
                'scope': 'Local spatial upscale; no temporal interpolation, sound change or provider calls.'}
    request.write_text(json.dumps(evidence, indent=2) + '\n')
    with (revision / 'qa/upscale-ffmpeg.log').open('w') as log:
        subprocess.run(args, check=True, stdout=log, stderr=log)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
        '-show_streams', '-show_format', '-of', 'json', str(output)]))
    video = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    assert (video['width'], video['height'], video['avg_frame_rate'], int(video['nb_read_frames'])) == (2160, 3840, '30/1', 720)
    assert all(video.get(key) == 'bt709' for key in ['color_space', 'color_transfer', 'color_primaries'])
    assert video['color_range'] == 'tv' and sha(source) == expected_source
    result = {'schemaVersion': 1, 'output': str(output.relative_to(root)), 'sha256': sha(output),
              'sourceSha256': expected_source, 'width': 2160, 'height': 3840,
              'fps': 30, 'frames': 720, 'durationSeconds': 24, 'probe': probe,
              'method': '2x Lanczos in limited-range BT.709; lossless H.264 counterpart',
              'checks': {'fullFrameCount': True, 'dimensions': True, 'colorTags': True, 'sourceUnchanged': True}}
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'probe'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default='data/workspace/wavefield-v1')
    main(parser.parse_args().workspace)
