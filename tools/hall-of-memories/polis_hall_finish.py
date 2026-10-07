#!/usr/bin/env python3
"""Native Hall review and exact three-scene context, with preservation evidence."""
import argparse, hashlib, json, math, shutil, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image
from polis_audio import stamp
from polis_invitation_finish import verify, sheet, run, save
from polis_hall_audio import sha
HERE=Path(__file__).resolve().parent

def video_hashes(path):
    data=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-f','framemd5','-']).decode()
    return [l.rsplit(',',1)[-1].strip() for l in data.splitlines() if l and not l.startswith('#')]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--frames',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    root=args.run.resolve();frames=args.frames.resolve();out=args.output.resolve()
    if out.exists():raise SystemExit('Refusing existing edit')
    if shutil.disk_usage(root).free<300*1024**2:raise SystemExit('Insufficient finishing reserve')
    tl=json.loads((root/'timeline.json').read_text());duration=tl['duration'];count=round(duration*8);nframes=count*3
    source_hashes={};dark=[]
    for i in range(count):
        p=frames/f'frame-{i:05d}.png'
        with Image.open(p) as im:im.verify()
        with Image.open(p) as im:
            assert im.size==(1920,1080)
            if np.asarray(im.resize((64,36))).mean()<2:dark.append(i)
        source_hashes[p.name]=sha(p)
    assert not dark,('Unexpected black source poses',dark)
    for folder in ['review','masters','qa','recipe']:(out/folder).mkdir(parents=True,exist_ok=True)
    for p in (frames.parent/'recipe').iterdir():
        if p.is_file():shutil.copy2(p,out/'recipe'/p.name)
    for name in ['polis_hall_finish.py','polis_invitation_finish.py','polis_hall_bake.py','polis_hall_animation_verify.py']:shutil.copy2(HERE/name,out/'recipe'/name)
    for name in ['timeline.json','screenplay.md']:shutil.copy2(root/name,out/name)
    save(out/'qa/source-hashes.json',source_hashes)
    master=out/'masters/polis-hall.mov';native=out/'review/polis-hall-1080p.mp4';proxy=out/'review/polis-hall-720p.mp4'
    run(['ffmpeg','-v','error','-nostdin','-framerate','8','-i',str(frames/'frame-%05d.png'),'-i',str(root/'audio/mix.wav'),'-vf','fps=24,format=yuv420p','-frames:v',str(nframes),'-t',str(duration),'-c:v','libx264','-preset','slow','-crf','16','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','pcm_s16le',str(master)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(master),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(native)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(master),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','160k','-movflags','+faststart',str(proxy)])
    sources=[root.parent/'polis-draft-v1/edit-v2/masters/polis-scene-draft.mov',root.parent/'polis-invitation-v1/edit-v1/masters/polis-invitation.mov',master]
    tls=[json.loads((root.parent/name/'timeline.json').read_text()) for name in ['polis-draft-v1','polis-invitation-v1']]+[tl]
    total=sum(t['duration'] for t in tls)
    if (root/'master-timeline.json').exists():shutil.copy2(root/'master-timeline.json',out/'master-timeline.json')
    else:
        offset=0;segments=[]
        for name,t in zip(['polis-draft-v1','polis-invitation-v1',root.name],tls):
            segments.append({'id':name,'start':offset,'duration':t['duration'],'timeline':f'../{name}/timeline.json'});offset+=t['duration']
        master_timing={'scope':'Available core, from conversation through first jewel reveal. Factory and later chapters excluded.','duration':total,'fps':24,'segments':segments,'geological_time':'not begun','internal_simulation_time':'unspecified relative to external time'}
        save(root/'master-timeline.json',master_timing);save(out/'master-timeline.json',master_timing)
    concat=out/'context-inputs.ffconcat'
    def quoted(p):return "'"+str(p).replace("'","'\\''")+"'"
    concat.write_text('ffconcat version 1.0\n'+''.join('file '+quoted(p)+'\n' for p in sources))
    picture=out/'masters/context-picture.mp4'
    run(['ffmpeg','-v','error','-nostdin','-f','concat','-safe','0','-i',str(concat),'-map','0:v:0','-an','-c:v','copy',str(picture)])
    # Build context from decoded PCM masters, without independent gain changes
    # or the earlier AAC review tracks. Exactly one AAC encode for this review.
    pcm=out/'masters/context-audio.wav';pcm_hash=hashlib.sha256()
    with wave.open(str(pcm),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000)
        for p in sources:
            data=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-f','s16le','-'])
            pcm_hash.update(data);w.writeframes(data)
    context_master=out/'masters/polis-three-scenes.mov';context=out/'review/polis-three-scenes-1080p.mp4';small=out/'review/polis-three-scenes-720p.mp4'
    run(['ffmpeg','-v','error','-nostdin','-i',str(picture),'-i',str(pcm),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','pcm_s16le',str(context_master)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(context_master),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(context)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(context_master),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','160k','-movflags','+faststart',str(small)])
    shutil.copy2(root/'dialogue.vtt',out/'review/dialogue.vtt');caps=['WEBVTT',''];offset=0
    for t in tls:
        for l in t['lines']:caps.extend([l['id'],f"{stamp(offset+l['start'])} --> {stamp(offset+l['end'])}",l['text'],''])
        offset+=t['duration']
    (out/'review/context-dialogue.vtt').write_text('\n'.join(caps))
    poster=round((duration-1)*8);shutil.copy2(frames/f'frame-{poster:05d}.png',out/'review/poster.png')
    shutil.copy2(root.parent/'polis-draft-v1/edit-v2/review/poster.png',out/'review/context-poster.png')
    selected=[(min(count-1,round((s['start']+min(2,(s['end']-s['start'])/2))*8)),s['id']+' '+s['shot']) for s in tl['shots']]
    selected.append((count-1,'final jewel hold'));sheet(frames,selected,out/'qa/scene-contact-sheet.jpg')
    moving=[(i,'entry') for i in range(0,52,4)]+[(i,'withdraw / facet / jewel') for i in range(round(tl['cues']['withdraw']*8),count,8)]
    sheet(frames,moving,out/'qa/transition-contact-sheet.jpg')
    bounds=[(max(0,round(s['start']*8)-1),'before '+s['id']) for s in tl['shots'][1:]]+[(round(s['start']*8),'after '+s['id']) for s in tl['shots'][1:]]
    sheet(frames,sorted(bounds),out/'qa/cut-contact-sheet.jpg')
    report={'status':'technical checks passed; new Hall draft awaits creative review','duration':duration,'context_duration':total,'source_pose_frames':count,'output_frames':nframes,'fps':24,'pose_fps':8,'unexpected_black_poses':dark,'files':{}}
    for p,size,seconds in [(master,(1920,1080),duration),(native,(1920,1080),duration),(proxy,(1280,720),duration),(context_master,(1920,1080),total),(context,(1920,1080),total),(small,(1280,720),total)]:report['files'][str(p.relative_to(out))]=verify(p,round(seconds*24),seconds,size)
    preserved=json.loads((root/'baseline-preservation.json').read_text())
    assert all(sha(root.parent/name)==value for name,value in preserved.items());report['baseline_preserved']=preserved
    expected=sum((video_hashes(p) for p in sources),[])
    assert video_hashes(context)==expected;report['context_picture']='All decoded frames match all three native masters in order, exactly.'
    data=subprocess.check_output(['ffmpeg','-v','error','-i',str(context_master),'-map','0:a:0','-f','s16le','-'])
    assert hashlib.sha256(data).hexdigest()==pcm_hash.hexdigest();report['context_pcm_sha256']=pcm_hash.hexdigest();report['context_pcm_samples']=len(data)//4
    assert len(data)//4==round(total*48000)
    with wave.open(str(root/'audio/mix.wav'),'rb') as w:
        assert w.getnframes()==round(duration*48000);x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.int32)
    report['peak_dbfs']=round(20*np.log10(np.abs(x).max()/32768),2);assert np.abs(x).max()<32767
    report['final_hold_pixel_identical']=len({source_hashes[f'frame-{i:05d}.png'] for i in range(count-32,count)})==1;assert report['final_hold_pixel_identical']
    report['first_voice_isolation_seconds']=tl['cues']['many']-(tl['cues']['first_voice']+4.25+.67);assert report['first_voice_isolation_seconds']>2
    report['review_scope']='Native key frames, all-shot contact sheets and technical audio measurements. No listening or real-time playback assessment claimed.'
    save(out/'qa/verification.json',report)
    caption_assets=json.dumps([(out/'review/dialogue.vtt').read_text(),(out/'review/context-dialogue.vtt').read_text()]).replace('<','\\u003c')
    (out/'index.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hall of Memories · One whole life</title><style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#161b1b;color:#eee8d9;font:18px/1.55 system-ui,sans-serif}}main{{max-width:1120px;margin:auto;padding:36px 22px 70px}}h1{{font-weight:450;font-size:clamp(36px,5vw,58px);line-height:1.06}}a{{color:#d5bd7b}}video,img{{display:block;width:100%;height:auto}}nav{{display:flex;gap:22px;flex-wrap:wrap;margin:20px 0 28px}}.eyebrow{{font-size:13px;letter-spacing:.15em;text-transform:uppercase;color:#aebcb7}}.small{{font-size:14px;color:#b8c2bd}}details{{margin-top:30px;border-top:1px solid #43544c;padding-top:20px}}summary{{cursor:pointer}}</style></head><body><main>
<p class="eyebrow">Hall of Memories · Hall draft 01</p><h1>One whole life</h1><p>A blue cup. A few moments from one person's life. Then the weight of many lives, held inside something very small.</p>
<video controls playsinline preload="metadata" poster="review/poster.png"><source src="review/polis-hall-720p.mp4" type="video/mp4"><track kind="subtitles" src="review/dialogue.vtt" srclang="en" label="English dialogue"></video>
<nav><a href="review/polis-hall-1080p.mp4">Hall segment · native 1080p</a><a href="review/polis-hall-720p.mp4">Smaller 720p copy</a><a href="screenplay.md">Read the scene</a></nav>
<p>{duration:.3f} seconds, from the threshold to the first jewel reveal. Stops before deep time.</p><p class="small">First draft. Fictional records, local CG miniatures, temporary synthetic dialogue and wordless distress voices. Sound recognition and emotional effect need listening review. Optional dialogue captions are off by default.</p>
<details open><summary>Watch all three scenes · 3 minutes 5 seconds</summary><p>The complete accepted conversation and invitation, followed by this Hall draft. Their timing is preserved.</p>
<video controls playsinline preload="none" poster="review/context-poster.png"><source src="review/polis-three-scenes-720p.mp4" type="video/mp4"><track kind="subtitles" src="review/context-dialogue.vtt" srclang="en" label="English dialogue"></video>
<nav><a href="review/polis-three-scenes-1080p.mp4">Three scenes · native 1080p</a><a href="review/polis-three-scenes-720p.mp4">Three scenes · 720p</a></nav></details>
<details><summary>Production notes and inspection frames</summary><p>Native 1920 × 1080 at 24 fps, eight held poses per second. Separate recorded-fragment, dialogue, first-voice, accumulation, atmosphere and Foley stems. No music or provider calls.</p><p><a href="README.md">Production record</a> · <a href="qa/verification.json">Technical verification</a> · <a href="../animation-v1/polis-hall-animation.blend">Editable animation</a> · <a href="masters/polis-hall.mov">PCM segment master</a> · <a href="masters/polis-three-scenes.mov">PCM context master</a></p><img src="qa/scene-contact-sheet.jpg" alt="Hall entry, Mara's four fragments, reactions, voices and emerald reveal"></details></main>
<script>const captions={caption_assets};document.querySelectorAll('track').forEach((track,i)=>{{track.src=URL.createObjectURL(new Blob([captions[i]],{{type:'text/vtt'}}));}});</script></body></html>''')
    (out/'README.md').write_text(f'''# One whole life — Hall draft 01

Native segment: {duration:.3f} seconds. Three-scene context: {total:.3f} seconds.
First Hall draft for user review; the preceding two scenes are accepted working
material for later coordinated polis revision. No final design or voice lock.

Mara is an original fictional adult. Four miniature fragments share a chipped
blue cup. Her father and the silent recipient of her private letter are separate
people. There is no extinction explanation or identification with the elder.
The elder distinguishes recorded moments from the Hall's derived whole-life
sound. One voice and reaction precede the accumulation. The external jewel is a
conceptual coordinate change; the camera does not enter a tunnel into rock.
The uneven six-sided green housing has one pale diagonal inclusion, retained as
GEM-01 for later continuity. End before geology, aliens or later human scenes.

Local Blender geometry and held poses; CG miniatures, not physical stop motion.
Native PNG poses are retained. Exact identical poses share disk storage through
hard links. Edit recipes rebuild geometry; manual animation changes must also
be transferred to source. The compressed .blend retains stepped keys and sound.
The facet image is a locally rendered view of this same Hall, not external media.

Installed local synthetic dialogue, including fictional record voices. Original
procedural wordless distress sounds are temporary, not recorded suffering or
voice clones. Separate stems and individual voices remain in the parent audio/
directory for later revision and reuse. No music. Levels retain the preceding
scenes' gain convention; the context is made from PCM masters, with one AAC pass.

QA: source image integrity, frame counts, full export decodes, raster, rates,
sample counts, headroom, preservation hashes, identical decoded context picture,
exact context PCM concatenation, and held ending. Visual inspection uses contact
sheets and key frames. No real-time playback or listening assessment is claimed.
Technical checks are not creative approval. See the parent QA notes for details.

Zero new provider calls and charges. Prior fifteen built-in image calls remain
unmetered. No 4K finishing, publication, commit or push. Media stays local.
''')
    save(out/'manifest.json',{str(p.relative_to(out)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()})
    (root/'index.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=edit-v1/index.html"><a href="edit-v1/index.html">One whole life review</a>')
    print(json.dumps({'review':str(out/'index.html'),'seconds':duration,'context_seconds':total,'source_poses':count},indent=2),flush=True)
if __name__=='__main__':main()
