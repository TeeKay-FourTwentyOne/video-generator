#!/usr/bin/env node
/** Retain revised deliveries and frame-accurate use records in the clip library. */
import fs from 'node:fs';
import path from 'node:path';
import { workspace, localPath, readJson, hashFile } from '../production/film.mjs';
import { importClip, recordUse } from '../production/clip-library.mjs';
import { budgetSummary, readLedger } from '../../mcp/video-generator/dist/production/ledger.js';

const root = workspace(process.argv[2]);
const projectId = readJson(localPath(root, 'workspace.json')).projectId;
for(const [version,reason] of [
  ['draft-v4-untagged','incomplete colour metadata'],
  ['draft-v4-aac-candidate','AAC channel residue'],
  ['4k-v1-aac-candidate','AAC channel residue']
]) {
  const candidate = localPath(root, `final/${version}/film.mp4`);
  if (fs.existsSync(candidate)) {
    const clip = importClip(candidate, {kind:'derived',collections:[projectId],labels:[`Unused finishing candidate: ${reason}`]});
    fs.writeFileSync(localPath(root, `final/${version}/library.json`), JSON.stringify({clipId:clip.id,decision:`retained unused: ${reason}`},null,2)+'\n');
  }
}
let nativeClip;
for (const version of ['draft-v4','4k-v1']) {
  const folder=localPath(root,`final/${version}`), report=readJson(path.join(folder,'delivery.json'));
  const movie=localPath(root,report.output);
  if(hashFile(movie)!==report.sha256)throw new Error('Delivery changed');
  const check=readJson(localPath(root,`qa/${version}-verification.json`));
  if(check.sha256!==report.sha256 || !check.fullDecode)throw new Error('Verify delivery before importing');
  const clip=importClip(movie,{kind:'delivery',collections:[projectId],labels:[version==='draft-v4'?'Director-trimmed native film':'Director-authorized 4K film']});
  if(version==='draft-v4') {
    nativeClip=clip;
    let at=0;
    for(const [i,s] of report.edit.segments.entries()) {
      recordUse({clipId:s.clipId,projectId,editVersion:`edit/${version}`,segmentIndex:i,shotId:s.shotId,status:'rendered',evidence:'saved-frame-edit',range:{unit:'frames',start:s.inFrame,length:s.frames,fps:30},timelineStartFrame:at,outputSha256:report.sha256});
      at+=s.frames;
    }
  } else {
    recordUse({clipId:nativeClip.id,projectId,editVersion:`edit/${version}`,segmentIndex:0,shotId:'FILM',status:'rendered',evidence:'saved-upscale-recipe',range:{unit:'frames',start:0,length:776,fps:30},timelineStartFrame:0,outputSha256:report.sha256});
  }
  report.budget=budgetSummary(readLedger(localPath(root,'budget.json')));
  report.verification={path:`qa/${version}-verification.json`,sha256:hashFile(localPath(root,`qa/${version}-verification.json`))};
  fs.writeFileSync(path.join(folder,'delivery.json'),JSON.stringify(report,null,2)+'\n');
  fs.writeFileSync(path.join(folder,'library.json'),JSON.stringify({deliveryClipId:clip.id},null,2)+'\n');
  const recipe=path.resolve('data/clips',clip.id,'local-render-recipe.json');
  if(!fs.existsSync(recipe))fs.writeFileSync(recipe,JSON.stringify({projectId,version,parent:report.parent,transform:report.transform,recipe:report.recipe},null,2)+'\n');
  console.log(JSON.stringify({version,clipId:clip.id,frames:776}));
}
