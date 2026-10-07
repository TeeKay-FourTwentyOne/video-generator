#!/usr/bin/env python3
"""Render the available opening only; never fill missing performances with stills."""
import json, subprocess, hashlib, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'data/workspace/hall-of-memories/exchange-dark-video-v1'
def call(args): subprocess.run(args,check=True)
def main():
    edit=RUN/'edit'; edit.mkdir(exist_ok=True)
    parts=json.loads((RUN/'timeline-planned.json').read_text())['segments'][:5]
    graph=[]; inputs=[]
    for i,s in enumerate(parts):
        inputs+=['-i',str(RUN/s['source'])]
        effect='crop=1600:900:160:90,scale=1920:1080,' if i==1 else ''
        graph.append(f"[{i}:v]trim=start={s['in']}:end={s['out']},setpts=PTS-STARTPTS,{effect}fps=24,setsar=1[v{i}]")
        graph.append(f"[{i}:a]atrim=start={s['in']}:end={s['out']},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.008,afade=t=out:st={s['out']-s['in']-.015}:d=0.015[a{i}]")
    graph.append(''.join(f'[v{i}][a{i}]' for i in range(len(parts)))+f'concat=n={len(parts)}:v=1:a=1[v][a]')
    master=edit/'opening-1080p.mov'
    call(['ffmpeg','-v','error','-n',*inputs,'-filter_complex',';'.join(graph),'-map','[v]','-map','[a]','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','pcm_s16le',str(master)])
    for height in (1080,720):
        call(['ffmpeg','-v','error','-n','-i',str(master),'-vf',f'scale=-2:{height}','-c:v','libx264','-crf','20','-c:a','aac','-b:a','192k','-movflags','+faststart',str(edit/f'opening-{height}p.mp4')])
    call(['ffmpeg','-v','error','-n','-i',str(master),'-vn','-c:a','pcm_s16le',str(RUN/'audio/opening-native.wav')])
    (edit/'timeline.json').write_text(json.dumps({'status':'partial opening, missing argument and ending','duration':7.75,'segments':parts},indent=2)+'\n')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in edit.glob('opening-*')}
    (edit/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copy2(__file__,RUN/'recipe/exchange_dark_finish.py')
if __name__=='__main__': main()
