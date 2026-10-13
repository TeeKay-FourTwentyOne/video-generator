import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createLedger, readLedger, updateSpend } from '../../mcp/video-generator/dist/production/ledger.js';
import { saveGenerationSnapshot, readGenerationSnapshot, snapshotHash, writeSnapshot } from './generation-snapshot.mjs';
import { importClip, readClip, hashFile, readJson, run, verifyClipSnapshots } from './clip-library.mjs';
import { main as clipsMain } from './clips.mjs';

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'generation-snapshot-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const budgetFile = path.join(root, 'data/workspace/fixture/budget.json');
  createLedger(budgetFile, 10, 'Synthetic offline allocation');
  return { root, budgetFile, workspace: path.dirname(budgetFile) };
}
const request = { provider: 'fixture', requestId: 'S01-v1', fingerprint: 'a'.repeat(64),
  prompt: '  A lamp turns on.\n', requestedModel: 'fixture-alias', model: 'fixture-model-v1', seed: 0,
  parameters: { durationSeconds: 8, aspectRatio: '16:9', resolution: '720p', generateAudio: false },
  sources: [{ role: 'first_frame', sha256: 'b'.repeat(64), bytes: 10 }] };
function video(root) {
  const file = path.join(root, 'fixture.mp4');
  run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=90x160:r=24', '-t', '1',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file]);
  return file;
}

test('creation snapshots preserve exact text, refuse replacement and validate request identity', t => {
  const { budgetFile, workspace } = fixture(t);
  const snapshot = saveGenerationSnapshot(budgetFile, request);
  const file = path.join(workspace, 'operations/S01-v1.request.json');
  assert.equal(snapshot.prompt, request.prompt); assert.equal(snapshot.seed, 0);
  assert.equal(fs.statSync(file).mode & 0o777, 0o400);
  writeSnapshot(file, snapshot);
  assert.throws(() => writeSnapshot(file, { ...snapshot, prompt: 'Changed' }), /conflicts/);
  assert.throws(() => readGenerationSnapshot(budgetFile, request.requestId, { provider: 'other' }), /does not match/);
  assert.throws(() => readGenerationSnapshot(budgetFile, request.requestId, { snapshotSha256: '0'.repeat(64) }), /does not match/);
  assert.equal(readGenerationSnapshot(budgetFile, 'legacy-attempt'), undefined);
  fs.chmodSync(file, 0o600); fs.writeFileSync(file, '{ malformed private prompt fragment');
  assert.throws(() => readGenerationSnapshot(budgetFile, request.requestId), e =>
    /unreadable/.test(e.message) && !e.message.includes('private prompt fragment'));
});

test('private snapshots follow deduplicated masters, withhold sensitive text and survive workspace removal', async t => {
  const { root, budgetFile, workspace } = fixture(t), source = video(root);
  const privatePrompt = 'Use ' + ['gs:', '', 'fixture-private-bucket', 'reference'].join('/');
  const snapshot = saveGenerationSnapshot(budgetFile, { ...request, prompt: privatePrompt });
  const file = path.join(workspace, 'operations/S01-v1.request.json');
  const clip = await clipsMain(['import', source, `--snapshot=${file}`], root);
  importClip(source, { generationSnapshot: snapshot }, root);
  const generation = readClip(clip.id, root).generations[0];
  assert.equal(readClip(clip.id, root).generations.length, 1);
  assert.equal(generation.promptStatus, 'withheld'); assert.equal(generation.promptId, null);
  assert.equal(generation.model, request.model); assert.equal(generation.requestedModel, request.requestedModel);
  assert.equal(generation.sources[0].sha256, request.sources[0].sha256);
  assert.ok(!JSON.stringify(clip).includes(privatePrompt));
  const retained = path.join(root, 'data/clips', clip.id, 'generations', `${generation.snapshotSha256}.json`);
  assert.equal(readJson(retained).prompt, privatePrompt);
  fs.rmSync(workspace, { recursive: true });
  verifyClipSnapshots(readClip(clip.id, root), root);
  assert.equal((await clipsMain(['validate', '--media'], root)).valid, true);
  // Distinct creation attempts can return identical media without losing either provenance record.
  importClip(source, { generationSnapshot: { ...snapshot, requestId: 'S01-v2' } }, root);
  assert.equal(readClip(clip.id, root).generations.length, 2);
  fs.chmodSync(retained, 0o600);
  fs.writeFileSync(retained, JSON.stringify({ ...snapshot, prompt: 'Tampered' }));
  assert.throws(() => verifyClipSnapshots(readClip(clip.id, root), root), /differs/);
});

// Isolate the built Google clients from real config/auth while exercising their actual submission code.
async function googleFixture(t) {
  const f = fixture(t);
  fs.writeFileSync(path.join(f.root, 'package.json'), JSON.stringify({ type: 'module' }));
  for (const relative of ['mcp/video-generator/dist/clients/veo.js', 'mcp/video-generator/dist/clients/gcs.js',
    'mcp/video-generator/dist/production/ledger.js', 'mcp/video-generator/dist/production/veo-spec.js',
    'mcp/video-generator/dist/utils/paths.js', 'mcp/video-generator/dist/utils/config.js',
    'tools/production/clip-library.mjs', 'tools/production/generation-snapshot.mjs', 'tools/production/google-image.mjs',
    'tools/privacy-check.mjs', 'docs/schemas/clip.schema.json']) {
    const target = path.join(f.root, relative); fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(relative, target);
  }
  fs.writeFileSync(path.join(f.root, 'tools/production/film.mjs'),
    `export { localPath, hashFile } from ${JSON.stringify(new URL('./film.mjs', import.meta.url).href)};`);
  const authFile = path.join(f.root, 'mcp/video-generator/dist/clients/google-auth.js');
  fs.writeFileSync(authFile, `let callback = () => {};
    export function onAuth(fn) { callback = fn; }
    export async function getGoogleAccessToken() { await callback(); return { accessToken: 'fixture', projectId: 'fixture' }; }
    export function buildVertexUrl(_project, model, method) { return 'https://example.invalid/' + model + ':' + method; }`);
  const auth = await import(pathToFileURL(authFile).href);
  const veo = await import(pathToFileURL(path.join(f.root, 'mcp/video-generator/dist/clients/veo.js')).href);
  const image = await import(pathToFileURL(path.join(f.root, 'tools/production/google-image.mjs')).href);
  return { ...f, auth, veo, image };
}

test('Veo snapshots before auth, sends the captured reference bytes and retains defaults through legacy retrieval', async t => {
  const { root, workspace, budgetFile, auth, veo } = await googleFixture(t);
  const anchor = path.join(workspace, 'anchor.png'); fs.writeFileSync(anchor, 'original image bytes');
  const anchorHash = hashFile(anchor), output = video(root);
  const options = { budgetFile, requestId: 'S01-v1', prompt: '  A lamp.\n', firstFramePath: anchor };
  const file = path.join(workspace, 'operations/S01-v1.request.json');
  auth.onAuth(() => {
    assert.equal(readJson(file).prompt, options.prompt);
    fs.writeFileSync(anchor, 'modified while authenticating');
  });
  let posts = 0;
  t.mock.method(globalThis, 'fetch', async (_url, init) => {
    posts++;
    const body = JSON.parse(init.body), snapshot = readJson(file);
    assert.equal(Buffer.from(body.instances[0].image.bytesBase64Encoded, 'base64').toString(), 'original image bytes');
    assert.equal(snapshot.sources[0].sha256, anchorHash);
    assert.equal(snapshot.model, 'veo-3.1-generate-001'); assert.equal(snapshot.requestedModel, null);
    assert.equal(snapshot.seed, body.parameters.seed);
    assert.equal(snapshot.parameters.resolution, '1080p'); assert.equal(snapshot.parameters.generateAudio, true);
    return new Response(JSON.stringify({ name: 'fixture-operation' }));
  });
  const submitted = await veo.submitVeoGeneration(options);
  assert.equal(posts, 1); const original = fs.readFileSync(file, 'utf8');
  const result = await veo.downloadVeoVideo({ done: true, operationName: submitted.operationName,
    video: { bytesBase64Encoded: fs.readFileSync(output).toString('base64') } },
  { request: { ...options, prompt: 'Changed after generation' }, catalogRoot: root });
  const generation = readClip(result.clipId, root).generations[0];
  assert.equal(generation.prompt, 'A lamp.'); assert.equal(generation.parameters.durationSeconds, 8);
  assert.equal(generation.sources[0].sha256, anchorHash);
  assert.equal(fs.readFileSync(file, 'utf8'), original);
  // Repair a lost ledger update from the journal without regenerating or rewriting creation time.
  fs.writeFileSync(anchor, 'original image bytes');
  updateSpend(budgetFile, options.requestId, { operationName: undefined, status: 'uncertain' });
  await veo.submitVeoGeneration(options);
  assert.equal(readLedger(budgetFile).entries[0].operationName, submitted.operationName);
  assert.equal(fs.readFileSync(file, 'utf8'), original); assert.equal(posts, 1);
});

test('Veo auth failure retains its snapshot and reservation without permitting another submission', async t => {
  const { workspace, budgetFile, auth, veo } = await googleFixture(t);
  const file = path.join(workspace, 'operations/S01-v1.request.json');
  auth.onAuth(() => { assert.ok(fs.existsSync(file)); throw new Error('Synthetic auth failure'); });
  let calls = 0;
  t.mock.method(globalThis, 'fetch', async () => { calls++; throw new Error('Unexpected network'); });
  const options = { budgetFile, requestId: 'S01-v1', prompt: 'A lamp.' };
  await assert.rejects(veo.submitVeoGeneration(options), /Synthetic auth failure/);
  const original = fs.readFileSync(file, 'utf8');
  await assert.rejects(veo.submitVeoGeneration(options), /without a known operation/);
  assert.equal(readLedger(budgetFile).entries[0].status, 'uncertain');
  assert.equal(fs.readFileSync(file, 'utf8'), original); assert.equal(calls, 0);
});

test('snapshot persistence failure prevents Veo network access', async t => {
  const { workspace, budgetFile, auth, veo } = await googleFixture(t);
  fs.mkdirSync(path.join(workspace, 'operations/S01-v1.request.json'), { recursive: true });
  let calls = 0; auth.onAuth(() => { calls++; });
  t.mock.method(globalThis, 'fetch', async () => { calls++; throw new Error('Unexpected network'); });
  await assert.rejects(veo.submitVeoGeneration({ budgetFile, requestId: 'S01-v1', prompt: 'A lamp.' }));
  assert.equal(calls, 0);
});

test('image anchors capture prompt, reference bytes, model and generation settings before auth', async t => {
  const { workspace, auth, image } = await googleFixture(t);
  fs.writeFileSync(path.join(workspace, 'prompt.txt'), '  A still lamp.\n');
  fs.writeFileSync(path.join(workspace, 'reference.png'), 'image reference');
  const refHash = hashFile(path.join(workspace, 'reference.png'));
  const file = path.join(workspace, 'operations/I01.request.json');
  auth.onAuth(() => {
    assert.equal(readJson(file).prompt, '  A still lamp.\n');
    fs.writeFileSync(path.join(workspace, 'prompt.txt'), 'Changed');
    fs.writeFileSync(path.join(workspace, 'reference.png'), 'Changed');
  });
  t.mock.method(globalThis, 'fetch', async (_url, init) => {
    const body = JSON.parse(init.body), snapshot = readJson(file);
    assert.equal(body.contents[0].parts[1].text, snapshot.prompt);
    assert.equal(snapshot.sources[0].sha256, refHash);
    assert.equal(snapshot.model, 'gemini-3-pro-image');
    assert.equal(snapshot.parameters.imageConfig.imageSize, '2K');
    return new Response(JSON.stringify({ modelVersion: 'fixture-reported-version', usageMetadata: {},
      candidates: [{ content: { parts: [{ inlineData: { mimeType: 'image/png', data: Buffer.from('fixture result').toString('base64') } }] } }] }));
  });
  const result = await image.generateAnchor(workspace, { id: 'I01', promptFile: 'prompt.txt', refs: ['reference.png'],
    aspectRatio: '16:9', output: 'anchor.png' });
  const receipt = readJson(path.join(workspace, 'operations/I01.asset.json'));
  assert.equal(receipt.sha256, result.sha256); assert.equal(receipt.snapshotSha256, snapshotHash(readJson(file)));
  assert.equal(readJson(path.join(workspace, 'operations/I01.usage.json')).modelVersion, 'fixture-reported-version');
});
