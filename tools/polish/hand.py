#!/usr/bin/env python3
"""Composite the exact animated interface onto the retained normal-speed hand take."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import cv2
import numpy as np
from PIL import Image,ImageDraw
from render import ui,SW,SH


def main():
    p=argparse.ArgumentParser();p.add_argument('workspace',type=Path);p.add_argument('source',type=Path)
    p.add_argument('--version',default='v1');p.add_argument('--source-start-frame',type=int,default=30);a=p.parse_args()
    w=a.workspace;cap=cv2.VideoCapture(str(a.source))
    width,height=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    assert (width,height)==(720,1280)
    # Observed physical screen corners; the upper-left corner is outside the camera view.
    corners=np.float32([[-238,300],[190,117],[748,849],[285,1064]])
    hom=cv2.getPerspectiveTransform(np.float32([[0,0],[SW,0],[SW,SH],[0,SH]]),corners)
    m=Image.new('L',(SW,SH));ImageDraw.Draw(m).rounded_rectangle((0,0,SW,SH),radius=83,fill=255)
    mask=cv2.warpPerspective(np.array(m),hom,(width,height),flags=cv2.INTER_LINEAR).astype(np.float32)/255
    mask=cv2.GaussianBlur(mask,(0,0),.6)
    destination=w/f'renders/hand-composite-{a.version}.mp4'
    if destination.exists():raise SystemExit('Refusing to overwrite hand composite')
    enc=subprocess.Popen(['ffmpeg','-v','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(destination)],stdin=subprocess.PIPE)
    cap.set(cv2.CAP_PROP_POS_FRAMES,a.source_start_frame)
    strips=[]
    for i in range(36):
        ok,frame=cap.read()
        if not ok:raise RuntimeError('Short hand source')
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB).astype(np.float32)
        screen=cv2.warpPerspective(np.asarray(ui(30+i/24)),hom,(width,height),flags=cv2.INTER_CUBIC).astype(np.float32)
        # The warm skin is a foreground holdout; do not paint letters on the finger.
        skin=np.clip((rgb[:,:,0]-rgb[:,:,1]-8)/16,0,1)*np.clip((rgb[:,:,0]-rgb[:,:,2]-15)/25,0,1)
        skin=cv2.dilate(skin,np.ones((3,3),np.uint8));skin=cv2.GaussianBlur(skin,(0,0),.55)
        skin=np.clip(skin,0,1)
        luminance=rgb.mean(axis=2)
        shadow=np.clip(luminance/42,.38,1)
        surface=screen*(.80+.12*shadow[:,:,None])+rgb*.10
        alpha=mask*(1-skin)
        result=np.clip(rgb*(1-alpha[:,:,None])+surface*alpha[:,:,None],0,255).astype(np.uint8)
        result=cv2.resize(result,(1080,1920),interpolation=cv2.INTER_LANCZOS4)
        enc.stdin.write(result.tobytes())
        if i in (0,12,24,35):
            image=Image.fromarray(result);image.save(w/f'qa/hand-v1/composite-{a.version}-{i:02d}.png');image.thumbnail((270,480));strips.append(image)
    enc.stdin.close();assert enc.wait()==0;cap.release()
    sheet=Image.new('RGB',(1080,480))
    for n,im in enumerate(strips):sheet.paste(im,(n*270,0))
    sheet.save(w/f'qa/hand-v1/composite-strip-{a.version}.jpg')
    receipt={'source':str(a.source),'sourceSha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'sourceStartFrame':a.source_start_frame,'frames':36,'fps':24,'editStartFrame':720,'output':str(destination.relative_to(w)),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'screenCorners':corners.tolist(),'method':'Exact local interface, planar composite, skin foreground holdout, retained normal-speed source frames; no retiming.'}
    (w/f'qa/hand-v1/composite-{a.version}.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
