#!/usr/bin/env python3
"""Assemble and verify the local Borrowed Light review draft without API calls."""
import argparse
import hashlib
import html
import json
import os
import shutil
import subprocess
from pathlib import Path


def command(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def movie_name(spec):
    number=spec.get('draft',1)
    return 'carnival-dream-borrowed-light-draft-1080p.mp4' if number==1 else f'carnival-dream-borrowed-light-draft-{number}-1080p.mp4'


def frames_for_blockout(run, spec, stills):
    dest = run / 'blockout-frames'
    dest.mkdir(exist_ok=True)
    for s in spec['shots']:
        source = stills / (s['id'] + '-' + s['kind'] + '.png')
        if not source.is_file():
            raise RuntimeError('Missing still: ' + source.name)
        for n in range(s['start_frame'], s['end_frame']):
            target = dest / f'frame-{n:05d}.png'
            if not target.exists():
                os.link(source, target)
    return dest


def encode(run, spec, frames, blockout=False):
    review = run / 'review'
    review.mkdir(exist_ok=True)
    output = review / ('carnival-dream-blockout-720p.mp4' if blockout else movie_name(spec))
    if output.exists():
        raise RuntimeError('Preserve the existing export; use a new review directory or remove only the failed export after inspection.')
    expected = [frames / f'frame-{n:05d}.png' for n in range(spec['frames'])]
    if any(not p.is_file() for p in expected):
        raise RuntimeError('Frame sequence has missing frames')
    from PIL import Image
    width, height = Image.open(expected[0]).size
    if not blockout and (width, height) != (1920, 1080):
        raise RuntimeError('Native 1920x1080 frames required; scaling is not permitted')
    fade = f"fade=t=in:st=0:d=0.50,fade=t=out:st={spec['duration']-.80:.9f}:d=0.80,format=yuv420p"
    log = run / 'operations' / ('encode-blockout.log' if blockout else 'encode-final.log')
    with log.open('w') as f:
        command(['ffmpeg', '-hide_banner', '-nostdin', '-n', '-framerate', spec['fps'], '-i', frames / 'frame-%05d.png',
                 '-i', run / spec['audio'], '-map', '0:v:0', '-map', '1:a:0', '-vf', fade,
                 '-c:v', 'libx264', '-preset', 'medium', '-crf', '19' if blockout else '17',
                 '-c:a', 'aac', '-b:a', '320k', '-ar', '44100', '-ac', '2',
                 '-t', f"{spec['duration']:.9f}", '-video_track_timescale', '24000',
                 '-movflags', '+faststart', '-map_metadata', '-1', '-metadata', f"title=Carnival Dream - Borrowed Light - Draft {spec.get('draft',1)}",
                 output], stdout=f, stderr=f)
    return output


def verify(run, spec, output, frames):
    import numpy as np
    info = probe(output)
    vs = [s for s in info['streams'] if s['codec_type'] == 'video']
    aus = [s for s in info['streams'] if s['codec_type'] == 'audio']
    assert len(vs) == 1 and len(aus) == 1 and len(info['streams']) == 2, 'Exactly one picture and one song stream required'
    v, a = vs[0], aus[0]
    assert (v['width'], v['height'], v['avg_frame_rate'], int(v['nb_frames'])) == (1920, 1080, '24/1', spec['frames'])
    assert a['channels'] == 2 and int(a['sample_rate']) == 44100
    assert abs(float(a['duration']) - spec['duration']) < .001
    assert abs(float(v['duration']) - spec['duration']) <= 1 / spec['fps']
    err = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(output), '-f', 'null', '-'], capture_output=True)
    assert err.returncode == 0 and not err.stderr, 'Full decode must be clean'
    def pcm(path):
        b = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path), '-map', '0:a:0', '-f', 'f32le', '-acodec', 'pcm_f32le', '-ar', '44100', '-ac', '2', '-'])
        return np.frombuffer(b, dtype='<f4').reshape(-1, 2)
    source = run / spec['audio']
    original = pcm(source); delivery = pcm(output)
    assert len(delivery) >= len(original) - 1
    n = min(len(original), len(delivery))
    correlations = [float(np.corrcoef(original[:n, c], delivery[:n, c])[0, 1]) for c in range(2)]
    assert min(correlations) > .995, 'Music differs or is shifted'
    windows = []
    for seconds in [0, 30, 60, 90, 120, 160]:
        start = int(seconds * 44100); end = min(n, start + 44100 * 5)
        corr = float(np.corrcoef(original[start:end].ravel(), delivery[start:end].ravel())[0, 1])
        assert corr > .99, 'Local music window differs or is shifted'
        windows.append({'start_s': seconds, 'correlation_at_zero_offset': corr})
    source_record = json.loads((run / 'source.json').read_text())
    assert sha(source) == source_record['sha256'], 'Copied original changed'
    # A decoded PCM music master makes the unretimed source independently inspectable.
    master = run / 'assets' / 'song-decoded-44100hz.wav'
    if not master.exists():
        command(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', source, '-map', '0:a:0', '-c:a', 'pcm_f32le', '-map_metadata', '-1', master])
    assert np.array_equal(original, pcm(master)), 'PCM master must preserve every decoded source sample'
    counts = {'frames': 0, 'unique_rendered_images': 0, 'held_frame_links': 0}
    inodes = set()
    for f in sorted(frames.glob('frame-*.png')):
        counts['frames'] += 1
        inodes.add(f.stat().st_ino)
    counts['unique_rendered_images'] = len(inodes)
    counts['held_frame_links'] = counts['frames'] - len(inodes)
    assert counts['frames'] == spec['frames']
    result = {'status': 'pass', 'full_decode': 'clean', 'video': v, 'audio': a,
              'song_samples': len(original), 'decoded_delivery_samples_with_codec_padding': len(delivery),
              'source_song_duration_s': len(original) / 44100,
              'picture_frame_rounding_s': float(v['duration']) - len(original) / 44100,
              'audio_start_time_s': float(a['start_time']), 'audio_correlation_by_channel': correlations,
              'audio_windows': windows, 'source_copy_sha256': sha(source), 'output_sha256': sha(output),
              'pcm_master_sample_identity': 'exact', 'pcm_master_sha256': sha(master),
              'output_bytes': output.stat().st_size, 'render': counts,
              'audio_policy': 'One full unretimed source song, transcoded to AAC; no added sound or level processing.',
              'visual_review_limit': 'Contact sheets and motion samples are reviewed separately; numerical checks do not establish artistic approval.'}
    (run / 'qa' / 'technical.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def review_page(run, spec, stills=None, frames=None):
    review = run / 'review'
    shot=next(s for s in spec['shots'] if s['id']=='BL35')
    poster = frames/f"frame-{(shot['start_frame']+shot['end_frame'])//2:05d}.png" if frames else stills/'BL35-return_light.png'
    shutil.copy2(poster, review / 'poster.png')
    chapters = [(0, 'Opening'), (15.68, 'The partner'), (42.34, 'First carnival'), (76.08, 'Paper stars'),
                (95.68, 'Three failures'), (124.64, 'Behind the scenery'), (140.64, 'The choice'), (162.8, 'Return')]
    buttons = ''.join(f'<button data-time="{t}"><span>{int(t)//60}:{int(t)%60:02d}</span>{html.escape(label)}</button>' for t, label in chapters)
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carnival Dream — Borrowed Light</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#11121c;color:#eee8e0}*{box-sizing:border-box}body{margin:0 auto;max-width:1250px;padding:32px 24px}header{display:flex;justify-content:space-between;align-items:end;gap:20px}h1{font-family:Georgia,serif;font-size:clamp(28px,4vw,48px);font-weight:400;margin:8px 0}.eyebrow{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:#c5a47e}.subtitle{color:#b9b2c4;margin:6px 0 24px}video{display:block;width:100%;aspect-ratio:16/9;background:black;box-shadow:0 12px 60px #0007}nav{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:24px 0}button{cursor:pointer;text-align:left;font:inherit;color:#e9e2ed;background:#242330;border:1px solid #393343;border-radius:5px;padding:13px}button:hover,button:focus{border-color:#d291ae;background:#302936}button span{display:block;font-size:11px;color:#c9a078;margin-bottom:4px}a{color:#d8a4c3}footer{display:flex;gap:24px;flex-wrap:wrap;color:#aaa2b4;font-size:13px;line-height:1.6}.note{max-width:780px;color:#bdb5c6;font-size:14px;line-height:1.65}@media(max-width:650px){nav{grid-template-columns:repeat(2,1fr)}body{padding:20px 12px}header{display:block}}
</style><header><div><div class="eyebrow">First draft · September 28, 2026</div><h1>Carnival Dream</h1><p class="subtitle">Borrowed Light</p></div></header>
<video id="film" controls preload="metadata" playsinline poster="poster.png"><source src="carnival-dream-borrowed-light-draft-1080p.mp4" type="video/mp4"></video>
<nav aria-label="Film chapters">BUTTONS</nav>
<p class="note">A paper performer, a borrowed partner, and three imperfect attractions. This first draft keeps the full song as its only audio. The paper figures and sets were modeled and animated locally.</p>
<footer><span>1920 × 1080 · 16:9 · 24 fps · Stop motion at 8 poses/sec</span><span>Production API spend: $0 / $30</span><a href="carnival-dream-borrowed-light-draft-1080p.mp4" download>Download the draft</a></footer>
<script>const v=document.getElementById('film');document.querySelectorAll('button[data-time]').forEach(b=>b.addEventListener('click',()=>{v.currentTime=Number(b.dataset.time);v.focus()}));</script></html>'''.replace('BUTTONS', buttons)
    page=page.replace('carnival-dream-borrowed-light-draft-1080p.mp4',movie_name(spec))
    page=page.replace('First draft ·',f"Draft {spec.get('draft',1)} ·")
    if spec.get('draft',1)>1:
        page=page.replace('This first draft','This revision').replace('The paper figures and sets were modeled and animated locally.','The paper figures and sets use local stop motion, with any accepted generated accents recorded in the review notes.')
    budget=json.loads((run/'budget.json').read_text())
    page=page.replace('Production API spend: $0 / $30',f"Generation/API estimate: ${budget.get('external_spend_estimate_usd',0):.2f} / $30")
    (review / 'index.html').write_text(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--frames', type=Path)
    ap.add_argument('--stills', type=Path)
    ap.add_argument('--blockout', action='store_true')
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    run = args.run.resolve(); spec = json.loads((run / 'timeline.json').read_text())
    if args.blockout:
        if args.stills is None:raise RuntimeError('--stills is required for a blockout')
        frames = frames_for_blockout(run, spec, args.stills.resolve())
        print(encode(run, spec, frames, True), flush=True)
        return
    frames = args.frames.resolve()
    output = run / 'review' / movie_name(spec)
    if not args.verify_only:
        output = encode(run, spec, frames)
    result = verify(run, spec, output, frames)
    review_page(run, spec, args.stills.resolve() if args.stills else None, frames)
    shutil.copy2(__file__, run / 'recipe' / 'finish.py')
    print(json.dumps({'status': result['status'], 'movie': str(output), 'audio_correlation': result['audio_correlation_by_channel']}, indent=2))


if __name__ == '__main__':
    main()
