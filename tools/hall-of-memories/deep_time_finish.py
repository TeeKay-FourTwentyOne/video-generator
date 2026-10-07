#!/usr/bin/env python3
"""Finish, inspect and package the deep-time draft plus preserved prior context."""
import argparse
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import wave
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent


def run(cmd):
    subprocess.run(cmd,check=True)


def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]))


def frame_hashes(path):
    s=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-an','-f','framemd5','-']).decode()
    return [line.rsplit(',',1)[1].strip() for line in s.splitlines() if line and not line.startswith('#')]


def pcm_hash(path):
    proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-f','s16le','-'],stdout=subprocess.PIPE)
    h=hashlib.sha256();n=0
    for chunk in iter(lambda:proc.stdout.read(1024*1024),b''):h.update(chunk);n+=len(chunk)
    if proc.wait()!=0:raise RuntimeError('PCM decode failed')
    return h.hexdigest(),n


def export(root):
    out=root/'edit-v1';master=out/'masters/deep-time.mov';review=out/'review'
    if master.exists():raise SystemExit('Refusing existing finish')
    if shutil.disk_usage(root).free<650*1024**2:raise SystemExit('Insufficient finishing reserve')
    common=['ffmpeg','-v','error','-nostdin']
    run(common+['-i',str(root/'render-v1/picture.mp4'),'-i',str(root/'audio/mix.wav'),'-map','0:v:0','-map','1:a:0',
                '-c:v','copy','-c:a','pcm_s16le',str(master)])
    def copies(src,stem):
        run(common+['-i',str(src),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(review/f'{stem}-1080p.mp4')])
        run(common+['-i',str(src),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','medium','-crf','19',
                    '-c:a','aac','-b:a','160k','-movflags','+faststart',str(review/f'{stem}-720p.mp4')])
    copies(master,'deep-time')
    previous=root.parent/'polis-hall-v1/edit-v1/masters'
    old_picture=previous/'context-picture.mp4';old_pcm=previous/'context-audio.wav'
    # Demuxer concat is used for video only. PCM is concatenated separately.
    listing=out/'masters/video-concat.txt'
    sources=[old_picture,root/'render-v1/picture.mp4']
    listing.write_text(''.join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in sources))
    joined_picture=out/'masters/context-picture.mp4'
    run(common+['-f','concat','-safe','0','-i',str(listing),'-map','0:v:0','-an','-c:v','copy',
                '-video_track_timescale','12288',str(joined_picture)])
    joined_pcm=out/'masters/context-audio.wav';h=hashlib.sha256();samples=0
    with wave.open(str(joined_pcm),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000)
        for path in [old_pcm,root/'audio/mix.wav']:
            with wave.open(str(path),'rb') as src:
                assert(src.getnchannels(),src.getsampwidth(),src.getframerate())==(2,2,48000)
                while True:
                    data=src.readframes(48000)
                    if not data:break
                    w.writeframes(data);h.update(data);samples+=len(data)//4
    ctx=out/'masters/hall-through-departure.mov'
    run(common+['-i',str(joined_picture),'-i',str(joined_pcm),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','pcm_s16le',str(ctx)])
    copies(ctx,'hall-through-departure')
    save(root/'qa/assembly.json',{'context_pcm_sha256':h.hexdigest(),'context_samples_per_channel':samples,
                                 'prior_seconds':185,'new_seconds':121,'context_seconds':306})
    for name in ['deep_time_finish.py','deep_time_render.py','deep_time_audio.py','deep_time.json']:
        shutil.copy2(HERE/name,root/'recipe'/name)


def review_page(root):
    out=root/'edit-v1';review=out/'review';plan=json.loads((root/'timeline.json').read_text())
    selected=[(4,'The housing'),(20,'Ice'),(34,'Descent'),(43,'Deep interior'),(65,'Thaw'),(72,'Vegetation'),
              (78,'The clearing'),(87.5,'Landing'),(97,'Explorers'),(104.5,'The question'),(113,'Return'),(120.5,'After departure')]
    sheet=Image.new('RGB',(1440,4*300),(17,23,20));draw=ImageDraw.Draw(sheet)
    for i,(at,label) in enumerate(selected):
        path=root/'qa/keyframes'/f'{at:07.3f}-1920.png'
        # Extract the actual encoded picture for review, not an alternate recipe.
        run(['ffmpeg','-v','error','-nostdin','-y','-ss',str(at),'-i',str(review/'deep-time-1080p.mp4'),'-frames:v','1',str(path)])
        with Image.open(path) as im:thumb=im.resize((480,270),Image.Resampling.LANCZOS)
        x=(i%3)*480;y=(i//3)*300;sheet.paste(thumb,(x,y));draw.text((x+10,y+278),f'{at:05.1f}s  /  {label}',fill=(225,216,192))
    sheet.save(review/'contact-sheet.jpg',quality=92)
    shutil.copy2(root/f'qa/keyframes/{72:07.3f}-1920.png',review/'poster.png')
    buttons=''.join(f'<button data-time="{s["start"]}">{s["start"]:g}s · {html.escape(s["name"])}</button>' for s in plan['shots'])
    prompts=''.join(f'<li><a href="../prompts/{x}.txt">{x} asset prompt</a></li>' for x in ['dry','green','clearing','ship','explorer'])
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hall of Memories — The Earth goes on</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#141a16;color:#e8e5d8;font:17px/1.6 system-ui,-apple-system,sans-serif}main{max-width:1200px;margin:auto;padding:30px 24px 60px}h1{font:42px/1.2 Georgia,serif;margin:10px 0}h2{font-size:22px;margin-top:30px}p{color:#c0c6b8;max-width:920px}a{color:#e6be7c;text-underline-offset:3px}video{display:block;width:100%;background:#050806;max-height:78vh}button{font:inherit;font-size:13px;background:#253127;border:1px solid #647258;color:#eee5cf;padding:9px 12px;border-radius:4px;cursor:pointer}.chapters{display:flex;flex-wrap:wrap;gap:7px;margin:15px 0 24px}.links{display:flex;gap:20px;flex-wrap:wrap;margin:12px 0}.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:12px;color:#d2b176}img{max-width:100%;height:auto}details{border-top:1px solid #425044;padding:16px 0}summary{cursor:pointer}li{margin:5px 0}.small{font-size:14px}button:focus-visible,a:focus-visible{outline:3px solid #e6be7c;outline-offset:3px}</style></head><body><main>
<div class="eyebrow">Hall of Memories / working core</div><h1>The Earth goes on</h1><p>A 2:01 first draft from the jewel hold through geological change, descent into the interior, the return of vegetation, and the visitors' departure. B supplies the painted landscape; C with A supplies the deeper matter.</p>
<video id="segment" controls preload="metadata" poster="review/poster.png"><source src="review/deep-time-720p.mp4" type="video/mp4"></video>
<div class="links"><a href="review/deep-time-1080p.mp4">1080p segment</a><a href="review/deep-time-720p.mp4">720p segment</a><a href="masters/deep-time.mov">PCM master</a></div><nav class="chapters" aria-label="Jump to a beat">BUTTONS</nav>
<h2>In context · 5:06</h2><p>The preceding three polis scenes retain their picture frames, timing and PCM sound. The new segment begins at <strong>3:05</strong>. The factory opening remains outside this core review.</p>
<video id="context" controls preload="metadata"><source src="review/hall-through-departure-720p.mp4" type="video/mp4"></video>
<div class="links"><button id="join">Play from the Hall-to-Earth join</button><a href="review/hall-through-departure-1080p.mp4">1080p context</a><a href="review/hall-through-departure-720p.mp4">720p context</a><a href="masters/hall-through-departure.mov">Context PCM master</a></div>
<h2>Frame overview</h2><a href="review/contact-sheet.jpg"><img src="review/contact-sheet.jpg" loading="lazy" alt="Twelve frames from jewel reveal through ship departure"></a>
<details><summary>Method and review limits</summary><p>This is editable local 2.5D animation of generated painted artwork, with eight source poses per second held into 24 fps. Rock folds deform, the camera travels through a mineral relief, and ship and puppet pieces articulate. The interior is a stylized passage, not a volumetric scientific model. The jewel's visibility uses deliberate changes of scale.</p><p>The visitors, ship, timing and sound are provisional. Their limited puppet articulation and the transition into and out of the illustrated geology are review points. The sound is original procedural scratch sound, including a fictional-language performance; there are no animal calls or music. Visual inspection and technical audio checks do not establish that the sound has been listened through.</p><p>Five new built-in imagegen requests supplied the supporting artwork. Exact tool billing is unavailable. Motion and sound were generated locally, with no video or voice API calls. No 4K finish or publication.</p></details>
<details><summary>Editable recipe, prompts and QA</summary><p><a href="../timeline.json">Timeline</a> · <a href="../recipe/deep_time_render.py">Animation recipe</a> · <a href="../recipe/deep_time_audio.py">Sound recipe</a> · <a href="../recipe/deep_time_finish.py">Finishing recipe</a> · <a href="../audio/manifest.json">Audio stems and provenance</a> · <a href="../qa/verification.json">Technical verification</a> · <a href="../ledger.json">Run ledger</a></p><ul>PROMPTS</ul></details>
</main><script>const segment=document.getElementById('segment');function playAt(v,time){document.querySelectorAll('video').forEach(other=>{if(other!==v)other.pause();});const seek=()=>{v.currentTime=time;v.play().catch(()=>{});};if(v.readyState>=1)seek();else v.addEventListener('loadedmetadata',seek,{once:true});v.scrollIntoView({behavior:'smooth',block:'center'});}document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>playAt(segment,Number(b.dataset.time))));document.getElementById('join').addEventListener('click',()=>playAt(document.getElementById('context'),179));document.querySelectorAll('video').forEach(v=>v.addEventListener('play',()=>document.querySelectorAll('video').forEach(other=>{if(other!==v)other.pause();})));</script></body></html>'''
    (out/'index.html').write_text(page.replace('BUTTONS',buttons).replace('PROMPTS',prompts))
    (root/'index.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=edit-v1/index.html"><a href="edit-v1/index.html">Open the deep-time review</a>')


def verify(root):
    out=root/'edit-v1';plan=json.loads((root/'timeline.json').read_text());checks=[]
    for group,duration,frames in [('deep-time',121,2904),('hall-through-departure',306,7344)]:
        files=[(out/'masters'/f'{group}.mov',1920,1080),
               (out/'review'/f'{group}-1080p.mp4',1920,1080),(out/'review'/f'{group}-720p.mp4',1280,720)]
        for path,w,h in files:
            d=probe(path);v=next(s for s in d['streams'] if s['codec_type']=='video');a=next(s for s in d['streams'] if s['codec_type']=='audio')
            assert (v['width'],v['height'])==(w,h),(path,'raster')
            assert v['r_frame_rate']==v['avg_frame_rate']=='24/1',(path,'rate',v['r_frame_rate'],v['avg_frame_rate'])
            assert int(v['nb_read_frames'])==frames,(path,'frames',v['nb_read_frames'])
            assert abs(float(v['duration'])-duration)<.001,(path,'duration')
            assert int(a['sample_rate'])==48000 and int(a['channels'])==2
            run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
            checks.append({'path':str(path.relative_to(root)),'width':w,'height':h,'fps':24,'frames':frames,'seconds':duration,'full_decode':'passed'})
            print(f'Verified {path.name}',flush=True)
    previous=root.parent/'polis-hall-v1/edit-v1/masters/polis-three-scenes.mov'
    old=frame_hashes(previous);new=frame_hashes(out/'masters/deep-time.mov');combined=frame_hashes(out/'masters/hall-through-departure.mov')
    assert len(old)==4440 and combined==old+new,'Context changed decoded source picture'
    assembly=json.loads((root/'qa/assembly.json').read_text())
    audio_hash,audio_bytes=pcm_hash(out/'masters/hall-through-departure.mov')
    assert audio_hash==assembly['context_pcm_sha256']
    assert audio_bytes==306*48000*4
    preserved=json.loads((root/'baseline-preservation.json').read_text())
    for p in preserved:assert sha(root/p['path'])==p['sha256'],p['path']
    source=np.array(Image.open(root/'assets/jewel.png').convert('RGB'))
    from deep_time_render import Renderer
    renderer=Renderer(root,1920)
    assert np.array_equal(renderer.frame(0),source),'First pose differs from retained jewel hold'
    # Boundary state and subtitles are tested from their actual rendered images.
    sub=plan['subtitle'];assert sub['text']=='Where is everybody?'
    for at in [sub['start']-.125,sub['start'],sub['end']-.125,sub['end']]:
        a=renderer.frame(at);assert a.shape==(1080,1920,3) and float(a.mean())>5
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            self.links.extend(v for k,v in attrs if k in ['href','src'] and v and not v.startswith(('http:','https:','#')))
    links=Links();links.feed((out/'index.html').read_text())
    missing=[p for p in links.links if not(out/p).is_file() and p!='../qa/verification.json']
    assert not missing,missing
    poses=json.loads((root/'qa/source-pose-hashes.json').read_text());assert poses['count']==968
    report={'status':'passed','exports':checks,'first_source_pose_matches_prior_jewel':True,
            'context_decoded_picture_exact_concatenation':True,'preserved_prior_frames':len(old),
            'context_pcm_exact_concatenation':True,'context_samples_per_channel':306*48000,
            'baseline_hashes_unchanged':len(preserved),'source_pose_count':968,'source_pose_rate':8,
            'subtitle':sub,'local_review_links':len(links.links),'listening_review':'not performed',
            'visual_review':'Native keyframes plus dense pose strips; inspection notes retained separately.'}
    save(root/'qa/verification.json',report)
    ledger=json.loads((root/'ledger.json').read_text());ledger.update({'status':'complete first draft awaiting user review','selected_review':'edit-v1/index.html','segment_seconds':121,'context_seconds':306})
    save(root/'ledger.json',ledger)
    files=[]
    for f in sorted(root.rglob('*')):
        if f.is_file() and f!=root/'manifest.json':files.append({'path':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':sha(f)})
    save(root/'manifest.json',{'files':files})
    print(json.dumps({'verification':'passed','files':len(files),'bytes':sum(x['bytes'] for x in files)}),flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--export',action='store_true');ap.add_argument('--review',action='store_true');ap.add_argument('--verify',action='store_true')
    args=ap.parse_args();root=args.run.resolve()
    if args.export:export(root)
    if args.review:review_page(root)
    if args.verify:verify(root)


if __name__=='__main__':main()
