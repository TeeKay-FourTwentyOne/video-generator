"""Cut on measured musical attacks; retain original story coverage and exact song."""
import json, math, hashlib, shutil
from pathlib import Path
R=Path('data/workspace/carnival-dream/draft-v5-kinetic')
old=json.loads(Path('tools/carnival-dream/film.json').read_text())
onsets=json.loads(Path('data/workspace/carnival-dream/analysis-v1/onsets.json').read_text())
attacks=[dict(x,frame=round(x['time']*24)) for x in onsets]
source=Path('../music-distribution/audio/01 - Carnival Dream.mp3')
record={'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_mtime_ns':source.stat().st_mtime_ns,'original_size':source.stat().st_size}
assert record['sha256']=='1c9fe8ec22dd2da42f2d1cfe554f02e68c4b982c967b9e5b2acc42550174dcf9'
shutil.copy2(source,R/'assets/song.mp3');(R/'source.json').write_text(json.dumps(record,indent=2))
clips=[];colors=['black','crimson','violet','cobalt','magenta']
for shot in old['shots']:
 idx=int(shot['id'][2:]);a=shot['start_frame'];end=shot['end_frame'];j=0
 energetic=idx in list(range(9,16))+list(range(20,29))+list(range(33,38))
 while a<end:
  lock=idx==16 and a<round(69*24)
  if lock:
   candidates=[o for o in attacks if a+7<=o['frame']<=min(a+13,end)]
   b=max(candidates,key=lambda o:o['strength'])['frame'] if candidates else min(a+10,end)
  else:
   target=a+([26,34,22,30][j%4] if energetic else [43,35,47,38][j%4])
   candidates=[o for o in attacks if target-5<=o['frame']<=min(target+5,end)]
   b=max(candidates,key=lambda o:o['strength']-.035*abs(o['frame']-target))['frame'] if candidates else min(target,end)
   if 0<end-b<10 and end-a<=60:b=end
  b=min(end,b)
  if idx==16 and a<round(69*24)<b:b=round(69*24)
  assert 0<b-a<=60
  nearby=min(attacks,key=lambda o:abs(o['frame']-a))
  view=['wide','pair','detail','dutch'][j%4]
  if idx in [6,7,22,23,24,31,32]:view=['detail','wide','pair'][j%3]
  if lock:view='locked'
  color=['black','crimson','violet','black','magenta','cobalt'][(len(clips)+idx)%6]
  if lock:color=['black','crimson','violet','crimson','cobalt','violet'][j%6]
  clips.append({'id':f'K{len(clips)+1:03d}','start_frame':a,'end_frame':b,'start':a/24,'end':b/24,'source_id':shot['id'],'kind':shot['kind'],'view':view,'male_color':color,'lock_except_male_color':lock,'source_frame':1200 if lock else None,'nearest_attack_s':nearby['time'],'attack_offset_ms':round((a/24-nearby['time'])*1000,2),'intent':shot['intent']})
  a=b;j+=1
new=dict(old,draft=5,title='Carnival Dream — The Clockwork Theatre / Kinetic Princess',shots=clips,story_shots=old['shots'],budget_cap_usd=20)
(R/'timeline.json').write_text(json.dumps(new,indent=2))
(R/'budget.json').write_text(json.dumps({'cap_usd':20,'external_spend_actual_usd':0,'external_spend_estimate_usd':0,'reserved_usd':0,'calls':[],'scope':'Local revision of draft 4. No paid calls; cumulative drafts 4 and 5 spend is zero.'},indent=2))
(R/'recipe/edit-plan.json').write_text(json.dumps({'cuts':len(clips)-1,'shots':len(clips),'max_shot_s':max((s['end_frame']-s['start_frame'])/24 for s in clips),'mean_shot_s':4084/24/len(clips),'color_lock_sequence':[s for s in clips if s['lock_except_male_color']],'timing_basis':'Existing locally measured broadband attacks. Timing uses transient evidence, not an assertion of instrument separation.','requirements':['Full-song revision','No shot longer than 2.5 seconds','Princess silhouette and separate male design','Black, crimson, violet and other saturated male colors','Locked scene with male-only color cuts','Physically rendered recurring theatre surroundings','Ride transformations synchronized to attacks'],'recurring_details':['Walnut mouldings and brass star medallion','Gathered burgundy velvet and red tassel','Warm footlights with one blue housing','Loose winding key','Paper crescent moon and hanging stars']},indent=2))
print(json.dumps({'shots':len(clips),'max_shot_seconds':max((s['end_frame']-s['start_frame'])/24 for s in clips),'color_cuts':sum(s['lock_except_male_color'] for s in clips)},indent=2))
