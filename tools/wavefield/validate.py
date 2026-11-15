#!/usr/bin/env python3
"""Decode and measure a rendered picture or native review; no creative approval."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from render import contact


def inspect(file,workspace,name,audio_reference='audio/mix-v1.wav',width=1080,height=1920):
    w=Path(workspace);file=Path(file)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(file)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    subprocess.run(['ffmpeg','-v','error','-i',str(file),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
    assert int(video['nb_read_frames'])==720
    assert (video['width'],video['height'],video['avg_frame_rate'])==(width,height,'30/1')
    assert all(video.get(k)=='bt709' for k in ['color_space','color_transfer','color_primaries'])
    chosen=[0,60,120,180,240,300,360,420,480,540,600,648]
    ending=[657,660,661,662,663,664,669,678,687,696,705,719]
    dense=[base+offset for base in [60,180,300,420,540,660] for offset in [-1,1,9]]
    images={};diffs=[];previous=None;c=cv2.VideoCapture(str(file));i=0
    last=None;point=None
    while True:
        ok,frame=c.read()
        if not ok:break
        small=cv2.resize(frame,(90,160)).astype(np.float32)/255
        if previous is not None:diffs.append(float(np.mean(abs(small-previous))))
        previous=small
        if i in set(chosen+ending+dense):images[i]=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        if i==666:point={'mean':float(frame.mean()),'nonblackFraction':float(np.mean(np.max(frame,axis=2)>10))}
        last=frame;i+=1
    c.release();assert i==720
    # Lossy limited-range H.264 may decode nominal white two code values low.
    # The authored frame is exactly 255; allow <= 3/255 codec deviation.
    assert float(last.mean())>=252 and float(last.std())<.6
    assert point['nonblackFraction']<.002 and point['mean']<.2
    contact([images[f] for f in chosen],[f'{f/30:.3f}s / frame {f}' for f in chosen],w/'qa'/f'{name}-timeline.jpg',240)
    contact([images[f] for f in ending],[f'{f/30:.3f}s / frame {f}' for f in ending],w/'qa'/f'{name}-ending.jpg',240)
    contact([images[f] for f in dense],[f'{f/30:.3f}s / frame {f}' for f in dense],w/'qa'/f'{name}-pulses.jpg',180)
    report={'file':str(file.relative_to(w)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
            'fullDecode':True,'frames':i,'fps':30,'width':width,'height':height,'durationSeconds':24,
            'color':{k:video.get(k) for k in ['color_space','color_transfer','color_primaries','color_range']},
            'finalFrame':{'mean':float(last.mean()),'std':float(last.std())},'pointFrame':point,
            'maxAdjacentDifferenceBeforeCollapse':max(diffs[:659]),
            'identicalAdjacentFramesBeforeCollapse':sum(d==0 for d in diffs[:659]),
            'visualReview':'Frame plates prepared for agent inspection; no director approval implied.',
            'browserPlayback':'Not established by this validator; frame plates are supplied for separate inspection.',
            'listening':'Full human listening pending.'}
    if any(s['codec_type']=='audio' for s in probe['streams']):
        data=subprocess.check_output(['ffmpeg','-v','error','-i',str(file),'-vn','-ac','2','-ar','48000','-f','f32le','pipe:1'])
        pcm=np.frombuffer(data,dtype='<f4').reshape(-1,2)
        reference=w/audio_reference
        sr,ref=wavfile.read(reference);assert sr==48000
        n=min(len(pcm),len(ref))
        corr=float(np.corrcoef(pcm[:n].ravel(),ref[:n].ravel())[0,1])
        peak=float(np.max(abs(resample_poly(pcm,4,1,axis=0))))
        silence=float(np.max(abs(pcm[round(22.5*sr):])))
        report['audio']={'decodedSamples':len(pcm),'channels':2,'sampleRate':sr,
                         'reference':audio_reference,'referenceSha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
                         'preparedMixCorrelation':corr,'truePeakDbTP':float(20*np.log10(max(peak,1e-12))),
                         'endingSilencePeak':silence}
        assert corr>.99 and peak<1 and silence<1e-5
    (w/'qa'/f'{name}-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--workspace',default='data/workspace/wavefield-v1');p.add_argument('--name',default='native')
    p.add_argument('--audio-reference',default='audio/mix-v1.wav')
    p.add_argument('--width',type=int,default=1080);p.add_argument('--height',type=int,default=1920)
    a=p.parse_args();inspect(a.file,a.workspace,a.name,a.audio_reference,a.width,a.height)
