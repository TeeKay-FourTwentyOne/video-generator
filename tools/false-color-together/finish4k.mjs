#!/usr/bin/env node
/** Film-specific 60 fps finish; shared film loadPlan currently stops at 30 fps. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { importClip, recordUse } from '../production/clip-library.mjs';

const [workspace] = process.argv.slice(2);
if (!workspace) throw new Error('Workspace required');
const root=path.resolve(workspace), version='v1-4k';
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const write=(p,v)=>fs.writeFileSync(path.join(root,p),JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const run=(program,args)=>execFileSync(program,args,{encoding:'utf8',maxBuffer:8*1024*1024});
const base=read('final/v1/delivery.json'), baseFile=path.join(root,base.output);
const source=path.join(root,'render/picture-4k-v1.mp4'), sourceSha=hash(source);
const geometry=read('qa/4k-v1/geometry.json');
const sourceReceipt=read('provenance/picture-4k-v1.mp4.completed.json');
const projectId=read('workspace.json').projectId;
if(hash(baseFile)!==base.sha256 || base.sha256!==read('notes/finish-authorized-2026-11-05.json').baseSha256)
  throw new Error('The authorized base delivery hash changed');
if(!Object.values(base.checks).every(Boolean) || sourceReceipt.sha256!==sourceSha || !geometry.pairedTargetCropsIdentical || !geometry.targetCropStableDuringContextChange)
  throw new Error('Source verification failed');
const probe=JSON.parse(run('ffprobe',['-v','error','-show_streams','-of','json',source])).streams.find(s=>s.codec_type==='video');
if(probe.width!==2160 || probe.height!==3840 || probe.avg_frame_rate!=='60/1' || probe.nb_frames!=='2280')throw new Error('4K counterpart does not match the cut');
let cumulative=0;
for(const segment of base.edit.segments){
  if(segment.clipId!=='clip_fded829d9f17d3b72699477c85b0d760e11bb6538d6c1e2f2d7e95309a50ea8b' || segment.inFrame!==cumulative || segment.fadeInFrames || segment.fadeOutFrames)
    throw new Error('This finish requires the original contiguous full-source edit');
  cumulative+=segment.frames;
}
if(cumulative!==2280)throw new Error('Base edit frame total changed');
execFileSync('node',['tools/production/clips.mjs','analysis','process-project',projectId,'--check'],{stdio:'inherit'});
const folder=path.join(root,'final',version);fs.mkdirSync(folder);
const output=path.join(folder,'film.mp4');
// No duration trim and no audio encoder: retain every original AAC packet.
run('ffmpeg',['-v','error','-n','-i',source,'-i',baseFile,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-movflags','+faststart',output]);
run('ffmpeg',['-v','error','-i',output,'-f','null','-']);
const details=JSON.parse(run('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',output]));
const video=details.streams.find(s=>s.codec_type==='video');
if(video.width!==2160 || video.height!==3840 || video.nb_read_frames!=='2280' || video.avg_frame_rate!=='60/1' || Number(video.duration)!==38)
  throw new Error('Finished timing or geometry differs from v1');
if(['color_space','color_primaries','color_transfer'].some(k=>video[k]!=='bt709') || video.color_range!=='tv')throw new Error('Colour metadata mismatch');
const mediaHash=(file,args)=>run('ffmpeg',['-v','error','-i',file,...args,'-f','hash','-hash','sha256','-']).trim().replace('SHA256=','');
const audioHash=file=>({packets:mediaHash(file,['-map','0:a:0','-c:a','copy']),pcm:mediaHash(file,['-map','0:a:0','-c:a','pcm_s16le','-ac','2','-ar','48000'])});
const audio={base:audioHash(baseFile),output:audioHash(output)};
if(audio.base.packets!==audio.output.packets || audio.base.pcm!==audio.output.pcm)throw new Error('Soundtrack identity check failed');
const picture={source:mediaHash(source,['-map','0:v:0','-c:v','rawvideo']),output:mediaHash(output,['-map','0:v:0','-c:v','rawvideo'])};
if(picture.source!==picture.output)throw new Error('Mux altered decoded 4K pixels');
if(hash(baseFile)!==base.sha256 || hash(source)!==sourceSha)throw new Error('Source changed while finishing');
const clip=importClip(source,{kind:'derived',collections:[projectId]});
const segments=base.edit.segments.map((s,index)=>({index,shotId:s.shotId,baseClipId:s.clipId,clipId:clip.id,sha256:sourceSha,counterpart:'render/picture-4k-v1.mp4',inFrame:s.inFrame,frames:s.frames}));
const descriptionSource='briefs/false-color-together/description.md';
const description=fs.readFileSync(descriptionSource);fs.writeFileSync(path.join(folder,'description.txt'),description,{flag:'wx'});
const outputSha=hash(output);
const report={schemaVersion:1,version,title:base.title,output:`final/${version}/film.mp4`,sha256:outputSha,expected:{frames:2280,seconds:38},probe:details,
  checks:{fullDecode:true,dimensions:true,frameCount:true,baseHash:true,counterpartHashes:true,audioPackets:true,audioPcm:true,decodedPictureUnchanged:true,colourTags:true},
  edit:base.edit,finishing:{role:'finishing-master',baseVersion:'v1',baseOutput:base.output,baseSha256:base.sha256,width:2160,height:3840,segments,
    audio:{streamCopied:true,packetsSha256:{base:audio.base.packets,output:audio.output.packets},pcmSha256:{base:audio.base.pcm,output:audio.output.pcm}},
    pictureSha256:picture,method:'Native rasterization at twice the spatial resolution from the immutable v1 scene. The contiguous 60 fps edit is stream copied with original AAC audio.'},
  audioReview:'Unchanged from v1; full human listening is a separate event.',artisticApproval:false,publication:null,
  description:{path:`final/${version}/description.txt`,sha256:hash(path.join(folder,'description.txt')),source:descriptionSource},
  recipe:{path:'tools/false-color-together/finish4k.mjs',sha256:hash(new URL(import.meta.url))}};
write(`final/${version}/delivery.json`,report);
let at=0;
for(const s of segments){recordUse({clipId:clip.id,projectId,editVersion:`finish/${version}`,segmentIndex:s.index,shotId:s.shotId,status:'rendered',evidence:'saved-finishing-master',range:{unit:'frames',start:s.inFrame,length:s.frames,fps:60},timelineStartFrame:at,outputSha256:outputSha});at+=s.frames;}
const deliveryClip=importClip(output,{kind:'delivery',labels:['FALSE COLOR — TOGETHER: 4K finishing master'],collections:[projectId],tags:['4k','60fps','finishing-master','programmatic']});
for(let i=1;i<=7;i++)fs.copyFileSync(path.join(root,`final/v1/shot-${i}.jpg`),path.join(folder,`shot-${i}.jpg`));
const html=fs.readFileSync(path.join(root,'final/v1/review.html'),'utf8')
  .replace('Together — native review','Together — 4K master')
  .replace('1080 × 1920','2160 × 3840').replace('Native review v1','4K master v1-4k')
  .replace('Geometry and technical checks passed. Phone perception, real-time listening and artistic approval remain open. Working title: Together.',
           'Native 4K rerender. Geometry and technical checks passed. The soundtrack matches v1 packet for packet and sample for sample. Listening and artistic review remain separate.');
fs.writeFileSync(path.join(folder,'review.html'),html,{flag:'wx'});
write('qa/4k-v1/finish-verification.json',{sha256:outputSha,checks:report.checks,audio:report.finishing.audio,picture,baseSha256:base.sha256,sourceSha256:sourceSha});
console.log(JSON.stringify({output:report.output,sha256:outputSha,frames:2280,seconds:38,width:2160,height:3840,checks:report.checks,deliveryClipId:deliveryClip.id},null,2));
