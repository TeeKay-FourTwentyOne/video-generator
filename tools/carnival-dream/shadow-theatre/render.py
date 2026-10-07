"""Native raster cut-paper theatre. Deterministic, entirely local; no model calls."""
import argparse, json, math, os, shutil, hashlib, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
TAU=math.tau
INK=(23,27,32); IVORY=(226,214,175); GOLD=(162,118,64); ROSE=(168,65,63); BLUE=(49,85,99)
W,H=1920,1080
ROOT=Path(__file__).resolve().parent
RUN=Path('data/workspace/carnival-dream/draft-v4-shadow')
SPEC=json.loads((ROOT/'film.json' if (ROOT/'film.json').exists() else Path('tools/carnival-dream/film.json')).read_text())

def clamp(x):return max(0,min(1,x))
def ease(x):x=clamp(x);return x*x*(3-2*x)
def mix(a,b,t):return a+(b-a)*t

def background(mode):
    rng=np.random.default_rng(421)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32);x=xx/W;y=yy/H
    center=np.exp(-(((x-.50)/.54)**2+((y-.44)/.67)**2)*1.5)
    if mode=='blue': low=np.array([18,33,41]);high=np.array([124,156,158])
    elif mode=='red':low=np.array([35,24,30]);high=np.array([176,99,74])
    elif mode=='mono':low=np.array([27,30,30]);high=np.array([213,212,194])
    elif mode=='night':low=np.array([12,20,29]);high=np.array([70,99,114])
    else:low=np.array([39,30,28]);high=np.array([229,189,120])
    noise=rng.normal(0,3.2,(H,W));fibers=np.sin(xx*.8+np.sin(yy*.045))*1.8+np.sin(yy*1.8)*1.2
    # Unevenly soaked paper, not a smooth computer gradient.
    blotches=np.zeros((H,W),np.float32)
    for _ in range(60):
        bx,by=rng.uniform(0,1,2);bw=rng.uniform(.015,.16)
        blotches+=rng.uniform(-3,3)*np.exp(-((x-bx)**2+(y-by)**2)/bw**2)
    noise+=blotches
    arr=low+(high-low)*center[:,:,None]+(noise+fibers)[:,:,None]
    return Image.fromarray(np.uint8(np.clip(arr,0,255)))
BGS={m:background(m) for m in ['amber','blue','red','mono','night']}
# Native-resolution substrate masks reused across frames; frame grain is separately stepped.
rng=np.random.default_rng(113)
GRAIN=[Image.fromarray(np.uint8(np.clip(rng.normal(128,1.6,(H,W)),0,255)),'L') for _ in range(4)]

class Stage:
    def __init__(self,mode='amber',zoom=1,cx=800,cy=450,roll=0):
        self.im=BGS[mode].copy();self.layer=Image.new('RGBA',(W,H));self.d=ImageDraw.Draw(self.layer)
        self.z=zoom;self.cx=cx;self.cy=cy;self.roll=roll
    def p(self,p):
        x=(p[0]-self.cx)*self.z;y=(p[1]-self.cy)*self.z
        c=math.cos(self.roll);s=math.sin(self.roll)
        return ((800+x*c-y*s)*1.2,(450+x*s+y*c)*1.2)
    def poly(self,pts,c,outline=None,width=1):
        pts=[self.p(p) for p in pts];self.d.polygon(pts,fill=c)
        if outline:self.d.line(pts+[pts[0]],fill=outline,width=max(1,round(width*self.z*1.2)))
    def line(self,pts,c=INK,w=2):self.d.line([self.p(p) for p in pts],fill=c,width=max(1,round(w*self.z*1.2)),joint='curve')
    def ell(self,x,y,rx,ry,c,outline=None,w=1):
        self.poly([(x+rx*math.cos(a),y+ry*math.sin(a)) for a in np.linspace(0,TAU,65)],c,outline,w)
    def star(self,x,y,r,c=IVORY,angle=0,n=5):
        self.poly([(x+(r if i%2==0 else r*.40)*math.cos(angle-math.pi/2+i*math.pi/n),y+(r if i%2==0 else r*.40)*math.sin(angle-math.pi/2+i*math.pi/n)) for i in range(n*2)],c)
    def gear(self,x,y,r,a=0,c=INK,n=18):
        self.poly([(x+r*(1 if i%4 in [1,2] else .88)*math.cos(a+i*TAU/(n*4)),y+r*(1 if i%4 in [1,2] else .88)*math.sin(a+i*TAU/(n*4))) for i in range(n*4)],c)
        self.ell(x,y,r*.68,r*.68,None,GOLD,2)
        for i in range(6):
            an=a+i*TAU/6;self.line([(x+math.cos(an)*r*.25,y+math.sin(an)*r*.25),(x+math.cos(an)*r*.65,y+math.sin(an)*r*.65)],GOLD,r*.085)
        self.ell(x,y,r*.20,r*.20,GOLD);self.ell(x,y,r*.075,r*.075,INK)
    def flush(self,shadow=True):
        if shadow:
            a=self.layer.getchannel('A');sh=Image.new('RGBA',(W,H),(0,0,0,0));sh.putalpha(a.point(lambda p:int(p*.26)))
            sh=ImageChops.offset(sh,6,8).filter(ImageFilter.GaussianBlur(3))
            self.im=Image.alpha_composite(self.im.convert('RGBA'),sh).convert('RGB')
        self.im=Image.alpha_composite(self.im.convert('RGBA'),self.layer).convert('RGB')
        self.layer=Image.new('RGBA',(W,H));self.d=ImageDraw.Draw(self.layer)
    def finish(self,f):
        self.flush()
        # Actual paper pigment variation, vignette baked into screen, stepped photographic grain.
        self.im=ImageChops.add(self.im,Image.merge('RGB',(GRAIN[f%4],)*3),scale=1,offset=-128)
        return self.im

def sky(s,t,stars=True):
    # Cut-paper scalloped clouds, engraved moon with a crescent face.
    s.ell(1170,206,100,100,(197,169,117),INK,3)
    s.ell(1201,184,83,83,INK)
    s.line([(1138,161),(1118,179),(1131,195),(1114,218),(1139,229)],INK,3)
    s.ell(1140,177,3,5,INK)
    if stars:
        for i in range(23):
            x=220+(i*197)%1170;y=100+(i*83)%380
            s.star(x,y,4+(i%4)*2,(180,154,111),.12*i)
    for side in [-1,1]:
        for k in range(3):
            x=800+side*(450+k*55);y=350+k*65
            s.line([(x-140,y+10),(x-95,y-16),(x-50,y+8),(x,y-10),(x+100,y+10)],(57,61,58),2)

def arch(s,t,open_=1):
    # Black velvet wings with scalloped edges, ornamental carved proscenium.
    for side in [0,1]:
        pts=[(0,0),(205,0),(205,110),(177,220),(161,340),(134,475),(112,610),(105,790),(0,900)]
        if side:pts=[(1600-x,y) for x,y in pts]
        s.poly(pts,INK)
        for i in range(6):
            x=25+i*22
            if side:x=1600-x
            s.line([(x,90),(x+(12 if side else -12),420),(x,790)],(52,42,38),3)
    s.poly([(0,0),(1600,0),(1600,78),(1450,99),(1270,69),(1100,89),(950,65),(800,91),(650,65),(480,89),(320,70),(150,99),(0,78)],INK)
    s.line([(160,90),(400,55),(800,68),(1200,55),(1440,90)],GOLD,3)
    for x in range(220,1400,55):s.ell(x,64+12*math.sin(x*.01),4,4,GOLD)
    s.poly([(0,798),(1600,798),(1600,900),(0,900)],INK)
    s.line([(115,799),(1485,799)],GOLD,3)
    for y in [820,848,890]:s.line([(100,y),(1500,y)],(60,48,39),2)
    for x in range(-300,1900,130):s.line([(800+(x-800)*.65,798),(x,900)],(60,48,39),2)
    # Curtain draws inward only when explicitly requested.
    if open_<1:
        w=650*(1-open_)
        s.poly([(105,90),(105+w,90),(105+w*.82,797),(105,797)],INK)
        s.poly([(1495,90),(1495-w,90),(1495-w*.82,797),(1495,797)],INK)

def horse(s,x,y,size=1,a=0,color=IVORY):
    # Hand-cut rocking horse profile, including mane, four legs, muzzle and tail.
    pts=[(-70,-8),(-58,-37),(-25,-42),(12,-33),(28,-73),(22,-96),(35,-87),(48,-92),(60,-63),(77,-55),(72,-40),(53,-40),(47,-14),(28,8),(45,47),(30,54),(5,18),(-24,17),(-45,52),(-60,49),(-47,7),(-67,2),(-87,24),(-95,10),(-88,-12)]
    def p(pt):u,v=pt;return x+size*(u*math.cos(a)-v*math.sin(a)),y+size*(u*math.sin(a)+v*math.cos(a))
    s.poly([p(p0) for p0 in pts],color,INK,2)
    s.poly([p(p0) for p0 in [(12,-32),(30,-42),(18,-10),(-15,-8),(-27,-27)]],ROSE)
    s.ell(*p((56,-61)),size*2.5,size*2.5,INK)
    for i in range(5):s.line([p((27+i*3,-77+i*9)),p((14+i*3,-73+i*9))],INK,2)

def carousel(s,t,x=800,y=568,r=360,broken=False,dismantle=0):
    # Turntable with z-sorted horses and true elliptical orbit, independently bobbing poles.
    s.ell(x,y+150,r,54,INK,GOLD,4);s.ell(x,y+140,r*.97,45,(103,70,49),GOLD,2)
    s.line([(x,y-295),(x,y+140)],GOLD,13)
    phase=t*.55 if not broken else -TAU/3+math.pi/2+(t-96.48)*.18
    items=sorted([(math.sin(phase+i*TAU/6),i) for i in range(6)])
    for z,i in items:
        a=phase+i*TAU/6;px=x+math.cos(a)*r*.76;py=y+z*46
        if dismantle:py+=dismantle*(180+30*i);px+=(px-x)*dismantle*.5
        scale=.65+.19*(z+1)
        s.line([(px,py-250),(px,py+122)],GOLD,4)
        if not(broken and i==2):horse(s,px,py+14*math.sin(t*2.3+i),scale,0,IVORY if z>0 else (117,122,115))
        else:s.line([(px-20,py+30),(px+20,py+30)],ROSE,6)
    cy=y-255-dismantle*250
    for i in range(12):
        a=i*math.pi/12;b=(i+1)*math.pi/12
        s.poly([(x,cy-100),(x+r*math.cos(a),cy+25*math.sin(a)),(x+r*math.cos(b),cy+25*math.sin(b))],ROSE if i%2 else IVORY,INK,1)
    s.line([(x-r,cy),(x+r,cy)],GOLD,8)
    for i in range(13):s.ell(x-r+i*r/6,cy+7,6,6,IVORY)
    s.star(x,cy-117,23,GOLD,t*.25)

def wheel(s,t,x=800,y=445,r=285,broken=False,amount=1):
    s.poly([(x-190,y+350),(x-45,y),(x+45,y),(x+190,y+350),(x+155,y+350),(x,y+65),(x-155,y+350)],INK,GOLD,2)
    s.ell(x,y,r,r,None,INK,14);s.ell(x,y,r-20,r-20,None,GOLD,3)
    for i in range(12):
        a=(t*.31 if not broken else -math.pi/2+(t-95.68)*.2)+i*TAU/12;px=x+r*math.cos(a);py=y+r*math.sin(a)
        if i/12>amount:continue
        s.line([(x,y),(px,py)],INK,6)
        if not(broken and i==3):
            s.line([(px-19,py+40),(px,py),(px+19,py+40)],INK,3)
            s.poly([(px-28,py+35),(px+28,py+35),(px+23,py+62),(px-23,py+62)],IVORY,INK,3)
            s.line([(px-28,py+43),(px+28,py+43)],ROSE,4)
        else:s.line([(px,py),(px+15,py+21)],ROSE,5)
    s.gear(x,y,43,-t*.31,GOLD,12)

def swings(s,t,x=800,y=360,broken=False,amount=1):
    s.line([(x,y-70),(x,y+398)],INK,28);s.ell(x,y+404,160,29,INK,GOLD,3)
    phase=t*.65 if not broken else -math.pi+(t-97.28)*.2+math.pi/2
    for z,i in sorted([(math.sin(phase+i*TAU/8),i) for i in range(8)]):
        if i/8>amount:continue
        a=phase+i*TAU/8;ax=x+240*math.cos(a);ay=y+35*z;px=x+340*math.cos(a);py=y+225+z*70
        if broken and i==4:py+=45
        s.line([(ax,ay),(px-20,py)],INK,3)
        if not (broken and i==4):s.line([(ax+25,ay),(px+20,py)],INK,3)
        s.poly([(px-30,py),(px+30,py+ (20 if broken and i==4 else 0)),(px+22,py+25),(px-22,py+25)],IVORY,INK,2)
    s.poly([(x-278,y),(x,y-133),(x+278,y)],INK,GOLD,3)
    for i in range(10):s.star(x-220+i*49,y-9,7,IVORY)
    s.star(x,y-150,24,GOLD,t)

def puppet(s,x,y,scale=1,t=0,pose='idle',shadow=False,flip=False,color=IVORY,strings=True,reach=0):
    # Local origin is the neck. Distinct paper profile, articulated limbs, pleated skirt.
    if scale>=.9:y+=30
    bob=2*math.sin(t*2.3);lean=0.03*math.sin(t*1.7)
    if pose=='bow':lean=.20
    if pose=='reach':reach=1
    if pose=='dance':lean=.10*math.sin(t*2.3);reach=.45+.3*math.sin(t*1.15)
    sign=-1 if flip else 1
    def p(q):
        u,v=q;u*=sign
        return (x+scale*(u*math.cos(lean)-v*math.sin(lean)),y+scale*(u*math.sin(lean)+v*math.cos(lean)+bob))
    col=INK if shadow else color; edge=(68,65,56) if shadow else INK
    def poly(pts,c=col):s.poly([p(z) for z in pts],c,edge,1.5)
    def ell(q,rx,ry,c):s.ell(*p(q),rx*scale,ry*scale,c)
    def limb(a,b,w):
        dx=b[0]-a[0];dy=b[1]-a[1];l=math.hypot(dx,dy);nx=-dy/l*w/2;ny=dx/l*w/2
        poly([(a[0]+nx,a[1]+ny),(b[0]+nx*.72,b[1]+ny*.72),(b[0]-nx*.72,b[1]-ny*.72),(a[0]-nx,a[1]-ny)])
        ell(a,w*.45,w*.45,col);ell(b,w*.32,w*.32,col)
    # Legs with a bent knee, limited mechanical stepping.
    walk=math.sin(t*4.6) if pose in ['walk','dance'] else .18*math.sin(t*2.3)
    for side in [-1,1]:
        hip=(side*23,145);knee=(side*25+walk*side*20,207);foot=(side*30-walk*side*13,261-max(0,walk*side)*10)
        limb(hip,knee,17);limb(knee,foot,12)
        poly([(foot[0]-7,foot[1]-7),(foot[0]+9,foot[1]-7),(foot[0]+24,foot[1]+5),(foot[0]-12,foot[1]+5)],edge)
        ell(knee,4,4,GOLD)
    poly([(-25,10),(25,10),(33,65),(22,84),(-23,84),(-34,65)])
    # Bell-shaped skirt with asymmetrical pleats and printed hatching.
    pts=[(-23,73),(22,73),(40,102),(64,143),(82,168),(50,180),(14,174),(-18,181),(-50,174),(-78,163),(-43,112)]
    poly(pts)
    for i in range(9):
        bx=-68+i*17;s.line([p((-20+i*5,81)),p((bx,165+5*math.sin(i)))],edge,1.5)
    if not shadow:
        for i in range(7):s.star(*p((-54+i*18,148+(i%2)*6)),scale*4,ROSE,.2*i)
        s.line([p((-64,164)),p((-25,173)),p((15,169)),p((65,166))],ROSE,4)
    # Arms can reach toward the partner or above to pluck the hanging star.
    elbows=[(-61,73-30*reach),(63+reach*15,65-reach*37)]
    hands=[(-49,120-50*reach),(64+reach*74,115-reach*103)]
    if pose=='pluck':elbows[1]=(63,-31);hands[1]=(86,-98)
    if pose=='wind':elbows[1]=(65,53);hands[1]=(100+12*math.cos(t*3),64+12*math.sin(t*3))
    for a,b,c in zip([(-30,21),(30,21)],elbows,hands):
        limb(a,b,17);limb(b,c,12);ell(b,4,4,GOLD)
        poly([(c[0]-7,c[1]-5),(c[0]+7,c[1]-5),(c[0]+15,c[1]+5),(c[0]+4,c[1]+14),(c[0]-6,c[1]+9)])
    # Long ivory face with visible nose, almond eye, cap and paper ruff.
    poly([(-13,10),(-13,-20),(-31,-41),(-35,-70),(-25,-91),(5,-96),(27,-83),(32,-66),(46,-54),(33,-49),(29,-26),(11,-14),(11,10)])
    poly([(-33,-59),(-47,-71),(-44,-95),(-22,-112),(10,-110),(31,-92),(29,-79),(0,-85),(-20,-72)],edge)
    if not shadow:
        s.line([p((13,-66)),p((23,-65))],INK,2)
        ell((21,-52),5,3,ROSE);s.line([p((24,-34)),p((32,-34))],ROSE,2)
    for i in range(9):
        xx=-41+i*10;poly([(xx,6),(xx+4,22),(xx+12,10),(xx+5,-1)],col)
    for yy in [40,59]:ell((0,yy),3,3,edge)
    if strings:
        for q in [(-28,20),(28,20),*hands]:
            v=p(q);s.line([(v[0]+15*math.sin(t*.8),-120),v],(110,102,82,145),.8)
    return p(hands[1])

def clock(s,t,op=0,x=800,y=418,scale=1):
    def pt(p):return (x+p[0]*scale,y+p[1]*scale)
    def poly(p,c,edge=GOLD):s.poly([pt(v) for v in p],c,edge,3)
    poly([(-245,-125),(0,-350),(245,-125),(207,-102),(200,245),(-200,245),(-207,-102)],INK)
    for i in [-1,1]:
        for j in range(5):s.line([pt((i*(240-j*25),-120-j*25)),pt((i*(190-j*24),-100-j*25))],GOLD,2)
    s.ell(x,y+50*scale,128*scale,128*scale,IVORY,GOLD,4)
    for i in range(12):
        a=i*TAU/12;s.line([pt((100*math.sin(a),50-100*math.cos(a))),pt((115*math.sin(a),50-115*math.cos(a)))],INK,4)
    s.line([pt((0,50)),pt((75*math.sin(t*.35),50-75*math.cos(t*.35)))],INK,7)
    s.line([pt((0,50)),pt((46*math.sin(t*.1),50-46*math.cos(t*.1)))],INK,10)
    s.ell(x,y+50*scale,9*scale,9*scale,GOLD)
    for side in [-1,1]:
        ax=side*65;poly([(ax-42,-208),(ax+42,-208),(ax+42,-118),(ax-42,-118)],(15,21,28))
        dx=op*80*side
        poly([(ax-42+dx,-208-op*12),(ax+42+dx,-208+op*12),(ax+42+dx,-118),(ax-42+dx,-118)],(83,54,39))
    if op>.15:
        # Cuckoo bird emerges on a horizontal wooden slide.
        bx=x+op*130*scale;by=y-163*scale
        s.line([(x,by+20*scale),(bx+40*scale,by+20*scale)],GOLD,6)
        s.poly([(bx-36*scale,by),(bx-58*scale,by-28*scale),(bx-18*scale,by-13*scale),(bx,by-30*scale),(bx+18*scale,by-18*scale),(bx+43*scale,by-10*scale),(bx+17*scale,by-4*scale),(bx+10*scale,by+16*scale),(bx-23*scale,by+14*scale)],IVORY)
        s.ell(bx+9*scale,by-16*scale,3*scale,3*scale,INK)
    a=.25*math.sin(t*2.3);ex=x+math.sin(a)*180*scale;ey=y+245*scale+math.cos(a)*180*scale
    s.line([pt((0,245)),(ex,ey)],GOLD,8);s.ell(ex,ey,35*scale,35*scale,GOLD,INK,4)
    for side in [-1,1]:
        s.line([pt((side*112,245)),pt((side*112,360+side*15*math.sin(t)))],GOLD,2)
        s.ell(*pt((side*112,376+side*15*math.sin(t))),17*scale,34*scale,INK,GOLD,2)

def lantern(s,t,x=1060,y=440,size=1):
    s.gear(x,y+220*size,100*size,t*.45,INK)
    s.line([(x,y-200*size),(x,y+228*size)],GOLD,10)
    s.ell(x,y,160*size,190*size,INK,GOLD,4)
    for i in range(8):
        a=t*.45+i*TAU/8;xx=x+math.cos(a)*130*size
        col=[ROSE,BLUE,GOLD,IVORY][i%4]
        s.poly([(xx-14*size,y-155*size),(xx+14*size,y-155*size),(xx+14*size,y+155*size),(xx-14*size,y+155*size)],col)
    s.ell(x,y,40*size,92*size,IVORY);s.star(x,y,24*size,GOLD,t)
    for yy in [-175,175]:s.ell(x,y+yy*size,157*size,23*size,INK,GOLD,4)
    s.poly([(x-205*size,y-193*size),(x,y-267*size),(x+205*size,y-193*size)],INK,GOLD,4)


def render(f):
    shot=next(s for s in SPEC['shots'] if s['start_frame']<=f<s['end_frame']);idx=int(shot['id'][2:]);kind=shot['kind']
    u=(f-shot['start_frame'])/max(1,shot['end_frame']-shot['start_frame']-1);t=f/24
    # Mechanical pose cadence remains 8fps, including cameras and wheel gearing.
    mode='amber';zoom=1;cx=800;cy=450;roll=0
    if idx in [7,8,12,16,17,18,19,27,28,29,38]:mode='blue'
    if idx in [11,13,15,22,23,24,34,36,37]:mode='mono'
    if idx in [20,21,25,26,35,39,40,41]:mode='red'
    if idx in [1,30,31,32]:mode='night'
    if idx==3:zoom=1.65;cx=630;cy=405
    if idx==6:zoom=2.25;cx=795;cy=715
    if idx==7:zoom=2.5;cx=614;cy=480
    if idx in [10,26,40]:zoom=1.35;cx=790;cy=455
    if idx==18:zoom=1.35;cx=635;cy=450
    if idx==19:zoom=1.18;cx=760;cy=450
    if idx==22:zoom=1.85;cx=1060;cy=495
    if idx==23:zoom=1.5;cx=800;cy=603
    if idx==24:zoom=1.55;cx=800;cy=625
    if idx==21:roll=.10*math.sin(u*TAU);zoom=1.08
    if idx==31:zoom=1.3;cx=980;cy=460
    if idx==32:zoom=1.3;cx=930;cy=490
    # Small hand-operated rostrum moves, not continuous digital drift.
    zoom*=1+.025*ease(u)
    s=Stage(mode,zoom,cx,cy,roll)
    sky(s,t,stars=idx not in [1,30,31,32,38])
    s.flush(False)
    # Giant setpiece episodes.
    if idx==1:
        s.gear(790,455,290,t*.21,INK,24);s.gear(1175,642,156,-t*.39,INK,17);s.gear(343,262,181,-t*.34,INK,20)
        s.ell(790,455,153,153,IVORY,GOLD,4);s.star(790,455,106,GOLD,t*.21,12)
        s.ell(790,455,65,65,INK);s.ell(790,455,27,27,GOLD)
        s.line([(200,760),(1410,160)],(155,118,65),3)
    elif idx in [11,22,34]:wheel(s,t,broken=idx==22,amount=1-ease(u) if idx==34 else ease(u)*.8+.2 if idx==11 else 1)
    elif idx in [13,23,36]:carousel(s,t,broken=idx==23,dismantle=ease(u) if idx==36 else 0)
    elif idx in [15,24,37]:swings(s,t,broken=idx==24,amount=1-ease(u) if idx==37 else .3+.7*ease(u) if idx==15 else 1)
    elif idx in [29,30]:
        clock(s,t,op=ease((u-.15)*2) if idx==29 else 1,x=950,y=390,scale=.8)
        puppet(s,475+u*75,450,1.1,t,'walk' if idx==29 else 'reach')
        if idx==30:lantern(s,t,x=1250,y=490,size=.43)
    elif idx in [31,32]:
        s.poly([(300,680),(1060,285),(1060,600)],(213,168,98,75));s.flush(False)
        for gx,gy,gr,sg in [(360,340,160,1),(630,600,125,-1),(1400,310,210,-1)]:s.gear(gx,gy,gr,t*.3*sg)
        lantern(s,t,x=1030,y=430,size=1)
        # Accessible winding crank connects the performer's hand to the lantern axle.
        s.line([(813,587),(1030,650)],GOLD,10)
        s.gear(813,587,36,-t*.7,GOLD,12)
        s.line([(813,587),(813+12*math.cos(t*3),587+12*math.sin(t*3))],INK,7)
        if idx==32:puppet(s,713,493,1,t,'wind',strings=True)
        else:
            for i in range(4):
                a=t*.4+i*TAU/4;puppet(s,1030+math.cos(a)*265,438+math.sin(a)*45,.32,t,'dance',True,strings=False)
    else:
        # Rotating colored gel beam visibly lends its colors to the paper world.
        beamx=820+180*math.sin(t*.33)
        if idx not in [2,17,28,38]:
            s.poly([(1430,190),(beamx-430,785),(beamx+290,785)],(221,162,97,50) if mode!='red' else (216,122,79,65));s.flush(False)
        if idx in [9,10,20,21,25,26,35]:
            # A hinged fan of paper rays unfolds behind the first dance.
            fan=ease(u*2) if idx==9 else 1
            for i in range(19):
                a=math.pi+i*math.pi/18
                r=330*fan
                s.poly([(805,490),(805+r*math.cos(a-.027),490+r*math.sin(a-.027)),(805+r*math.cos(a+.027),490+r*math.sin(a+.027))],(163,124,79,135))
            wheel(s,t,x=355,y=335,r=185,amount=ease(u) if idx==9 else 1)
            carousel(s,t,x=1250,y=423,r=230)
            s.flush()
        if idx in [16,17]:
            # Repeating toy landscape slides past while the performer goes nowhere.
            for j in range(4):
                xx=((j*450-t*60)%1800)-100
                s.poly([(xx-100,725),(xx-100,340),(xx,230),(xx+100,340),(xx+100,725)],INK,GOLD,2)
                s.ell(xx,355,40,40,(102,122,119));s.line([(xx,355),(xx+22,333)],INK,3)
        if idx in [33,35,39,40,41]:
            s.gear(1280,676,120,t*.28,INK);lantern(s,t,1350,338,.36)
        # Narrative blocking.
        px=615;py=488;pose='idle';shx=1000;show=idx in [4,5,6,7,8,9,10,12,14,20,21,25,26,27,28,33,35,39,40,41]
        if idx==2:px=740;pose='bow'
        if idx==3:px=620
        if idx==4:shx=1320-ease(u)*320
        if idx==5:pose='reach';shx=970-ease(u)*70
        if idx==6:px=655+u*110;pose='walk';shx=1000
        if idx==7:px=615;pose='reach'
        if idx==8:pose='reach';shx=950+ease(u)*380
        if idx in [9,10,20,25,26,35,40,41]:pose='dance';px=610+22*math.sin(t*1.15);shx=950+30*math.sin(t*1.15+1)
        if idx==12:pose='reach';shx=950+u*550
        if idx==14:pose='walk';px=580+u*230;shx=1100+u*300
        if idx==16:pose='walk';px=750
        if idx==17:px=755;pose='bow'
        if idx==18:px=600;pose='pluck'
        if idx==19:px=540+u*220;pose='walk'
        if idx==21:px=800+210*math.cos(u*TAU);shx=800-210*math.cos(u*TAU);pose='dance'
        if idx==27:pose='reach';shx=1000+u*260
        if idx==28:pose='reach';shx=1120+u*460
        if idx==33:pose='idle';px=590;shx=1160-ease(u)*200
        if idx==38:px=760;pose='bow'
        if idx==39:px=605+ease(u)*90;pose='walk';shx=1010
        if idx in [40,41]:
            pose='reach';px=650;shx=980-30*ease(u) if idx==40 else 950
        if show:
            puppet(s,shx,488 if idx in [40,41] else 447,1.05 if idx in [40,41] else 1.2,t+.5,'reach' if pose=='reach' else 'dance',True,True,strings=False)
            s.flush(False)
        # White performer catches colored pigment, then loses it.
        col=IVORY
        if idx in [9,10,20,21,25,26,35,40,41]:col=(222,154,117)
        if idx==12:col=tuple(round(mix(a,b,ease(u))) for a,b in zip((222,154,117),IVORY))
        hand=puppet(s,px,py,1.05,t,pose,False,False,col)
        if idx in [18,19,20,21,26,27]:
            n=7 if idx in [20,21,26,27] else 1
            for i in range(n):
                sx=690+i*95 if n>1 else hand[0];sy=250+70*math.sin(i*1.7+t*.6) if n>1 else (mix(235,hand[1]-8,ease(u*2)) if idx==18 else hand[1]-8)
                if idx==27:sy+=ease(u)*(650+i*35)
                s.line([(sx,-40),(sx,sy)],(158,132,89),1);s.star(sx,sy,30 if n==1 else 19,GOLD if idx!=27 else IVORY,t*.2+i)
        if idx==17:s.ell(1120,730,90,18,None,GOLD,2)
    s.flush()
    arch(s,t,open_=ease(u*1.5) if idx==2 else 1)
    im=s.finish(f//3)
    if f<12:im=Image.blend(Image.new('RGB',im.size,(9,14,20)),im,f/12)
    # End on the joined gesture; only the final decay fades the theatre.
    if f>4053:im=Image.blend(im,Image.new('RGB',im.size,(9,14,20)),ease((f-4053)/30))
    return im

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--start',type=int,default=0);ap.add_argument('--end',type=int,default=4084);args=ap.parse_args()
    if args.stills:
        for shot in SPEC['shots']:
            f=(shot['start_frame']+shot['end_frame'])//2
            render(f).save(RUN/'stills'/f"{shot['id']}-{shot['kind']}.jpg",quality=94)
        thumbs=Image.new('RGB',(1600,math.ceil(len(SPEC['shots'])/4)*250),(15,19,24));d=ImageDraw.Draw(thumbs)
        for i,shot in enumerate(SPEC['shots']):
            im=Image.open(RUN/'stills'/f"{shot['id']}-{shot['kind']}.jpg");im.thumbnail((400,225));x=i%4*400;y=i//4*250;thumbs.paste(im,(x,y));d.text((x+8,y+228),f"{shot['id']} {shot['start']:.1f}s / {shot['kind']}",fill='white')
        thumbs.save(RUN/'review'/'contact-sheet.jpg',quality=91)
    if args.render:
        cuts={s['start_frame'] for s in SPEC['shots']};last=None
        for f in range(args.start,args.end):
            dst=RUN/'frames'/f'frame-{f:05d}.png'
            if f%3==0 or f in cuts or last is None:
                if not dst.exists():render(f).save(dst,compress_level=1)
                last=dst
            elif not dst.exists():os.link(last,dst)
            if f%120==0:print(f'{f}/4084',flush=True)
if __name__=='__main__':main()
