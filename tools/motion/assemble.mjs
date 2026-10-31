#!/usr/bin/env node
/** Join the locally finished camera files without another picture encode. */
import fs from 'node:fs';
import path from 'node:path';
import { workspace, localPath, readJson, hashFile, command, probe } from '../production/film.mjs';
import { importClip, recordUse } from '../production/clip-library.mjs';
import { budgetSummary, readLedger } from '../../mcp/video-generator/dist/production/ledger.js';

const [location, renderVersion, version] = process.argv.slice(2);
if (![renderVersion, version].every(v => /^[a-zA-Z0-9_-]+$/.test(v ?? ''))) throw new Error('Specify safe render and delivery versions');
const root = workspace(location);
const receipt = readJson(localPath(root, `render/${renderVersion}/receipt.json`));
const plan = readJson(localPath(root, 'edit/assembly-plan-v1.json'));
const projectId = readJson(localPath(root, 'workspace.json')).projectId;
const final = localPath(root, `final/${version}`);
if (fs.existsSync(final)) throw new Error('Delivery version exists; preserve it and choose a new version');
const black = localPath(root, `render/${renderVersion}/BLACK.mp4`);
if (!fs.existsSync(black)) command('ffmpeg', ['-v','error','-n','-f','lavfi','-i','color=black:s=1080x1920:r=30','-frames:v','30','-an','-c:v','libx264','-preset','medium','-crf','16','-profile:v','high','-pix_fmt','yuv420p','-g','60','-bf','0','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',black]);
const sources = {};
for (const [id, row] of Object.entries({...receipt.clips, BLACK:{path:`render/${renderVersion}/BLACK.mp4`,sha256:hashFile(black),frames:30}})) {
  const source=localPath(root,row.path);
  if (hashFile(source)!==row.sha256) throw new Error(`Changed source ${id}`);
  const details=probe(source), v=details.streams.find(x=>x.codec_type==='video');
  if (v.width!==1080 || v.height!==1920 || v.avg_frame_rate!=='30/1' || Number(v.nb_frames)!==row.frames) throw new Error(`Invalid local source ${id}`);
  command('ffmpeg',['-v','error','-i',source,'-f','null','-']);
  const clip=importClip(source,{kind:'derived',collections:[projectId],labels:[`Untitled trail-camera film ${id} local camera render`]});
  const decisionFile=`qa/${id}-${renderVersion}-render-acceptance.json`;
  if (!fs.existsSync(localPath(root,decisionFile))) throw new Error(`Review local source first: ${id}`);
  const decision=readJson(localPath(root,decisionFile));
  if (decision.sha256!==row.sha256 || decision.decision!=='keep') throw new Error('Missing local source acceptance');
  sources[id]={...row,clipId:clip.id,decisionFile};
}
const audio=localPath(root,receipt.soundtrack.path);
if (hashFile(audio)!==receipt.soundtrack.sha256) throw new Error('Soundtrack changed');
const segments=[], timeline=[];
let at=0;
for (const beat of receipt.beats.beats) {
  const src=sources[beat.kind==='black'?'BLACK':beat.id];
  segments.push({shotId:beat.id,clipId:src.clipId,sha256:src.sha256,inFrame:0,frames:beat.frames,decisionFile:src.decisionFile});
  timeline.push({label:beat.id,shot:beat.id,frame:at,frames:beat.frames,sourceFrame:0,source:src.path});
  at+=beat.frames;
}
const edit={schemaVersion:1,segments,audio:{path:receipt.soundtrack.path,sha256:receipt.soundtrack.sha256}};
fs.mkdirSync(final);
const concat=segments.map(s=>{
  const beat=receipt.beats.beats.find(b=>b.id===s.shotId);
  const src=sources[beat.kind==='black'?'BLACK':beat.id];
  const relative=path.relative(final,localPath(root,src.path));
  if (relative.includes("'")) throw new Error('Unsupported quote in concat path');
  return `file '${relative}'\ninpoint 0\noutpoint ${(s.frames/30).toFixed(9)}\nduration ${(s.frames/30).toFixed(9)}`;
}).join('\n')+'\n';
fs.writeFileSync(path.join(final,'concat.txt'),concat);
const output=path.join(final,'film.mp4');
command('ffmpeg',['-v','error','-n','-f','concat','-safe','0','-i',path.join(final,'concat.txt'),'-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',String(at/30),'-movflags','+faststart',output]);
command('ffmpeg',['-v','error','-i',output,'-f','null','-']);
const details=JSON.parse(command('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',output]));
const v=details.streams.find(x=>x.codec_type==='video');
if (Number(v.nb_read_frames)!==at || v.width!==1080 || v.height!==1920) throw new Error('Final picture contract failed');
const finalHash=hashFile(output);
const budget=budgetSummary(readLedger(localPath(root,'budget.json')));
if (budget.remainingUsd<0) throw new Error('Budget overrun');
const report={schemaVersion:1,version,title:plan.title,output:`final/${version}/film.mp4`,sha256:finalHash,expected:{frames:at,seconds:at/30},probe:details,checks:{fullDecode:true,dimensions:true,frameCount:true,sourceHashes:true},audioReview:'Procedural stems and computational audio checks; independent real-time listening remains separate.',budget,edit,artisticApproval:false,publication:null,recipe:{path:'tools/motion/assemble.mjs',sha256:hashFile('tools/motion/assemble.mjs')},renderReceipt:{path:`render/${renderVersion}/receipt.json`,sha256:hashFile(localPath(root,`render/${renderVersion}/receipt.json`))}};
fs.writeFileSync(localPath(root,`edit/${version}.json`),JSON.stringify(edit,null,2)+'\n',{flag:'wx'});
fs.writeFileSync(path.join(final,'delivery.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(final,'timeline.json'),JSON.stringify(timeline,null,2)+'\n');
fs.writeFileSync(localPath(root,'film.json'),JSON.stringify(plan,null,2)+'\n');
for (const [i,s] of segments.entries()) recordUse({clipId:s.clipId,projectId,editVersion:`edit/${version}`,segmentIndex:i,shotId:s.shotId,status:'rendered',evidence:'saved-frame-edit',range:{unit:'frames',start:0,length:s.frames,fps:30},timelineStartFrame:timeline[i].frame,outputSha256:finalHash});
// Keep creation evidence for locally authored masters beside their retained copies.
for (const [id,s] of Object.entries(sources)) {
  const privateRecipe=path.resolve('data/clips',s.clipId,'local-render-recipe.json');
  if (!fs.existsSync(privateRecipe)) fs.writeFileSync(privateRecipe,JSON.stringify({projectId,renderVersion,id,source:s,recipe:receipt.recipe,recipeSha256:receipt.recipeSha256,selectionSha256:receipt.selectionSha256},null,2)+'\n');
}
const deliveryClip=importClip(output,{kind:'delivery',collections:[projectId],labels:['Untitled trail-camera film native finished draft']});
fs.writeFileSync(path.join(final,'library.json'),JSON.stringify({deliveryClipId:deliveryClip.id,sources},null,2)+'\n');
console.log(JSON.stringify({output:report.output,sha256:finalHash,frames:at,seconds:at/30,deliveryClipId:deliveryClip.id},null,2));
