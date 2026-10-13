import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createLedger, readLedger, updateSpend, budgetSummary } from '../../mcp/video-generator/dist/production/ledger.js';
import { qualifyMiniMax } from '../../mcp/video-generator/dist/production/minimax-spec.js';
import { prepareMiniMaxRequest, submitMiniMaxGeneration, pollMiniMaxOperation, interpretMiniMaxTask,
  listMiniMaxTasks, recoverMiniMaxOperation, downloadMiniMaxVideo } from '../../mcp/video-generator/dist/clients/minimax.js';
import { main as filmMain, readJson, hashFile, videoProvider } from './film.mjs';
const main = args => filmMain(args, { catalogRoot: args[1] && path.isAbsolute(args[1]) ? path.join(args[1], 'catalog-fixture') : undefined });

const credential = 'synthetic-minimax-credential';
const outputUrl = 'https://video-product.cdn.minimax.io/fixture.mp4?token=private-fixture';
const base = { provider: 'minimax', model: 'MiniMax-H3-Max', prompt: 'A lamp turns on.', durationSeconds: 6,
  resolution: '768P', aspectRatio: '16:9' };
const json = (value, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } });
const task = (status = 'succeeded', extra = {}) => ({ id: 'fixture-task', model: base.model, status,
  resolution: '768P', duration: 6, ratio: '16:9', task_type: 'generation', content: { url: outputUrl },
  usage: { output_seconds: 6, input_seconds: 0, input_image_count: 1 }, ...extra });

function fixture(t, limit = 5) {
  fs.mkdirSync('data/workspace', { recursive: true });
  const root = fs.mkdtempSync(path.resolve('data/workspace/minimax-test-'));
  t.after(() => fs.rmSync(root, { force: true, recursive: true }));
  for (const d of ['refs', 'prompts', 'clips', 'operations']) fs.mkdirSync(path.join(root, d));
  const budgetFile = path.join(root, 'budget.json');
  createLedger(budgetFile, limit, 'Synthetic offline test allocation');
  return { root, budgetFile, request: { ...base, requestId: 'S01-v1', budgetFile } };
}
function network(t, handler) {
  const original = globalThis.fetch;
  const previousKey = process.env.MINIMAX_API_KEY;
  process.env.MINIMAX_API_KEY = credential;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    return handler(String(url), options, calls.length);
  };
  t.after(() => {
    globalThis.fetch = original;
    if (previousKey === undefined) delete process.env.MINIMAX_API_KEY; else process.env.MINIMAX_API_KEY = previousKey;
  });
  return calls;
}
function media(root) {
  const video = path.join(root, 'refs/motion.mp4');
  const image = path.join(root, 'refs/start.png');
  const audio = path.join(root, 'refs/voice.wav');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=512x288:r=24', '-t', '2',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', video]);
  execFileSync('ffmpeg', ['-v', 'error', '-i', video, '-frames:v', '1', image]);
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', '2', audio]);
  return { video, image, audio };
}

test('MiniMax quotes include model-specific image/video rates and conservative fractional input seconds', () => {
  assert.equal(qualifyMiniMax(base).estimatedUsd, .48);
  assert.equal(qualifyMiniMax({ ...base, resolution: '480P' }).estimatedUsd, .30);
  assert.equal(qualifyMiniMax({ ...base, model: 'MiniMax-H3', resolution: '2K' }).estimatedUsd, .78);
  const max = qualifyMiniMax({ ...base, referenceImagePaths: ['a', 'b', 'c'], referenceVideoPaths: ['d'] }, { video: [2.1], audio: [] });
  assert.equal(max.inputImagesUsd, .074);
  assert.equal(max.inputVideoUsd, .429);
  assert.equal(max.estimatedUsd, .983);
  const standard = qualifyMiniMax({ ...base, model: 'MiniMax-H3', resolution: '2K',
    referenceImagePaths: ['a', 'b', 'c', 'd', 'e', 'f'], referenceVideoPaths: ['g'], referenceAudioPaths: ['h'] }, { video: [2], audio: [2] });
  assert.equal(standard.estimatedUsd, 1.08);
});

test('unsupported parameters, incompatible modes and unmeasured references fail locally', () => {
  for (const changes of [{ durationSeconds: 4 }, { durationSeconds: 5.5 }, { durationSeconds: NaN }, { resolution: '2K' },
    { model: 'MiniMax-H3', resolution: '480P' }, { prompt: '' }, { prompt: 'x'.repeat(7001) }, { model: 'Hailuo-02' },
    { seed: 42 }, { generateAudio: false }, { aspectRatio: 'adaptive' }, { provider: 'fal' }, { referenceImagePaths: 'a.png' },
    { firstFramePath: 'a.png', referenceImagePaths: ['b.png'] }, { referenceImagePaths: Array(10).fill('a.png') },
    { promptExpansionMode: 'balance' }, { model: 'MiniMax-H3', promptExpansionMode: 'quality' }, { referenceVideoPaths: ['a.mp4'] }])
    assert.throws(() => qualifyMiniMax({ ...base, ...changes }));
  assert.throws(() => qualifyMiniMax({ ...base, referenceVideoPaths: ['a', 'b'] }, { video: [8, 8], audio: [] }), /totaling/);
  assert.equal(qualifyMiniMax({ ...base, model: 'MiniMax-H3', durationSeconds: 4 }).durationSeconds, 4);
  assert.equal(videoProvider({ model: 'veo-3.1-prod' }), 'veo');
  assert.throws(() => videoProvider({ provider: 'minmax' }), /Unsupported/);
  assert.throws(() => videoProvider({ referenceImagePaths: ['a'] }), /require provider/);
});

test('local preparation validates frames, measures references, hashes bytes and builds V2 content', t => {
  const { root } = fixture(t);
  const { image, video, audio } = media(root);
  const first = prepareMiniMaxRequest({ ...base, firstFramePath: image, promptExpansionMode: 'disabled' });
  const body = JSON.parse(first.serializedBody);
  assert.equal(body.ratio, 'adaptive');
  assert.equal(body.extra.prompt_expansion_mode, 'disabled');
  assert.equal(body.content[1].role, 'first_frame');
  assert.ok(body.content[1].image_url.url.startsWith('data:image/png;base64,'));
  assert.equal(first.sources[0].sha256, hashFile(image));
  assert.equal(prepareMiniMaxRequest({ ...base, lastFramePath: image }).quote.mode, 'image-to-video');
  const refs = prepareMiniMaxRequest({ ...base, referenceImagePaths: [image], referenceVideoPaths: [video], referenceAudioPaths: [audio] });
  assert.equal(refs.quote.estimatedUsd, .766);
  assert.equal(refs.quote.referenceVideoSeconds, 2);
  assert.deepEqual(JSON.parse(refs.serializedBody).content.slice(1).map(c => c.role), ['reference_image', 'reference_video', 'reference_audio']);
  assert.throws(() => prepareMiniMaxRequest({ ...base, aspectRatio: '9:16', firstFramePath: image }), /aspect ratio/);
  const invalid = path.join(root, 'refs/not-an-image.png'); fs.writeFileSync(invalid, 'invalid image');
  assert.throws(() => prepareMiniMaxRequest({ ...base, firstFramePath: invalid }), /ffprobe|dimensions|encoding/);
  fs.copyFileSync(video, invalid);
  assert.throws(() => prepareMiniMaxRequest({ ...base, firstFramePath: invalid }), /encoding/);
});

test('budget, credentials and input validation block POST before money or network is used', async t => {
  const calls = network(t, () => { throw new Error('Unexpected network access'); });
  const { request, budgetFile } = fixture(t, .01);
  await assert.rejects(submitMiniMaxGeneration({ ...base }), /budgetFile/);
  await assert.rejects(submitMiniMaxGeneration(request), /Budget exceeded/);
  process.env.MINIMAX_API_KEY = '';
  await assert.rejects(submitMiniMaxGeneration(request), /Configure MINIMAX_API_KEY/);
  assert.equal(calls.length, 0);
  assert.equal(readLedger(budgetFile).entries.length, 0);
});

test('submission reserves before POST, stores safe provenance and resumes without submitting twice', async t => {
  const { root, request, budgetFile } = fixture(t);
  const { image } = media(root); request.firstFramePath = image;
  const calls = network(t, (url, options) => {
    assert.equal(url, 'https://api.minimax.io/v2/video_generation');
    assert.equal(options.method, 'POST'); assert.equal(options.redirect, 'error');
    assert.equal(options.headers.Authorization, `Bearer ${credential}`);
    assert.ok(options.signal instanceof AbortSignal);
    assert.equal(readLedger(budgetFile).entries[0].reservedMicros, 480000);
    assert.equal(readJson(path.join(root, 'operations/S01-v1.json')).status, 'reserved');
    const snapshot = readJson(path.join(root, 'operations/S01-v1.request.json'));
    assert.equal(snapshot.prompt, base.prompt);
    assert.equal(snapshot.model, 'MiniMax-H3-Max');
    assert.equal(snapshot.parameters.promptExpansionMode, 'balanced');
    assert.equal(snapshot.parameters.ratio, 'adaptive');
    assert.equal(snapshot.sources[0].sha256, hashFile(image));
    assert.equal(JSON.parse(options.body).content[1].role, 'first_frame');
    return json({ task_id: 'fixture-task', ignored_debug: credential });
  });
  assert.equal((await submitMiniMaxGeneration(request)).operationName, 'fixture-task');
  process.env.MINIMAX_API_KEY = '';
  assert.equal((await submitMiniMaxGeneration(request)).operationName, 'fixture-task');
  await assert.rejects(submitMiniMaxGeneration({ ...request, prompt: 'A different lamp' }), /changed content/);
  fs.appendFileSync(image, 'changed-source');
  await assert.rejects(submitMiniMaxGeneration(request), /changed content/);
  assert.equal(calls.length, 1);
  for (const p of [budgetFile, path.join(root, 'operations/S01-v1.json'), path.join(root, 'operations/S01-v1.request.json')]) {
    const text = fs.readFileSync(p, 'utf8');
    assert.ok(!text.includes(credential)); assert.ok(!text.includes('data:image/'));
  }
});

test('timeout, server failure and missing task ID remain uncertain; rejection retains its reservation', async t => {
  let response;
  const calls = network(t, () => response());
  for (const [action, status] of [
    [() => { throw new Error(credential); }, 'uncertain'],
    [() => new Response(credential, { status: 503 }), 'uncertain'],
    [() => new Response(credential, { status: 401 }), 'failed'],
    [() => json({}), 'uncertain'],
    [() => new Response(credential), 'uncertain'],
  ]) {
    response = action;
    const { request, budgetFile } = fixture(t);
    await assert.rejects(submitMiniMaxGeneration(request), e => !e.message.includes(credential));
    assert.equal(readLedger(budgetFile).entries[0].status, status);
    assert.equal(budgetSummary(readLedger(budgetFile)).committedUsd, .48);
    const before = calls.length;
    await assert.rejects(submitMiniMaxGeneration(request), /already reserved/);
    assert.equal(calls.length, before);
  }
});

test('a durable task record repairs a missing ledger task ID without credentials or another POST', async t => {
  const { request, budgetFile } = fixture(t);
  const calls = network(t, () => json({ task_id: 'fixture-task' }));
  await submitMiniMaxGeneration(request);
  updateSpend(budgetFile, request.requestId, { operationName: undefined, status: 'uncertain' });
  process.env.MINIMAX_API_KEY = '';
  await submitMiniMaxGeneration(request);
  assert.equal(calls.length, 1);
  assert.equal(readLedger(budgetFile).entries[0].operationName, 'fixture-task');
});

test('task decoder distinguishes pending, failed, cancelled, empty, mismatched and completed responses', () => {
  for (const status of ['queued', 'running']) assert.equal(interpretMiniMaxTask({ task: task(status) }, 'fixture-task').done, false);
  for (const status of ['failed', 'cancelled']) {
    const result = interpretMiniMaxTask({ task: task(status, { error: { code: '1026', message: credential } }) }, 'fixture-task');
    assert.equal(result.done, true); assert.ok(result.error.includes(status)); assert.ok(!result.error.includes(credential));
  }
  const empty = interpretMiniMaxTask({ task: task('succeeded', { content: {} }) }, 'fixture-task');
  assert.equal(empty.done, true); assert.ok(empty.error);
  for (const value of [null, {}, { task: task('unknown') }, { task: task('succeeded', { id: 'wrong' }) }])
    assert.throws(() => interpretMiniMaxTask(value, 'fixture-task'), /Malformed/);
  const result = interpretMiniMaxTask({ task: task() }, 'fixture-task');
  assert.equal(result.video.uri, outputUrl); assert.equal(result.usage.output_seconds, 6);
});

test('read-only task listing and evidence-based recovery never issue another POST', async t => {
  const { request, budgetFile } = fixture(t);
  let recoveredTask = task();
  const calls = network(t, (url, options) => {
    if (options.method === 'POST') throw new Error('Synthetic lost response');
    if (url.includes('?')) {
      const params = new URL(url).searchParams;
      assert.equal(params.get('page_num'), '2'); assert.equal(params.get('filter.task_type'), 'generation');
      return json({ items: [task()], total: 1 });
    }
    return json({ task: recoveredTask });
  });
  await assert.rejects(submitMiniMaxGeneration(request));
  const snapshotFile = path.join(path.dirname(budgetFile), 'operations/S01-v1.request.json');
  const snapshotBefore = fs.readFileSync(snapshotFile, 'utf8');
  const createdAt = readJson(path.join(path.dirname(budgetFile), 'operations/S01-v1.json')).createdAt;
  assert.equal((await listMiniMaxTasks(2)).tasks[0].operationName, 'fixture-task');
  await assert.rejects(listMiniMaxTasks(0), /page/);
  await assert.rejects(recoverMiniMaxOperation(request, 'fixture-task', ''), /evidence/);
  recoveredTask = task('succeeded', { resolution: '2K' });
  await assert.rejects(recoverMiniMaxOperation(request, 'fixture-task', 'Synthetic provider match'), /parameters differ/);
  recoveredTask = task();
  await recoverMiniMaxOperation(request, 'fixture-task', 'Synthetic provider match');
  assert.equal(fs.readFileSync(snapshotFile, 'utf8'), snapshotBefore);
  assert.equal(readJson(path.join(path.dirname(budgetFile), 'operations/S01-v1.json')).createdAt, createdAt);
  assert.equal(readJson(path.join(path.dirname(budgetFile), 'operations/S01-v1.json')).status, 'submitted');
  assert.equal(readLedger(budgetFile).entries[0].operationName, 'fixture-task');
  assert.equal(calls.filter(c => c.options.method === 'POST').length, 1);
  await assert.rejects(pollMiniMaxOperation('fixture-task', 'MiniMax-H3'), /model differs/);
  await assert.rejects(pollMiniMaxOperation('../escape'), /Invalid/);
});

test('downloads send no key, preserve existing files and reject unsafe CDN redirects', async t => {
  const { root } = fixture(t);
  const output = path.join(root, 'clips/take.mp4');
  let response = () => new Response('synthetic-video');
  const calls = network(t, (url, options) => { assert.equal(options.headers, undefined); return response(); });
  const result = interpretMiniMaxTask({ task: task() }, 'fixture-task');
  await downloadMiniMaxVideo(result, output);
  assert.equal(fs.readFileSync(output, 'utf8'), 'synthetic-video');
  await assert.rejects(downloadMiniMaxVideo(result, output), /overwrite/);
  assert.equal(calls.length, 1);
  const authenticatedUrl = new URL('https://cdn.minimax.io/a');
  authenticatedUrl.username = 'fixture'; authenticatedUrl.password = 'fixture';
  for (const uri of ['http://cdn.minimax.io/a', 'https://minimax.io.evil.example/a', authenticatedUrl.href])
    await assert.rejects(downloadMiniMaxVideo({ ...result, video: { uri } }, path.join(root, 'clips/refused.mp4')), /host/);
  response = () => new Response(null, { status: 302, headers: { Location: 'https://untrusted.example/output.mp4' } });
  await assert.rejects(downloadMiniMaxVideo(result, path.join(root, 'clips/refused.mp4')), /host/);
  response = () => new Response(new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array([1, 2])); controller.error(new Error(credential)); } }));
  await assert.rejects(downloadMiniMaxVideo(result, path.join(root, 'clips/partial.mp4')), e => !e.message.includes(credential));
  assert.deepEqual(fs.readdirSync(path.join(root, 'clips')), ['take.mp4']);
});

test('CLI plans mixed providers offline, submits MiniMax, saves usage/media and reuses the local source', async t => {
  const { root, budgetFile } = fixture(t);
  const { image, video } = media(root);
  fs.writeFileSync(path.join(root, 'film.json'), JSON.stringify({ schemaVersion: 1, title: 'Synthetic MiniMax film',
    width: 512, height: 288, fps: 24, shots: [
      { id: 'S01', beat: 'A lamp turns on', frames: 48, requestId: 'S01-v1', request: { ...base, firstFramePath: 'refs/start.png' } },
      { id: 'S02', beat: 'Existing Veo route', frames: 48, request: { prompt: 'A lamp', aspectRatio: '16:9', generateAudio: false } },
    ] }));
  const calls = network(t, (url, options) => {
    if (options.method === 'POST') return json({ task_id: 'fixture-task' });
    if (url.startsWith('https://api.minimax.io/')) return json({ task: task() });
    assert.equal(url, outputUrl); assert.equal(options.headers, undefined);
    return new Response(fs.readFileSync(video));
  });
  assert.equal((await main(['plan', root])).videoQuoteUsd, 2.08);
  assert.equal(calls.length, 0); assert.equal(readLedger(budgetFile).entries.length, 0);
  const doctor = await main(['doctor']);
  assert.equal(doctor.minimaxCredentialsConfigured, true); assert.ok(!JSON.stringify(doctor).includes(credential));
  await main(['submit', root, 'S01']);
  const anchorHash = hashFile(image);
  const changedPlan = readJson(path.join(root, 'film.json'));
  changedPlan.shots[0].request = { provider: 'runway', promptFile: 'prompts/removed.txt', firstFramePath: 'refs/moved.png' };
  fs.writeFileSync(path.join(root, 'film.json'), JSON.stringify(changedPlan));
  fs.appendFileSync(image, 'edited after submission');
  const result = await main(['poll', root, 'S01']);
  assert.equal(result.status, 'complete');
  assert.equal(result.sha256, hashFile(video));
  assert.equal(readJson(path.join(root, 'operations/S01-v1.json')).sources[0].sha256, anchorHash);
  const catalog = readJson(path.join(root, 'catalog-fixture/catalog/clips', `${result.clipId}.json`));
  const generation = catalog.generations[0];
  assert.equal(generation.source, 'creation-snapshot'); assert.equal(generation.prompt, base.prompt);
  assert.equal(generation.parameters.durationSeconds, 6); assert.equal(generation.provider, 'minimax');
  assert.equal(generation.sources[0].sha256, anchorHash);
  assert.ok(fs.existsSync(path.join(root, 'catalog-fixture/data/clips', result.clipId, 'generations', `${generation.snapshotSha256}.json`)));
  assert.equal(readJson(path.join(root, 'operations/S01-v1.poll.json')).usage.output_seconds, 6);
  assert.equal(readLedger(budgetFile).entries[0].status, 'complete');
  const before = calls.length;
  await main(['poll', root, 'S01']); assert.equal(calls.length, before);
  // A pre-library asset receipt is upgraded locally without a provider call.
  const oldCopy = path.join(root, 'clips/legacy.mp4');
  fs.copyFileSync(path.join(root, 'catalog-fixture', result.path), oldCopy);
  fs.writeFileSync(path.join(root, 'operations/S01-v1.asset.json'), JSON.stringify({ path: 'clips/legacy.mp4', sha256: result.sha256 }));
  assert.equal((await main(['poll', root, 'S01'])).clipId, result.clipId);
  assert.equal(calls.length, before); assert.ok(fs.existsSync(oldCopy));
  assert.match(result.clipId, /^clip_[a-f0-9]{64}$/);
  const master = path.join(root, 'catalog-fixture', result.path);
  fs.chmodSync(master, 0o644); fs.appendFileSync(master, 'changed');
  await assert.rejects(main(['poll', root, 'S01']), /source hash changed/);
});

test('concurrent attempts with the same ID cannot send a second paid submission', async t => {
  const { request, budgetFile } = fixture(t);
  let finish;
  const pending = new Promise(resolve => { finish = resolve; });
  const calls = network(t, () => pending);
  const first = submitMiniMaxGeneration(request);
  await assert.rejects(submitMiniMaxGeneration(request), /already reserved/);
  finish(json({ task_id: 'fixture-task' }));
  await first;
  assert.equal(calls.length, 1);
  assert.equal(readLedger(budgetFile).entries.length, 1);
});

test('CLI terminal failures stop without downloading or releasing the reservation', async t => {
  const { root, budgetFile } = fixture(t);
  fs.writeFileSync(path.join(root, 'film.json'), JSON.stringify({ schemaVersion: 1, title: 'Failure fixture',
    width: 512, height: 288, fps: 24, shots: [{ id: 'S01', beat: 'A lamp', frames: 144, request: base }] }));
  const calls = network(t, (_url, options) => options.method === 'POST' ? json({ task_id: 'fixture-task' })
    : json({ task: task('failed', { error: { message: credential } }) }));
  await main(['submit', root, 'S01']);
  await assert.rejects(main(['poll', root, 'S01', '--wait=300']), /generation failed/);
  assert.equal(calls.length, 2);
  assert.equal(readLedger(budgetFile).entries[0].status, 'failed');
  assert.equal(budgetSummary(readLedger(budgetFile)).committedUsd, .48);
  assert.deepEqual(fs.readdirSync(path.join(root, 'clips')), []);
});
