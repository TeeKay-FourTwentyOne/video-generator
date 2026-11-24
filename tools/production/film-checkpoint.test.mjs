import test from 'node:test';
import assert from 'node:assert/strict';
import { projectCheckpoint } from './film.mjs';

const quiet = async fn => { const w = process.stderr.write; process.stderr.write = () => true; try { return await fn(); } finally { process.stderr.write = w; } };

test('the analysis checkpoint is repeated once when its first pass is incomplete', async () => {
  const calls = [];
  const run = async (id, root) => { calls.push([id, root]); return { status: calls.length === 1 ? 'incomplete' : 'complete', report: 'r.json' }; };
  const result = await quiet(() => projectCheckpoint('my-film', '/repo', { process: run }));
  assert.equal(result.status, 'complete');
  assert.deepEqual(calls, [['my-film', '/repo'], ['my-film', '/repo']]);
});

test('a complete first pass is not repeated, and a second failure is reported as incomplete', async () => {
  let n = 0;
  assert.equal((await projectCheckpoint('a', '/r', { process: async () => { n += 1; return { status: 'complete' }; } })).status, 'complete');
  assert.equal(n, 1);
  n = 0;
  assert.equal((await projectCheckpoint('a', '/r', { process: async () => { n += 1; return { status: 'incomplete' }; } })).status, 'incomplete');
  assert.equal(n, 2);
});
