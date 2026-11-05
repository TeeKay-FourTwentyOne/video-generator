#!/usr/bin/env node
/** Local 60 fps delivery. The shared editor currently accepts only 24/25/30 fps. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { recordUse } from '../production/clip-library.mjs';
import { measure } from '../production/mix.mjs';

const [workspace, version = 'v1'] = process.argv.slice(2);
if (!workspace || !/^[a-z0-9-]+$/.test(version)) throw new Error('Workspace and a new version required');
const root = path.resolve(workspace);
const read = p => JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const hash = p => createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const write = (p, value) => fs.writeFileSync(path.join(root,p),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const source = path.join(root,'render/picture-v1.mp4');
const soundtrack = path.join(root,'audio/mix-master-v1.wav');
const sourceSha = hash(source), audioSha = hash(soundtrack);
const clipId = `clip_${sourceSha}`;
const identity = read('workspace.json');
const geometry = read('qa/geometry.json');
if (!geometry.pairedTargetCropsIdentical || !geometry.targetCropStableDuringContextChange || geometry.maxPathPerpendicularErrorPixels > 1e-9)
  throw new Error('Geometry verification failed');
// This is an independent 60 fps editor; still require the maintained analysis gate.
execFileSync('node',['tools/production/clips.mjs','analysis','process-project',identity.projectId,'--check'],{stdio:'inherit'});
const folder = path.join(root,'final',version);
fs.mkdirSync(folder,{recursive:false});
const output = path.join(folder,'film.mp4');
execFileSync('ffmpeg',['-v','error','-n','-i',source,'-i',soundtrack,'-map','0:v:0','-map','1:a:0',
  '-c:v','copy','-bsf:v','h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
  '-c:a','aac','-b:a','192k','-ar','48000','-t','38','-movflags','+faststart',output]);
execFileSync('ffmpeg',['-v','error','-i',output,'-f','null','-']);
const probe = JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',output],{encoding:'utf8'}));
const video = probe.streams.find(s=>s.codec_type==='video');
if (video.width!==1080 || video.height!==1920 || video.nb_read_frames!=='2280' || video.avg_frame_rate!=='60/1') throw new Error('Delivery geometry mismatch');
if (video.color_primaries!=='bt709' || video.color_transfer!=='bt709' || video.color_space!=='bt709' || video.color_range!=='tv') throw new Error('Delivery colour tags missing');
const decodedHash = file => execFileSync('ffmpeg',['-v','error','-i',file,'-map','0:v:0','-f','hash','-hash','sha256','-'],{encoding:'utf8'}).trim();
const sourcePictureHash = decodedHash(source), finalPictureHash = decodedHash(output);
if(sourcePictureHash!==finalPictureHash)throw new Error('Mux changed decoded picture');
const timeline = read('edit/timeline.json');
const decision = {sha256:sourceSha,decision:'keep',startFrame:0,endFrameExclusive:2280,
  notes:'Exact local stimuli. Source frames and dense transition strips inspected; target masks match and all Tusi trajectories are straight. Perceptual effect strength and director approval remain open.'};
write('qa/source-v1.json',decision);
const edit={schemaVersion:1,segments:timeline.segments.map(s=>({shotId:s.shot,clipId,inFrame:s.sourceFrame,frames:s.frames,decisionFile:'qa/source-v1.json'})),audio:{path:'audio/mix-master-v1.wav',sha256:audioSha}};
write(`edit/${version}.json`,edit);
const outputSha=hash(output);
const audio=measure(output);
const report={schemaVersion:1,version,title:'FALSE COLOR — TOGETHER',output:`final/${version}/film.mp4`,sha256:outputSha,
  expected:{frames:2280,seconds:38},probe,checks:{fullDecode:true,dimensions:true,frameCount:true,sourceHashes:hash(source)===sourceSha&&hash(soundtrack)===audioSha,decodedPictureUnchanged:true,colourTags:true},
  sourcePictureHash,finalPictureHash,audioMeasurement:audio,edit,
  audioReview:'Computational measurement only; full real-time listening remains open.',artisticApproval:false,publication:null,
  localMethod:'Deterministic 60 fps source with original synthesized score. Video stream copied; H.264 colour tags set explicitly.',
  recipe:{path:'tools/false-color-together/assemble.mjs',sha256:hash(new URL(import.meta.url))}};
write(`final/${version}/delivery.json`,report);
for(const [i,s] of timeline.segments.entries())recordUse({clipId,projectId:identity.projectId,editVersion:`edit/${version}`,segmentIndex:i,shotId:s.shot,status:'rendered',evidence:'saved-frame-edit',range:{unit:'frames',start:s.sourceFrame,length:s.frames,fps:60},timelineStartFrame:s.frame,outputSha256:outputSha});
const scenes = read('film.json').shots;
const cards=timeline.segments.map((s,i)=>{
  execFileSync('ffmpeg',['-v','error','-n','-ss',String((s.frame+s.frames/2)/60),'-i',output,'-frames:v','1','-vf','scale=270:-2',path.join(folder,`shot-${i+1}.jpg`)]);
  return `<button data-frame="${s.frame}"><img src="shot-${i+1}.jpg" alt="${s.shot}"><b>${s.shot} · ${(s.frame/60).toFixed(1)}s</b><span>${scenes[i].beat}</span></button>`;
}).join('');
const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Together — native review</title>
<style>*{box-sizing:border-box}body{background:#0b0f17;color:#eae6d7;font:16px/1.5 system-ui;margin:0}main{max-width:1200px;margin:auto;padding:28px}h1{font-size:38px;margin:0}p{color:#9aabbc}.layout{display:grid;grid-template-columns:minmax(280px,430px) 1fr;gap:30px}video{width:100%;max-height:79vh}aside{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;align-content:start}button{background:#151d28;color:inherit;border:1px solid #2a3949;padding:0;text-align:left;cursor:pointer;border-radius:6px;overflow:hidden}button img{width:100%}b,span{display:block;padding:5px 10px}span{font-size:12px;color:#acbac8}.transport button{padding:7px 12px}a{color:#3acaf7}#tc{font:14px ui-monospace,monospace}footer{font-size:13px;color:#9aabbc;margin-top:22px}@media(max-width:760px){main{padding:16px}.layout{display:block}aside{margin-top:22px}h1{font-size:30px}}</style>
<main><h1>FALSE COLOR — TOGETHER</h1><p>38 seconds · 1080 × 1920 · 60 fps · Native review ${version}</p><div class="layout"><div><video id="film" controls playsinline preload="metadata" src="film.mp4"></video><p id="tc">0.000 s · frame 0</p><div class="transport"><button id="back">−1 frame</button> <button id="forward">+1 frame</button> <button id="copy">Copy time</button></div><p><a href="film.mp4">Open film</a> · <a href="delivery.json">Technical evidence</a></p></div><aside>${cards}</aside></div><footer>Original programmatic picture and synthesized sound. Geometry and technical checks passed. Phone perception, real-time listening and artistic approval remain open. Working title: Together.</footer></main>
<script>const v=document.getElementById('film'),tc=document.getElementById('tc');const show=()=>tc.textContent=v.currentTime.toFixed(3)+' s · frame '+Math.min(2279,Math.round(v.currentTime*60));v.addEventListener('timeupdate',show);v.addEventListener('seeked',show);document.querySelectorAll('[data-frame]').forEach(b=>b.onclick=()=>{v.pause();v.currentTime=Number(b.dataset.frame)/60;show()});document.getElementById('back').onclick=()=>{v.pause();v.currentTime=Math.max(0,Math.round(v.currentTime*60)-1)/60};document.getElementById('forward').onclick=()=>{v.pause();v.currentTime=Math.min(2279,Math.round(v.currentTime*60)+1)/60};document.getElementById('copy').onclick=()=>navigator.clipboard.writeText(tc.textContent);</script></html>`;
fs.writeFileSync(path.join(folder,'review.html'),html,{flag:'wx'});
console.log(JSON.stringify({output:report.output,sha256:outputSha,frames:2280,seconds:38,audio,checks:report.checks},null,2));
