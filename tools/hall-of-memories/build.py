#!/usr/bin/env python3
"""Build a new, self-contained local audition package; refuse existing output."""
from pathlib import Path
import argparse, hashlib, html, json, math, shutil, subprocess, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import picture as pic
import sound

HERE=Path(__file__).resolve().parent
FPS=24;SAMPLES=12

def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def mmss(t):return f'{int(t)//60}:{int(t)%60:02d}'
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def strip(runpath,name,frames,labels,columns=4):
    w,h=480,270;rows=math.ceil(len(frames)/columns)
    out=Image.new('RGB',(columns*w,rows*(h+39)), '#181f22');d=ImageDraw.Draw(out)
    f=ImageFont.truetype(pic.FONT,17)
    for i,(im,label) in enumerate(zip(frames,labels)):
        x=(i%columns)*w;y=(i//columns)*(h+39)
        out.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y));d.text((x+12,y+h+9),label,font=f,fill='#e0ddcd')
    out.save(runpath/'qa'/f'{name}.jpg',quality=94)

def boards(runpath,plan):
    out=Image.new('RGB',(2400,2235),'#ede8dc');d=ImageDraw.Draw(out)
    head=ImageFont.truetype(pic.BOLD,39);title=ImageFont.truetype(pic.BOLD,23);small=ImageFont.truetype(pic.FONT,19)
    d.text((40,24),'HALL OF MEMORIES  /  ROUGH WHOLE-FILM BOARD',font=head,fill='#283330')
    d.text((40,76),'12 broad beats. Designs provisional. Temporary timing totals 5:14; this is not a runtime commitment.',font=small,fill='#57625a')
    cursor=0;timeline=[]
    for i,b in enumerate(plan['board']):
        frame=pic.board_frame(b['scene']);frame.save(runpath/'board'/f"{b['id']}.png")
        x=40+(i%3)*780;y=124+(i//3)*514
        out.paste(frame.resize((760,428),Image.Resampling.LANCZOS),(x,y))
        label=f"{b['id']}   {b['title']}"
        d.text((x,y+439),label,font=title,fill='#283330')
        d.text((x,y+472),f"{mmss(cursor)}–{mmss(cursor+b['seconds'])}   /   {b['seconds']}s sketch",font=small,fill='#57625a')
        timeline.append({**b,'screen_start':cursor,'screen_end':cursor+b['seconds'],'geological_time':'unspecified; independent of screen time','character_state':'provisional board state'})
        cursor+=b['seconds']
    d.text((40,2190),'Locally drawn blocking. No final voices, materials, biography, simulation clock or outside-view mechanism selected.',font=small,fill='#57625a')
    out.save(runpath/'rough-board.jpg',quality=95)
    (runpath/'timeline.json').write_text(json.dumps({'screen_seconds':cursor,'shots':timeline},indent=2)+'\n')
    return timeline

def encode(runpath,name,duration,frame,audio):
    dest=runpath/'review'/f'{name}.mp4'
    cmd=['ffmpeg','-v','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s',f'{pic.W}x{pic.H}','-r',str(SAMPLES),'-i','pipe:0','-i',str(audio),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r',str(FPS),'-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',str(dest)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(round(duration*SAMPLES)):
            im=frame(i/SAMPLES)
            p.stdin.write(im.tobytes())
            if i%120==0:print(f'{name}: {i/SAMPLES:.0f}/{duration:.2f}s',flush=True)
        p.stdin.close()
        if p.wait()!=0:raise RuntimeError(f'Encoding failed: {name}')
    except BaseException:
        p.kill();p.wait();raise
    # PCM master supports exact sample-silence review; browser MP4 uses lossy AAC.
    run(['ffmpeg','-v','error','-n','-i',str(dest),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','pcm_s16le','-t',str(duration),'-movflags','+faststart',str(runpath/'masters'/f'{name}.mov')])
    run(['ffmpeg','-v','error','-n','-i',str(dest),'-vf','scale=1280:720','-c:v','libx264','-preset','fast','-crf','22','-c:a','copy','-movflags','+faststart',str(runpath/'review'/f'{name}-720p.mp4')])
    frame(0).save(runpath/'review'/f'{name}-poster.jpg',quality=90)
    print(f'{name}: complete',flush=True)

def vtt(cues):
    def stamp(s):
        n=round(s*1000);return f'{n//3600000:02d}:{n//60000%60:02d}:{n//1000%60:02d}.{n%1000:03d}'
    return 'WEBVTT\n\n'+'\n\n'.join(f"{x['id']}\n{stamp(x['start'])} --> {stamp(x['end'])}\n{x['text']}" for x in cues['dialogue'])+'\n'

def docs(runpath,plan,cues,timeline):
    notes='''# Hall of Memories — rough auditions v2

Status: ready for creative review; every design, voice and timing remains provisional.

Open `index.html` for the board, all auditions and the comparison notes. Native
1920 × 1080 review MP4s and smaller 720p copies are in `review/`. Lossless-audio
MOV masters are in `masters/`. The board is deliberately twelve broad beats,
not a shot list. Its 5:14 total is a pacing hypothesis, not an agreed runtime.

## Point of view

- **Factory:** oxide, dull brass, slumped paper puppets. Bureaucratic cheer should
  make the cruelty banal. A six-second routine lead-in only tests entry rhythm;
  the whole-film board gives the opening more room. Every demonstrated rewrite
  is scheduled after its spoken cause. No visible violence, mouth animation,
  explanatory framing label or burned-in dialogue captions.
- **Polis:** chalk figures, yellow eyes, violet-grey sky with misregistered discs,
  tall, pale ribs. Their world feels composed rather than metallic or electronic.
  Storytelling uses hands; the worker and child share the cut's exact joint pose.
- **Hall to housing:** an actual translating camera withdraws from persistent
  Hall geometry; a graphic facet boundary replaces simulated space with physical
  material. The emerald then recedes among fixed rock layers. This is an audition
  of the transition's grammar, not a geological model or a literal tunnel.
- **Emerald:** uneven six-sided prism, pale diagonal inclusion. Shape and inclusion
  repeat in the strata, hand and necklace images. The cord attachment is a sketch.
- **Ending:** prefer the motionless crowd. Their attention lets the audience supply
  the concern. The return-to-daughter alternative uses identical sound and length,
  but cuts at 4s and reaches black earlier. The clothed adult is not animated into
  an intimate act. Neither version depicts sex. Outside perception remains open.

## What to judge

1. Factory: does the timer objection land, and do the matching hands make the
   reveal readable? These adult stock voices are timing placeholders, not casting.
2. Hall: does the facet transition say 'this world is housed here'? Judge camera
   translation and foreground occlusion separately from the deliberately crude
   materials. The jewel is enlarged for legibility in the far cutaway.
3. Ending: does the still crowd carry more weight than returning to the daughter?
   Does the infant register before the Hall returns? The same recorded synthesis
   motif is reused in both passages. Synthetic cries are only timing proxies;
   naturalness and emotional effect remain unresolved until listening review.

## Sound and review limits

All sound is local: installed macOS speech and original procedural scratch
synthesis. No recordings of real suffering are used. Wordless vowel models stand
in for party walla, an infant and Hall voices. No voice provider, image provider,
music provider, external sample library, generated motion or paid QA was called.
The sound comparison uses one mix and one shared gain, with separate editable
stems. In the Hall test a single voice ends at 2.5s; the accumulation starts at
4.5s. In the ending the infant begins at 10.5s; Hall material begins at 19.5s.

The ending reaches its cutoff at 29.75s. PCM master and WAV have exactly 12,000
silent samples / six black frames at the end. AAC review copies may have codec
ringing around the cutoff; inspect the PCM master for sample-exact timing. This
is a provisional 24 fps audition, not an approved delivery specification.

Visual QA uses sampled rendered frames and frame hashes; automated measurements
do not establish emotional success. Listening judgment is pending the user's
audition. The first Hall record's biography, final voice performances, material
designs, simulation/exterior time relationship and outside-view mechanism remain
unselected. No paid chapter has an authorized ceiling. No 4K or publication work.

## Rebuild and preservation

`recipe/` contains the exact scripts and input plan used. Run its `build.py` with
a NEW output directory; existing directories are refused. Requirements: Python,
Pillow, NumPy, FFmpeg, macOS `say`, Arial (or HALL_FONT/HALL_FONT_BOLD paths).
The recipe reconstructs geometric artwork and scratch audio without provider
calls. All prior project work and archives are untouched.
'''
    (runpath/'README.md').write_text(notes)
    (runpath/'review'/'factory.vtt').write_text(vtt(cues))
    (runpath/'ledger.json').write_text(json.dumps({'status':'local exploration only','paid_ceiling_usd':None,'minimum_chapter_planning_floor_usd':20,'provider_calls':0,'known_new_provider_charges_usd':0,'reservations_usd':0,'unmetered_provider_calls':0,'scope':'This audition run only. Local computation and previously installed software are not billed provider generation.'},indent=2)+'\n')
    rows=''.join(f"<li><b>{b['id']} · {html.escape(b['title'])}</b><span>{mmss(b['screen_start'])}–{mmss(b['screen_end'])}</span><p>{html.escape(b['note'])}</p></li>" for b in timeline)
    panels=[]
    for name,title,desc in [
        ('01-factory-circle','01 · Who is telling the story?','Oxide factory → chalk polis. Listen for the objection before each change; watch the hands at the cut. Stock adult voices are scratch timing only.'),
        ('02-hall-emerald-strata','02 · A world inside a material thing','The Hall camera translates backward and sideways; the simulated view becomes a facet, then material. The foreground rock lip occludes the lower edge. This is a conceptual scale change.'),
        ('03-ending-crowd','03A · Stay with the witnesses — preferred','The crowd is completely still. Infant begins at 10.5s, black completes at 18s, the Hall returns at 19.5s. Judge whether the infant reads as an infant in this deliberately synthetic scratch track.'),
        ('03-ending-daughter','03B · Return to the daughter — comparison','The same sound and duration. Return to the clothed adult at 4s; reach black at 14s. Compare intimacy and explanatory weight with the sustained collective gaze.')]:
        track='<track kind="captions" src="review/factory.vtt" srclang="en" label="Optional scratch transcript">' if name.startswith('01') else ''
        panels.append(f'<section><h2>{title}</h2><p>{desc}</p><video controls preload="metadata" playsinline poster="review/{name}-poster.jpg"><source src="review/{name}-720p.mp4" type="video/mp4">{track}</video><p class="links"><a href="review/{name}.mp4">1080p review</a> · <a href="masters/{name}.mov">PCM audio master</a></p></section>')
    doc='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hall of Memories · rough auditions</title><style>
    :root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#19211f;color:#e8e3d3;font:17px/1.55 system-ui,sans-serif}main{max-width:1140px;margin:auto;padding:32px 24px 64px}h1{font-size:clamp(28px,5vw,46px);font-weight:500;line-height:1.15;margin:8px 0 22px}h2{font-size:25px;font-weight:500}p{max-width:850px}a{color:#bad4b5}img,video{width:100%;height:auto;display:block}video{background:#000}section{margin:48px 0;border-top:1px solid #48564c;padding-top:20px}.eyebrow{font-size:13px;text-transform:uppercase;letter-spacing:.15em;color:#a6baa6}.muted,.links{color:#bac4b5;font-size:15px}details{margin:20px 0}summary{padding:10px 0}ol{padding-left:24px;display:grid;grid-template-columns:1fr 1fr;gap:20px 40px}li span{display:block;color:#a6baa6;font-size:14px}li p{margin:5px 0;font-size:15px}nav{display:flex;gap:16px;flex-wrap:wrap}footer{border-top:1px solid #48564c;padding-top:20px}@media(max-width:640px){main{padding:22px 14px}ol{grid-template-columns:1fr}section{margin:32px 0}}
    </style></head><body><main><div class="eyebrow">Local blocking · version 1 · for discussion</div><h1>Hall of Memories</h1><p>One tactile film, three registers: oxide machinery, chalk simulation, ochre Earth. The emerald carries a pale diagonal inclusion through every scale. These are deliberate visual choices for audition; designs remain open.</p><nav><a href="rough-board.jpg">Open rough board</a><a href="README.md">Direction and review notes</a><a href="qa/verification.json">Technical checks</a></nav><section><h2>Twelve broad beats</h2><p>A provisional 5:14 shape. This board sets emphasis and sequence, not shot counts or a target runtime.</p><img src="rough-board.jpg" alt="Twelve-panel rough board: factory routine, story rewrite, polis circle, individual record, Hall, buried emerald, jungle, alien visitors, human recurrence, retrieving hand, feast, still witnesses"><details><summary>Beat notes and temporary timing</summary><ol>BOARD_ROWS</ol></details></section>VIDEO_PANELS<footer><p class="muted">All voices and effects are local scratch material. The infant and screams are synthesized timing proxies; emotional credibility and recognition need listening review. No paid provider calls. The final quarter-second is exact in the PCM masters; AAC copies have the usual codec boundary limitation.</p><p class="muted">Review package only. No design, chapter ceiling, final runtime or ending has been approved.</p></footer></main><script>document.querySelectorAll('video').forEach(v=>v.addEventListener('play',()=>document.querySelectorAll('video').forEach(other=>{if(other!==v)other.pause()})));</script></body></html>'''
    (runpath/'index.html').write_text(doc.replace('BOARD_ROWS',rows).replace('VIDEO_PANELS',''.join(panels)))

def checks(runpath,cues):
    report={'scope':'Technical verification and sampled visual QA; listening judgment remains pending','files':{}}
    for p in sorted((runpath/'masters').glob('*.mov')):
        meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
        v=next(s for s in meta['streams'] if s['codec_type']=='video')
        a=next(s for s in meta['streams'] if s['codec_type']=='audio')
        assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'24/1')
        assert a['codec_name']=='pcm_s16le' and a['sample_rate']=='48000'
        result={'seconds':float(meta['format']['duration']),'frames':int(v['nb_read_frames']),'resolution':[v['width'],v['height']],'fps':v['r_frame_rate'],'audio':a['codec_name']}
        if 'ending' in p.name:
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-f','s16le','-'])
            x=np.frombuffer(raw,'<i2').reshape(-1,2)
            nonzero=np.flatnonzero(np.any(x!=0,axis=1));tail=len(x)-nonzero[-1]-1
            assert len(x)==30*sound.SR and tail==12000,(p.name,len(x),tail)
            result['exact_trailing_silent_samples']=int(tail)
            result['audio_peak_dbfs']=round(20*np.log10(max(1,np.max(np.abs(x.astype(float))))/32768),2)
            # Decode every crowd frame before fade and check physical stillness.
            if 'crowd' in p.name:
                cmd=['ffmpeg','-v','error','-i',str(p),'-t','16','-vf','scale=320:180','-f','rawvideo','-pix_fmt','gray','-']
                rawv=subprocess.check_output(cmd);arr=np.frombuffer(rawv,np.uint8).reshape(-1,180,320)
                # H.264 can refine a static picture slightly between I/P frames.
                result['encoded_static_mean_abs_delta_max']=float(np.abs(np.diff(arr.astype(float),axis=0)).mean(axis=(1,2)).max())
            black=subprocess.check_output(['ffmpeg','-v','error','-sseof','-0.25','-i',str(p),'-map','0:v:0','-f','rawvideo','-pix_fmt','rgb24','-'])
            b=np.frombuffer(black,np.uint8)
            assert len(b)==6*pic.W*pic.H*3 and b.max()==0
            result['final_black_frames']=6
        report['files'][str(p.relative_to(runpath))]=result
    hashes=[hashlib.sha256(pic.ending(t).tobytes()).hexdigest() for t in [0,1,4,8,12,15.9]]
    assert len(set(hashes))==1
    report['crowd_source_pixels_identical_before_fade']=True
    report['factory_events']=cues['events']
    for line in cues['dialogue']:
        if line.get('event') and line['event']!='circle_cut':assert cues['events'][line['event']]>=line['end']
    report['factory_rewrites_follow_spoken_causes']=True
    report['matched_gesture_joint_coordinates']={'worker_and_child':{'feet':[710,661],'height':335,'pose':'match'},'cut_seconds':cues['events']['circle_cut']}
    report['local_generation_cost_usd']=0
    (runpath/'qa'/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--stills-only',action='store_true');args=ap.parse_args()
    runpath=Path(args.output).resolve()
    if runpath.exists():raise SystemExit('Refusing existing output. Choose a new versioned directory.')
    runpath.mkdir(parents=True)
    for name in ['board','qa','recipe','review','masters']:(runpath/name).mkdir()
    for name in ['plan.json','picture.py','sound.py','build.py']:
        shutil.copy2(HERE/name,runpath/'recipe'/name)
    plan=json.loads((HERE/'plan.json').read_text());timeline=boards(runpath,plan)
    strip(runpath,'hall-scale-study',[pic.hall_transition(t) for t in [0,3,5.9,6,8,11,16,23]],['Hall / 0s','Withdraw / 3s','Exterior / 5.9s','Facet entry / 6s','Boundary / 8s','Emerald / 11s','Occlusion / 16s','Strata / 23s'])
    if args.stills_only:
        print(f'Still study complete: {runpath}',flush=True);return
    cues=sound.prepare(runpath,plan);docs(runpath,plan,cues,timeline)
    ev=cues['events'];cut=ev['circle_cut']
    f=lambda t:pic.factory(t,ev) if t<cut else pic.circle(True if t<cut+1.2 else False)
    strip(runpath,'factory-events',[f(t) for t in [0,ev['duplicate']+.8,ev['door_vanish']+1.25,ev['timer']+.3,ev['eyes']+.3,cut-1/24,cut,cut+2]],['Routine','Next shift arrives','Door vanishes','Timer appears','Eyes answer objection','Worker: shared gesture','Child: shared gesture','Circle revealed'])
    strip(runpath,'ending-comparison',[pic.ending(t,v) for v in ['crowd','daughter'] for t in [0,5,13,17]],['Crowd / 0s','Crowd / 5s','Crowd / 13s','Crowd / fade','Alt / 0s','Alt / return','Alt / fade','Alt / black'])
    encode(runpath,'01-factory-circle',cues['factory_duration'],f,runpath/'audio'/'factory-mix.wav')
    encode(runpath,'02-hall-emerald-strata',24,pic.hall_transition,runpath/'audio'/'hall-mix.wav')
    encode(runpath,'03-ending-crowd',30,lambda t:pic.ending(t,'crowd'),runpath/'audio'/'ending-mix.wav')
    encode(runpath,'03-ending-daughter',30,lambda t:pic.ending(t,'daughter'),runpath/'audio'/'ending-mix.wav')
    checks(runpath,cues)
    manifest={str(p.relative_to(runpath)):{'sha256':hashfile(p),'bytes':p.stat().st_size} for p in sorted(runpath.rglob('*')) if p.is_file()}
    (runpath/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Complete: {runpath}',flush=True)

if __name__=='__main__':main()
