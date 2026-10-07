#!/usr/bin/env python3
"""Rebuild a native Exchange edit from retained Veo clips; no provider calls."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=Path, required=True)
    args = ap.parse_args()
    run = args.run.resolve()
    timeline = json.loads((run / 'timeline.json').read_text())
    out = run / 'edit'
    out.mkdir(exist_ok=True)
    audio = run / 'audio'
    audio.mkdir(exist_ok=True)
    # Explicit still placeholder; no claim of generated motion for this beat.
    still = run / 'clips/EX04-still.mov'
    if not still.exists():
        command(['ffmpeg','-v','error','-n','-loop','1','-i',str(run/'anchors/fascination.png'),'-i',str(run/'clips/EX03.mp4'),'-map','0:v','-map','1:a','-vf','scale=1920:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p','-t','4.5','-c:v','libx264','-crf','16','-preset','fast','-c:a','pcm_s24le',str(still)])
    segments = timeline['segments']
    ff = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n']
    for segment in segments:
        ff += ['-i', str(run / segment['source'])]
    chains = []
    duration = 0
    for i, s in enumerate(segments):
        start, end = s['in'], s['out']
        d = end - start
        crop = f",crop={s['crop']}" if s.get('crop') else ''
        chains.append(f'[{i}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS{crop},scale=1920:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p[v{i}]')
        chains.append(f'[{i}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume={s.get("audio_gain_db",-4)}dB,afade=t=in:d=0.025,afade=t=out:st={d-.04}:d=0.04[a{i}]')
        duration += d
    chains.append(''.join(f'[v{i}][a{i}]' for i in range(len(segments))) + f'concat=n={len(segments)}:v=1:a=1[v][a]')
    master = out / 'exchange-native.mov'
    command(ff + ['-filter_complex', ';'.join(chains), '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-c:a', 'pcm_s24le', str(master)])
    review = out / 'exchange-1080p.mp4'
    command(['ffmpeg','-v','error','-n','-i',str(master),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(review)])
    command(['ffmpeg','-v','error','-n','-i',str(master),'-vf','scale=1280:720','-c:v','libx264','-preset','fast','-crf','22','-c:a','aac','-b:a','128k','-movflags','+faststart',str(out/'exchange-720p.mp4')])
    command(['ffmpeg','-v','error','-n','-i',str(master),'-vn','-c:a','pcm_s24le',str(audio/'exchange-mix.wav')])
    for source in sorted(set(s['source'] for s in segments)):
        command(['ffmpeg','-v','error','-n','-i',str(run/source),'-vn','-c:a','pcm_s24le',str(audio/(Path(source).stem+'-native.wav'))])
    verification = {'expected_duration':duration, 'expected_frames':round(duration*24), 'outputs':[]}
    for file in [master,review,out/'exchange-720p.mp4']:
        probe=json.loads(command(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(file)]))
        video=next(s for s in probe['streams'] if s['codec_type']=='video')
        assert int(video['nb_read_frames'])==round(duration*24)
        assert video['r_frame_rate']=='24/1'
        assert (video['width'],video['height'])==((1280,720) if '720p' in file.name else (1920,1080))
        command(['ffmpeg','-v','error','-i',str(file),'-f','null','-'])
        verification['outputs'].append({'path':str(file.relative_to(run)), 'sha256':hashlib.sha256(file.read_bytes()).hexdigest(), 'probe':probe, 'full_decode':'pass'})
    (run/'qa/verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(f'Exported and verified {duration:.3f}s, {round(duration*24)} frames; native 1080p and 720p review.')

if __name__=='__main__':
    main()
