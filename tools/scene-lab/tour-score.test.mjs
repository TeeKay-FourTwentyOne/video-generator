import test from 'node:test';
import assert from 'node:assert/strict';
import {compose,wav,loudnessJSON} from './tour-score.mjs';

test('original local score is finite, deterministic and has a valid stereo WAV',()=>{
  const a=compose({duration:2,sampleRate:8000}),b=compose({duration:2,sampleRate:8000});
  assert.deepEqual(a.left,b.left);assert.deepEqual(a.right,b.right);
  assert.equal(a.left.length,16000);
  assert.ok(a.events.length>60);
  let peak=0;for(const channel of [a.left,a.right])for(const value of channel){assert.ok(Number.isFinite(value));peak=Math.max(peak,Math.abs(value));}
  assert.ok(peak>.3&&peak<.351);assert.equal(a.left[0],0);
  const bytes=wav(a);assert.equal(bytes.length,44+16000*4);
  assert.equal(bytes.toString('ascii',0,4),'RIFF');assert.equal(bytes.readUInt16LE(22),2);assert.equal(bytes.readUInt32LE(24),8000);
});

test('loudnorm parser ignores surrounding FFmpeg diagnostics',()=>{
  assert.deepEqual(loudnessJSON('progress\n{\n"input_i":"-20.3","output_i":"-19.0"\n}\n[out] trailing stats'),{input_i:'-20.3',output_i:'-19.0'});
  assert.throws(()=>loudnessJSON('no measurements'),/No loudnorm/);
});
