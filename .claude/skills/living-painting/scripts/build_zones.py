# TEMPLATE from "The Other Window" (first living-painting). Parameterized by the states/worlds lists
# and the clip-naming convention clips/fg_<state>[_2].mp4 + clips/mw_<world>.mp4. Adapt per project.

#!/usr/bin/env python3
"""The Other Window — zone-track builder.
modes: 'sample' | 'full'. Video-only; audio separate (build_audio.py).
FG state has TWO action clips: fg_<state>.mp4 (curtain billow) + fg_<state>_2.mp4 (inward settle).
"""
import subprocess, os, sys, shutil

C="data/workspace/the-other-window/clips"; S="data/workspace/the-other-window/scratch"; U=f"{S}/units"
os.makedirs(U, exist_ok=True)
MCI="minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"

def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode!=0: print("ERR:"," ".join(c)[:240]); print(r.stderr[-1200:]); raise SystemExit(1)
def dur(f):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())
def V(src,vf,out,pre="medium"):
    run(["ffmpeg","-y","-v","error","-i",src,"-vf",vf,"-an","-r","24","-c:v","libx264","-preset",pre,"-crf","18","-pix_fmt","yuv420p",out]); return out
def stretch(src,f,mode,out):
    return V(src, f"setpts={f}*PTS,{MCI}" if mode=="mci" else f"setpts={f}*PTS", out)
def selfxfade(src,x,out):
    d=dur(src); off=max(0.1,d-x)
    run(["ffmpeg","-y","-v","error","-i",src,"-i",src,"-filter_complex",f"[0:v][1:v]xfade=transition=fade:duration={x}:offset={off}[v]","-map","[v]","-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",out]); return out
def pingpong(src,out):
    run(["ffmpeg","-y","-v","error","-i",src,"-filter_complex","[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]","-map","[v]","-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",out]); return out
def rev(src,out): return V(src,"reverse",out)
def seq_xfade(units,x,out):
    cur=units[0]
    for i,nxt in enumerate(units[1:]):
        d=dur(cur); off=max(0.1,d-x); tmp=f"{U}/_sq_{os.path.basename(out)}_{i}.mp4"
        run(["ffmpeg","-y","-v","error","-i",cur,"-i",nxt,"-filter_complex",f"[0:v][1:v]xfade=transition=fade:duration={x}:offset={off}[v]","-map","[v]","-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",tmp]); cur=tmp
    shutil.copy(cur,out); return out
def fill(unit,target,out):
    n=int(target//dur(unit))+2
    run(["ffmpeg","-y","-v","error","-stream_loop",str(n),"-i",unit,"-t",f"{target}","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",out]); return out
def multi_xfade(inputs,x,out):
    """One ffmpeg, chained xfade with cumulative offsets. inputs same w/h."""
    cmd=["ffmpeg","-y","-v","error"]
    for f in inputs: cmd+=["-i",f]
    fc=""; cur="[0:v]"; length=dur(inputs[0])
    for i in range(1,len(inputs)):
        off=length-x; lbl=f"[v{i}]"
        fc+=f"{cur}[{i}:v]xfade=transition=fade:duration={x}:offset={off:.3f}{lbl};"
        cur=lbl; length=length+dur(inputs[i])-x
    fc=fc.rstrip(";")
    cmd+=["-filter_complex",fc,"-map",cur,"-an","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",out]
    run(cmd); return out

def fg_block(state):
    """Dual-action varied seamless block: 3 units from billow clip + 3 from settle clip, interleaved."""
    b=f"{C}/fg_{state}.mp4"; s=f"{C}/fg_{state}_2.mp4"
    bu1=selfxfade(stretch(b,2,"mci",f"{U}/fg_{state}_b_s2.mp4"),1.5,f"{U}/fg_{state}_bu1.mp4")
    bu2=          stretch(b,4,"setpts",f"{U}/fg_{state}_b_s4.mp4")
    bu3=pingpong( stretch(b,2,"setpts",f"{U}/fg_{state}_b_pp.mp4"),f"{U}/fg_{state}_bu3.mp4")
    su1=selfxfade(stretch(s,2,"mci",f"{U}/fg_{state}_s_s2.mp4"),1.5,f"{U}/fg_{state}_su1.mp4")
    su2=          stretch(s,4,"setpts",f"{U}/fg_{state}_s_s4.mp4")
    su3=rev(stretch(s,3,"setpts",f"{U}/fg_{state}_s_s3.mp4"),f"{U}/fg_{state}_su3.mp4")
    blk=seq_xfade([bu1,su1,bu2,su2,bu3,su3],2.0,f"{U}/fg_{state}_block.mp4")
    return selfxfade(blk,2.0,f"{U}/fg_{state}_blockloop.mp4")

def world_block(world,directional):
    src=f"{C}/mw_{world}.mp4"
    if directional:
        u1=selfxfade(stretch(src,2,"mci",f"{U}/mw_{world}_s2.mp4"),1.5,f"{U}/mw_{world}_u1.mp4")
        u2=selfxfade(stretch(src,3,"mci",f"{U}/mw_{world}_s3.mp4"),1.5,f"{U}/mw_{world}_u2.mp4")
    else:
        u1=pingpong(stretch(src,2,"mci",f"{U}/mw_{world}_s2.mp4"),f"{U}/mw_{world}_u1.mp4")
        u2=pingpong(stretch(src,2,"setpts",f"{U}/mw_{world}_ss.mp4"),f"{U}/mw_{world}_u2.mp4")
    blk=seq_xfade([u1,u2],2.0,f"{U}/mw_{world}_block.mp4")
    return selfxfade(blk,2.0,f"{U}/mw_{world}_blockloop.mp4")

if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "full"
    states=["dawn","morning","midday","dusk","night"]
    worlds=[("beach",True),("forest",False),("city",False),("snow",False),("underwater",False),("desert",True)]
    if mode=="full":
        FG_HOLD=744; FG_X=30; MW_HOLD=634; MW_X=40
        print("== FG blocks (dual-action) ==")
        fg_holds=[]
        for st in states:
            blk=fg_block(st); h=fill(blk,FG_HOLD,f"{U}/fg_{st}_hold.mp4"); fg_holds.append(h)
            print(" fg",st,"block",round(dur(blk),1))
        print("== assemble FG zone (single pass) ==")
        fgz=multi_xfade(fg_holds,FG_X,f"{U}/zone_fg_raw.mp4")
        run(["ffmpeg","-y","-v","error","-i",fgz,"-t","3600","-c","copy",f"{S}/full_fg.mp4"])
        print(" FG zone",round(dur(f'{S}/full_fg.mp4'),1))
        print("== world blocks ==")
        mw_holds=[]
        for w,d in worlds:
            blk=world_block(w,d); h=fill(blk,MW_HOLD,f"{U}/mw_{w}_hold.mp4"); mw_holds.append(h)
            print(" mw",w,"block",round(dur(blk),1))
        print("== assemble MW zone (single pass) ==")
        mwz=multi_xfade(mw_holds,MW_X,f"{U}/zone_mw_raw.mp4")
        run(["ffmpeg","-y","-v","error","-i",mwz,"-t","3600","-c","copy",f"{S}/full_mw.mp4"])
        print(" MW zone",round(dur(f'{S}/full_mw.mp4'),1))
        print("DONE zones: full_fg.mp4 full_mw.mp4")
