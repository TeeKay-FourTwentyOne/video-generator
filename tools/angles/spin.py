#!/usr/bin/env python3
"""Fast, distinct fixed-center camera rotations through a full Cycles sphere."""
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

SHOTS = [
    {'start': 0, 'end': 5, 'id': 'equator', 'title': 'Horizontal sweep', 'motion': '120 degrees/second around the vertical axis'},
    {'start': 5, 'end': 10, 'id': 'flip', 'title': 'End over end', 'motion': '144 degrees/second around a horizontal axis'},
    {'start': 10, 'end': 15, 'id': 'diagonal', 'title': 'Diagonal orbit', 'motion': '180 degrees/second around a 45-degree tilted axis'},
    {'start': 15, 'end': 20, 'id': 'reverse', 'title': 'Fast reverse', 'motion': '240 degrees/second in the opposite horizontal direction'},
    {'start': 20, 'end': 25, 'id': 'corkscrew', 'title': 'Corkscrew', 'motion': '180-degree/second yaw, 35-degree pitch oscillation, 120-degree/second roll'},
    {'start': 25, 'end': 30, 'id': 'accelerate', 'title': 'Accelerating tumble', 'motion': '144 to 288 degrees/second around a 75-degree tilted axis'},
]

def basis(yaw, pitch=0, roll=0):
    y, p, r = np.deg2rad([yaw, pitch, roll])
    forward = np.array([math.sin(y)*math.cos(p), math.cos(y)*math.cos(p), math.sin(p)])
    right = np.array([math.cos(y), -math.sin(y), 0])
    up = np.cross(right, forward)
    return np.column_stack((right*math.cos(r)+up*math.sin(r), up*math.cos(r)-right*math.sin(r), forward))

def rotate(frame, axis, angle):
    n = np.array(axis, dtype=float); n /= np.linalg.norm(n)
    x, y, z = n; skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    theta = math.radians(angle)
    matrix = np.eye(3)*math.cos(theta)+(1-math.cos(theta))*np.outer(n, n)+math.sin(theta)*skew
    return matrix@frame

def camera(time):
    segment = min(int(time//5), 5); t = time-segment*5
    if segment == 0: frame = rotate(basis(204, 0, -8), [0, 0, 1], -120*t)
    elif segment == 1:
        start = basis(212); frame = rotate(start, start[:, 0], 144*t)
    elif segment == 2:
        start = basis(212, 0, -30)
        axis = np.array([0, 0, 1])+basis(212)[:, 0]
        frame = rotate(start, axis, -180*t)
    elif segment == 3: frame = rotate(basis(42, -12, 22), [0, 0, 1], 240*t)
    elif segment == 4: frame = basis(200+180*t, 35*math.sin(math.tau*t/2.5), 40+120*t)
    else:
        start = basis(204, 0, -8)
        axis = math.cos(math.radians(75))*np.array([0, 0, 1])+math.sin(math.radians(75))*basis(204)[:, 0]
        frame = rotate(start, axis, -(144*t+14.4*t*t))
    assert np.max(abs(frame.T @ frame - np.eye(3))) < 1e-12
    assert abs(np.linalg.det(frame)+1) < 1e-12
    return frame, SHOTS[segment]

class Projector:
    def __init__(self, plate, width, height, latitude=90):
        self.plate_height, self.plate_width = plate.shape
        self.plate = np.pad(plate, ((4, 4), (0, 0)), mode='edge'); self.latitude = latitude
        py, px = np.indices((height, width), dtype=np.float32)
        focal = width*35/36
        self.x = (px+.5-width/2)/focal; self.y = (height/2-py-.5)/focal

    def render(self, frame):
        r, u, f = frame.T.astype(np.float32)
        direction = f+self.x[..., None]*r+self.y[..., None]*u
        direction /= np.linalg.norm(direction, axis=2, keepdims=True)
        longitude = np.arctan2(direction[:, :, 1], direction[:, :, 0])
        latitude = np.arcsin(np.clip(direction[:, :, 2], -1, 1))
        mx = ((.5-longitude/math.tau)*self.plate_width-.5).astype(np.float32)
        my = ((math.radians(self.latitude)-latitude)/math.radians(2*self.latitude)*self.plate_height-.5).astype(np.float32)
        # Azimuth wraps. Pole samples clamp vertically; a row never wraps to the opposite pole.
        assert my.min() >= -.501 and my.max() <= self.plate_height-.499
        np.clip(my, 0, self.plate_height-1, out=my); my += 4
        sampled = cv2.remap(self.plate, mx, my, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_WRAP)
        return np.clip(np.round(sampled.astype(np.float32)/257), 0, 255).astype(np.uint8)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--size', type=int, default=1080, choices=[270, 540, 1080])
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    for name in ['frames', 'qa', 'recipe']: (a.output/name).mkdir()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    meta = json.loads((a.source/'manifest.json').read_text())
    assert meta['latitudeDegrees'] == [-90, 90] and meta['longitudeDegrees'] == [-180, 180]
    assert meta['materialsOpaque'] and meta['neutralMaterialsAndLights'] and meta['cameraOrigin'] == [0, 0, 0]
    assert sha(a.source/'radiance.png') == meta['sha256']
    plate = cv2.imread(str(a.source/'radiance.png'), cv2.IMREAD_UNCHANGED)
    assert plate.ndim == 2 and plate.dtype == np.uint16
    H = a.size; W = H*16//9; fps = 12
    projector = Projector(plate, W, H)
    shutil.copyfile(__file__, a.output/'recipe/spin.py')
    shutil.copyfile(Path(__file__).with_name('physical-panorama.py'), a.output/'recipe/physical-panorama.py')
    assert np.max(abs(camera(30)[0]-camera(0)[0])) < 1e-12
    frames = []
    for i in range(360):
        time = i/fps; frame, shot = camera(time)
        out = projector.render(frame)
        path = a.output/f'frames/frame-{i:04d}.png'
        cv2.imwrite(str(path), out, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        frames.append({'index': i, 'time': time, 'shot': shot['id'], 'cameraOrigin': [0, 0, 0],
                       'cameraBasis': frame.tolist(), 'path': str(path.relative_to(a.output)), 'sha256': sha(path),
                       'meanLuma': float(out.mean()), 'brightFraction': float(np.mean(out>210)),
                       'darkFraction': float(np.mean(out<24))})
        if i % 60 == 0: print(f'{shot["title"]}: {i}/360', flush=True)
    shot_stats = []
    for shot in SHOTS:
        group = [f for f in frames if f['shot'] == shot['id']]
        levels = np.array([f['meanLuma'] for f in group])
        # Count substantial crossings of two thresholds, with hysteresis.
        state = None; transitions = 0
        for level in levels:
            next_state = 'dark' if level<35 else 'light' if level>100 else state
            if state is not None and next_state != state: transitions += 1
            state = next_state
        run = longest = 0
        for level in levels:
            run = run+1 if level<12 else 0; longest = max(run, longest)
        shot_stats.append({**shot, 'meanLumaRange': [float(levels.min()), float(levels.max())],
                           'darkLightTransitions': transitions, 'longestNearBlackSeconds': longest/fps})
    manifest = {'title': 'ANGLES / rotation', 'duration': 30, 'size': [W, H], 'poseFPS': fps, 'outputFPS': 24,
                'shots': shot_stats, 'frames': frames, 'source': '../source', 'sourcePanorama': meta,
                'constraints': {'cameraOrigin': [0, 0, 0], 'opaque': True, 'palette': 'black and neutral metal', 'upscale': False},
                'providerCalls': 0, 'apiCostUSD': 0}
    (a.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    video = a.output/'angles-rotation-30s.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-framerate', str(fps), '-i', str(a.output/'frames/frame-%04d.png'),
                    '-vf', 'fps=24,setsar=1', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
                    '-an', '-movflags', '+faststart', str(video)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
    stream = probe['streams'][0]
    assert (stream['width'], stream['height'], stream['nb_frames'], stream['r_frame_rate']) == (W, H, '720', '24/1')
    assert float(probe['format']['duration']) == 30 and len(probe['streams']) == 1
    def decoder(args, filters, pixfmt):
        return subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '2', *args, '-vf', filters,
                                 '-f', 'rawvideo', '-pix_fmt', pixfmt, '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    reference = decoder(['-framerate', str(fps), '-i', str(a.output/'frames/frame-%04d.png')], 'fps=24,scale=480:270:flags=area', 'gray')
    encoded = decoder(['-i', str(video)], 'scale=480:270:flags=area', 'yuv420p')
    psnr = []; holds = []; previous = None
    for i in range(720):
        ref = reference.stdout.read(480*270); enc = encoded.stdout.read(480*270*3//2)
        assert len(ref) == 480*270 and len(enc) == 480*270*3//2
        chroma = np.frombuffer(enc[480*270:], np.uint8); assert np.all(chroma == 128)
        x = np.frombuffer(ref, np.uint8).astype(float)
        y = np.clip(np.round((np.frombuffer(enc[:480*270], np.uint8).astype(float)-16)*255/219), 0, 255)
        mse = float(np.mean((x-y)**2)); psnr.append(10*math.log10(255**2/max(mse, 1e-12)))
        if i % 2: holds.append(float(np.mean(abs(y-previous))))
        previous = y
    for process in [reference, encoded]:
        assert not process.stdout.read(); process.wait(); assert process.returncode == 0, process.stderr.read().decode()
    assert min(psnr)>35 and max(holds)<1
    validation = {'passed': True, 'decodedFrames': 720, 'poseSlots': 360, 'duration': 30, 'dimensions': [W, H],
                  'allCamerasAtCenter': True, 'allCameraBasesOrthonormal': True, 'fullSphereCoverage': True,
                  'minimumFramePSNR': min(psnr), 'maximumHoldMAE': max(holds), 'allChromaNeutral': True,
                  'videoSHA256': sha(video), 'shotStats': shot_stats, 'providerCalls': 0, 'apiCostUSD': 0,
                  'limits': ['Rendered CG, not captured metrology data.', 'Encoding comparisons use 480 by 270 proxies.']}
    (a.output/'qa/validation.json').write_text(json.dumps(validation, indent=2)+'\n')
    font_path = Path('/System/Library/Fonts/Helvetica.ttc')
    font = lambda size: ImageFont.truetype(str(font_path), size) if font_path.exists() else ImageFont.load_default()
    board = Image.new('RGB', (1440, 1390), '#101010'); draw = ImageDraw.Draw(board)
    draw.text((24, 20), 'ANGLES / ROTATION', font=font(30), fill='white')
    draw.text((24, 63), 'One fixed center. Six distinct motions. Light and dark revealed by turning.', font=font(19), fill='#aaa')
    for index, shot in enumerate(SHOTS):
        group = [f for f in frames if f['shot'] == shot['id']]
        selected = sorted(group, key=lambda f: f['meanLuma'])[len(group)*2//3]
        x = index%2*720+10; y = index//2*423+110
        im = Image.open(a.output/selected['path']).convert('RGB').resize((700, 394), Image.Resampling.LANCZOS)
        board.paste(im, (x, y)); draw.text((x, y+398), f'{shot["start"]:02d} / {shot["title"].upper()}', font=font(16), fill='#ddd')
    board.save(a.output/'contact-sheet.jpg', quality=94)
    shutil.copyfile(a.output/'frames/frame-0000.png', a.output/'poster.png')
    buttons = ''.join(f'<button data-time="{s["start"]}">{s["start"]:02d} / {s["title"]}</button>' for s in SHOTS)
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Angles / Rotation</title><style>
*{box-sizing:border-box}body{background:#090909;color:#eee;margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1240px;margin:auto;padding:38px 24px 64px}h1{font-size:clamp(42px,6vw,74px);letter-spacing:-.05em;line-height:1;margin:16px 0 20px}.label{color:#aaa;font-size:12px;letter-spacing:.16em}p{color:#aaa;max-width:940px}video,img{display:block;width:100%;border:1px solid #333}video{aspect-ratio:16/9;background:black}a{color:#ddd}.buttons{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}button{background:#1a1a1a;color:#ddd;border:1px solid #555;font:inherit;font-size:12px;padding:9px 12px;cursor:pointer}button:hover,button.active{background:#eee;color:#111}#beat{min-height:26px;color:#ddd;font-size:14px}details{margin-top:28px}summary{cursor:pointer;margin-bottom:12px}.foot{font-size:12px;color:#888;margin-top:34px;border-top:1px solid #333;padding-top:18px}@media(max-width:640px){main{padding:24px 14px}}</style>
<main><div class="label">ANGLES / NEW MOTION STUDY</div><h1>Inside the sphere.</h1><p>Rapid turns carry us through bright silver and black recesses. Each hard cut changes the axis, direction or pace. Our viewpoint stays at the center throughout.</p>
<video id="film" controls playsinline loop preload="metadata" poster="poster.png" src="angles-rotation-30s.mp4"></video><div class="buttons">BUTTONS</div><div id="beat">00–05 / Horizontal sweep</div><p class="label">30 SECONDS · 16:9 · 1080P · SILENT</p><p><a href="angles-rotation-30s.mp4">Open the film ↗</a></p>
<details><summary>Six passages</summary><img src="contact-sheet.jpg" alt="Views from the six rotation segments"></details><details><summary>Production record</summary><p>The original solid-silver scene and its fixed white lights are preserved. Full spherical coverage supports horizontal, vertical and oblique rotations. Twelve distinct poses per second are held for two frames each in the 24 fps film. No zoom, camera translation, animated lighting or exposure changes.</p><p>Local Blender Cycles render and perspective projection. Black and opaque neutral metal only. No paid generation or 4K upscale. <a href="qa/validation.json">Verification</a> · <a href="manifest.json">Camera record</a></p></details><div class="foot">Creative development and local rendering: OpenAI Codex. Blender Cycles, Python, OpenCV and FFmpeg.<br><a href="https://github.com/TeeKay-FourTwentyOne/video-generator">https://github.com/TeeKay-FourTwentyOne/video-generator</a></div></main>
<script>const film=document.getElementById('film');document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{film.currentTime=Number(b.dataset.time);film.play().catch(()=>{});});film.ontimeupdate=()=>{const index=Math.min(5,Math.floor(film.currentTime/5));document.querySelectorAll('[data-time]').forEach((b,i)=>{b.classList.toggle('active',i===index);if(i===index)document.getElementById('beat').textContent=b.textContent;});};window.sceneLab={};</script></html>'''
    (a.output/'review.html').write_text(html.replace('BUTTONS', buttons))
    print(json.dumps({'validation': {k: v for k, v in validation.items() if k!='shotStats'}, 'shots': shot_stats}, indent=2), flush=True)

if __name__ == '__main__': main()
