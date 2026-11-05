#!/usr/bin/env python3
"""Exact optical stimuli. All time is derived from integer frame indices."""
import argparse
import hashlib
import json
import math
import subprocess
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, FRAMES = 1080, 1920, 60, 2280
BG = (11, 15, 23)
IVORY = (234, 230, 215)
BLUE = (58, 202, 247)
MUTED = (127, 140, 154)
CX, CY, RADIUS = 500, 975, 383
TARGET_RADIUS = 66
FONT = Path('/System/Library/Fonts/Avenir Next.ttc')
FALLBACK_FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
if not FONT.exists():
    FONT = FALLBACK_FONT


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def smooth(t, a, b):
    q = max(0., min(1., (t-a)/(b-a)))
    return q*q*(3-2*q)


def window(t, a, b, fade=.3):
    return smooth(t, a, a+fade)*(1-smooth(t, b-fade, b))


def mix(a, b, p):
    return tuple(round(x+(y-x)*p) for x, y in zip(a, b))


@lru_cache(128)
def font(size):
    return ImageFont.truetype(str(FONT), size, index=0)


def text(im, message, y, size=50, color=IVORY, opacity=1, center=CX):
    if opacity <= 0:
        return
    d = ImageDraw.Draw(im)
    f = font(size)
    width = d.textlength(message, font=f)
    if width > 860:
        raise ValueError('Caption exceeds safe width: '+message)
    d.text((center-width/2, y), message, font=f, fill=mix(BG, color, opacity))


@lru_cache(4096)
def circle_mask(radius_q, xq, yq):
    r = radius_q/4
    n = math.ceil(2*r)+8
    mask = Image.new('L', (n*3, n*3))
    d = ImageDraw.Draw(mask)
    x, y = 3+xq/4, 3+yq/4
    d.ellipse((x*3, y*3, (x+2*r)*3, (y+2*r)*3), fill=255)
    return mask.resize((n, n), Image.Resampling.LANCZOS)


def circle(im, x, y, r, color, opacity=1):
    if opacity < .002:
        return
    left, top = x-r-3, y-r-3
    ix, iy = math.floor(left), math.floor(top)
    xq, yq = round((left-ix)*4), round((top-iy)*4)
    mask = circle_mask(round(r*4), xq, yq)
    if opacity < 1:
        mask = mask.point(lambda v: round(v*opacity))
    im.paste(color, (ix, iy, ix+mask.width, iy+mask.height), mask)


def line(im, points, color, opacity=1, width=2):
    if opacity < .002:
        return
    ImageDraw.Draw(im).line(points, fill=mix(BG, color, opacity), width=width)


def header(im, chapter, t):
    d = ImageDraw.Draw(im)
    d.text((91, 135), 'FALSE COLOR', font=font(22), fill=MUTED)
    d.text((718, 135), chapter, font=font(20), fill=MUTED)
    line(im, [(92, 190), (909, 190)], MUTED, .23, 1)


def tusi_positions(t):
    theta = np.arange(8)*np.pi/8
    phase = (t-14)*2*np.pi/5 + np.pi/2
    scalar = RADIUS*np.cos(phase-theta)
    return np.column_stack((CX+scalar*np.cos(theta), CY+scalar*np.sin(theta)))


def frame(index):
    t = index/FPS
    im = Image.new('RGB', (W,H), BG)
    if t < 14:
        header(im, '01 / SIZE', t)
        swap = smooth(t, 4.1, 7.3)
        surrounds = 1-smooth(t, 9, 9.7)
        merge = smooth(t, 11.8, 13.6)
        ys = [685+(CY-685)*merge, 1265+(CY-1265)*merge]
        for y, size in zip(ys, (swap, 1-swap)):
            r, orbit = 27+78*size, 117+111*size
            for n in range(6):
                a = (n+.5)*2*math.pi/6
                circle(im, CX+orbit*math.cos(a), y+orbit*math.sin(a), r, IVORY, surrounds)
        guides = window(t, 9.65, 12.1, .35)
        for y in ys:
            line(im, [(CX-66,y-92),(CX+66,y-92)], IVORY, guides*.8)
            for x in (CX-66,CX+66):
                line(im, [(x,y-104),(x,y-80)], IVORY, guides*.8)
        # The exact same cached mask and RGB value are used for both targets.
        for y in ys:
            circle(im, CX, y, TARGET_RADIUS, BLUE)
        text(im, 'which blue is bigger?', 256, opacity=1-smooth(t,3.3,3.65))
        text(im, 'watch the blue.', 256, opacity=window(t,3.8,8.7,.3))
        text(im, 'they never changed size.', 256, size=46, opacity=window(t,9.75,13.5,.3))
        text(im, 'only their company did.', 326, size=31, color=MUTED, opacity=window(t,10.5,13.5,.3))
    else:
        tag = smooth(t,35,35.7)
        header(im, '02 / MOTION', t)
        points = tusi_positions(t)
        grow = smooth(t,14,15.2)
        first_r = TARGET_RADIUS+(26-TARGET_RADIUS)*grow
        # Hold at the merge point while smoothly catching the continuous trajectory.
        points[0] = np.array([CX,CY])*(1-grow)+points[0]*grow
        wheel_opacity = 1-.93*tag
        single_guide = window(t,20,24,.35)
        all_guides = window(t,23.4,27,.5)
        guide_strength = max(single_guide,all_guides)
        for n in range(8):
            a = n*math.pi/8
            g = guide_strength if n == 0 else all_guides*.67
            p0 = (CX-RADIUS*math.cos(a),CY-RADIUS*math.sin(a))
            p1 = (CX+RADIUS*math.cos(a),CY+RADIUS*math.sin(a))
            line(im, [p0,p1], BLUE if n == 0 else MUTED, g*.7, 2)
            for x,y in (p0,p1):
                circle(im,x,y,3,BLUE if n==0 else MUTED,g)
        # Highlight is restored only for the path demonstration, then becomes ivory.
        highlight = 1-smooth(t,27,27.65)
        for n,(x,y) in enumerate(points):
            color = mix(IVORY,BLUE,highlight) if n==0 else IVORY
            r = first_r if n==0 else 26
            appear = 1 if n==0 else smooth(t,14.35+(n-1)*.11,15.2+(n-1)*.11)
            circle(im,float(x),float(y),r,color,appear*wheel_opacity)
        text(im, 'a wheel?', 256, opacity=window(t,15.7,18.6))
        text(im, 'follow the blue dot.', 256, size=47, opacity=window(t,18.8,23.1))
        text(im, 'one straight line.', 327, size=31, color=MUTED, opacity=window(t,20.7,23.1))
        text(im, 'eight straight lines.', 256, size=47, opacity=window(t,23.5,27.05))
        text(im, 'now watch them together.', 256, size=43, opacity=window(t,27.5,31.15))
        text(im, 'the whole changes the motion.', 256, size=39, opacity=window(t,31.45,34.7))
        if tag > 0:
            text(im, 'TOGETHER', 830, size=83, opacity=tag)
            text(im, 'FALSE COLOR', 953, size=25, color=BLUE, opacity=tag)
            text(im, 'same parts. different perception.', 1051, size=28, color=MUTED, opacity=tag)
    return im


def checks(workspace):
    # Every actual Tusi source point stays on a fixed diameter. Exclude the
    # deliberate introduction transition from the physical-invariant claim.
    indices = np.arange(16*FPS,35*FPS)
    points = np.array([tusi_positions(i/FPS) for i in indices])
    theta = np.arange(8)*np.pi/8
    p = points-np.array([CX,CY])
    perpendicular = p[:,:,0]*(-np.sin(theta))+p[:,:,1]*np.cos(theta)
    phase = (indices/FPS-14)*2*np.pi/5+np.pi/2
    centers = np.column_stack((CX+RADIUS/2*np.cos(phase),CY+RADIUS/2*np.sin(phase)))
    radial = np.linalg.norm(points-centers[:,None,:],axis=2)
    same = []
    target_masks = []
    for i in (0,120,240,342,438,510,560):
        image = np.asarray(frame(i))
        a = image[615:756,430:571]
        b = image[1195:1336,430:571]
        same.append(bool(np.array_equal(a,b)))
        target_masks.append(hashlib.sha256(a.tobytes()).hexdigest())
    report = {
        'schemaVersion':1,'frames':FRAMES,'fps':FPS,'durationSeconds':FRAMES/FPS,
        'targetRadiusPixels':TARGET_RADIUS,
        'pairedTargetCropsIdentical':all(same),
        'targetCropStableDuringContextChange':len(set(target_masks))==1,
        'maxPathPerpendicularErrorPixels':float(np.abs(perpendicular).max()),
        'maxCollectiveRadiusErrorPixels':float(np.abs(radial-RADIUS/2).max()),
        'invariantMotionRangeFrames':[16*FPS,35*FPS],
        'sourceRgbBlue':BLUE,'sourceRgbBackground':BG,
        'claims':'Equal target masks and straight individual trajectories are checked. Perceptual effect strength and listening remain human review.'
    }
    if not all(same) or len(set(target_masks))!=1 or report['maxPathPerpendicularErrorPixels']>1e-9:
        raise ValueError(json.dumps(report))
    (workspace/'qa/geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def stills(workspace):
    times = [1,5.7,8,10.6,13.8,16.7,21.5,24.8,29,33,36.5]
    cards=[]
    for t in times:
        im=frame(round(t*FPS))
        im.save(workspace/f'refs/frame-{round(t*FPS):04d}.png')
        card=Image.new('RGB',(270,520),BG)
        card.paste(im.resize((270,480),Image.Resampling.LANCZOS),(0,0))
        ImageDraw.Draw(card).text((12,488),f'{t:04.1f}s',font=font(18),fill=IVORY)
        cards.append(card)
    sheet=Image.new('RGB',(270*4,520*3),BG)
    for i,c in enumerate(cards): sheet.paste(c,((i%4)*270,(i//4)*520))
    sheet.save(workspace/'qa/contact-sheet.png')


def render(workspace, preview):
    name = 'proof-540-v1.mp4' if preview else 'picture-v1.mp4'
    out=workspace/'render'/name
    if out.exists(): raise SystemExit('Refusing to overwrite '+str(out))
    width,height=(540,960) if preview else (W,H)
    snapshot={'createdAt':datetime.now(timezone.utc).isoformat(),'method':'local-programmatic',
              'recipeSha256':sha(__file__),'fontSha256':sha(FONT),'fontName':FONT.name,
              'width':width,'height':height,'fps':FPS,'frames':FRAMES,
              'provider':None,'model':None,'prompt':None,
              'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]}
    receipt=workspace/'provenance'/(name+'.json')
    if receipt.exists(): raise SystemExit('Refusing to overwrite recipe receipt')
    receipt.write_text(json.dumps(snapshot,indent=2)+'\n')
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-n','-f','rawvideo','-pix_fmt','rgb24',
         '-s',f'{width}x{height}','-r',str(FPS),'-i','pipe:0','-an',
         '-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
         '-c:v','libx264','-preset','fast','-crf','14' if not preview else '19',
         '-threads','6','-color_range','tv','-colorspace','bt709','-color_primaries','bt709',
         '-color_trc','bt709','-movflags','+faststart',str(out)]
    start=time.monotonic()
    with open(workspace/'scratch'/(name+'.ffmpeg.log'),'w') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        try:
            for i in range(FRAMES):
                im=frame(i)
                if preview:im=im.resize((width,height),Image.Resampling.LANCZOS)
                proc.stdin.write(im.tobytes())
                if i%300==0: print(json.dumps({'frame':i,'of':FRAMES,'elapsed':round(time.monotonic()-start,1)}),flush=True)
        finally:
            proc.stdin.close()
        if proc.wait()!=0: raise RuntimeError('FFmpeg failed; inspect retained log')
    snapshot.update({'outputSha256':sha(out),'renderSeconds':round(time.monotonic()-start,2)})
    (workspace/'provenance'/(name+'.completed.json')).write_text(json.dumps(snapshot,indent=2)+'\n')
    print(json.dumps({'output':str(out),'sha256':snapshot['outputSha256'],'seconds':snapshot['renderSeconds']}),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('workspace',type=Path)
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--render',action='store_true')
    args=parser.parse_args()
    for folder in ['refs','render','qa','scratch','provenance']:(args.workspace/folder).mkdir(parents=True,exist_ok=True)
    print(json.dumps(checks(args.workspace)),flush=True)
    if args.stills:stills(args.workspace)
    if args.preview:render(args.workspace,True)
    if args.render:render(args.workspace,False)


if __name__=='__main__':main()
