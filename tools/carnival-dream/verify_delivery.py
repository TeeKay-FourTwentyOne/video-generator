#!/usr/bin/env python3
"""Verify the preserved three-film delivery and original song without network use."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
ap.add_argument('--root',type=Path,default=Path('data/workspace/carnival-dream'))
a=ap.parse_args()
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
expected=json.loads((a.root/'draft-v1/source.json').read_text())
assert a.source.is_file(),'Original song is missing'
assert sha(a.source)==expected['sha256'],'Original song content changed'
assert a.source.stat().st_mtime_ns==expected['mtime_ns'],'Original song modification time changed'
rows=[]
for n in [1,2,3]:
    r=a.root/f'draft-v{n}'
    filename='carnival-dream-borrowed-light-draft-1080p.mp4' if n==1 else f'carnival-dream-borrowed-light-draft-{n}-1080p.mp4'
    movie=r/'review'/filename
    qa=json.loads((r/'qa/technical.json').read_text())
    integrity=json.loads((r/'qa/motion-strips/manifest.json').read_text())
    budget=json.loads((r/'budget.json').read_text())
    assert qa['status']=='pass' and integrity['native_png_integrity']=='pass'
    assert sha(movie)==qa['output_sha256'],'Export changed after technical QA'
    assert sha(r/'assets/song.mp3')==expected['sha256']
    assert budget['ceiling_usd']==30 and budget.get('reserved_total_usd',0)<=30
    assert budget['external_spend_estimate_usd']<=30
    payload=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(movie),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()
    rows.append({'draft':n,'file':filename,'sha256':qa['output_sha256'],'bytes':movie.stat().st_size,
                 'width':qa['video']['width'],'height':qa['video']['height'],'frames':int(qa['video']['nb_frames']),
                 'picture_duration_s':float(qa['video']['duration']),'song_duration_s':qa['source_song_duration_s'],
                 'audio_payload_hash':payload,'estimated_api_usd':budget['external_spend_estimate_usd']})
assert len({r['sha256'] for r in rows})==3,'Draft exports must be distinct'
assert len({r['audio_payload_hash'] for r in rows})==1,'The three song streams differ'
assert all((r['width'],r['height'],r['frames'])==(1920,1080,4084) for r in rows)
report={'status':'pass','original_song_content_and_mtime':'unchanged','original_song_sha256':expected['sha256'],
        'song_only_audio':'identical encoded AAC payload in all three full exports','drafts':rows,
        'production_api_estimate_usd':round(sum(r['estimated_api_usd'] for r in rows),6),
        'user_review_status':'Three complete drafts ready for review; no artistic approval or publication inferred.'}
(a.root/'review/delivery-qa.json').write_text(json.dumps(report,indent=2)+'\n')
for n in [1,2,3]:
    (a.root/f'draft-v{n}/qa/source-preservation-final.json').write_text(json.dumps({'status':'pass','original_sha256':expected['sha256'],'original_mtime_ns':expected['mtime_ns'],'original_unchanged':True,'copy_matches_original':True},indent=2)+'\n')
print(json.dumps({'status':'pass','drafts':3,'raster':'1920x1080','original_song':'unchanged','song_payloads':'identical','production_api_estimate_usd':report['production_api_estimate_usd']}))
