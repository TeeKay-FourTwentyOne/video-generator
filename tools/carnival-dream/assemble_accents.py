#!/usr/bin/env python3
"""Build a new frame sequence containing only explicitly accepted accents.

Original local frames and provider files remain untouched. Generated audio is
discarded. Every replacement is native 1080p and held at eight poses/second.
"""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from PIL import Image

ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
ap.add_argument('--frames',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();run=a.run.resolve();spec=json.loads((run/'timeline.json').read_text())
decision=json.loads((run/'qa'/'accent-acceptance.json').read_text())
dest=a.output.resolve()
if dest.exists():raise RuntimeError('Use a fresh assembly directory to preserve reviewed exports')
patch_plan=run/'qa/local-patches.json'
patches=json.loads(patch_plan.read_text())['patches'] if patch_plan.exists() else []
for patch in patches:
    if patch['decision']!='accept':continue
    shot=next(s for s in spec['shots'] if s['id']==patch['shot'])
    if not all((run/patch['frames']/f'frame-{n:05d}.png').is_file() for n in range(shot['start_frame'],shot['end_frame'])):
        raise RuntimeError('Local correction still incomplete; no assembly written')
dest.mkdir(parents=True)
for n in range(spec['frames']):os.link(a.frames/f'frame-{n:05d}.png',dest/f'frame-{n:05d}.png')
patch_records=[]
if patches:
    for patch in patches:
        if patch['decision']!='accept':continue
        assert patch['visual_reviewed'],'Local patch needs visual review'
        shot=next(s for s in spec['shots'] if s['id']==patch['shot'])
        source=run/patch['frames'];seen=set()
        for n in range(shot['start_frame'],shot['end_frame']):
            frame=source/f'frame-{n:05d}.png';inode=frame.stat().st_ino
            if inode not in seen:
                with Image.open(frame) as im:assert im.size==(1920,1080);im.verify()
                seen.add(inode)
            target=dest/frame.name;target.unlink();os.link(frame,target)
        patch_records.append({'shot':shot['id'],'frames':patch['frames'],'start_frame':shot['start_frame'],'end_frame':shot['end_frame'],'unique_poses':len(seen),'reason':patch['reason'],'render_recipe':json.loads((source/'render.json').read_text())})
records=[]
for entry in decision['clips']:
    if entry['decision']!='accept':continue
    if not all(entry.get(key) for key in ['container_pass','clip_qa_reviewed','clone_check_reviewed']):
        raise RuntimeError('The complete clip gate is required')
    shot=next(s for s in spec['shots'] if s['id']==entry['shot'])
    clip=run/entry['file'];probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(clip)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['width'],video['height'])==(1920,1080),'Native 1080p required; no upscaling'
    count=shot['end_frame']-shot['start_frame'];seconds=count/24
    assert float(video['duration'])>=seconds-.025
    out=run/'generation'/('frames-'+entry['id']);out.mkdir()
    subprocess.run(['ffmpeg','-v','error','-nostdin','-n','-ss',str(entry.get('trim_start_s',0)),'-i',str(clip),'-an',
                    '-vf','fps=8:round=near,fps=24,format=rgb24','-frames:v',str(count),'-start_number','0',str(out/'frame-%05d.png')],check=True)
    hashes={}
    for n in range(count):
        frame=out/f'frame-{n:05d}.png';h=hashlib.sha256(frame.read_bytes()).hexdigest()
        if h in hashes:frame.unlink();os.link(hashes[h],frame)
        else:hashes[h]=frame
        target=dest/f"frame-{shot['start_frame']+n:05d}.png";target.unlink();os.link(frame,target)
    records.append({'id':entry['id'],'shot':shot['id'],'source':entry['file'],'source_sha256':hashlib.sha256(clip.read_bytes()).hexdigest(),'start_frame':shot['start_frame'],'frames':count,'unique_poses':len(hashes),'audio':'discarded'})
(dest/'assembly.json').write_text(json.dumps({'frames':spec['frames'],'local_frame_source':str(a.frames),'local_patches':patch_records,'accents':records},indent=2)+'\n')
print(json.dumps({'frames':spec['frames'],'accepted_accents':len(records),'output':str(dest)}))
