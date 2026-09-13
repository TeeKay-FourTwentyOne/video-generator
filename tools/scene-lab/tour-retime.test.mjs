import test from 'node:test';
import assert from 'node:assert/strict';
import {sourceAt,timeAtSource,SPEEDS} from './tour-retime.mjs';

test('camera retime is monotonic, matches the anchor and is invertible',()=>{
  for(const s of SPEEDS){
    assert.ok(Math.abs(sourceAt(0,s))<1e-8);
    assert.ok(Math.abs(sourceAt(1,s)-88)<1e-8);
    let prev=-1;
    for(let i=0;i<=1000;i++){const x=sourceAt(i/1000,s);assert.ok(x>prev);prev=x;}
    for(let n=0;n<=88;n++)assert.ok(Math.abs(sourceAt(timeAtSource(n,s)/4,s)-n)<1e-8);
    assert.ok(Math.abs((sourceAt(1e-5,s)-sourceAt(0,s))/(96e-5)-s.start)<1e-4);
    assert.ok(Math.abs((sourceAt(1,s)-sourceAt(1-1e-5,s))/(96e-5)-s.end)<1e-4);
  }
});
