#!/usr/bin/env python3
"""Render the film from six generated boundary masks and computed wave fields."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

from field import Fresnel, interference, phase_screen, verify

cv2.setNumThreads(2)
FPS = 30
FRAMES = 720
MILESTONES = np.array([0, 4.4, 8.8, 13.2, 17.6, 21.6])
CLICKS = np.array([2, 6, 10, 14, 18, 22])


def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def linear(rgb):
    return np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4).astype(np.float32)


def display(rgb):
    rgb = np.maximum(rgb, 0)
    return np.where(rgb <= .0031308, 12.92*rgb, 1.055*rgb**(1/2.4)-.055)


def fitted_image(path, width, height):
    im = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)/255
    ih, iw = im.shape[:2]
    scale = min(width/iw, height/ih)
    resized = cv2.resize(im, (round(iw*scale), round(ih*scale)), interpolation=cv2.INTER_AREA)
    out = np.zeros((height,width,3),np.float32)
    y,x = (height-resized.shape[0])//2,(width-resized.shape[1])//2
    out[y:y+resized.shape[0],x:x+resized.shape[1]] = resized
    return out


class Boundary:
    def __init__(self, workspace, width, height):
        self.w, self.h = width, height
        rows = json.loads((workspace/'selections.json').read_text())
        self.paths = [workspace/'refs'/f"{r['selected']}.png" for r in rows]
        self.images = [fitted_image(p,width,height) for p in self.paths]
        self.times = MILESTONES[:len(self.images)]
        self.y,self.x=np.mgrid[:height,:width].astype(np.float32)
        self.flows=[]
        for a,b in zip(self.images,self.images[1:]):
            ga=cv2.cvtColor(np.uint8(a*255),cv2.COLOR_RGB2GRAY)
            gb=cv2.cvtColor(np.uint8(b*255),cv2.COLOR_RGB2GRAY)
            ab=cv2.calcOpticalFlowFarneback(ga,gb,None,.5,4,31,4,7,1.5,0)
            ba=cv2.calcOpticalFlowFarneback(gb,ga,None,.5,4,31,4,7,1.5,0)
            self.flows.append((ab,ba))

    def at(self,t):
        i=min(max(0,np.searchsorted(self.times,t,side='right')-1),len(self.images)-1)
        if i==len(self.images)-1:
            return linear(self.images[i])
        u=float(smooth((t-self.times[i])/(self.times[i+1]-self.times[i])))
        ab,ba=self.flows[i]
        a=cv2.remap(self.images[i],self.x-u*ab[...,0],self.y-u*ab[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        b=cv2.remap(self.images[i+1],self.x-(1-u)*ba[...,0],self.y-(1-u)*ba[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        return linear(a*(1-u)+b*u)


class Film:
    def __init__(self,workspace,width=1080,field_width=576):
        self.ws=Path(workspace)
        self.width=width
        self.height=round(width*16/9)
        self.fw=field_width
        self.fh=round(field_width*16/9)
        self.boundary=Boundary(self.ws,self.fw,self.fh)
        self.py,self.px=np.mgrid[:self.fh,:self.fw].astype(np.float32)
        self.dx=9/self.fw
        self.x=(self.px-self.fw/2)*self.dx
        self.y=(self.py-self.fh/2)*self.dx
        self.pad=(self.fh//4,self.fw//4)
        self.op=Fresnel((self.fh+2*self.pad[0],self.fw+2*self.pad[1]),self.dx)
        self.crop=(slice(self.pad[0],self.pad[0]+self.fh),slice(self.pad[1],self.pad[1]+self.fw))
        yy,xx=np.mgrid[:self.height,:self.width].astype(np.float32)
        self.end_r=np.sqrt(((xx-self.width*.5)/self.width)**2+((yy-self.height*.5)/self.width)**2)
        self.last_stats={}
        self.last_fields=None

    def fields(self,t):
        p=float(np.clip(t/22,0,1))
        source=self.boundary.at(t)
        ph,ripple=phase_screen(self.x,self.y,t)
        # Perceived forward travel and parallax are authored; wave propagation below is numerical.
        zoom=.84+1.85*p**1.7
        angle=.045*np.sin(.23*t)-.035*p
        ca,sa=np.cos(angle),np.sin(angle)
        rx=ca*self.x+sa*self.y
        ry=-sa*self.x+ca*self.y
        radius=np.sqrt(rx*rx+ry*ry+1e-6)
        # A slow, spatially varying fold flex; traveling pulse adds displacement.
        breath=.035*np.sin(.43*t+1.9*ry)+.025*np.sin(.71*t-1.3*rx)
        bend=(breath+.19*ripple)*(1+.5*p)
        fields=[]
        colors=[]
        errors=[]
        for j,off in enumerate([-1,0,1]):
            localzoom=zoom*(1+off*(.018+.020*p))
            separation=(.035+.18*p**1.6)*off
            sx=(rx+bend*rx/(radius+.2))/localzoom-separation*np.cos(.21*t)
            sy=(ry+bend*ry/(radius+.2))/localzoom-separation*np.sin(.21*t)
            sx += .035*off*np.sin(.41*t+ry*.8)
            sy += .020*off*np.sin(.29*t+rx)
            mapx=(sx/self.dx+self.fw/2).astype(np.float32)
            mapy=(sy/self.dx+self.fh/2).astype(np.float32)
            rgb=cv2.remap(source,mapx,mapy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
            lum=np.maximum(rgb @ np.array([.2126,.7152,.0722],np.float32),0)
            # Three displaced coherent amplitudes with distinct carrier tilt and curvature.
            phase=off*((3.1+.65*p)*self.x+(1.8+.4*p)*self.y+.10*(self.x**2-self.y**2))
            phase += (.24,-.13,.37)[j]*t+(.15,.0,-.35)[j]+ph*(1+.15*off)
            psi=(np.sqrt(lum/3)*np.exp(1j*phase)).astype(np.complex64)
            padded=np.pad(psi,((self.pad[0],self.pad[0]),(self.pad[1],self.pad[1])))
            propagated=self.op.propagate(padded,.08+.19*p+.015*j)
            before=np.sum(np.abs(padded)**2,dtype=np.float64)
            after=np.sum(np.abs(propagated)**2,dtype=np.float64)
            errors.append(float(abs(after/max(before,1e-20)-1)))
            fields.append(propagated[self.crop])
            colors.append(rgb)
        fields=np.stack(fields)
        total,coherent,incoherent,cross=interference(fields)
        color=np.sum(colors,axis=0)/3
        color_luma=color @ np.array([.2126,.7152,.0722],np.float32)
        chroma=np.clip(color/(color_luma[...,None]+.008),.45,1.9)
        rgb=coherent[...,None]*chroma
        # A faint phase tint makes changing relative phase legible in near-white material.
        phase=np.angle(total)
        tint=np.stack([.94+.06*np.cos(phase+1.2),.94+.06*np.cos(phase),1+.08*np.cos(phase-1.2)],axis=-1)
        rgb*=tint
        visible=incoherent>max(float(incoherent.max())*.02,1e-6)
        self.last_stats={'time':float(t),'energyRelativeErrorMax':max(errors),
            'crossIdentityMaxError':float(np.max(np.abs(coherent-incoherent-cross))),
            'coherentPower':float(np.sum(coherent,dtype=np.float64)),
            'incoherentPower':float(np.sum(incoherent,dtype=np.float64)),
            'destructiveFraction':float(np.mean((coherent[visible]<.22*incoherent[visible]))) if visible.any() else 0,
            'constructiveFraction':float(np.mean((coherent[visible]>1.6*incoherent[visible]))) if visible.any() else 0,
            'zoom':zoom,'finite':bool(np.isfinite(rgb).all())}
        self.last_fields={'branches':fields,'coherent':coherent,'incoherent':incoherent,'cross':cross,'phase':phase}
        return rgb

    def frame(self,frame):
        t=frame/FPS
        if t>=22.12:
            return self.ending(t)
        rgb=self.fields(t)
        p=t/22
        gain=.65+.85*p
        transient=sum((.025,.045,.08,.13,.22,.8)[j]*np.exp(-max(0,t-v)/.17) for j,v in enumerate(CLICKS) if t>=v)
        rgb*=gain*(1+transient)
        if t>=22:
            rgb*=max(0,1-(t-22)/.12)**2
        # Bloom is computed from HDR intensity before the display transform.
        bloom=cv2.GaussianBlur(rgb,(0,0),1.6)
        halo=cv2.GaussianBlur(rgb,(0,0),8.5)
        rgb=rgb+.28*bloom+.12*halo
        rgb=1-np.exp(-rgb*2.6)
        rgb=display(rgb)
        rgb=cv2.resize(rgb,(self.width,self.height),interpolation=cv2.INTER_CUBIC)
        return np.uint8(np.clip(rgb*255+.5,0,255))

    def ending(self,t):
        if t>=23.5:
            return np.full((self.height,self.width,3),255,np.uint8)
        r=self.end_r
        expansion=float(smooth((t-22.55)/.95))
        if expansion<=0:
            point=np.exp(-.5*(r/(1.25/self.width))**2)
            halo=.055*np.exp(-.5*(r/(9/self.width))**2)
            im=np.clip(point+halo,0,1)
        else:
            radius=.0015+1.3*expansion**2
            edge=.0015+.035*expansion
            im=np.clip(.5-(r-radius)/edge,0,1)
            im=smooth(im)
            im+=.13*np.exp(-np.maximum(r-radius,0)/(edge*4))
            im=np.clip(im,0,1)
        return np.repeat(np.uint8(im[...,None]*255+.5),3,axis=-1)


def contact(images,labels,out,thumb_width=270):
    th=round(thumb_width*16/9)
    cols=3
    rows=(len(images)+cols-1)//cols
    canvas=Image.new('RGB',(cols*thumb_width,rows*(th+32)),(15,17,23))
    draw=ImageDraw.Draw(canvas)
    for i,(im,label) in enumerate(zip(images,labels)):
        x=(i%cols)*thumb_width;y=(i//cols)*(th+32)
        canvas.paste(Image.fromarray(im).resize((thumb_width,th)),(x,y))
        draw.text((x+8,y+th+8),label,fill=(220,226,238))
    canvas.save(out)


def main(film_class=Film, recipe=__file__, snapshots=(0,132,264,396,528,648)):
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['preview','render','verify'])
    p.add_argument('--workspace',default='data/workspace/wavefield-v1')
    p.add_argument('--width',type=int,default=1080)
    p.add_argument('--field-width',type=int,default=576)
    p.add_argument('--output',default='previews/picture-v1.mp4')
    p.add_argument('--step',type=int,default=1)
    p.add_argument('--preview-prefix',default='v1')
    p.add_argument('--start-frame',type=int,default=0)
    p.add_argument('--frames',type=int,default=FRAMES)
    a=p.parse_args();w=Path(a.workspace)
    if a.step<1 or a.start_frame<0 or a.frames<1 or a.start_frame+a.frames>FRAMES:
        raise ValueError('Render range must be inside the 720-frame timeline.')
    if a.command=='verify':
        report=verify();(w/'qa/numerical-verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2));assert report['passed'];return
    film=film_class(w,a.width,a.field_width)
    if a.command=='preview':
        times=getattr(film,'preview_times',[.5,4.4,8.8,13.2,17.6,21.6,22.07,22.4,23.0])
        images=[]
        for t in times:
            im=film.frame(round(t*FPS));images.append(im)
            Image.fromarray(im).save(w/'previews'/f'{a.preview_prefix}-frame-{t:05.2f}.png')
            print(json.dumps(film.last_stats),flush=True)
        contact(images,[f'{t:.2f} s' for t in times],w/'previews'/f'contact-{a.preview_prefix}.jpg')
        return
    out=w/a.output
    if out.exists():raise ValueError('Refusing to replace render; choose a new output version.')
    out.parent.mkdir(parents=True,exist_ok=True)
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-f','rawvideo','-pix_fmt','rgb24',
         '-s',f'{film.width}x{film.height}','-r',str(FPS/a.step),'-i','pipe:0','-an',
         '-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
         '-c:v','libx264','-preset','slow','-crf','15','-pix_fmt','yuv420p','-color_range','tv',
         '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
         '-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
         '-movflags','+faststart',str(out)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    stats=[];start=time.monotonic()
    snapshot_dir=w/'simulation'/out.stem
    snapshot_dir.mkdir(exist_ok=False)
    try:
        for frame in range(a.start_frame,a.start_frame+a.frames,a.step):
            im=film.frame(frame)
            process.stdin.write(im.tobytes())
            if frame<=660:stats.append({'frame':frame,**film.last_stats})
            if frame in snapshots and film.last_fields is not None:
                np.savez_compressed(snapshot_dir/f'field-{frame:04d}.npz',**film.last_fields)
            if frame%60==0:
                print(json.dumps({'frame':frame,'frames':a.frames,'elapsedSeconds':round(time.monotonic()-start,1)}),flush=True)
    finally:
        process.stdin.close()
    if process.wait()!=0:raise RuntimeError('Encoder failed')
    report={'artifact':str(out.relative_to(w)),'sha256':digest(out),
            'startFrame':a.start_frame,'frames':len(range(a.start_frame,a.start_frame+a.frames,a.step)),
            'fps':FPS/a.step,'width':film.width,'height':film.height,'fieldWidth':film.fw,'fieldHeight':film.fh,
            'paddedFieldShape':list(film.op.shape),'spacing':film.dx,'k0':film.op.k0,
            'sourceImages':[{'path':str(p.relative_to(w)),'sha256':digest(p)} for p in film.boundary.paths],
            'recipeSha256':digest(recipe),'renderCodeSha256':digest(__file__),
            'fieldCodeSha256':digest(Path(__file__).with_name('field.py')),
            'maxPropagationEnergyRelativeError':max(s['energyRelativeErrorMax'] for s in stats),
            'maxCrossIdentityError':max(s['crossIdentityMaxError'] for s in stats),
            'allFinite':all(s['finite'] for s in stats),'renderSeconds':round(time.monotonic()-start,2)}
    if hasattr(film,'recipe_metadata'):
        report.update(film.recipe_metadata())
    (out.with_suffix('.render.json')).write_text(json.dumps(report,indent=2)+'\n')
    (w/'simulation'/f'{out.stem}-frame-metrics.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
