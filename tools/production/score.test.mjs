import test from 'node:test';
import assert from 'node:assert/strict';
import { synthesize } from './score.mjs';
import { wav } from '../scene-lab/tour-score.mjs';

test('cue score is reproducible, frame-duration aligned, finite and refuses invalid events', () => {
  const cue = { duration: 1.25, events: [
    { voice: 'bell', at: .1, length: .9, midi: 72, amp: .08, pan: -.3 },
    { voice: 'air', at: 0, length: 1.25, midi: 60, amp: .02 },
  ] };
  const a = synthesize(cue), b = synthesize(cue);
  assert.equal(a.left.length, 60000);
  assert.deepEqual(wav(a), wav(b));
  assert.ok(a.peak > 0 && a.peak < .9);
  assert.ok(a.left.every(Number.isFinite)); assert.ok(a.right.every(Number.isFinite));
  assert.equal(wav(a).readUInt32LE(40), 60000 * 4);
  for (const patch of [{ at: -1 }, { at: NaN }, { length: 10 }, { voice: 'unknown' }, { amp: 2 }])
    assert.throws(() => synthesize({ ...cue, events: [{ ...cue.events[0], ...patch }] }), /Invalid audio cue/);
});
