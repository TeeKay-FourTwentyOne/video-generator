#!/usr/bin/env python3
"""A single fixed-axis rotation, exponentially accelerated over thirty seconds."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from spin import basis, rotate, Projector

DURATION, FPS = 30, 60
START_RPS = 1/60
START_BASIS = basis(-17, 0, -8)

def motion(t, end_rps=24):
    k = math.log(end_rps/START_RPS)/DURATION
    speed = START_RPS*math.exp(k*t)
    turns = START_RPS*math.expm1(k*t)/k
    return turns*360, speed

class YawProjector:
    """Cache latitude and initial longitude; only world-Z rotation is permitted."""
    def __init__(self, plate, width, height):
        self.height, self.width = plate.shape
        self.plate = np.pad(plate, ((4, 4), (0, 0)), mode='edge')
        py, px = np.indices((height, width), dtype=np.float32)
        focal = width*35/36
        x, y = (px+.5-width/2)/focal, (height/2-py-.5)/focal
        right, up, forward = START_BASIS.T
        d = forward+x[..., None]*right+y[..., None]*up
        d /= np.linalg.norm(d, axis=2, keepdims=True)
        self.mx = ((.5-np.arctan2(d[:, :, 1], d[:, :, 0])/math.tau)*self.width-.5).astype(np.float32)
        self.my = ((.5-np.arcsin(d[:, :, 2])/math.pi)*self.height-.5+4).astype(np.float32)
        assert self.my.min()>4 and self.my.max()<self.height+3

    def render(self, phase):
        mx = np.remainder(self.mx+(phase%360)/360*self.width, self.width).astype(np.float32)
        out = cv2.remap(self.plate, mx, self.my, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_WRAP)
        return np.clip(np.round(out.astype(np.float32)/257), 0, 255).astype(np.uint8)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--size', type=int, choices=[270, 540, 1080], default=1080)
    p.add_argument('--end-rps', type=float, default=24)
    a = p.parse_args()
    assert START_RPS < a.end_rps <= 24
    a.output.mkdir(parents=True, exist_ok=False)
    for name in ['reference', 'stills', 'qa', 'recipe']: (a.output/name).mkdir()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    source = json.loads((a.source/'manifest.json').read_text())
    assert source['cameraOrigin']==[0, 0, 0] and source['materialsOpaque'] and source['neutralMaterialsAndLights']
    assert source['latitudeDegrees']==[-90, 90] and source['longitudeDegrees']==[-180, 180]
    assert sha(a.source/'radiance.png')==source['sha256']
    for name in ['accelerate.py', 'spin.py']: shutil.copyfile(Path(__file__).with_name(name), a.output/'recipe'/name)
    plate = cv2.imread(str(a.source/'radiance.png'), cv2.IMREAD_UNCHANGED)
    assert plate.ndim==2 and plate.dtype==np.uint16
    W, H = a.size*16//9, a.size
    projector = YawProjector(plate, W, H)
    # Cross-check the cached yaw mapping against a general 3-D camera rotation.
    small = YawProjector(plate, 480, 270); general = Projector(plate, 480, 270)
    comparisons = []
    for phase in [0, 39, 179, 300, 720, 32165]:
        x = small.render(phase).astype(float)
        frame = rotate(START_BASIS, [0, 0, 1], -phase)
        assert np.max(abs(frame.T @ frame - np.eye(3))) < 1e-12
        y = general.render(frame).astype(float)
        mse = float(np.mean((x-y)**2)); psnr = 10*math.log10(255**2/max(mse, 1e-12))
        assert psnr>55
        comparisons.append({'phaseDegrees': phase, 'PSNR': psnr})
    assert np.array_equal(small.render(0), small.render(360))
    del small, general
    video = a.output/'angles-acceleration-30s.mp4'
    encoder = subprocess.Popen(['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pixel_format', 'gray',
        '-video_size', f'{W}x{H}', '-framerate', str(FPS), '-i', '-', '-vf', 'setsar=1',
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-an',
        '-movflags', '+faststart', str(video)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    frames = []; still_indices = {0, 240, 480, 720, 960, 1200, 1440, 1560, 1620, 1680, 1740, 1799}
    try:
        for i in range(DURATION*FPS):
            t = i/FPS; phase, speed = motion(t, a.end_rps)
            frame = projector.render(phase)
            raw = frame.tobytes(); encoder.stdin.write(raw)
            proxy = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(a.output/f'reference/frame-{i:04d}.png'), proxy, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            if i in still_indices: cv2.imwrite(str(a.output/f'stills/frame-{i:04d}.png'), frame)
            frames.append({'index': i, 'time': t, 'phaseDegreesUnwrapped': phase, 'turnsPerSecond': speed,
                           'nativeGray8SHA256': hashlib.sha256(raw).hexdigest(), 'meanLuma': float(proxy.mean()),
                           'brightFraction': float(np.mean(proxy>210)), 'darkFraction': float(np.mean(proxy<24))})
            if i % 300 == 0: print(f'{t:02.0f}s / {speed:.3f} turns per second / {i}/1800', flush=True)
    finally:
        encoder.stdin.close(); encoder.wait()
    assert encoder.returncode==0, encoder.stderr.read().decode()
    phases = np.array([f['phaseDegreesUnwrapped'] for f in frames]); speeds = np.array([f['turnsPerSecond'] for f in frames])
    assert np.all(np.diff(phases)>0) and np.all(np.diff(speeds)>0)
    assert np.diff(phases).max()<180
    checkpoints = [{'time': t, 'phaseDegrees': motion(t, a.end_rps)[0], 'turnsPerSecond': motion(t, a.end_rps)[1]} for t in range(0, 31, 5)]
    manifest = {'title': 'ANGLES / acceleration', 'duration': DURATION, 'dimensions': [W, H], 'fps': FPS,
        'camera': {'origin': [0, 0, 0], 'worldAxis': [0, 0, -1], 'startYawPitchRollDegrees': [-17, 0, -8],
                   'lensMM': 35, 'sensorWidthMM': 36, 'cuts': 0, 'phaseResets': 0, 'motionBlur': False},
        'speed': {'startTurnsPerSecond': START_RPS, 'endTurnsPerSecond': a.end_rps, 'curve': 'continuous exponential',
                  'formula': 'speed(t)=start*exp(k*t); turns(t)=start*expm1(k*t)/k; k=ln(end/start)/30', 'checkpoints': checkpoints},
        'sourcePath': os.path.relpath(a.source, a.output), 'sourcePanorama': source, 'frames': frames,
        'provenance': {'method': 'Perspective views from the existing fixed Cycles sphere; only the world-Z camera rotation rate changes.',
                       'nativeSources': 'Deterministic recipe and source panorama; all native frame byte hashes plus 480x270 reference frames and selected native stills.',
                       'providerCalls': 0, 'apiCostUSD': 0, 'upscale': False}}
    (a.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
    stream = probe['streams'][0]
    assert (stream['width'], stream['height'], stream['nb_frames'], stream['r_frame_rate'])==(W, H, '1800', '60/1')
    assert float(probe['format']['duration'])==30 and len(probe['streams'])==1
    decoder = subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(video), '-vf', 'scale=480:270:flags=area',
                                '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    quality = []
    for i in range(1800):
        data = decoder.stdout.read(480*270*3//2); assert len(data)==480*270*3//2
        assert np.all(np.frombuffer(data[480*270:], np.uint8)==128)
        x = cv2.imread(str(a.output/f'reference/frame-{i:04d}.png'), 0).astype(float)
        y = np.clip(np.round((np.frombuffer(data[:480*270], np.uint8).astype(float).reshape(270, 480)-16)*255/219), 0, 255)
        mse = float(np.mean((x-y)**2)); quality.append(10*math.log10(255**2/max(mse, 1e-12)))
    assert not decoder.stdout.read(); decoder.wait(); assert decoder.returncode==0, decoder.stderr.read().decode()
    assert min(quality)>35
    windows = []
    for start in range(0, 30, 5):
        group = frames[start*FPS:(start+5)*FPS]; levels = np.array([f['meanLuma'] for f in group])
        state = None; transitions = 0
        for value in levels:
            new = 'dark' if value<35 else 'bright' if value>100 else state
            if state is not None and new!=state: transitions+=1
            state = new
        windows.append({'start': start, 'end': start+5, 'lumaRange': [float(levels.min()), float(levels.max())],
                        'lumaStdDev': float(levels.std()), 'darkBrightTransitions': transitions})
    validation = {'passed': True, 'duration': 30, 'dimensions': [W, H], 'fps': FPS, 'decodedFrames': 1800,
        'fixedAxisAndCenter': True, 'sameImageEveryRevolution': True, 'speedStrictlyIncreasing': True,
        'phaseStrictlyIncreasing': True, 'maximumDegreesPerFrame': float(np.diff(phases).max()),
        'minimumFramePSNR': min(quality), 'allEncodedChromaNeutral': True, 'projectionChecks': comparisons,
        'brightnessWindows': windows, 'videoSHA256': sha(video), 'sourcePanoramaSHA256': source['sha256'],
        'limits': ['The final section intentionally produces rapid flashing light.',
                   'Finite frame rates can alias fine repeated details at high rotation speeds; phase increments remain below half a revolution per frame.',
                   'Native frame hashes are retained; encoding comparisons use 480 by 270 proxies.']}
    (a.output/'qa/validation.json').write_text(json.dumps(validation, indent=2)+'\n')
    shutil.copyfile(a.output/'stills/frame-0000.png', a.output/'poster.png')
    font_path = Path('/System/Library/Fonts/Helvetica.ttc')
    font = lambda size: ImageFont.truetype(str(font_path), size) if font_path.exists() else ImageFont.load_default()
    board = Image.new('RGB', (1440, 1420), '#111'); draw = ImageDraw.Draw(board)
    draw.text((20, 18), 'ANGLES / ONE AXIS, INCREASING SPEED', fill='white', font=font(28))
    for i, t in enumerate([0, 8, 16, 24, 28, 29]):
        x, y = i%2*720+10, i//2*430+90
        im = Image.open(a.output/f'stills/frame-{t*60:04d}.png').convert('RGB').resize((700, 394), Image.Resampling.LANCZOS)
        board.paste(im, (x, y)); draw.text((x, y+400), f'{t:02d}s / {motion(t,a.end_rps)[1]:.2f} turns per second', font=font(18), fill='#ccc')
    board.save(a.output/'contact-sheet.jpg', quality=94)
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Angles / Acceleration</title><style>
*{box-sizing:border-box}body{margin:0;background:#090909;color:#eee;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1240px;margin:auto;padding:38px 24px 64px}h1{font-size:clamp(40px,6vw,72px);letter-spacing:-.05em;line-height:1;margin:16px 0 20px}.label{color:#aaa;font-size:12px;letter-spacing:.14em}p{max-width:900px;color:#aaa}video{display:block;width:100%;aspect-ratio:16/9;background:black;border:1px solid #333}.controls{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}button{background:#202020;color:#ddd;border:1px solid #555;padding:9px 14px;font:inherit;font-size:13px;cursor:pointer}button:hover{background:#ddd;color:#111}a{color:#ddd}.meter{display:flex;justify-content:space-between;gap:20px;font-variant-numeric:tabular-nums;color:#ddd;font-size:14px}progress{display:block;width:100%;height:4px;margin:12px 0 24px;accent-color:#ddd}details{margin:26px 0}summary{cursor:pointer}.foot{font-size:12px;color:#888;border-top:1px solid #333;padding-top:20px;margin-top:34px}@media(max-width:640px){main{padding:24px 14px}}
</style><main><div class="label">ANGLES / CONTINUOUS ACCELERATION</div><h1>One axis. Faster.</h1><p>The same circle, again and again. A slow look at the metal builds into flashes of silver and black. Only the rotation speed changes.</p><p class="label">30 SECONDS · 16:9 · 1080P · 60 FPS · SILENT<br>RAPID FLASHING LIGHT IN THE FINAL SECTION</p>
<video id="film" controls playsinline preload="metadata" poster="poster.png" src="angles-acceleration-30s.mp4"></video><div class="controls"><button data-time="0">Start</button><button data-time="10">10s / Building</button><button data-time="20">20s / Fast</button><button data-time="25">25s / Final surge</button></div><div class="meter"><span id="rate">0.017 turns / second</span><span id="rpm">1 rpm</span></div><progress id="ramp" max="30" value="0" aria-label="Progress through acceleration"></progress><p><a href="angles-acceleration-30s.mp4">Open the film ↗</a></p><details><summary>The motion</summary><p>One fixed vertical axis, one direction, one lens and the same surrounding geometry and lighting. The camera stays at the center. Speed rises continuously from 6 degrees per second to ENDRATE full turns per second. There are no cuts, phase resets or exposure changes.</p><p>Sixty distinct frames per second and sharp poses preserve the final flashes. Playback is not looped, so the ending does not jump back to the slow start.</p></details><details><summary>Production record</summary><p>Existing local Blender Cycles sphere, sampled at native 1920 by 1080. Opaque neutral metal and black. No paid generation or 4K upscale. <a href="qa/validation.json">Verification</a> · <a href="manifest.json">Camera and speed record</a></p></details><div class="foot">Creative development and local rendering: OpenAI Codex. Blender Cycles, Python, OpenCV and FFmpeg.<br><a href="https://github.com/TeeKay-FourTwentyOne/video-generator">https://github.com/TeeKay-FourTwentyOne/video-generator</a></div></main><script>
const film=document.getElementById('film'),k=Math.log(ENDRATE*60)/30;document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{film.pause();film.currentTime=Number(b.dataset.time);});film.ontimeupdate=()=>{const speed=Math.exp(k*film.currentTime)/60;document.getElementById('rate').textContent=speed.toFixed(speed<1?3:2)+' turns / second';document.getElementById('rpm').textContent=Math.round(speed*60)+' rpm';document.getElementById('ramp').value=film.currentTime;};window.sceneLab={};
</script></html>'''
    (a.output/'review.html').write_text(html.replace('ENDRATE', str(a.end_rps)))
    print(json.dumps({'speedCheckpoints': checkpoints, 'validation': validation}, indent=2), flush=True)

if __name__=='__main__': main()
