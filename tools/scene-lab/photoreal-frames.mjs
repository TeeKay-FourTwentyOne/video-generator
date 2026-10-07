#!/usr/bin/env node
// One coherent Nano Banana treatment of the existing eight-camera rotation.
// Prepare is local; generate submits exactly one explicitly selected take.
import { readFile, writeFile, mkdir, copyFile, access, readdir } from 'node:fs/promises';
import { constants } from 'node:fs';
import { resolve, join, basename } from 'node:path';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { buildScene } from './scene.mjs';
import { validateReference, geometryHash } from './reference.mjs';
import { documentaryLook, documentaryDetails } from './documentary-look.mjs';

const ROOT=resolve(import.meta.dirname,'../..');
const DEFAULT='data/workspace/meridian-house/photoreal-v1';
const LOOK=`Use case: sketch-to-render / calibrated architectural reference.
Primary request: Turn the exact supplied 3D model view into a convincing photograph of a real, full-scale mansion. The eight views belong to ONE physical house photographed during the SAME midnight session. This is a cohesive photorealistic material study.
Image 1 is the authoritative geometry and camera composition. Image 2 is the matching object-boundary guide: its false colors must never appear in the result. Any later images are material/lighting references only; never borrow their camera position or their visible objects.
Photographic treatment: natural architectural interior photography with physically believable light falloff, soft bounced light, contact shadows, restrained reflections and fine real surface detail. Neutral photographic tonality with luminous practical lamps and gently cool moonlight. Deep focus, clean fine detail, no bloom, vignette, fog, dramatic shafts, extreme HDR or shallow-focus miniature effect. It must look built and photographed, without illustrative strokes, canvas grain, painted shading, plastic CGI or video-game surfaces.
Fixed material bible: existing jade/teal walls are dark mineral-jade lime plaster with restrained fine mottling; existing ivory arches and columns are warm honed limestone with subtle pores; existing gold trim and orrery rings are satin aged brass with restrained patina; existing blue library walls are deep desaturated blue plaster; existing wooden shelves, desk and chair structure are oiled walnut with fine directional grain; existing dusty-rose cushions are real woven velvet. Existing pale/teal floor squares are honed ivory limestone and muted green marble, with very subtle natural veining following each tile. Keep the tile grid and its brass inlay exactly. Existing books have restrained cloth/leather covers in the source colors, without legible invented titles. Existing leaves have natural waxy surfaces and fine veins inside their original silhouettes. Existing pots retain their source colors and shapes as glazed ceramics. Existing orrery planets are smooth enamel spheres in their exact source colors, sizes and positions. Keep the pale stone pedestal and the exact rings, base and floor compass.
Lighting continuity: every view has the same exposure, material hues and white balance. Warm 2700 K light comes ONLY from the lamps and glowing orrery sphere already visible or physically present in the model. Cool moonlight comes only through existing exterior glazing/openings. Do not add fixtures or windows to justify lighting. Preserve the moon's position and size if visible. Keep indirect illumination broad and soft; no new hard shadow shapes painted across unrelated surfaces.
Geometry invariants: match image 1 in normalized pixel coordinates: identical perspective, field of view, horizon, crop, vanishing points, object sizes, silhouettes, positions and occlusion order. Do not straighten, zoom, shift, widen, distort or reframe the camera. Preserve all arch boundaries, shelf divisions, tile intersections, columns, chair legs, leaf outlines and orrery rings. All visible objects stay in place and keep their exact counts. Surfaces may gain fine texture and realistic shading, but no silhouette may change. Geometry takes priority over photographic decoration.
Closed inventory: only what is actually visible in image 1 may appear. Empty walls stay empty. No people, figures, animals, sculptures, flowers, added plants or pots, picture frames, curtains, rugs, doors, windows, extra lights, ornaments, floating objects or new architecture. Do not turn empty wall recesses into doors. Do not move library shelves into the conservatory. Never copy objects from a style reference into a target view where they are absent. Reflections must not invent objects or additional rooms.
Output: one full-bleed landscape 16:9 photograph, no border, collage, caption, logo, watermark or text. This image will be projected onto the unchanged 3D model, so registration is essential.
`;
const DETAILS=[
  'Front atrium view. Preserve the central brass orrery and all ring intersections, the pale pedestal, the two fluted columns, the arched moonlit window, the lamps and the partial room views at the left and right edges.',
  'Oblique atrium view toward the conservatory. The near orrery stays at the left, and only the modeled planting and furnishings appear through the right-hand arch. Preserve its empty wall areas and every visible leaf silhouette.',
  'Side view of the existing chair and conservatory arch. Keep the exact chair structure and upholstery outline, arch shape, floor grid and plant inventory. Do not add a rug or table.',
  'Oblique rear-wall view with the existing plant and architectural details. Keep the broad plaster wall quiet and undecorated. Do not introduce extra lighting, ornaments or furniture.',
  'Rear atrium wall. The large broad wall plane remains an uninterrupted plaster surface. Any existing decorative recess or ring remains shallow and fixed: it is not a door or opening. Do not add objects to this intentionally sparse view.',
  'Oblique rear-wall view toward the library side. Preserve the exact plant, pot and existing architectural details. Empty wall areas remain empty; the existing lamp stays in exactly the same position.',
  'Side view toward the library arch. Bookshelves visible through it remain inside the library and behind its doorway, with exactly the source divisions and outline. Preserve the existing adjacent chair and plants where visible.',
  'Oblique atrium view back toward the front orrery and the library. This must close the full rotation into the master photograph: match its jade plaster, limestone, brass, floor finish, exposure and lighting exactly.',
];
const exists=async p=>{try{await access(p);return true;}catch(e){if(e.code==='ENOENT')return false;throw e;}};
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=(p,v)=>writeFile(p,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
function command(name,args){return new Promise((yes,no)=>{const p=spawn(name,args,{cwd:ROOT,stdio:['ignore','pipe','pipe']});let out='',err='';p.stdout.on('data',c=>out+=c);p.stderr.on('data',c=>err+=c);p.on('error',no);p.on('close',code=>{if(code===0)return yes(out);const error=new Error(`${name} failed (${code}); inspect the local request error record.`);error.stderr=err;error.stdout=out;no(error);});});}
const [action,...argv]=process.argv.slice(2),opts={output:DEFAULT,index:null,take:1,look:'photoreal'};
for(const arg of argv){const m=arg.match(/^--(output|index|take|look)=(.+)$/);if(!m)throw new Error('Unknown option');opts[m[1]]=m[2];}
if(!['photoreal','documentary'].includes(opts.look))throw new Error('Choose --look=photoreal|documentary.');
const dir=resolve(ROOT,opts.output);
const budgetTag=basename(dir);
if(!/^[a-z0-9-]+$/.test(budgetTag)||dir!==join(ROOT,'data/workspace/meridian-house',budgetTag))throw new Error('Use a distinct run directly under data/workspace/meridian-house/. Each run needs its own matching RESERVE tag.');
if(action==='prepare'){
  if(await exists(dir))throw new Error('Choose a new run directory.');
  const scene=buildScene(),frames=[],documentary=opts.look==='documentary';
  const look=documentary?documentaryLook:LOOK,details=documentary?documentaryDetails:DETAILS;
  for(const sub of ['source','prompts','raw','normalized','requests','reviews'])await mkdir(join(dir,sub),{recursive:true});
  for(let i=0;i<8;i++){
    const stem=`anchor-${String(i).padStart(2,'0')}`;
    for(const suffix of ['beauty.png','objects.png','camera.json'])await copyFile(join(ROOT,'data/workspace/meridian-house/rotation-v1/16x9/refs',`${stem}.${suffix}`),join(dir,'source',`${stem}.${suffix}`),constants.COPYFILE_EXCL);
    validateReference(JSON.parse(await readFile(join(dir,'source',`${stem}.camera.json`),'utf8')),scene);
    const refs=documentary?[`source/${stem}.beauty.png`]:[`source/${stem}.beauty.png`,`source/${stem}.objects.png`];
    frames.push({index:i,yawDegrees:i*45,camera:`source/${stem}.camera.json`,refs,sourceHashes:await Promise.all(refs.map(async p=>sha(await readFile(join(dir,p))))),detail:details[i]});
  }
  await writeFile(join(dir,'material-bible.txt'),look,{flag:'wx'});
  await json(join(dir,'plan.json'),{schemaVersion:1,look:opts.look,sceneId:scene.id,geometryHash:geometryHash(scene.vertices),provider:'Google Vertex AI / Nano Banana Pro',model:'gemini-3-pro-image',size:'2K',aspect:'16:9',temperature:.35,frames,plannedImages:8,maxRequests:10,automaticRetries:false,budgetReserveUSD:8,budgetReservationTag:budgetTag,projectCeilingUSD:49,authorization:documentary?'User requested the strongest possible documentary photographic realism after reviewing photoreal-v1. Existing project ceiling applies.':'User requested repeating the Nano Banana exercise with a cohesive photorealistic mansion; original video is preserved.',scope:documentary?'Eight documentary stills using original spatial references. Small shape refinements allowed for realism; not calibrated projection approval. No Veo requests.':'Eight matching rotation views, calibrated projections and local preview. No Veo requests.',promptSHA256:sha(look),pricingSource:'https://cloud.google.com/vertex-ai/generative-ai/pricing',pricingChecked:'2026-09-13',outputImageSubtotalPerRequestUSD:.1344,actualBilledUSD:null});
  console.log(`Prepared ${opts.output}`);
}else if(action==='generate'){
  const index=Number(opts.index),take=Number(opts.take);
  if(opts.index===null||!Number.isInteger(index)||index<0||index>7||![1,2,3,4].includes(take))throw new Error('Choose --index=0..7 and --take=1, 2, 3 or 4.');
  const plan=JSON.parse(await readFile(join(dir,'plan.json'),'utf8')),frame=plan.frames[index];
  if(plan.budgetReservationTag!==budgetTag)throw new Error('Budget reserve belongs to a different run.');
  if(plan.model!=='gemini-3-pro-image'||!((plan.budgetReserveUSD===8&&[10,12].includes(plan.maxRequests))||([10,12].includes(plan.budgetReserveUSD)&&plan.maxRequests===16)||(plan.budgetReserveUSD===11&&plan.maxRequests===20)))throw new Error('Recipe/budget changed; review first.');
  const bible=await readFile(join(dir,'material-bible.txt'),'utf8');if(sha(bible)!==plan.promptSHA256)throw new Error('Material bible changed after preparation.');
  const ledger=await readFile(join(ROOT,'data/veo-budget-meridian-house.tsv'),'utf8');
  const rows=ledger.trim().split('\n').slice(1).map(l=>l.split('\t'));
  const allocation=rows.reduce((a,r)=>a+Number(r[5]),0),reserve=rows.filter(r=>r[6]?.startsWith(`RESERVE ${budgetTag}:`)).reduce((a,r)=>a+Number(r[5]),0);
  if(!Number.isFinite(allocation)||allocation>49||reserve<plan.budgetReserveUSD)throw new Error('Missing image reserve or exceeded project allocation.');
  const attempts=(await readdir(join(dir,'requests'))).filter(n=>n.endsWith('.attempt.json'));
  if(attempts.length>=plan.maxRequests)throw new Error('Request limit reached; no additional submission.');
  const stem=`anchor-${String(index).padStart(2,'0')}-take-${take}`,attempt=join(dir,'requests',`${stem}.attempt.json`),image=`raw/${stem}.png`;
  if(await exists(attempt)||await exists(join(dir,image)))throw new Error('This take already has a record; inspect it, never resubmit.');
  const refs=[...frame.refs];
  for(let i=0;i<refs.length;i++)if(sha(await readFile(join(dir,refs[i])))!==frame.sourceHashes[i])throw new Error('Source reference changed.');
  const styleRefs=[];
  async function selected(i){const r=JSON.parse(await readFile(join(dir,'reviews',`anchor-${String(i).padStart(2,'0')}.json`),'utf8'));if(r.verdict!=='selected'||sha(await readFile(join(dir,r.image)))!==r.sha256)throw new Error('Style reference not selected or changed.');return r.image;}
  if(index>0 && plan.styleReferenceMode!=='material-swatches'){styleRefs.push(await selected(0));if(index>1)styleRefs.push(await selected(index-1));}
  refs.push(...styleRefs);
  let prompt=bible+`\nView-specific instruction: ${frame.detail}\n`;
  if(index>=3 && index<=6)prompt+='\nThere is NO visible moon in this geometry view. Do not copy the moon or orrery from a style reference into this composition.\n';
  if(styleRefs.length)prompt+=`\nImage ${frame.refs.length+1} is the selected MASTER photograph: match its material palette, light quality, surface realism, exposure and white balance. `+(styleRefs.length>1?`Image ${frame.refs.length+2} is the selected adjacent-angle photograph: keep overlapping surfaces and visible objects consistent with it. `:'')+'Only image 1 controls geometry, camera and object inventory. Do not repeat the composition of the style photographs.\n';
  if(plan.styleReferenceMode==='material-swatches'){
    const swatches='material-swatches.png';if(sha(await readFile(join(dir,swatches)))!==plan.swatchSHA256)throw new Error('Material reference changed after selection.');
    refs.push(swatches);
    prompt+=`\nImage ${frame.refs.length+1} contains isolated material samples cropped from the selected photographs. Use it ONLY for material texture, color and finish. Its arrangement and labels are not part of the scene. Keep the architectural layout and camera of image 1, subject to the physical-plausibility instructions above. Never draw a material sample board or copy labels.\n`;
  }
  const correction=join(dir,'prompts',`${stem}.correction.txt`);if(take>1){if(!await exists(correction))throw new Error('A correction take requires a saved targeted correction.');prompt+='\nTargeted correction: '+await readFile(correction,'utf8');}
  const editSourceFile=join(dir,'prompts',`${stem}.edit-source.txt`);
  if(take>1 && await exists(editSourceFile)){
    const target=(await readFile(editSourceFile,'utf8')).trim();
    if(!/^normalized\/anchor-\d{2}-take-[1234]\.png$/.test(target)||!await exists(join(dir,target)))throw new Error('Edit target must be a retained normalized image in this run.');
    const photoOnly=plan.editReferenceMode==='photo-only';
    refs.splice(0,refs.length,target,...(photoOnly?[]:[frame.refs[0]]));
    prompt='Use case: precise-object-edit. Image 1 is the photograph to edit. '+(photoOnly?'This photograph is the sole image reference. Keep its real photographic surfaces; do not stylize or recreate it as CGI. ':'Image 2 is the original 3D geometry guide for identifying the true contents of windows and openings. ')+'Return the SAME photograph as image 1, with ONLY the localized correction below. Preserve every other pixel as closely as possible: same material colors, upholstery, light, exposure, camera, composition, furniture, plants, stone and brass. Do not re-render or redesign the room. Full-bleed 16:9, one image, no text.\nTargeted correction: '+await readFile(correction,'utf8');
  }
  const promptFile=`prompts/${stem}.txt`;await writeFile(join(dir,promptFile),prompt,{flag:'wx'});
  await json(attempt,{index,take,startedAt:new Date().toISOString(),image,promptFile,promptSHA256:sha(prompt),refs,inputHashes:await Promise.all(refs.map(async p=>sha(await readFile(join(dir,p))))),reservedWithinBatchUSD:plan.budgetReserveUSD/plan.maxRequests,actualBilledUSD:null});
  console.log(`Submitting view ${index+1}/8, take ${take}; ${refs.length} references.`);
  try{
    const out=await command(process.execPath,['tools/nano-banana.cjs',`--prompt-file=${join(dir,promptFile)}`,...refs.map(p=>`--ref=${join(dir,p)}`),'--aspect=16:9','--model=pro','--size=2K','--temperature=0.35',`--output=${join(dir,image)}`,'--json']);
    await json(join(dir,'requests',`${stem}.result.json`),{status:'completed',finishedAt:new Date().toISOString(),...JSON.parse(out),sha256:sha(await readFile(join(dir,image))),reviewStatus:'pending',actualBilledUSD:null});
    const probe=JSON.parse(await command('ffprobe',['-v','error','-show_entries','stream=width,height','-of','json',join(dir,image)])).streams[0];
    if(Math.abs((probe.width/probe.height)/(16/9)-1)>.02)throw new Error('Image aspect differs by more than 2%; inspect before normalization.');
    const normalized=`normalized/${stem}.png`;
    await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',join(dir,image),'-vf','scale=2048:1152:flags=lanczos,setsar=1','-frames:v','1',join(dir,normalized)]);
    await json(join(dir,`${normalized}.json`),{source:image,sourceSHA256:sha(await readFile(join(dir,image))),sourceWidth:probe.width,sourceHeight:probe.height,width:2048,height:1152,operation:'Full-canvas resize to exact 16:9; no crop or content synthesis.'});
    console.log(`Saved ${opts.output}/${normalized}; inspect before selecting.`);
  }catch(error){await json(join(dir,'requests',`${stem}.error.json`),{status:'failed-or-needs-inspection',at:new Date().toISOString(),message:error.message,stderr:error.stderr??null,stdout:error.stdout??null,automaticRetry:false});throw new Error(error.message);}
}else throw new Error('Usage: photoreal-frames.mjs prepare|generate [--output=NEW_RUN] [--look=photoreal|documentary] [--index=0..7] [--take=1|2|3|4]');
