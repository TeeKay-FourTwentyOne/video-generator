#!/usr/bin/env python3
"""Native continuation, preserved-baseline context edit, captions and QA."""
import argparse, hashlib, json, math, shutil, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from polis_audio import stamp

HERE=Path(__file__).resolve().parent
def run(cmd):subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def sheet(frames,items,out,columns=4):
    w,h=384,216;tile=Image.new('RGB',(w*columns,(h+30)*math.ceil(len(items)/columns)),(23,25,30));draw=ImageDraw.Draw(tile)
    for i,(n,label) in enumerate(items):
        with Image.open(frames/f'frame-{n:05d}.png') as im:im=im.resize((w,h),Image.Resampling.LANCZOS);tile.paste(im,((i%columns)*w,(i//columns)*(h+30)))
        draw.text(((i%columns)*w+8,(i//columns)*(h+30)+h+7),f'{n/8:.3f}s | {label}',fill=(220,220,220))
    tile.save(out,quality=91)

def verify(path,frames,duration,size):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]))
    v=next(s for s in data['streams'] if s['codec_type']=='video');a=next(s for s in data['streams'] if s['codec_type']=='audio')
    assert int(v['nb_read_frames'])==frames,(path,int(v['nb_read_frames']),frames)
    assert v['r_frame_rate']=='24/1' and (v['width'],v['height'])==size
    assert a['sample_rate']=='48000' and a['channels']==2
    assert abs(float(data['format']['duration'])-duration)<.06
    assert abs(float(a['duration'])-duration)<.06
    run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
    return {'dimensions':size,'frames':frames,'duration':float(data['format']['duration']),'audio':a['codec_name'],'full_decode':'pass','bytes':path.stat().st_size}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--frames',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);args=ap.parse_args()
    root=args.run.resolve();frames=args.frames.resolve();out=args.output.resolve();base=args.baseline.resolve()
    if out.exists():raise SystemExit('Refusing existing edit directory.')
    tl=json.loads((root/'timeline.json').read_text());bt=json.loads((base/'timeline.json').read_text())
    duration=tl['duration'];count=round(duration*8);nframes=round(duration*24);context_duration=bt['duration']+duration
    source_hashes={}
    for i in range(count):
        p=frames/f'frame-{i:05d}.png'
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:assert im.size==(1920,1080)
        source_hashes[p.name]=digest(p)
    for folder in ['review','masters','qa','recipe']:(out/folder).mkdir(parents=True,exist_ok=True)
    for name in ['polis_render.py','polis_invitation_render.py','polis_audio.py','polis_invitation_audio.py','polis_invitation.json']:
        shutil.copy2(frames.parent/'recipe'/name,out/'recipe'/name)
    shutil.copy2(HERE/'polis_invitation_finish.py',out/'recipe'/'polis_invitation_finish.py')
    shutil.copy2(HERE/'polis_invitation_verify.py',out/'recipe'/'polis_invitation_verify.py')
    for name in ['screenplay.md','timeline.json']:shutil.copy2(root/name,out/name)
    save(out/'qa'/'source-hashes.json',source_hashes)
    master=out/'masters'/'polis-invitation.mov';native=out/'review'/'polis-invitation-1080p.mp4';proxy=out/'review'/'polis-invitation-720p.mp4'
    run(['ffmpeg','-v','error','-nostdin','-framerate','8','-i',str(frames/'frame-%05d.png'),'-i',str(root/'audio/mix.wav'),
         '-vf','fps=24,format=yuv420p','-frames:v',str(nframes),'-t',str(duration),'-c:v','libx264','-preset','slow','-crf','16',
         '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','pcm_s16le',str(master)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(master),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(native)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(master),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','160k','-movflags','+faststart',str(proxy)])
    # Identical native encoding parameters permit a lossless picture append.
    # Inputs have PCM audio: there is no independent AAC encoder-padding seam.
    concat=out/'context-inputs.ffconcat'
    old=base/'edit-v2/masters/polis-scene-draft.mov'
    def quoted(path):return "'"+str(path).replace("'","'\\''")+"'"
    concat.write_text('ffconcat version 1.0\nfile '+quoted(old)+'\nfile '+quoted(master)+'\n')
    context=out/'review'/'polis-conversation-and-invitation-1080p.mp4';context_small=out/'review'/'polis-conversation-and-invitation-720p.mp4'
    run(['ffmpeg','-v','error','-nostdin','-f','concat','-safe','0','-i',str(concat),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(context)])
    run(['ffmpeg','-v','error','-nostdin','-i',str(context),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','medium','-crf','18','-c:a','copy','-movflags','+faststart',str(context_small)])
    shutil.copy2(root/'dialogue.vtt',out/'review'/'dialogue.vtt')
    captions=['WEBVTT','']
    for source,offset in [(bt,0),(tl,bt['duration'])]:
        for line in source['lines']:captions.extend([line['id'],f"{stamp(line['start']+offset)} --> {stamp(line['end']+offset)}",line['text'],''])
    (out/'review'/'context-dialogue.vtt').write_text('\n'.join(captions))
    poster=round((duration-.5)*8);shutil.copy2(frames/f'frame-{poster:05d}.png',out/'review'/'poster.png')
    shutil.copy2(base/'edit-v2/review/poster.png',out/'review'/'context-poster.png')
    selected=[(min(count-1,round((l['start']+.5)*8)),l['id']+' '+l['speaker']) for l in tl['lines']]
    selected.extend([(round((tl['cues']['walk_start']+3)*8),'crossing'),(round((tl['cues']['hall_reveal']+1)*8),'Hall approach'),(count-1,'threshold hold')])
    sheet(frames,selected,out/'qa'/'scene-contact-sheet.jpg')
    movement=[(n,'stand and walk') for n in range(round((tl['cues']['stand_start']-.25)*8),round((tl['cues']['walk_end']+.25)*8),6)]
    sheet(frames,movement,out/'qa'/'movement-contact-sheet.jpg')
    boundaries=[(round((l['start']-.25)*8),'before '+l['id']) for l in tl['lines'][1:]]
    sheet(frames,boundaries,out/'qa'/'cut-contact-sheet.jpg')
    join=round(bt['duration']*24)
    join_samples=[join-24,join-1,join,join+12,join+36]
    selection='+'.join(f'eq(n\\,{n})' for n in join_samples)
    run(['ffmpeg','-v','error','-nostdin','-i',str(context),'-vf',f'select={selection},scale=384:216,tile=5x1',
         '-frames:v','1','-update','1',str(out/'qa'/'context-join.jpg')])
    save(out/'qa'/'sample-times.json',{'dialogue_and_walk':selected,'movement':movement,'cuts':boundaries})
    report={'status':'technical checks passed; native creative review pending','duration':duration,'context_duration':context_duration,
            'source_pose_frames':count,'output_frames':nframes,'pose_fps':8,'fps':24,'files':{},'dialogue_lines':len(tl['lines'])}
    for path,size,seconds,frame_count in [(master,(1920,1080),duration,nframes),(native,(1920,1080),duration,nframes),(proxy,(1280,720),duration,nframes),
                                          (context,(1920,1080),context_duration,round(context_duration*24)),(context_small,(1280,720),context_duration,round(context_duration*24))]:
        report['files'][str(path.relative_to(out))]=verify(path,frame_count,seconds,size)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(master),'-map','0:a:0','-f','s16le','-'])
    audio=np.frombuffer(raw,'<i2').reshape(-1,2)
    assert len(audio)==round(duration*48000)
    peak=int(np.abs(audio.astype(np.int32)).max());assert 0<peak<32767
    report['audio_samples']=len(audio);report['peak_dbfs']=round(20*math.log10(peak/32768),2)
    report['silent_record_boundary']='End at the Hall threshold; no record, human voice or scream played.'
    report['final_hold_pixel_identical']=len({source_hashes[f'frame-{i:05d}.png'] for i in range(count-16,count)})==1
    assert report['final_hold_pixel_identical']
    preserved=json.loads((root/'baseline-preservation.json').read_text())
    assert all(digest(base/name)==sha for name,sha in preserved.items())
    report['baseline_preserved']=preserved
    # Decode the appended native picture to demonstrate that the baseline frames
    # and the new segment survive the context append without a dropped cut frame.
    def video_hashes(path):
        text=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-f','framemd5','-']).decode()
        return [l.rsplit(',',1)[-1].strip() for l in text.splitlines() if l and not l.startswith('#')]
    assert video_hashes(context)==video_hashes(old)+video_hashes(master)
    report['context_picture']='Decoded frames match the complete baseline followed by the complete invitation, exactly.'
    save(out/'qa'/'verification.json',report)
    caption_assets=json.dumps([(out/'review'/'dialogue.vtt').read_text(),(out/'review'/'context-dialogue.vtt').read_text()]).replace('<','\\u003c')
    (out/'index.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hall of Memories · With one person</title><style>
    :root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#191b22;color:#e8e4d8;font:18px/1.55 system-ui,sans-serif}}main{{max-width:1120px;margin:auto;padding:36px 22px 70px}}h1{{font-weight:450;font-size:clamp(34px,5vw,55px);line-height:1.06}}a{{color:#edbb6e}}video,img{{display:block;width:100%;height:auto}}nav{{display:flex;gap:22px;flex-wrap:wrap;margin:20px 0 28px}}.eyebrow{{font-size:13px;letter-spacing:.15em;text-transform:uppercase;color:#bab6c0}}.small{{font-size:14px;color:#b9b5be}}details{{margin-top:30px;border-top:1px solid #454650;padding-top:20px}}summary{{cursor:pointer}}</style></head><body><main>
    <p class="eyebrow">Hall of Memories · invitation draft 01</p><h1>With one person</h1><p>The elder invites the children to the Hall of Memories. A question about everybody becomes a decision to listen to one person.</p>
    <video controls playsinline preload="metadata" poster="review/poster.png"><source src="review/polis-invitation-720p.mp4" type="video/mp4"><track kind="subtitles" src="review/dialogue.vtt" srclang="en" label="English dialogue"></video>
    <nav><a href="review/polis-invitation-1080p.mp4">Invitation · native 1080p</a><a href="review/polis-invitation-720p.mp4">Smaller 720p copy</a><a href="screenplay.md">Read the scene</a></nav>
    <p>{duration:.2f} seconds. Ends at the open threshold, before the first human record.</p><p class="small">Same provisional puppets, voices and held-pose cadence as the accepted conversation baseline. The Hall and new dialogue are first-draft choices.</p>
    <details open><summary>Watch both scenes together · {context_duration:.2f} seconds</summary><p>The complete existing conversation followed by the invitation.</p>
    <video controls playsinline preload="none" poster="review/context-poster.png"><source src="review/polis-conversation-and-invitation-720p.mp4" type="video/mp4"><track kind="subtitles" src="review/context-dialogue.vtt" srclang="en" label="English dialogue"></video>
    <nav><a href="review/polis-conversation-and-invitation-1080p.mp4">Both scenes · native 1080p</a><a href="review/polis-conversation-and-invitation-720p.mp4">Both scenes · 720p</a></nav></details>
    <details><summary>Production notes and inspection frames</summary><p>Locally modeled and rendered in Blender. Native 1920 × 1080, 24 fps, eight held poses per second. Temporary installed synthetic voices, separate dialogue, atmosphere and footsteps. No music or provider calls.</p><p><a href="README.md">Production record</a> · <a href="qa/verification.json">Technical checks</a> · <a href="../animation-v1/polis-invitation-animation.blend">Editable animation</a> · <a href="masters/polis-invitation.mov">PCM audio master</a></p><img src="qa/scene-contact-sheet.jpg" alt="Views of the invitation, walk and Hall threshold"></details></main>
    <script>const captionAssets={caption_assets};document.querySelectorAll('track').forEach((track,i)=>{{track.src=URL.createObjectURL(new Blob([captionAssets[i]],{{type:'text/vtt'}}));}});</script></body></html>''')
    (out/'README.md').write_text(f'''# With one person — first invitation draft

Continuation: {duration:.3f} seconds. In context: {context_duration:.3f} seconds.
The earlier conversation is accepted as a baseline for later coordinated polis
revisions. This new segment remains a first draft for user review.

The elder admits uncertainty, invites the children to see what people left,
and leads them through the same simulated neighborhood to the Hall. The final
exchange is “Where do we start?” / “With one person.” Hold at the threshold;
no record is played. The Hall design and its unplayed panels are provisional.
No biological past for the elder or literal extinction mechanism is established.

Native 1920 x 1080 at 24 fps, with eight pose samples per second. One persistent
Blender set extends east of the retained courtyard. The recipe shares the original
puppet construction and materials. New held gestures, a seated-to-standing
transition and deterministic walking lead to a motionless final tableau.
These are CG puppets rendered in a stop-motion style, not physical miniatures.
The .blend contains constant pose keys and a relative sound link. Recipe renders
rebuild the scene; manual .blend edits must be carried back to source explicitly.

Temporary installed synthetic voices retain the baseline casting. Dialogue,
atmosphere and footsteps remain separate. No music. Optional captions remain
external and disabled by default. The context edit appends the preserved native
baseline to this draft; neither source is overwritten or retimed.

QA verifies all source PNGs, every delivered encode, decoded picture continuity
across the context cut, audio duration/headroom and baseline file hashes.
Contact sheets cover each line, camera boundaries and the stand/walk sequence.
See the parent run's QA note for the actual visual/listening review scope.
Technical checks do not constitute creative approval.

No paid provider calls or new provider charges. No 4K finishing or publication.
Exact source is retained in recipe/; all generated media remain local.
''')
    save(out/'manifest.json',{str(p.relative_to(out)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()})
    print(json.dumps({'review':str(out/'index.html'),'seconds':duration,'context_seconds':context_duration,'source_frames':count},indent=2),flush=True)

if __name__=='__main__':main()
