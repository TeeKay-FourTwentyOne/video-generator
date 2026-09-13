import test from 'node:test';
import assert from 'node:assert/strict';
import {validateEdit} from './tour-finish.mjs';
import {readFileSync} from 'node:fs';
import {SPEEDS} from './tour-retime.mjs';

test('matched-anchor edit excludes the duplicate anchor and counts cuts exactly',()=>{
  const plan={fps:24,clips:Array.from({length:6},(_,i)=>({shot:i+1,take:1,startFrame:0,endFrameExclusive:i===5?89:88}))};
  assert.deepEqual(validateEdit(plan),{frames:529,seconds:529/24,cutFrames:[88,176,264,352,440],cutTimes:[88,176,264,352,440].map(n=>n/24)});
  const invalid=structuredClone(plan);invalid.clips[1].endFrameExclusive=97;
  assert.throws(()=>validateEdit(invalid),/frame-exact/);
  invalid.clips[1].endFrameExclusive=0;
  assert.throws(()=>validateEdit(invalid),/frame-exact/);
});

test('published Meridian recipe preserves reviewed ranges and retime settings',()=>{
  const plan=JSON.parse(readFileSync(new URL('../../briefs/meridian_house_edit.json',import.meta.url),'utf8'));
  assert.equal(validateEdit(plan).frames,529);
  assert.deepEqual(plan.finish.speedRamps,SPEEDS);
  assert.equal(plan.finish.frames,576);
  assert.equal(plan.finish.sourceAnchorFrame,88);
  for(const [i,clip] of plan.clips.entries()){
    assert.equal(clip.file,`clips/shot-${i+1}.mp4`);
    assert.match(clip.sha256,/^[a-f0-9]{64}$/);
  }
});
