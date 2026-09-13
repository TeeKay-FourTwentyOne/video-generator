#!/usr/bin/env node
// Prepare and explicitly submit a bounded set of source-image style variations.
// Generation uses the repository's existing Nano Banana CLI. There are no retries.
import { readFile, writeFile, appendFile, mkdir, access } from 'node:fs/promises';
import { resolve, join, relative } from 'node:path';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { buildScene } from './scene.mjs';
import { validateReference } from './reference.mjs';

const STYLES=[
  {name:'Oil painting',slug:'oil',description:'A luminous oil painting on fine linen. Rich jade and deep petrol shadows, warm brass highlights, subtle impasto and precise architectural brushwork. Paint texture follows the existing surfaces; contours stay sharply registered.'},
  {name:'Watercolor',slug:'watercolor',description:'A refined architectural watercolor. Transparent mineral pigments, soft teal and sage washes, warm ochre brass, controlled wet edges and delicate cold-press paper grain. Keep every existing contour crisply aligned even where the washes are loose.'},
  {name:'Cut paper',slug:'paper',description:'An intricately handcrafted cut-paper illustration of exactly this view. Existing object surfaces have matte colored-paper texture and subtle layered paper-edge shading. Jewel-green leaves, dusty rose upholstery, ivory architecture and muted gold trim. Preserve the exact perspective and silhouettes; no extra paper shapes or layers protruding into space.'},
  {name:'Woodcut',slug:'woodcut',description:'An elegant three-color reduction woodcut print: deep indigo shadows, warm ivory paper, muted copper-gold accents. Fine carved hatching and confident contour lines describe precisely the existing geometry. Keep wall planes calm; hatching is surface shading, never new ornaments or objects.'},
  {name:'Glazed ceramic',slug:'ceramic',description:'A sophisticated handmade glazed-ceramic miniature rendering. Existing surfaces have tactile celadon and cream glaze, subtle crazing, dark emerald recesses, lustrous warm brass-colored glaze and restrained highlights. The exact existing objects are given ceramic surface finish without thickening, rounding, replacing, or adding any forms.'},
  {name:'Soft pastel',slug:'pastel',description:'A richly atmospheric soft-pastel drawing on fine tooth paper. Velvet charcoal-green shadows, luminous pale jade walls, dusty mauve upholstery, creamy stone and soft gold highlights. Fine pigment grain and confident marks give depth while all architectural lines and object boundaries remain exactly registered.'},
  {name:'Ink wash',slug:'ink',description:'An exquisite ink-and-wash architectural drawing. Charcoal brush ink, restrained jade watercolor accents and small warm gold highlights. Subtle ink pooling and precise fine contour work describe the unchanged scene. Preserve the existing perspective and full composition; do not add calligraphy, stamps, or illustrative motifs.'},
  {name:'Cinematic realism',slug:'cinematic',description:'Photorealistic cinematic architectural materials: dark jade lime plaster, aged brushed brass, ivory stone, real velvet, wood grain, and natural leaf texture on the exact existing shapes. Soft illumination from the existing practical fixtures and cool night light from existing openings, realistic contact shading and gentle film grain. Keep all source object shapes and positions exactly, including the simplified plant leaf silhouettes.'},
];
const COMMON=`Use case: style-transfer / calibrated 3D projection texture.
Input image 1: the exact source-camera composition to preserve. Input image 2: an object-boundary guide for the same view; its false colors are diagnostic and must not appear in the output.
Primary request: Bring this exact unoccupied 3D mansion view to life using the specified artistic medium. Change surface rendering, color, texture, and shading only.
Composition: Match image 1 precisely, pixel for pixel in normalized coordinates. Identical fixed eye-level camera, field of view, crop, vanishing points, horizon, object sizes, silhouettes, edge locations, and occlusion order. Full-bleed 16:9 landscape. Do not zoom, rotate, reframe, straighten, or move anything.
Scene inventory: Only the objects actually visible in image 1 may appear. Preserve their exact counts and locations. Existing geometry includes architecture, arch openings, trim, lamps, orrery components where visible, tiled floor, chairs, plants, and furnishings visible through the existing openings. Treat those as a closed inventory. Objects not visible in this particular reference must not be introduced.
Hard constraints: No people, faces, human figures, animals, statues, new furniture, new plants, new pots, flowers, picture frames, artwork, ornaments, signs, text, additional lamps, curtains, new doors or windows, new moon or stars, floating particles, additional orrery rings or planets, or imaginary architecture. Do not fill empty walls with decorations. Do not create reflections that introduce additional objects. Do not turn shadows or brush marks into recognizable new objects. Do not remove existing geometry. Floor tile intersections, plant leaf outlines, chair structure, and every arch boundary must stay registered to image 1.
Output: Exactly one finished image, full composition, no border, no collage, no labels, no watermark. This image will be projected onto the existing rigid 3D mesh; geometric deviations will cause visible double edges. Prioritize faithful boundaries over decorative invention.
`;
function args(argv){
  const out={source:'data/workspace/meridian-house/rotation-v1/16x9/refs',output:'data/workspace/meridian-house/styles-v1',generate:false,normalize:false,only:null};
  for(const arg of argv){
    if(arg==='--generate'){out.generate=true;continue;}
    if(arg==='--normalize'){out.normalize=true;continue;}
    if(arg==='--help'){console.log('node tools/scene-lab/style-frames.mjs [--source=REFS] [--output=DIR] [--only=0,1] [--generate] [--normalize]\n--generate sends selected references to the configured Vertex AI Nano Banana integration. No automatic retries.\n--normalize locally resizes the full generated canvas to exact 16:9 and writes a projection list. No crop.\nWith neither flag: prepare prompts only.');return null;}
    const match=arg.match(/^--(source|output|only)=(.+)$/);if(!match)throw new Error(`Unknown argument: ${arg}`);out[match[1]]=match[2];
  }
  if(out.only!==null){out.only=out.only.split(',').map(Number);if(!out.only.length||out.only.some(i=>!Number.isInteger(i)||i<0||i>7)||new Set(out.only).size!==out.only.length)throw new Error('--only must contain unique indices from 0 to 7.');}
  return out;
}
const exists=async path=>{try{await access(path);return true;}catch(error){if(error.code==='ENOENT')return false;throw error;}};
async function ensureText(path,text){
  if(await exists(path)){if(await readFile(path,'utf8')!==text)throw new Error(`Existing input differs: ${path}. Choose a new output directory.`);}
  else await writeFile(path,text,{flag:'wx'});
}
function command(executable,args){return new Promise((resolve,reject)=>{
  const child=spawn(executable,args,{stdio:['ignore','pipe','pipe']});let stdout='',stderr='';
  child.stdout.on('data',chunk=>{stdout+=chunk;});child.stderr.on('data',chunk=>{stderr+=chunk;});child.on('error',reject);
  child.on('close',code=>code===0?resolve(stdout):reject(new Error(`${executable} exited ${code}: ${stderr.slice(-2000)}`)));
});}
async function main(){
  const options=args(process.argv.slice(2));if(!options)return;
  const source=resolve(options.source),output=resolve(options.output),scene=buildScene();
  const plans=[];
  for(let i=0;i<8;i++){
    const anchor=`anchor-${String(i).padStart(2,'0')}`,camera=join(source,`${anchor}.camera.json`);
    validateReference(JSON.parse(await readFile(camera,'utf8')),scene);
    const refs=[join(source,`${anchor}.beauty.png`),join(source,`${anchor}.objects.png`)];
    const hashes=[];for(const ref of refs)hashes.push(createHash('sha256').update(await readFile(ref)).digest('hex'));
    plans.push({index:i,yawDegrees:i*45,...STYLES[i],refs,sourceHashes:hashes,camera,prompt:`${COMMON}\nStyle/medium: ${STYLES[i].description}\n`,
      promptFile:join(output,'prompts',`${anchor}-${STYLES[i].slug}.txt`),image:join(output,'raw',`${anchor}-${STYLES[i].slug}.png`)});
  }
  for(const dir of ['prompts','raw','metadata'])await mkdir(join(output,dir),{recursive:true});
  for(const plan of plans)await ensureText(plan.promptFile,plan.prompt);
  await ensureText(join(output,'plan.json'),JSON.stringify({schemaVersion:1,provider:'Google Vertex AI / existing Nano Banana integration',model:'gemini-3-pro-image',size:'2K',aspect:'16:9',temperature:.35,
    authorization:'User approved bringing the 16:9 rotation to life with different artistic styles; no people or additional objects.',
    plannedRequests:8,automaticRetries:false,estimatedCostUSD:null,frames:plans},null,2)+'\n');
  await ensureText(join(output,'projections-raw.json'),JSON.stringify(plans.map(p=>({image:relative(output,p.image),camera:relative(output,p.camera)})),null,2)+'\n');
  console.log(`Prepared ${plans.length} styles: ${output}`);
  const selected=plans.filter(p=>options.only===null||options.only.includes(p.index));
  if(!options.generate)console.log('No generation requests submitted.');
  for(const plan of options.generate?selected:[]){
    const metadataPath=join(output,'metadata',`anchor-${String(plan.index).padStart(2,'0')}.json`);
    if(await exists(plan.image)){
      if(!await exists(metadataPath))throw new Error(`Image exists without completion metadata: ${plan.image}. Inspect it before requesting another generation.`);
      console.log(`Keeping existing ${plan.name}: ${plan.image}`);continue;
    }
    const startedAt=new Date().toISOString(),start=Date.now();
    await appendFile(join(output,'requests.jsonl'),JSON.stringify({event:'submitted',index:plan.index,style:plan.name,startedAt,model:'gemini-3-pro-image',refs:plan.refs,output:plan.image})+'\n');
    console.log(`Generating ${plan.index+1}/8: ${plan.name}`);
    const result=await new Promise((resolve,reject)=>{
      const child=spawn(process.execPath,['tools/nano-banana.cjs',`--prompt-file=${plan.promptFile}`,...plan.refs.map(ref=>`--ref=${ref}`),'--aspect=16:9','--model=pro','--size=2K','--temperature=0.35',`--output=${plan.image}`,'--json'],{stdio:['ignore','pipe','pipe']});
      let stdout='',stderr='';child.stdout.on('data',chunk=>{stdout+=chunk;});child.stderr.on('data',chunk=>{stderr+=chunk;process.stderr.write(chunk);});child.on('error',reject);
      child.on('close',code=>code===0?resolve({stdout,stderr}):reject(new Error(`Nano Banana exited ${code}: ${stderr.slice(-2500)}`)));
    }).catch(async error=>{await appendFile(join(output,'requests.jsonl'),JSON.stringify({event:'failed',index:plan.index,finishedAt:new Date().toISOString(),message:error.message})+'\n');throw error;});
    const response=JSON.parse(result.stdout),metadata={index:plan.index,style:plan.name,startedAt,finishedAt:new Date().toISOString(),elapsedSeconds:(Date.now()-start)/1000,...response,costUSD:null,reviewStatus:'pending'};
    await writeFile(metadataPath,JSON.stringify(metadata,null,2)+'\n',{flag:'wx'});
    await appendFile(join(output,'requests.jsonl'),JSON.stringify({event:'completed',index:plan.index,finishedAt:metadata.finishedAt,elapsedSeconds:metadata.elapsedSeconds,image:plan.image})+'\n');
    console.log(`Saved ${plan.name} (${metadata.elapsedSeconds.toFixed(1)}s): ${plan.image}`);
  }
  if(options.normalize){
    await mkdir(join(output,'normalized'),{recursive:true});const projections=[];
    for(const plan of selected){
      const probe=JSON.parse(await command('ffprobe',['-v','error','-show_entries','stream=width,height','-of','json',plan.image]));
      const {width,height}=probe.streams[0],aspectError=width/height/(16/9)-1;
      if(Math.abs(aspectError)>.02)throw new Error(`Generated ${plan.name} aspect differs by more than 2%. Inspect framing before normalization.`);
      const normalized=join(output,'normalized',`anchor-${String(plan.index).padStart(2,'0')}-${plan.slug}.png`);
      if(!await exists(normalized))await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',plan.image,'-vf','scale=2048:1152:flags=lanczos,setsar=1','-frames:v','1',normalized]);
      await ensureText(`${normalized}.json`,JSON.stringify({source:plan.image,sourceSHA256:createHash('sha256').update(await readFile(plan.image)).digest('hex'),sourceWidth:width,sourceHeight:height,width:2048,height:1152,aspectError,operation:'Full-canvas resize to requested 16:9, no crop, no content synthesis'},null,2)+'\n');
      projections.push({image:relative(output,normalized),camera:relative(output,plan.camera)});
    }
    const name=options.only?`projections-${options.only.map(i=>String(i).padStart(2,'0')).join('-')}.json`:'projections.json';
    await ensureText(join(output,name),JSON.stringify(projections,null,2)+'\n');
    console.log(`Prepared ${projections.length} normalized projections: ${join(output,name)}`);
  }
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
