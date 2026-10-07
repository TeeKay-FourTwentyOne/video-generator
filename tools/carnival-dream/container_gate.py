#!/usr/bin/env python3
"""Read-only native clip preflight; retain ffmpeg evidence beside the run."""
import argparse,json,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
a=ap.parse_args()
for p in sorted((a.run/'clips').glob('*.mp4')):
    report=a.run/'qa'/f'{p.stem}-container.json'
    if report.exists():continue
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
    video=[s for s in probe['streams'] if s['codec_type']=='video']
    assert len(video)==1
    v=video[0];assert(v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'24/1')
    result=subprocess.run(['ffmpeg','-v','info','-nostdin','-i',str(p),'-vf',
        'blackdetect=d=0.1:pix_th=0.05,freezedetect=n=-50dB:d=1.0,cropdetect=24:2:0',
        '-an','-f','null','-'],capture_output=True,text=True)
    log=a.run/'operations'/f'{p.stem}-container.log';log.write_text(result.stderr)
    assert result.returncode==0
    flags=[line for line in result.stderr.splitlines() if 'black_start:' in line or 'freeze_start:' in line]
    report.write_text(json.dumps({'probe':probe,'decode_pass':True,'native_1080':True,'black_freeze_flags':flags,
        'ffmpeg_log':str(log.relative_to(a.run)),'decision':'review flags and crop evidence before acceptance'},indent=2)+'\n')
    print(json.dumps({'clip':p.name,'duration':v['duration'],'streams':len(probe['streams']),'flags':flags}))
