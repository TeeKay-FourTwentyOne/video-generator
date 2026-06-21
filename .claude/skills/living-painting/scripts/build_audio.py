# TEMPLATE from "The Other Window" (first living-painting). Parameterized by the states/worlds lists
# and the clip-naming convention clips/fg_<state>[_2].mp4 + clips/mw_<world>.mp4. Adapt per project.

#!/usr/bin/env python3
"""The Other Window — full-hour audio bed.
Pads track the room (dawn->night); weather tracks the mirror worlds (beach->...->desert);
bells mark each world change. Output: full_bed.m4a (3600s)."""
import subprocess, os, shutil
S="data/workspace/the-other-window/scratch"; A="data/audio"; U=f"{S}/aunits"
os.makedirs(U,exist_ok=True)
PAD={"dawn":f"{A}/music/music_1781997776186_ek6o9o.mp3","morning":f"{A}/music/music_1781992074617_1t1klj.mp3",
     "midday":f"{A}/music/music_1781997780875_nxfl4i.mp3","dusk":f"{A}/music/music_1781997787190_uwnhm2.mp3",
     "night":f"{A}/music/music_1781997792561_95byfk.mp3"}
WX={"beach":"weather_surf","forest":"weather_forest","city":"weather_city","snow":"weather_snow",
    "underwater":"weather_underwater","desert":"weather_desert"}
BELL=f"{A}/sfx/bell.mp3"
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode!=0: print("ERR",r.stderr[-1000:]); raise SystemExit(1)
def adur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())
def loopfill(src,target,vol,out):
    run(["ffmpeg","-y","-v","error","-i",src,"-filter_complex",
         f"[0:a]aloop=loop=-1:size=8000000,atrim=0:{target},volume={vol},afade=t=in:d=2,afade=t=out:st={target-2}:d=2[a]",
         "-map","[a]","-ar","48000","-ac","2","-c:a","pcm_s16le",out]); return out
def axfade_chain(parts,x,out):
    cur=parts[0]
    for i,nxt in enumerate(parts[1:]):
        tmp=f"{U}/_ax_{os.path.basename(out)}_{i}.wav"
        run(["ffmpeg","-y","-v","error","-i",cur,"-i",nxt,"-filter_complex",f"[0:a][1:a]acrossfade=d={x}:c1=tri:c2=tri[a]","-map","[a]","-ar","48000","-ac","2","-c:a","pcm_s16le",tmp]); cur=tmp
    shutil.copy(cur,out); return out

states=["dawn","morning","midday","dusk","night"]
worlds=["beach","forest","city","snow","underwater","desert"]
PAD_HOLD=760; PAD_X=50; W_HOLD=634; W_X=40

print("pads…")
pad_parts=[loopfill(PAD[s],PAD_HOLD,0.55,f"{U}/pad_{s}.wav") for s in states]
pad=axfade_chain(pad_parts,PAD_X,f"{U}/pad_full.wav")
print("weather…")
w_parts=[loopfill(f"{A}/sfx/{WX[w]}.mp3",W_HOLD,0.38,f"{U}/w_{w}.wav") for w in worlds]
weather=axfade_chain(w_parts,W_X,f"{U}/weather_full.wav")
print("pad",round(adur(pad),1),"weather",round(adur(weather),1))

# bells at MW world transitions (xfade centers): t_i = i*(W_HOLD) - (i-1)*W_X - W_X/2 ... compute running
btimes=[]; length=W_HOLD
for i in range(1,6):
    btimes.append(length-W_X/2); length=length+W_HOLD-W_X
print("bell times",[round(t) for t in btimes])

# mix pad + weather + bells
cmd=["ffmpeg","-y","-v","error","-i",pad,"-i",weather]
for _ in btimes: cmd+=["-i",BELL]
fc="[0:a]atrim=0:3600[pad];[1:a]atrim=0:3600[wx];"
fc+="[pad][wx]amix=inputs=2:duration=longest:normalize=0[m0];"
prev="m0"
for i,t in enumerate(btimes):
    idx=2+i; ms=int(t*1000)
    fc+=f"[{idx}:a]adelay={ms}|{ms},volume=0.5[b{i}];"
    fc+=f"[{prev}][b{i}]amix=inputs=2:duration=longest:normalize=0[mb{i}];"; prev=f"mb{i}"
fc+=f"[{prev}]atrim=0:3600,loudnorm=I=-18:TP=-1.5:LRA=11,afade=t=in:d=4,afade=t=out:st=3595:d=5[mix]"
cmd+=["-filter_complex",fc,"-map","[mix]","-t","3600","-ar","48000","-ac","2","-c:a","aac","-b:a","192k",f"{S}/full_bed.m4a"]
run(cmd)
print("DONE full_bed.m4a",round(adur(f'{S}/full_bed.m4a'),1))
