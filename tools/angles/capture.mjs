#!/usr/bin/env node
import {readFile,mkdir,writeFile,copyFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {startServer} from '../scene-lab/server.mjs';
import {openBrowser} from '../scene-lab/chrome.mjs';
import {buildScene,cameraAt,SHOTS,DURATION,POSE_FPS,OUTPUT_FPS} from './scene.mjs';

const args=Object.fromEntries(process.argv.slice(2).map(a=>a.replace(/^--/,'').split('=')));
const output=resolve(args.output??`data/workspace/angles/audition-${Date.now()}`);
const size=Number(args.size??720),stills=args.stills==='true',look=Number(args.look??0);
if(![360,540,720,1080].includes(size))throw new Error('Choose native 360, 540, 720 or 1080; 4K is deferred.');
const width=size*16/9;
const html='<!doctype html><meta charset="utf-8"><title>ANGLES render</title><canvas></canvas><script type="module" src="/angles-app.mjs"></script>';
const app="import {createRenderer} from './angles-renderer.mjs';try{window.sceneLab=createRenderer(document.querySelector('canvas'));}catch(e){window.sceneLabError=String(e.stack||e);}";
const assets=new Map([
 ['index.html',{contentType:'text/html',body:html}],['angles-app.mjs',{contentType:'text/javascript',body:app}],
 ['angles-renderer.mjs',{contentType:'text/javascript',body:(await readFile(new URL('renderer.mjs',import.meta.url),'utf8')).replace("'./scene.mjs'","'./angles-scene.mjs'")}],
 ['angles-scene.mjs',{contentType:'text/javascript',body:await readFile(new URL('scene.mjs',import.meta.url))}],
]);
await mkdir(output,{recursive:false});await mkdir(join(output,'frames'));await mkdir(join(output,'qa'));await mkdir(join(output,'recipe'));
for(const file of ['scene.mjs','renderer.mjs','capture.mjs'])await copyFile(new URL(file,import.meta.url),join(output,'recipe',file));
const scene=buildScene(),sceneHash=createHash('sha256').update(JSON.stringify(scene)).digest('hex');
const manifest={schema:1,title:'ANGLES / opposed surfaces',status:'first visual audition',size:[width,size],duration:DURATION,poseFPS:POSE_FPS,outputFPS:OUTPUT_FPS,scene,sceneHash,shots:SHOTS,frames:[],look,
  provenance:{method:'Local analytic 3D ray tracing in WebGL 2, three specular bounces with analytic studio fill and four subpixel samples; procedural machining marks. Persistent geometry and object-local texture. No captured metrology data.',providerCalls:0,apiCostUSD:0},
  constraints:{cameraOrigin:[0,0,0],aspect:'16:9',upscale:false,fourKDeferred:true,motionBlur:false,opticalFlow:false,audio:'silent visual audition'},
};
const {server,url}=await startServer(0,assets);let browser;
try{
 browser=await openBrowser(url);manifest.renderer=await browser.evaluate('sceneLab.info');console.log(manifest.renderer);
 const jobs=stills?[
  ...[0,3,6,8,10.5,13,16.5,19,21,24,25.5,29.875].map(time=>({time,look})),
  {time:0,baseline:true,look},{time:0,look:1},{time:0,look:2},{time:0,mode:1},{time:0,mode:2},{time:0,mode:3}
 ]:Array.from({length:DURATION*POSE_FPS},(_,i)=>({time:i/POSE_FPS,look}));
 for(let i=0;i<jobs.length;i++){
  const request={...jobs[i],width,height:size};
  const result=await browser.evaluateLarge(`sceneLab.render(${JSON.stringify(request)})`);
  const bytes=Buffer.from(result.png.split(',')[1],'base64'),name=`frames/frame-${String(i).padStart(4,'0')}.png`;
  await writeFile(join(output,name),bytes,{flag:'wx'});delete result.png;
  manifest.frames.push({index:i,...result,path:name,sha256:createHash('sha256').update(bytes).digest('hex')});
  if(i%8===0||i===jobs.length-1)console.log(`${i+1}/${jobs.length} frames`);
 }
 // Independent repeated render must return exactly to the first view.
 const again=await browser.evaluateLarge(`sceneLab.render(${JSON.stringify({time:0,width,height:size,look})})`);
 const againHash=createHash('sha256').update(Buffer.from(again.png.split(',')[1],'base64')).digest('hex');
 manifest.qa={deterministicReturn:againHash===manifest.frames[0].sha256,allCamerasAtCenter:manifest.frames.every(f=>f.camera.eye.every(v=>v===0)),webglErrors:0};
 if(!Object.values(manifest.qa).every(v=>v===true||v===0))throw new Error('Geometry/camera verification failed.');
 await writeFile(join(output,'manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
 await copyFile(join(output,'frames/frame-0000.png'),join(output,'poster.png'));
 if(!stills){
  const result=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-framerate',String(POSE_FPS),'-i',join(output,'frames/frame-%04d.png'),'-vf',`fps=${OUTPUT_FPS},setsar=1`,'-c:v','libx264','-crf','17','-preset','slow','-pix_fmt','yuv420p','-an','-movflags','+faststart',join(output,'angles-audition.mp4')],{stdio:'inherit'});
  if(result.status!==0)throw new Error('FFmpeg encoding failed');
 }
 console.log(`Saved ${output}`);
}finally{await browser?.close();await new Promise(r=>server.close(r));}
