#!/usr/bin/env node
// A bounded, resumable six-shot Veo experiment using the existing 3D tour.
// prepare is local-only; submit requires a reviewed plan and pre-logs spend.
import { readFile, writeFile, mkdir, access, copyFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { startServer } from './server.mjs';
import { openBrowser } from './chrome.mjs';

const ROOT=resolve(import.meta.dirname,'../..');
const DEFAULT=join(ROOT,'data/workspace/meridian-house/veo-tour-v1');
const MARKS=[0,.16,.32,.50,.66,.82,1];
const NAMES=['Atrium departure','Cross the library arch','Approach the reading desk','Turn back toward the atrium','Leave the library','Return to the orrery'];
const MOTION=[
  'Glide diagonally left and forward from the atrium, smoothly turning left to face the existing library arch. Keep the orrery on the right as the arch and library approach. Do not enter through any wall.',
  'Dolly forward through the existing open library arch into the library. The arch naturally passes out of frame; the existing shelves and reading desk grow larger with correct parallax. No door opens and no new passage appears.',
  'Continue forward along the open library floor toward the reading desk and gently look toward the book-lined corner. Stop at the ending camera mark before touching any furniture. Keep every shelf and book attached in place.',
  'Rotate the camera smoothly to the RIGHT from a fixed position inside the library, revealing the existing open arch and the atrium beyond. This is a continuous rightward pan of roughly 114 degrees, not a dolly or a dissolve. The shelves pass across the view with rigid perspective; the camera never moves through a shelf.',
  'Dolly forward out of the library through the SAME open arch toward the atrium. The library shelves stay behind the camera and the existing orrery is revealed in the atrium. Do not invent a corridor, wall opening, or additional room.',
  'Glide diagonally back and right to the ORIGINAL atrium camera mark, smoothly facing the central orrery. End on the exact original view. The same chairs, lamps, arches, plants, rings and planets are still in their original places.',
];
const LOOK='Preserve the supplied stylized miniature mansion and its exact painted surface treatment. Keep all architecture rigid and every object count unchanged. The camera physically travels through one connected 3D set: never dissolve between the anchors, morph walls, cut, teleport, zoom, or replace the room. Preserve the full 16:9 framing with no bars, titles, subtitles or watermark.';
const LIFE='Make this unoccupied magical house quietly alive: the EXISTING lamps and the existing central orrery sun breathe very gently in warm brightness, casting a slow soft light shimmer on nearby surfaces; existing plant leaves, only if visible, sway a few centimeters and settle. The orrery rings and planets remain mechanically rigid and stay in their anchored positions. Every book remains on its existing shelf or desk. No people, animals, faces, creatures, additional objects, floating books, particles, smoke, fire, new fixtures, new doorways or new decorations. Finish in the precise calm state of the ending anchor.';
const SOUND='Audio: quiet airy indoor room tone, soft existing-leaf rustle when visible, faint delicate clockwork ticking from the orrery, with natural room reverberation. No speech, voices, footsteps, music, dramatic impacts or loud chimes.';

async function exists(path){try{await access(path);return true;}catch(e){if(e.code==='ENOENT')return false;throw e;}}
const json=(path,value)=>writeFile(path,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const stem=shot=>`shot-${shot.id}${shot.take>1?`-take-${shot.take}`:''}`;
function command(name,args){return new Promise((yes,no)=>{const child=spawn(name,args,{cwd:ROOT,stdio:['ignore','pipe','pipe']});let out='',err='';child.stdout.on('data',c=>out+=c);child.stderr.on('data',c=>err+=c);child.on('error',no);child.on('close',code=>code===0?yes(out):no(new Error(`${name} exited ${code}: ${err||out}`)));});}
function options(argv){const [action,...args]=argv;const o={action,output:DEFAULT,shot:null};for(const arg of args){const m=arg.match(/^--(output|shot)=(.+)$/);if(!m)throw new Error(`Unknown argument ${arg}`);o[m[1]]=m[2];}o.output=resolve(o.output);if(!['prepare','submit','poll','status','assemble'].includes(action))throw new Error('Usage: tour-veo.mjs prepare|submit|poll|status|assemble [--output=DIR] [--shot=1..6]');return o;}

async function prepare(dir){
  if(await exists(dir))throw new Error('Choose a new output directory; existing runs are never overwritten.');
  const assets=new Map();
  const {server,url}=await startServer(0,assets);let browser;
  try{
    browser=await openBrowser(url);await mkdir(dir,{recursive:true});
    for(const folder of ['anchors','prompts','operations','clips','qa','edit'])await mkdir(join(dir,folder));
    const anchors=[];
    for(let i=0;i<MARKS.length;i++){
      const frame=await browser.evaluateLarge(`sceneLab.renderFrame(${JSON.stringify({shot:'tour',progress:MARKS[i],width:1920,height:1080})})`);
      const stem=`anchors/mark-${String(i).padStart(2,'0')}`;
      const bytes=Buffer.from(frame.png.split(',')[1],'base64');
      await writeFile(join(dir,`${stem}.geometry.png`),bytes,{flag:'wx'});
      await json(join(dir,`${stem}.camera.json`),frame.reference);
      anchors.push({index:i,progress:MARKS[i],sourceTime:MARKS[i]*24,camera:frame.reference.camera,image:`${stem}.geometry.png`,geometry:`${stem}.geometry.png`,reference:`${stem}.camera.json`,sha256:sha(bytes)});
    }
    const shots=[];
    for(let i=0;i<6;i++){
      const prompt=`One continuous 4-second book-ended architectural camera shot. ${MOTION[i]}\n\n${LOOK}\n\n${LIFE}\n\n${SOUND}\n`;
      const promptFile=`prompts/shot-${i+1}.txt`;await writeFile(join(dir,promptFile),prompt,{flag:'wx'});
      shots.push({id:i+1,name:NAMES[i],start:i,end:i+1,sourceStart:MARKS[i]*24,sourceEnd:MARKS[i+1]*24,durationSeconds:4,model:'veo-3.1-prod',resolution:'1080p',aspectRatio:'16:9',generateAudio:true,seed:9122600+i,promptFile,promptSHA256:sha(prompt),estimatedUSD:1.60});
    }
    await json(join(dir,'plan.json'),{schemaVersion:1,title:'Meridian House — the living library tour',createdAt:new Date().toISOString(),sourceTour:'../tour-v1/16x9/tour.mp4',paintSource:null,anchors,shots,reviewStatus:'pending',project:'meridian-house',estimatedNewVeoUSD:9.60,automaticRetries:false,notes:['Exact camera marks and clean geometry/materials from tour-v1. No new image generation.','Six four-second segments retime the original approximately four-second beats to an even 24 seconds.','Frames constrain endpoints but do not guarantee a spatially correct generated path.','Rotation paint is not used: the translation test revealed stretched contours and duplicate-looking wall details.','Visual QA is performed locally/in this conversation; no other review provider receives footage.']});
    const boardFrames=anchors.map(a=>({path:a.image,label:`${String(a.index+1).padStart(2,'0')}  ${a.sourceTime.toFixed(2)}s  /  ${a.index===0?'START':a.index===6?'RETURN':NAMES[a.index-1].toUpperCase()}`}));
    // Supply explicit anchor bytes to the same loopback allowlist for contact QA.
    for(let i=0;i<boardFrames.length;i++)assets.set(`tour-board-${i}`,{body:await readFile(join(dir,boardFrames[i].path)),contentType:'image/png'});
    const board=await browser.evaluateLarge(`(async()=>{const frames=${JSON.stringify(boardFrames)},c=document.createElement('canvas');c.width=1920;c.height=620;const x=c.getContext('2d');x.fillStyle='#f1f0e9';x.fillRect(0,0,c.width,c.height);x.font='600 13px system-ui';x.textBaseline='middle';for(let i=0;i<frames.length;i++){const img=new Image();img.src=${JSON.stringify(url)}+'/tour-board-'+i;await img.decode();const a=(i%4)*480,b=Math.floor(i/4)*310;x.drawImage(img,a,b,480,270);x.fillStyle='#24382f';x.fillText(frames[i].label,a+12,b+290,455);}x.font='600 24px system-ui';x.fillText('MERIDIAN HOUSE / TOUR',1460,450);x.font='16px system-ui';x.fillText('Shared endpoints · 6 × 4 seconds',1460,488);return c.toDataURL('image/png');})()`);
    await writeFile(join(dir,'qa/anchor-board.png'),Buffer.from(board.split(',')[1],'base64'),{flag:'wx'});
    console.log(`Prepared ${dir}. Inspect anchors and write anchor-review.json before submitting.`);
  }finally{await browser?.close();await new Promise(r=>server.close(r));}
}

async function validatedPlan(dir){
  const plan=JSON.parse(await readFile(join(dir,'plan.json'),'utf8'));
  if(plan.project!=='meridian-house'||plan.shots.length!==6)throw new Error('Unexpected project or shot count.');
  const review=JSON.parse(await readFile(join(dir,'anchor-review.json'),'utf8'));
  if(review.verdict!=='approved')throw new Error('Anchor review has not approved this plan.');
  const ledger=await readFile(join(ROOT,'data/veo-budget-meridian-house.tsv'),'utf8');
  if(!ledger.includes('RESERVE legacy-image')||!ledger.includes('RESERVE infrastructure'))throw new Error('The all-in budget must include prior images and cloud overhead before submission.');
  for(const anchor of plan.anchors)if(sha(await readFile(join(dir,anchor.image)))!==anchor.sha256||review.anchorHashes[anchor.index]!==anchor.sha256)throw new Error('Reviewed anchor changed.');
  for(const shot of plan.shots){if(shot.model!=='veo-3.1-prod'||![4,8].includes(shot.durationSeconds)||shot.resolution!=='1080p'||shot.aspectRatio!=='16:9'||shot.generateAudio!==true||![1,2].includes(shot.take??1))throw new Error('Parameters differ from the budgeted recipe.');if(sha(await readFile(join(dir,shot.promptFile)))!==shot.promptSHA256)throw new Error('Prompt changed after preparation.');}
  return plan;
}

async function submit(dir,id){
  const plan=await validatedPlan(dir),shot=plan.shots.find(s=>s.id===Number(id));if(!shot)throw new Error('Submit requires --shot=1..6.');
  const attempt=join(dir,`operations/${stem(shot)}.attempt.json`),operation=join(dir,`operations/${stem(shot)}.json`);
  if(await exists(attempt)||await exists(operation))throw new Error('This shot already has a submission record. Poll or inspect it; no automatic resubmission.');
  // This command pre-logs before making a paid request, including failed attempts.
  const budget=await command('python3',['tools/veo-budget.py','preflight','--project','meridian-house','--model','quality','--seconds',String(shot.durationSeconds),'--resolution','1080p','--audio','yes','--note',`Meridian living tour ${stem(shot)}: ${shot.name}`]);
  await json(attempt,{submittedAt:new Date().toISOString(),shot:shot.id,take:shot.take??1,promptFile:shot.promptFile,promptSHA256:shot.promptSHA256,estimatedUSD:shot.durationSeconds*.4,budget});console.log(budget.trim());
  const {submitVeoGeneration}=await import('../../mcp/video-generator/dist/clients/veo.js');
  const result=await submitVeoGeneration({...shot,prompt:await readFile(join(dir,shot.promptFile),'utf8'),firstFramePath:join(dir,plan.anchors[shot.start].image),lastFramePath:join(dir,plan.anchors[shot.end].image)});
  await json(operation,{...result,shot:shot.id,take:shot.take??1,submittedAt:new Date().toISOString()});console.log(JSON.stringify({shot:shot.id,take:shot.take??1,...result}));
}

async function poll(dir){
  const {getGoogleAccessToken,buildVertexUrl}=await import('../../mcp/video-generator/dist/clients/google-auth.js');
  const {downloadVeoVideo}=await import('../../mcp/video-generator/dist/clients/veo.js');
  const plan=JSON.parse(await readFile(join(dir,'plan.json'),'utf8'));
  const {accessToken,projectId}=await getGoogleAccessToken();
  for(const shot of plan.shots){
    const opPath=join(dir,`operations/${stem(shot)}.json`),donePath=join(dir,`operations/${stem(shot)}.result.json`);
    if(!await exists(opPath)){console.log(`Shot ${shot.id}: not submitted`);continue;}
    if(await exists(donePath)){const done=JSON.parse(await readFile(donePath,'utf8'));console.log(`Shot ${shot.id}: ${done.status}`);continue;}
    const op=JSON.parse(await readFile(opPath,'utf8'));
    const response=await fetch(buildVertexUrl(projectId,op.model,'fetchPredictOperation'),{method:'POST',headers:{Authorization:`Bearer ${accessToken}`,'Content-Type':'application/json'},body:JSON.stringify({operationName:op.operationName})});
    const result=await response.json();if(!response.ok)throw new Error(`Poll failed ${response.status}: ${JSON.stringify(result.error)}`);
    if(!result.done){console.log(`Shot ${shot.id}: generating`);continue;}
    const video=result.response?.videos?.[0];
    if(!video){await json(donePath,{status:'failed',finishedAt:new Date().toISOString(),error:result.error||result.response||'No video'});console.log(`Shot ${shot.id}: terminal failure (saved; not retried)`);continue;}
    const downloaded=await downloadVeoVideo({done:true,operationName:op.operationName,video});
    const dest=`clips/${stem(shot)}.mp4`;
    await copyFile(join(ROOT,'data/video',downloaded.filename),join(dir,dest),1);
    const probe=JSON.parse(await command('ffprobe',['-v','error','-show_streams','-show_format','-of','json',join(dir,dest)]));
    await json(donePath,{status:'completed',finishedAt:new Date().toISOString(),video:dest,original:downloaded,probe});console.log(`Shot ${shot.id}: downloaded ${dest}`);
  }
}

async function assemble(dir){
  const plan=await validatedPlan(dir);
  const review=JSON.parse(await readFile(join(dir,'clip-review.json'),'utf8'));
  if(review.verdict!=='approved'||review.clips.length!==6)throw new Error('Six reviewed clips are required.');
  const args=['-hide_banner','-loglevel','error','-n'];
  for(const shot of plan.shots){const entry=review.clips.find(c=>c.shot===shot.id&&c.accepted);if(!entry||(entry.take??1)!==(shot.take??1))throw new Error(`Shot ${shot.id} selected take not accepted.`);const file=join(dir,`clips/${stem(shot)}.mp4`);if(entry.sha256!==sha(await readFile(file)))throw new Error('Reviewed clip changed.');args.push('-i',file);}
  const chains=[];
  for(let i=0;i<6;i++){const duration=plan.shots[i].durationSeconds,speed=duration/4;chains.push(`[${i}:v]trim=duration=${duration},setpts=(PTS-STARTPTS)/${speed},fps=24,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[v${i}]`);chains.push(`[${i}:a]atrim=duration=${duration},asetpts=PTS-STARTPTS,atempo=${speed},apad,atrim=duration=4,aresample=48000,aformat=channel_layouts=stereo,volume=-6dB,afade=t=in:d=0.04,afade=t=out:st=3.92:d=0.08[a${i}]`);}
  chains.push(`${Array.from({length:6},(_,i)=>`[v${i}][a${i}]`).join('')}concat=n=6:v=1:a=1[v][a]`);
  args.push('-filter_complex',chains.join(';'),'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart',join(dir,'tour.mp4'));
  await command('ffmpeg',args);console.log(`Saved ${join(dir,'tour.mp4')}`);
}

const o=options(process.argv.slice(2));
try{if(o.action==='prepare')await prepare(o.output);else if(o.action==='submit')await submit(o.output,o.shot);else if(o.action==='poll')await poll(o.output);else if(o.action==='assemble')await assemble(o.output);else console.log(await command('python3',['tools/veo-budget.py','status','--project','meridian-house']));}catch(e){console.error(e.message);process.exitCode=1;}
