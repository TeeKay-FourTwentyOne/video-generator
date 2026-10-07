#!/usr/bin/env python3
"""Temporary local dialogue and a continuous outdoor-to-Hall sound bed."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import numpy as np
from polis_audio import SR, read, write, edge, put, stamp

HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,help='Retained conversation run; defaults to sibling polis-draft-v1.')
    args=ap.parse_args()
    out=args.output.resolve();audio=out/'audio'
    if audio.exists():raise SystemExit('Refusing existing audio directory.')
    baseline=args.baseline.resolve() if args.baseline else out.parent/'polis-draft-v1'
    retained=['edit-v2/review/polis-scene-draft-1080p.mp4','edit-v2/masters/polis-scene-draft.mov',
              'animation-v3/polis-animation.blend','timeline.json']
    if not all((baseline/name).is_file() for name in retained):
        raise SystemExit('Retained baseline files missing; provide --baseline with the complete selected conversation run.')
    preserved={name:hashlib.sha256((baseline/name).read_bytes()).hexdigest() for name in retained}
    (audio/'dialogue').mkdir(parents=True)
    (out/'baseline-preservation.json').write_text(json.dumps(preserved,indent=2)+'\n')
    script=json.loads((HERE/'polis_invitation.json').read_text())
    cursor=.375;lines=[];clips={}
    for line in script['dialogue']:
        cast=script['cast'][line['speaker']];path=audio/'dialogue'/f"{line['id']}.aiff"
        subprocess.run(['say','-v',cast['voice'],'-r',str(cast['rate']),'-o',str(path),line['text']],check=True)
        x=read(path,f"aresample=48000,asetrate={round(SR*cast['pitch'])},aresample=48000,atempo={1/cast['pitch']},highpass=f=85,lowpass=f=8500")
        active=np.flatnonzero(np.abs(x)>.002)
        if not len(active):raise RuntimeError('Empty dialogue output')
        x=edge(x[max(0,active[0]-1800):min(len(x),active[-1]+2400)])
        x*=.34/max(.001,float(np.abs(x).max()));path=path.with_suffix('.wav');write(path,x);clips[line['id']]=x
        start=math.ceil(cursor*8)/8;end=start+len(x)/SR
        lines.append({**line,'start':start,'end':end,'file':str(path.relative_to(out))})
        cursor=end+line['gap_after']
    duration=math.ceil(cursor*8)/8
    byid={l['id']:l for l in lines}
    cues={'stand_start':math.ceil((byid['I08']['end']+.35)*8)/8}
    cues['walk_start']=cues['stand_start']+1.25
    cues['walk_end']=byid['I09']['start']-.625
    cues['hall_reveal']=cues['walk_start']+(cues['walk_end']-cues['walk_start'])*.48
    cues['threshold_hold']=byid['I13']['end']+.5
    n=round(duration*SR);dialogue=np.zeros((n,2));room=np.zeros_like(dialogue);foley=np.zeros_like(dialogue)
    for line in lines:
        x=clips[line['id']];pan=script['cast'][line['speaker']]['pan'];put(dialogue,x,line['start'],pan)
        late=line['start']>=cues['walk_end']
        for delay,gain in ([(.105,.07),(.225,.035)] if late else [(.065,.055),(.13,.022)]):
            put(dialogue,x*gain,line['start']+delay,-pan)
    rng=np.random.default_rng(927);t=np.arange(n)/SR
    # Running average avoids a long direct convolution on this full-length bed.
    noise=rng.normal(0,1,n+1800);cs=np.r_[0,np.cumsum(noise)]
    wind=(cs[1801:]-cs[:-1801])/1801
    approach=np.clip((t-cues['hall_reveal'])/(cues['walk_end']-cues['hall_reveal']),0,1)
    bed=.016*wind*(1-.40*approach)+.0018*np.sin(2*np.pi*83*t)+.0012*np.sin(2*np.pi*124.5*t)
    room[:,0]=bed;room[:,1]=bed*.95
    step_events=[]
    for who,offset,level,period in [('elder',0,.025,1.125),('story',.34,.017,.875),('challenge',.14,.017,.875),('quiet',.60,.014,.875)]:
        at=cues['walk_start']+offset
        while at<cues['walk_end']-.35:
            tt=np.arange(round(.19*SR))/SR
            x=(np.sin(2*np.pi*(143 if who=='elder' else 183)*tt)+rng.normal(0,.21,len(tt)))*np.exp(-tt*34)
            put(foley,edge(x,120)*level,at,script['cast'][who]['pan'])
            step_events.append({'speaker':who,'time':round(at,4),'period':period});at+=period/2
    for i,who in enumerate(['story','challenge','quiet']):
        tt=np.arange(round(.25*SR))/SR
        put(foley,edge(rng.normal(0,1,len(tt))*np.exp(-tt*18))*.007,cues['stand_start']+i*.16,script['cast'][who]['pan'])
    for name,stem in [('dialogue',dialogue),('atmosphere',room),('foley',foley)]:
        stem[:480]*=np.linspace(0,1,480)[:,None];stem[-1200:]*=np.linspace(1,0,1200)[:,None]
        write(audio/f'{name}.wav',stem)
    mix=dialogue+room+foley
    if np.abs(mix).max()>=.8:raise RuntimeError('Unexpected mix peak')
    write(audio/'mix.wav',mix)
    timeline={**script,'duration':duration,'lines':lines,'cues':cues,'footsteps':step_events,
              'voice_provenance':'Installed macOS synthetic speech; same temporary casting as The tellers. No provider calls.',
              'audio_peak_dbfs':float(20*np.log10(np.abs(mix).max()))}
    (out/'timeline.json').write_text(json.dumps(timeline,indent=2)+'\n')
    captions=['WEBVTT','']
    screenplay=['# With one person — invitation draft','',f'Duration: {duration:.3f} seconds. Temporary voices.','',
                'Continue after the elder says, “I used to ask that, too.”','']
    for line in lines:
        captions.extend([line['id'],f"{stamp(line['start'])} --> {stamp(line['end'])}",line['text'],''])
        screenplay.extend([f"**{script['cast'][line['speaker']]['role'].upper()}** ({line['start']:.3f}s)",line['text'],''])
        if line['id']=='I08':screenplay.extend(['The children rise. The elder leads them across the court. Reveal the Hall as they approach. Let the walk play without music.',''])
    screenplay.extend(['Hold the four figures at the open threshold. End before any record is selected or heard.',''])
    (out/'dialogue.vtt').write_text('\n'.join(captions));(out/'screenplay.md').write_text('\n'.join(screenplay))
    print(json.dumps({'duration':duration,'lines':len(lines),'cues':cues},indent=2),flush=True)

if __name__=='__main__':main()
