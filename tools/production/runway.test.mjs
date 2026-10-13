import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createLedger, readLedger, updateSpend, budgetSummary } from '../../mcp/video-generator/dist/production/ledger.js';
import { qualifyRunway, prepareRunwayRequest } from '../../mcp/video-generator/dist/production/runway-spec.js';
import { submitRunwayGeneration, pollRunwayOperation, interpretRunwayTask, getRunwayAccount,
  recoverRunwayOperation, downloadRunwayVideo } from '../../mcp/video-generator/dist/clients/runway.js';
import { main as filmMain, readJson, hashFile, videoProvider } from './film.mjs';
const main = args => filmMain(args, { catalogRoot: args[1] && path.isAbsolute(args[1]) ? path.join(args[1], 'catalog-fixture') : undefined });

const credential = 'synthetic-runway-credential';
const id = '00000000-0000-4000-8000-000000000001';
const id2 = '00000000-0000-4000-8000-000000000002';
const outputUrl = 'https://fixture.cloudfront.net/fixture.mp4?token=private-fixture';
const base = { provider: 'runway', model: 'gen4.5', prompt: 'A lamp turns on.', durationSeconds: 8,
  aspectRatio: '16:9', resolution: '720p', seed: 0 };
const json = (value, status = 200) => new Response(JSON.stringify(value), { status });
const task = (status = 'SUCCEEDED', extra = {}) => ({ id, status, createdAt: '2026-10-11T12:00:00.000Z',
  output: [outputUrl], cost: { credits: 96 }, ...extra });
function fixture(t, limit = 2) {
  fs.mkdirSync('data/workspace', { recursive: true });
  const root = fs.mkdtempSync(path.resolve('data/workspace/runway-test-'));
  t.after(() => fs.rmSync(root, { force: true, recursive: true }));
  for (const d of ['refs', 'prompts', 'clips', 'operations']) fs.mkdirSync(path.join(root, d));
  const budgetFile = path.join(root, 'budget.json');
  createLedger(budgetFile, limit, 'Synthetic offline test allocation');
  return { root, budgetFile, request: { ...base, requestId: 'S01-v1', budgetFile } };
}
function network(t, handler) {
  const original = globalThis.fetch, previousKey = process.env.RUNWAYML_API_SECRET;
  process.env.RUNWAYML_API_SECRET = credential;
  const calls = [];
  globalThis.fetch = async (url, options) => { calls.push({ url: String(url), options }); return handler(String(url), options); };
  t.after(() => { globalThis.fetch = original;
    if (previousKey === undefined) delete process.env.RUNWAYML_API_SECRET; else process.env.RUNWAYML_API_SECRET = previousKey;
  });
  return calls;
}
function media(root) {
  const video = path.join(root, 'refs/motion.mp4'), image = path.join(root, 'refs/start.png');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=512x288:r=24', '-t', '2',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', video]);
  execFileSync('ffmpeg', ['-v', 'error', '-i', video, '-frames:v', '1', image]);
  return { video, image };
}

test('Runway pricing, model input requirements and strict unsupported-control validation', () => {
  assert.equal(qualifyRunway(base).estimatedUsd, .96);
  assert.equal(qualifyRunway({ ...base, model: 'gen4_turbo', firstFramePath: 'frame.png' }).estimatedUsd, .4);
  assert.equal(qualifyRunway({ ...base, firstFramePath: 'frame.png', aspectRatio: '1:1' }).ratio, '960:960');
  for (const changes of [{ durationSeconds: 1 }, { durationSeconds: 11 }, { durationSeconds: 2.5 }, { durationSeconds: NaN },
    { prompt: '' }, { prompt: 'a'.repeat(1001) }, { prompt: '😀'.repeat(501) }, { model: 'veo3.1' }, { provider: 'veo' },
    { model: 'gen4_turbo' }, { aspectRatio: '1:1' }, { aspectRatio: 'toString' }, { resolution: '1080p' },
    { generateAudio: true }, { seed: -1 }, { seed: 4294967296 }, { firstFramePath: '' },
    { lastFramePath: 'end.png' }, { promptExpansionMode: 'quality' }, { outputFormat: 'prores' }, { referenceImagePaths: [] }])
    assert.throws(() => qualifyRunway({ ...base, ...changes }));
  assert.equal(qualifyRunway({ ...base, seed: 4294967295, durationSeconds: 2 }).estimatedUsd, .24);
  assert.equal(videoProvider(base), 'runway');
});

test('Runway local image validation prevents silent crops, disguised files and oversized inline payloads', t => {
  const { root } = fixture(t), { image, video } = media(root);
  const prepared = prepareRunwayRequest({ ...base, firstFramePath: image });
  const body = JSON.parse(prepared.serializedBody);
  assert.equal(prepared.endpoint, '/v1/image_to_video');
  assert.equal(body.seed, 0); assert.equal(body.ratio, '1280:720');
  assert.ok(body.promptImage.startsWith('data:image/png;base64,'));
  assert.equal(prepared.sources[0].sha256, hashFile(image));
  assert.equal(prepareRunwayRequest(base).endpoint, '/v1/text_to_video');
  const copy = path.join(root, 'refs/same.png'); fs.copyFileSync(image, copy);
  assert.equal(prepareRunwayRequest({ ...base, firstFramePath: copy }).fingerprint, prepared.fingerprint);
  assert.throws(() => prepareRunwayRequest({ ...base, firstFramePath: image, aspectRatio: '9:16' }), /aspect ratio/);
  fs.copyFileSync(video, copy);
  assert.throws(() => prepareRunwayRequest({ ...base, firstFramePath: copy }), /encoded/);
  fs.writeFileSync(copy, Buffer.alloc(4_000_000));
  assert.throws(() => prepareRunwayRequest({ ...base, firstFramePath: copy }), /encoded data URI/);
});

test('Runway budget and missing credentials prevent paid submission', async t => {
  const calls = network(t, () => { throw new Error('Unexpected fetch'); });
  const { request, budgetFile } = fixture(t, .01);
  await assert.rejects(submitRunwayGeneration(base), /budgetFile/);
  await assert.rejects(submitRunwayGeneration(request), /Budget exceeded/);
  process.env.RUNWAYML_API_SECRET = '';
  await assert.rejects(submitRunwayGeneration(request), /Configure RUNWAYML_API_SECRET/);
  assert.equal(calls.length, 0); assert.equal(readLedger(budgetFile).entries.length, 0);
});

test('Runway reserves before POST, journals safely and prevents duplicate or changed submissions', async t => {
  const { root, request, budgetFile } = fixture(t);
  const calls = network(t, (url, options) => {
    assert.equal(url, 'https://api.dev.runwayml.com/v1/text_to_video');
    assert.equal(options.method, 'POST'); assert.equal(options.redirect, 'error');
    assert.equal(options.headers.Authorization, `Bearer ${credential}`);
    assert.equal(options.headers['X-Runway-Version'], '2024-11-06');
    assert.equal(readLedger(budgetFile).entries[0].reservedMicros, 960000);
    assert.equal(readJson(path.join(root, 'operations/S01-v1.json')).status, 'reserved');
    const snapshot = readJson(path.join(root, 'operations/S01-v1.request.json'));
    assert.equal(snapshot.prompt, base.prompt); assert.equal(snapshot.model, 'gen4.5');
    assert.equal(snapshot.seed, 0); assert.equal(snapshot.parameters.ratio, '1280:720');
    assert.equal(snapshot.api.version, '2024-11-06');
    assert.equal(snapshot.parameters.generateAudio, false);
    assert.deepEqual(JSON.parse(options.body), { model: 'gen4.5', promptText: base.prompt, duration: 8, ratio: '1280:720', seed: 0 });
    return json({ id, debug: credential });
  });
  assert.equal((await submitRunwayGeneration(request)).operationName, id);
  const snapshotBefore = fs.readFileSync(path.join(root, 'operations/S01-v1.request.json'), 'utf8');
  process.env.RUNWAYML_API_SECRET = '';
  assert.equal((await submitRunwayGeneration(request)).operationName, id);
  await assert.rejects(submitRunwayGeneration({ ...request, seed: 1 }), /changed content/);
  assert.equal(calls.length, 1);
  assert.ok(!fs.readFileSync(path.join(root, 'operations/S01-v1.json'), 'utf8').includes(credential));
  updateSpend(budgetFile, request.requestId, { operationName: undefined, status: 'uncertain' });
  await submitRunwayGeneration(request);
  assert.equal(fs.readFileSync(path.join(root, 'operations/S01-v1.request.json'), 'utf8'), snapshotBefore);
  assert.equal(readLedger(budgetFile).entries[0].operationName, id);
  assert.equal(calls.length, 1);
});

test('Runway timeout, malformed success and HTTP failures retain money and never retry automatically', async t => {
  let action;
  const calls = network(t, () => action());
  for (const [fn, status] of [[() => { throw new Error(credential); }, 'uncertain'],
    [() => json({}, 503), 'uncertain'], [() => json({ error: credential }, 402), 'failed'],
    [() => json({ id: 'invalid' }), 'uncertain'], [() => new Response(credential), 'uncertain']]) {
    action = fn;
    const { request, budgetFile } = fixture(t);
    await assert.rejects(submitRunwayGeneration(request), e => !e.message.includes(credential));
    assert.equal(readLedger(budgetFile).entries[0].status, status);
    assert.equal(budgetSummary(readLedger(budgetFile)).committedUsd, .96);
    const count = calls.length;
    await assert.rejects(submitRunwayGeneration(request), /already reserved/);
    assert.equal(calls.length, count);
  }
});

test('Runway concurrent submit permits only one POST for a request ID', async t => {
  const { request } = fixture(t);
  let release;
  const calls = network(t, () => new Promise(resolve => { release = () => resolve(json({ id })); }));
  const first = submitRunwayGeneration(request);
  await assert.rejects(submitRunwayGeneration(request), /already reserved/);
  release(); await first;
  assert.equal(calls.length, 1);
});

test('Runway task decoding handles throttling, terminal errors, empty outputs and reported costs', () => {
  for (const status of ['PENDING', 'THROTTLED', 'RUNNING']) {
    const decoded = interpretRunwayTask(task(status, { estimatedCost: { credits: 96 } }), id, 'gen4.5');
    assert.equal(decoded.done, false); assert.equal(decoded.estimatedCostCredits, 96); assert.equal(decoded.costCredits, undefined);
  }
  for (const status of ['FAILED', 'CANCELLED']) {
    const decoded = interpretRunwayTask(task(status, { failure: credential, failureCode: 'SAFETY.INPUT.TEXT', cost: { credits: 0 } }), id, 'gen4.5');
    assert.equal(decoded.done, true); assert.equal(decoded.costCredits, 0); assert.ok(!decoded.error.includes(credential));
  }
  assert.equal(interpretRunwayTask(task(), id, 'gen4.5').costCredits, 96);
  assert.match(interpretRunwayTask(task('SUCCEEDED', { output: [] }), id, 'gen4.5').error, /without exactly one/);
  assert.throws(() => interpretRunwayTask(task(), id2, 'gen4.5'), /mismatched/);
  assert.throws(() => interpretRunwayTask(task('UNKNOWN'), id, 'gen4.5'), /mismatched/);
});

test('Runway account query and explicit recovery use read-only endpoints and require evidence', async t => {
  const { request, budgetFile } = fixture(t);
  let failPost = true;
  const calls = network(t, (url, options) => {
    if (options.method === 'POST' && failPost) throw new Error('Simulated lost response');
    if (url.endsWith('/organization')) return json({ creditBalance: 1000, privateAccount: credential,
      tier: { models: { 'gen4.5': { maxConcurrentGenerations: 1, maxDailyGenerations: 50 } } } });
    return json(task('RUNNING'));
  });
  assert.equal((await getRunwayAccount()).balanceUsd, 10);
  assert.ok(!JSON.stringify(await getRunwayAccount()).includes(credential));
  await assert.rejects(submitRunwayGeneration(request), /transport/);
  const count = calls.length; failPost = false;
  await assert.rejects(recoverRunwayOperation(request, id, ''), /evidence/);
  assert.equal(calls.length, count);
  await recoverRunwayOperation(request, id, 'Matched original prompt and timestamp in provider portal');
  assert.equal(readLedger(budgetFile).entries[0].operationName, id);
  assert.equal(calls.filter(c => c.options.method === 'POST').length, 1);
  assert.equal((await pollRunwayOperation(id, 'gen4.5')).done, false);
});

test('Runway download isolates credentials, refuses unsafe redirects and preserves prior files', async t => {
  const { root } = fixture(t), output = path.join(root, 'clips/S01.mp4');
  let mode = 'success';
  const calls = network(t, (url, options) => {
    assert.equal(options.headers, undefined);
    if (mode === 'redirect') return new Response(null, { status: 302, headers: { location: 'http://127.0.0.1/private' } });
    if (mode === 'transport') throw new Error(`${credential} ${outputUrl}`);
    if (mode === 'partial') return new Response(new ReadableStream({start(controller) {
      controller.enqueue(new Uint8Array([1,2])); controller.error(new Error(`${credential} ${outputUrl}`));
    }}));
    if (mode === 'empty') return new Response('');
    return new Response('fixture video');
  });
  const result = interpretRunwayTask(task(), id, 'gen4.5');
  await assert.rejects(downloadRunwayVideo({ ...result, video: { uri: 'https://untrusted.example/video' } }, output), /host/);
  assert.equal(calls.length, 0);
  mode = 'redirect'; await assert.rejects(downloadRunwayVideo(result, output), /host/);
  mode = 'empty'; await assert.rejects(downloadRunwayVideo(result, output), /incomplete/);
  for (const failure of ['transport','partial']) {
    mode = failure;
    await assert.rejects(downloadRunwayVideo(result, output), e => !e.message.includes(credential) && !e.message.includes(outputUrl));
  }
  assert.deepEqual(fs.readdirSync(path.dirname(output)), []);
  mode = 'success'; await downloadRunwayVideo(result, output);
  assert.equal(fs.statSync(output).mode & 0o777, 0o600);
  await assert.rejects(downloadRunwayVideo(result, output), /already exists/);
  assert.equal(fs.readFileSync(output, 'utf8'), 'fixture video');
});

test('Runway CLI dry plan, native download, cached polling and cost reconciliation share the ledger', async t => {
  const { root, budgetFile } = fixture(t), { video } = media(root);
  const plan = { schemaVersion: 1, title: 'Fixture', width: 1280, height: 720, fps: 24,
    shots: [{ id: 'S01', beat: 'A lamp turns on', frames: 192, requestId: 'S01-v1', request: base }] };
  fs.writeFileSync(path.join(root, 'film.json'), JSON.stringify(plan));
  const calls = network(t, (url, options) => options.method === 'POST' ? json({ id })
    : url.startsWith('https://api.dev.runwayml.com') ? json(task()) : new Response(fs.readFileSync(video)));
  assert.equal((await main(['plan', root])).videoQuoteUsd, .96); assert.equal(calls.length, 0);
  await main(['submit', root, 'S01']);
  plan.shots[0].request = { provider: 'veo', promptFile: 'prompts/removed.txt', firstFramePath: 'refs/moved.png', seed: 1 };
  fs.writeFileSync(path.join(root, 'film.json'), JSON.stringify(plan));
  const result = await main(['poll', root, 'S01']);
  assert.equal(result.status, 'complete');
  const generation = readJson(path.join(root, 'catalog-fixture/catalog/clips', `${result.clipId}.json`)).generations[0];
  assert.equal(generation.prompt, base.prompt); assert.equal(generation.model, base.model);
  assert.equal(generation.seed, 0); assert.equal(generation.parameters.durationSeconds, 8);
  assert.equal(generation.source, 'creation-snapshot');
  const count = calls.length;
  assert.equal((await main(['poll', root, 'S01'])).status, 'complete'); assert.equal(calls.length, count);
  assert.equal((await main(['reconcile-runway', root, 'S01'])).usd, .96);
  assert.equal(readLedger(budgetFile).entries[0].status, 'reconciled');
  plan.shots[0].request.seed = 1;
  fs.writeFileSync(path.join(root, 'film.json'), JSON.stringify(plan));
  assert.equal((await main(['poll', root, 'S01'])).status, 'complete');
  assert.equal(calls.length, count);
  assert.equal(readJson(path.join(root, 'catalog-fixture/catalog/clips', `${result.clipId}.json`)).generations.length, 1);
  fs.unlinkSync(path.join(root, 'operations/S01-v1.request.json'));
  await assert.rejects(main(['poll', root, 'S01']), /snapshot is missing/);
  assert.equal(calls.length, count);
});

test('Runway terminal failures stop CLI polling and retain reservations until reported-cost reconciliation', async t => {
  const { root, budgetFile } = fixture(t);
  fs.writeFileSync(path.join(root, 'film.json'), JSON.stringify({ schemaVersion: 1, title: 'Fixture', width: 1280, height: 720, fps: 24,
    shots: [{ id: 'S01', beat: 'Lamp', frames: 192, requestId: 'S01-v1', request: base }] }));
  const calls = network(t, (_url, options) => options.method === 'POST' ? json({ id })
    : json(task('FAILED', { failure: credential, cost: { credits: 0 } })));
  await main(['submit', root, 'S01']);
  await assert.rejects(main(['poll', root, 'S01', '--wait=60']), /failed/);
  assert.equal(calls.length, 2); assert.equal(budgetSummary(readLedger(budgetFile)).committedUsd, .96);
  assert.equal((await main(['reconcile-runway', root, 'S01'])).usd, 0);
  assert.equal(budgetSummary(readLedger(budgetFile)).committedUsd, 0);
});
