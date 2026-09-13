import test from 'node:test';
import assert from 'node:assert/strict';
import { buildScene } from './scene.mjs';
import { cameraAt, cameraMatrix, transform, sub, cross, dot } from './math.mjs';
import { geometryHash, validateReference } from './reference.mjs';
import { startServer } from './server.mjs';
import { openBrowser } from './chrome.mjs';

const scene=buildScene();
test('Camera calibration maps its target to center and preserves world up',()=>{
  for(const aspect of [16/9,9/16]){
    const camera={eye:[0,1.7,3.8],target:[0,1.7,-2],fov:64},vp=cameraMatrix(camera,aspect);
    const center=transform(vp,camera.target),above=transform(vp,[0,2.7,-2]),right=transform(vp,[1,1.7,-2]);
    assert.ok(Math.abs(center[0]/center[3])<1e-6);assert.ok(Math.abs(center[1]/center[3])<1e-6);
    assert.ok(above[1]/above[3]>0);assert.ok(right[0]/right[3]>0);assert.ok(center[3]>0);
  }
});
test('Corresponding sweep poses and tour endpoints are exactly repeatable',()=>{
  for(let i=0;i<72;i++)assert.deepEqual(cameraAt('sweep',i/144),cameraAt('sweep',i/144+.5));
  assert.deepEqual(cameraAt('sweep',0),cameraAt('sweep',1));
  assert.deepEqual(cameraAt('tour',0),cameraAt('tour',1));
});
test('Camera metadata rejects changed geometry, invalid dimensions, and singular poses',()=>{
  const ref={schemaVersion:1,sceneId:scene.id,geometryHash:geometryHash(scene.vertices),width:1280,height:720,camera:cameraAt('sweep',0)};
  assert.equal(validateReference(ref,scene),ref);
  assert.throws(()=>validateReference({...ref,geometryHash:'changed'},scene));
  assert.throws(()=>validateReference({...ref,width:0},scene));
  assert.throws(()=>validateReference({...ref,camera:{eye:[0,0,0],target:[0,1,0],fov:64}},scene));
  assert.ok(scene.vertices.every(Number.isFinite));
});
test('The tour centerline does not cross scene triangles',()=>{
  // Segment/triangle intersection catches walls placed across a nominal doorway.
  const data=scene.vertices;
  for(let step=0;step<100;step++){
    const a=cameraAt('tour',step/100).eye,b=cameraAt('tour',(step+1)/100).eye,direction=sub(b,a);
    if(Math.hypot(...direction)<1e-8)continue;
    for(let i=0;i<data.length;i+=33){
      const p=Array.from(data.slice(i,i+3)),q=Array.from(data.slice(i+11,i+14)),r=Array.from(data.slice(i+22,i+25));
      if([0,1,2].some(k=>Math.max(a[k],b[k])<Math.min(p[k],q[k],r[k])||Math.min(a[k],b[k])>Math.max(p[k],q[k],r[k])))continue;
      const e1=sub(q,p),e2=sub(r,p),h=cross(direction,e2),det=dot(e1,h);if(Math.abs(det)<1e-10)continue;
      const s=sub(a,p),u=dot(s,h)/det;if(u<0||u>1)continue;
      const c=cross(s,e1),v=dot(direction,c)/det;if(v<0||u+v>1)continue;
      const t=dot(e2,c)/det;
      assert.ok(t<0||t>1,`Camera crossed triangle ${i/33} at tour segment ${step}`);
    }
  }
});
test('GPU projections respect occlusion, and preview controls work',async()=>{
  const {server,url}=await startServer(0);let browser;
  try{
    browser=await openBrowser(url);
    const result=await browser.evaluate(`(async()=>{
      const width=640,height=360;
      const source=sceneLab.renderFrame({width,height,progress:0});
      sceneLab.renderFrame({width,height,mode:'clay'});const clayBefore=sceneLab.pixelHash();
      const sample=camera=>{
        sceneLab.renderFrame({width,height,camera});const p=sceneLab.pixels();
        const index=((height/2)*width+width/2)*4;return p.slice(index,index+3);
      };
      // The source ray hits the sun; this offset ray reaches the window behind it
      // without hitting an orbit ring. These sight lines were checked on the mesh.
      const hidden={eye:[-4,1.8,2.5],target:[.25,2.42,-5.815],fov:64};
      const visible={eye:[-4,1.8,2.5],target:[-2,2.4,-5.87],fov:64};
      const hiddenBefore=sample(hidden),visibleBefore=sample(visible);
      const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
      const ctx=canvas.getContext('2d');ctx.fillStyle='#ff00ff';ctx.fillRect(0,0,width,height);
      await sceneLab.addProjection(canvas.toDataURL('image/png'),source.reference);
      sceneLab.renderFrame({width,height,mode:'clay'});const clayAfter=sceneLab.pixelHash();
      const hiddenAfter=sample(hidden),visibleAfter=sample(visible),glError=sceneLab.glError();
      sceneLab.clearProjections();
      document.querySelector('[data-shot="tour"]').click();
      const title=document.getElementById('shot-title').textContent;
      document.getElementById('aspect').value='9:16';document.getElementById('aspect').dispatchEvent(new Event('change'));
      const dimensions=[document.getElementById('view').width,document.getElementById('view').height];
      document.getElementById('timeline').value='.5';document.getElementById('timeline').dispatchEvent(new Event('input'));
      const pose=document.getElementById('pose-label').textContent;
      return {hiddenBefore,hiddenAfter,visibleBefore,visibleAfter,glError,title,dimensions,pose,clayBefore,clayAfter};
    })()`);
    assert.deepEqual(result.hiddenAfter,result.hiddenBefore,`Paint leaked behind the orrery: ${JSON.stringify(result)}`);
    assert.ok(result.visibleAfter[0]>240&&result.visibleAfter[1]<15&&result.visibleAfter[2]>240,`Visible wall did not receive the projection: ${JSON.stringify(result)}`);
    assert.equal(result.glError,0);assert.equal(result.title,'Library & return');assert.deepEqual(result.dimensions,[720,1280]);assert.match(result.pose,/X -8.60/);
    assert.equal(result.clayAfter,result.clayBefore,'Clay geometry inspection must ignore projected images.');
    const large=await browser.evaluateLarge(`Promise.resolve({text:'frame-data-'.repeat(500000),nested:[true,42,null]})`);
    assert.equal(large.text,'frame-data-'.repeat(500000));assert.deepEqual(large.nested,[true,42,null]);
    assert.deepEqual(await browser.evaluate(`Object.keys(globalThis).filter(key=>key.startsWith('__sceneLabTransfer'))`),[]);
    await assert.rejects(browser.evaluateLarge(`Promise.reject(new Error('transfer test'))`),/transfer test/);
    const traversal=await fetch(`${url}/data/config.json`);assert.equal(traversal.status,404);
    const post=await fetch(url,{method:'POST',body:'test'});assert.equal(post.status,404);
  }finally{await browser?.close();await new Promise(resolve=>server.close(resolve));}
});
