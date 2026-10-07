"""Draft 5: princess, chromatic partner, physical stage, and attack-driven montage."""
import argparse, importlib.util, json, math, os, hashlib
from pathlib import Path
from bisect import bisect_right
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageEnhance, ImageFilter
ROOT=Path(__file__).resolve().parent
RUN=Path('data/workspace/carnival-dream/draft-v5-kinetic')
base_path=ROOT/'base-render.py' if (ROOT/'base-render.py').exists() else Path('tools/carnival-dream/shadow-theatre/render.py')
mod=importlib.util.spec_from_file_location('base',base_path);base=importlib.util.module_from_spec(mod);mod.loader.exec_module(base)
SPEC=json.loads((RUN/'timeline.json').read_text());SHOTS=SPEC['shots'];STARTS=[s['start_frame'] for s in SHOTS]
ATTACKS=json.loads(Path('data/workspace/carnival-dream/analysis-v1/onsets.json').read_text())
ATTACK_TIMES=[o['time'] for o in ATTACKS]
TAU=math.tau;INK=base.INK;GOLD=base.GOLD;IVORY=base.IVORY
COLORS={'black':(17,20,29),'crimson':(192,22,47),'violet':(113,31,167),'cobalt':(24,99,173),'magenta':(185,27,115)}
CURRENT={};CURRENT_FRAME=0;MALE_MASK=None
PLATE=Image.open(RUN/'assets/stage-full.png').convert('RGB')
FORE=Image.open(RUN/'assets/stage-foreground.png').convert('RGBA')
# Only the canvas receives colored gels; the same wood, velvet, brass and fixtures recur.
canvasmask=ImageChops.invert(FORE.getchannel('A'))
BGS={}
for name,c in {'amber':(214,176,117),'blue':(121,151,159),'red':(184,128,117),'mono':(198,193,173),'night':(103,126,145)}.items():
 tint=ImageChops.multiply(PLATE,Image.new('RGB',PLATE.size,c))
 BGS[name]=Image.composite(tint,ImageEnhance.Brightness(PLATE).enhance(.82),canvasmask)
# The figures stand ON the rear boards. Only the front lip and footlights occlude them.
front_alpha=FORE.getchannel('A');ad=ImageDraw.Draw(front_alpha);k=FORE.width/1600
ad.rectangle((170*k,735*k,1430*k,850*k),fill=0);FORE.putalpha(front_alpha)
FORE=ImageEnhance.Brightness(FORE).enhance(.82)

class Stage(base.Stage):
 def __init__(self,mode='amber',zoom=1,cx=800,cy=450,roll=0):
  global MALE_MASK
  view=CURRENT['view'];idx=int(CURRENT['source_id'][2:])
  # Independent camera takes of the same continuous performance.
  if view=='wide':zoom=1;cx=800;cy=450;roll=0
  elif view=='pair':zoom=1.18;cx=810;cy=500;roll=0
  elif view=='dutch':zoom=1.14;cx=800;cy=480;roll=.035*(-1 if int(CURRENT['id'][1:])%2 else 1)
  elif view=='locked':zoom=1.10;cx=800;cy=470;roll=0
  elif view=='detail':
   zoom=1.64;cx=800;cy=475;roll=0
   if idx in [2,3,7,17,18,19,38]:cx=650 if idx!=17 else 755;cy=450;zoom=1.9
   if idx==6:cx=800;cy=705;zoom=1.85
   if idx in [11,22,34]:cx=1060;cy=480;zoom=1.70
   if idx in [13,23,36]:cx=805;cy=590;zoom=1.55
   if idx in [15,24,37]:cx=800;cy=580;zoom=1.60
   if idx in [29,30]:cx=960;cy=410;zoom=1.50
   if idx in [31,32]:cx=945;cy=445;zoom=1.5
   if idx==1:cx=800;cy=450;zoom=1.65
  self.z=zoom;self.cx=cx;self.cy=cy;self.roll=roll
  cs=math.cos(roll);sn=math.sin(roll);k=PLATE.width/1600;z=zoom
  affine=(k*cs/(1.2*z),k*sn/(1.2*z),k*(cx-(800*cs+450*sn)/z),-k*sn/(1.2*z),k*cs/(1.2*z),k*(cy+(800*sn-450*cs)/z))
  self.im=BGS[mode].transform((1920,1080),Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC)
  self.fore=FORE.transform((1920,1080),Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC)
  self.layer=Image.new('RGBA',(1920,1080));self.d=ImageDraw.Draw(self.layer);self.mode=mode
  MALE_MASK=Image.new('L',(1920,1080))
 def finish(self,f):
  self.flush()
  # Foreground columns and velvet physically occlude the paper performance.
  self.im=Image.alpha_composite(self.im.convert('RGBA'),self.fore).convert('RGB')
  # Light film grain remains frozen during the male-only replacement sequence.
  grain=base.GRAIN[(400 if CURRENT['lock_except_male_color'] else f)%4]
  return ImageChops.add(self.im,Image.merge('RGB',(grain,)*3),offset=-128)

base.Stage=Stage

def arch(s,t,open_=1):
 # Physical plate supplies the proscenium. A brief opening curtain is paper on the screen.
 if open_<.95:
  w=620*(1-open_)
  s.poly([(185,132),(185+w,132),(185+w*.9,786),(185,786)],(45,20,28))
  s.poly([(1415,132),(1415-w,132),(1415-w*.9,786),(1415,786)],(45,20,28))
base.arch=arch

def bez(points,steps=18):
 """Cubic contours for flowing hair and a bell gown, rather than angular polygons."""
 result=[]
 for a,b,c,d in points:
  for t in np.linspace(0,1,steps):
   result.append(((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*d[0],(1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*d[1]))
 return result

def puppet(s,x,y,scale=1,t=0,pose='idle',shadow=False,flip=False,color=IVORY,strings=True,reach=0):
 global MALE_MASK
 male=shadow;col=COLORS[CURRENT['male_color']] if male else (242,216,160)
 edge=tuple(max(10,int(v*.55)) for v in col) if male else (73,49,45)
 if scale>=.9:y+=30
 # More animated silhouettes; motion steps are still held in the final timeline.
 energy=1.45 if pose in ['dance','walk'] else 1
 bob=2.5*math.sin(t*4.6);lean=.035*math.sin(t*2.3)
 if pose=='bow':lean=.12
 if pose=='reach':reach=1
 if pose=='dance':lean=.105*math.sin(t*2.3);reach=.60+.35*math.sin(t*2.3)
 sign=-1 if flip else 1
 def p(q):
  u,v=q;u*=sign
  return x+scale*(u*math.cos(lean)-v*math.sin(lean)),y+scale*(u*math.sin(lean)+v*math.cos(lean)+bob)
 if male:
  previous=s.layer;s.layer=Image.new('RGBA',(1920,1080));s.d=ImageDraw.Draw(s.layer)
 def poly(pts,c=col,outline=edge,w=1.2):s.poly([p(z) for z in pts],c,outline,w)
 def line(pts,c=edge,w=1.2):s.line([p(z) for z in pts],c,w)
 def ell(q,rx,ry,c):s.ell(*p(q),rx*scale,ry*scale,c)
 def limb(a,b,w,c=col):
  dx=b[0]-a[0];dy=b[1]-a[1];l=math.hypot(dx,dy);nx=-dy/l*w/2;ny=dx/l*w/2
  poly([(a[0]+nx,a[1]+ny),(b[0]+nx*.68,b[1]+ny*.68),(b[0]-nx*.68,b[1]-ny*.68),(a[0]-nx,a[1]-ny)],c)
  ell(a,w*.42,w*.42,c);ell(b,w*.31,w*.31,c)
 walk=math.sin(t*4.6)*energy if pose in ['walk','dance'] else .14*math.sin(t*2.3)
 # Hair is behind the princess's arms and gown, with a repeated ribbon and tiny star.
 if not male:
  hair=bez([((-21,-98),(-60,-111),(-70,-47),(-42,-10)),((-42,-10),(-64,25),(-24,55),(-48,95)),((-48,95),(10,75),(-4,38),(-4,-3)),((-4,-3),(18,-39),(28,-72),(4,-99)),((4,-99),(-3,-107),(-14,-106),(-21,-98))])
  poly(hair,(44,33,36))
  line([(-34,-55),(-39,-9),(-26,38),(-31,64)],(121,79,56),1.5)
  poly([(-33,-57),(-63,-47),(-48,-35),(-35,-44),(-48,-17),(-28,-36)],(140,43,65))
 for side in [-1,1]:
  hip=(side*20,108 if male else 183);knee=(side*23+walk*side*14,192 if male else 225);foot=(side*28-walk*side*12,261-max(0,walk*side)*10)
  limb(hip,knee,24 if male else 12);limb(knee,foot,17 if male else 9)
  poly([(foot[0]-9,foot[1]-15),(foot[0]+7,foot[1]-15),(foot[0]+24,foot[1]+3),(foot[0]-12,foot[1]+3)],edge)
  if male:ell(knee,3,3,(195,148,80))
 if male:
  # High-collared tailcoat, narrow hips, trousers, and pointed boots: a separate male outline.
  poly([(-39,9),(-17,1),(15,1),(39,11),(34,56),(27,96),(48,144),(13,125),(0,104),(-14,129),(-44,146),(-29,88),(-32,52)])
  poly([(-16,5),(0,37),(16,5),(13,57),(0,76),(-13,57)],tuple(min(255,int(v*1.1)+15) for v in col))
  line([(-16,5),(-26,27),(0,45),(26,27),(16,5)],(201,158,96),1.1)
  for yy in [50,67,83]:ell((0,yy),2,2,(220,174,94))
 else:
  # Classic fitted bodice, tiny waist and a full bell-shaped skirt that reaches the floor.
  poly([(-28,9),(-11,18),(0,10),(11,18),(28,9),(27,38),(15,76),(0,88),(-16,76),(-27,38)])
  skirt=bez([((-16,74),(-26,102),(-72,120),(-87,179)),((-87,179),(-96,211),(-112,239),(-131,248)),((-131,248),(-74,270),(74,268),(128,247)),((128,247),(101,228),(92,204),(82,173)),((82,173),(64,116),(26,102),(16,74)),((16,74),(5,82),(-5,82),(-16,74))])
  poly(skirt)
  # Ivory front panel, warm underskirt and scalloped embroidery keep the silhouette readable.
  panel=bez([((-8,86),(-17,143),(-47,206),(-70,256)),((-70,256),(-28,264),(26,264),(69,256)),((69,256),(39,195),(21,141),(8,86)),((8,86),(3,88),(-3,88),(-8,86))])
  poly(panel,(250,232,189),(174,136,90),1)
  for side in [-1,1]:
   for j in range(3):
    pts=bez([((side*(23+j*4),101+j*14),(side*(40+j*10),158),(side*(55+j*15),218),(side*(77+j*19),248))])
    line(pts,(185,139,83),1)
  for j in range(9):
   xx=-105+j*26;s.star(*p((xx,247+5*math.cos(xx*.013))),scale*3.8,(162,83,57),.1*j)
  line([(-19,75),(0,84),(18,75)],(175,113,58),3)
 # Arms and hands preserve reach, pluck and wind actions from the original story.
 elbows=[(-59,68-23*reach),(64+reach*15,62-reach*35)]
 hands=[(-48,118-40*reach),(64+reach*74,112-reach*100)]
 if pose=='pluck':elbows[1]=(63,-31);hands[1]=(86,-98)
 if pose=='wind':elbows[1]=(65,53);hands[1]=(100+12*math.cos(t*3),64+12*math.sin(t*3))
 for a,b,c in zip([(-29,21),(29,21)],elbows,hands):
  limb(a,b,19 if male else 12);limb(b,c,13 if male else 9)
  if not male:ell(a,16,13,(237,201,142));ell(b,3,3,(168,126,81))
  else:ell(b,3,3,(201,158,96))
  poly([(c[0]-5,c[1]-5),(c[0]+5,c[1]-5),(c[0]+15,c[1]+1),(c[0]+10,c[1]+5),(c[0]+5,c[1]+10),(c[0]-5,c[1]+8)])
 # Different male and female profiles, both retain silhouette readability at wide scale.
 if male:
  poly([(-13,11),(-13,-19),(-31,-39),(-32,-76),(-20,-93),(9,-95),(27,-80),(28,-61),(43,-49),(29,-43),(26,-20),(12,-10),(12,11)])
  poly([(-32,-57),(-40,-70),(-36,-94),(-12,-112),(15,-100),(33,-87),(28,-77),(1,-82),(-17,-66)],edge)
  line([(12,-61),(23,-60)],(211,163,93),1)
 else:
  profile=bez([((-11,12),(-10,-5),(-16,-17),(-23,-26)),((-23,-26),(-37,-49),(-30,-82),(-14,-91)),((-14,-91),(4,-99),(22,-89),(24,-70)),((24,-70),(26,-58),(27,-56),(36,-51)),((36,-51),(38,-49),(27,-46),(27,-46)),((27,-46),(30,-38),(23,-35),(23,-35)),((23,-35),(21,-17),(7,-20),(8,12))])
  poly(profile)
  # Swept fringe, long hair, three-point crown, necklace, and pearl earring.
  fringe=bez([((-28,-52),(-45,-69),(-33,-97),(-11,-105)),((-11,-105),(9,-112),(31,-95),(27,-78)),((27,-78),(6,-83),(-6,-69),(-28,-52))])
  poly(fringe,(44,33,36))
  poly([(-26,-99),(-33,-121),(-17,-111),(-9,-136),(0,-111),(17,-125),(14,-99)],(224,178,79),(112,78,44),1.3)
  for pt in [(-33,-121),(-9,-136),(17,-125)]:ell(pt,2.6,2.6,(244,215,139))
  s.star(*p((-9,-108)),scale*4,(148,36,64))
  line([(10,-60),(20,-60),(23,-64)],(61,40,38),1.5);line([(21,-36),(28,-35)],(140,43,65),1.4)
  ell((-12,-36),2.4,3.4,(249,232,178));line([(-11,12),(0,18),(11,12)],(168,110,52),1.4);ell((0,19),3,4,(151,36,62))
 if strings:
  for q in [(-28,20),(28,20),*hands]:
   v=p(q);s.line([(v[0]+12*math.sin(t*.8),60),v],(93,83,67,125),.65)
 if male:
  male_layer=s.layer;MALE_MASK=ImageChops.lighter(MALE_MASK,male_layer.getchannel('A'))
  s.layer=Image.alpha_composite(previous,male_layer);s.d=ImageDraw.Draw(s.layer)
 return p(hands[1])
base.puppet=puppet

# Snap ride assembly/disassembly to actual nearby attacks, accelerating rotation on chorus returns.
original_wheel=base.wheel;original_carousel=base.carousel;original_swings=base.swings

def cue_step():
 story=next(s for s in SPEC['story_shots'] if s['id']==CURRENT['source_id']);a=story['start'];b=story['end']
 hits=[o['time'] for o in ATTACKS if a<=o['time']<b and o['strength']>=.25]
 if not hits:return (CURRENT_FRAME/24-a)/(b-a)
 return sum(v<=CURRENT_FRAME/24 for v in hits)/len(hits)

def wheel(s,t,*a,**kw):
 idx=int(CURRENT['source_id'][2:])
 if not CURRENT['lock_except_male_color']:
  if idx in [9,11]:kw['amount']=max(1/12,math.floor(cue_step()*12)/12)
  if idx==34:kw['amount']=1-math.floor(cue_step()*12)/12
 return original_wheel(s,t*1.65 if not kw.get('broken') else t,*a,**kw)
def carousel(s,t,x=800,y=568,r=360,broken=False,dismantle=0):
 idx=int(CURRENT['source_id'][2:])
 if idx==36:dismantle=math.floor(cue_step()*6)/6
 count=max(1,int(cue_step()*6)) if idx==13 else 6
 s.ell(x,y+150,r,54,INK,GOLD,4);s.ell(x,y+140,r*.97,45,(103,70,49),GOLD,2)
 s.line([(x,y-295),(x,y+140)],GOLD,13)
 phase=t*.86 if not broken else -TAU/3+math.pi/2+(t-96.48)*.18
 for z,i in sorted([(math.sin(phase+i*TAU/6),i) for i in range(6)]):
  if i>=count:continue
  a=phase+i*TAU/6;px=x+math.cos(a)*r*.76;py=y+z*46
  if dismantle:py+=dismantle*(180+30*i);px+=(px-x)*dismantle*.5
  scale=.65+.19*(z+1);s.line([(px,py-250),(px,py+122)],GOLD,4)
  if not(broken and i==2):base.horse(s,px,py+18*math.sin(t*3.1+i),scale,0,IVORY if z>0 else (117,122,115))
  else:s.line([(px-20,py+30),(px+20,py+30)],base.ROSE,6)
 cy=y-255-dismantle*250
 for i in range(12):
  a=i*math.pi/12;b=(i+1)*math.pi/12
  s.poly([(x,cy-100),(x+r*math.cos(a),cy+25*math.sin(a)),(x+r*math.cos(b),cy+25*math.sin(b))],base.ROSE if i%2 else IVORY,INK,1)
 s.line([(x-r,cy),(x+r,cy)],GOLD,8)
 for i in range(13):s.ell(x-r+i*r/6,cy+7,6,6,IVORY)
 s.star(x,cy-117,23,GOLD,t*.40)
def swings(s,t,*a,**kw):
 idx=int(CURRENT['source_id'][2:])
 if idx==15:kw['amount']=max(1/8,math.floor(cue_step()*8)/8)
 if idx==37:kw['amount']=1-math.floor(cue_step()*8)/8
 return original_swings(s,t*1.65 if not kw.get('broken') else t,*a,**kw)
base.wheel=wheel;base.carousel=carousel;base.swings=swings

def render(f):
 global CURRENT,CURRENT_FRAME
 CURRENT=SHOTS[bisect_right(STARTS,f)-1];CURRENT_FRAME=f
 source=CURRENT['source_frame'] if CURRENT['lock_except_male_color'] else f
 return base.render(source)

def contact(stills,filename,cols=5):
 n=len(stills);out=Image.new('RGB',(cols*384,math.ceil(n/cols)*238),(17,19,25));d=ImageDraw.Draw(out)
 for i,(p,label) in enumerate(stills):
  im=Image.open(p);im.thumbnail((384,216));x=i%cols*384;y=i//cols*238;out.paste(im,(x,y));d.text((x+6,y+219),label,fill=(237,216,175))
 out.save(filename,quality=91)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--start',type=int,default=0);ap.add_argument('--end',type=int,default=4084);ap.add_argument('--frame',type=int);args=ap.parse_args()
 if args.frame is not None:render(args.frame).save(RUN/'stills'/f'frame-{args.frame:05d}.png');return
 if args.stills:
  stills=[]
  for clip in SHOTS:
   f=(clip['start_frame']+clip['end_frame'])//2;p=RUN/'stills'/f"{clip['id']}.jpg";render(f).save(p,quality=92);stills.append((p,f"{clip['id']} {clip['start']:.2f}s {clip['view']} {clip['male_color']}"))
  for page in range(math.ceil(len(stills)/35)):contact(stills[page*35:(page+1)*35],RUN/'review'/f'contact-{page+1}.jpg')
 if args.render:
  cuts=set(STARTS);last=None
  for f in range(args.start,args.end):
   p=RUN/'frames'/f'frame-{f:05d}.png'
   if f%3==0 or f in cuts or last is None:
    if not p.exists():render(f).save(p,compress_level=1)
    last=p
   elif not p.exists():os.link(last,p)
   if f%120==0:print(f'{f}/4084',flush=True)
if __name__=='__main__':main()
