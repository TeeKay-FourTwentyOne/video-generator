"""Assemble the complete shadow-theatre draft and verify the unchanged source song."""
import hashlib, importlib.util, json, shutil, subprocess
from pathlib import Path
RUN=Path('data/workspace/carnival-dream/draft-v4-shadow')
SPEC=json.loads((RUN/'timeline.json').read_text())
OUT=RUN/'review/carnival-dream-clockwork-theatre-draft-4-1080p.mp4'

def main():
    frames=RUN/'frames'
    expected=[frames/f'frame-{f:05d}.png' for f in range(SPEC['frames'])]
    assert all(p.exists() for p in expected), 'Complete frame sequence is required'
    if not OUT.exists():
        with (RUN/'operations/encode.log').open('w') as log:
            subprocess.run(['ffmpeg','-hide_banner','-nostdin','-n','-framerate','24','-i',str(frames/'frame-%05d.png'),'-i',str(RUN/'assets/song.mp3'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','44100','-ac','2','-t',str(SPEC['duration']),'-video_track_timescale','24000','-movflags','+faststart','-map_metadata','-1','-metadata','title=Carnival Dream - The Clockwork Theatre - Draft 4',str(OUT)],stdout=log,stderr=log,check=True)
    module=importlib.util.spec_from_file_location('finish',Path('tools/carnival-dream/finish.py'));finish=importlib.util.module_from_spec(module);module.loader.exec_module(finish)
    qa=finish.verify(RUN,SPEC,OUT,frames)
    source=Path('../music-distribution/audio/01 - Carnival Dream.mp3');record=json.loads((RUN/'source.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==record['sha256']
    assert source.stat().st_mtime_ns==record['original_mtime_ns']
    assert source.stat().st_size==record['original_size']
    (RUN/'qa/source-preservation.json').write_text(json.dumps({'status':'pass','original_hash_unchanged':True,'original_mtime_unchanged':True,'original_size_unchanged':True},indent=2))
    # Unique images are the authored poses; intermediate delivery frames are hard-linked holds.
    from PIL import Image,ImageDraw
    hashes={};posecount=0
    for path in expected:
        st=path.stat()
        if st.st_ino not in hashes:
            with Image.open(path) as im:
                assert im.size==(1920,1080);im.verify()
            hashes[st.st_ino]=True;posecount+=1
    coverage=[]
    for shot in SPEC['shots']:
        paths=expected[shot['start_frame']:shot['end_frame']]
        unique=len({p.stat().st_ino for p in paths})
        assert unique>1
        coverage.append({'id':shot['id'],'kind':shot['kind'],'frames':len(paths),'authored_poses':unique})
    (RUN/'qa/frame-integrity.json').write_text(json.dumps({'status':'pass','frames':len(expected),'native_size':[1920,1080],'unique_pose_pngs_verified':posecount,'coverage':coverage},indent=2))
    # Review three poses from every delivered shot, taken from the actual render sequence.
    sheets=[]
    for page in range(3):
        subset=SPEC['shots'][page*14:(page+1)*14]
        sheet=Image.new('RGB',(1440,len(subset)*290),(15,19,24));d=ImageDraw.Draw(sheet)
        for row,shot in enumerate(subset):
            for col,q in enumerate([.10,.50,.90]):
                f=shot['start_frame']+int((shot['end_frame']-shot['start_frame']-1)*q)
                im=Image.open(expected[f]);im.thumbnail((480,270));sheet.paste(im,(col*480,row*290))
            d.text((10,row*290+272),f"{shot['id']} / {shot['kind']} / {shot['start']:.2f}s",fill='white')
        p=RUN/f'qa/motion-coverage-{page+1}.jpg';sheet.save(p,quality=91);sheets.append(p.name)
    # Poster and contact sheet now come from delivered pixels, not obsolete look-development stills.
    shutil.copy2(expected[3651],RUN/'review/poster.png')
    sheet=Image.new('RGB',(1600,2750),(15,19,24));d=ImageDraw.Draw(sheet)
    for i,shot in enumerate(SPEC['shots']):
        f=(shot['start_frame']+shot['end_frame'])//2
        im=Image.open(expected[f]);im.thumbnail((400,225));x=i%4*400;y=i//4*250;sheet.paste(im,(x,y));d.text((x+8,y+228),f"{shot['id']} / {shot['start']:.1f}s / {shot['kind']}",fill='white')
    sheet.save(RUN/'review/contact-sheet.jpg',quality=92)
    chapters=[(0,'The sleeping machine'),(21.18,'A borrowed partner'),(42.34,'The carnival opens'),(76.08,'Painted stars'),(95.68,'One, two, three'),(119.26,'Behind the clock'),(140.64,'A deliberate return')]
    buttons=''.join(f'<button data-time="{t}"><small>{int(t)//60}:{int(t)%60:02d}</small>{label}</button>' for t,label in chapters)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Carnival Dream · The Clockwork Theatre</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#13191e;color:#e4d6b7}*{box-sizing:border-box}body{max-width:1320px;margin:auto;padding:36px 24px}h1{font:normal clamp(32px,5vw,64px) Georgia,serif;margin:10px 0}p{color:#b7b1a4;line-height:1.6}.kicker{letter-spacing:.2em;text-transform:uppercase;color:#c09365;font-size:12px}video{width:100%;aspect-ratio:16/9;background:#090e14;box-shadow:0 15px 65px #0008}nav{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin:20px 0}button{font:inherit;font-size:13px;text-align:left;color:#ddd0b2;border:1px solid #4c4a40;background:#212a2f;padding:12px;cursor:pointer}button:hover,button:focus-visible{border-color:#d1a468;background:#344047}small{display:block;color:#ad8b62;margin-bottom:8px}a{color:#d1a468}footer{font-size:13px;display:flex;flex-wrap:wrap;gap:24px;padding-top:20px;border-top:1px solid #394046}.note{max-width:850px}@media(max-width:850px){nav{grid-template-columns:repeat(3,1fr)}body{padding:24px 12px}}
</style><div class="kicker">Draft 04 · Borrowed Light</div><h1>Carnival Dream</h1><p>The Clockwork Theatre</p><video id="film" controls playsinline preload="metadata" poster="poster.png"><source src="MOVIE" type="video/mp4"></video><nav aria-label="Film chapters">BUTTONS</nav><p class="note">A paper marionette, a partner made of shadow, and a carnival wound by hand. The pleasure remains real even when the mechanism becomes visible.</p><footer><span>2:50 · 1920 × 1080 · 16:9</span><span>Digital cutout stop motion</span><span>Production spend: $0 / $20</span><a href="MOVIE" download>Download draft</a><a href="contact-sheet.jpg">Shot contact sheet</a></footer><script>const v=document.getElementById('film');document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{v.currentTime=+b.dataset.time;v.focus()}));</script></html>'''.replace('MOVIE',OUT.name).replace('BUTTONS',buttons)
    (RUN/'review/index.html').write_text(page)
    for filename in ['deliver.py','render.py']:
        shutil.copy2(Path('tools/carnival-dream/shadow-theatre')/filename,RUN/'recipe'/filename)
    shutil.copy2('tools/carnival-dream/finish.py',RUN/'recipe/finish.py')
    print(json.dumps({'status':'pass','output':str(OUT),'poses':posecount,'audio_correlation':qa['audio_correlation_by_channel'],'api_spend_usd':0},indent=2),flush=True)
if __name__=='__main__':main()
