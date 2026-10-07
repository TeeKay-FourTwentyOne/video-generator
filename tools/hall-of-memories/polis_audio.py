#!/usr/bin/env python3
"""Local temporary voices, timed dialogue and separate stems for the polis scene."""
from pathlib import Path
import argparse, json, math, subprocess, wave
import numpy as np

SR=48000
HERE=Path(__file__).resolve().parent

def write(path,x):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1 if x.ndim==1 else 2);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes(np.rint(np.clip(x,-1,1)*32767).astype('<i2').tobytes())

def read(path,filters=None):
    cmd=['ffmpeg','-v','error','-i',str(path)]
    if filters:cmd+=['-af',filters]
    cmd+=['-ar',str(SR),'-ac','1','-f','f32le','-']
    return np.frombuffer(subprocess.check_output(cmd),'<f4').copy()

def edge(x,n=480):
    x=x.copy();n=min(n,len(x)//2)
    x[:n]*=np.linspace(0,1,n);x[-n:]*=np.linspace(1,0,n)
    return x

def put(dst,x,at,pan=0):
    n=round(at*SR);m=min(len(x),len(dst)-n)
    if m>0:dst[n:n+m]+=np.c_[x[:m]*(1-max(0,pan)*.25),x[:m]*(1+min(0,pan)*.25)]

def stamp(t):
    ms=round(t*1000);h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000
    return f'{h:02}:{m:02}:{ms//1000:02}.{ms%1000:03}'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    out=args.output.resolve();audio=out/'audio'
    if audio.exists():raise SystemExit('Refusing existing audio directory.')
    (audio/'dialogue').mkdir(parents=True)
    script=json.loads((HERE/'polis_scene.json').read_text())
    cursor=.25;lines=[];clips={}
    for line in script['dialogue']:
        cast=script['cast'][line['speaker']]
        path=audio/'dialogue'/f"{line['id']}.aiff"
        subprocess.run(['say','-v',cast['voice'],'-r',str(cast['rate']),'-o',str(path),line['text']],check=True)
        x=read(path,f"aresample=48000,asetrate={round(SR*cast['pitch'])},aresample=48000,atempo={1/cast['pitch']},highpass=f=85,lowpass=f=8500")
        active=np.flatnonzero(np.abs(x)>.002)
        if not len(active):raise RuntimeError('Empty dialogue output')
        x=x[max(0,active[0]-1800):min(len(x),active[-1]+2400)]
        x=edge(x)
        # Stable voice headroom. Do not normalize chapters independently later.
        x*=.34/max(.001,float(np.abs(x).max()))
        path=path.with_suffix('.wav');write(path,x);clips[line['id']]=x
        start=math.ceil(cursor*8)/8;end=start+len(x)/SR
        lines.append({**line,'start':start,'end':end,'file':str(path.relative_to(out))})
        cursor=end+line['gap_after']
    duration=math.ceil(cursor*8)/8
    n=round(duration*SR);dialogue=np.zeros((n,2));room=np.zeros_like(dialogue);foley=np.zeros_like(dialogue)
    for line in lines:
        x=clips[line['id']];pan=script['cast'][line['speaker']]['pan']
        put(dialogue,x,line['start'],pan)
        # Small stone-court reflection, intelligibility kept forward.
        for delay,gain in [(.065,.055),(.13,.022)]:put(dialogue,x*gain,line['start']+delay,-pan)
    rng=np.random.default_rng(926);t=np.arange(n)/SR
    noise=rng.normal(0,1,n);wind=np.convolve(noise,np.ones(1801)/1801,mode='same')
    bed=.016*wind+.0018*np.sin(2*np.pi*83*t)+.0012*np.sin(2*np.pi*124.5*t)
    room[:,0]=bed;room[:,1]=bed*.95
    arrivals=[lines[-1]['start']-3.4+i*.625 for i in range(5)]
    for i,at in enumerate(arrivals):
        tt=np.arange(round(.25*SR))/SR
        step=(np.sin(2*np.pi*(132+i*3)*tt)+rng.normal(0,.26,len(tt)))*np.exp(-tt*29)
        put(foley,edge(step)*.035,at,.65)
    for line in lines[:10]:
        tt=np.arange(round(.14*SR))/SR
        soft=rng.normal(0,1,len(tt))*np.sin(np.pi*np.arange(len(tt))/len(tt))**2*.0018
        put(foley,soft,line['start']+.2,script['cast'][line['speaker']]['pan'])
    for name,stem in [('dialogue',dialogue),('atmosphere',room),('foley',foley)]:
        stem[:480]*=np.linspace(0,1,480)[:,None];stem[-1200:]*=np.linspace(1,0,1200)[:,None]
        write(audio/f'{name}.wav',stem)
    mix=dialogue+room+foley
    assert np.abs(mix).max()<.8
    write(audio/'mix.wav',mix)
    timeline={**script,'duration':duration,'lines':lines,'elder_walk_start':arrivals[0]-.75,'elder_arrival':lines[-1]['start']-.7,
              'voice_provenance':'Installed macOS synthetic speech, lightly pitch-adjusted for this draft. Temporary casting; no voice provider calls.',
              'audio_peak_dbfs':float(20*np.log10(np.abs(mix).max()))}
    (out/'timeline.json').write_text(json.dumps(timeline,indent=2)+'\n')
    captions=['WEBVTT','']
    for line in lines:captions.extend([line['id'],f"{stamp(line['start'])} --> {stamp(line['end'])}",line['text'],''])
    (out/'dialogue.vtt').write_text('\n'.join(captions))
    screenplay=['# The tellers — complete first scene draft','',f'Duration: {duration:.3f} seconds. Temporary synthetic voices.','',
                'Hard cut from the factory to the storyteller continuing the raised-hand gesture.','']
    for line in lines:screenplay.extend([f"**{line['speaker'].upper()}** ({line['start']:.2f}s)",line['text'],''])
    screenplay.extend(['The children turn to the elder. End this segment before the explanation or the walk to the Hall.',''])
    (out/'screenplay.md').write_text('\n'.join(screenplay))
    print(json.dumps({'duration':duration,'lines':len(lines),'elder_walk_start':timeline['elder_walk_start'],'elder_reply_start':lines[-1]['start']},indent=2),flush=True)

if __name__=='__main__':main()
