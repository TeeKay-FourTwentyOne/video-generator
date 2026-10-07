#!/usr/bin/env python3
"""Author a whole Hall timeline, local speech and independent original voices."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import numpy as np
from polis_audio import SR, read, write, edge, put, stamp
from sound import vowel
HERE=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();audio=out/'audio'
    if audio.exists():raise SystemExit('Refusing existing audio.')
    (audio/'dialogue').mkdir(parents=True);(audio/'voices').mkdir()
    retained={}
    for root,names in {
      'polis-draft-v1':['timeline.json','animation-v3/polis-animation.blend','edit-v2/masters/polis-scene-draft.mov','edit-v2/review/polis-scene-draft-1080p.mp4'],
      'polis-invitation-v1':['timeline.json','animation-v1/polis-invitation-animation.blend','edit-v1/masters/polis-invitation.mov','edit-v1/review/polis-invitation-1080p.mp4','edit-v1/review/polis-conversation-and-invitation-1080p.mp4']}.items():
        for name in names:retained[f'{root}/{name}']=sha(out.parent/root/name)
    (out/'baseline-preservation.json').write_text(json.dumps(retained,indent=2)+'\n')
    script=json.loads((HERE/'polis_hall.json').read_text());lines=[];shots=[];clips={};cursor=0
    for b in script['blocks']:
        start=cursor
        if 'text' in b:
            cast=script['cast'][b['speaker']];p=audio/'dialogue'/f"{b['id']}.aiff"
            subprocess.run(['say','-v',cast['voice'],'-r',str(cast['rate']),'-o',str(p),b['text']],check=True)
            x=read(p,f"aresample=48000,asetrate={round(SR*cast['pitch'])},aresample=48000,atempo={1/cast['pitch']},highpass=f=85,lowpass=f=8500")
            active=np.flatnonzero(np.abs(x)>.002)
            if not len(active):raise RuntimeError('Empty speech')
            x=edge(x[max(0,active[0]-1800):min(len(x),active[-1]+2400)])
            x*=.34/max(.001,float(np.abs(x).max()));p=p.with_suffix('.wav');write(p,x);clips[b['id']]=x
            at=math.ceil((start+b['before'])*8)/8;end=at+len(x)/SR
            lines.append({**b,'start':at,'end':end,'file':str(p.relative_to(out))})
            cursor=math.ceil((end+b['after'])*8)/8
        else:cursor=start+b['duration']
        shots.append({'id':b['id'],'shot':b['shot'],'start':start,'end':cursor})
    duration=cursor;by={b['id']:b for b in shots};n=round(duration*SR)
    stems={k:np.zeros((n,2),np.float32) for k in ['dialogue','record','first-voice','accumulation','atmosphere','foley']}
    for l in lines:
        x=clips[l['id']];pan=script['cast'][l['speaker']]['pan'];s=stems['record' if l['speaker'] in ['mara','father'] else 'dialogue']
        put(s,x,l['start'],pan)
        for delay,gain in ([(.065,.04)] if s is stems['record'] else [(.12,.085),(.27,.04)]):put(s,x*gain,l['start']+delay,-pan)
    rng=np.random.default_rng(928);t=np.arange(n)/SR
    retreat=by['H14']['start'];jewel=by['H16']['start']
    room_env=np.interp(t,[0,5,by['H03']['start'],by['H07']['end'],by['H08']['start'],retreat,jewel,duration],[1,1,.45,.45,1,1,.13,.1])
    noise=rng.normal(0,1,n+1000);cs=np.r_[0,np.cumsum(noise)];wind=(cs[1001:]-cs[:-1001])/1001
    bed=(.016*wind+.0018*np.sin(2*np.pi*83*t)+.0012*np.sin(2*np.pi*124.5*t))*room_env
    stems['atmosphere'][:,0]=bed;stems['atmosphere'][:,1]=bed*.95
    for person,offset,period,level in [('elder',0,1.125,.025),('story',.34,.875,.017),('challenge',.14,.875,.017),('quiet',.60,.875,.014)]:
        for at in np.arange(.25+offset,5.8,period/2):
            tt=np.arange(round(.19*SR))/SR;x=(np.sin(2*np.pi*153*tt)+rng.normal(0,.21,len(tt)))*np.exp(-tt*34)
            put(stems['foley'],edge(x,120)*level,float(at),script['cast'][person]['pan'])
    for block in ['H03','H07']:
        tt=np.arange(round(.3*SR))/SR
        x=(np.sin(2*np.pi*1430*tt)+.24*np.sin(2*np.pi*3221*tt))*np.exp(-tt*24)*.019
        put(stems['foley'],edge(x,100),by[block]['start']+.75,-.15)
    # A synthetic adult open vowel with an uneven respiratory envelope. This is
    # original scratch synthesis, not recorded suffering or a cloned performance.
    def voice(length,base,seed):
        x=vowel(length,base,seed);tt=np.arange(len(x))/SR
        x*=.78+.14*np.sin(2*np.pi*2.1*tt+seed)+.08*np.sin(2*np.pi*7.4*tt)
        return edge(x,1200)
    first=voice(4.25,247,928);write(audio/'voices'/'mara-whole-life.wav',first)
    first_at=by['H10']['start']+.5
    put(stems['first-voice'],first*.62,first_at,0)
    for delay,gain in [(.16,.18),(.38,.09),(.67,.035)]:put(stems['first-voice'],first*gain,first_at+delay,-.2)
    voice_cues=[{'id':'MARA-WHOLE','at':first_at,'duration':len(first)/SR,'file':'audio/voices/mara-whole-life.wav','role':'solitary derived voice'}]
    many=by['H13']['start']
    for i,(offset,base) in enumerate([(0,247),(2.5,174),(5,329),(7,207),(8.5,384),(10,138),(11.1,293),(12,433),(12.8,228),(13.5,352),(14,186),(14.4,270)]):
        length=duration-(many+offset);x=voice(length,base,930+i)
        # Individual onsets stay readable; later sound does not become louder
        # without bound. Remove upper density progressively at the jewel reveal.
        tt=np.arange(len(x))/SR+many+offset
        env=np.interp(tt,[many,retreat,jewel,jewel+3,duration],[.32,.72,.3,.085,.045])
        x*=env;name=f'voice-{i+1:02d}.wav';write(audio/'voices'/name,x)
        put(stems['accumulation'],x*.20,many+offset,(i%5-2)*.35)
        voice_cues.append({'id':f'WHOLE-{i+1:02d}','at':many+offset,'duration':len(x)/SR,'file':f'audio/voices/{name}','role':'derived voice accumulation'})
    for s in stems.values():
        s[:480]*=np.linspace(0,1,480)[:,None];s[-480:]*=np.linspace(1,0,480)[:,None]
    mix=sum(stems.values());peak=float(np.abs(mix).max())
    if peak>.75:raise RuntimeError(f'Unexpected mix peak {peak}')
    for name,s in stems.items():write(audio/f'{name}.wav',s)
    write(audio/'mix.wav',mix)
    check_start=by['H09']['start'];check_end=by['H12']['end']
    write(audio/'first-voice-check.wav',mix[round(check_start*SR):round(check_end*SR)])
    tl={**script,'duration':duration,'lines':lines,'shots':shots,'voices':voice_cues,'cues':{'first_voice':first_at,'many':many,'withdraw':retreat,'facet':by['H15']['start'],'jewel':jewel},'peak_dbfs':float(20*np.log10(peak)),
        'provenance':'Local CG, installed synthetic speech and original procedural wordless voices; all fictional and temporary. No provider calls.'}
    (out/'timeline.json').write_text(json.dumps(tl,indent=2)+'\n')
    caps=['WEBVTT',''];screen=['# One whole life','',f'Duration: {duration:.3f} seconds. Temporary local voices.','']
    for s in shots:
        screen.extend([f"## {s['id']} / {s['shot']} ({s['start']:.3f}-{s['end']:.3f}s)",''])
        for l in lines:
            if l['id']==s['id']:
                caps.extend([l['id'],f"{stamp(l['start'])} --> {stamp(l['end'])}",l['text'],''])
                screen.extend([f"{l['speaker']}: {l['text']}",''])
    (out/'dialogue.vtt').write_text('\n'.join(caps));(out/'screenplay.md').write_text('\n'.join(screen))
    (out/'ledger.json').write_text(json.dumps({'scope':script['scope'],'new_provider_calls':0,'new_provider_charges_usd':0,'prior_unmetered_image_calls':15,'prior_exact_cost':'unknown','chapter_ceiling':None,'status':'local native drafting only'},indent=2)+'\n')
    print(json.dumps({'duration':duration,'peak_dbfs':tl['peak_dbfs'],'shots':shots},indent=2))
if __name__=='__main__':main()
