#!/usr/bin/env python3
"""Assemble photographic factory motion studies locally with FFmpeg.

Generated plates stay under ignored data paths. This recipe uses no providers.
Image editing/extraction is performed upstream by imagegen; FFmpeg animates the
resulting layers and a code-native clock hand. Existing outputs are refused.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import math
import shutil
import subprocess
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
SR = 48000
W, H, FPS = 1664, 936, 24
CROP = 'crop=1664:936:4:2,setsar=1'


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def write_wav(path, samples):
    data = np.rint(np.clip(samples, -1, 1) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(SR)
        out.writeframes(data.tobytes())


def eased_angle(degrees, start, stop, hold, end):
    return (f'{degrees}*PI/180*if(lt(t,{start}),0,'
            f'if(lt(t,{stop}),(1-cos(PI*(t-{start})/{stop-start}))/2,'
            f'if(lt(t,{hold}),1,'
            f'if(lt(t,{end}),(1+cos(PI*(t-{hold})/{end-hold}))/2,0))))')


def rotate_layer(label, output, pivot, angle):
    px, py = pivot
    ox, oy = 1024-px, 1024-py
    return (f'[{label}]pad=2048:2048:{ox}:{oy}:color=black@0,'
            f"rotate='{angle}':ow=2048:oh=2048:c=none:bilinear=1,"
            f'crop={W}:{H}:{ox}:{oy}[{output}]')


def picture(out, assets, name, duration, inputs, graph, input_rate=8):
    graphfile = out/'recipe'/f'{name}.ffmpeg.txt'
    graphfile.write_text(graph + '\n')
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-filter_complex_threads', '2']
    for item in inputs:
        if item.startswith('lavfi:'):
            cmd += ['-f', 'lavfi', '-i', item[6:]]
        else:
            cmd += ['-loop', '1', '-framerate', str(input_rate), '-i', str(assets/item)]
    cmd += ['-filter_complex_script', str(graphfile), '-map', '[v]', '-an',
            '-frames:v', str(round(duration*FPS)), '-c:v', 'libx264', '-preset', 'medium',
            '-crf', '15', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709',
            '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart',
            str(out/'shots'/f'{name}.mp4')]
    run(cmd)
    print(f'Rendered {name}: {duration}s', flush=True)


def render_pictures(out, assets, plan):
    picture(out, assets, 'wide', 5, ['F01-no-robots.png'],
            f'[0:v]{CROP},fps={FPS},format=yuv420p[v]')
    lever = plan['lever']
    angle = eased_angle(lever['angle_degrees'], *lever['pull'], lever['hold_until'], lever['return_until'])
    graph = ';'.join([
        f'[0:v]{CROP},format=rgba[bg]',
        f'[1:v]{CROP},format=rgba[arm]',
        rotate_layer('arm', 'moving', lever['pivot'], angle),
        f'[bg][moving]overlay=0:0:format=auto,fps={FPS},format=yuv420p[v]'])
    picture(out, assets, 'lever', 5, ['L01-clean-plate.png', 'L01-hand-lever-layer.png'], graph)
    clock = plan['clock']
    x, y = clock['pivot']
    length = clock['second_hand_length']
    angle = f'2*PI*({clock["start_second"]}+floor(t))/60'
    graph = ';'.join([
        f'[0:v]{CROP},format=rgba[bg]',
        f"[1:v]format=rgba,geq=r=64:g=59:b=49:a='255*between(X,{x-1},{x+1})*between(Y,{y-length},{y+22})'[hand]",
        rotate_layer('hand', 'moving', clock['pivot'], angle),
        f'[bg][moving]overlay=0:0:format=auto,fps={FPS},format=yuv420p[v]'])
    picture(out, assets, 'clock', 4, ['C01-clock.png', f'lavfi:color=c=black@0:s={W}x{H}:r=8,format=rgba'], graph)
    robot = plan['robot']
    angle = eased_angle(robot['angle_degrees'], *robot['tilt'], robot['hold_until'], robot['return_until'])
    # Curved chin division retains the neck behind the tilt. A horizontal slice
    # through the head/neck junction produces a visible straight seam.
    head_mask = 'if(lt(Y,607),1,if(gt(Y,650),0,clip(650-43*pow((X-829)/137,2)-Y+0.5,0,1)))'
    graph = ';'.join([
        f'[0:v]{CROP},format=rgba[bg]',
        f'[1:v]{CROP},format=rgba,split=3[h][b][n]',
        '[n]crop=260:52:696:650,scale=260:92:flags=lanczos[neck]',
        f"[b]geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*(1-({head_mask}))'[body]",
        f"[h]geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*({head_mask})'[head]",
        '[bg][neck]overlay=696:610:format=auto[neckbg]',
        '[neckbg][body]overlay=0:0:format=auto[bodybg]',
        rotate_layer('head', 'moving', robot['head_pivot'], angle),
        f'[bodybg][moving]overlay=0:0:format=auto,fps={FPS},format=yuv420p[v]'])
    picture(out, assets, 'robot', robot['duration'], ['R01-clean-plate.png', 'R01-robot-layer.png'], graph)


def sound(out):
    """Quiet room tone, heavy machine cycle, clock and relay; no voices/music."""
    rng = np.random.default_rng(240924)

    def stereo(x, pan=0):
        return np.column_stack([x*(1-max(0,pan)*.35), x*(1+min(0,pan)*.35)])

    def add(dst, x, at, pan=0):
        start = round(at*SR)
        count = min(len(x), len(dst)-start)
        dst[start:start+count] += stereo(x[:count], pan)

    def tone(duration):
        t = np.arange(round(duration*SR))/SR
        noise = rng.normal(0, 1, len(t))
        noise = np.convolve(noise, np.ones(65)/65, mode='same')
        x = (.009*np.sin(2*np.pi*60*t)+.003*np.sin(2*np.pi*120*t)
             +.002*np.sin(2*np.pi*179.8*t)+.009*noise)
        x *= .93+.07*np.sin(2*np.pi*.27*t)
        return stereo(x, -.1)

    def knock(duration=.65, freq=74, strength=.18):
        t = np.arange(round(duration*SR))/SR
        x = (np.sin(2*np.pi*freq*t)*np.exp(-t*11)
             +.31*np.sin(2*np.pi*freq*2.63*t)*np.exp(-t*19)
             +.23*rng.normal(0, 1, len(t))*np.exp(-t*70))
        x *= np.minimum(1, t/.003)*strength
        return x

    def scrape(duration, strength=.018):
        t = np.arange(round(duration*SR))/SR
        n = rng.normal(0,1,len(t))
        n = n-np.convolve(n,np.ones(21)/21,mode='same')
        return n*np.sin(np.pi*np.arange(len(n))/len(n))**.8*strength

    room = tone(18)
    machine = np.zeros_like(room)
    clock = np.zeros_like(room)
    add(machine, scrape(.75), 6.25, -.3)
    add(machine, knock(), 7.0, -.25)
    add(machine, knock(.32, 143, .052), 7.16, .15)
    add(machine, scrape(.5,.011), 8.25, -.3)
    add(machine, knock(.26, 165, .035), 8.75, -.3)
    # Offscreen machinery continues after the return to the wide.
    add(machine, knock(.85, 59, .095), 16.4, .4)
    for at in range(18):
        gain = .028 if 10 <= at < 14 else .0045
        add(clock, knock(.045, 1350 if at%2 else 1650, gain), float(at), .35)
    # Short edge ramps avoid clicks; this is an excerpt, not the film's ending.
    stems = {'room':room, 'machinery':machine, 'clock':clock}
    mix = sum(stems.values())
    gain = min(1.0, 10**(-6/20)/max(.00001, float(np.abs(mix).max())))
    for name,x in stems.items():
        x = x*gain
        x[:480] *= np.linspace(0,1,480)[:,None]
        x[-480:] *= np.linspace(1,0,480)[:,None]
        write_wav(out/'audio'/f'opening-{name}.wav', x)
        stems[name] = x
    mix = sum(stems.values())
    write_wav(out/'audio'/'opening-mix.wav', mix)
    robot = tone(6)*gain
    add(robot, knock(.25, 210, .025)*gain, 1.8, -.25)
    robot[:480] *= np.linspace(0,1,480)[:,None]
    robot[-480:] *= np.linspace(1,0,480)[:,None]
    write_wav(out/'audio'/'robot-mix.wav', robot)
    save_json(out/'audio'/'cues.json', {'sample_rate':SR,'shared_gain':gain,
        'lever_pull':[6.25,7.0], 'machine_response':7.0,'lever_return':[8.25,8.75],
        'foreground_clock_ticks':[10,11,12,13], 'offscreen_machine':16.4,
        'robot_attention_cue':1.8, 'provenance':'Original local procedural sound. No provider, external recording, dialogue or music.',
        'listening_review':'pending user review'})


def assemble(out, plan):
    for name, audio in [('01-work-routine','opening-mix.wav'),('02-robot-performance','robot-mix.wav')]:
        duration = 18 if name.startswith('01') else plan['robot']['duration']
        master = out/'masters'/f'{name}.mov'
        cmd = ['ffmpeg','-hide_banner','-loglevel','error','-nostdin']
        if name.startswith('01'):
            graph = []
            for i, shot in enumerate(plan['opening']):
                cmd += ['-i',str(out/'shots'/f"{shot['kind']}.mp4")]
                graph.append(f"[{i}:v]trim=end_frame={round(shot['duration']*FPS)},setpts=PTS-STARTPTS[s{i}]")
            graph.append('[s0][s1][s2][s3]concat=n=4:v=1:a=0[v]')
            graphfile=out/'recipe'/'assembly.ffmpeg.txt'
            graphfile.write_text(';'.join(graph)+'\n')
            cmd += ['-i',str(out/'audio'/audio),'-filter_complex_script',str(graphfile),
                    '-map','[v]','-map','4:a:0','-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p']
        else:
            cmd += ['-i',str(out/'shots'/'robot.mp4'),'-i',str(out/'audio'/audio),
                    '-map','0:v:0','-map','1:a:0','-c:v','copy']
        cmd += ['-frames:v',str(round(duration*FPS)),'-t',str(duration),'-c:a','pcm_s16le',str(master)]
        run(cmd)
        run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-i',str(master),
             '-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'review'/f'{name}.mp4')])
        run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-i',str(master),
             '-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','medium',
             '-crf','18','-c:a','aac','-b:a','160k','-movflags','+faststart',str(out/'review'/f'{name}-720p.mp4')])
        run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-i',str(master),
             '-frames:v','1','-update','1',str(out/'review'/f'{name}-poster.png')])
        print(f'Assembled {name}', flush=True)


def qa(out, plan):
    results = {'scope':'Decoded-frame, timing and audio checks; sampled visual inspection and user listening review are separate.', 'files':{}}
    for name, count in [('01-work-routine',432),('02-robot-performance',144)]:
        master = out/'masters'/f'{name}.mov'
        meta = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(master)]))
        video = next(s for s in meta['streams'] if s['codec_type']=='video')
        audio = next(s for s in meta['streams'] if s['codec_type']=='audio')
        assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_read_frames'])) == (W,H,'24/1',count)
        assert audio['codec_name']=='pcm_s16le' and audio['sample_rate']=='48000'
        raw = subprocess.check_output(['ffmpeg','-v','error','-i',str(master),'-map','0:a:0','-f','s16le','-'])
        samples = np.frombuffer(raw,dtype='<i2').reshape(-1,2)
        assert len(samples)==count*SR//FPS
        peak = float(np.abs(samples.astype(float)).max()/32768)
        assert 0 < peak < .99
        # Decode the entire picture stream; a corrupt frame causes failure.
        run(['ffmpeg','-v','error','-xerror','-i',str(master),'-map','0:v:0','-f','null','-'])
        results['files'][name]={'frames':count,'duration':count/FPS,'size':[W,H],
            'audio_peak_dbfs':round(20*math.log10(peak),2),'decoded_audio_samples':len(samples)}
    for name,times in [('lever',[0,1.25,1.5,1.75,2,3.25,3.5,4.5]),('robot',[0,2,2.25,2.625,3.5,4.25,4.625,5.5]),('clock',[0,1,2,3])]:
        for i,t in enumerate(times):
            run(['ffmpeg','-v','error','-nostdin','-ss',str(t),'-i',str(out/'shots'/f'{name}.mp4'),
                 '-frames:v','1','-update','1',str(out/'qa'/f'{name}-{i:02d}.png')])
        run(['ffmpeg','-v','error','-nostdin','-framerate','1','-i',str(out/'qa'/f'{name}-%02d.png'),
             '-vf',f'scale=416:234,tile=4x{math.ceil(len(times)/4)}','-frames:v','1','-update','1',str(out/'qa'/f'{name}-strip.jpg')])
    results['opening_shot_dependencies'] = ['F01-no-robots.png','L01-clean-plate.png','L01-hand-lever-layer.png','C01-clock.png']
    results['robot_assets_excluded_from_opening'] = True
    results['source_raster'] = [1672,941]
    results['crop'] = plan['source_crop']
    results['upscaled'] = False
    save_json(out/'qa'/'verification.json', results)


def docs(out, assets, plan):
    limits = ''.join(f'<li>{html.escape(item)}</li>' for item in plan['limits'])
    panels = []
    for name,title,text in [
        ('01-work-routine','18 seconds · work routine','No robots or narration. One controlled lever stroke, a clock pause, then back to work. This excerpt begins at the workstation; clock-in and stool-adjustment beats remain for the full opening.'),
        ('02-robot-performance','6 seconds · separate robot study','For later coverage only. A frontal hold, small head tilt, another hold, then return. This clip is deliberately excluded from the opening.')]:
        panels.append(f'<section><h2>{title}</h2><p>{text}</p><video controls playsinline preload="metadata" poster="review/{name}-poster.png"><source src="review/{name}-720p.mp4" type="video/mp4"></video><p><a href="review/{name}.mp4">Native 1664 × 936 review</a> · <a href="masters/{name}.mov">PCM audio master</a></p></section>')
    (out/'index.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Hall of Memories · factory motion</title><style>
    :root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#1b1e1b;color:#e7e4d8;font:17px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:30px 22px 70px}h1{font-size:clamp(30px,5vw,48px);font-weight:500;line-height:1.1}h2{font-size:25px;font-weight:500}p{max-width:860px}a{color:#d5b871}video{width:100%;display:block;background:#000}section{margin-top:42px;padding-top:15px;border-top:1px solid #4d5349}.kicker{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#bbc0af}li{margin:9px 0}details{margin:30px 0}.muted{color:#b4bcac;font-size:14px}</style></head><body><main><p class="kicker">Hall of Memories · motion study 01</p><h1>The work continues.</h1><p>A quiet photographic factory opening, with a separate performance test for the unreal supervisors. No music, narration or opening robot reveal.</p>'''+''.join(panels)+f'''<details><summary>What this test establishes</summary><p>Judge the lever action, the length of the holds, and how much movement the robot needs to feel attentive. The motion cadence is still an audition.</p><ul>{limits}</ul></details><p class="muted">Generated stills and transparent layers; local FFmpeg animation and original sound synthesis. Seven built-in image calls for this run, with exact billing unavailable. No Veo or paid audio generation. Native crop, no upscale. Ending work deferred.</p><p><a href="README.md">Production notes</a> · <a href="qa/verification.json">Technical checks</a> · <a href="../prompts/">Still prompts</a></p></main></body></html>''')
    (out/'README.md').write_text('''# Factory motion study

Status: user review pending. The approved robot look is carried forward; this
new performance, shot timing and local motion treatment remain auditions.

- `review/01-work-routine.mp4`: 18 seconds, no robots, no narration.
- `review/02-robot-performance.mp4`: 6 seconds, separate later-coverage study.
- Matching 720p copies and native PCM-audio masters are retained.

The main excerpt covers workstation routine, not the full chapter opening.
Clock-in, stool adjustment, clipboard marking and later story beats remain.
Robots must be absent at the chapter beginning, sparse until the last two thirds,
and increasingly present toward the end. No exact reveal time is locked.

## Technique and limits

The wide is a held photographic plate. The hand, forearm and lever are one rigid
transparent layer rotating through 11 degrees over a stationary photographic
machine. This tests grip and edit rhythm, not a complete articulated human rig.
A code-native second hand ticks over the clock plate. The robot head makes a
small planar tilt above stationary shoulders; it is not a 3D turn. These motions
use eight poses per second, held in a 24 fps stream. There is no optical-flow
interpolation, camera drift or added blinking.

Source stills are 1672 × 941. A centered 1664 × 936 crop supplies exact 16:9
without upscaling. Review copies have AAC; masters retain 48 kHz stereo PCM.
Sound is original local synthesis with separate room, machinery and clock stems;
listening quality remains for user review. No music or dialogue is present.

Seven built-in image calls produced the plates and cutouts; exact charges were
not exposed. No Veo, paid audio generation, provider QA, upscale or publication.
The parent directory retains exact prompts, original PNGs and a local ledger.
The source recipe is copied here, with timing, filter graphs and asset hashes.

Technical verification decodes all master frames and verifies duration, frame
count, raster, audio sample count and peak headroom. Sampled motion frames are
retained in `qa/`; these checks do not establish emotional success.
''')
    save_json(out/'timeline.json', plan)
    save_json(out/'asset-manifest.json', {p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(assets.glob('*.png'))})


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--assets',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    assets=args.assets.resolve()
    out=args.output.resolve()
    if out.exists():
        raise SystemExit('Refusing existing output; choose a new edit version.')
    required=['F01-no-robots.png','L01-clean-plate.png','L01-hand-lever-layer.png','C01-clock.png','R01-clean-plate.png','R01-robot-layer.png']
    for name in required:
        if not (assets/name).is_file():
            raise SystemExit(f'Missing input: {name}')
    plan=json.loads((HERE/'factory_motion_plan.json').read_text())
    for folder in ['shots','review','masters','audio','qa','recipe']:
        (out/folder).mkdir(parents=True,exist_ok=True)
    for filename in ['factory_motion.py','factory_motion_plan.json']:
        shutil.copy2(HERE/filename,out/'recipe'/filename)
    render_pictures(out,assets,plan)
    sound(out)
    assemble(out,plan)
    qa(out,plan)
    docs(out,assets,plan)
    save_json(out/'manifest.json',{str(p.relative_to(out)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()})
    print('Factory study complete.',flush=True)


if __name__=='__main__':
    main()
