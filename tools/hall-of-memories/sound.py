"""Original local scratch synthesis and installed macOS speech. No remote calls."""
from pathlib import Path
import json, math, subprocess, wave
import numpy as np

SR=48000

def write(path,x):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=np.rint(np.clip(x,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1 if data.ndim==1 else data.shape[1]);w.setsampwidth(2);w.setframerate(SR);w.writeframes(data.tobytes())

def read(path):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ar',str(SR),'-ac','1','-f','f32le','-'])
    return np.frombuffer(raw,dtype='<f4').copy()

def edge(x,seconds=.015):
    x=x.copy();n=min(round(seconds*SR),len(x)//2)
    if n:
        x[:n]*=np.linspace(0,1,n);x[-n:]*=np.linspace(1,0,n)
    return x

def norm(x,amp=.3): return x*amp/max(.00001,np.max(np.abs(x)))

def put(dst,x,at,pan=0,amp=1):
    start=round(at*SR);n=min(len(x),len(dst)-start)
    if n<=0:return
    if x.ndim==1:x=np.c_[x,x]
    dst[start:start+n]+=x[:n]*np.array([1-max(0,pan)*.5,1+min(0,pan)*.5])*amp

def hit(freq=180,duration=.17,seed=0):
    t=np.arange(round(duration*SR))/SR;rng=np.random.default_rng(seed)
    return edge((np.sin(2*np.pi*freq*t)+.3*np.sin(2*np.pi*freq*2.31*t)+rng.normal(0,.19,len(t)))*np.exp(-t*25),.003)

def vowel(duration,base,seed=1,baby=False):
    """A wordless vowel model for timing, not a recorded human performance."""
    n=round(duration*SR);t=np.arange(n)/SR;rng=np.random.default_rng(seed)
    freq=base*(1+.15*np.sin(np.pi*t/duration)+.022*np.sin(t*2*np.pi*5.8))
    phase=np.cumsum(freq)*2*np.pi/SR
    formants=[(1150,280),(2850,420),(4400,500)] if baby else [(770,200),(1210,210),(2800,430)]
    x=np.zeros(n)
    for k in range(1,25):
        hz=k*freq
        weight=.07/k+sum(np.exp(-.5*((hz-f)/bw)**2)*a for (f,bw),a in zip(formants,[1,.65,.32]))/np.sqrt(k)
        x+=weight*np.sin(k*phase+rng.uniform(-.06,.06))
    noise=rng.normal(0,1,n)
    x+=noise*.06
    env=np.sin(np.pi*np.arange(n)/n)**.65
    if baby:env*=.76+.24*np.sin(2*np.pi*8*t)**2
    return norm(edge(x*env,.045),.45)

def prepare(run,plan):
    audio=run/'audio';(audio/'dialogue').mkdir(parents=True)
    lines=[];events={};cursor=6.0
    voices={'storyteller':'Samantha','challenger':'Karen'}
    for item in plan['dialogue']:
        raw=audio/'dialogue'/f"{item['id']}.aiff"
        subprocess.run(['say','-v',voices[item['speaker']],'-r','176','-o',str(raw),item['text']],check=True)
        x=read(raw)
        active=np.flatnonzero(np.abs(x)>.002)
        if not len(active):raise RuntimeError('Local speech produced silence')
        x=x[max(0,active[0]-2400):min(len(x),active[-1]+2400)]
        x=norm(edge(x),.34)
        path=audio/'dialogue'/f"{item['id']}.wav";write(path,x)
        end=cursor+len(x)/SR
        line={**item,'start':cursor,'end':end,'file':str(path.relative_to(run)),'source':'installed macOS speech; adult placeholder voice'}
        lines.append(line)
        if item.get('event')=='circle_cut':events['circle_cut']=math.floor((cursor-.12)*12)/12
        elif item.get('event'):events[item['event']]=math.ceil(end*6)/6
        cursor=end+item['gap_after']
    duration=math.ceil(cursor*12)/12
    dialog=np.zeros((round(duration*SR),2));machine=np.zeros_like(dialog)
    for line in lines:put(dialog,read(run/line['file']),line['start'], -.1 if line['speaker']=='storyteller' else .2)
    t=np.arange(len(machine))/SR
    motor=(np.sin(2*np.pi*57*t)+.15*np.sin(2*np.pi*114*t))*.009
    motor*=np.minimum(1,np.maximum(0,(events['circle_cut']-t)/.2))
    machine+=motor[:,None]
    for at in [1,3,5]:put(machine,norm(hit(91,.32,int(at)),.17),at,-.25)
    for name,f in [('duplicate',170),('door_vanish',130),('timer',750),('eyes',1030)]:put(machine,norm(hit(f,.12),.06),events[name],.35)
    write(audio/'factory-dialogue.wav',dialog);write(audio/'factory-machinery.wav',machine)
    # A repeatable motif: one voice, a solitary pause, then accumulating lives.
    first=vowel(1.5,285,91)
    write(audio/'hall-first-voice.wav',first)
    chorus=np.zeros((12*SR,2))
    for j,(at,base) in enumerate([(0,285),(.8,209),(1.7,365),(2.6,247),(3.4,412),(4.5,173),(5.3,329),(6,463),(7.1,232)]):
        voice=vowel(12-at,base,91+j)
        write(audio/f'hall-voice-{j+1:02d}.wav',voice)
        put(chorus,voice,at,(j%3-1)*.65,.14)
    env=np.linspace(.32,1,len(chorus))
    chorus*=env[:,None]
    write(audio/'hall-chorus.wav',chorus)
    hall_one=np.zeros((24*SR,2));hall_many=np.zeros_like(hall_one);room=np.zeros_like(hall_one)
    put(hall_one,first,1.0,0,.6)
    put(hall_many,chorus,4.5,0,.8)
    put(hall_many,chorus,15.0,0,.42)
    room_t=np.arange(24*SR)/SR
    room+=np.sin(2*np.pi*84*room_t)[:,None]*.005
    hall_many[-SR:]*=np.linspace(1,0,SR)[:,None]
    write(audio/'hall-single.wav',hall_one);write(audio/'hall-accumulation.wav',hall_many);write(audio/'hall-room.wav',room)
    # Party is wordless walla, irregular table percussion and cup taps.
    party=np.zeros((30*SR,2));infant=np.zeros_like(party);recall=np.zeros_like(party)
    rng=np.random.default_rng(771)
    for j in range(46):
        at=float(rng.uniform(0,11));v=vowel(float(rng.uniform(.35,1.0)),float(rng.uniform(110,235)),j)
        put(party,v,at,float(rng.uniform(-1,1)),.08)
    for j,at in enumerate(np.arange(.1,11,.57)):
        put(party,norm(hit(130+(j%4)*220,.14,j),.08),float(at),float(rng.uniform(-1,1)))
    for j,at in enumerate([10.5,12.2,14.1,16.0,18.1]):
        v=vowel([1.15,1.30,1.32,1.45,1.30][j],500+[25,-20,40,-10,15][j],300+j,True)
        put(infant,v,at,.04,.47)
        # Brief airy in-breath after each wail makes the respiratory rhythm explicit.
        breath=edge(norm(rng.normal(0,1,round(.18*SR)),.023),.05)
        put(infant,breath,at+len(v)/SR+.09,0,.65)
    put(recall,chorus,19.5,0,1)
    cutoff=round(29.75*SR)
    for stem in [party,infant,recall]:
        fade=round(.006*SR);stem[cutoff-fade:cutoff]*=np.linspace(1,.002,fade)[:,None];stem[cutoff:]=0
    write(audio/'ending-party.wav',party);write(audio/'ending-infant-synthetic.wav',infant);write(audio/'ending-hall-return.wav',recall)
    mixes={'factory':dialog+machine,'hall':hall_one+hall_many+room,'ending':party+infant+recall}
    # One shared gain across auditions; never independently normalize chapters.
    gain=min(1,10**(-5/20)/max(float(np.max(np.abs(x))) for x in mixes.values()))
    for name,x in mixes.items():
        x=x*gain
        if name=='ending':
            x[cutoff:]=0
            if round(x[cutoff-1,0]*32767)==0:x[cutoff-1,0]=1/32767
        write(audio/f'{name}-mix.wav',x)
    cues={'factory_duration':duration,'dialogue':lines,'events':events,'shared_gain':gain,
          'hall':{'one_voice':[1,2.5],'solitary_pause':[2.5,4.5],'accumulation_starts':4.5},
          'ending':{'party':[0,11.6],'infant':[10.5,19.58],'infant_alone':[12,19.5],'hall_return':[19.5,29.75],'black_crowd':[18,30],'black_daughter':[14,30],'silence':[29.75,30]},
          'provenance':'Original procedural scratch synthesis and installed local speech. No recorded distress or provider generation. Infant recognizability and emotional credibility require listening review.'}
    (run/'cues.json').write_text(json.dumps(cues,indent=2)+'\n')
    return cues
