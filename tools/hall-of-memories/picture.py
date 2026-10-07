"""Local geometric paper-theatre blocking. No image/video provider calls."""
from functools import lru_cache
from pathlib import Path
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
S = W / 1280
INK = '#20272b'
FONT = os.environ.get('HALL_FONT', '/System/Library/Fonts/Supplemental/Arial.ttf')
BOLD = os.environ.get('HALL_FONT_BOLD', '/System/Library/Fonts/Supplemental/Arial Bold.ttf')

def ease(x):
    x = max(0, min(1, x)); return x*x*(3-2*x)

def held(t, hz=6): return math.floor(t*hz + 1e-7)/hz

@lru_cache(maxsize=64)
def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, round(size*S))

class Draw:
    def __init__(self, im): self.im=im; self.d=ImageDraw.Draw(im)
    def pts(self,p): return [(round(x*S),round(y*S)) for x,y in p]
    def poly(self,p,c,outline=None,width=1): self.d.polygon(self.pts(p),fill=c,outline=outline,width=max(1,round(width*S)))
    def line(self,p,c,width=1): self.d.line(self.pts(p),fill=c,width=max(1,round(width*S)),joint='curve')
    def rect(self,b,c,outline=None,width=1): self.d.rectangle(tuple(round(x*S) for x in b),fill=c,outline=outline,width=max(1,round(width*S)))
    def ellipse(self,b,c,outline=None,width=1): self.d.ellipse(tuple(round(x*S) for x in b),fill=c,outline=outline,width=max(1,round(width*S)))
    def text(self,p,text,size=18,c='#dfddd0',bold=False,anchor=None):
        self.d.text((round(p[0]*S),round(p[1]*S)),text,font=font(size,bold),fill=c,anchor=anchor)

@lru_cache(maxsize=16)
def paper(color):
    base=np.array(Image.new('RGB',(1,1),color))[0,0].astype(float)
    rng=np.random.default_rng(230923)
    noise=rng.normal(0,1.1,(H,W,1))
    return Image.fromarray(np.clip(base[None,None,:]+noise,0,255).astype('uint8'))

def puppet(d,x,y,h,kind='robot',pose='rest',tone=None,gaze='level'):
    """Feet at (x,y). Identical joints in match pose on both sides of the cut."""
    human=kind in ('human','daughter','warrior','elder-human','record-human')
    col=tone or ('#a99e8b' if human else '#b8beb5')
    dark='#61574d' if human else '#747f7b'
    def p(a,b): return (x+a*h,y+b*h)
    def ln(a,b,c,w): d.line([p(*a),p(*b)],c,w*h)
    def pl(pts,c): d.poly([p(*v) for v in pts],c)
    d.ellipse((x-h*.19,y-h*.017,x+h*.23,y+h*.04),'#252c2d')
    legs=[(-.073,-.31,-.1,-.025),(.065,-.31,.11,-.025)]
    for a,b,c,e in legs: ln((a,b),(c,e),dark,.065)
    for a in [-.1,.11]: ln((a-.04,-.015),(a+.055,-.015),dark,.05)
    pl([(-.12,-.73),(.105,-.73),(.14,-.32),(-.13,-.30)],col)
    pl([(-.10,-.70),(-.02,-.70),(-.015,-.32),(-.13,-.30)],dark)
    if human:
        apron='#855944' if kind=='human' else '#b58b59' if kind=='daughter' else '#6e8590' if kind=='record-human' else '#60594c'
        pl([(-.08,-.69),(.075,-.69),(.13,-.30),(-.12,-.30)],apron)
        ln((-.06,-.48),(.075,-.48),'#d0af7b',.018)
    # Hand and elbow marks stay geometrically identical in the matched gesture.
    arms={
        'rest': [(-.105,-.69,-.15,-.48,-.12,-.39),(.10,-.69,.15,-.49,.15,-.37)],
        'lever':[(-.105,-.69,-.16,-.5,-.1,-.44),(.10,-.69,.28,-.55,.37,-.49)],
        'point':[(-.105,-.69,-.16,-.50,-.13,-.39),(.10,-.69,.23,-.62,.37,-.75)],
        'match':[(-.105,-.69,-.26,-.70,-.32,-.88),(.10,-.69,.26,-.63,.39,-.70)],
        'withdraw':[(-.105,-.69,-.13,-.5,.01,-.51),(.10,-.69,.13,-.52,.01,-.51)],
        'jewel':[(-.105,-.69,-.19,-.56,-.025,-.61),(.10,-.69,.20,-.55,.055,-.63)],
        'proud':[(-.105,-.69,-.22,-.54,-.30,-.60),(.10,-.69,.22,-.54,.30,-.60)]
    }
    for a,b,c,e,f,g in arms.get(pose,arms['rest']):
        ln((a,b),(c,e),dark,.055);ln((c,e),(f,g),col,.052)
        d.ellipse((x+(f-.035)*h,y+(g-.04)*h,x+(f+.035)*h,y+(g+.025)*h),col)
        if pose=='match': ln((f,g),(f-.035,g-.07),col,.022)
    # Asymmetric cutout head; no mouth is ever drawn on an avatar.
    pl([(-.105,-.98),(.08,-1.015),(.14,-.91),(.10,-.78),(-.045,-.75),(-.13,-.84)],col)
    pl([(-.105,-.98),(-.06,-.93),(-.058,-.79),(-.045,-.75),(-.13,-.84)],dark)
    if human:
        pl([(-.115,-.97),(.08,-1.035),(.115,-.96),(-.06,-.95),(-.1,-.86)],'#4e473e')
        if kind=='daughter':pl([(-.12,-.97),(-.085,-.92),(-.11,-.72),(-.19,-.70),(-.16,-.91)],'#4e473e')
        ln((-.018,-.896),(.015,-.892),INK,.013);ln((.055,-.89),(.083,-.884),INK,.013)
        ln((.04,-.88),(.055,-.84),dark,.012)
    else:
        ey=-.946 if gaze=='up' else -.8975
        if gaze=='up':pl([(-.10,-.80),(.08,-.79),(.105,-.84),(-.07,-.86)],'#ccd0bc')
        for ex in [-.018,.062]:
            d.ellipse((x+(ex-.018)*h,y+(ey-.0175)*h,x+(ex+.015)*h,y+(ey+.0175)*h),'#dfc86d')
    if kind=='elder-human': ln((-.06,-.81),(.04,-.74),'#d4c4a8',.03)

def jewel(d,x,y,h):
    p=[(-.32,-.5),(.21,-.53),(.40,-.19),(.30,.42),(-.20,.52),(-.40,.14)]
    pts=[(x+a*h,y+b*h) for a,b in p]
    d.poly([(a+.08*h,b+.03*h) for a,b in pts],'#123e35')
    d.poly(pts,'#257157', '#abc18d',1)
    inn=[(x+a*h*.72,y+b*h*.72) for a,b in p]
    for i in range(6): d.poly([pts[i],pts[(i+1)%6],inn[(i+1)%6],inn[i]],['#265640','#4b9870','#174b3c','#0e392e','#39765a','#6b9d73'][i])
    d.line([(x-.22*h,y-.18*h),(x+.16*h,y+.16*h)],'#bdd0a0',max(1,h*.014))

def sky():
    im=paper('#555d69').copy();d=Draw(im)
    d.poly([(0,310),(460,299),(720,330),(1280,316),(1280,720),(0,720)],'#697373')
    # Two displaced semicircles make the sky feel constructed, rather than lunar.
    d.poly([(966+101*math.cos(a),164+101*math.sin(a)) for a in np.linspace(math.pi,2*math.pi,64)],'#a5a493')
    d.poly([(1035+101*math.cos(a),174+101*math.sin(a)) for a in np.linspace(0,math.pi,64)],'#a5a493')
    d.line([(0,297),(440,294),(820,316),(1280,306)],'#b0a892',2)
    d.poly([(0,489),(415,363),(716,381),(1280,465),(1280,720),(0,720)],'#868981')
    for i in range(8):d.line([(i*240-400,720),(580+i*22,364)],'#767f79',2)
    return im

def factory(t=0,events=None):
    events=events or {'duplicate':999,'door_vanish':999,'timer':999,'eyes':999,'circle_cut':999,'safety':999}
    t=held(t);im=paper('#504e44').copy();d=Draw(im)
    d.poly([(0,0),(1280,0),(1280,492),(0,460)],'#514f43')
    d.poly([(0,460),(1280,492),(1280,720),(0,720)],'#393b35')
    for x in [90,490,920,1240]:d.rect((x,0,x+11,474),'#6e6a55')
    d.line([(0,111),(1280,118)],'#272d29',18)
    d.rect((275,28,478,43),'#d3bd7b');d.rect((800,31,1004,46),'#d3bd7b')
    # No chamber interior or violence is visible. The right edge is an opaque screen.
    d.poly([(968,171),(1182,149),(1280,204),(1280,567),(971,547)],'#30372f')
    for x in range(996,1260,35):d.line([(x,187),(x,548)],'#465044',2)
    d.poly([(0,554),(967,556),(994,607),(0,614)],'#6c6a51')
    for x in range(-40,980,64):
        a=x+(t*10%64 if t<5.5 else 0);d.line([(a,559),(a+27,603)],'#353c34',7)
    # Queue is barely readable behind the conveyor; never literal execution coverage.
    for x in [58,137,223]:puppet(d,x,550,122,'human','rest','#777765')
    for x in [873,945]:puppet(d,x,485,180,'robot','proud' if t<events['safety'] else 'point','#9a9e86')
    if t<events['door_vanish']+.75:
        d.rect((340,185,450,460),'#242e29');d.line([(336,461),(336,181),(451,181),(451,461)],'#85816a',8)
    if events['duplicate']<=t<events['door_vanish']+.75:
        q=ease((t-events['duplicate'])/.75)
        retreat=ease((t-events['door_vanish'])/.65)
        puppet(d,399+108*q*(1-retreat),505,239,'human','rest')
    if events['door_vanish']+.75<=t<events['door_vanish']+1.1:
        d.rect((333,178,456,466),'#625f4c')
    d.rect((1050,68,1253,130),'#bcb48e')
    d.text((1151,86),'SAFETY FIRST',16,INK,True,'mm');d.text((1151,112),'NO ROBOT SHALL KILL',11,INK,False,'mm')
    d.ellipse((551,58,623,130),'#b7b193',INK,3);d.line([(587,94),(587,71)],INK,3);d.line([(587,94),(611,100)],INK,3)
    d.rect((559,482,720,501),'#222b27');d.line([(581,500),(570,667)],'#232d27',11);d.line([(700,500),(719,667)],'#232d27',11)
    d.poly([(615,482),(620,464),(672,468),(670,488)],'#c4b588')
    pose='lever' if int(t*1.2)%3==0 and t<5.5 else 'rest'
    if t>=events['timer']:pose='point'
    if t>=events['circle_cut']-1.0:pose='match'
    puppet(d,710,661,335,'human',pose)
    d.rect((835,446,869,615),'#8d7050');d.line([(852,475),(832 if pose=='lever' else 875,399)],'#262f29',11)
    d.ellipse((865,383,884,404),'#b1a880')
    if t>=events['timer']:
        d.rect((956,357,1123,444),'#b8ab7c',INK,4)
        d.rect((975,371,1103,409),'#3b4638')
        if t>=events['eyes']:
            for x in [1006,1068]:d.ellipse((x-7,382,x+7,395),'#e0cb6e')
            d.rect((955,446,1156,495),'#c1b68d')
            d.text((1056,461),'HUMAN AUTHORIZATION',11,INK,True,'mm');d.text((1056,480),'REQUIRED',13,INK,True,'mm')
        else:d.text((1039,390),'00:00',23,'#d9c987',True,'mm')
    return im

def circle(match=False):
    im=sky();d=Draw(im)
    d.ellipse((334,413,1022,706),'#656e6a')
    for x,y,h,p in [(392,570,211,'rest'),(485,666,205,'point'),(965,587,200,'rest'),(1050,681,228,'withdraw')]:puppet(d,x,y,h,'robot',p)
    puppet(d,710,661,335,'robot','match' if match else 'point')
    puppet(d,199,493,233,'robot','rest','#969e98')
    return im

def project(points,eye,target,focal=800):
    eye=np.asarray(eye,float);target=np.asarray(target,float)
    f=target-eye;f/=np.linalg.norm(f)
    r=np.cross(f,[0,1,0]);r/=np.linalg.norm(r)
    u=np.cross(r,f)
    # x direction is corrected so world +x appears screen right.
    r=-r
    xyz=np.asarray(points,float)-eye
    dep=xyz@f
    xy=np.c_[640+focal*(xyz@r)/np.maximum(dep,.02),360-focal*(xyz@u)/np.maximum(dep,.02)]
    return xy,dep

def box(faces,lo,hi,col):
    x,y,z=lo;X,Y,Z=hi
    pts=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    rgb=np.asarray(Image.new('RGB',(1,1),col))[0,0]
    for ids,shade in [([0,1,2,3],1),([1,5,6,2],.66),([4,0,3,7],.8),([3,2,6,7],1.16),([5,4,7,6],.84),([4,5,1,0],.55)]:
        faces.append(([pts[i] for i in ids],tuple(np.clip(rgb*shade,0,255).astype(int))))

def polygons(im,faces,eye,target,focal=800):
    d=Draw(im);items=[]
    for p,c in faces:
        xy,z=project(p,eye,target,focal)
        if np.min(z)>.06:items.append((float(np.mean(z)),xy.tolist(),c))
    for _,p,c in sorted(items,key=lambda x:-x[0]):d.poly(p,c)

def hall(eye=(9,8,-21),target=(0,3,5),inside=False):
    im=sky();faces=[]
    box(faces,(-9,-.5,-5),(9,0,17),'#87887a')
    box(faces,(-7,0,-3),(7,.25,2),'#a2a28f')
    box(faces,(-6.5,.25,-2),(6.5,.5,2),'#b0b09c')
    box(faces,(-6.1,.5,-1),(6.1,.75,13),'#bfc0ab')
    box(faces,(-6.1,.75,12),(6.1,7.3,13),'#5f6965')
    box(faces,(-6.1,.75,0),(-5.4,7.3,13),'#90998e')
    box(faces,(5.4,.75,0),(6.1,7.3,13),'#77877f')
    box(faces,(-6.1,7.0,0),(6.1,7.5,13),'#a4ac9a')
    for x in [-5.5,-3.2,-1.25,1.25,3.2,5.5]:box(faces,(x-.32,.75,-.1),(x+.32,7.05,.75),'#b5b9a6')
    # Side bays closed, central opening remains a distinct narrow void.
    for a,b in [(-5.4,-1.55),(1.55,5.4)]:box(faces,(a,1,0),(b,6.7,.4),'#71847b')
    box(faces,(-1.15,1.2,10),(1.15,5.8,10.2),'#c7b892')
    for x in [-3.3,3.3]:
        for y in [2,3.5,5]:box(faces,(x-.52,y,11.6),(x+.52,y+.6,11.8),'#9caa97')
    polygons(im,faces,eye,target)
    # One human record is a sparse piece of paper, not a score or a living captive.
    p,z=project([(-.05,3.6,9.95)],eye,target)
    if z[0]>.1 and inside:
        d=Draw(im);x,y=p[0];h=800*1.4/z[0];puppet(d,x,y+h*.4,h,'record-human','withdraw')
    return im

GEM_RING=[(-.72,1.2),(.48,1.3),(.90,.43),(.68,-1.0),(-.45,-1.22),(-.90,-.32)]
@lru_cache(maxsize=1)
def facet_source():
    # Edge extension preserves the exact Hall composition at the graphic handoff.
    source=hall((3.2,5.3,-20),(0,3,5),True)
    return Image.fromarray(np.pad(np.asarray(source),((H,H),(W,W),(0,0)),mode='edge'))

def gem_camera(t):
    q=ease((t-6)/16)
    distance=1.15*math.exp(q*4.18)
    return (q*distance*.19,q*distance*.075,-distance),(0,0,0)

def housing(t):
    eye,target=gem_camera(t)
    im=paper('#343f38').copy();faces=[]
    # Fixed physical geometry: strata behind the jewel, with a foreground rock lip.
    bands=[(-22,-11,'#4b4038'),(-11,-4,'#746249'),(-4,2,'#968567'),(2,7,'#b2a285'),(7,12,'#827d65'),(12,16,'#566755')]
    for low,high,col in bands:
        box(faces,(-65,low,1.4),(65,high,5.0),col)
    polygons(im,faces,eye,target)
    d=Draw(im)
    for low,high,col in bands:
        pts=[(-65,low+.2,1.32),(-25,low+1.0,1.32),(0,low-.5,1.32),(30,low+1.6,1.32),(65,low+.4,1.32)]
        xy,z=project(pts,eye,target)
        if min(z)>.1:d.line(xy.tolist(),'#4a4b3f',2)
    ring=[(x,y,-.22) for x,y in GEM_RING]
    back=[(x*.85,y*.85,.60) for x,y in GEM_RING]
    gems=[]
    for i in range(6):gems.append(([ring[i],ring[(i+1)%6],back[(i+1)%6],back[i]],['#325e46','#467958','#204a39','#123d30','#4c8460','#84a681'][i]))
    gems.append((ring,'#2c7855'))
    polygons(im,gems,eye,target)
    xy,z=project(ring,eye,target)
    # A graphic scale transition: the simulated view is briefly bounded by a facet.
    # It is not a doorway, and this is not a commitment to the outside-view mechanism.
    alpha=1-ease((t-7.3)/2.4)
    if alpha>0 and min(z)>.06:
        source=facet_source()
        corner,_=project([(-2.232,1.2555,-.22),(2.232,1.2555,-.22),(2.232,-1.2555,-.22),(-2.232,-1.2555,-.22)],eye,target)
        dst=corner*S;src=np.array([[0,0],[W*3,0],[W*3,H*3],[0,H*3]],float)
        mat=[];rhs=[]
        for (x,y),(u,v) in zip(dst,src):
            mat.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);rhs.extend([u,v])
        coeff=np.linalg.solve(np.asarray(mat),rhs)
        source=source.transform((W,H),Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC)
        mask=Image.new('L',(W,H));Draw(mask).poly(xy.tolist(),int(255*alpha))
        im.paste(source,(0,0),mask);d=Draw(im)
    if alpha<1:
        bevels=im.copy();bd=Draw(bevels)
        inner=[(x*.72,y*.72,-.22) for x,y in GEM_RING];ip,_=project(inner,eye,target)
        for i in range(6):bd.poly([xy[i],xy[(i+1)%6],ip[(i+1)%6],ip[i]],['#568365','#437b55','#1b503c','#143d31','#397153','#77a077'][i])
        im=Image.blend(im,bevels,1-alpha);d=Draw(im)
    seam,z=project([(-.5,.45,-.235),(.35,-.40,-.235)],eye,target)
    if min(z)>.1 and t>8.7:d.line(seam.tolist(),'#c6d2a0',max(1,5*800/(np.mean(z)*1280)))
    # Occludes the lower right edge after leaving the simulated facet.
    lip=[([(0.45,-.65,-.5),(5.4,-1.4,-.5),(5.5,-3.1,-.5),(.30,-2.8,-.5)],'#72715b')]
    polygons(im,lip,eye,target)
    return im

def hall_transition(t):
    if t<6:
        q=ease(held(t,12)/6)
        return hall((3.2*q,3.1+2.2*q,2.0-22*q),(0,3,7-2*q),True)
    return housing(held(t,12))

@lru_cache(maxsize=1)
def crowd():
    im=hall((8,9,-24),(0,3,5));d=Draw(im)
    # Frozen draw order, poses, eyes, shadows and texture. No frame clock enters.
    for row in range(4):
        h=62+row*30;y=437+row*83
        for j in range(12-row):
            x=60+j*(110+row*5)+row*24
            if x>1250:continue
            puppet(d,x,y,h,'robot','rest', ['#929d94','#acb2a4','#b3b9ac','#bbc0b1'][row],gaze='up')
    return im

def daughter():
    im=paper('#392e2a').copy();d=Draw(im)
    d.poly([(0,0),(760,0),(610,580),(0,720)],'#574136')
    d.poly([(840,0),(1280,0),(1280,720),(719,720)],'#241f21')
    for x in [34,99,160,240]:d.line([(x,0),(x+75,600)],'#73503b',8)
    d.poly([(171,566),(679,487),(1075,573),(996,720),(74,720)],'#77604d')
    for x in range(150,1000,70):d.line([(x,615),(x+100,584)],'#a18a65',3)
    puppet(d,664,771,539,'daughter','jewel')
    # Cord around the waist of the canonical jewel; feasibility remains for design.
    d.line([(626,384),(642,457),(700,461),(718,387)],'#d6c096',4)
    jewel(d,669,451,69)
    d.line([(645,450),(693,448)],'#cbb38d',2)
    # A fur cover across the lap reads as seated on bedding, not standing on it.
    d.poly([(285,673),(518,627),(762,622),(1007,681),(976,720),(182,720)],'#947856')
    for x in range(315,940,48):d.line([(x,685),(x+68,658)],'#b0956c',3)
    return im

def ending(t,variant='crowd'):
    im=(crowd().copy() if variant=='crowd' or t<4 else daughter())
    start=16 if variant=='crowd' else 12
    fade=ease((t-start)/2)
    if fade:im=Image.blend(im,Image.new('RGB',(W,H)),fade)
    return im

def landscape(aliens=False):
    im=paper('#a1a294').copy();d=Draw(im)
    d.ellipse((968,57,1075,165),'#d8cfb0')
    d.poly([(0,319),(245,230),(449,281),(719,227),(1010,309),(1280,251),(1280,720),(0,720)],'#748471')
    d.poly([(0,510),(479,386),(774,455),(1280,356),(1280,720),(0,720)],'#546e54')
    for x,y,h in [(74,638,291),(198,502,182),(1158,581,240),(989,460,127)]:
        d.line([(x,y),(x-13,y-h)],'#4d5440',15)
        for j in range(4):d.poly([(x-13,y-h+24*j),(x-130+20*j,y-h+60+30*j),(x+50,y-h+30+30*j)],'#647d4d')
    if aliens:
        d.poly([(487,346),(650,244),(808,340),(766,413),(536,414)],'#c2bca3',INK,2)
        d.poly([(536,414),(650,360),(766,413)],'#686f68')
        for x in [518,789]:d.line([(x,393),(x-23,469)],'#4f5952',7)
        for x,y in [(797,557),(901,534)]:
            d.poly([(x-11,y),(x-21,y-102),(x-42,y-135),(x+4,y-172),(x+32,y-130),(x+13,y-70),(x+30,y)],'#d3c7a6')
            d.line([(x-17,y-120),(x+9,y-135)],'#444e49',7)
        d.text((640,668),'Where is everybody?',30,'#f0e5c9',False,'mm')
    return im

def feast():
    im=paper('#4e3830').copy();d=Draw(im)
    d.poly([(0,83),(395,17),(970,37),(1280,211),(1280,720),(0,720)],'#654638')
    for x in [79,266,1093,1200]:puppet(d,x,554,197,'human','proud','#a17d58')
    puppet(d,515,621,322,'warrior','point')
    puppet(d,892,593,301,'elder-human','withdraw')
    puppet(d,1045,649,291,'daughter','withdraw')
    d.poly([(0,566),(713,522),(827,639),(0,703)],'#8f6343')
    for x in [120,260,449,602]:d.ellipse((x,582,x+75,604),'#b49160')
    jewel(d,634,382,46)
    return im

def record():
    im=hall((-.4,3.1,2),(0,3.3,10),True);d=Draw(im)
    # Record metaphor for an ordinary person, deliberately no chosen biography yet.
    d.rect((395,122,882,574),'#c4b391')
    d.rect((415,146,864,550),'#a58f6c')
    d.line([(492,431),(794,431)],'#574e3f',10)
    d.line([(520,435),(510,513)],'#574e3f',8);d.line([(770,435),(780,513)],'#574e3f',8)
    puppet(d,566,513,240,'record-human','rest')
    d.line([(492,431),(794,431)],'#574e3f',10)
    d.line([(746,404),(743,322),(805,321),(807,490)],'#605441',8)
    d.line([(743,417),(807,417)],'#605441',8)
    return im

def recurrence():
    im=landscape();d=Draw(im)
    # Three separate eras in one rough board panel, not a literal morphing shot.
    for x in [425,855]:d.line([(x,180),(x,664)],'#bbb79b',2)
    d.poly([(101,575),(236,565),(291,545),(308,567),(241,597),(123,597),(74,615)],'#384d3d')
    d.poly([(479,547),(683,526),(748,491),(799,507),(767,546),(699,563),(672,610),(647,610),(654,562),(524,576),(511,614),(487,614)],'#394a3a')
    puppet(d,1047,623,213,'human','rest','#938263')
    d.text((217,223),'EARLIER',19,'#e2dbc0',True,'mm');d.text((640,223),'MUCH LATER',19,'#e2dbc0',True,'mm');d.text((1066,223),'LATER STILL',19,'#e2dbc0',True,'mm')
    return im

def hand():
    im=paper('#807a5d').copy();d=Draw(im)
    for j,col in enumerate(['#72745a','#999271','#a6a27c','#6c7052']):d.poly([(0,320+j*80),(550,274+j*86),(1280,318+j*93),(1280,720),(0,720)],col)
    d.poly([(1280,0),(1120,0),(1000,148),(917,297),(752,328),(681,369),(700,407),(821,384),(754,476),(778,502),(879,397),(854,493),(880,505),(940,391),(993,329),(1091,211)],'#b09975', '#6b5b47',3)
    jewel(d,700,431,157)
    return im

def board_frame(scene):
    if scene=='routine':return factory(1)
    if scene=='rewrite':return factory(40,{'duplicate':12,'door_vanish':16,'timer':20,'eyes':25,'circle_cut':99,'safety':9})
    if scene=='circle':return circle(True)
    if scene=='record':return record()
    if scene=='hall':return hall()
    if scene=='strata':return housing(21)
    if scene=='jungle':return landscape()
    if scene=='aliens':return landscape(True)
    if scene=='return':return recurrence()
    if scene=='hand':return hand()
    if scene=='feast':return feast()
    if scene=='witnesses':return crowd().copy()
    raise ValueError(scene)
