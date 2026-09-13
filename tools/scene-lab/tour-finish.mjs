#!/usr/bin/env node
// Local finishing of reviewed footage. Never imports a paid generation client.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

export function command(name,args){return new Promise((yes,no)=>{
  const child=spawn(name,args,{stdio:['ignore','pipe','pipe']});let out='',err='';
  child.stdout.on('data',c=>out+=c);child.stderr.on('data',c=>err+=c);
  child.on('error',no);child.on('close',code=>code===0?yes({out,err}):no(new Error(`${name} ${code}: ${err||out}`)));
});}
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export const saveJSON=(file,data)=>writeFile(file,JSON.stringify(data,null,2)+'\n',{flag:'wx'});

export function validateEdit(plan){
  if(plan.fps!==24||!Array.isArray(plan.clips)||plan.clips.length!==6)throw new Error('Expected six 24 fps clips.');
  let total=0;const cuts=[];
  for(let i=0;i<6;i++){
    const c=plan.clips[i];
    if(c.shot!==i+1||c.take!==1||!Number.isInteger(c.startFrame)||!Number.isInteger(c.endFrameExclusive)||c.startFrame<0||c.endFrameExclusive>96||c.endFrameExclusive<=c.startFrame)throw new Error('Invalid frame-exact range.');
    total+=c.endFrameExclusive-c.startFrame;if(i<5)cuts.push(total);
  }
  return {frames:total,seconds:total/24,cutFrames:cuts,cutTimes:cuts.map(n=>n/24)};
}

export async function renderEdit(dir,planFile,output){
  const plan=JSON.parse(await readFile(planFile,'utf8')),timing=validateEdit(plan);
  const paths=plan.clips.map(c=>join(dir,`clips/shot-${c.shot}.mp4`));
  for(let i=0;i<6;i++)if(sha(await readFile(paths[i]))!==plan.clips[i].sha256)throw new Error('Source changed after review.');
  await mkdir(output);
  const filters=[];
  for(let i=0;i<6;i++){
    const c=plan.clips[i],duration=(c.endFrameExclusive-c.startFrame)/24;
    filters.push(`[${i}:v]trim=start_frame=${c.startFrame}:end_frame=${c.endFrameExclusive},setpts=PTS-STARTPTS,setsar=1,fps=24,format=yuv420p[v${i}]`);
    filters.push(`[${i}:a]atrim=start=${c.startFrame/24}:end=${c.endFrameExclusive/24},asetpts=PTS-STARTPTS,apad,atrim=duration=${duration},aresample=48000,aformat=channel_layouts=stereo,volume=-6dB,afade=t=in:d=0.025,afade=t=out:st=${duration-.04}:d=0.04[a${i}]`);
  }
  filters.push(`${plan.clips.map((_,i)=>`[v${i}][a${i}]`).join('')}concat=n=6:v=1:a=1[v][a]`);
  const file=join(output,'tour-trimmed.mp4');
  await command('ffmpeg',['-hide_banner','-loglevel','error','-n',...paths.flatMap(p=>['-i',p]),'-filter_complex',filters.join(';'),'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','17','-c:a','aac','-b:a','192k','-frames:v',String(timing.frames),'-movflags','+faststart',file]);
  const probe=JSON.parse((await command('ffprobe',['-v','error','-show_streams','-show_format','-of','json',file])).out);
  const video=probe.streams.find(s=>s.codec_type==='video');
  if(Number(video.nb_frames)!==timing.frames||video.r_frame_rate!=='24/1'||video.width!==1920||video.height!==1080)throw new Error('Unexpected export timing/size.');
  await saveJSON(join(output,'manifest.json'),{status:'candidate-awaiting-motion-review',plan:resolve(planFile),planSHA256:sha(await readFile(planFile)),sources:plan.clips,...timing,probe,output:file,sha256:sha(await readFile(file)),paidRequests:0,visualProcessing:'Frame-exact trimming only. No geometric warps, optical flow, crossfades, or repeated shared-anchor frames.'});
  console.log(JSON.stringify({file,...timing}));
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  const dir=resolve(process.argv[2]||'data/workspace/meridian-house/veo-tour-v1');
  const plan=resolve(process.argv[3]||join(dir,'edit/local-v2/edit-plan.json'));
  const output=resolve(process.argv[4]||join(dir,'edit/local-v2/trim-v1'));
  renderEdit(dir,plan,output).catch(e=>{console.error(e.message);process.exitCode=1;});
}
