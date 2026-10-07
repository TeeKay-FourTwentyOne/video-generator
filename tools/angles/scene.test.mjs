import test from 'node:test';
import assert from 'node:assert/strict';
import {buildScene,cameraAt,cavityDistance,dot,SHOTS} from './scene.mjs';
test('all 240 held poses rotate at the center with an orthonormal camera',()=>{
 for(let i=0;i<240;i++){
  const c=cameraAt(i/8);assert.deepEqual(c.eye,[0,0,0]);
  for(const v of [c.forward,c.right,c.up])assert.ok(Math.abs(dot(v,v)-1)<1e-12);
  assert.ok(Math.abs(dot(c.forward,c.right))<1e-12);assert.ok(Math.abs(dot(c.up,c.right))<1e-12);
 }
});
test('irregular cavity has measurable relief; baseline is an exact sphere',()=>{
 const s=buildScene();assert.deepEqual(s,buildScene());
 const distances=s.planes.map(p=>cavityDistance(p.normal,s));
 assert.ok(Math.max(...distances)-Math.min(...distances)>.6);
 for(const p of s.planes)assert.equal(cavityDistance(p.normal,s,true),s.radius);
 for(const r of s.rings)assert.ok(Math.hypot(...r.center)-r.outer>.4);
});
test('cuts partition 30 seconds and return to the first orientation',()=>{
 assert.equal(SHOTS[0].start,0);assert.equal(SHOTS.at(-1).end,30);
 for(let i=1;i<SHOTS.length;i++)assert.equal(SHOTS[i-1].end,SHOTS[i].start);
 assert.deepEqual(cameraAt(0).forward,cameraAt(29.875).forward);
 assert.notDeepEqual(cameraAt(5.875).forward,cameraAt(6).forward);
});
