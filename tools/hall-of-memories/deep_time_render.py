#!/usr/bin/env python3
"""Deterministic painted-relief animation, streamed to video without frame dumps.

Generated originals remain untouched. All warps, mattes and articulated pieces
are evaluated as animation at render time. Coordinates below refer to the
retained 1672 x 941 artwork. This is a 2.5D recipe, not a volumetric Earth model.
"""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
cv2.setNumThreads(4)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)


def interval(t, a, b):
    return float(smooth((t-a)/(b-a)))


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def translation(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], dtype=np.float32)


def hinge(pivot, degrees=0, sy=1):
    a = math.radians(degrees)
    m = np.array([[math.cos(a), -math.sin(a)*sy, 0],
                  [math.sin(a), math.cos(a)*sy, 0], [0, 0, 1]], np.float32)
    return translation(*pivot) @ m @ translation(-pivot[0], -pivot[1])


class Renderer:
    def __init__(self, root, width=1920):
        self.root = root
        self.w, self.h = width, round(width*9/16)
        self.plan = json.loads((root/'timeline.json').read_text())
        self.x, self.y = np.meshgrid(np.linspace(0, 1, self.w, dtype=np.float32),
                                    np.linspace(0, 1, self.h, dtype=np.float32))
        self.plates = {}
        for name in ['dry', 'ice', 'green', 'interior', 'clearing', 'jewel']:
            a = np.array(Image.open(root/'assets'/f'{name}.png').convert('RGB'))
            self.plates[name] = cv2.resize(a, (self.w, self.h), interpolation=cv2.INTER_LANCZOS4)
        self.raw = {}
        for name in ['ship', 'explorer']:
            a = np.array(Image.open(root/'assets'/f'{name}.png').convert('RGBA')).astype(np.float32)/255
            a[a[:, :, 3] < 8/255, 3] = 0  # suppress almost-transparent matte noise
            a[:, :, :3] *= a[:, :, 3:4]  # premultiplied filtering avoids black fringes
            self.raw[name] = a
        self.make_rigs()
        self.field = self.x*.60 + self.y*.20 + .11*np.sin(self.x*7+self.y*4)
        self.field = (self.field-self.field.min())/(self.field.max()-self.field.min())
        self.subtitle = None
        self.telemetry = []

    def piece(self, source, mask):
        src = self.raw[source]
        ys, xs = np.where((mask*src[:, :, 3]) > .002)
        if not len(xs):
            raise ValueError('Empty articulated piece')
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1
        a = src[y0:y1, x0:x1].copy()*mask[y0:y1, x0:x1, None]
        return a, (x0, y0)

    def polygon(self, points):
        m = np.zeros((941, 1672), np.float32)
        cv2.fillPoly(m, [np.array(points, np.int32)], 1)
        return m

    def make_rigs(self):
        head = self.polygon([(738,0),(940,0),(940,177),(885,216),(796,219),(738,158)])
        left = self.polygon([(698,214),(775,227),(777,300),(724,380),(715,472),
                             (731,605),(689,646),(625,608),(620,505),(644,403),(668,302)])
        right = self.polygon([(888,251),(933,293),(954,386),(1004,438),(1048,551),
                              (1035,623),(963,627),(960,534),(926,450),(891,385)])
        leg_l = self.polygon([(750,496),(840,496),(832,615),(778,738),(778,817),
                              (793,941),(628,941),(634,816),(689,716),(719,610)])
        leg_r = self.polygon([(835,498),(914,498),(926,624),(924,767),(1045,850),
                              (1045,941),(826,941),(828,807),(848,741),(845,620)])
        masks = {'head':head,'left':left,'right':right,'leg_l':leg_l,'leg_r':leg_r}
        union = np.maximum.reduce(list(masks.values()))
        masks['body'] = 1-union
        self.explorer = {k:self.piece('explorer', m) for k,m in masks.items()}
        # These pieces are attached below the hull and compress towards their
        # hinges in flight. Their stored source pixels never change.
        gear_l = self.polygon([(266,483),(344,508),(313,586),(230,715),(310,747),
                               (310,792),(48,792),(64,741),(187,552)])
        gear_c = self.polygon([(573,602),(647,608),(666,695),(737,708),(742,753),
                               (546,756),(542,706),(584,688)])
        gear_r = self.polygon([(1205,626),(1280,648),(1407,807),(1518,823),
                               (1520,870),(1238,867),(1200,826),(1270,789),(1197,690)])
        ramp = self.polygon([(849,567),(989,577),(942,694),(869,780),(720,779),
                             (725,724),(802,655)])
        masks = {'left':gear_l,'middle':gear_c,'right':gear_r,'ramp':ramp}
        masks['body'] = 1-np.maximum.reduce(list(masks.values()))
        self.ship = {k:self.piece('ship', m) for k,m in masks.items()}
        # Feather only the outer edge of the retained rock-and-jewel image.
        edge = np.minimum.reduce([self.x, 1-self.x, self.y, 1-self.y])
        m = np.asarray(smooth(edge/.09), np.float32)
        rgb = self.plates['jewel'].astype(np.float32)/255
        self.jewel_full = (np.dstack([rgb*m[:,:,None], m]), (0,0))
        mineral=((rgb[:,:,1]>rgb[:,:,0]*1.6)&(rgb[:,:,1]>rgb[:,:,2]*1.25)&(rgb[:,:,1]>.07)).astype(np.uint8)
        k=max(3,round(self.w*.004)//2*2+1)
        mineral=cv2.dilate(mineral,np.ones((k,k),np.uint8)).astype(np.float32)
        mineral=cv2.GaussianBlur(mineral,(3,3),0)
        self.jewel = (np.dstack([rgb*mineral[:,:,None], mineral]), (0,0))

    def paste(self, dst, piece, matrix, opacity=1):
        if opacity <= 0:
            return
        a, (ox,oy) = piece
        m = matrix @ translation(ox,oy)
        ah, aw = a.shape[:2]
        corners = m @ np.array([[0,aw,aw,0],[0,0,ah,ah],[1,1,1,1]],np.float32)
        x0=max(0, math.floor(float(corners[0].min()))-2)
        y0=max(0, math.floor(float(corners[1].min()))-2)
        x1=min(self.w, math.ceil(float(corners[0].max()))+2)
        y1=min(self.h, math.ceil(float(corners[1].max()))+2)
        if x1<=x0 or y1<=y0:
            return
        local = translation(-x0,-y0) @ m
        b=cv2.warpAffine(a,local[:2],(x1-x0,y1-y0),flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT)*opacity
        old=dst[y0:y1,x0:x1].astype(np.float32)
        dst[y0:y1,x0:x1]=np.clip(b[:,:,:3]*255+old*(1-b[:,:,3:4]),0,255).astype(np.uint8)

    def sample(self, name, u, v, reflect=False):
        return cv2.remap(self.plates[name],np.asarray(u*self.w,np.float32),
                         np.asarray(v*self.h,np.float32),cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT_101 if reflect else cv2.BORDER_REPLICATE)

    def surface(self, t, state='dry', crop=(0,0,1,1)):
        cx,cy,cw,ch=crop
        u=cx+self.x*cw;v=cy+self.y*ch
        lower=smooth((v-.32)/.48)
        phase=t*.045
        u=u+.012*np.sin(v*5+phase)*lower
        v=v+.023*np.sin(u*5.7+phase)*lower
        a=self.sample(state,.03+.94*u,.025+.94*v)
        return a

    def wipe(self, a, b, amount, reverse=False):
        if amount<=0:return a
        if amount>=1:return b
        field=1-self.field if reverse else self.field
        mask=np.clip((amount*1.12-.06-field)/.045+.5,0,1).astype(np.float32)
        return np.clip(a*(1-mask[:,:,None])+b*mask[:,:,None],0,255).astype(np.uint8)

    def gem_overlay(self, a, t):
        if t<.625:
            return self.plates['jewel'].copy()
        q=interval(t,.625,9)
        scale=math.exp(math.log(.027)*q)
        gx=.61+.012*math.sin(.76*5+t*.045)
        gy=.76+.023*math.sin(.61*5.7+t*.045)
        px=.50+(gx-.50)*q;py=.50+(gy-.50)*q
        m=translation(px*self.w,py*self.h) @ np.diag([scale,scale,1]).astype(np.float32) @ translation(-self.w*.5,-self.h*.5)
        # Full-frame source to a tiny physical housing: a deliberate scale change.
        self.paste(a,self.jewel_full,m,1-interval(t,.75,2.7))
        self.paste(a,self.jewel,m)
        if q<.16:
            blend=interval(q,0,.16)
            a=(a*blend+self.plates['jewel']*(1-blend)).astype(np.uint8)
        return a

    def buried_gem(self,a,t,depth=0):
        y=.76+.023*math.sin(.61*5.7+t*.045)-depth
        x=.61+.012*math.sin(.76*5+t*.045)
        m=translation(x*self.w,y*self.h) @ np.diag([.027,.027,1]).astype(np.float32) @ translation(-self.w*.5,-self.h*.5)
        self.paste(a,self.jewel,m)

    def interior(self,t,depth):
        world_y=self.y+depth
        phase=t*.045
        # Surface transitions to a continuous mineral tapestry as the camera
        # translates downward. Reflection extends the artwork without seams.
        lower=smooth((world_y-.30)/.5)
        u=self.x+.012*np.sin(world_y*5+phase)*lower
        v=world_y+.023*np.sin(u*5.7+phase)*lower
        top=self.sample('ice',.03+.94*u,.025+.94*v,True)
        di=.56*world_y+.085*np.sin(self.x*3+phase)
        du=.10+self.x*.78+.06*np.sin(world_y*1.1+phase)
        deep=self.sample('interior',du,di,True)
        warm=smooth((world_y-1.6)/1.6)
        mult=np.stack([1-.06*warm,1-.23*warm,1-.35*warm],axis=2)
        deep=np.clip(deep*mult,0,255).astype(np.uint8)
        join=smooth((world_y-.90)/.30)*float(smooth(depth/.20))
        a=(top*(1-join[:,:,None])+deep*join[:,:,None]).astype(np.uint8)
        if depth<1:self.buried_gem(a,t,depth)
        return a

    def forest(self,t,crop):
        cx,cy,cw,ch=crop
        u=cx+self.x*cw;v=cy+self.y*ch
        # Small held shifts in foliage; the clearing remains fixed under feet.
        leaves=(1-smooth((v-.45)/.17))*(.5+.5*np.sin(u*5)**2)
        u=u+.0012*math.sin(t*1.15)*leaves
        return self.sample('clearing',u,v)

    def screen(self, x,y,crop):
        cx,cy,cw,ch=crop
        return (x-cx)*self.w/cw,(y-cy)*self.h/ch

    def shadow(self,a,x,y,width,height,crop,strength=.20):
        sx,sy=self.screen(x,y,crop)
        rx=max(1,round(width*self.w/crop[2]));ry=max(1,round(height*self.h/crop[3]))
        if sx+rx<0 or sx-rx>=self.w or sy+ry<0 or sy-ry>=self.h:return
        mask=np.zeros((self.h,self.w),np.uint8)
        cv2.ellipse(mask,(round(sx),round(sy)),(rx,ry),0,0,360,255,-1)
        k=max(3,round(self.w*.004)//2*2+1)
        mask=cv2.GaussianBlur(mask,(k,k),0).astype(np.float32)*(strength/255)
        a[:]=np.clip(a*(1-mask[:,:,None]),0,255).astype(np.uint8)

    def draw_ship(self,a,t,crop):
        if t<80 or t>=120:return
        landing=interval(t,80,87.5)
        leaving=interval(t,116,120)
        x=.43+.43*leaving
        y=.66-1.20*(1-landing)-1.30*leaving
        width=.48*(1-.35*leaving)
        sx,sy=self.screen(x,y,crop)
        scale=width*self.w/(1620*crop[2])
        m=translation(sx,sy) @ np.diag([scale,scale,1]).astype(np.float32) @ translation(840,0) @ translation(-1672/2-840,-856)
        # The matrix above anchors the center of the source at its lowest foot.
        self.shadow(a,x,.668,width*.35,.012,crop,.24*landing*(1-leaving))
        deployed=interval(t,83,86.5)*(1-interval(t,116.5,118.7))
        for part,pivot,sign in [('left',(280,525),1),('middle',(615,620),0),('right',(1240,654),-1)]:
            self.paste(a,self.ship[part],m @ hinge(pivot,sign*8*(1-deployed),.22+.78*deployed))
        self.paste(a,self.ship['body'],m)
        self.paste(a,self.ship['ramp'],m @ hinge((916,583),0,.04+.96*deployed))

    def crew_state(self,t,j):
        end=[(.665,.835,.282),(.552,.810,.245)][j]
        start=[(.466,.621,.108),(.447,.613,.096)][j]
        if t<90:return None
        if t<102:
            p=interval(t,90+j*.8,98+j*.5)
            vals=tuple(a+(b-a)*p for a,b in zip(start,end))
            walk=1 if 90+j*.8<t<98+j*.5 else 0
            phase=(t-90-j*.8)*1.25*math.tau
            return (*vals,walk,phase,False)
        if t<111:return (*end,0,0,False)
        if t<115.75:
            begin,finish=[(111,114.25),(113,115.70)][j]
            p=interval(t,begin,finish)
            door=[(.452,.548,.083),(.447,.545,.081)][j]
            vals=tuple(b+(a-b)*p for a,b in zip(door,end))
            if p>.985:return None
            return (*vals,1 if t>begin else 0,(t-begin)*1.5*math.tau,True)
        return None

    def draw_explorer(self,a,t,j,crop):
        state=self.crew_state(t,j)
        if state is None:return
        x,y,height,walk,phase,returning=state
        step=math.sin(phase)*walk
        bob=abs(math.sin(phase))*1.9*walk
        sx,sy=self.screen(x,y,crop)
        self.shadow(a,x,y-.004,height*.092,.006,crop,.20)
        scale=height*self.h/(922*crop[3])
        # Both emerge toward screen right. The closer two-shot reverses the
        # lead's eyeline toward the companion; both face left when boarding.
        flip=-1 if returning or (102<=t<111 and j==0) else 1
        m=translation(sx,sy-bob*self.h/1080/crop[3]) @ np.diag([scale*flip,scale,1]).astype(np.float32) @ translation(-831,-931)
        speech=interval(t,103.1,104.0)*(1-interval(t,107.2,108.4)) if j==0 else 0
        nod=(-6*interval(t,102.6,103.6)+8*interval(t,108,109.3)) if j==0 else 3*interval(t,105.7,107)
        gestures={'leg_l':((793,502),step*7),'leg_r':((875,500),-step*7),
                  'left':((739,260),-step*4-12*speech),'right':((913,293),step*4+8*speech),
                  'head':((840,208),nod)}
        for name in ['leg_r','leg_l','right','body','left','head']:
            local=hinge(*gestures[name]) if name in gestures else np.eye(3,dtype=np.float32)
            self.paste(a,self.explorer[name],m @ local)

    def add_subtitle(self,a):
        if self.subtitle is None:
            im=Image.new('RGBA',(self.w,self.h))
            draw=ImageDraw.Draw(im)
            candidates=['/System/Library/Fonts/Supplemental/Arial.ttf','/System/Library/Fonts/Helvetica.ttc']
            font_path=next((x for x in candidates if Path(x).exists()),None)
            font=ImageFont.truetype(font_path,round(self.h*.043)) if font_path else ImageFont.load_default()
            text=self.plan['subtitle']['text'];box=draw.textbbox((0,0),text,font=font,stroke_width=2)
            tw=box[2]-box[0];x=(self.w-tw)/2;y=self.h*.895
            draw.rounded_rectangle((x-24,y-12,x+tw+24,y+self.h*.060),radius=8,fill=(8,10,9,180))
            draw.text((x,y),text,font=font,fill=(248,245,230,255),stroke_width=2,stroke_fill=(10,12,10,240))
            self.subtitle=np.array(im).astype(np.float32)/255
        b=self.subtitle
        return np.clip(a*(1-b[:,:,3:4])+b[:,:,:3]*b[:,:,3:4]*255,0,255).astype(np.uint8)

    def frame(self,t):
        # Quantized source poses are authored at 8 Hz and held three output frames.
        t=math.floor((t+1e-7)*8)/8
        if t<9:
            return self.gem_overlay(self.surface(t),t)
        if t<26:
            a=self.surface(t)
            a=self.wipe(a,self.surface(t,'ice'),interval(t,17,24.5))
            self.buried_gem(a,t)
            return a
        if t<62:
            if t<38:depth=2.15*interval(t,26,38)
            elif t<50:depth=2.15+.55*interval(t,38,50)
            else:depth=2.70*(1-interval(t,50,62))
            return self.interior(t,depth)
        if t<74:
            ice=self.surface(t,'ice');dry=self.surface(t,'dry');green=self.surface(t,'green')
            a=self.wipe(ice,dry,interval(t,62,67),True)
            a=self.wipe(a,green,interval(t,66.5,73),True)
            self.buried_gem(a,t)
            return a
        crop=(.435,.395,.47,.47) if 102<=t<111 else (0,0,1,1)
        a=self.forest(t,crop)
        # At the ramp, hull occlusion makes entrance/exit disappear inside the craft.
        behind=[];front=[]
        for j in [1,0]:
            state=self.crew_state(t,j)
            if state is not None:(behind if state[1]<.628 else front).append(j)
        front.sort(key=lambda j:self.crew_state(t,j)[1])
        for j in behind:self.draw_explorer(a,t,j,crop)
        self.draw_ship(a,t,crop)
        for j in front:self.draw_explorer(a,t,j,crop)
        sub=self.plan['subtitle']
        if sub['start']<=t<sub['end']:a=self.add_subtitle(a)
        return a


def prepare(root):
    plan=json.loads((HERE/'deep_time.json').read_text())
    save(root/'timeline.json',plan)
    for path in ['render-v1','qa/keyframes','audio','edit-v1/review','edit-v1/masters','recipe']:
        (root/path).mkdir(parents=True,exist_ok=True)
    for name in ['deep_time.json','deep_time_render.py']:
        shutil.copy2(HERE/name,root/'recipe'/name)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--stills',action='store_true');ap.add_argument('--render',action='store_true')
    ap.add_argument('--width',type=int,default=1920);ap.add_argument('--times',default='0,4,9,20,29,34,43,55,65,72,78,86,92,97,104.5,108,113,117,120.5')
    args=ap.parse_args();root=args.run.resolve();prepare(root);r=Renderer(root,args.width)
    if args.stills:
        paths=[]
        for t in [float(x) for x in args.times.split(',')]:
            p=root/'qa/keyframes'/f'{t:07.3f}-{args.width}.png'
            Image.fromarray(r.frame(t)).save(p);paths.append(str(p.relative_to(root)))
        print(json.dumps({'keyframes':paths}),flush=True)
    if args.render:
        output=root/'render-v1/picture.mp4'
        if output.exists():raise SystemExit('Refusing to overwrite existing render')
        if shutil.disk_usage(root).free<750*1024**2:raise SystemExit('Insufficient render reserve')
        duration=r.plan['duration'];count=round(duration*8)
        cmd=['ffmpeg','-v','error','-nostdin','-f','rawvideo','-pix_fmt','rgb24','-s',f'{r.w}x{r.h}',
             '-r','8','-i','pipe:0','-an','-vf','fps=24,scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p','-frames:v',str(count*3),
             '-c:v','libx264','-preset','medium','-crf','16','-color_primaries','bt709',
             '-color_trc','bt709','-colorspace','bt709','-video_track_timescale','12288','-movflags','+faststart',str(output)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        pose_hashes=[];means=[]
        try:
            for i in range(count):
                frame=r.frame(i/8)
                means.append(float(frame.mean()))
                if means[-1]<2:raise RuntimeError(f'Unexpected dark frame at pose {i}')
                pose_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
                proc.stdin.write(frame.tobytes())
                if i%80==0:print(f'Rendered {i}/{count} poses ({i/8:.1f}s)',flush=True)
            proc.stdin.close()
            if proc.wait()!=0:raise RuntimeError('FFmpeg render failed')
        except BaseException:
            proc.kill();raise
        save(root/'qa/source-pose-hashes.json',{'rate':8,'count':count,'hashes':pose_hashes})
        save(root/'qa/source-frame-audit.json',{'count':count,'mean_luma_min':min(means),'mean_luma_max':max(means),'unexpected_black_poses':[]})
        print(json.dumps({'output':str(output),'source_poses':count,'output_frames':count*3}),flush=True)


if __name__=='__main__':main()
