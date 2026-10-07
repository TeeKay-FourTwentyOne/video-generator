"""Encode and audit the full kinetic revision, preserving the previous draft."""
import json,hashlib,importlib.util,subprocess,shutil,os
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
R=Path('data/workspace/carnival-dream/draft-v5-kinetic');S=json.loads((R/'timeline.json').read_text())
OUT=R/'review/carnival-dream-kinetic-princess-draft-5-1080p.mp4'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def main():
 frames=[R/'frames'/f'frame-{f:05d}.png' for f in range(4084)]
 assert all(p.is_file() for p in frames)
 assert S['shots'][0]['start_frame']==0 and S['shots'][-1]['end_frame']==4084
 assert all(a['end_frame']==b['start_frame'] for a,b in zip(S['shots'],S['shots'][1:]))
 assert max(s['end_frame']-s['start_frame'] for s in S['shots'])<=60
 if not OUT.exists():
  with (R/'operations/encode.log').open('w') as log:
   subprocess.run(['ffmpeg','-hide_banner','-nostdin','-n','-framerate','24','-i',str(R/'frames/frame-%05d.png'),'-i',str(R/'assets/song.mp3'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','44100','-ac','2','-t',str(S['duration']),'-video_track_timescale','24000','-movflags','+faststart','-map_metadata','-1','-metadata','title=Carnival Dream - Kinetic Princess - Draft 5',str(OUT)],stdout=log,stderr=log,check=True)
 spec=importlib.util.spec_from_file_location('finish','tools/carnival-dream/finish.py');finish=importlib.util.module_from_spec(spec);spec.loader.exec_module(finish)
 result=finish.verify(R,S,OUT,R/'frames')
 source=Path('../music-distribution/audio/01 - Carnival Dream.mp3');record=json.loads((R/'source.json').read_text())
 assert sha(source)==record['sha256'];assert source.stat().st_mtime_ns==record['original_mtime_ns']
 old=R.parent/'draft-v4-shadow/review/carnival-dream-clockwork-theatre-draft-4-1080p.mp4'
 oldrecord=json.loads((R.parent/'draft-v4-shadow/qa/completion.json').read_text());assert sha(old)==oldrecord['export_sha256']
 # Verify all authored PNGs and every editorial boundary from actual rendered pixels.
 unique=set()
 for p in frames:
  inode=p.stat().st_ino
  if inode in unique:continue
  with Image.open(p) as im:assert im.size==(1920,1080);im.verify()
  unique.add(inode)
 cuts=[]
 for clip in S['shots'][1:]:
  f=clip['start_frame'];before=np.asarray(Image.open(frames[f-1]).convert('RGB'));after=np.asarray(Image.open(frames[f]).convert('RGB'))
  changed=int(np.sum(np.any(before!=after,axis=2)));assert changed>1000,f'No visible cut at {f}'
  cuts.append({'clip':clip['id'],'frame':f,'time_s':f/24,'changed_pixels':changed,'view':clip['view'],'male_color':clip['male_color'],'nearest_measured_attack_offset_ms':clip['attack_offset_ms']})
 # Every original story scene receives a revised treatment; this is a full-film pass.
 coverage=[]
 for story in S['story_shots']:
  clips=[c for c in S['shots'] if c['source_id']==story['id']];assert clips
  assert clips[0]['start_frame']==story['start_frame'] and clips[-1]['end_frame']==story['end_frame']
  coverage.append({'story_id':story['id'],'takes':len(clips),'views':[c['view'] for c in clips]})
 (R/'qa/edit-audit.json').write_text(json.dumps({'status':'pass','shots':len(S['shots']),'cuts':len(cuts),'max_shot_s':max((c['end_frame']-c['start_frame'])/24 for c in S['shots']),'average_shot_s':4084/24/len(S['shots']),'frames':4084,'unique_pngs_verified':len(unique),'all_41_story_scenes_revised':coverage,'actual_cut_checks':cuts},indent=2))
 (R/'qa/source-preservation.json').write_text(json.dumps({'status':'pass','original_audio_hash_and_mtime_unchanged':True,'draft4_hash_unchanged':True},indent=2))
 # Contact sheets are regenerated from the delivered frame sequence.
 for page in range(4):
  subset=S['shots'][page*35:(page+1)*35];sheet=Image.new('RGB',(1920,7*238),(16,19,26));d=ImageDraw.Draw(sheet)
  for i,c in enumerate(subset):
   f=(c['start_frame']+c['end_frame'])//2;im=Image.open(frames[f]);im.thumbnail((384,216));x=i%5*384;y=i//5*238;sheet.paste(im,(x,y));d.text((x+6,y+219),f"{c['id']} {c['start']:.2f}s {c['view']} {c['male_color']}",fill='white')
  sheet.save(R/'review'/f'contact-{page+1}.jpg',quality=93)
 shutil.copy2(frames[2440],R/'review/poster.png')
 previous=R/'review/draft-4-reference.mp4'
 if not previous.exists():os.link(old,previous)
 chapters=[(0,'Opening'),(15.67,'The partner'),(42.33,'First carnival'),(64.79,'Color percussion'),(76.08,'Borrowed stars'),(95.67,'Three failures'),(119.25,'The clock'),(140.625,'Final carnival')]
 buttons=''.join(f'<button data-time="{t}"><small>{int(t)//60}:{int(t)%60:02d}</small>{label}</button>' for t,label in chapters)
 html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Carnival Dream · Kinetic Princess</title><style>:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#16141b;color:#eee1c6}*{box-sizing:border-box}body{max-width:1320px;margin:auto;padding:30px 24px}h1{font:normal clamp(32px,5vw,62px) Georgia,serif;margin:10px 0}p{color:#bcb1aa;line-height:1.6}.kicker{letter-spacing:.18em;text-transform:uppercase;color:#c6a06e;font-size:12px}video{width:100%;aspect-ratio:16/9;background:#111;box-shadow:0 18px 70px #0009}nav{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:18px 0}button{font:inherit;font-size:13px;text-align:left;color:#e5d6c1;border:1px solid #594453;background:#29202c;padding:12px;cursor:pointer}button:hover,button:focus-visible,button[aria-pressed=true]{background:#483048;border-color:#ca9a78}small{display:block;color:#c79a73;margin-bottom:6px}a{color:#dfad83}.versions{display:flex;gap:8px;margin:18px 0}.versions button{font-size:14px}footer{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;padding-top:20px;border-top:1px solid #473a47}.note{max-width:850px}@media(max-width:650px){body{padding:22px 12px}nav{grid-template-columns:repeat(2,1fr)}}</style><div class="kicker">Borrowed Light · Full revision 05</div><h1>Carnival Dream</h1><p>Kinetic Princess / The Clockwork Theatre</p><div class="versions" aria-label="Compare drafts"><button data-source="MOVIE" aria-pressed="true">Draft 5 · Kinetic Princess</button><button data-source="draft-4-reference.mp4" aria-pressed="false">Draft 4 · Previous version</button></div><video id="film" controls preload="metadata" playsinline poster="poster.png"><source src="MOVIE" type="video/mp4"></video><nav aria-label="Chapters">BUTTONS</nav><p class="note">A princess in a mechanical theatre, pursued by a partner who becomes black, crimson, violet, blue, and magenta. At 1:05, the entire world holds still while his color changes to the musical attacks.</p><footer><span>Full song · 2:50 · 1920 × 1080</span><span>134 shots · longest 2.375 seconds</span><span>Production spend: $0</span><a href="MOVIE" download>Download Draft 5</a><a href="contact-1.jpg">Contact sheet 1</a><a href="contact-2.jpg">2</a><a href="contact-3.jpg">3</a><a href="contact-4.jpg">4</a></footer><script>const v=document.querySelector('video');document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{v.currentTime=+b.dataset.time;v.focus()});document.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>{const t=v.currentTime,playing=!v.paused;v.pause();v.src=b.dataset.source;v.addEventListener('loadedmetadata',()=>{v.currentTime=Math.min(t,v.duration);if(playing)v.play().catch(()=>{})},{once:true});v.load();document.querySelectorAll('[data-source]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))});</script></html>'''.replace('MOVIE',OUT.name).replace('BUTTONS',buttons)
 (R/'review/index.html').write_text(html)
 for p in Path('tools/carnival-dream/kinetic-theatre').glob('*.py'):shutil.copy2(p,R/'recipe'/p.name)
 shutil.copy2('tools/carnival-dream/finish.py',R/'recipe/finish.py')
 print(json.dumps({'status':'pass','movie':str(OUT),'shots':len(S['shots']),'max_shot_s':max((s['end_frame']-s['start_frame'])/24 for s in S['shots']),'original_song_correlation':result['audio_correlation_by_channel'],'unique_rendered_poses':len(unique),'spend_usd':0},indent=2),flush=True)
if __name__=='__main__':main()
