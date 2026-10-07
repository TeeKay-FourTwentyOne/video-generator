import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {validate} from './documentary-tour.mjs';

test('documentary submission validation rejects changed media, parameters and authorization',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'documentary-validation-'));
  const hash=x=>createHash('sha256').update(x).digest('hex');
  const plan={project:'meridian-house',automaticRetries:false,
    budget:{proposalApproved:true,authorizedAdditionalUSD:30,retainedPriorAllocationUSD:48.4,currentOperationalCeilingUSD:78.4,maximumVeoRequests:8},
    anchors:[0,1,2,3].map(index=>({index,image:'anchor.png',sha256:hash('anchor')})),
    shots:[0,1,2].map(i=>({id:i+1,start:i,end:i+1,take:1,durationSeconds:8,model:'veo-3.1-prod',resolution:'1080p',aspectRatio:'16:9',generateAudio:true,promptFile:'prompt.txt',promptSHA256:hash('prompt')}))};
  const save=()=>writeFile(join(dir,'plan.json'),JSON.stringify(plan));
  const ledger=join(dir,'ledger.tsv'),check=()=>validate(dir,ledger);
  try{
    await writeFile(ledger,'RESERVE legacy-image\nRESERVE infrastructure\nRESERVE documentary-veo-v1 images\n');
    await writeFile(join(dir,'anchor.png'),'anchor');await writeFile(join(dir,'prompt.txt'),'prompt');
    await writeFile(join(dir,'anchor-review.json'),JSON.stringify({verdict:'approved',anchorHashes:plan.anchors.map(a=>a.sha256)}));
    await save();await check();
    await writeFile(join(dir,'anchor.png'),'changed');await assert.rejects(check(),/anchor bytes changed/);
    await writeFile(join(dir,'anchor.png'),'anchor');
    plan.budget.proposalApproved=false;await save();await assert.rejects(check(),/authorization/);
    plan.budget.proposalApproved=true;plan.shots[0].durationSeconds=6;await save();await assert.rejects(check(),/Shot parameters/);
    plan.shots[0].durationSeconds=8;await save();await writeFile(join(dir,'prompt.txt'),'changed');await assert.rejects(check(),/prompt differ/);
    await writeFile(join(dir,'prompt.txt'),'prompt');plan.anchors[3].image='different.png';await save();await assert.rejects(check(),/canonical file/);
  }finally{await rm(dir,{recursive:true,force:true});}
});
