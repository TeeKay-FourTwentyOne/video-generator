import test from 'node:test';
import assert from 'node:assert/strict';
import {delta,search} from './seam-search.mjs';

test('local seam search finds an interior overlap and preserves separate motion metrics',()=>{
  const make=indices=>{const frames=indices.map(n=>Uint8Array.from({length:400},(_,k)=>(k+n*7)%256));return {frames,means:frames.map(f=>f.reduce((s,v)=>s+v,0)/f.length),adjacent:frames.slice(1).map((f,i)=>delta(frames[i],f))};};
  const a=make(Array.from({length:48},(_,i)=>i)),b=make(Array.from({length:36},(_,i)=>i+30));
  const found=search(a,b,{aStart:28,bEnd:10});
  assert.equal(found.top[0].mae,0);
  assert.equal(found.top[0].aFrame,found.top[0].bFrame+30);
  assert.ok(found.baseline.mae>0);
  assert.ok(Number.isFinite(found.top[0].velocityRatio));
  assert.ok(Number.isFinite(found.top[0].motionCosine));
});
