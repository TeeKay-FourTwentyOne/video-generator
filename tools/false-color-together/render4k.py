#!/usr/bin/env python3
"""Re-rasterize the immutable v1 scene at 2x size, without changing its clock."""
import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def sha(file):
    h=hashlib.sha256()
    with open(file,'rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block)
    return h.hexdigest()


def load_scene(workspace):
    receipt=json.loads((workspace/'provenance/picture-v1.mp4.json').read_text())
    recipe=workspace/'provenance/render.py'
    if sha(recipe)!=receipt['recipeSha256']:
        raise ValueError('The preserved native recipe differs from its creation receipt')
    spec=importlib.util.spec_from_file_location('together_approved_v1',recipe)
    scene=importlib.util.module_from_spec(spec);spec.loader.exec_module(scene)
    if sha(scene.FONT)!=receipt['fontSha256']:
        raise ValueError('Font changed since native rendering')
    return scene,recipe,receipt


def scale_primitives(scene):
    # The original frame() and tusi_positions() remain unchanged. Only their
    # drawing primitives and canvas raster receive the exact 2x spatial scale.
    circle=scene.circle
    line=scene.line
    def circle2(im,x,y,r,color,opacity=1):
        circle(im,x*2,y*2,r*2,color,opacity)
    def line2(im,points,color,opacity=1,width=2):
        line(im,[(x*2,y*2) for x,y in points],color,opacity,width*2)
    def text2(im,message,y,size=50,color=scene.IVORY,opacity=1,center=scene.CX):
        if opacity<=0:return
        draw=ImageDraw.Draw(im);font=scene.font(size*2)
        width=draw.textlength(message,font=font)
        if width>1720:raise ValueError('4K caption exceeds the safe width')
        draw.text((center*2-width/2,y*2),message,font=font,fill=scene.mix(scene.BG,color,opacity))
    def header2(im,chapter,t):
        draw=ImageDraw.Draw(im)
        draw.text((182,270),'FALSE COLOR',font=scene.font(44),fill=scene.MUTED)
        draw.text((1436,270),chapter,font=scene.font(40),fill=scene.MUTED)
        line2(im,[(92,190),(909,190)],scene.MUTED,.23,1)
    scene.circle=circle2;scene.line=line2;scene.text=text2;scene.header=header2
    scene.W=2160;scene.H=3840


def inspect(scene,workspace):
    folder=workspace/'qa/4k-v1';folder.mkdir(parents=True,exist_ok=True)
    same=[];stable=[];cards=[];comparisons=[]
    for frame in [0,60,120,240,342,438,510,560]:
        image=np.asarray(scene.frame(frame))
        a=image[1230:1512,860:1142];b=image[2390:2672,860:1142]
        same.append(bool(np.array_equal(a,b)));stable.append(hashlib.sha256(a.tobytes()).hexdigest())
    for frame in [60,342,480,636,828,1002,1290,1488,1740,1980,2190]:
        im=scene.frame(frame)
        im.save(folder/f'frame-{frame:04d}.png')
        card=Image.new('RGB',(270,520),scene.BG);card.paste(im.resize((270,480),Image.Resampling.LANCZOS),(0,0))
        ImageDraw.Draw(card).text((10,490),f'{frame/60:.1f}s / frame {frame}',fill=scene.IVORY)
        cards.append(card)
        old=Image.open(workspace/f'refs/frame-{frame:04d}.png').convert('RGB')
        down=im.resize(old.size,Image.Resampling.LANCZOS)
        delta=np.abs(np.asarray(down).astype(float)-np.asarray(old).astype(float))
        comparisons.append({'frame':frame,'meanAbsoluteChannelError':float(delta.mean()),'channelFractionDeltaOver32':float((delta>32).mean())})
    sheet=Image.new('RGB',(1080,1560),scene.BG)
    for i,card in enumerate(cards):sheet.paste(card,((i%4)*270,(i//4)*520))
    sheet.save(folder/'contact-sheet.png')
    result={'width':2160,'height':3840,'fps':60,'frames':2280,'durationSeconds':38,
            'targetRadiusPixels':132,'pairedTargetCropsIdentical':all(same),
            'targetCropStableDuringContextChange':len(set(stable))==1,
            'sceneClockAndGeometry':'Unmodified functions from the hash-verified native recipe; only drawing coordinates, fonts and canvas scaled by two.',
            'nativeComparisons':comparisons,
            'comparisonLimit':{'meanAbsoluteChannelError':1.0,'channelFractionDeltaOver32':.01}}
    if not all(same) or len(set(stable))!=1 or any(c['meanAbsoluteChannelError']>1 or c['channelFractionDeltaOver32']>.01 for c in comparisons):
        raise ValueError(json.dumps(result))
    (folder/'geometry.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'4kGeometryPassed':True,'maxNativeComparisonMeanError':max(c['meanAbsoluteChannelError'] for c in comparisons)}),flush=True)


def render(scene,workspace,recipe,base_receipt):
    out=workspace/'render/picture-4k-v1.mp4'
    receipt=workspace/'provenance/picture-4k-v1.mp4.json'
    if out.exists() or receipt.exists():raise ValueError('Refusing to overwrite a 4K render or its creation receipt')
    snapshot={'createdAt':datetime.now(timezone.utc).isoformat(),'method':'native-programmatic-rerender',
              'baseRecipeSha256':sha(recipe),'spatialAdapterSha256':sha(__file__),
              'fontSha256':base_receipt['fontSha256'],'width':2160,'height':3840,'frames':2280,'fps':60,
              'provider':None,'model':None,'prompt':None}
    receipt.write_text(json.dumps(snapshot,indent=2)+'\n')
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-n','-f','rawvideo','-pix_fmt','rgb24',
         '-s','2160x3840','-r','60','-i','pipe:0','-an',
         '-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
         '-c:v','libx264','-preset','fast','-crf','12','-threads','6',
         '-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
         '-bsf:v','h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
         '-movflags','+faststart',str(out)]
    start=time.monotonic()
    with open(workspace/'scratch/picture-4k-v1.ffmpeg.log','x') as log:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        try:
            for i in range(2280):
                process.stdin.write(scene.frame(i).tobytes())
                if i%300==0:print(json.dumps({'frame':i,'of':2280,'elapsed':round(time.monotonic()-start,1)}),flush=True)
        finally:process.stdin.close()
        if process.wait():raise RuntimeError('4K encoder failed; inspect the retained log')
    snapshot.update({'sha256':sha(out),'renderSeconds':round(time.monotonic()-start,2)})
    (workspace/'provenance/picture-4k-v1.mp4.completed.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    print(json.dumps(snapshot),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('workspace',type=Path);parser.add_argument('--render',action='store_true')
    args=parser.parse_args();scene,recipe,receipt=load_scene(args.workspace)
    scale_primitives(scene);inspect(scene,args.workspace)
    if args.render:render(scene,args.workspace,recipe,receipt)
