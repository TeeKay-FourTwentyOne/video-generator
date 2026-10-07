#!/usr/bin/env node
// Bounded three-shot documentary run. No automatic submission retries.
import {readFile,writeFile,readdir,copyFile,access} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

const ROOT=resolve(import.meta.dirname,'../..');
const sha=b=>createHash('sha256').update(b).digest('hex');
const readJSON=async p=>JSON.parse(await readFile(p,'utf8'));
const save=(p,v)=>writeFile(p,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const stem=s=>`shot-${s.id}${s.take>1?`-take-${s.take}`:''}`;
async function exists(p){try{await access(p);return true;}catch(e){if(e.code==='ENOENT')return false;throw e;}}

export async function validate(dir,ledgerFile=join(ROOT,'data/veo-budget-meridian-house.tsv')){
  const p=await readJSON(join(dir,'plan.json'));
  const r=await readJSON(join(dir,'anchor-review.json'));
  if(p.project!=='meridian-house'||p.shots.length!==3||p.anchors.length!==4||
     p.budget.proposalApproved!==true||p.budget.authorizedAdditionalUSD!==30||
     p.budget.retainedPriorAllocationUSD!==48.4||p.budget.currentOperationalCeilingUSD!==78.4||
     p.budget.maximumVeoRequests!==8||p.automaticRetries!==false||r.verdict!=='approved')
    throw new Error('Recipe, budget authorization or anchor review is invalid.');
  if(p.anchors[0].image!==p.anchors[3].image)throw new Error('Opening and return must share the canonical file.');
  for(const a of p.anchors)if(sha(await readFile(join(dir,a.image)))!==a.sha256||r.anchorHashes[a.index]!==a.sha256)
    throw new Error('Reviewed anchor bytes changed.');
  for(let i=0;i<3;i++){
    const s=p.shots[i];
    if(s.id!==i+1||s.start!==i||s.end!==i+1||s.durationSeconds!==8||s.model!=='veo-3.1-prod'||
       s.resolution!=='1080p'||s.aspectRatio!=='16:9'||s.generateAudio!==true||
       !Number.isInteger(s.take)||s.take<1||s.take>5||
       (s.reverseGeneration!==undefined&&(s.id!==2||s.reverseGeneration!==true))||
       sha(await readFile(join(dir,s.promptFile)))!==s.promptSHA256)
      throw new Error('Shot parameters or prompt differ from the reviewed recipe.');
  }
  const ledger=await readFile(ledgerFile,'utf8');
  if(!ledger.includes('RESERVE legacy-image')||!ledger.includes('RESERVE infrastructure')||
     !ledger.includes('RESERVE documentary-veo-v1 images'))throw new Error('Missing retained all-in reservations.');
  return p;
}

async function submit(dir,id){
  const p=await validate(dir),s=p.shots.find(s=>s.id===id);
  if(!s)throw new Error('Choose shot 1, 2 or 3.');
  if((await readdir(join(dir,'operations'))).filter(f=>f.endsWith('.attempt.json')).length>=p.budget.maximumVeoRequests)
    throw new Error('Reviewed request limit reached.');
  const name=stem(s),attempt=join(dir,`operations/${name}.attempt.json`);
  if(s.take>1){
    const decision=await readJSON(join(dir,`reviews/${name}.correction.json`));
    if(decision.verdict!=='reroll'||decision.promptSHA256!==s.promptSHA256||!decision.reason)
      throw new Error('A targeted correction decision is required before another take.');
  }
  const {getGoogleAccessToken}=await import('../../mcp/video-generator/dist/clients/google-auth.js');
  await getGoogleAccessToken(); // connectivity before reservation; never print credentials
  await save(attempt,{shot:s.id,take:s.take,startedAt:new Date().toISOString(),promptFile:s.promptFile,
    promptSHA256:s.promptSHA256,reverseGeneration:s.reverseGeneration??false,
    anchorHashes:[p.anchors[s.start].sha256,p.anchors[s.end].sha256],estimatedUSD:3.2});
  try{
    const budget=execFileSync('python3',['tools/veo-budget.py','preflight','--project','meridian-house',
      '--model','quality','--seconds','8','--resolution','1080p','--audio','yes',
      '--note',`Documentary walkthrough ${name}: ${s.name}`],{cwd:ROOT,encoding:'utf8'});
    await save(join(dir,`operations/${name}.reservation.json`),{budget,estimatedUSD:3.2});
    const {submitVeoGeneration}=await import('../../mcp/video-generator/dist/clients/veo.js');
    const op=await submitVeoGeneration({...s,prompt:await readFile(join(dir,s.promptFile),'utf8'),
      firstFramePath:join(dir,p.anchors[s.reverseGeneration?s.end:s.start].image),
      lastFramePath:join(dir,p.anchors[s.reverseGeneration?s.start:s.end].image)});
    await save(join(dir,`operations/${name}.json`),{...op,shot:s.id,take:s.take,reverseGeneration:s.reverseGeneration??false});
    console.log(`${name}: submitted; $3.20 reserved; no automatic retries.`);
  }catch(e){
    await save(join(dir,`operations/${name}.error.json`),{error:e.message,automaticRetry:false});
    throw new Error(`${name}: submission stopped; inspect the retained local operation records.`);
  }
}

async function poll(dir){
  const {getGoogleAccessToken,buildVertexUrl}=await import('../../mcp/video-generator/dist/clients/google-auth.js');
  const {downloadVeoVideo}=await import('../../mcp/video-generator/dist/clients/veo.js');
  const {accessToken,projectId}=await getGoogleAccessToken();
  const files=(await readdir(join(dir,'operations'))).filter(f=>/^shot-\d(?:-take-\d)?\.json$/.test(f)).sort();
  for(const file of files){
    const name=file.slice(0,-5),resultPath=join(dir,`operations/${name}.result.json`);
    if(await exists(resultPath)){console.log(`${name}: ${(await readJSON(resultPath)).status}`);continue;}
    const op=await readJSON(join(dir,'operations',file));
    const response=await fetch(buildVertexUrl(projectId,op.model,'fetchPredictOperation'),{
      method:'POST',headers:{Authorization:`Bearer ${accessToken}`,'Content-Type':'application/json'},
      body:JSON.stringify({operationName:op.operationName})});
    if(!response.ok)throw new Error(`Poll HTTP ${response.status}; no resubmission.`);
    const result=await response.json();
    if(!result.done&&!result.error){console.log(`${name}: generating`);continue;}
    const video=result.response?.videos?.[0];
    if(!video){await save(resultPath,{status:'failed',error:result.error||result.response||'Empty terminal result',automaticRetry:false});console.log(`${name}: failed; terminal result saved.`);continue;}
    const out=await downloadVeoVideo({done:true,operationName:op.operationName,video});
    const dest=`clips/${name}.mp4`;
    const raw=op.reverseGeneration?`clips/${name}-generated-reverse.mp4`:dest;
    await copyFile(join(ROOT,'data/video',out.filename),join(dir,raw),1);
    if(op.reverseGeneration)execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',join(dir,raw),
      '-vf','reverse','-af','areverse','-c:v','libx264','-preset','fast','-crf','16','-c:a','aac','-b:a','192k',
      '-movflags','+faststart',join(dir,dest)]);
    await save(resultPath,{status:'completed',video:dest,raw,reverseGeneration:op.reverseGeneration??false,
      original:out,sha256:sha(await readFile(join(dir,dest)))});
    console.log(`${name}: downloaded; visual review pending.`);
  }
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  const [action,directory,id]=process.argv.slice(2);
  const dir=resolve(directory||join(ROOT,'data/workspace/meridian-house/documentary-veo-v1'));
  try{
    if(action==='validate'){await validate(dir);console.log('Reviewed anchors, recipe and authorization verified; no paid request.');}
    else if(action==='submit')await submit(dir,Number(id));
    else if(action==='poll')await poll(dir);
    else throw new Error('Usage: documentary-tour.mjs validate|submit|poll [RUN_DIRECTORY] [SHOT]');
  }catch(e){console.error(e.message);process.exitCode=1;}
}
