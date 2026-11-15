#!/usr/bin/env python3
"""Exact POLISH interface and photographed-screen composites; no provider calls."""
import argparse
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SW, SH = 1000, 2000
W, H, FPS, FRAMES = 1080, 1920, 24, 912
FONT = os.environ.get('POLISH_FONT', '/System/Library/Fonts/HelveticaNeue.ttc')
BG = (19, 23, 28)
INK = (239, 241, 242)
MUTED = (146, 154, 165)
BLUE = (79, 133, 169)
EVENTS = []


def typing(start, text, steps=.105, pauses=None):
    out = []
    cursor = start
    for i, c in enumerate(text):
        cursor += (pauses or {}).get(i, steps * (1 + .15 * math.sin(i * 2.8)))
        out.append((round(cursor, 4), c))
    return out


FIRST = [(1.35+i*.115,c) for i,c in enumerate('Pretty ter')]
FIRST += [(3.05,'r'),(3.36,'i'),(3.75,'b'),(3.95,'l'),(4.13,'e'),(4.29,'.')]
SECOND = typing(8.05, 'Maybe later.', .115)
THIRD = typing(15.08, 'Not really. I need you.', .132, {3:.34,11:.34})
FOURTH = typing(24.62, 'Please stop.', .13, {7:.28})
for group in [FIRST,SECOND,THIRD,FOURTH]:
    EVENTS.extend({'at':t,'kind':'key','char':c} for t,c in group)
EVENTS += [{'at':x,'kind':'notification'} for x in (.7,7.1,13.65,34.0)]
EVENTS += [{'at':x,'kind':'send'} for x in (5.65,11.65,32.2)]
EVENTS += [{'at':x,'kind':'tap'} for x in (10.8,19.55,22.5,24.18,27.32,28.75,31.45)]
EVENTS.sort(key=lambda x:x['at'])


@lru_cache(None)
def font(size):
    return ImageFont.truetype(FONT, size)


def label(d, xy, text, size=52, fill=INK, anchor=None):
    d.text(xy,text,font=font(size),fill=fill,anchor=anchor,stroke_width=0)


def rr(d, box, fill, radius=30, outline=None, width=1):
    d.rounded_rectangle(tuple(int(x) for x in box),radius=radius,fill=fill,outline=outline,width=width)


def lines(text, size, width):
    out=[];line=''
    for word in text.split(' '):
        trial=(line+' '+word).strip()
        if font(size).getlength(trial)>width and line:
            out.append(line);line=word
        else:line=trial
    if line:out.append(line)
    return out or ['']


def thumb(d,x,y,scale=1,color=(224,184,117)):
    # Original monochrome emoji-like hand glyph; not a borrowed messenger asset.
    p=np.array([(0,28),(15,28),(28,9),(31,-13),(41,-16),(48,-9),(47,17),
                (72,17),(81,23),(81,35),(75,40),(75,51),(69,57),(68,67),
                (60,74),(27,74),(15,65),(0,65)])*scale+np.array([x,y])
    d.polygon([tuple(q) for q in p],fill=color)
    rr(d,(x-10*scale,y+26*scale,x+11*scale,y+70*scale),(176,145,96),int(4*scale))


def current_text(t):
    if t<5.65:
        return ''.join(c for at,c in FIRST if at<=t)
    if 8<t<11.65:
        if t>=10.8:return 'In a little while?'
        return ''.join(c for at,c in SECOND if at<=t)
    if 15<t<24.18:
        return ''.join(c for at,c in THIRD if at<=t)
    if 24.62<t<32.2:
        if t>=31.45:return '👍'
        return ''.join(c for at,c in FOURTH if at<=t)
    return ''


def ui(t):
    im=Image.new('RGB',(SW,SH),BG);d=ImageDraw.Draw(im)
    d.rectangle((0,0,SW,212),fill=(24,28,33))
    label(d,(66,28),'20:14',32)
    for n in range(4):rr(d,(813+n*13,45-n*5,822+n*13,63),(201,206,211),3)
    rr(d,(887,33,949,66),None,8,(195,202,210),3)
    rr(d,(893,39,936,60),(195,202,210),4)
    d.rectangle((952,43,957,56),fill=(195,202,210))
    d.line([(75,115),(56,137),(75,159)],fill=INK,width=5)
    d.ellipse((109,96,186,173),fill=(63,75,86));label(d,(147,133),'J',38,INK,'mm')
    label(d,(212,99),'Jamie',49);label(d,(214,159),'Messages',27,MUTED)
    for y in (122,139,156):d.ellipse((923,y,930,y+7),fill=MUTED)
    d.line((0,211,SW,211),fill=(49,54,61),width=2)

    messages=[(-3,'in','Did you get home?'),(-2,'out','Yep. Thanks for tonight.'),(-1,'in','Anytime.'),
      (.7,'in','How was today?'),(5.65,'out','Pretty terrible.'),
      (7.1,'in','Want to talk?'),(11.65,'out','In a little while?'),
      (13.65,'in','You okay though?'),(32.2,'out','👍'),
      (34,'in','Good. I was worried about you.')]
    visible=[x for x in messages if x[0]<=t]
    heights=[]
    for _,_,text in visible:
        heights.append(128 if text=='👍' else 50+len(lines(text,58,750))*72)
    total=sum(heights)+28*max(0,len(heights)-1)+65+(65 if t>=.7 else 0)
    # Scroll only as an appended message needs room; preserve the newest exchange.
    offset=max(0,total-770)
    if visible and offset:
        lastat=visible[-1][0];prior=max(0,total-heights[-1]-28-770)
        ease=min(1,max(0,(t-lastat)/.25));ease=ease*ease*(3-2*ease)
        offset=prior+(offset-prior)*ease
    chat=Image.new('RGB',(SW,820),BG);c=ImageDraw.Draw(chat);y=18-offset
    label(c,(500,y+18),'Yesterday',27,MUTED,'mm');y+=65
    for (at,side,text),hh in zip(visible,heights):
        if at==.7:
            label(c,(500,y+18),'Today',27,MUTED,'mm');y+=65
        ls=lines(text,58,750);ww=160 if text=='👍' else max(font(58).getlength(s) for s in ls)+60
        x=42 if side=='in' else SW-ww-42
        rise=max(0,1-(t-at)/.18)*14
        rr(c,(x,y+rise,x+ww,y+hh+rise),(47,52,59) if side=='in' else (47,84,111),32)
        if text=='👍':thumb(c,x+51,y+42+rise,.72)
        else:
            for j,line in enumerate(ls):label(c,(x+30,y+22+j*72+rise),line,58)
        y+=hh+28
    im.paste(chat,(0,232));d=ImageDraw.Draw(im)
    if visible and visible[-1][1]=='out' and t-visible[-1][0]>.25:
        label(d,(947,1050),'Delivered',25,MUTED,'ra')
    if 33.08<t<34:
        rr(d,(44,966,190,1032),(47,52,59),28)
        for i in range(3):
            v=int(130+48*max(0,math.sin(t*5-i)))
            d.ellipse((74+i*33,990,86+i*33,1002),fill=(v,v+3,v+7))

    txt=current_text(t)
    blocked=(19.55<=t<31.45)
    enabled=bool(txt) and not blocked
    comp=(33,1096,967,1242)
    rr(d,comp,(28,33,39),38,(83,91,102),2)
    label(d,(67,1142),'+',47,MUTED)
    if txt=='👍':thumb(d,139,1146,.65)
    elif txt:
        ls=lines(txt,52,715)
        starty=1128 if len(ls)>1 else 1140
        for j,line in enumerate(ls):label(d,(134,starty+j*59),line,52)
        if int(t*2)%2==0:
            cx=134+font(52).getlength(ls[-1])+3
            d.line((cx,starty+(len(ls)-1)*59+5,cx,starty+(len(ls)-1)*59+55),fill=(113,176,217),width=3)
        if txt in ('Pretty ter','Pretty terr','Pretty terri'):
            suffix={'Pretty ter':'rific','Pretty terr':'ific','Pretty terri':'fic'}[txt]
            label(d,(134+font(52).getlength(txt),1140),suffix,52,(112,122,136))
    else:label(d,(134,1140),'Message',52,(107,117,130))
    sendcolor=BLUE if enabled else (56,63,72)
    if any(0<t-at<.14 for at in (5.65,11.65,19.55,22.5,27.32,28.75,32.2)):
        sendcolor=tuple(int(v*.72) for v in sendcolor)
    d.ellipse((865,1130,938,1203),fill=sendcolor)
    d.line((901,1185,901,1149),fill=INK if enabled else (127,135,145),width=5)
    d.line([(886,1163),(901,1148),(916,1163)],fill=INK if enabled else (127,135,145),width=5)

    # Identical quiet prediction controls as the content becomes coercive.
    d.rectangle((0,1262,SW,1434),fill=(25,30,36))
    if 2.38<t<5.65:
        label(d,(500,1331),'terrific',46,(209,216,224),'mm')
        d.line((295,1298,295,1361),fill=(57,64,74),width=2)
        d.line((705,1298,705,1361),fill=(57,64,74),width=2)
    elif (9.85<t<10.8) or (18.55<t<24.18) or (26.5<t<31.45):
        suggestion='In a little while?' if t<14 else ('I’m fine.' if t<24.18 else '👍')
        label(d,(58,1275),'Suggested',26,MUTED)
        rr(d,(42,1315,957,1394),(43,51,62),22)
        if suggestion=='👍':thumb(d,443,1336,.48)
        else:label(d,(500,1352),suggestion,49,INK,'mm')
        label(d,(910,1351),'×',36,MUTED,'mm')
    if blocked:label(d,(500,1412),'Apply suggestion to send',27,(177,185,195),'mm')
    d.rectangle((0,1440,SW,SH),fill=(36,42,50))
    keyevents=[e for e in EVENTS if e['kind']=='key' and 0<=t-e['at']<.10]
    lastchar=keyevents[-1]['char'].lower() if keyevents else None
    rows=[('qwertyuiop',38,1462,92),('asdfghjkl',87,1576,92),('zxcvbnm',183,1690,92)]
    for chars,x,y,step in rows:
        for i,ch in enumerate(chars):
            xx=x+i*step
            active=ch==lastchar
            rr(d,(xx,y,xx+82,y+96),(109,120,135) if active else (78,87,101),13)
            label(d,(xx+41,y+44),ch,48,INK,'mm')
    rr(d,(37,1690,164,1786),(58,66,79),13)
    d.line([(78,1741),(100,1716),(122,1741),(111,1741),(111,1761),(89,1761),(89,1741),(78,1741)],fill=INK,width=3)
    rr(d,(848,1690,966,1786),(58,66,79),13)
    d.line([(878,1738),(890,1720),(932,1720),(932,1756),(890,1756),(878,1738)],fill=INK,width=3)
    d.line((903,1730,919,1746),fill=INK,width=3);d.line((919,1730,903,1746),fill=INK,width=3)
    rr(d,(37,1805,198,1904),(58,66,79),13);label(d,(117,1854),'123',38,INK,'mm')
    rr(d,(220,1805,774,1904),(78,87,101),13);label(d,(497,1854),'space',34,INK,'mm')
    rr(d,(796,1805,966,1904),(58,66,79),13);label(d,(881,1854),'return',29,INK,'mm')
    rr(d,(371,1954,629,1964),(177,183,193),5)
    return im


class Renderer:
    def __init__(self,workspace):
        self.w=workspace
        self.plate=np.array(Image.open(workspace/'refs/A01-phone-v1.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS))
        # Observed screen corners on the generated plate, normalized to image.
        corners=np.float32([[.187,.130],[.805,.128],[.824,.869],[.144,.869]])*np.array([W,H],np.float32)
        self.hom=cv2.getPerspectiveTransform(np.float32([[0,0],[SW,0],[SW,SH],[0,SH]]),corners)
        m=Image.new('L',(SW,SH));ImageDraw.Draw(m).rounded_rectangle((0,0,SW,SH),radius=83,fill=255)
        self.mask=cv2.warpPerspective(np.array(m),self.hom,(W,H),flags=cv2.INTER_CUBIC).astype(np.float32)/255
        self.mask=cv2.GaussianBlur(self.mask,(0,0),.7)
        self.mask=self.mask[...,None]
        self.plateblur=cv2.GaussianBlur(self.plate,(0,0),7).astype(np.float32)
        rng=np.random.default_rng(421)
        self.grain=rng.normal(0,.65,(H,W,1)).astype(np.float32)

    def main(self,t):
        screen=np.array(ui(t))
        warped=cv2.warpPerspective(screen,self.hom,(W,H),flags=cv2.INTER_CUBIC).astype(np.float32)
        surface=warped*.91+self.plateblur*.105+(self.plate.astype(np.float32)-self.plateblur)*.25
        comp=self.plate*(1-self.mask)+surface*self.mask
        comp=np.clip(comp+self.grain,0,255).astype(np.uint8)
        # Crop slightly closer to the handset; minute camera breathing, not time stretching.
        scale=1.16+.0018*math.sin(t*.63)
        mat=cv2.getRotationMatrix2D((W/2,H*.52),.035*math.sin(t*.5),scale)
        mat[0,2]+=1.0*math.sin(t*.85);mat[1,2]+=.8*math.sin(t*.69)
        return Image.fromarray(cv2.warpAffine(comp,mat,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT))

    def macro(self,t):
        # The same exact interface, sampled as physical RGB display subpixels.
        a=np.asarray(ui(t)).astype(np.float32)
        lcd=np.repeat(np.repeat(a,3,axis=0),3,axis=1)
        for k in range(3):
            for channel in range(3):lcd[:,k::3,channel]*=1.12 if channel==k else .90
        lcd[2::3]*=.77
        lcd=np.clip(lcd,0,255).astype(np.uint8)
        source=np.float32([[180,1230],[850,1230],[850,1490],[180,1490]])*3
        dest=np.float32([[-105,800],[1155,385],[1230,1200],[-30,1615]])
        hom=cv2.getPerspectiveTransform(source,dest)
        out=cv2.warpPerspective(lcd,hom,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        # Gentle lens focus falloff around the slanted suggestion line.
        yy,xx=np.mgrid[0:H,0:W]
        distance=np.abs(yy-(1180-.33*xx))
        sharp=np.clip(1-distance/580,0,1)[...,None]
        blur=cv2.GaussianBlur(out,(0,0),2.0)
        out=out*sharp+blur*(1-sharp)
        flare=np.exp(-((xx-80)**2/(500**2)+(yy-180)**2/(800**2)))*3
        out+=flare[...,None]*np.array([1,.8,.6])
        out+=self.grain
        return Image.fromarray(np.clip(out,0,255).astype(np.uint8))

    def frame(self,t):
        return self.macro(t) if 20.45<=t<22.15 else self.main(t)


def main():
    p=argparse.ArgumentParser();p.add_argument('workspace',type=Path)
    p.add_argument('--stills',action='store_true');p.add_argument('--render')
    args=p.parse_args();r=Renderer(args.workspace)
    if args.stills:
        out=args.workspace/'qa/looks';out.mkdir(parents=True,exist_ok=True)
        for name,t in [('autofill',2.7),('terrible',4.9),('suggestion',10.1),('blocked',20.0),('macro',21.0),('thumb',27),('ending',35.5)]:
            r.frame(t).save(out/f'{name}-v1.png')
            ui(t).save(out/f'{name}-ui-v1.png')
        print(json.dumps({'stills':7,'directory':str(out)}),flush=True)
    (args.workspace/'edit/typing-cues.json').write_text(json.dumps(EVENTS,indent=2)+'\n')
    if args.render:
        dest=args.workspace/args.render
        if dest.exists():raise SystemExit('Refusing to overwrite render')
        dest.parent.mkdir(parents=True,exist_ok=True)
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            for f in range(FRAMES):
                proc.stdin.write(np.asarray(r.frame(f/FPS)).tobytes())
                if f%120==0:print(f'{f}/{FRAMES}',flush=True)
        finally:proc.stdin.close()
        if proc.wait():raise SystemExit('Encoder failed')
        print(json.dumps({'path':str(dest),'frames':FRAMES,'fps':FPS}),flush=True)


if __name__=='__main__':main()
