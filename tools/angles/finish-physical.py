#!/usr/bin/env python3
"""Perspective sampling, held-frame finishing and QA for the solid-metal study."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

p=argparse.ArgumentParser()
p.add_argument('--panorama',type=Path,required=True)
p.add_argument('--scene-run',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
for folder in ['frames','qa','recipe','source']: (a.output/folder).mkdir()
meta=json.loads((a.panorama/'manifest.json').read_text())
manifest=json.loads((a.scene_run/'manifest.json').read_text())
assert meta['materialsOpaque'] and meta['neutralMaterialsAndLights']
assert meta['width']>=16384 and meta['height']>=4096
assert meta['cameraOrigin']==[0,0,0]
image=cv2.imread(str(a.panorama/'radiance.png'),cv2.IMREAD_UNCHANGED)
assert image.dtype==np.uint16 and image.ndim==2
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(a.panorama/'radiance.png')==meta['sha256']
for file in ['radiance.png','manifest.json','angles-solid-silver-panorama.blend']:
    shutil.copyfile(a.panorama/file,a.output/'source'/file)
for file in ['physical.py','physical-panorama.py','finish-physical.py']:
    shutil.copyfile(Path(__file__).parent/file,a.output/'recipe'/file)

W,H=1920,1080
py,px=np.indices((H,W),dtype=np.float32)
focal=W*35/36
screen_x=(px+.5-W/2)/focal
screen_y=(H/2-py-.5)/focal
def pose(t):
    s=next((s for s in manifest['shots'] if s['start']<=t<s['end']),manifest['shots'][-1])
    u=max(0,min(1,(t-s['start']-.375)/(s['end']-s['start']-.875)));u=u*u*(3-2*u)
    angles=[x+(y-x)*u for x,y in zip(s['from'],s['to'])]
    return angles,s['id']

def project(angles):
    yaw,pitch,roll=np.deg2rad(angles)
    forward=np.array([math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)],dtype=np.float32)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    rr=right*math.cos(roll)+up*math.sin(roll);uu=up*math.cos(roll)-right*math.sin(roll)
    direction=forward+screen_x[...,None]*rr+screen_y[...,None]*uu
    direction/=np.linalg.norm(direction,axis=2,keepdims=True)
    mx=((.5-np.arctan2(direction[:,:,1],direction[:,:,0])/math.tau)*image.shape[1]-.5).astype(np.float32)
    my=((math.pi/4-np.arcsin(direction[:,:,2]))/(math.pi/2)*image.shape[0]-.5).astype(np.float32)
    assert my.min()>=0 and my.max()<image.shape[0]-1
    remap=cv2.remap(image,mx,my,cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_WRAP)
    return np.clip(np.round(remap.astype(np.float32)/257),0,255).astype(np.uint8)

frames=[];cache={}
for i in range(240):
    angles,shot=pose(i/8);key=tuple(round(x,10) for x in angles)
    name=f'frames/frame-{i:04d}.png';dest=a.output/name
    if key in cache:shutil.copyfile(a.output/cache[key],dest)
    else:
        out=project(angles);cv2.imwrite(str(dest),out,[cv2.IMWRITE_PNG_COMPRESSION,4]);cache[key]=name
    frames.append({'index':i,'time':i/8,'path':name,'angles':angles,'shot':shot,'camera':{'eye':[0,0,0]},'sha256':sha(dest)})
    if i%24==0:print(f'Projected {i+1}/240',flush=True)
assert frames[0]['sha256']==frames[-1]['sha256']
manifest.update({'title':'ANGLES / solid silver','status':'revised 30-second audition','frames':frames,'size':[W,H],
 'renderer':manifest['renderer']+'; center-view angular sampling','sourcePanorama':meta,
 'qa':{'allCamerasAtCenter':True,'exactSourceReturn':True},
 'provenance':{'method':'Local Cycles path tracing of solid geometry to a native 16384 by 4096 angular plate, followed by exact center-camera perspective sampling to 1920 by 1080. Fixed world, lighting and viewpoint. No optical interpolation.','providerCalls':0,'apiCostUSD':0}})
(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
video=a.output/'angles-solid-silver-30s.mp4'
subprocess.run(['ffmpeg','-v','error','-framerate','8','-i',str(a.output/'frames/frame-%04d.png'),'-vf','fps=24,setsar=1',
 '-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(video)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
stream=probe['streams'][0]
assert (stream['width'],stream['height'],stream['nb_frames'],stream['r_frame_rate'])==(W,H,'720','24/1')
assert len(probe['streams'])==1 and float(probe['format']['duration'])==30

def decoder(inputs,filter):
    return subprocess.Popen(['ffmpeg','-v','error','-threads','2',*inputs,'-vf',filter,'-f','rawvideo','-pix_fmt','gray','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
ref=decoder(['-framerate','8','-i',str(a.output/'frames/frame-%04d.png')],'fps=24,scale=480:270:flags=area')
enc=decoder(['-i',str(video)],'scale=480:270:flags=area')
psnr=[];errors=[];holds=[];previous=None
for i in range(720):
    r=ref.stdout.read(480*270);e=enc.stdout.read(480*270)
    assert len(r)==len(e)==480*270
    x=np.frombuffer(r,np.uint8).astype(np.float32);y=np.frombuffer(e,np.uint8).astype(np.float32)
    mse=float(np.mean((x-y)**2));psnr.append(10*math.log10(255**2/max(mse,1e-12)));errors.append(float(np.mean(abs(x-y))))
    if i%3 and previous is not None:holds.append(float(np.mean(abs(y-previous))))
    previous=y
assert not ref.stdout.read() and not enc.stdout.read()
for process in [ref,enc]:
    process.wait();assert process.returncode==0,process.stderr.read().decode()
validation={'passed':min(psnr)>35 and max(holds)<1,'duration':30,'dimensions':[W,H],'decodedFrames':720,'poseSlots':240,
 'comparisonResolution':[480,270],'minimumFramePSNR':min(psnr),'maximumFrameMAE':max(errors),'maximumHoldMAE':max(holds),
 'allSourceFramesGrayscale':all(Image.open(a.output/f['path']).mode=='L' for f in frames),
 'allCamerasAtCenter':True,'sourceOpeningAndClosingIdentical':frames[0]['sha256']==frames[-1]['sha256'],
 'sourceGeometry':meta['meshChecks'],'materialsOpaque':True,'neutralMaterialsAndLights':True,'videoSHA256':sha(video),
 'limits':['This is rendered CG, not a photograph or calibrated instrument capture.','Full video decoding; encoding comparisons use 480 by 270 proxies.','Depth of field is disabled; all surfaces are held in focus.']}
validation['passed']=validation['passed'] and validation['allSourceFramesGrayscale']
(a.output/'qa/validation.json').write_text(json.dumps(validation,indent=2)+'\n')

fonts=[Path('/System/Library/Fonts/Helvetica.ttc'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
fontpath=next((x for x in fonts if x.exists()),None)
font=lambda size:ImageFont.truetype(str(fontpath),size) if fontpath else ImageFont.load_default()
board=Image.new('RGB',(1440,1432),'#101010');draw=ImageDraw.Draw(board)
draw.text((20,18),'ANGLES / SOLID SILVER',font=font(28),fill='#eeeeee')
draw.text((20,56),'Opaque metal. Black. Bright white light.',font=font(20),fill='#bdbdbd')
for i,(t,label) in enumerate([(0,'TURNED SHOULDER'),(6,'GROUND EDGE'),(13.5,'OPPOSED FACES'),(18,'CURVED FLANK'),(24,'FLAT FLANK'),(29.875,'RETURN')]):
    x=(i%2)*720+10;y=(i//2)*440+100
    im=Image.open(a.output/f'frames/frame-{round(t*8):04d}.png').convert('RGB')
    board.paste(im.resize((700,394),Image.Resampling.LANCZOS),(x,y))
    draw.text((x+3,y+402),f'{label} / {t:g}s',font=font(20),fill='#d8d8d8')
board.save(a.output/'contact-sheet.jpg',quality=94)
shutil.copyfile(a.output/'frames/frame-0108.png',a.output/'poster.png')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Angles / Solid silver</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b0b0b;color:#eee;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1220px;margin:auto;padding:42px 24px 72px}h1{font-size:clamp(40px,6vw,74px);letter-spacing:-.05em;line-height:1;margin:12px 0 18px}.label{font-size:12px;letter-spacing:.17em;color:#aaa}p{color:#bbb;max-width:830px}video,img{display:block;width:100%;border:1px solid #333}video{aspect-ratio:16/9;background:black}.buttons{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}button,a{color:#ddd}button,.open{background:#202020;border:1px solid #484848;padding:9px 14px;font:inherit;font-size:13px;border-radius:3px;cursor:pointer;text-decoration:none}button:hover{background:#ddd;color:#111}.head{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:26px}details{margin:30px 0}summary{cursor:pointer;color:#bbb;margin:12px 0}.foot{color:#888;font-size:12px;border-top:1px solid #333;padding-top:16px;margin-top:34px}@media(max-width:650px){main{padding:26px 14px}.head{display:block}.open{display:inline-block;margin-top:16px}}
</style><main><div class="head"><div><div class="label">REVISED AUDITION / 02</div><h1>Solid silver.</h1><div class="label">ANGLES · 30 SECONDS · 16:9 · 1080P · SILENT</div></div><a class="open" href="angles-solid-silver-30s.mp4">Open the film ↗</a></div>
<video id="film" controls playsinline preload="metadata" poster="poster.png"><source src="angles-solid-silver-30s.mp4" type="video/mp4"></video>
<div class="buttons"><button data-time="0">00 / Turned shoulder</button><button data-time="6">06 / Ground edge</button><button data-time="11">11 / Opposed faces</button><button data-time="17">17 / Curved flank</button><button data-time="22">22 / Flat flank</button><button data-time="26">26 / Return</button></div>
<p>Fewer forms. Brighter metal. Real thickness, curved shoulders and machined bevels under white light. Black recesses separate the solid surfaces. The camera rotates from the same fixed center throughout, with eight held poses per second and hard cuts.</p>
<details open><summary>Views from the revised cut</summary><img src="contact-sheet.jpg" alt="Six monochrome close views of solid machined metal"></details>
<details><summary>Production record</summary><p>Local physically based Cycles rendering of closed metal meshes. All materials are opaque; transmission is zero. Lights and metal are neutral. A single surrounding angular render supplies every perspective view, preserving the static world and reflections. No generated video, no provider calls, no 4K upscale. This is rendered CG, not instrument footage.</p><p><a href="qa/validation.json">Verification</a> · <a href="manifest.json">Camera and source record</a> · <a href="source/angles-solid-silver-panorama.blend">Blender scene</a></p></details>
<div class="foot">Creative development and local rendering: OpenAI Codex. Blender Cycles, Python, OpenCV and FFmpeg.<br><a href="https://github.com/TeeKay-FourTwentyOne/video-generator">https://github.com/TeeKay-FourTwentyOne/video-generator</a></div></main>
<script>const film=document.getElementById('film');document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{film.pause();film.currentTime=Number(b.dataset.time)})</script></html>'''
(a.output/'review.html').write_text(html)
print(json.dumps(validation,indent=2),flush=True)
assert validation['passed']
