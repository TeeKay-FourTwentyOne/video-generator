#!/usr/bin/env node
// Diagnostic exports only. This does not approve clips or bypass tour-veo's final-edit gate.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {startServer} from './server.mjs';
import {openBrowser} from './chrome.mjs';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const json=(path,value)=>writeFile(path,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const clipStem=c=>`shot-${c.shot}${c.take>1?`-take-${c.take}`:''}`;

export async function reviewSources(dir,review){
  if(review.verdict!=='needs-review'||!Array.isArray(review.clips)||review.clips.length!==6)
    throw new Error('A six-shot needs-review decision is required; this is not a final edit.');
  const selected=[];
  for(let shot=1;shot<=6;shot++){
    const entries=review.clips.filter(c=>c.shot===shot);
    const c=entries[0];
    if(entries.length!==1||c.includedForReview!==true||![1,2].includes(c.take)||![4,8].includes(c.durationSeconds))
      throw new Error(`Shot ${shot} lacks an explicit, valid review selection.`);
    const path=join(dir,`clips/${clipStem(c)}.mp4`);
    if(sha(await readFile(path))!==c.sha256)throw new Error(`Shot ${shot} reviewed bytes changed.`);
    selected.push({...c,path});
  }
  return selected;
}

function command(name,args){return new Promise((yes,no)=>{
  const child=spawn(name,args,{stdio:['ignore','pipe','pipe']});let out='',err='';
  child.stdout.on('data',c=>out+=c);child.stderr.on('data',c=>err+=c);
  child.on('error',no);child.on('close',code=>code===0?yes(out):no(new Error(`${name} exited ${code}: ${err||out}`)));
});}

async function plates(output){
  const {server,url}=await startServer(0);let browser;
  try{
    browser=await openBrowser(url);
    for(const kind of ['review-label','comparison-plate']){
      const png=await browser.evaluateLarge(`(()=>{
        const c=document.createElement('canvas');c.width=1920;c.height=1080;
        const x=c.getContext('2d');x.textBaseline='middle';
        if(${JSON.stringify(kind)}==='review-label'){
          x.fillStyle='rgba(20,38,32,.82)';x.fillRect(24,24,678,54);
          x.fillStyle='#f1f0e9';x.font='600 22px system-ui';
          x.fillText('MERIDIAN HOUSE  /  REVIEW CUT - continuity issues',42,51);
        }else{
          x.fillStyle='#f1f0e9';x.fillRect(0,0,1920,1080);x.fillStyle='#203b31';
          x.font='600 48px system-ui';x.fillText('MERIDIAN HOUSE / THE LIVING LIBRARY',48,92);
          x.font='25px system-ui';x.fillText('Six shared camera beats. One persistent set. A first Veo motion experiment.',48,151);
          x.font='600 24px system-ui';x.fillText('01 / ORIGINAL 3D TOUR',48,218);x.fillText('02 / VEO 3.1 - REVIEW CUT',976,218);
          x.font='24px system-ui';x.fillText('3D motion study: 6 unique frames per second.',48,805);x.fillText('Generated motion: 24 frames per second.',976,805);
          x.font='600 28px system-ui';x.fillText('Lighting comes alive. Spatial continuity does not yet hold.',48,902);
          x.font='22px system-ui';x.fillText('Watch the right-hand arch, the reading table, and the return to the atrium.',48,948);
          x.fillStyle='#68786c';x.font='18px system-ui';x.fillText('24 seconds / 16:9 / beat-aligned comparison / no new image generations',48,1028);
        }
        return c.toDataURL('image/png');
      })()`);
      await writeFile(join(output,`${kind}.png`),Buffer.from(png.split(',')[1],'base64'),{flag:'wx'});
    }
  }finally{await browser?.close();await new Promise(r=>server.close(r));}
}

export async function createReview(dir,output){
  const plan=JSON.parse(await readFile(join(dir,'plan.json'),'utf8'));
  const review=JSON.parse(await readFile(join(dir,'clip-review.json'),'utf8'));
  const clips=await reviewSources(dir,review);
  if(plan.shots.length!==6)throw new Error('Expected six camera beats.');
  await mkdir(output); // no overwrite and no recursive creation of ambiguous paths
  await plates(output);
  const inputArgs=clips.flatMap(c=>['-i',c.path]);
  const filters=[];
  for(let i=0;i<6;i++){
    const duration=clips[i].durationSeconds,speed=duration/4;
    filters.push(`[${i}:v]trim=duration=${duration},setpts=(PTS-STARTPTS)/${speed},fps=24,tpad=stop_mode=clone:stop_duration=0.1,trim=end_frame=96,scale=1920:1080,setsar=1,format=yuv420p[v${i}]`);
    filters.push(`[${i}:a]atrim=duration=${duration},asetpts=PTS-STARTPTS,atempo=${speed},apad,atrim=duration=4,aresample=48000,aformat=channel_layouts=stereo,volume=-6dB,afade=t=in:d=0.04,afade=t=out:st=3.92:d=0.08[a${i}]`);
  }
  filters.push(`${clips.map((_,i)=>`[v${i}][a${i}]`).join('')}concat=n=6:v=1:a=1[joined][a]`);
  filters.push('[joined][6:v]overlay=0:0:format=auto,format=yuv420p[v]');
  const encode=['-c:v','libx264','-preset','fast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart'];
  const tour=join(output,'tour-review.mp4');
  await command('ffmpeg',['-hide_banner','-loglevel','error','-n',...inputArgs,'-loop','1','-framerate','24','-i',join(output,'review-label.png'),'-filter_complex',filters.join(';'),'-map','[v]','-map','[a]','-t','24','-frames:v','576',...encode,tour]);
  console.log(`Saved ${tour}`);

  // Retiming the original six beats independently aligns their cut marks, not their inferred paths.
  const comparison=[];
  comparison.push(`[0:v]split=6${clips.map((_,i)=>`[s${i}]`).join('')}`);
  for(let i=0;i<6;i++){
    const s=plan.shots[i],duration=s.sourceEnd-s.sourceStart;
    if(!(duration>0))throw new Error('Invalid source camera beat.');
    comparison.push(`[s${i}]trim=start=${s.sourceStart}:end=${s.sourceEnd},setpts=(PTS-STARTPTS)*${4/duration},fps=24,tpad=stop_mode=clone:stop_duration=0.2,trim=end_frame=96,scale=896:504:flags=lanczos,setsar=1[r${i}]`);
  }
  comparison.push(`${clips.map((_,i)=>`[r${i}]`).join('')}concat=n=6:v=1:a=0[reference]`);
  comparison.push('[1:v]scale=896:504:flags=lanczos,setsar=1[generated]');
  comparison.push('[2:v][reference]overlay=48:256:format=auto[withref]');
  comparison.push('[withref][generated]overlay=976:256:format=auto,format=yuv420p[v]');
  const comparisonFile=join(output,'tour-comparison.mp4');
  await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',resolve(dir,plan.sourceTour),'-i',tour,'-loop','1','-framerate','24','-i',join(output,'comparison-plate.png'),'-filter_complex',comparison.join(';'),'-map','[v]','-map','1:a','-t','24','-frames:v','576',...encode,comparisonFile]);
  console.log(`Saved ${comparisonFile}`);
  const outputs=[];
  for(const file of [tour,comparisonFile]){
    const probe=JSON.parse(await command('ffprobe',['-v','error','-show_streams','-show_format','-of','json',file]));
    const v=probe.streams.find(s=>s.codec_type==='video');
    if(v.width!==1920||v.height!==1080||v.nb_frames!=='576'||v.r_frame_rate!=='24/1')throw new Error('Export dimensions/timing failed.');
    outputs.push({path:file,sha256:sha(await readFile(file)),probe});
  }
  await json(join(output,'manifest.json'),{status:'review-only',continuityApproved:false,createdAt:new Date().toISOString(),selected:clips,outputs,edit:{seconds:24,frames:576,cutTimes:[4,8,12,16,20],visualTransitions:'hard cuts; defects not masked',audio:'native Veo; -6 dB gain with short fades at joins; not auditioned',reference:'Original tour-v1, each beat retimed to 4 seconds; no optical flow'},paidRequests:0});
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  const dir=resolve(process.argv[2]||'data/workspace/meridian-house/veo-tour-v1');
  const output=resolve(process.argv[3]||join(dir,'edit/review-v1'));
  try{await createReview(dir,output);}catch(e){console.error(e.message);process.exitCode=1;}
}
