#!/usr/bin/env python3
"""Inspect retained Exchange clips, preserving every automated flag for review."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'data/workspace/hall-of-memories/exchange-dark-video-v1'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('shot');args=ap.parse_args()
    plan=json.loads((RUN/'plan.json').read_text())
    shot=next(s for s in plan['shots'] if s['id']==args.shot)
    clip=RUN/f"clips/{shot['id']}.mp4";q=RUN/'qa';id=shot['id']
    if not clip.exists():raise SystemExit('No source clip; never substitute a still silently.')
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(clip)]))
    (q/f'{id}-probe.json').write_text(json.dumps(probe,indent=2)+'\n')
    with (q/f'{id}-technical.log').open('w') as log:
        subprocess.run(['ffmpeg','-hide_banner','-i',str(clip),'-vf','blackdetect=d=0.1:pix_th=0.1,freezedetect=n=-50dB:d=0.5','-af','volumedetect','-f','null','-'],stdout=log,stderr=log,check=True)
    rows=6 if shot['seconds']==6 else 4
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(clip),'-vf',f'fps=4,scale=480:-1,tile=4x{rows}','-frames:v','1',str(q/f'{id}-overview.jpg')],check=True)
    results={}
    for name,extra in [('clip-qa',[]),('clone-check',['--expected',str(shot['expected'])])]:
        out=q/f'{id}-{name}.json'
        if out.exists() and out.stat().st_size:continue
        command=[sys.executable,str(ROOT/f'tools/{name}.py'),str(clip),f'--context-file={RUN}/prompts/{id}.txt','--json','--fail-on=medium','--retries=0',*extra]
        with out.open('w') as output:
            result=subprocess.run(command,stdout=output,stderr=subprocess.PIPE,text=True,cwd=ROOT)
        results[name]=result.returncode
        if result.returncode not in (0,3):
            (q/f'{id}-{name}-error.txt').write_text(result.stderr)
    print(json.dumps({'shot':id,'checks':results,'verdict':'Inspect saved reports and frames; no auto acceptance or reroll'}))

if __name__=='__main__':main()
