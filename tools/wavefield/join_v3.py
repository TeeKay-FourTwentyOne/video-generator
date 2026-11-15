#!/usr/bin/env python3
"""Stream-copy the revised opening onto v2 and verify every decoded frame."""
import hashlib
import json
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    return subprocess.check_output(args,text=True)


def frame_hashes(path,receipt):
    data=run(['ffmpeg','-v','error','-i',str(path),'-an','-f','framehash','-hash','sha256','-'])
    receipt.write_text(data)
    return [line.split(',')[-1].strip() for line in data.splitlines() if line and not line.startswith('#')]


def main():
    w=Path('data/workspace/wavefield-v1');r=w/'revisions/v3';qa=r/'qa'
    opening=w/'edit/picture-v3-opening.mp4';tail=r/'retained-v2-tail.mp4';base=w/'edit/picture-v2.mp4'
    output=w/'edit/picture-v3.mp4'
    assert not output.exists(),'Refuse to replace an existing source'
    op=json.loads(opening.with_suffix('.render.json').read_text())
    bp=json.loads(base.with_suffix('.render.json').read_text())
    assert op['frames']==250 and op['startFrame']==0 and op['fps']==30
    assert sha(opening)==op['sha256'] and sha(base)==bp['sha256']
    manifest=r/'concat.txt'
    manifest.write_text("file '../../edit/picture-v3-opening.mp4'\nfile 'retained-v2-tail.mp4'\n")
    command=['ffmpeg','-v','warning','-n','-f','concat','-safe','0','-i',str(manifest),
             '-map','0:v:0','-c:v','copy','-color_primaries','bt709','-color_trc','bt709',
             '-colorspace','bt709','-color_range','tv','-movflags','+faststart',str(output)]
    start=time.monotonic()
    p=subprocess.run(command,check=True,capture_output=True,text=True)
    (qa/'join-ffmpeg.log').write_text(p.stderr)
    assert 'non-monoton' not in p.stderr.lower(),'Unexpected timestamp correction'
    probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(output)]))
    v=probe['streams'][0]
    assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_read_frames']))==(1080,1920,'30/1',720)
    assert float(v['duration'])==24 and float(v['start_time'])==0
    frames=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_frames',
                          '-show_entries','frame=pts','-of','json',str(output)]))['frames']
    assert v['time_base']=='1/15360' and [f['pts'] for f in frames]==[i*512 for i in range(720)]
    head_hashes=frame_hashes(opening,qa/'opening.framehash')
    joined_hashes=frame_hashes(output,qa/'joined.framehash')
    tail_hashes=[line.split(',')[-1].strip() for line in (qa/'v2-tail.framehash').read_text().splitlines()
                 if line and not line.startswith('#')]
    assert len(head_hashes)==250 and len(tail_hashes)==470
    assert joined_hashes==head_hashes+tail_hashes,'Decoded picture changed at the join'
    head_metrics=json.loads((w/'simulation/picture-v3-opening-frame-metrics.json').read_text())
    tail_metrics=json.loads((w/'simulation/picture-v2-frame-metrics.json').read_text())
    metrics=[{**m,'origin':'recomputed-v3-opening'} for m in head_metrics]
    metrics += [{**m,'origin':'retained-v2-picture'} for m in tail_metrics if m['frame']>=250]
    (w/'simulation/picture-v3-frame-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    report={'artifact':str(output.relative_to(w)),'sha256':sha(output),'frames':720,'fps':30,
            'width':1080,'height':1920,'fieldWidth':1080,'fieldHeight':1920,'revision':'v3',
            'method':'Recomputed opening; stream-copied v2 tail at its frame-250 keyframe',
            'sourceRanges':[{'path':str(opening.relative_to(w)),'sha256':op['sha256'],'start':0,'frames':250},
                            {'path':str(base.relative_to(w)),'sha256':bp['sha256'],'start':250,'frames':470}],
            'sourceImages':op['sourceImages'],'recipeSha256':sha(__file__),
            'openingRecipeSha256':op['recipeSha256'],'fieldCodeSha256':op['fieldCodeSha256'],
            'maxPropagationEnergyRelativeError':max(m['energyRelativeErrorMax'] for m in metrics),
            'maxCrossIdentityError':max(m['crossIdentityMaxError'] for m in metrics),
            'allFinite':all(m['finite'] for m in metrics),'allTailFramesDecodedIdentical':True,
            'allOpeningFramesDecodedIdentical':True,'exactFrameTimestamps':True,
            'openingRenderSeconds':op['renderSeconds'],'joinAndVerificationSeconds':round(time.monotonic()-start,2),
            'openingZoomIncrementRatio':2/3,'ratioHoldThroughSeconds':3,'rejoinV2AtFrame':250}
    output.with_suffix('.render.json').write_text(json.dumps(report,indent=2)+'\n')
    (qa/'picture-preservation.json').write_text(json.dumps({'passed':True,'joinFrame':250,
        'verifiedOpeningFrames':250,'verifiedUnchangedV2TailFrames':470,'exactFrameTimestamps':True,
        'sourceSha256':report['sha256'],'baseSha256':bp['sha256'],'command':command},indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
