import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';
import { createLedger, reserveSpend, readLedger, budgetSummary, reconcileSpend, updateSpend } from '../../mcp/video-generator/dist/production/ledger.js';
import { claudeRequestBody } from '../../mcp/video-generator/dist/clients/claude.js';
import { qualifyVeo } from '../../mcp/video-generator/dist/production/veo-spec.js';
import { interpretVeoOperation, submitVeoGeneration } from '../../mcp/video-generator/dist/clients/veo.js';

function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'film-budget-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return path.join(dir, 'budget.json');
}
test('all-in budget survives exact boundary, duplicate ID, corruption and attempted reset', t => {
  const p = fixture(t); createLedger(p, 2, 'Synthetic test allocation');
  const item = { id: 's01', category: 'veo', usd: 1.6, note: 'Eight silent seconds', fingerprint: 'a' };
  for (const id of [undefined, null, '', '../escape']) assert.throws(() => reserveSpend(p, { ...item, id }), /stable ID/);
  assert.equal(readLedger(p).entries.length, 0);
  reserveSpend(p, item);
  assert.throws(() => reserveSpend(p, item), /already reserved/);
  reserveSpend(p, { ...item, id: 'qa', category: 'qa', usd: .4 });
  assert.equal(budgetSummary(readLedger(p)).remainingUsd, 0);
  assert.throws(() => reserveSpend(p, { ...item, id: 'overflow', usd: .000001 }), /exceeded/);
  assert.throws(() => createLedger(p, 20, 'Reset'), /already exists/);
  fs.writeFileSync(p, '{broken');
  assert.throws(() => reserveSpend(p, { ...item, id: 'new' }));
});
test('uncertain spend stays committed until explicit evidence-based reconciliation', t => {
  const p = fixture(t); createLedger(p, 1, 'Synthetic allocation');
  reserveSpend(p, { id: 'image', category: 'image', usd: 1, fingerprint: 'x', note: 'Image allowance' });
  assert.throws(() => reconcileSpend(p, 'image', .1, ''), /evidence/);
  reconcileSpend(p, 'image', .1, 'Synthetic provider usage record');
  assert.equal(budgetSummary(readLedger(p)).remainingUsd, .9);
  assert.equal(readLedger(p).entries[0].history.length, 1);
});
test('live lock refuses writes; no expiry-based theft of a live reservation', t => {
  const p = fixture(t); createLedger(p, 1, 'Synthetic allocation');
  fs.writeFileSync(p + '.lock', '{}');
  assert.throws(() => reserveSpend(p, { id: 'a', category: 'qa', usd: .1, fingerprint: 'a', note: 'test' }), /locked/);
  assert.equal(readLedger(p).entries.length, 0);
});
test('qualified variants reject misleading parameters and quote exact audio/resolution cost', () => {
  assert.equal(qualifyVeo({ prompt: 'A lamp', generateAudio: false }).estimatedUsd, 1.6);
  assert.equal(qualifyVeo({ prompt: 'A lamp', model: 'veo-3.1-fast', resolution: '1080p' }).estimatedUsd, .96);
  assert.equal(qualifyVeo({ prompt: 'A lamp', model: 'veo-3.1' }).modelId, 'veo-3.1-generate-001');
  for (const invalid of [{ durationSeconds: 7 }, { durationSeconds: NaN }, { aspectRatio: '1:1' }, { resolution: '4k' }, { seed: -1 }, { lastFramePath: 'last.png' }])
    assert.throws(() => qualifyVeo({ prompt: 'test', ...invalid }));
});
test('finished filtered/empty/malformed output is terminal, not indefinite polling', () => {
  for (const response of [{}, { videos: [] }, { videos: [{}] }, { raiMediaFilteredCount: 1 }]) {
    const result = interpretVeoOperation({ done: true, response }, 'test-operation');
    assert.equal(result.done, true); assert.ok(result.error);
  }
  assert.equal(interpretVeoOperation({ done: false }, 'op').done, false);
  assert.equal(interpretVeoOperation({ done: true, response: { videos: [{ bytesBase64Encoded: 'test' }] } }, 'op').done, true);
});
test('missing or exhausted budgets fail before any network access', async t => {
  const original = globalThis.fetch; let calls = 0;
  globalThis.fetch = async () => { calls++; throw new Error('Network forbidden in test'); };
  t.after(() => { globalThis.fetch = original; });
  await assert.rejects(submitVeoGeneration({ prompt: 'test' }), /budgetFile/);
  const p = fixture(t); createLedger(p, .01, 'Synthetic allocation');
  await assert.rejects(submitVeoGeneration({ prompt: 'test', budgetFile: p, requestId: 's01' }), /exceeded/);
  assert.equal(calls, 0);
});
test('known operations resume without POST, while changed and ambiguous attempts refuse', async t => {
  const original = globalThis.fetch; let calls = 0;
  globalThis.fetch = async () => { calls++; throw new Error('Network forbidden in test'); };
  t.after(() => { globalThis.fetch = original; });
  const p = fixture(t); createLedger(p, 4, 'Synthetic allocation');
  const request = { prompt: 'A lamp', generateAudio: false, requestId: 's01', budgetFile: p };
  const fingerprint = createHash('sha256').update(JSON.stringify({ ...qualifyVeo(request), prompt: request.prompt,
    first: null, last: null, seed: null })).digest('hex');
  reserveSpend(p, { id: 's01', category: 'veo', fingerprint, usd: 1.6, note: 'Synthetic request' });
  await assert.rejects(submitVeoGeneration(request), /without a known operation/);
  updateSpend(p, 's01', { status: 'submitted', operationName: 'synthetic-operation', model: 'veo-3.1-generate-001', seed: 421 });
  assert.equal((await submitVeoGeneration(request)).operationName, 'synthetic-operation');
  await assert.rejects(submitVeoGeneration({ ...request, prompt: 'Changed lamp' }), /changed content/);
  assert.equal(calls, 0); assert.equal(readLedger(p).entries.length, 1);
});
test('concurrent processes cannot over-reserve the same allocation', async t => {
  const p = fixture(t); createLedger(p, 2, 'Synthetic concurrency allocation');
  const module = new URL('../../mcp/video-generator/dist/production/ledger.js', import.meta.url).href;
  const source = `import {reserveSpend} from ${JSON.stringify(module)};
    reserveSpend(process.argv[1], {id:process.argv[2],category:'veo',usd:1.6,fingerprint:'test',note:'Concurrent fixture'});`;
  const results = await Promise.allSettled([0, 1, 2, 3].map(i => promisify(execFile)(process.execPath,
    ['--input-type=module', '-e', source, p, 's' + i])));
  assert.equal(results.filter(r => r.status === 'fulfilled').length, 1);
  assert.equal(budgetSummary(readLedger(p)).committedUsd, 1.6);
});
test('current Claude request omits unsupported sampling and keeps vision content', () => {
  const messages = [{ role: 'user', content: [{ type: 'text', text: 'Describe only visible facts.' }] }];
  const body = claudeRequestBody({ model: 'claude-sonnet-5-5', maxTokens: 2000, system: 'Review', messages, temperature: .2 });
  assert.ok(!Object.hasOwn(body, 'temperature')); assert.deepEqual(body.messages, messages);
  assert.equal(claudeRequestBody({ model: 'legacy-model', maxTokens: 100, system: 'Review', messages, temperature: .2 }).temperature, .2);
});
