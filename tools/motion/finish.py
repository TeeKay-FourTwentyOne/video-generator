#!/usr/bin/env python3
"""Reproducible local camera treatment and sound for the untitled trail film.

Uses the provisioned Pillow/NumPy/SciPy environment. Never changes source media.
The selected-source JSON and frame-addressed beats are private production inputs.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess as sp
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import butter, sosfilt


SR = 48000
W, H = 960, 720


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(args):
    return sp.run(args, check=True, stdout=sp.PIPE, stderr=sp.PIPE).stdout


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def wav(path, signal):
    signal = np.column_stack([signal, signal])
    pcm = (np.clip(signal, -1, 1) * 32767).round().astype('<i2')
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


def band(signal, lo=150, hi=7000):
    return sosfilt(butter(3, [lo, hi], btype='bandpass', fs=SR, output='sos'), signal)


def peak(signal, db):
    return signal * (10 ** (db / 20) / max(np.max(np.abs(signal)), 1e-12))


def rms(signal, db):
    return signal * (10 ** (db / 20) / max(np.sqrt(np.mean(signal ** 2)), 1e-12))


def place(dst, sig, t):
    at = round(t * SR)
    end = min(len(dst), at + len(sig))
    if at >= 0 and end > at:
        dst[at:end] += sig[:end-at]


def audio_file(beat, options, out, seed):
    """Separate, unlooped noise fields and non-rhythmic leaf detail per file."""
    rng = np.random.default_rng(seed)
    seconds = beat['frames'] / 30
    n = round(seconds * SR)
    t = np.arange(n) / SR
    hiss = band(rng.normal(size=n))
    # Slowly irregular wind; no tonal drones, musical intervals or animal calls.
    knots = rng.uniform(.25, 1, 16)
    env = np.interp(t, np.linspace(0, seconds, len(knots)), knots)
    wind = band(rng.normal(size=n), 150, 850) * env
    bed = rms(hiss, -39) + rms(wind, -42)
    for when in rng.uniform(.45, seconds-.25, 9):
        m = int(rng.uniform(.012, .045) * SR)
        tick = band(rng.normal(size=m), 900, 6000) * np.exp(-np.arange(m)/(SR*.009))
        place(bed, peak(tick, rng.uniform(-49, -43)), float(when))
    # Quiet files release toward higher gain. The deer transients hold gain down.
    if beat['id'] == 'C1':
        gain = 1 + .18 * (1-np.exp(-t/1.5))
        for when in options.get('hooves', []):
            elapsed = np.maximum(0, t-when)
            gain -= .10*(1-np.exp(-elapsed/.4))*np.exp(-elapsed/1.5)
        target = -36.5
    else:
        gain = 1 + 1.05 * (1-np.exp(-t/1.5))
        target = {'C2':-35.0, 'C3':-33.0, 'C4':-31.0}[beat['id']]
    bed = rms(bed * gain, target)
    # Electronic self-noise is introduced after the microphone's 7 kHz limit.
    whine = (10**(-48/20)) * np.sin(2*np.pi*11000*t + seed*.1)
    whine *= gain / np.max(gain)
    bed += whine
    clicks = np.zeros(n)
    q = np.arange(round(.04*SR))/SR
    clack = rng.normal(size=len(q)) * np.exp(-q/.0025)
    clack += .7*np.sin(2*np.pi*1700*q)*np.exp(-q/.004)
    mask = q >= .019
    clack[mask] += .65*rng.normal(size=mask.sum())*np.exp(-(q[mask]-.019)/.003)
    clack = band(clack)
    place(clicks, peak(clack, -14), 0)
    pop = np.sin(2*np.pi*230*q)*np.exp(-q/.0018)
    place(clicks, peak(pop, -30), 0)
    animal = np.zeros(n)
    if beat['id'] == 'C1':
        for j, when in enumerate(options.get('hooves', [.2,.58,.97,1.36,4.2,4.58,4.97,5.36])):
            m = round(.18*SR)
            z = np.arange(m)/SR
            impact = np.sin(2*np.pi*(210+25*rng.random())*z)*np.exp(-z/.012)
            litter = band(rng.normal(size=m), 650, 6300)*np.exp(-z/.035)
            # Several tiny leaf breaks trail each soft hoof impact.
            for at in [.027,.044,.075]:
                k = round(at*SR)
                litter[k:k+70] += rng.normal(size=70)*.25
            hoof = band(.42*impact + .7*litter)
            place(animal, peak(hoof, -19.0+rng.uniform(-1,1)), when)
        z = np.arange(round(.36*SR))/SR
        breath = band(rng.normal(size=len(z)), 300, 2800)*np.sin(np.pi*z/.36)**2
        place(animal, peak(breath, -33), options.get('exhaleAt', 2.8))
    mixed = bed + clicks + animal
    assert np.max(np.abs(mixed)) < 10**(-1/20)
    for name, sig in [('bed',bed), ('trigger',clicks), ('animal',animal), ('mix',mixed)]:
        wav(out/f"{beat['id']}-{name}.wav", sig)
    return mixed, {'bedRmsDbfs':float(20*np.log10(np.sqrt(np.mean(bed**2)))),
                   'mixPeakDbfs':float(20*np.log10(np.max(np.abs(mixed)))),
                   'seed':seed, 'samples':n, 'source':'authored procedural sound',
                   'agcAttackSeconds':.4, 'agcReleaseSeconds':1.5,
                   'microphoneBandHz':[150,7000], 'selfNoiseWhineHz':11000,
                   'footsteps':beat['id']=='C1', 'cricket':False}


def strip(frame, font, start, index, temperature):
    d = ImageDraw.Draw(frame)
    d.rectangle((0,668,959,719), fill=20)
    yy, xx = np.mgrid[:96,:96]
    x, y = (xx-47.5)/47, (yy-47.5)/47
    disc = x*x+y*y <= 1
    lit = disc & (x <= .48*np.sqrt(np.maximum(0,1-y*y)))
    moon = Image.fromarray((lit*255).astype('uint8')).resize((24,24),Image.Resampling.LANCZOS)
    frame.paste(230, (16,682,40,706), moon)
    d.text((52,694), f'{temperature}°F', font=font, fill=230, anchor='lm')
    clock = (start + dt.timedelta(seconds=index//15)).strftime('%m/%d/%Y  %I:%M:%S %p')
    d.text((480,694), clock, font=font, fill=230, anchor='mm')
    d.rectangle((915,688,941,700), outline=230, width=2)
    d.rectangle((942,691,944,697), fill=230)
    for x0 in (919,925,931):
        d.rectangle((x0,691,x0+3,697),fill=230)
    return frame


def eyes(a, tracks, t):
    """Optional explicitly reviewed per-frame eye tracks, in 960x720 pixels."""
    for tr in tracks:
        keys = tr['keys']
        if not keys[0][0] <= t <= keys[-1][0]:
            continue
        j = next((i for i in range(len(keys)-1) if keys[i][0] <= t <= keys[i+1][0]), 0)
        p, q = keys[j], keys[j+1]
        f = (t-p[0]) / max(q[0]-p[0],1e-6)
        x,y,r,g = [(1-f)*p[k]+f*q[k] for k in range(1,5)]
        radius = int(math.ceil(r*3))
        x0,x1 = max(0,int(x)-radius),min(W,int(x)+radius+1)
        y0,y1 = max(0,int(y)-radius),min(H,int(y)+radius+1)
        yy,xx = np.mgrid[y0:y1,x0:x1]
        dot = np.exp(-((xx-x)**2+(yy-y)**2)/(2*r*r))
        a[y0:y1,x0:x1] += g*dot*(1+.10*math.sin(t*31+tr.get('phase',0)))
    return a


def camera(w, repo, beat, options, out, font, seed):
    source = repo/options['source']
    assert sha(source) == options['sha256'], 'Source changed'
    n = beat['frames']//2
    assert beat['frames'] % 2 == 0
    start_frame = options.get('inFrame',0)
    filt = f'trim=start_frame={start_frame},setpts=PTS-STARTPTS,fps=15:round=near,crop=ih*4/3:ih:(iw-ow)/2:0,scale=960:720:flags=lanczos,format=gray'
    raw = run(['ffmpeg','-v','error','-i',str(source),'-an','-vf',filt,'-frames:v',str(n),'-f','rawvideo','-pix_fmt','gray','pipe:1'])
    assert len(raw)==n*W*H, 'Insufficient source frames'
    pixels = np.frombuffer(raw,np.uint8).reshape(n,H,W)
    internal = out/f"{beat['id']}-camera15.mp4"
    args = ['ffmpeg','-v','error','-n','-f','rawvideo','-pix_fmt','gray','-s','960x720','-r','15','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-profile:v','high','-pix_fmt','yuv420p','-b:v','1000k','-maxrate','1000k','-bufsize','500k','-g','30','-keyint_min','30','-sc_threshold','0','-bf','0',str(internal)]
    encoder = sp.Popen(args,stdin=sp.PIPE,stderr=sp.PIPE)
    rng=np.random.default_rng(seed)
    fixed = rng.normal(0,.7,(H,W)) + rng.normal(0,.35,(1,W))
    start=dt.datetime.fromisoformat(beat['time'])
    for index,p in enumerate(pixels):
        frame=Image.fromarray(p).filter(ImageFilter.GaussianBlur(.6))
        a=np.asarray(frame,dtype=np.float32)
        if 'exposureDipAt' in options:
            elapsed=index/15-options['exposureDipAt']
            if 0 <= elapsed < 1.6:
                stops=1.5*min(elapsed/.4,1) if elapsed<.4 else 1.5*(1-(elapsed-.4)/1.2)
                a*=2**(-stops)
        a=np.clip(8+np.power(np.clip(a,0,255)/255,1.08)*247,8,235)
        a=eyes(a, options.get('eyeTracks',[]), index/15)
        a=np.clip(a+rng.normal(0,6.5,(H,W))+fixed,8,255)
        frame=strip(Image.fromarray(a.astype('uint8')),font,start,index,beat['temperatureF'])
        encoder.stdin.write(np.asarray(frame).tobytes())
    encoder.stdin.close()
    error=encoder.stderr.read()
    assert encoder.wait()==0,error.decode()
    output=out/f"{beat['id']}.mp4"
    # Deliberately duplicate each 15 fps camera frame; no interpolation or blending.
    # Five black pixels inside each horizontal edge keep transform/deblock
    # ringing inside the defined 810-pixel camera window, even at CRF 16.
    # Compose in RGB: YUV 4:2:0 padding silently rounds the odd y=555 to 554.
    run(['ffmpeg','-v','error','-n','-i',str(internal),'-an','-vf','scale=1080:810:flags=bilinear,format=rgb24,pad=1080:1920:0:555:black,drawbox=x=0:y=555:w=1080:h=5:color=black:t=fill,drawbox=x=0:y=1360:w=1080:h=5:color=black:t=fill,fps=30:round=down,setsar=1,format=yuv420p','-frames:v',str(beat['frames']),'-c:v','libx264','-preset','medium','-crf','16','-profile:v','high','-pix_fmt','yuv420p','-g','60','-bf','0','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(output)])
    return {'path':output.relative_to(w).as_posix(),'sha256':sha(output),'source':options['source'],
            'sourceSha256':options['sha256'],'sourceInFrame':start_frame,'sourceFps':24,
            'frames':beat['frames'],'cameraFrames':n,'cameraFps':15,'fps':30,
            'internal':internal.relative_to(w).as_posix(),'internalSha256':sha(internal),
            'sourceSampling':'timestamp resampling to 15 fps, nearest frame; each camera frame repeated twice',
            'crop':'centered 4:3 of source','cameraWindow':[0,555,1080,810],'insideHorizontalEdgeGuardPixels':5,
            'firstClock':start.isoformat(),'lastClock':(start+dt.timedelta(seconds=(n-1)//15)).isoformat(),
            'options':options}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('workspace',type=Path)
    ap.add_argument('--selection',type=Path,required=True)
    ap.add_argument('--version',required=True)
    ap.add_argument('--audio-only',action='store_true')
    args=ap.parse_args()
    w=args.workspace.resolve();repo=Path.cwd()
    selection=json.loads(args.selection.read_text())
    beats=json.loads((w/selection.get('beats','edit/beats-v1.json')).read_text())
    out=w/'render'/args.version;out.mkdir(parents=True,exist_ok=False)
    audio=out/'audio';audio.mkdir()
    font_path=w/'sources/fonts/RobotoMono-wght.ttf'
    font=ImageFont.truetype(str(font_path),30);font.set_variation_by_axes([700])
    all_audio=[];receipt={'schemaVersion':1,'version':args.version,'recipe':'tools/motion/finish.py','recipeSha256':sha(Path(__file__)),'selectionSha256':sha(args.selection),'fontSha256':sha(font_path),'clips':{},'audio':{},'beats':beats,'artisticApproval':False}
    for i,b in enumerate(beats['beats']):
        if b['kind']=='black':
            all_audio.append(np.zeros(b['frames']*SR//30));continue
        options=selection['shots'][b['id']]
        mix,report=audio_file(b,options,audio,20261030+i*97)
        all_audio.append(mix);receipt['audio'][b['id']]=report
        if not args.audio_only:
            receipt['clips'][b['id']]=camera(w,repo,b,options,out,font,20261031+i*97)
        print(json.dumps({'completed':b['id']}),flush=True)
    soundtrack=np.concatenate(all_audio)
    wav(out/'soundtrack.wav',soundtrack)
    receipt['soundtrack']={'path':(out/'soundtrack.wav').relative_to(w).as_posix(),'sha256':sha(out/'soundtrack.wav'),'samples':len(soundtrack),'channels':'identical dual mono','sampleRate':SR,'digitalZeroGaps':True,'peakDbfs':float(20*np.log10(np.max(np.abs(soundtrack))))}
    write_json(out/'receipt.json',receipt)
    print(json.dumps({'receipt':str(out/'receipt.json'),'seconds':len(soundtrack)/SR}))


if __name__=='__main__':
    main()
