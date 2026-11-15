#!/usr/bin/env python3
"""Mix exact phone input cues and retained offscreen vocal source for POLISH."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import wave
import numpy as np
from scipy.signal import butter, sosfiltfilt

SR=48000


def read(path):
    return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ar',str(SR),'-ac','1','-f','f32le','-']),dtype='<f4').copy()


def write(path,x):
    if x.ndim==1:x=np.column_stack([x,x])
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes(np.rint(np.clip(x,-1,1)*32767).astype('<i2').tobytes())


def faded(x,seconds=.015):
    x=x.copy();n=min(len(x)//2,round(seconds*SR))
    x[:n]*=np.linspace(0,1,n);x[-n:]*=np.linspace(1,0,n);return x


def peak(x,db):
    return x*(10**(db/20)/max(1e-9,float(np.max(np.abs(x)))))


def main():
    p=argparse.ArgumentParser();p.add_argument('workspace',type=Path);p.add_argument('--version',default='v1');a=p.parse_args();w=a.workspace
    destination=w/f'audio/mix-{a.version}.wav'
    if destination.exists():raise SystemExit('Refusing to overwrite mix')
    cues=json.loads((w/'edit/typing-cues.json').read_text());rng=np.random.default_rng(421)
    stems={k:np.zeros(SR*38,dtype=np.float64) for k in ('keys','notifications','touch','voice','room')}
    def put(name,at,x):
        i=round(at*SR);n=min(len(x),len(stems[name])-i)
        stems[name][i:i+n]+=x[:n]
    for e in cues:
        if e['kind']=='key':
            t=np.arange(round(.045*SR))/SR
            sound=(rng.normal(size=len(t))*.35+np.sin(2*np.pi*(1170+rng.uniform(-100,100))*t))
            sound*=np.exp(-t/0.006)*(1-np.exp(-t/.0003))
            sound=sosfiltfilt(butter(2,[500,5400],btype='bandpass',fs=SR,output='sos'),sound)
            put('keys',e['at'],peak(sound,-25+(1.2 if 3.7<e['at']<4.4 else 0)))
        elif e['kind']=='notification':
            t=np.arange(round(.36*SR))/SR
            sound=np.sin(2*np.pi*1350*t)*np.exp(-t/.065)
            u=np.maximum(0,t-.09);sound+=.65*np.sin(2*np.pi*1800*u)*np.exp(-u/.09)*(t>=.09)
            put('notifications',e['at'],peak(faded(sound,.003),-20))
        else:
            t=np.arange(round(.060*SR))/SR
            sound=(np.sin(2*np.pi*235*t)+rng.normal(size=len(t))*.15)*np.exp(-t/.008)
            put('touch',e['at'],peak(faded(sound,.001),-27))
    room=rng.normal(size=SR*38)
    room=sosfiltfilt(butter(2,[90,1900],btype='bandpass',fs=SR,output='sos'),room)
    stems['room']=room*(10**(-52/20)/np.sqrt(np.mean(room**2)))
    source=w/'audio/raw/V01-voice.wav';voice=read(source)
    voice=sosfiltfilt(butter(2,[100,10000],btype='bandpass',fs=SR,output='sos'),voice)
    ranges=[{'line':'No.','sourceFile':'audio/raw/V01-voice.wav','sourceStart':2.18,'sourceEnd':3.02,'at':22.7,'peakDb':-10},
            {'line':'Oh, come on.','sourceFile':'audio/raw/V01-voice.wav','sourceStart':5.05,'sourceEnd':6.2,'at':27.85,'peakDb':-10},
            {'line':'Exhale','sourceFile':'audio/raw/V02-sigh.wav','sourceStart':.7,'sourceEnd':2.7,'at':29.4,'peakDb':-25}]
    for r in ranges:
        take=voice if r['sourceFile'].endswith('V01-voice.wav') else sosfiltfilt(butter(2,[100,9000],btype='bandpass',fs=SR,output='sos'),read(w/r['sourceFile']))
        clip=faded(take[round(r['sourceStart']*SR):round(r['sourceEnd']*SR)])
        put('voice',r['at'],peak(clip,r['peakDb']))
        write(w/f'audio/stems/voice-{r["line"].split()[0].strip(".,").lower()}-{a.version}.wav',peak(clip,r['peakDb']))
    for name,x in stems.items():write(w/f'audio/stems/{name}-{a.version}.wav',x)
    mix=sum(stems.values())*10**(6/20);write(destination,mix)
    receipt={'sampleRate':SR,'samples':len(mix),'seconds':38,'voiceSource':'audio/raw/V01-voice.wav','voiceSourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'voiceRanges':ranges,'masterGainDb':6,'peakDbfs':float(20*np.log10(np.max(np.abs(mix)))),'listening':'Pending director listening; transcription supports the two spoken lines, not performance approval. Separate native breath candidate selected from V02.'}
    (w/f'qa/audio/mix-{a.version}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
