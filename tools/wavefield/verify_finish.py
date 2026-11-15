#!/usr/bin/env python3
"""Verify full-frame timing, copied sound packets and 4K encoding fidelity."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def probe(file, *args):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', *args,
                                              '-of', 'json', str(file)]))


def verify(workspace):
    root = Path(workspace)
    revision = root / 'revisions/v4-4k'
    qa = revision / 'qa'
    report_path = qa / 'finish-verification.json'
    if report_path.exists():
        raise ValueError('Preserve the existing finish verification.')
    base = root / 'final/v4/film.mp4'
    master = root / 'final/v4-4k/film.mp4'
    counterpart = root / 'edit/picture-v4-4k.mp4'
    delivery = json.loads((master.parent / 'delivery.json').read_text())
    assert sha(master) == delivery['sha256']
    assert sha(base) == delivery['finishing']['baseSha256']
    timing = []
    packets = []
    for path in [base, master]:
        frames = probe(path, '-select_streams', 'v:0', '-show_frames',
                       '-show_entries', 'frame=best_effort_timestamp_time,duration_time')['frames']
        timing.append([(row['best_effort_timestamp_time'], row.get('duration_time')) for row in frames])
        audio = probe(path, '-select_streams', 'a:0', '-show_packets', '-show_data_hash', 'sha256')['packets']
        packets.append([{key: row.get(key) for key in ['pts_time', 'dts_time', 'duration_time',
                                                     'size', 'data_hash', 'side_data_list']}
                        for row in audio])
    assert len(timing[0]) == len(timing[1]) == 720 and timing[0] == timing[1]
    assert packets[0] == packets[1]
    stats = qa / 'finish-ssim.txt'
    args = ['ffmpeg', '-hide_banner', '-nostdin', '-i', str(master), '-i', str(counterpart),
            '-filter_complex', f'[0:v][1:v]ssim=stats_file={stats}', '-an', '-f', 'null', '-']
    with (qa / 'finish-ssim.log').open('w') as log:
        subprocess.run(args, stdout=log, stderr=log, check=True)
    scores = [float(re.search(r'All:([0-9.]+)', line)[1]) for line in stats.read_text().splitlines()]
    assert len(scores) == 720
    mean_score = sum(scores) / len(scores)
    assert mean_score > .99 and min(scores) > .98
    report = {
        'schemaVersion': 1, 'version': 'v4-4k', 'baseVersion': 'v4',
        'masterSha256': delivery['sha256'], 'baseSha256': delivery['finishing']['baseSha256'],
        'width': 2160, 'height': 3840, 'fps': 30, 'frames': 720, 'durationSeconds': 24,
        'allVideoTimestampsEqual': True, 'audioPacketCount': len(packets[0]),
        'allAudioPacketsHashesAndTimestampsEqual': True,
        'gaplessAudioMetadataEqual': True,
        'decodedAudioDigestEqual': delivery['finishing']['audio']['pcmSha256']['base'] ==
                                   delivery['finishing']['audio']['pcmSha256']['output'],
        'ssimAgainstLosslessCounterpart': {'frames': len(scores), 'mean': mean_score,
                                          'minimum': min(scores)},
        'method': 'All-frame temporal comparison, complete AAC packet comparison and full-frame SSIM.',
        'limits': 'Resampling and compression checks do not establish new image detail or human listening.',
    }
    assert report['decodedAudioDigestEqual']
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default='data/workspace/wavefield-v1')
    verify(parser.parse_args().workspace)
