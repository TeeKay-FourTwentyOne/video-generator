#!/usr/bin/env node
/** Project-specific stream-copy assembly. Uses maintained acceptance, analysis,
 * library use records and review builder; the computed video is not re-encoded. */
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { validateEdit, review, segmentSource } from '../production/edit.mjs';
import { loadPlan, hashFile, command } from '../production/film.mjs';
import { recordUse } from '../production/clip-library.mjs';
import { readLedger, budgetSummary } from '../../mcp/video-generator/dist/production/ledger.js';

const root=path.resolve(process.argv[2] ?? 'data/workspace/wavefield-v1');
const version=process.argv[3] ?? 'v1';
if (!/^[a-z0-9-]+$/.test(version)) throw new Error('Invalid version');
const copyAudioVersion=process.argv.find(a=>a.startsWith('--copy-audio-from='))?.split('=')[1];
if (copyAudioVersion && !/^[a-z0-9-]+$/.test(copyAudioVersion)) throw new Error('Invalid audio base version');
const plan=loadPlan(root);
const edit=JSON.parse(fs.readFileSync(path.join(root,`edit/${version}.json`)));
const expected=validateEdit(root,edit,plan);
let end=0;
for (const s of edit.segments) {
  if (s.clipId!==edit.segments[0].clipId || s.inFrame!==end || s.fadeInFrames || s.fadeOutFrames)
    throw new Error('Stream copy requires one continuous, unmodified source range.');
  end+=s.frames;
}
const source=segmentSource(root,edit.segments[0]);
const sourceProbe=JSON.parse(command('ffprobe',['-v','error','-show_streams','-of','json',source]));
if (Number(sourceProbe.streams.find(s=>s.codec_type==='video').nb_frames)!==end)
  throw new Error('The complete source must equal the edit.');
const analysis=spawnSync(process.execPath,['--max-old-space-size=16384','tools/production/clips.mjs',
  'analysis','process-project','wavefield','--check'],{encoding:'utf8',maxBuffer:64*1024*1024});
fs.writeFileSync(path.join(root,`qa/delivery-analysis-check-${version}.log`),`${analysis.stdout??''}\n${analysis.stderr??''}`);
if (analysis.status!==0) throw new Error('Maintained project analysis check did not pass. See the retained log.');
let audioInput=path.join(root,edit.audio.path),audioBase;
if (copyAudioVersion) {
  audioBase=JSON.parse(fs.readFileSync(path.join(root,'final',copyAudioVersion,'delivery.json')));
  audioInput=path.join(root,audioBase.output);
  if (audioBase.expected.frames!==expected.frames || audioBase.edit.audio.sha256!==edit.audio.sha256
      || hashFile(audioInput)!==audioBase.sha256) throw new Error('Base soundtrack does not match the current edit.');
}
const folder=path.join(root,'final',version);
fs.mkdirSync(folder);
const output=path.join(folder,'film.mp4');
command('ffmpeg',['-v','error','-n','-i',source,'-i',audioInput,
  '-map','0:v:0','-map','1:a:0','-c:v','copy',
  '-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
  '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',
  ...(copyAudioVersion?['-c:a','copy']:['-c:a','aac','-b:a','256k','-ar','48000']),
  '-t',String(expected.seconds),'-movflags','+faststart',output]);
command('ffmpeg',['-v','error','-i',output,'-f','null','-']);
const probe=JSON.parse(command('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',output]));
const v=probe.streams.find(s=>s.codec_type==='video');
if (Number(v.nb_read_frames)!==expected.frames || v.width!==plan.width || v.height!==plan.height)
  throw new Error('Native delivery differs from the frame contract.');
if (['color_space','color_transfer','color_primaries'].some(k=>v[k]!=='bt709') || v.color_range!=='tv')
  throw new Error('Native delivery color tags do not match the renderer.');
const sourceSha=edit.segments[0].clipId.slice(5);
if (hashFile(source)!==sourceSha || hashFile(path.join(root,edit.audio.path))!==edit.audio.sha256)
  throw new Error('An input changed during assembly.');
const deliveredEdit={...edit,segments:edit.segments.map(s=>({...s,sha256:sourceSha}))};
let audioCopy;
if (copyAudioVersion) {
  const audioHash=(file,codec)=>command('ffmpeg',['-v','error','-i',file,'-map','0:a:0','-c:a',codec,
    '-f','hash','-hash','sha256','-']).trim().replace(/^SHA256=/,'');
  const packetSha256=audioHash(output,'copy'),decodedPcmSha256=audioHash(output,'pcm_f32le');
  if (packetSha256!==audioHash(audioInput,'copy') || decodedPcmSha256!==audioHash(audioInput,'pcm_f32le')
      || hashFile(audioInput)!==audioBase.sha256) throw new Error('Copied soundtrack identity check failed.');
  audioCopy={baseVersion:copyAudioVersion,baseArtifactSha256:audioBase.sha256,packetSha256,decodedPcmSha256,verified:true};
}
const report={schemaVersion:1,version,title:plan.title,output:path.relative(root,output),sha256:hashFile(output),
  expected,probe,checks:{fullDecode:true,dimensions:true,frameCount:true,sourceHashes:true,colorMetadata:true},
  assemblyMethod:`continuous-picture-stream-copy; six logical milestone ranges; ${copyAudioVersion?'base soundtrack stream copied':'prepared soundtrack encoded once'}`,
  ...(audioCopy?{audioCopy}:{}),
  audioReview:'Technical measurements and source synthesis verified; full human listening remains pending.',
  budget:budgetSummary(readLedger(path.join(root,'budget.json'))),edit:deliveredEdit,artisticApproval:false,publication:null};
fs.writeFileSync(path.join(folder,'delivery.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
let at=0;
for (const [i,s] of deliveredEdit.segments.entries()) {
  recordUse({clipId:s.clipId,projectId:'wavefield',editVersion:`edit/${version}`,segmentIndex:i,
    shotId:s.shotId,status:'rendered',evidence:'continuous-frame-verified-stream-copy',
    range:{unit:'frames',start:s.inFrame,length:s.frames,fps:plan.fps},timelineStartFrame:at,outputSha256:report.sha256});
  at+=s.frames;
}
review(root,version);
const page=path.join(folder,'review.html');
let markup=fs.readFileSync(page,'utf8');
const status=JSON.parse(fs.readFileSync(path.join(root,'status/artifact.json')));
const calculation=new URL(version==='v1'?'calculation.html':`calculation-${version}.html`,status.url).href;
markup=markup.replace('All images and motion are fictional generated material.',
  `An approach through overlapping light toward a single intersection. <a href="${calculation}">Explore the computed wave fields</a>.`);
fs.writeFileSync(page,markup);
console.log(JSON.stringify({output:report.output,sha256:report.sha256,...expected,checks:report.checks},null,2));
