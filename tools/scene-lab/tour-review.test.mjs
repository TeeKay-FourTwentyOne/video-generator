import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {reviewSources} from './tour-review.mjs';

test('review assembly needs explicit selections and unchanged clip hashes',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'scene-tour-review-test-'));
  try{
    await mkdir(join(dir,'clips'));
    const clips=[];
    for(let shot=1;shot<=6;shot++){
      const data=Buffer.from(`fixture-${shot}`);
      await writeFile(join(dir,`clips/shot-${shot}.mp4`),data);
      clips.push({shot,take:1,durationSeconds:4,includedForReview:true,accepted:false,sha256:createHash('sha256').update(data).digest('hex')});
    }
    const review={verdict:'needs-review',clips};
    assert.equal((await reviewSources(dir,review)).length,6);
    await assert.rejects(reviewSources(dir,{...review,verdict:'approved'}),/not a final edit/);
    await assert.rejects(reviewSources(dir,{...review,clips:clips.slice(1)}),/six-shot/);
    const duplicate=structuredClone(review);duplicate.clips[5].shot=1;
    await assert.rejects(reviewSources(dir,duplicate),/explicit/);
    const implicit=structuredClone(review);delete implicit.clips[0].includedForReview;
    await assert.rejects(reviewSources(dir,implicit),/explicit/);
    const traversal=structuredClone(review);traversal.clips[0].take='../other';
    await assert.rejects(reviewSources(dir,traversal),/explicit/);
    await writeFile(join(dir,'clips/shot-1.mp4'),'changed fixture');
    await assert.rejects(reviewSources(dir,review),/bytes changed/);
  }finally{await rm(dir,{recursive:true,force:true});}
});
