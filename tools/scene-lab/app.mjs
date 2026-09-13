import { buildScene } from './scene.mjs';
import { cameraAt, cameraMatrix, SHOTS, normalize, sub } from './math.mjs';
import { Renderer, MAX_PROJECTIONS } from './renderer.mjs';
import { geometryHash, validateReference } from './reference.mjs';

const $=id=>document.getElementById(id);
const params=new URLSearchParams(location.search);
if(params.has('render')) document.documentElement.classList.add('render-only');
const scene=buildScene(), hash=geometryHash(scene.vertices);
let renderer;
const state={shot:'sweep',progress:0,playing:false,aspect:'16:9',mode:'beauty',lastTime:0};
let referencePair=null, importedReference=null;
const status=(text,error=false)=>{$('status').textContent=text;$('status').classList.toggle('error',error);};

function dimensions(shortEdge=720) {return state.aspect==='16:9'?[shortEdge*16/9,shortEdge]:[shortEdge,shortEdge*16/9];}
function reference(camera,width,height) {
  return {schemaVersion:1,sceneId:scene.id,geometryHash:hash,width,height,aspect:width>height?'16:9':'9:16',camera,
    viewProjection:Array.from(cameraMatrix(camera,width/height)),shot:state.shot,progress:state.progress,
    sceneTime:0,coordinateSystem:'right-handed, metres, Y up, camera -Z',imageOrigin:'top-left',
    notes:'Keep image dimensions, camera perspective, object boundaries, and occlusions unchanged. This is a static scene.'};
}
function drawMap(camera) {
  const canvas=$('map'),ctx=canvas.getContext('2d'),s=19,ox=330,oz=128;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const rect=(x,z,w,d)=>[ox+x*s,oz+z*s,w*s,d*s];
  scene.rooms.forEach((room,i)=>{
    const [x,z,x2,z2]=room.bounds;
    ctx.fillStyle=['#e3e8dc','#e3e4dc','#dfe8da'][i];ctx.strokeStyle='#a7b49c';ctx.lineWidth=2;
    ctx.fillRect(...rect(x,z,x2-x,z2-z));ctx.strokeRect(...rect(x,z,x2-x,z2-z));
    ctx.fillStyle='#71866b';ctx.textAlign='center';ctx.font='12px -apple-system, sans-serif';
    ctx.fillText(room.name.toUpperCase(),ox+(x+x2)/2*s,oz+(z2-1)*s);
  });
  for(const x of [-5,5]) {ctx.fillStyle='#f1f0e9';ctx.fillRect(...rect(x-.15,-1.45,.3,2.9));}
  ctx.beginPath();ctx.arc(ox,oz-1.8*s,1.3*s,0,Math.PI*2);ctx.strokeStyle='#af9a72';ctx.lineWidth=2;ctx.stroke();
  ctx.beginPath();ctx.arc(ox+10*s,oz,1.7*s,0,Math.PI*2);ctx.strokeStyle='#93b1a4';ctx.stroke();
  if(state.shot==='tour') {
    ctx.beginPath();for(let i=0;i<=100;i++){const c=cameraAt('tour',i/100);ctx[i?'lineTo':'moveTo'](ox+c.eye[0]*s,oz+c.eye[2]*s);}
    ctx.setLineDash([5,6]);ctx.strokeStyle='#a88b61';ctx.lineWidth=1.5;ctx.stroke();ctx.setLineDash([]);
  }
  const x=ox+camera.eye[0]*s,z=oz+camera.eye[2]*s,d=normalize(sub(camera.target,camera.eye)),a=Math.atan2(d[2],d[0]);
  ctx.beginPath();ctx.moveTo(x,z);ctx.arc(x,z,49,a-.5,a+.5);ctx.closePath();ctx.fillStyle='#68886723';ctx.fill();
  ctx.beginPath();ctx.arc(x,z,5,0,Math.PI*2);ctx.fillStyle='#335d43';ctx.fill();
  ctx.beginPath();ctx.moveTo(x,z);ctx.lineTo(x+Math.cos(a)*19,z+Math.sin(a)*19);ctx.strokeStyle='#335d43';ctx.lineWidth=2;ctx.stroke();
}
function draw() {
  const camera=cameraAt(state.shot,state.progress),[width,height]=dimensions();
  renderer.render(camera,{width,height,mode:state.mode});
  $('dimensions').textContent=`${width} × ${height}`;
  $('pose-label').textContent=camera.eye.map((v,i)=>`${['X','Y','Z'][i]} ${v.toFixed(2)}`).join(' · ');
  $('loop-label').textContent=state.shot==='sweep'?`REVOLUTION ${state.progress<.5?'01':'02'} / 02`:'LIBRARY & RETURN';
  $('frame-label').textContent=`${camera.eye[0]<-5?'LIB':camera.eye[0]>5?'CON':'ATR'} / CAM 01`;
  const time=state.progress*SHOTS[state.shot].duration;
  $('time').textContent=`00:${time.toFixed(1).padStart(4,'0')}`;
  $('timeline').value=state.progress;
  drawMap(camera);
}
function pause(){state.playing=false;$('play').textContent='▶';$('play').setAttribute('aria-label','Play camera path');}
function frame(now) {
  if(state.playing) {
    state.progress=Math.min(1,state.progress+(now-state.lastTime)/1000/SHOTS[state.shot].duration);
    if(state.progress===1) pause();draw();
  }
  state.lastTime=now;requestAnimationFrame(frame);
}
function save(name,data,type) {
  const a=document.createElement('a'),blob=new Blob([data],{type}),url=URL.createObjectURL(blob);
  a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
function savePNG(name,dataURL){const a=document.createElement('a');a.href=dataURL;a.download=name;a.click();}
function captureSource(){
  pause();const camera=cameraAt(state.shot,state.progress),[width,height]=dimensions();
  renderer.render(camera,{width,height,mode:'beauty'});
  referencePair={png:renderer.png(),reference:reference(camera,width,height)};
  return referencePair;
}
function imageFromURL(url) {return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('Could not decode the image.'));image.src=url;});}
async function project(url,ref){
  validateReference(ref,scene);const image=await imageFromURL(url);await renderer.addProjection(image,ref);
  $('projection-count').textContent=`${renderer.projections.length} / ${MAX_PROJECTIONS} images`;draw();
  status('Image projected onto surfaces visible from its saved camera.');
}
function safe(fn){return async event=>{try{await fn(event);}catch(error){status(error.message,true);console.error(error);}};}

try {
  renderer=new Renderer($('view'),scene);$('object-count').textContent=scene.objects.length.toLocaleString();
  document.querySelectorAll('[data-shot]').forEach(button=>button.addEventListener('click',()=>{
    pause();state.shot=button.dataset.shot;state.progress=0;
    document.querySelectorAll('[data-shot]').forEach(b=>b.classList.toggle('active',b===button));
    $('shot-title').textContent=SHOTS[state.shot].name;$('midpoint').textContent=state.shot==='sweep'?'360° / SAME VIEW':'INSIDE THE LIBRARY';draw();
  }));
  $('aspect').addEventListener('change',()=>{state.aspect=$('aspect').value;draw();});
  $('mode').addEventListener('change',()=>{state.mode=$('mode').value;draw();});
  $('timeline').addEventListener('input',()=>{pause();state.progress=Number($('timeline').value);draw();});
  $('play').addEventListener('click',()=>{
    if(state.playing){pause();return;}if(state.progress>=1)state.progress=0;
    state.playing=true;state.lastTime=performance.now();$('play').textContent='Ⅱ';$('play').setAttribute('aria-label','Pause camera path');
  });
  $('reset').addEventListener('click',()=>{pause();state.progress=0;draw();});
  $('save-image').addEventListener('click',safe(()=>{
    const pair=captureSource();savePNG('meridian-reference.png',pair.png);
    status('Frame saved. “Save camera” exports the matching camera even if you move the playhead.');
  }));
  $('save-camera').addEventListener('click',safe(()=>{
    const pair=referencePair||captureSource();
    save('meridian-reference.camera.json',JSON.stringify(pair.reference,null,2),'application/json');
    status('Camera saved for the last saved frame. Keep this JSON with that image.');
  }));
  $('reference-file').addEventListener('change',safe(async event=>{
    const file=event.target.files[0];if(!file)return;
    importedReference=validateReference(JSON.parse(await file.text()),scene);
    status(`Camera loaded: ${importedReference.width} × ${importedReference.height}. Choose its matching image.`);
  }));
  $('image-file').addEventListener('change',safe(async event=>{
    const file=event.target.files[0];if(!file)return;
    const ref=importedReference||referencePair?.reference;
    if(!ref)throw new Error('Load the matching camera JSON first, or save a reference frame from this session.');
    const url=URL.createObjectURL(file);
    try{await project(url,ref);}finally{URL.revokeObjectURL(url);event.target.value='';}
  }));
  $('self-project').addEventListener('click',safe(async()=>{
    const pair=captureSource();await project(pair.png,pair.reference);
    status('Local render projected back onto its own geometry. Move the camera or inspect coverage.');
  }));
  $('clear').addEventListener('click',()=>{renderer.clearProjections();$('projection-count').textContent='0 / 8 images';draw();status('All projected images cleared.');});
  draw();status('House ready. No image generation services are connected.');requestAnimationFrame(frame);
  // Local deterministic capture API used by capture.mjs, not an external service.
  window.sceneLab={
    scene:{id:scene.id,geometryHash:hash,objects:scene.objects,rooms:scene.rooms,triangles:scene.vertices.length/33},
    renderFrame({shot='sweep',progress=0,width=1280,height=720,mode='beauty',camera=null}={}){
      pause();if(!Number.isFinite(progress)||progress<0||progress>1)throw new Error('Progress must be between zero and one.');
      if(!Number.isInteger(width)||!Number.isInteger(height)||width<16||height<16||width>4096||height>4096)throw new Error('Render dimensions must be integers from 16 to 4096.');
      state.shot=shot;state.progress=progress;
      const pose=camera||cameraAt(shot,progress),ref=reference(pose,width,height);validateReference(ref,scene);
      renderer.render(pose,{width,height,mode});return {png:renderer.png(),reference:ref};
    },
    async addProjection(dataURL,ref){await project(dataURL,ref);},
    clearProjections(){renderer.clearProjections();draw();},
    pixelHash(){let hash=2166136261;for(const v of renderer.pixels())hash=Math.imul(hash^v,16777619)>>>0;return hash.toString(16);},
    pixels(){return Array.from(renderer.pixels());},
    glError(){return renderer.gl.getError();},
  };
} catch(error) {status(error.message,true);window.sceneLabError=error.message;console.error(error);}
