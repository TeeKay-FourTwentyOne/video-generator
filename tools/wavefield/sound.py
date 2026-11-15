#!/usr/bin/env python3
"""Deterministic six-click approach score, synthesized locally at 48 kHz."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly

SR=48000
DURATION=24
ONSETS=(2,6,10,14,18,22)


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


def lowpass(x,hz):
    return sosfilt(butter(3,hz,fs=SR,output='sos'),x)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(workspace):
    w=Path(workspace)
    out=w/'audio'
    out.mkdir(exist_ok=True)
    if (out/'mix-v1.wav').exists():raise ValueError('Audio version exists; preserve it.')
    rng=np.random.default_rng(20261114)
    n=SR*DURATION
    t=np.arange(n)/SR
    clicks=np.zeros((n,2),np.float64)
    body=np.zeros_like(clicks)
    resonance=np.zeros_like(clicks)
    # One source click reused six times; the approach changes its transfer function.
    ct=np.arange(round(SR*.05))/SR
    click=(rng.normal(size=ct.size)*np.exp(-ct/.0025)
           +.65*np.sin(2*np.pi*2700*ct)*np.exp(-ct/.0038))
    click*=smooth(ct/.0003)
    click/=np.max(np.abs(click))
    wavfile.write(out/'detector-source-click.wav',SR,click.astype(np.float32))
    gains=(.025,.055,.11,.20,.34,.62)
    cutoffs=(450,850,1700,3500,7000,14500)
    events=[]
    for j,onset in enumerate(ONSETS):
        start=round(onset*SR)
        direct=lowpass(click,cutoffs[j])*gains[j]
        # Increasing dry presence; early sound spreads diffusely through the field.
        clicks[start:start+len(direct),:]+=direct[:,None]
        for k,delay in enumerate((.027,.051,.083,.131,.197,.293)):
            echo=lowpass(click,max(220,cutoffs[j]/(1+.4*k)))
            echo*=gains[j]*(.48-.045*j)*np.exp(-k*.34)
            for channel in (0,1):
                s=start+round((delay+(channel*2-1)*.003*(k+1))*SR)
                resonance[s:s+len(echo),channel]+=echo
        bt=np.arange(round(SR*(2.8 if j<5 else .4)))/SR
        # Same descending resonator, progressively extended toward sub-bass.
        f0=(160,140,116,94,76,63)[j]
        f1=(88,74,62,51,43,35)[j]
        tau=.18+.025*j
        integral=f1*bt+(f0-f1)*tau*(1-np.exp(-bt/tau))
        low=np.sin(2*np.pi*integral)
        low+=.32*np.sin(2*np.pi*(1.97*integral)+.6)
        env=smooth(bt/(.035-.005*j))*np.exp(-bt/(.45+.11*j))
        tail=(.003,.011,.03,.075,.19,.68)[j]*low*env
        air=lowpass(rng.normal(size=bt.size),220+130*j)
        air/=max(np.std(air),1e-9)
        tail+=air*env*(.001,.002,.004,.009,.022,.055)[j]
        if j==5:tail*=1-smooth((bt-.17)/.15)
        for channel in (0,1):
            shift=round((.004 if channel else 0)*(1-j/5)*SR)
            s=start+shift
            body[s:s+len(tail),channel]+=tail[:min(len(tail),n-s)]
        events.append({'number':j+1,'seconds':onset,'sample':start,'frame':onset*30,
                       'sourceClickSha256':sha(out/'detector-source-click.wav'),
                       'gain':gains[j],'lowpassHz':cutoffs[j]})
    # Extremely quiet field air, responding to the same approach envelope.
    air=lowpass(rng.normal(size=n),190)
    air/=max(np.std(air),1e-9)
    env=(.001+.009*(np.minimum(t,22)/22)**2)*smooth(t/1.3)*(1-smooth((t-22.12)/.2))
    bed=np.stack([(air+.28*np.sin(2*np.pi*83*t)) * env,
                  (np.roll(air,317)+.28*np.sin(2*np.pi*83.13*t+.4))*env],axis=-1)
    for stem in (clicks,body,resonance,bed):
        stem*= (1-smooth((t-22.22)/.12))[:,None]
    mix=clicks+body+resonance+bed
    # One transparent global gain, no per-click normalization or compressor.
    oversampled=resample_poly(mix,4,1,axis=0)
    truepeak=float(np.max(np.abs(oversampled)))
    gain=min(1.8,10**(-2/20)/max(truepeak,1e-10))
    stems={'clicks-v1':clicks,'body-v1':body,'resonance-v1':resonance,'field-air-v1':bed}
    for name,signal in stems.items():wavfile.write(out/f'{name}.wav',SR,(signal*gain).astype(np.float32))
    mix*=gain
    wavfile.write(out/'mix-v1.wav',SR,mix.astype(np.float32))
    for e in events:
        seg=mix[e['sample']:e['sample']+SR//3]
        e['peakDbFS']=float(20*np.log10(max(np.max(abs(seg)),1e-12)))
        e['rmsDbFS']=float(20*np.log10(max(np.sqrt(np.mean(seg**2)),1e-12)))
    report={'schemaVersion':1,'method':'Local deterministic synthesis; no recorded or generated third-party audio',
            'sampleRate':SR,'samples':n,'durationSeconds':DURATION,'channels':2,'seed':20261114,
            'events':events,'intervalSamples':[events[i+1]['sample']-events[i]['sample'] for i in range(5)],
            'globalGain':gain,'truePeakDbTP':float(20*np.log10(truepeak*gain)),
            'silentAfterSeconds':22.34,'endingSilenceMaxAbs':float(np.max(abs(mix[round(22.34*SR):]))),
            'monotonicEventRms':all(events[i+1]['rmsDbFS']>events[i]['rmsDbFS'] for i in range(5)),
            'mixSha256':sha(out/'mix-v1.wav'),'recipeSha256':sha(__file__),
            'listening':'Real-time human listening remains pending.'}
    (w/'qa/audio-synthesis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    assert report['endingSilenceMaxAbs']==0 and report['monotonicEventRms']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',default='data/workspace/wavefield-v1')
    build(p.parse_args().workspace)
