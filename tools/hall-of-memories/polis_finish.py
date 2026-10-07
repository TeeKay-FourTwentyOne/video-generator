#!/usr/bin/env python3
"""Finish and verify the complete locally rendered polis scene draft."""
from pathlib import Path
import argparse, hashlib, html, json, math, shutil, subprocess
import numpy as np

HERE=Path(__file__).resolve().parent

def run(cmd):subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--frames',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();root=args.run.resolve();frames=args.frames.resolve();out=args.output.resolve()
    if out.exists():raise SystemExit('Refusing existing edit directory.')
    timeline=json.loads((root/'timeline.json').read_text());duration=timeline['duration'];source_count=round(duration*8);frame_count=round(duration*24)
    for i in range(source_count):
        if not (frames/f'frame-{i:05d}.png').is_file():raise SystemExit(f'Missing frame {i}')
    for folder in ['review','masters','qa','recipe']:(out/folder).mkdir(parents=True,exist_ok=True)
    for name in ['polis_scene.json','polis_audio.py','polis_render.py','polis_finish.py']:shutil.copy2(HERE/name,out/'recipe'/name)
    master=out/'masters'/'polis-scene-draft.mov'
    run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-framerate','8','-i',str(frames/'frame-%05d.png'),'-i',str(root/'audio/mix.wav'),
         '-vf','fps=24,format=yuv420p','-frames:v',str(frame_count),'-t',str(duration),'-c:v','libx264','-preset','slow','-crf','16',
         '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','pcm_s16le',str(master)])
    native=out/'review'/'polis-scene-draft-1080p.mp4';proxy=out/'review'/'polis-scene-draft-720p.mp4'
    run(['ffmpeg','-v','error','-nostdin','-i',str(master),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(native)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(master),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','160k','-movflags','+faststart',str(proxy)])
    shutil.copy2(root/'dialogue.vtt',out/'review'/'dialogue.vtt')
    shutil.copy2(root/'screenplay.md',out/'screenplay.md')
    shutil.copy2(root/'timeline.json',out/'timeline.json')
    shutil.copy2(frames/'frame-00004.png',out/'review'/'poster.png')
    selected=[]
    for j,line in enumerate(timeline['lines']):
        n=min(source_count-1,round((line['start']+.45)*8));name=f'shot-{j:02d}.png'
        shutil.copy2(frames/f'frame-{n:05d}.png',out/'qa'/name)
        selected.append({'file':name,'source_frame':n,'time':n/8,'line':line['id']})
    run(['ffmpeg','-v','error','-nostdin','-framerate','1','-i',str(out/'qa'/'shot-%02d.png'),'-vf','scale=384:216,tile=5x3','-frames:v','1','-update','1',str(out/'qa'/'scene-contact-sheet.jpg')])
    # Dense samples of the late approach and eyeline change.
    start=round((timeline['elder_walk_start']-.25)*8)
    for j,n in enumerate(range(start,min(source_count,start+32),4)):shutil.copy2(frames/f'frame-{n:05d}.png',out/'qa'/f'arrival-{j:02d}.png')
    run(['ffmpeg','-v','error','-nostdin','-framerate','1','-i',str(out/'qa'/'arrival-%02d.png'),'-vf','scale=384:216,tile=4x2','-frames:v','1','-update','1',str(out/'qa'/'arrival-strip.jpg')])
    save(out/'qa'/'sample-times.json',selected)
    report={'status':'technical checks passed; creative review pending','source_pose_frames':source_count,'output_frames':frame_count,'duration':duration,'pose_fps':8,'fps':24,'files':{}}
    for path in [master,native,proxy]:
        data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]))
        v=next(x for x in data['streams'] if x['codec_type']=='video');a=next(x for x in data['streams'] if x['codec_type']=='audio')
        assert int(v['nb_read_frames'])==frame_count
        assert v['r_frame_rate']=='24/1'
        assert (v['width'],v['height'])==((1280,720) if path==proxy else (1920,1080))
        assert a['sample_rate']=='48000'
        run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
        report['files'][str(path.relative_to(out))]={'dimensions':[v['width'],v['height']],'frames':int(v['nb_read_frames']),'duration':float(data['format']['duration']),'audio':a['codec_name'],'full_decode':'pass','bytes':path.stat().st_size}
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(master),'-map','0:a:0','-f','s16le','-'])
    x=np.frombuffer(raw,'<i2').reshape(-1,2)
    assert len(x)==round(duration*48000)
    assert float(np.max(np.abs(x.astype(float))))<32767
    report['audio_samples']=len(x);report['peak_dbfs']=round(20*math.log10(np.abs(x.astype(float)).max()/32768),2)
    # The script is complete and includes exactly one occurrence of the refrain.
    assert len(timeline['lines'])==15
    assert sum(l['text']=='Where is everybody?' for l in timeline['lines'])==1
    assert timeline['lines'][0]['text']=='Will you let me finish?'
    assert timeline['lines'][-1]['speaker']=='elder'
    report['dialogue_lines']=15;report['ending_boundary']='Elder first reply; no Hall visit or historical explanation.'
    report['caption_mode']='Optional separate WebVTT; no burned-in labels or subtitles.'
    save(out/'qa'/'verification.json',report)
    (out/'index.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hall of Memories · The tellers</title><style>
    :root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#191b22;color:#e8e4d8;font:18px/1.55 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:36px 22px 70px}h1{font-weight:450;font-size:clamp(34px,5vw,55px);line-height:1.06;margin:12px 0 18px}p{max-width:900px}a{color:#edbb6e}video,img{display:block;width:100%;height:auto}nav{display:flex;gap:24px;flex-wrap:wrap;margin:20px 0 30px}.eyebrow{font-size:13px;letter-spacing:.15em;text-transform:uppercase;color:#bab6c0}.small{font-size:14px;color:#b9b5be}details{margin-top:38px;border-top:1px solid #454650;padding-top:20px}summary{cursor:pointer}li{margin:8px 0}</style></head><body><main><p class="eyebrow">Hall of Memories · complete scene draft 01</p><h1>The tellers</h1><p>A story loses its argument. A quieter child asks a different question.</p><video controls playsinline preload="metadata" poster="review/poster.png"><source src="review/polis-scene-draft-720p.mp4" type="video/mp4"><track kind="subtitles" src="review/dialogue.vtt" srclang="en" label="English dialogue"></video><nav><a href="review/polis-scene-draft-1080p.mp4">Watch native 1080p</a><a href="review/polis-scene-draft-720p.mp4">Smaller 720p copy</a><a href="screenplay.md">Read the scene</a></nav><p>From “Will you let me finish?” immediately after the factory cut, through the children’s conversation, to the older resident’s first reply. About 40 seconds, with complete dialogue, character performance, atmosphere and footsteps.</p><p class="small">Temporary synthetic voices. The children’s proportions, polis architecture and new dialogue are draft choices for review.</p><details><summary>Scene and production notes</summary><p>Three children: a confident storyteller, a literal-minded challenger and a quieter observer. Their argument gradually loses its certainty. The elder arrives from the side of the circle and the children turn toward them.</p><p>Locally modeled and rendered in Blender with eight held poses per second inside a 24 fps edit. One persistent set and articulated puppets. Native 1920 × 1080; no upscale. No image, video or voice provider calls.</p><p><a href="README.md">Production record</a> · <a href="qa/verification.json">Technical checks</a> · <a href="masters/polis-scene-draft.mov">PCM audio master</a></p><img src="qa/scene-contact-sheet.jpg" alt="Fifteen views covering the complete children conversation and the elder joining"></details></main></body></html>''')
    (out/'README.md').write_text('''# The tellers — complete first scene draft

Status: pending user review. This is a complete edited segment, not an isolated
motion test. It begins just after the factory cut and ends after the elder's
first reply, before the historical explanation or journey to the Hall.

## Direction

Three rounded dark graphite avatars share a stone conversation court. The
storyteller defends a failed story; the challenger keeps identifying its holes;
the quieter child imagines the loneliness of a final human. “Where is everybody?”
changes the question. The elder approaches from the side and joins the circle.
The courtyard, cast proportions, exact new lines and voices are draft choices.
Nothing establishes that the elder personally had a biological life.

The opening raised-hand pose is a target for the future factory match cut.
The preceding factory endpoint is not final and is not included in this export.
The earlier mostly-frontal robot coverage instruction applied to the factory;
this polis conversation uses close shots, a group reveal and a later wider view.

## Picture and sound

Persistent Blender set and articulated puppets, local Cycles rendering, eight
pose samples per second held in 24 fps. Camera marks and gaze/hand performance
are generated by the retained source recipe. No video model, optical-flow
interpolation, face mouths, blinking speech indicators or simulated lip sync.
The split disc is a fixed unreal sky feature. These are rendered stop-motion
style puppets, not photographs of a physical miniature production.

Native 1920 × 1080, with a 720p review copy and H.264/48 kHz stereo PCM master.
Installed macOS speech supplies temporary voices, lightly adjusted in pitch.
Original local atmosphere and Foley are separate stems under the parent run.
No music. Optional review subtitles are a separate WebVTT file, disabled by
default. No character labels or subtitles are burned into the picture.

`screenplay.md` and `timeline.json` preserve every line, speaker and timing.
`recipe/` retains exact source. The parent run retains every source pose frame,
the Blender scene, local voice files, separate sound stems and a zero-provider
call ledger. Prior factory media and earlier look reviews are preserved.

## Validation and limits

All final encodes are fully decoded and checked for frame count, raster and
audio duration/headroom. Contact sheets sample every dialogue line and the
elder approach. Technical verification does not approve dialogue, voice acting,
visual design or emotional pacing. Native user review is still required before
any finishing/upscale. No paid calls, 4K, publication, commit or push.
''')
    save(out/'manifest.json',{str(p.relative_to(out)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()})
    print(json.dumps({'review':str(out/'index.html'),'seconds':duration,'source_frames':source_count,'output_frames':frame_count},indent=2),flush=True)

if __name__=='__main__':main()
