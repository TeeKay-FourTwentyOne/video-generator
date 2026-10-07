// Bounded, resumable Exchange generation. Never retries paid submissions.
import {readFile,writeFile,mkdir,copyFile,access} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'../..');
const run=join(root,'data/workspace/hall-of-memories/exchange-veo-v1');
const hash=b=>createHash('sha256').update(b).digest('hex');
const exists=async p=>{try{await access(p);return true;}catch{return false;}};
const save=(p,o)=>writeFile(p,JSON.stringify(o,null,2)+'\n',{flag:'wx'});
const common='One continuous photoreal cinematic shot, natural real-time human motion, exact identities and worn clothing of supplied anchor, amber hearth light and cool recesses. Locked camera, no cuts, no zoom, no slow motion, no added props, no captions. All characters are adults. No one touches another person. No smiles from the three principals. Sound: distant rowdy adult feast, cups tapping wood, fire crackle, clothing rustle. No intelligible speech, no dialogue, no music.';
const shots=[
  {
    "id": "EX01",
    "anchor": "demand",
    "seconds": 8,
    "action": "The standing dark-haired warrior on LEFT demands a personal reward: briefly tap his own chest with his right hand, then clearly extend that same hand toward the seated adult daughter on RIGHT, and bring it back to his chest. His expression is entitled and insistent. The seated grey-haired chief CENTER keeps his palm up in refusal, slowly shakes his head once. Daughter RIGHT remains unsmiling, tense, arms close, looking at the warrior. Background adult celebrants toast and laugh softly; foreground tension stands apart. There is NO jewel anywhere in this shot. Exactly one warrior, one chief, one adult daughter, distinct background adults. Hands move slowly and individually. Do not reach across faces."
  },
  {
    "id": "EX02",
    "anchor": "resistance",
    "seconds": 4,
    "action": "Tight two-shot: grey-haired chief LEFT and adult daughter RIGHT. The chief slowly shakes his head once at the offscreen warrior to left, palm still raised in refusal. The daughter turns her head and gaze slightly down and right AWAY from the warrior, pulling her shawl close with her existing right hand. Small restrained movement. She remains guarded and unhappy. NO jewel, no hand enters, no added objects. Exactly these two foreground people; background celebrants remain distinct and defocused."
  },
  {
    "id": "EX03",
    "anchor": "offer",
    "seconds": 6,
    "action": "Exactly ONE standing dark-haired warrior in foreground, looking toward offscreen right. His LEFT open palm already holds exactly one broad six-sided emerald with a single pale diagonal inclusion. His RIGHT hand rests at the belt pouch. Slowly raise the open LEFT palm from waist height and extend it a little toward the seated people offscreen right, offering the gem as leverage, then hold. Keep gem solidly resting on palm, face upward, same shape and inclusion, no turning or passing between hands. Keep right hand at belt. His mouth stays closed, expression calmly insistent, no smile. Background adults are separate defocused celebrants. No chief or daughter enters, no new objects. No dialogue. Locked camera."
  },
  {
    "id": "EX04",
    "anchor": "fascination",
    "seconds": 8,
    "action": "Held intimate reaction: the adult woman watches the single green jewel on the single steady male palm at LOWER LEFT. One small blink, shallow breath, attention intensifies, eyes stay down-left on stone. Her mouth remains tight and unsmiling, guarded shoulders. No reaching, no consent gesture, no nodding, no romantic smile. Gem remains still and identical, broad six-sided emerald with ONE pale diagonal inclusion, no glow. The male hand stays steady. Background feast slightly moves out of focus. Exactly one foreground woman, one male hand, chief partial shoulder far left."
  }
];
const action=process.argv[2], id=process.argv[3];
if(action==='prepare'){
 await mkdir(run,{recursive:true});
 const plan=[];
 for(const s of shots){const p=common+'\n\n'+s.action+'\n';await writeFile(join(run,`prompts/${s.id}.txt`),p,{flag:'wx'});plan.push({...s,anchorSHA256:hash(await readFile(join(run,`anchors/${s.anchor}.png`))),promptSHA256:hash(p),estimatedUSD:s.seconds*.4});}
 await save(join(run,'plan.json'),{title:'The Exchange',ceilingUSD:30,nonVeoReserveUSD:6,automaticRetries:false,model:'veo-3.1-prod',resolution:'1080p',aspectRatio:'16:9',generateAudio:true,shots:plan});
 console.log('Prepared four-shot plan.');
}else if(action==='submit'){
 const p=JSON.parse(await readFile(join(run,'plan.json'))),s=p.shots.find(x=>x.id===id);if(!s)throw Error('Unknown shot');
 const review=JSON.parse(await readFile(join(run,'qa/anchor-review.json')));if(review.verdict!=='approved')throw Error('Anchors need review');
 const af=join(run,`anchors/${s.anchor}.png`),prompt=await readFile(join(run,`prompts/${id}.txt`),'utf8');
 if(hash(await readFile(af))!==s.anchorSHA256||hash(prompt)!==s.promptSHA256)throw Error('Reviewed input changed');
 const attempt=join(run,`operations/${id}.attempt.json`);if(await exists(attempt))throw Error('Already attempted; inspect/poll, never resubmit');
 const budget=spawnSync('python3',['tools/veo-budget.py','preflight','--project','hall-exchange','--model','quality','--seconds',String(s.seconds),'--resolution','1080p','--audio','yes','--note',`Exchange ${id}`],{cwd:root,encoding:'utf8'});if(budget.status!==0)throw Error(budget.stderr||budget.stdout);
 await save(attempt,{id,time:new Date().toISOString(),estimatedUSD:s.estimatedUSD,budget:budget.stdout});
 const {submitVeoGeneration}=await import('../../mcp/video-generator/dist/clients/veo.js');
 try{const op=await submitVeoGeneration({prompt,firstFramePath:af,durationSeconds:s.seconds,model:p.model,resolution:p.resolution,aspectRatio:p.aspectRatio,generateAudio:true,seed:9282600+Number(id.slice(2))});await save(join(run,`operations/${id}.json`),op);console.log(`${id}: submitted, $${s.estimatedUSD.toFixed(2)} allocated`);}catch(e){await save(join(run,`operations/${id}.error.json`),{error:String(e)});throw Error(`${id}: submission failed; local error record saved; no retry`);}
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
