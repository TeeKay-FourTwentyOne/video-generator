#!/usr/bin/env python3
"""Build the local audition page and compare all decoded frames to the recipe."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser()
parser.add_argument('run', type=Path)
parser.add_argument('--materials', type=Path, required=True)
args = parser.parse_args()
run = args.run
manifest = json.loads((run/'manifest.json').read_text())
qa = run/'qa'
review = run/'review'
review.mkdir(exist_ok=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

source_hashes = all(digest(run/f['path']) == f['sha256'] for f in manifest['frames'])
source_return = manifest['frames'][0]['sha256'] == manifest['frames'][-1]['sha256']
video = run/'angles-audition.mp4'
probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
stream = probe['streams'][0]
assert (stream['width'],stream['height'],stream['r_frame_rate'],stream['nb_frames']) == (1920,1080,'24/1','720')
assert float(probe['format']['duration']) == 30
assert len(probe['streams']) == 1

def decode(inputs, vf):
    return subprocess.Popen(['ffmpeg','-v','error','-threads','2',*inputs,'-vf',vf,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)

reference = decode(['-framerate','8','-i',str(run/'frames/frame-%04d.png')],'fps=24,scale=480:270:flags=area')
encoded = decode(['-i',str(video)],'scale=480:270:flags=area')
errors=[]
hold_errors=[]
first=None
previous=None
count=0
for index in range(720):
    a=reference.stdout.read(480*270*3)
    b=encoded.stdout.read(480*270*3)
    if len(a)!=480*270*3 or len(b)!=480*270*3:
        raise RuntimeError(f'Incomplete frame at {index}')
    x=np.frombuffer(a,np.uint8).astype(np.float32)
    y=np.frombuffer(b,np.uint8).astype(np.float32)
    mse=float(np.mean((x-y)**2))
    errors.append({'frame':index,'mae':float(np.mean(abs(x-y))),'psnr':10*math.log10(255**2/max(mse,1e-12))})
    if index%3 and previous is not None:
        hold_errors.append(float(np.mean(abs(previous-y))))
    if first is None:first=y.copy()
    previous=y
    count+=1
assert reference.stdout.read()==b'' and encoded.stdout.read()==b''
for process in [reference,encoded]:
    process.wait()
    if process.returncode:raise RuntimeError(process.stderr.read().decode())

result={
 'passed':True,'sourcePNGHashesMatch':source_hashes,
 'all720FramesDecodedAndCompared':count==720,
 'comparisonResolution':[480,270],
 'minimumFramePSNR':min(e['psnr'] for e in errors),
 'maximumFrameMeanAbsoluteError':max(e['mae'] for e in errors),
 'maximumWithinHoldMeanAbsoluteError':max(hold_errors),
 'sourceOpeningAndReturnPNGIdentical':source_return,
 'decodedOpeningAndReturnMeanAbsoluteError':float(np.mean(abs(first-previous))),
 'cameraAlwaysAtCenter':manifest['qa']['allCamerasAtCenter'],
 'dimensions':[stream['width'],stream['height']],
 'durationSeconds':30,'frames':720,'frameRate':24,'poseRate':8,'audio':'silent',
 'cutFrameIndices':[round(s['start']*24) for s in manifest['shots'][1:]],
 'videoSHA256':digest(video),
 'limits':['Encoding comparisons use 480 by 270 proxies after full video decoding.',
           'Analytic reflection fill is an artistic approximation, not calibrated optics.',
           'Fine highlight edges retain some aliasing; this is a first visual audition.']}
result['passed']=all([source_hashes,source_return,result['cameraAlwaysAtCenter'],count==720,
 result['minimumFramePSNR']>35,result['maximumWithinHoldMeanAbsoluteError']<1])
(qa/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
(qa/'per-frame-comparison.json').write_text(json.dumps(errors,indent=2)+'\n')

font_paths=[Path('/System/Library/Fonts/Helvetica.ttc'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
font_path=next((p for p in font_paths if p.exists()),None)
font=lambda size:ImageFont.truetype(str(font_path),size) if font_path else ImageFont.load_default()
board=Image.new('RGB',(1440,1448),'#111417')
draw=ImageDraw.Draw(board)
draw.text((20,20),'ANGLES / OPPOSED SURFACES',font=font(28),fill='#f2f3f2')
draw.text((20,60),'30 seconds · fixed center · chrome, curvature and cuts',font=font(20),fill='#abb6bd')
for i,(time,label) in enumerate([(0,'EDGE'),(6,'REVERSE'),(13,'FLANK'),(19,'UNDERCUT'),(21,'CROWN'),(29.875,'RETURN')]):
    image=Image.open(run/f'frames/frame-{round(time*8):04d}.png')
    x=(i%2)*720+10;y=(i//2)*442+110
    board.paste(image.resize((700,394),Image.Resampling.LANCZOS),(x,y))
    draw.text((x+4,y+401),f'{label} / {time:g}s',font=font(22),fill='#d8e0e5')
board.save(review/'contact-sheet.jpg',quality=93)
for source,name in [(0,'precision'),(12,'sphere'),(13,'mirror'),(14,'warm'),(15,'depth'),(17,'clay')]:
    shutil.copyfile(args.materials/f'frames/frame-{source:04d}.png',review/f'{name}.png')

html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ANGLES — First audition</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0d1012;color:#e6e9e9;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1220px;margin:auto;padding:48px 24px 80px}header{display:flex;justify-content:space-between;align-items:end;gap:24px;margin-bottom:26px}h1{font-size:clamp(38px,6vw,76px);letter-spacing:-.05em;line-height:1;margin:8px 0 14px}h2{font-size:24px;font-weight:500;margin:42px 0 8px}.eyebrow{letter-spacing:.18em;font-size:12px;color:#a1b6c3}p{max-width:780px;color:#b6c2c9}video{width:100%;display:block;background:#000;aspect-ratio:16/9;border:1px solid #303b43}.meta{font-size:13px;color:#9daab2}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}button,a.download{background:#1b242a;color:#dfe7ec;border:1px solid #394853;border-radius:4px;padding:9px 14px;font:inherit;font-size:13px;cursor:pointer;text-decoration:none}button:hover,button.active{background:#dee9ef;color:#13212b}a{color:#adcfe5}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0}img{max-width:100%;display:block}figcaption{margin:9px 0 20px;color:#acbac3;font-size:14px}.decision{border-left:2px solid #9ec3d8;padding-left:22px;margin:42px 0}.decision p{font-size:21px;max-width:850px;color:#e3e9ec}details{margin:24px 0;color:#98aab5}summary{cursor:pointer}.foot{font-size:12px;color:#7c8d98;border-top:1px solid #29343c;padding-top:18px;margin-top:42px}@media(max-width:700px){header{display:block}.grid{grid-template-columns:1fr}main{padding:28px 14px}h1{font-size:52px}}
</style></head><body><main>
<header><div><div class="eyebrow">FIRST VISUAL AUDITION / 01</div><h1>Angles.</h1><div class="meta">30 seconds · 16:9 · native 1080p · silent</div></div><a class="download" href="angles-audition.mp4">Open the film ↗</a></header>
<video id="film" controls playsinline preload="metadata" poster="poster.png"><source src="angles-audition.mp4" type="video/mp4"></video>
<div class="controls" aria-label="Jump to passage"><button data-time="0">00 / Edge</button><button data-time="6">06 / Reverse</button><button data-time="10.5">10.5 / Flank</button><button data-time="16.5">16.5 / Undercut</button><button data-time="21">21 / Crown</button><button data-time="25.5">25.5 / Return</button></div>
<p>One fixed observer, enclosed by an imperfect sphere. Chrome circles meet planar cuts. Light becomes an edge; the reverse angle opens a dark cavity. Eight held poses per second give each turn a deliberate, stepped rhythm.</p>
<div class="decision"><div class="eyebrow">THE ARTISTIC DECISION</div><p>Keep the precision-made cavity, or make the metal stranger—burrs, chips and fractured ridges?</p><p style="font-size:16px;color:#b6c2c9">My choice for this pass is precision. The clear circles give the hard cuts something to oppose. The next step would be to disturb that order selectively.</p></div>
<h2>Surface audition</h2><p>Same geometry, same angle. Select a finish to compare. The film uses the first finish.</p>
<div class="controls" id="looks"><button class="active" data-image="precision" data-label="01 / Precision chrome — selected for the film">Precision chrome</button><button data-image="mirror" data-label="02 / Mirror-dense — more reflection, less separation">Mirror-dense</button><button data-image="warm" data-label="03 / Warm metal — a gentler, less surgical character">Warm metal</button></div>
<figure><img id="look" src="review/precision.png" alt="Chrome surfaces from the fixed center"><figcaption id="look-label">01 / Precision chrome — selected for the film</figcaption></figure>
<h2>The enclosure</h2><div class="grid"><figure><img src="review/sphere.png" alt="Perfect sphere control"><figcaption>Perfect sphere / control. Without the relief, there is little for the eye to locate.</figcaption></figure><figure><img src="review/clay.png" alt="Unreflective geometry view"><figcaption>Irregular cavity / plain surface. This reveals the geometry beneath the reflections.</figcaption></figure></div>
<details><summary>Six views from the cut</summary><img src="review/contact-sheet.jpg" alt="Six views across the 30-second audition"></details>
<details><summary>Production notes</summary><p>Local procedural 3D rendering; fixed geometry and fixed light panels. The camera stays at [0, 0, 0]. Three specular bounces with an analytic reflection fill approximate the chrome. This is an artistic surface study, not captured or calibrated metrology data. No image or video generation provider was called. No 4K upscale. Fine reflected edges retain some aliasing.</p><p><a href="qa/validation.json">Verification record</a> · <a href="manifest.json">Scene and camera record</a></p></details>
<div class="foot">Creative development and local rendering: OpenAI Codex. WebGL 2, FFmpeg, Python.<br><a href="https://github.com/TeeKay-FourTwentyOne/video-generator">https://github.com/TeeKay-FourTwentyOne/video-generator</a></div>
</main><script>
const film=document.getElementById('film');document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{film.currentTime=Number(b.dataset.time);film.pause()});
document.querySelectorAll('[data-image]').forEach(b=>b.onclick=()=>{document.getElementById('look').src='review/'+b.dataset.image+'.png';document.getElementById('look-label').textContent=b.dataset.label;document.querySelectorAll('[data-image]').forEach(x=>x.classList.toggle('active',x===b))});
</script></body></html>'''
(run/'review.html').write_text(html)
print(json.dumps(result,indent=2))
if not result['passed']:raise SystemExit(1)
