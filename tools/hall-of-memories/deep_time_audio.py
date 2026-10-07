#!/usr/bin/env python3
"""Original procedural deep-time/visitor sound, with separate editable stems."""
import argparse
import json
import math
import shutil
from pathlib import Path

import numpy as np
from sound import SR, write, edge, norm, put

HERE=Path(__file__).resolve().parent


def noise(duration,seed,cutoff=600):
    n=round(duration*SR);rng=np.random.default_rng(seed)
    x=rng.normal(0,1,n).astype(np.float32)
    spectrum=np.fft.rfft(x)
    hz=np.fft.rfftfreq(n,1/SR)
    spectrum*=1/np.sqrt(1+(hz/cutoff)**4)
    return norm(np.fft.irfft(spectrum,n).astype(np.float32),1)


def fade(duration,attack=.1,release=.2):
    n=round(duration*SR);e=np.ones(n,np.float32)
    a=min(round(attack*SR),n//2);b=min(round(release*SR),n//2)
    if a:e[:a]=np.sin(np.linspace(0,np.pi/2,a))**2
    if b:e[-b:]=np.sin(np.linspace(np.pi/2,0,b))**2
    return e


def grain(duration,seed,pitch=120):
    t=np.arange(round(duration*SR))/SR
    x=noise(duration,seed,2600)*np.exp(-t*9)
    x+=.26*np.sin(2*np.pi*pitch*t)*np.exp(-t*16)
    return edge(norm(x,.15),.005)


def syllable(duration,base,index):
    t=np.arange(round(duration*SR))/SR
    f=base*(1+.12*np.sin(t/duration*np.pi)+.017*np.sin(2*np.pi*19*t))
    phase=np.cumsum(f)*2*np.pi/SR
    x=np.zeros(len(t))
    for k in range(1,17):
        weight=.1/k+math.exp(-.5*((k*base-620)/270)**2)*.44
        x+=weight*np.sin(k*phase+index*.13)
    x*=.75+.25*np.sin(2*np.pi*31*t)
    x+=noise(duration,6100+index,2100)*.14
    return norm(x*np.sin(np.linspace(0,np.pi,len(t)))**.55,.24)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);args=ap.parse_args()
    root=args.run.resolve();out=root/'audio';out.mkdir(exist_ok=True)
    plan=json.loads((root/'timeline.json').read_text());duration=plan['duration'];n=round(duration*SR)
    stems={k:np.zeros((n,2),np.float32) for k in ['earth','ice','forest','craft','footsteps','alien']}
    def add(name,x,at,pan=0,amp=1):put(stems[name],x,at,pan,amp)
    # Earth movement is low, dry and irregular, rather than a continuous score.
    t=np.arange(round(74*SR))/SR
    rumble=(.55*np.sin(2*np.pi*39*t)+.25*np.sin(2*np.pi*61.3*t)+noise(74,527,180)*.5)
    rumble*=.018*fade(74,1.6,4)*(.75+.25*np.sin(t*.24)**2)
    add('earth',rumble,0)
    for j,(at,length,amp) in enumerate([(8,3,.22),(13,4,.26),(25.5,5,.28),(30,6,.32),
                                        (38.8,7,.34),(46,6,.27),(54,4,.24),(59,4,.20)]):
        x=noise(length,810+j,420)*fade(length,.8,1.5)*.11
        add('earth',x,at,(-1 if j%2 else 1)*.35,amp)
    for j,at in enumerate([10.4,15.1,29.2,33.5,37.2,42.8,47.2,53.4,58.6]):
        add('earth',grain(.75,950+j,72),at,(j%3-1)*.45,.17)
    wind=noise(48,713,1800)*fade(48,3,6)*.021
    add('ice',wind,17,-.12)
    for j,at in enumerate([18.4,21.5,24.2,27.6,58.5,62.9,64.2,66.0]):
        crack=grain(.55,1210+j,420)+edge(noise(.55,1310+j,4100)*np.exp(-np.arange(round(.55*SR))/SR*18)*.055)
        add('ice',crack,at,(-1 if j%2 else 1)*.5,.22)
    # Forest contains wind, foliage and water only; no animal recordings/calls.
    length=duration-68
    tt=np.arange(round(length*SR))/SR
    leaves=noise(length,8111,1700)*(.65+.35*np.sin(tt*.48)**2)*fade(length,5,.15)*.023
    water=noise(length,8112,4200)*fade(length,4,.15)*.012
    add('forest',leaves,68,-.55);add('forest',water,68,.7)
    def engine(length,seed,reverse=False):
        tt=np.arange(round(length*SR))/SR;p=tt/length
        freq=63+(22*p if reverse else 22*(1-p))
        phase=np.cumsum(freq)*2*np.pi/SR
        x=np.sin(phase)+.35*np.sin(phase*2.01)+.17*np.sin(phase*3.5)
        x+=noise(length,seed,410)*.5
        return norm(x,.105)*fade(length,1.4,1.3)
    add('craft',engine(10,4401),79.2,-.18)
    add('craft',grain(.85,4402,63),87.5,-.18,.40)
    humt=np.arange(round(26*SR))/SR
    add('craft',np.sin(2*np.pi*48.2*humt)*.006*fade(26,1,1),89,-.2)
    add('craft',engine(6,4403,True),115,-.05)
    for j,at in enumerate([83.6,85.9,87.4,115.9,117.4]):add('craft',grain(.38,4500+j,160),at,-.1,.15)
    # Footfalls follow the two deterministic walk intervals and cadence.
    for who,(start,stop,step) in enumerate([(90,98,.4),(90.8,98.5,.4),(111,114.25,.333),(113,115.7,.333)]):
        for j,at in enumerate(np.arange(start+.16,stop,step)):
            add('footsteps',grain(.16,5000+who*30+j,130),float(at),.28 if who%2==0 else -.08,.15)
    syllables=[(.00,.34,154),(.43,.58,128),(1.22,.28,173),(1.61,.43,147),(2.16,.54,191)]
    phrase=np.zeros(round(2.9*SR),np.float32)
    for j,(at,length,base) in enumerate(syllables):
        x=syllable(length,base,j);k=round(at*SR);phrase[k:k+len(x)]+=x
        if j in [0,2,4]:
            click=grain(.07,6100+j,760)*.22;phrase[k:k+len(click)]+=click
    add('alien',phrase,104.08,.24)
    write(out/'alien-phrase.wav',phrase)
    total=sum(stems.values());peak=float(np.abs(total).max());gain=min(1,10**(-7/20)/max(peak,1e-8))
    for name,x in stems.items():write(out/f'{name}.wav',x*gain)
    mix=total*gain;write(out/'mix.wav',mix)
    report={'duration':duration,'sample_rate':SR,'channels':2,'samples_per_channel':n,
            'mix_peak_dbfs':20*math.log10(max(float(np.abs(mix).max()),1e-9)),
            'shared_gain':gain,'stems':list(stems),'alien_voice_start':104.08,
            'alien_voice_end':106.98,'subtitle':plan['subtitle'],
            'provenance':'Original local procedural sounds and an invented phonetic performance; no speech/voice provider, recordings, music or animal calls.',
            'review_limit':'Technical timing and level checks are not a real-time listening assessment.'}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copy2(HERE/'deep_time_audio.py',root/'recipe/deep_time_audio.py')
    shutil.copy2(HERE/'sound.py',root/'recipe/sound.py')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
