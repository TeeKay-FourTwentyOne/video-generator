#!/usr/bin/env node
// Local, monotonic source-time ramps. Frame interpolation is confined within each shot.
import {readFile,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {command,saveJSON,validateEdit} from './tour-finish.mjs';

export const SPEEDS=[{start:.35,end:.30},{start:1.80,end:.50},{start:1.80,end:.18},{start:.18,end:1.00},{start:.60,end:1.00},{start:.60,end:.35}];

export function sourceAt(u,{start,end},fraction=.15,sourceFrames=88,outputFrames=96){
  const ratio=sourceFrames/outputFrames;
  const middle=(ratio-fraction*(start+end)/2)/(1-fraction);
  if(middle<=0||start<=0||end<=0)throw new Error('Retime must be strictly forward.');
  const h=fraction;
  if(u<=h){const z=u/h;return outputFrames*(middle*u+(start-middle)*h*(z-z**3+.5*z**4));}
  const head=h*(middle+start)/2;
  if(u<=1-h)return outputFrames*(head+middle*(u-h));
  const z=(u-(1-h))/h;
  return outputFrames*(head+middle*(1-2*h)+middle*h*z+(end-middle)*h*(z**3-.5*z**4));
}

export function timeAtSource(frame,speed,duration=4){
  if(frame>88)return duration+(frame-88)/24;
  let lo=0,hi=1;
  for(let i=0;i<45;i++){const mid=(lo+hi)/2;if(sourceAt(mid,speed)<frame)lo=mid;else hi=mid;}
  return (lo+hi)/2*duration;
}

export async function retime(dir,output,height=720,planFile=join(dir,'edit/local-v2/edit-plan.json')){
  const plan=JSON.parse(await readFile(planFile,'utf8'));validateEdit(plan);
  if(![720,1080].includes(height))throw new Error('Choose 720 or 1080.');
  await mkdir(output);
  const records=[];
  for(let i=0;i<6;i++){
    const source=join(dir,`clips/shot-${i+1}.mp4`);
    if(createHash('sha256').update(await readFile(source)).digest('hex')!==plan.clips[i].sha256)throw new Error('Reviewed source changed.');
    const speed=SPEEDS[i],duration=i===5?95/24:4;
    const times=Array.from({length:89},(_,n)=>timeAtSource(n,speed,duration));
    let expression=`${duration}+(N-88)/24`;
    for(let n=88;n>=0;n--)expression=`if(eq(N,${n}),${times[n].toFixed(8)},${expression})`;
    // The extra 0.2-second cloned tail supplies interpolation look-ahead, never enters the cut.
    const vf=`trim=end_frame=89,setpts=PTS-STARTPTS,scale=-2:${height}:flags=lanczos,tpad=stop_mode=clone:stop_duration=0.2,settb=1/24000,setpts='(${expression})/TB',minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:mb_size=16:search_param=16:vsbmc=1:scd=none,trim=end_frame=96,setpts=N/(24*TB),setsar=1,format=yuv420p`;
    const path=join(output,`shot-${i+1}.mp4`);
    await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',source,'-vf',vf,'-an','-c:v','libx264','-preset','fast','-crf','17','-frames:v','96','-movflags','+faststart',path]);
    const probe=JSON.parse((await command('ffprobe',['-v','error','-show_entries','stream=nb_frames,width,height,r_frame_rate,duration','-of','json',path])).out);
    const v=probe.streams[0];if(v.nb_frames!=='96'||v.r_frame_rate!=='24/1')throw new Error(`Retime shot ${i+1} did not produce 96 frames.`);
    records.push({shot:i+1,source,sha256:plan.clips[i].sha256,speed,sourceEndpointAtOutputSeconds:duration,sourceFrameTimes:times,output:path,probe});
    console.log(`Retimed shot ${i+1} / 6 at ${height}p`);
  }
  const joins=[];for(let i=0;i<6;i++)joins.push(`[${i}:v]setpts=PTS-STARTPTS,setsar=1[v${i}]`);
  joins.push(`${records.map((_,i)=>`[v${i}]`).join('')}concat=n=6:v=1:a=0[v]`);
  const file=join(output,'tour-retimed.mp4');
  await command('ffmpeg',['-hide_banner','-loglevel','error','-n',...records.flatMap(r=>['-i',r.output]),'-filter_complex',joins.join(';'),'-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','17','-frames:v','576','-movflags','+faststart',file]);
  await saveJSON(join(output,'manifest.json'),{status:'candidate-needs-interpolation-review',paidRequests:0,method:'Monotonic source-time ramps with within-shot FFmpeg motion interpolation. No frame blending across cuts, no geometric registration/warp of the room.',rampFraction:.15,records,output:file,frames:576,seconds:24,cutFrames:[96,192,288,384,480]});
  console.log(`Saved ${file}`);
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  const dir=resolve(process.argv[2]||'data/workspace/meridian-house/veo-tour-v1');
  const output=resolve(process.argv[3]||join(dir,'edit/local-v2/retime-preview'));
  const plan=process.argv[5]?resolve(process.argv[5]):undefined;
  retime(dir,output,Number(process.argv[4]||720),plan).catch(e=>{console.error(e.message);process.exitCode=1;});
}
