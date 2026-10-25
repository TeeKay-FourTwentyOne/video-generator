import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import { gunzipSync } from 'node:zlib';
import { buildPlan, privateJson, assertPrivateBucket, verifyObject, reserve, hashes, Gcs, sync, restore, curlPut, cloudMain } from './clip-cloud.mjs';
import { recordUse } from './clip-library.mjs';

const sha = b => createHash('sha256').update(b).digest('hex');
function fixture(t) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'clip-cloud-test-'));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  // Synthetic bytes exercise storage integrity; these fixtures are never sent to any service.
  const bytes = Buffer.from('synthetic private clip bytes'), id = `clip_${sha(bytes)}`;
  const record = { schemaVersion: 1, id, sha256: sha(bytes), bytes: bytes.length, extension: '.mp4', kind: 'source',
    technical: { durationSeconds: 1, width: 90, height: 160, frameRate: '24/1', frameCount: 24, videoCodec: 'h264', audioCodec: null },
    labels: [], collections: [], legacyIds: [], generations: [], analysis: [], characters: [], tags: [], availability: { status: 'local-only', urls: [], license: null } };
  privateJson(path.join(repo, `catalog/clips/${id}.json`), record);
  const file = path.join(repo, `data/clips/${id}/source.mp4`); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, bytes);
  const c = { schemaVersion: 1, projectId: 'fixture-project', bucket: 'fixture-private-clips', location: 'US-CENTRAL1', credentialFile: 'data/fixture-key.json',
    monthlyBudgetUsd: 100, headroomUsd: 1, maximumMonthlyDownloadBytes: 1024 ** 3, authorization: { scope: 'Synthetic offline test', at: new Date().toISOString() },
    rates: { checkedAt: new Date().toISOString(), storageUsdPerGiBMonth: 1, classAUsdPerRequest: .001, classBUsdPerRequest: .001, downloadUsdPerGiB: 1 } };
  privateJson(path.join(repo, 'data/clips/cloud/config.json'), c);
  return { repo, c, id, bytes, file, record };
}
const remote = o => ({ name: o.name, size: String(o.bytes), md5Hash: o.md5Hash, metadata: { sha256: o.sha256 }, generation: '123', storageClass: 'STANDARD' });
function fakeClient() {
  const objects = new Map(), uploads = [];
  return { objects, uploads, checkPrivate: async () => {}, list: async () => [...objects.values()],
    get: async name => objects.get(name), upload: async o => { uploads.push(o.name); const r = remote(o); objects.set(o.name, r); return r; } };
}

function projectFixture(t) {
  const f = fixture(t);
  f.record.collections = ['film-a']; privateJson(path.join(f.repo, `catalog/clips/${f.id}.json`), f.record);
  function add(label, collections, present = true) {
    const bytes = Buffer.from(label), id = `clip_${sha(bytes)}`;
    const clip = { ...f.record, id, sha256: sha(bytes), bytes: bytes.length, collections };
    privateJson(path.join(f.repo, `catalog/clips/${id}.json`), clip);
    if (present) { const file = path.join(f.repo, `data/clips/${id}/source.mp4`); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, bytes); }
    return clip;
  }
  const unused = add('unused selected take', ['film-a']), shared = add('shared clip selected by use', ['film-b']);
  recordUse({ clipId: shared.id, projectId: 'film-a', editVersion: 'v1', segmentIndex: 0, shotId: 'S01',
    status: 'rendered', evidence: 'saved-frame-edit', range: { unit: 'frames', start: 0, length: 24, fps: 24 },
    timelineStartFrame: 0, outputSha256: 'a'.repeat(64) }, f.repo);
  const unrelated = add('missing unrelated clip', ['film-b'], false);
  return { ...f, unused, shared, unrelated };
}

test('project sync includes unused takes and shared clips used by the project, ignoring unrelated missing media and support', async t => {
  const f = projectFixture(t), client = fakeClient();
  const globalFiles = ['plan.json', 'last-sync.json', 'last-backup-set.json'];
  for (const name of globalFiles) privateJson(path.join(f.repo, 'data/clips/cloud', name), { preserved: name });
  const globalBefore = globalFiles.map(name => fs.readFileSync(path.join(f.repo, 'data/clips/cloud', name)));
  privateJson(path.join(f.repo, 'data/clips/analysis/support.json'), { schemaVersion: 1, files: [
    { path: 'data/workspace/another-film/missing.json', sha256: 'a'.repeat(64), bytes: 1, role: 'dependency-audit' },
  ] });
  assert.throws(() => buildPlan(f.repo), /Missing unverified local master/);
  const plan = buildPlan(f.repo, () => {}, { projectId: 'film-a' });
  assert.deepEqual(plan.scope, { kind: 'project', projectId: 'film-a' });
  assert.deepEqual(new Set(plan.clipRecords.map(c => c.clipId)), new Set([f.id, f.unused.id, f.shared.id]));
  const catalog = plan.objects.find(o => o.kind === 'catalog');
  const decoded = JSON.parse(gunzipSync(fs.readFileSync(path.join(f.repo, catalog.localPath))));
  assert.deepEqual(decoded.scope, plan.scope); assert.equal(decoded.clips.length, 3); assert.equal(decoded.uses.length, 1);
  const first = await sync(f.repo, { client, projectId: 'film-a' });
  assert.equal(first.clips, 3); assert.equal(first.uploaded, 4);
  assert.ok(client.uploads.every(name => !name.includes(f.unrelated.id)));
  assert.equal((await sync(f.repo, { client, projectId: 'film-a' })).uploaded, 0);
  assert.deepEqual(globalFiles.map(name => fs.readFileSync(path.join(f.repo, 'data/clips/cloud', name))), globalBefore);
  const status = await cloudMain(['status', '--project', 'film-a'], f.repo);
  assert.equal(status.lastSync.backupSet.sha256, first.backupSet.sha256); assert.equal(status.initialBackup, null);
  assert.deepEqual(status.scope, plan.scope);
  client.objects.get(`clips/${f.id}/source.mp4`).md5Hash = 'wrong';
  await assert.rejects(sync(f.repo, { client, projectId: 'film-a' }), /checksum or identity/);
});

test('project planning rejects empty or invalid selections, selected corruption, and explicit missing support', async t => {
  const f = projectFixture(t);
  assert.throws(() => buildPlan(f.repo, () => {}, { projectId: 'unknown' }), /No catalog clips/);
  assert.throws(() => buildPlan(f.repo, () => {}, { projectId: '../outside' }), /Invalid project ID/);
  for (const args of [['plan', '--project'], ['plan', '--project='], ['plan', '--project', '--allow-absent'],
    ['sync', '--project', 'film-a', '--project=film-b'], ['status', '--allow-absent'], ['plan', '--unknown']])
    await assert.rejects(cloudMain(args, f.repo), /project ID|cloud option/);
  const report = await cloudMain(['plan', '--project=film-a'], f.repo);
  assert.equal(report.plan, 'data/clips/cloud/projects/film-a/plan.json'); assert.equal(report.network, false);
  const allPlan = { scope: { kind: 'library' } };
  await assert.rejects(sync(f.repo, { projectId: 'film-a', plan: allPlan, client: fakeClient() }), /does not match/);
  fs.appendFileSync(f.file, 'corrupt');
  assert.throws(() => buildPlan(f.repo, () => {}, { projectId: 'film-a' }), /checksum mismatch/);
  fs.writeFileSync(f.file, f.bytes);
  privateJson(path.join(f.repo, 'data/clips/analysis/projects/film-a.support.json'), { schemaVersion: 1, files: [
    { path: 'data/workspace/film-a/missing.json', sha256: 'a'.repeat(64), bytes: 1, role: 'dependency-audit' },
  ] });
  assert.throws(() => buildPlan(f.repo, () => {}, { projectId: 'film-a' }), /ENOENT/);
});

test('project absence uses its own verified set or a whole-library set without hiding missing selected originals', async t => {
  const f = projectFixture(t), client = fakeClient();
  await sync(f.repo, { client, projectId: 'film-a' }); fs.rmSync(f.file);
  assert.throws(() => buildPlan(f.repo, () => {}, { projectId: 'film-a' }), /Missing unverified local master/);
  const repeat = await sync(f.repo, { client, projectId: 'film-a', allowAbsent: true }); assert.equal(repeat.uploaded, 0);
  const remote = client.objects.get(`clips/${f.id}/source.mp4`); remote.generation = 'changed';
  await assert.rejects(sync(f.repo, { client, projectId: 'film-a', allowAbsent: true }), /checksum or identity/);
  const second = fixture(t), globalClient = fakeClient(); second.record.collections = ['film-c'];
  privateJson(path.join(second.repo, `catalog/clips/${second.id}.json`), second.record);
  await sync(second.repo, { client: globalClient }); fs.rmSync(second.file);
  const globalPointer = fs.readFileSync(path.join(second.repo, 'data/clips/cloud/last-backup-set.json'));
  const project = await sync(second.repo, { client: globalClient, projectId: 'film-c', allowAbsent: true });
  assert.deepEqual(project.scope, { kind: 'project', projectId: 'film-c' });
  assert.deepEqual(fs.readFileSync(path.join(second.repo, 'data/clips/cloud/last-backup-set.json')), globalPointer);
  globalClient.objects.delete(`clips/${second.id}/source.mp4`);
  await assert.rejects(sync(second.repo, { client: globalClient, projectId: 'film-c', allowAbsent: true }), /missing from the verified remote backup/);
});

test('inventory includes only immutable masters, snapshots and compressed catalog; detects corruption', t => {
  const { repo, file } = fixture(t);
  fs.writeFileSync(path.join(repo, 'data/credentials.json'), 'synthetic private credential marker');
  const a = buildPlan(repo), b = buildPlan(repo);
  assert.equal(a.clips, 1); assert.equal(a.objects.length, 2);
  assert.deepEqual(a.objects, b.objects);
  assert.ok(a.objects.every(o => !o.localPath.includes('credentials')));
  fs.appendFileSync(file, 'tampered'); assert.throws(() => buildPlan(repo), /checksum mismatch/);
});
test('privacy checks reject public principals, wrong projects, versioning and disabled access prevention', t => {
  const { c } = fixture(t);
  const bucket = { name: c.bucket, location: c.location, storageClass: 'STANDARD', iamConfiguration: { publicAccessPrevention: 'enforced', uniformBucketLevelAccess: { enabled: true } } };
  const policy = { bindings: [{ members: ['serviceAccount:fixture'] }] };
  assertPrivateBucket(c, bucket, policy);
  assert.throws(() => assertPrivateBucket(c, bucket, { bindings: [{ members: ['allUsers'] }] }), /public/);
  assert.throws(() => assertPrivateBucket(c, { ...bucket, versioning: { enabled: true } }, policy), /configuration/);
  assert.throws(() => assertPrivateBucket(c, { ...bucket, iamConfiguration: {} }, policy), /configuration/);
  assert.throws(() => assertPrivateBucket({ ...c, projectNumber: '123' }, { ...bucket, projectNumber: '456' }, policy), /configuration/);
});
test('budget reserves conservatively, persists uncertain spend and rejects over-limit work before mutation', t => {
  const { repo, c } = fixture(t), now = new Date().toISOString();
  const first = reserve(repo, c, { storedBytes: 1024 ** 3, classA: 10, action: 'fixture' }, now);
  assert.ok(first.estimatedReservedUsd > 1);
  assert.throws(() => reserve(repo, c, { downloadBytes: 2 * 1024 ** 3, action: 'too-large' }, now), /allowance/);
  assert.throws(() => reserve(repo, c, { storedBytes: 200 * 1024 ** 3, action: 'too-expensive' }, now), /budget/);
  const second = reserve(repo, c, { action: 'retry' }, now);
  assert.equal(second.estimatedReservedUsd, first.estimatedReservedUsd);
  assert.throws(() => reserve(repo, { ...c, bucket: 'different-bucket' }, { action: 'wrong-destination' }), /another destination/);
  const file = path.join(repo, 'data/clips/cloud/ledger.json'), ledger = JSON.parse(fs.readFileSync(file));
  ledger.months[now.slice(0, 7)].reservedOperationsUsd = 'invalid'; privateJson(file, ledger);
  assert.throws(() => reserve(repo, c, { action: 'corrupt-ledger' }, now), /Invalid monthly/);
});
test('incremental sync skips verified bytes and refuses a conflicting remote object without overwriting', async t => {
  const { repo } = fixture(t), client = fakeClient();
  const first = await sync(repo, { client }); assert.equal(first.uploaded, 2);
  const next = await sync(repo, { client }); assert.equal(next.uploaded, 0); assert.equal(next.skipped, 2);
  client.objects.values().next().value.md5Hash = 'incorrect';
  await assert.rejects(sync(repo, { client }), /checksum or identity/); assert.equal(client.uploads.length, 3, 'two members plus their immutable complete backup manifest');
});
test('upload resumes the retained session after an ambiguous interrupted chunk with create-only preconditions', async t => {
  const { repo, c, file } = fixture(t), o = { name: 'clips/fixture/source.mp4', localPath: path.relative(repo, file), ...hashes(file) };
  const calls = []; let writes = 0;
  const fetcher = async (url, options) => {
    calls.push({ url, options });
    if (options.method === 'POST') {
      assert.equal(new URL(url).searchParams.get('ifGenerationMatch'), '0');
      assert.equal(JSON.parse(options.body).md5Hash, o.md5Hash);
      return new Response(null, { status: 200, headers: { location: `https://storage.googleapis.com/upload/storage/v1/b/${c.bucket}/o?upload_id=fixture` } });
    }
    if (options.headers['Content-Length'] === '0') return new Response(null, { status: 308, headers: { range: 'bytes=0-2' } });
    if (++writes === 1) throw new Error('Synthetic dropped response after partial acceptance');
    assert.equal(options.headers['Content-Range'], `bytes 3-${o.bytes - 1}/${o.bytes}`);
    assert.deepEqual(options.body, fs.readFileSync(file).subarray(3));
    return Response.json(remote(o));
  };
  const client = new Gcs(c, repo, fetcher, async () => ({ projectId: c.projectId, accessToken: 'fixture', expiresIn: 3600 }));
  verifyObject(o, await client.upload(o));
  assert.equal(calls.filter(x => x.options.method === 'POST').length, 1);
  assert.equal(fs.readdirSync(path.join(repo, 'data/clips/cloud/sessions')).length, 0);
});
test('credentials never follow an untrusted session URL or redirects', async t => {
  const { repo, c } = fixture(t); let called = false;
  const client = new Gcs(c, repo, async () => { called = true; }, async () => { called = true; });
  await assert.rejects(client.request('https://example.invalid/'), /outside/);
  assert.throws(() => client.sessionUri(`https://storage.googleapis.com/upload/storage/v1/b/another-bucket/o?upload_id=fixture`), /endpoint/);
  assert.equal(called, false);
});
test('native transport keeps session capabilities out of process arguments and cleans temporary records', async t => {
  const { repo } = fixture(t), uri = 'https://storage.googleapis.com/upload/storage/v1/b/fixture-private-clips/o?upload_id=fixture-capability';
  const body = Buffer.from('fixture bytes');
  const response = await curlPut(uri, { headers: { 'Content-Length': String(body.length), 'Content-Range': 'bytes 0-12/26' }, body }, repo, (binary, args) => {
    assert.equal(binary, 'curl'); assert.ok(!args.some(x => x.includes('fixture-capability'))); assert.ok(!args.includes('--location'));
    const file = args[args.indexOf('--config') + 1]; assert.equal(fs.statSync(file).mode & 0o777, 0o600);
    assert.ok(fs.readFileSync(file, 'utf8').includes(uri));
    const child = new EventEmitter(); child.stdin = new PassThrough(); child.stdout = new PassThrough(); child.stderr = new PassThrough();
    const chunks = []; child.stdin.on('data', chunk => chunks.push(chunk));
    child.stdin.on('finish', () => queueMicrotask(() => {
      assert.deepEqual(Buffer.concat(chunks), body);
      fs.writeFileSync(args[args.indexOf('--dump-header') + 1], 'HTTP/1.1 100 Continue\r\n\r\nHTTP/2 308\r\nrange: bytes=0-12\r\n\r\n');
      fs.writeFileSync(args[args.indexOf('--output') + 1], ''); child.stdout.end('308'); child.stderr.end(); child.emit('close', 0);
    }));
    return child;
  });
  assert.equal(response.status, 308); assert.equal(response.headers.get('range'), 'bytes=0-12');
  assert.equal(fs.readdirSync(path.join(repo, 'data/clips/cloud/requests')).length, 0);
});
test('restore verifies downloaded bytes, installs without replacement and rejects corrupt payloads', async t => {
  const { repo, c, id, bytes } = fixture(t), o = buildPlan(repo).objects[0], client = fakeClient();
  client.objects.set(o.name, remote(o)); client.url = suffix => suffix;
  client.request = async () => new Response(bytes);
  const output = 'data/workspace/fixture/restore/source.mp4';
  const receipt = await restore(id, output, repo, { client });
  assert.equal(receipt.sha256, sha(bytes)); assert.deepEqual(fs.readFileSync(path.join(repo, output)), bytes);
  await assert.rejects(restore(id, output, repo, { client }), /already exists/);
  client.request = async () => new Response(Buffer.alloc(bytes.length));
  await assert.rejects(restore(id, 'data/workspace/fixture/bad.mp4', repo, { client }), /checksum verification/);
  assert.equal(fs.existsSync(path.join(repo, 'data/workspace/fixture/bad.mp4')), false);
  assert.equal(fs.readdirSync(path.join(repo, 'data/workspace/fixture')).some(n => n.endsWith('.part')), false);
  await assert.rejects(restore(id, '../outside.mp4', repo, { client }), /escapes/);
});
