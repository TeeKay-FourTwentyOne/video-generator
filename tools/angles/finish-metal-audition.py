#!/usr/bin/env python3
"""Finish matched 11–14 second lighting auditions without altering the source cut."""
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

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--plates', type=Path, required=True)
p.add_argument('--reference-stills', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
(a.output/'qa').mkdir()
shutil.copyfile(__file__, a.output/'finish-metal-audition.py')
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
source = json.loads((a.source/'manifest.json').read_text())
poses = source['frames'][88:112]
assert len(poses) == 24 and poses[0]['time'] == 11 and poses[-1]['time'] == 13.875
original_sha = sha(a.source/'angles-solid-silver-30s.mp4')
W, H = 1920, 1080
py, px = np.indices((H, W), dtype=np.float32)
focal = W*35/36
screen_x, screen_y = (px+.5-W/2)/focal, (H/2-py-.5)/focal

def project(plate, meta, angles):
    yaw, pitch, roll = np.deg2rad(angles)
    forward = np.array([math.sin(yaw)*math.cos(pitch), math.cos(yaw)*math.cos(pitch), math.sin(pitch)], dtype=np.float32)
    right = np.cross(forward, [0, 0, 1]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    rr = right*math.cos(roll)+up*math.sin(roll)
    uu = up*math.cos(roll)-right*math.sin(roll)
    direction = forward+screen_x[..., None]*rr+screen_y[..., None]*uu
    direction /= np.linalg.norm(direction, axis=2, keepdims=True)
    longitude = np.rad2deg(np.arctan2(direction[:, :, 1], direction[:, :, 0]))
    latitude = np.rad2deg(np.arcsin(direction[:, :, 2]))
    lo, hi = meta['longitudeDegrees']; bottom, top = meta['latitudeDegrees']
    mx = ((hi-longitude)/(hi-lo)*plate.shape[1]-.5).astype(np.float32)
    my = ((top-latitude)/(top-bottom)*plate.shape[0]-.5).astype(np.float32)
    assert mx.min() >= 4 and mx.max() < plate.shape[1]-4
    assert my.min() >= 4 and my.max() < plate.shape[0]-4
    sampled = cv2.remap(plate, mx, my, cv2.INTER_LANCZOS4)
    return np.clip(np.round(sampled.astype(np.float32)/257), 0, 255).astype(np.uint8)

def decode(arguments, pixel_format='gray', filters='scale=480:270:flags=area'):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '2', *arguments,
                             '-vf', filters, '-f', 'rawvideo', '-pix_fmt', pixel_format, '-'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

records = {}
for variant in ['current', 'polished', 'shaped']:
    folder = a.output/variant
    (folder/'frames').mkdir(parents=True)
    meta = None
    if variant != 'current':
        plate_dir = a.plates/f'{variant}-plate'
        meta = json.loads((plate_dir/'manifest.json').read_text())
        assert meta['geometryUnchanged'] and meta['cameraOrigin'] == [0, 0, 0]
        assert all(m['opaque'] and m['neutral'] and m['metallic'] == 1 for m in meta['materials'])
        assert sha(plate_dir/'radiance.png') == meta['sha256']
        plate = cv2.imread(str(plate_dir/'radiance.png'), cv2.IMREAD_UNCHANGED)
        assert plate.dtype == np.uint16 and plate.ndim == 2
    frames = []
    for i, pose in enumerate(poses):
        target = folder/f'frames/frame-{i:04d}.png'
        if variant == 'current':
            shutil.copyfile(a.source/pose['path'], target)
            assert sha(target) == pose['sha256']
        else:
            cv2.imwrite(str(target), project(plate, meta, pose['angles']), [cv2.IMWRITE_PNG_COMPRESSION, 4])
        frames.append({'index': i, 'sourceTime': pose['time'], 'angles': pose['angles'], 'sha256': sha(target)})
    shutil.copyfile(folder/'frames/frame-0016.png', a.output/f'{variant}-13s.png')
    video = a.output/f'{variant}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-framerate', '8', '-i', str(folder/'frames/frame-%04d.png'),
                    '-vf', 'fps=24,setsar=1', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
                    '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', str(video)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
    stream = probe['streams'][0]
    assert (stream['width'], stream['height'], stream['nb_frames'], stream['r_frame_rate']) == (W, H, '72', '24/1')
    assert float(probe['format']['duration']) == 3 and len(probe['streams']) == 1
    ref = decode(['-framerate', '8', '-i', str(folder/'frames/frame-%04d.png')], filters='fps=24,scale=480:270:flags=area')
    enc = decode(['-i', str(video)], pixel_format='yuv420p')
    psnr, holds, previous = [], [], None
    for i in range(72):
        r, e = ref.stdout.read(480*270), enc.stdout.read(480*270*3//2)
        assert len(r) == 480*270 and len(e) == 480*270*3//2
        assert all(x == 128 for x in e[480*270:])
        x = np.frombuffer(r, np.uint8).astype(np.float32)
        # Gray decoding expands limited-range luma, matching the reference conversion.
        y = (np.frombuffer(e[:480*270], np.uint8).astype(np.float32)-16)*255/219
        y = np.clip(np.round(y), 0, 255)
        mse = float(np.mean((x-y)**2)); psnr.append(10*math.log10(255**2/max(mse, 1e-12)))
        if i % 3 and previous is not None: holds.append(float(np.mean(abs(y-previous))))
        previous = y
    for process in [ref, enc]:
        assert not process.stdout.read()
        process.wait(); assert process.returncode == 0, process.stderr.read().decode()
    assert min(psnr) > 35 and max(holds) < 1
    direct_psnr = None
    if variant != 'current':
        still_folder = 'polished-still' if variant == 'polished' else 'shaped-still-v2'
        direct = cv2.imread(str(a.reference_stills/still_folder/'at-13s.png'), 0).astype(np.float32)
        projected = cv2.imread(str(a.output/f'{variant}-13s.png'), 0).astype(np.float32)
        direct_psnr = 10*math.log10(255**2/max(float(np.mean((direct-projected)**2)), 1e-12))
        assert direct_psnr > 35, f'Direct perspective and angular render differ: {variant}, {direct_psnr:.2f} dB'
    records[variant] = {'frames': frames, 'materialAndLighting': meta, 'videoSHA256': sha(video),
                        'decodedFrames': 72, 'duration': 3, 'dimensions': [W, H], 'minimumFramePSNR': min(psnr),
                        'maximumHoldMAE': max(holds), 'allEncodedChromaNeutral': True, 'directPerspectivePSNR': direct_psnr}
    print(f'{variant}: 72 frames checked, minimum PSNR {min(psnr):.2f}', flush=True)

assert records['polished']['materialAndLighting']['geometryHash'] == records['shaped']['materialAndLighting']['geometryHash']
assert sha(a.source/'angles-solid-silver-30s.mp4') == original_sha
validation = {'passed': True, 'originalVideoUnchanged': True, 'originalVideoSHA256': original_sha,
              'allVariantsSameGeometryAndCamera': True, 'palette': 'black and neutral opaque metal',
              'providerCalls': 0, 'apiCostUSD': 0, 'variants': records}
(a.output/'qa/validation.json').write_text(json.dumps(validation, indent=2)+'\n')

font_path = Path('/System/Library/Fonts/Helvetica.ttc')
font = lambda size: ImageFont.truetype(str(font_path), size) if font_path.exists() else ImageFont.load_default()
board = Image.new('RGB', (1200, 2260), '#101010'); draw = ImageDraw.Draw(board)
draw.text((24, 20), 'ANGLES / LIGHT ON METAL', font=font(30), fill='white')
draw.text((24, 62), 'Same geometry. Same frame at 13 seconds.', font=font(19), fill='#aaa')
for i, (variant, title) in enumerate([('current', 'CURRENT'), ('polished', 'A / CLEAN POLISH'), ('shaped', 'B / SHAPED CHROME')]):
    im = Image.open(a.output/f'{variant}-13s.png').convert('RGB').resize((1200, 675), Image.Resampling.LANCZOS)
    board.paste(im, (0, 140+i*715))
    draw.text((24, 110+i*715), title, font=font(18), fill='#ddd')
board.save(a.output/'comparison.jpg', quality=95)

html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Angles / Light on metal</title><style>
*{box-sizing:border-box}body{margin:0;background:#090909;color:#eee;font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1240px;margin:auto;padding:38px 24px 60px}h1{font-size:clamp(38px,5.5vw,68px);letter-spacing:-.05em;line-height:1;margin:14px 0 20px}.eyebrow{font-size:12px;letter-spacing:.14em;color:#aaa}p{color:#aaa;max-width:890px}video{display:block;width:100%;aspect-ratio:16/9;background:black;border:1px solid #333}.switch{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 8px}button,a{color:#ddd}button{font:inherit;font-size:14px;border:1px solid #555;background:#191919;padding:10px 16px;cursor:pointer}button[aria-pressed=true]{background:#eee;color:#111}button:focus-visible,input:focus-visible{outline:2px solid white;outline-offset:4px}#description{min-height:48px}.links{font-size:13px;display:flex;gap:24px;flex-wrap:wrap}.still{position:relative;aspect-ratio:16/9;background:black;margin-top:20px}.still img{display:block;position:absolute;inset:0;width:100%;height:100%}#enhanced{clip-path:inset(0 0 0 50%)}#divider{position:absolute;top:0;bottom:0;left:50%;border-left:1px solid white}.tags{display:flex;justify-content:space-between;font-size:12px;color:#aaa;margin:8px 0}input{width:100%;accent-color:#ddd}.foot{border-top:1px solid #333;margin-top:34px;padding-top:20px;font-size:12px;color:#888}details{margin-top:28px}summary{cursor:pointer}#status{font-size:12px;color:#aaa}@media(max-width:640px){main{padding:24px 14px}button{padding:8px 10px;font-size:12px}}
</style><main><div class="eyebrow">ANGLES / MATERIAL & LIGHT AUDITION</div><h1>Light on metal.</h1><p>Your 11–14 second passage, with two approaches to stronger metallic reflections. The same shapes, framing and held motion in every version.</p>
<video id="film" controls playsinline loop preload="auto" poster="shaped-13s.png" src="shaped.mp4"></video>
<div class="switch" role="group" aria-label="Choose lighting version"><button data-variant="current" aria-pressed="false">Current</button><button data-variant="polished" aria-pressed="false">A / Clean polish</button><button data-variant="shaped" aria-pressed="true">B / Shaped chrome</button></div>
<p id="description">B adds a narrow white strip reflected across the darker face. The sharper finish makes bright reflections and deep black sit closer together.</p><div id="status">3 seconds · 16:9 · 1080p · silent · loops</div>
<p class="links"><a id="download" href="shaped.mp4">Open selected clip ↗</a><a href="../../solid-silver-v2/angles-solid-silver-30s.mp4">Original 30-second film ↗</a></p>
<details open><summary>Compare the frame at 13 seconds</summary><div class="still"><img src="current-13s.png" alt="Current metal lighting at 13 seconds"><img id="enhanced" src="shaped-13s.png" alt="Shaped chrome lighting at the same frame"><span id="divider"></span></div><div class="tags"><span>CURRENT</span><span>B / SHAPED CHROME</span></div><input id="wipe" type="range" min="0" max="100" value="50" aria-label="Reveal current versus shaped chrome"></details>
<details><summary>What changed</summary><p>A uses smoother silver and tighter machining detail to sharpen the existing reflections. B also narrows the reverse softbox and adds one physical white strip light. All surfaces remain solid opaque metal. No bloom, glow or colored light was added. The camera stays at the center.</p><p>Local Blender Cycles renders. No paid generation or 4K upscale. The original 30-second film is preserved. <a href="qa/validation.json">Verification record</a>.</p></details>
<div class="foot">Creative development and local rendering: OpenAI Codex. Blender Cycles, Python, OpenCV and FFmpeg.<br><a href="https://github.com/TeeKay-FourTwentyOne/video-generator">https://github.com/TeeKay-FourTwentyOne/video-generator</a></div></main><script>
const film=document.getElementById('film'),descriptions={current:'The original finish and lighting, taken directly from the 30-second cut.',polished:'A sharpens the existing reflections with smoother silver and more restrained surface texture.',shaped:'B adds a narrow white strip reflected across the darker face. The sharper finish makes bright reflections and deep black sit closer together.'};
let selected='shaped',revision=0;
document.querySelectorAll('[data-variant]').forEach(button=>button.onclick=()=>{const variant=button.dataset.variant;if(variant===selected)return;const time=film.currentTime,playing=!film.paused,token=++revision;selected=variant;film.pause();film.onloadedmetadata=()=>{if(token!==revision)return;film.currentTime=Math.min(time,Math.max(0,film.duration-.001));if(playing)film.play().catch(()=>{});};film.poster=variant+'-13s.png';film.src=variant+'.mp4';document.getElementById('download').href=variant+'.mp4';document.getElementById('description').textContent=descriptions[variant];document.querySelectorAll('[data-variant]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));});
document.getElementById('wipe').oninput=event=>{const x=event.target.value;document.getElementById('enhanced').style.clipPath=`inset(0 0 0 ${x}%)`;document.getElementById('divider').style.left=x+'%';};
window.sceneLab={};
</script></html>'''
(a.output/'review.html').write_text(html)
print(f'Review ready: {a.output}/review.html', flush=True)
