// Existing Vertex client, explicit quality/native settings, and one attempt per shot.
import {readFile,writeFile,mkdir,copyFile,access} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'../..');
const [action,draftText,id]=process.argv.slice(2);const draft=Number(draftText);
if(![2,3].includes(draft))throw Error('Use draft 2 or 3');
const run=join(root,`data/workspace/carnival-dream/draft-v${draft}`);
const plan=JSON.parse(await readFile(join(run,'generation/plan.json'),'utf8'));
const exists=async p=>{try{await access(p);return true;}catch{return false;}};
const save=(p,o)=>writeFile(p,JSON.stringify(o,null,2)+'\n',{flag:'wx'});
const hash=b=>createHash('sha256').update(b).digest('hex');
if(action==='submit'){
 const s=plan.shots.find(s=>s.id===id);if(!s)throw Error('Unknown shot');
 const review=JSON.parse(await readFile(join(run,'qa/anchor-acceptance.json'),'utf8'));
 if(review.shots?.[id]?.status!=='approved')throw Error('Reviewed anchors required');
 const first=join(run,s.first),last=join(run,s.last),prompt=await readFile(join(run,s.prompt),'utf8');
 for(const [p,h] of [[first,s.first_sha256],[last,s.last_sha256]])if(hash(await readFile(p))!==h)throw Error('Anchor changed after preparation');
 if(hash(prompt)!==s.prompt_sha256)throw Error('Prompt changed after preparation');
 const attempt=join(run,`operations/${id}-video.attempt.json`);
 if(await exists(attempt))throw Error('Already attempted; poll or inspect, never resubmit');
 const {getGoogleAccessToken}=await import('../../mcp/video-generator/dist/clients/google-auth.js');
 await getGoogleAccessToken();
 const gate=spawnSync(plan.python,['tools/carnival-dream/api_budget.py','--draft',String(draft),'--id',`${id}-video`,'--usd',String(s.seconds*.4),'--category','veo-quality','--note',`${id} native paper performance accent; conservative audio-tier reserve`,'--veo-seconds',String(s.seconds)],{cwd:root,encoding:'utf8'});
 if(gate.status!==0)throw Error('Budget preflight denied; no submission');
 await save(attempt,{id,seconds:s.seconds,time:new Date().toISOString(),reservedUSD:s.seconds*.4,estimatedSilentUSD:s.seconds*.2,budgetPreflight:gate.stdout});
 const {submitVeoGeneration}=await import('../../mcp/video-generator/dist/clients/veo.js');
 try{
  const op=await submitVeoGeneration({prompt,firstFramePath:first,lastFramePath:last,durationSeconds:s.seconds,model:'veo-3.1-prod',resolution:'1080p',aspectRatio:'16:9',generateAudio:false,seed:9282600+draft*100+Number(id.slice(-2))});
  await save(join(run,`operations/${id}-video.operation.json`),op);console.log(`${id}: submitted once`);
 }catch(e){await save(join(run,`operations/${id}-video.error.json`),{error:String(e)});throw Error(`${id}: submission failed; details local; no retry`);}
}else if(action==='poll'){
 const {downloadVeoVideo}=await import('../../mcp/video-generator/dist/clients/veo.js');
 const {getGoogleAccessToken,buildVertexUrl}=await import('../../mcp/video-generator/dist/clients/google-auth.js');
 const {accessToken,projectId}=await getGoogleAccessToken();
 for(const s of plan.shots){
  const opf=join(run,`operations/${s.id}-video.operation.json`),done=join(run,`operations/${s.id}-video.result.json`);
  if(!await exists(opf)||await exists(done))continue;
  const op=JSON.parse(await readFile(opf,'utf8'));
  const response=await fetch(buildVertexUrl(projectId,op.model,'fetchPredictOperation'),{method:'POST',headers:{Authorization:`Bearer ${accessToken}`,'Content-Type':'application/json'},body:JSON.stringify({operationName:op.operationName})});
  if(!response.ok)throw Error(`Poll HTTP ${response.status}`);
  const raw=await response.json();if(!raw.done){console.log(`${s.id}: generating`);continue;}
  const video=raw.response?.videos?.[0];
  if(!video){await save(done,{status:'terminal-no-video',response:raw});console.log(`${s.id}: no video; no retry`);continue;}
  const result={done:true,operationName:op.operationName,video};const download=await downloadVeoVideo(result);
  await copyFile(join(root,'data/video',download.filename),join(run,`clips/${s.id}.mp4`),1);
  await save(done,{status:'downloaded',...result,download,estimatedUSD:s.seconds*.2});console.log(`${s.id}: downloaded`);
 }
}else throw Error('Use submit <draft> <shot> or poll <draft>');
