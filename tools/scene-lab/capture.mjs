#!/usr/bin/env node
import { mkdir, writeFile, readFile, access, copyFile } from 'node:fs/promises';
import { constants } from 'node:fs';
import { resolve, join, dirname, extname } from 'node:path';
import { spawn } from 'node:child_process';
import { startServer } from './server.mjs';
import { openBrowser } from './chrome.mjs';
import { buildScene, exportOBJ } from './scene.mjs';
import { SHOTS } from './math.mjs';
import { geometryHash, validateReference } from './reference.mjs';

const HELP=`Scene Lab — entirely local 3D frames and timelapse video

  node tools/scene-lab/capture.mjs [options]

  --output=PATH       New output directory (default data/workspace/meridian-<timestamp>)
  --aspect=both       both, 16:9, or 9:16
  --shot=sweep        sweep or tour
  --fps=6            Unique samples per second; output is 24 fps with held frames
  --duration=24      Seconds per complete shot (two revolutions for sweep)
  --size=720         Short edge in pixels, divisible by 18 (720 -> 1280 × 720)
  --references=8     Number of source camera bundles from the first revolution
  --projections=PATH JSON array of {image, camera} paths for approved local images
  --no-video         Export frames without running ffmpeg

Requires Node 22+, installed Chrome/Chromium, and ffmpeg for MP4.
No image generation, uploads, or credentials. Existing output folders are refused.
`;
function parseArgs(argv) {
  const options={aspect:'both',shot:'sweep',fps:6,duration:24,size:720,references:8,video:true};
  const known=new Set(['output','aspect','shot','fps','duration','size','references','projections']);
  for(const arg of argv){
    if(arg==='--help'){console.log(HELP);return null;}
    if(arg==='--no-video'){options.video=false;continue;}
    const match=arg.match(/^--([^=]+)=(.+)$/);
    if(!match||!known.has(match[1]))throw new Error(`Unknown argument: ${arg}. Use --help.`);
    options[match[1]]=['fps','duration','size','references'].includes(match[1])?Number(match[2]):match[2];
  }
  if(!['both','16:9','9:16'].includes(options.aspect))throw new Error('Aspect must be both, 16:9, or 9:16.');
  if(!(options.shot in SHOTS))throw new Error('Shot must be sweep or tour.');
  if(!Number.isInteger(options.fps)||![1,2,3,4,6,8,12,24].includes(options.fps))throw new Error('FPS must divide 24: 1, 2, 3, 4, 6, 8, 12, or 24.');
  if(!Number.isFinite(options.duration)||options.duration<2||options.duration>120||!Number.isInteger(options.duration*options.fps)||!Number.isInteger(options.duration*24))throw new Error('Duration must be 2–120 seconds and produce whole frame counts.');
  if(options.shot==='sweep'&&(options.duration*options.fps)%2)throw new Error('Two-sweep capture requires an even sample count.');
  if(!Number.isInteger(options.size)||options.size<144||options.size>2160||options.size%18)throw new Error('Size must be 144–2160 and divisible by 18.');
  if(!Number.isInteger(options.references)||options.references<1||options.references>32)throw new Error('References must be an integer from 1 to 32.');
  return options;
}
function command(executable,args){return new Promise((resolve,reject)=>{
  const child=spawn(executable,args,{stdio:['ignore','ignore','pipe']});let errors='';
  child.stderr.on('data',chunk=>{errors=(errors+chunk).slice(-6000);});child.on('error',reject);
  child.on('close',code=>code===0?resolve():reject(new Error(`${executable} failed (${code}): ${errors}`)));
});}
const json=(path,value)=>writeFile(path,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const png=(path,dataURL)=>writeFile(path,Buffer.from(dataURL.split(',')[1],'base64'),{flag:'wx'});

async function main(){
  const options=parseArgs(process.argv.slice(2));if(!options)return;
  if(options.video)await command('ffmpeg',['-version']);
  const scene=buildScene(),projections=[];
  if(options.projections){
    const source=resolve(options.projections),entries=JSON.parse(await readFile(source,'utf8'));
    if(!Array.isArray(entries)||entries.length>8)throw new Error('Projections must be an array of at most 8 {image, camera} pairs.');
    for(const entry of entries){
      if(!entry||typeof entry.image!=='string'||typeof entry.camera!=='string')throw new Error('Each projection needs image and camera file paths.');
      const imagePath=resolve(dirname(source),entry.image),cameraPath=resolve(dirname(source),entry.camera);
      const mime={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}[extname(imagePath).toLowerCase()];
      if(!mime)throw new Error('Projection images must be PNG, JPEG, or WebP.');
      projections.push({dataURL:`data:${mime};base64,${(await readFile(imagePath)).toString('base64')}`,reference:validateReference(JSON.parse(await readFile(cameraPath,'utf8')),scene)});
    }
  }
  const output=resolve(options.output||`data/workspace/meridian-${new Date().toISOString().replace(/[:.]/g,'-')}`);
  try{await access(output);throw new Error(`Output directory already exists: ${output}. Choose a new run directory.`);}catch(error){if(error.code!=='ENOENT')throw error;}
  const assets=new Map(projections.map((p,i)=>[`capture-projector-${i}`,{contentType:p.dataURL.slice(5,p.dataURL.indexOf(';')),body:Buffer.from(p.dataURL.split(',')[1],'base64')}]));
  const {server,url}=await startServer(0,assets);let browser;
  try{
    browser=await openBrowser(url);
    await mkdir(output,{recursive:true});
    const model=exportOBJ(scene);
    await mkdir(join(output,'model'));
    await writeFile(join(output,'model/meridian-house.obj'),model.obj,{flag:'wx'});
    await writeFile(join(output,'model/meridian-house.mtl'),model.mtl,{flag:'wx'});
    await json(join(output,'model/scene.json'),{id:scene.id,geometryHash:geometryHash(scene.vertices),description:scene.description,rooms:scene.rooms,objects:scene.objects});
    const savedProjections=[];
    if(projections.length){
      await mkdir(join(output,'projections'));
      for(let i=0;i<projections.length;i++){
        const projection=projections[i],extension=projection.dataURL.startsWith('data:image/jpeg')?'jpg':projection.dataURL.startsWith('data:image/webp')?'webp':'png';
        const prefix=`projections/projector-${String(i).padStart(2,'0')}`;
        await writeFile(join(output,`${prefix}.${extension}`),Buffer.from(projection.dataURL.split(',')[1],'base64'),{flag:'wx'});
        await json(join(output,`${prefix}.camera.json`),projection.reference);
        savedProjections.push({image:`${prefix}.${extension}`,camera:`${prefix}.camera.json`});
      }
      await json(join(output,'projections.json'),savedProjections);
    }
    const manifest={schemaVersion:1,sceneId:scene.id,geometryHash:geometryHash(scene.vertices),createdAt:new Date().toISOString(),options,
      generation:{provider:null,requests:0,costUSD:0,scope:'this capture command only; costs of imported images are unknown'},
      renderer:projections.length?'local WebGL 2 with imported image projections':'local WebGL 2 material study; no generated images',
      projections:savedProjections,
      frames:[],continuity:[],formats:[],limitations:['Static geometry only; no character animation.','Rotation checks do not validate translation; use the tour shot.','Automated checks do not assess generated image quality or multiview consistency.'],
    };
    const aspects=options.aspect==='both'?['16:9','9:16']:[options.aspect];
    for(const aspect of aspects){
      await browser.evaluate('sceneLab.clearProjections()');
      for(let i=0;i<projections.length;i++){
        console.log(`Loading projection ${i+1}/${projections.length}`);
        await browser.evaluate(`sceneLab.addProjection(${JSON.stringify(`${url}/capture-projector-${i}`)},${JSON.stringify(projections[i].reference)})`);
      }
      const slug=aspect.replace(':','x'),dir=join(output,slug),n=options.duration*options.fps;
      const width=aspect==='16:9'?options.size/9*16:options.size,height=aspect==='16:9'?options.size:options.size/9*16;
      await mkdir(join(dir,'frames'),{recursive:true});await mkdir(join(dir,'refs'));await mkdir(join(dir,'qa'));
      const hashes=[];
      for(let i=0;i<n;i++){
        // Sweep is periodic; tour includes both exact endpoint marks.
        const progress=options.shot==='sweep'?i/n:i/(n-1);
        const result=await browser.evaluateLarge(`(()=>{const frame=sceneLab.renderFrame(${JSON.stringify({shot:options.shot,progress,width,height})});return {...frame,hash:sceneLab.pixelHash()};})()`);
        const filename=`frame-${String(i).padStart(5,'0')}.png`;
        await png(join(dir,'frames',filename),result.png);hashes.push(result.hash);
        manifest.frames.push({aspect,index:i,time:i/options.fps,path:`${slug}/frames/${filename}`,pixelHash:result.hash,...result.reference});
        if(i%Math.max(1,options.fps*4)===0||i===n-1)console.log(`${aspect} · ${options.shot} · ${i+1}/${n} frames`);
      }
      if(options.shot==='sweep'){
        const mismatches=[];for(let i=0;i<n/2;i++)if(hashes[i]!==hashes[i+n/2])mismatches.push(i);
        manifest.continuity.push({aspect,check:'independently rendered matching frames across both sweeps',pairs:n/2,mismatches,passed:mismatches.length===0});
      }else manifest.continuity.push({aspect,check:'independently rendered departure and return camera',passed:hashes[0]===hashes[n-1],firstHash:hashes[0],lastHash:hashes[n-1]});
      // All source bundles include exact pose plus guidance passes. They are never submitted.
      for(let i=0;i<options.references;i++){
        const progress=options.shot==='sweep'?i/options.references*.5:i/Math.max(1,options.references-1),prefix=`anchor-${String(i).padStart(2,'0')}`;
        let ref;
        for(const mode of ['beauty','depth','normals','objects']){
          const frame=await browser.evaluateLarge(`sceneLab.renderFrame(${JSON.stringify({shot:options.shot,progress,width,height,mode})})`);
          await png(join(dir,'refs',`${prefix}.${mode}.png`),frame.png);ref=frame.reference;
        }
        await json(join(dir,'refs',`${prefix}.camera.json`),ref);
      }
      // One local self-projection exercises calibrated image import and the depth visibility mask.
      const roundtrip=await browser.evaluateLarge(`(async()=>{
        sceneLab.clearProjections();
        const args=${JSON.stringify({shot:options.shot,progress:0,width,height})};
        const source=sceneLab.renderFrame(args),before=sceneLab.pixels();
        await sceneLab.addProjection(source.png,source.reference);sceneLab.renderFrame(args);
        const after=sceneLab.pixels();let total=0,max=0;for(let i=0;i<before.length;i++){if(i%4===3)continue;const d=Math.abs(before[i]-after[i]);total+=d;max=Math.max(max,d);}
        const coverage=sceneLab.renderFrame({...args,mode:'coverage'}),pixels=sceneLab.pixels();
        let covered=0;for(let i=0;i<pixels.length;i+=4)if(pixels[i+1]>pixels[i]*1.5)covered++;
        const error=sceneLab.glError();sceneLab.clearProjections();
        return {meanAbsoluteRGBError:total/(before.length/4*3),maxChannelError:max,coveredFraction:covered/(before.length/4),glError:error,coverage:coverage.png};
      })()`);
      await png(join(dir,'qa/self-projection-coverage.png'),roundtrip.coverage);delete roundtrip.coverage;
      manifest.continuity.push({aspect,check:'local source image projected back onto its visible geometry',...roundtrip,passed:roundtrip.meanAbsoluteRGBError<3&&roundtrip.coveredFraction>.25&&roundtrip.glError===0});
      await copyFile(join(dir,'frames/frame-00000.png'),join(dir,'poster.png'),constants.COPYFILE_EXCL);
      if(options.video){
        console.log(`Encoding ${aspect} · ${options.duration}s at 24 fps (${options.fps} unique frames/s)`);
        await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-framerate',String(options.fps),'-i',join(dir,'frames/frame-%05d.png'),
          '-vf','fps=24,setsar=1','-frames:v',String(options.duration*24),'-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',join(dir,`${options.shot}.mp4`)]);
      }
      manifest.formats.push({aspect,width,height,sampleFPS:options.fps,outputFPS:options.video?24:null,sampleCount:n,video:options.video?`${slug}/${options.shot}.mp4`:null});
    }
    const prompt=`Restyle this exact 3D reference as a richly detailed cinematic view of the Meridian House: jade and ivory architecture, aged brass, a celestial orrery, cobalt library, moonlit conservatory. Preserve every object silhouette, location, opening, camera perspective, and occlusion. Add surface detail and materials only. Do not add furniture, characters, text, or architecture. Return the identical image aspect ratio. The beauty render is the camera composition; depth, world normals, and object IDs are auxiliary guides, not colors to reproduce.\n\nReview the result against the reference before projecting it. A prompt alone does not enforce geometry.\n`;
    await writeFile(join(output,'image-prompt.txt'),prompt,{flag:'wx'});
    await json(join(output,'manifest.json'),manifest);
    const failures=manifest.continuity.filter(check=>!check.passed);
    console.log(`\nSaved: ${output}\nContinuity checks: ${manifest.continuity.length-failures.length}/${manifest.continuity.length} passed\nExternal image/video generation calls: 0`);
    if(failures.length){console.error(JSON.stringify(failures,null,2));process.exitCode=1;}
  }finally{await browser?.close();await new Promise(resolve=>server.close(resolve));}
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
