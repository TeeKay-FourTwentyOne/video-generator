// Bounded, resumable Exchange generation. Never retries paid submissions.
import {readFile,writeFile,mkdir,copyFile,access} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'../..');
const spec=JSON.parse(await readFile(join(root,'tools/hall-of-memories/exchange_dark.json')));
const run=join(root,spec.run);
const hash=b=>createHash('sha256').update(b).digest('hex');
const exists=async p=>{try{await access(p);return true;}catch{return false;}};
const save=(p,o)=>writeFile(p,JSON.stringify(o,null,2)+'\n',{flag:'wx'});
const common=spec.common;
const shots=spec.shots.map(s=>({...s,anchor:s.id,action:s.prompt}));
const action=process.argv[2], id=process.argv[3];
if(action==='prepare'){
 await mkdir(run,{recursive:true});
 const plan=[];
 for(const s of shots){const p=common+'\n\n'+s.action+'\n';await writeFile(join(run,`prompts/${s.id}.txt`),p,{flag:'wx'});plan.push({...s,anchorSHA256:hash(await readFile(join(run,`anchors/${s.anchor}.png`))),promptSHA256:hash(p),estimatedUSD:s.seconds*.4});}
 await save(join(run,'plan.json'),{title:spec.title,ceilingUSD:30,nonVeoReserveUSD:12,automaticRetries:false,model:'veo-3.1-prod',resolution:'1080p',aspectRatio:'16:9',generateAudio:true,shots:plan});
 console.log('Prepared seven-shot dark sequence.');
}else if(action==='submit'){
 const p=JSON.parse(await readFile(join(run,'plan.json'))),s=p.shots.find(x=>x.id===id);if(!s)throw Error('Unknown shot');
 const review=JSON.parse(await readFile(join(run,'qa/anchor-review.json')));if(review.verdict!=='approved')throw Error('Anchors need review');
 const af=join(run,`anchors/${s.anchor}.png`),prompt=await readFile(join(run,`prompts/${id}.txt`),'utf8');
 if(hash(await readFile(af))!==s.anchorSHA256||hash(prompt)!==s.promptSHA256)throw Error('Reviewed input changed');
 const attempt=join(run,`operations/${id}.attempt.json`);if(await exists(attempt))throw Error('Already attempted; inspect/poll, never resubmit');
 const budget=spawnSync('python3',['tools/veo-budget.py','preflight','--project','hall-exchange','--model','quality','--seconds',String(s.seconds),'--resolution','1080p','--audio','yes','--note',`Exchange ${id}`],{cwd:root,encoding:'utf8'});if(budget.status!==0)throw Error(budget.stderr||budget.stdout);
 await save(attempt,{id,time:new Date().toISOString(),estimatedUSD:s.estimatedUSD,budget:budget.stdout});
 const {submitVeoGeneration}=await import('../../mcp/video-generator/dist/clients/veo.js');
 try{const op=await submitVeoGeneration({prompt,firstFramePath:af,durationSeconds:s.seconds,model:p.model,resolution:p.resolution,aspectRatio:p.aspectRatio,generateAudio:true,seed:9292600+Number(id.slice(1))});await save(join(run,`operations/${id}.json`),op);console.log(`${id}: submitted, $${s.estimatedUSD.toFixed(2)} allocated`);}catch(e){await save(join(run,`operations/${id}.error.json`),{error:String(e)});throw Error(`${id}: submission failed; local error record saved; no retry`);}
}else if(action==='poll'){
 const {downloadVeoVideo}=await import('../../mcp/video-generator/dist/clients/veo.js');
 const {getGoogleAccessToken,buildVertexUrl}=await import('../../mcp/video-generator/dist/clients/google-auth.js');
 const {accessToken,projectId}=await getGoogleAccessToken();
 const plan=JSON.parse(await readFile(join(run,'plan.json')));
 for(const s of plan.shots){
  const opf=join(run,`operations/${s.id}.json`),done=join(run,`operations/${s.id}.result.json`);
  if(!await exists(opf)||await exists(done))continue;
  const op=JSON.parse(await readFile(opf));
  const response=await fetch(buildVertexUrl(projectId,op.model,'fetchPredictOperation'),{method:'POST',headers:{Authorization:`Bearer ${accessToken}`,'Content-Type':'application/json'},body:JSON.stringify({operationName:op.operationName})});
  if(!response.ok)throw Error(`Poll HTTP ${response.status}`);
  const raw=await response.json();
  if(!raw.done){console.log(`${s.id}: generating`);continue;}
  const video=raw.response?.videos?.[0];
  if(!video){await save(done,{status:'terminal-no-video',response:raw});console.log(`${s.id}: terminal without video; no retry`);continue;}
  const r={done:true,operationName:op.operationName,video};
  const d=await downloadVeoVideo(r);
  await copyFile(join(root,'data/video',d.filename),join(run,`clips/${s.id}.mp4`),1);
  await save(done,{...r,download:d});console.log(`${s.id}: downloaded`);
 }
}else throw Error('Use prepare | submit EX01..EX04 | poll');
