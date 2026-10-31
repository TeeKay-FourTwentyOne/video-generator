#!/usr/bin/env python3
"""Inspect decoded delivery pixels and audio independently of the renderer."""
import argparse
import hashlib
import json
import re
import subprocess as sp
import wave
from pathlib import Path

import cv2
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('workspace',type=Path);ap.add_argument('version');args=ap.parse_args()
    w=args.workspace;folder=w/'final'/args.version
    delivery=json.loads((folder/'delivery.json').read_text());timeline=json.loads((folder/'timeline.json').read_text())
    expected_frames=sum(s['frames'] for s in timeline);seconds=expected_frames/30
    width=delivery['expected'].get('width',1080);height=delivery['expected'].get('height',1920)
    assert width in (1080,2160) and height==width*16//9
    factor=width//1080;top=555*factor;bottom=1365*factor
    movie=folder/'film.mp4';cap=cv2.VideoCapture(str(movie));reports=[];outer_max=0;outer_sum=0;outer_count=0
    index=0;previous=None;pair_diffs=[];change_diffs=[];black_max=0
    starts={s['frame']:s for s in timeline};seg=timeline[0]
    while True:
        ok,bgr=cap.read()
        if not ok:break
        if index in starts:seg=starts[index];previous=None
        gray=cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY)
        outside=np.concatenate([gray[:top].ravel(),gray[bottom:].ravel()])
        outer_max=max(outer_max,int(outside.max()));outer_sum+=int(outside.sum());outer_count+=outside.size
        if seg['shot'].startswith(('HEAD','TAIL','GAP')):
            black_max=max(black_max,int(gray.max()))
        elif previous is not None:
            diff=float(np.abs(gray[top:bottom].astype(np.int16)-previous[top:bottom].astype(np.int16)).mean())
            (pair_diffs if (index-seg['frame'])%2 else change_diffs).append(diff)
        previous=gray;index+=1
    cap.release()
    assert index==expected_frames, index
    assert black_max==0, black_max
    assert outer_max<=8 and outer_sum/max(outer_count,1)<.01, (outer_max,outer_sum/outer_count)
    assert np.percentile(pair_diffs,95)<.5, 'Cadence mismatch'
    assert np.median(change_diffs)>np.median(pair_diffs)*3, 'Expected moving 15 fps noise field'
    probe=json.loads(sp.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (video['width'],video['height'],video['avg_frame_rate'],video['pix_fmt'],video['profile'])==(width,height,'30/1','yuv420p','High')
    assert all(video.get(k)=='bt709' for k in ['color_space','color_transfer','color_primaries'])
    assert audio['codec_name']=='aac' and audio['sample_rate']=='48000' and audio['channels']==2
    raw=sp.check_output(['ffmpeg','-v','error','-i',str(movie),'-t',str(seconds),'-vn','-f','f32le','-ac','2','-ar','48000','pipe:1'])
    pcm=np.frombuffer(raw,'<f4').reshape(-1,2)
    assert len(pcm)==expected_frames*1600
    channel_difference=float(np.max(np.abs(pcm[:,0]-pcm[:,1])))
    assert channel_difference<1e-5,channel_difference
    source=w/delivery['edit']['audio']['path']
    with wave.open(str(source)) as f:master=np.frombuffer(f.readframes(f.getnframes()),'<i2').reshape(-1,2)
    assert len(master)==expected_frames*1600
    for s in timeline:
        begin=s['frame']*1600;end=(s['frame']+s['frames'])*1600
        if s['shot'].startswith(('HEAD','TAIL','GAP')):
            assert not master[begin:end].any()
            # AAC overlap can ring at the exact edge. Inspect the full interval
            # and its interior separately rather than claiming PCM-equivalent silence.
            inside=pcm[begin+1536:end-1536]
            interior=float(np.max(np.abs(inside))) if len(inside) else None
            assert interior is not None and interior<1e-6,(s['shot'],interior)
            reports.append({'segment':s['shot'],'pcmMasterExactlyZero':True,'decodedAacWholeGapPeak':float(np.max(np.abs(pcm[begin:end]))),'decodedAacInteriorPeak':interior})
    loud=sp.run(['ffmpeg','-hide_banner','-i',str(movie),'-af','loudnorm=I=-24:TP=-1:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    measured=json.loads(re.findall(r'\{[^{}]+\}',loud.stderr)[-1]);assert float(measured['input_tp'])<=-1
    result={'schemaVersion':1,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'frames':index,'durationSeconds':seconds,'format':{'width':width,'height':height,'fps':30,'profile':video['profile'],'pixelFormat':video['pix_fmt'],'audioCodec':audio['codec_name'],'audioSampleRate':48000,'colour':'BT.709 matrix, transfer and primaries'},'allBlackIntervalsExactDecodedBlack':black_max==0,'outsideWindow':{'maximumDecodedValue':outer_max,'meanDecodedValue':outer_sum/outer_count,'note':'Tiny boundary quantization is permitted; all intended outer pixels are black.'},'cameraCadence':{'pairedFrameMeanDifference':float(np.mean(pair_diffs)),'pairedFrame95thPercentile':float(np.percentile(pair_diffs,95)),'newCameraFrameMedianDifference':float(np.median(change_diffs)),'method':'Decoded frame differences within each camera file; no pairs across recording cuts.'},'audio':{'samples':len(pcm),'dualMonoMaxDifference':channel_difference,'masterGapSamplesExactlyZero':True,'gaps':reports,'integratedLufs':float(measured['input_i']),'truePeakDbtp':float(measured['input_tp']),'loudnessRangeLu':float(measured['input_lra']),'realTimeListening':'not established by computational checks'},'fullDecode':True,'artisticApproval':False}
    assert result['sha256']==delivery['sha256']
    (w/'qa'/f'{args.version}-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
