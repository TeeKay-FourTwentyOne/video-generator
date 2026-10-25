import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { privateJson, Gcs } from './clip-cloud.mjs';
import { fetchClip, catalogs, recoverCatalog, download } from './clip-cloud-restore.mjs';
import { generationMetadata, resolveClip, verifyClipSnapshots } from './clip-library.mjs';
import { snapshotHash } from './generation-snapshot.mjs';

const sha = value => createHash('sha256').update(value).digest('hex');
function fixture(t) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'clip-recovery-test-'));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  const bytes = Buffer.from('Synthetic offline media'), id = `clip_${sha(bytes)}`;
  const snapshot = { schemaVersion: 1, evidence: 'creation-snapshot', provider: 'fixture', requestId: 'S01-v1', fingerprint: 'a'.repeat(64),
    createdAt: '2026-01-01T00:00:00.000Z', prompt: 'A synthetic test scene', model: 'fixture-model', requestedModel: null,
    seed: null, parameters: {}, sources: [], api: null };
  const snapshotBytes = Buffer.from(JSON.stringify(snapshot, null, 2) + '\n'), hash = snapshotHash(snapshot);
  const clip = { schemaVersion: 1, id, sha256: sha(bytes), bytes: bytes.length, extension: '.mp4', kind: 'source',
    technical: { durationSeconds: 1, width: 160, height: 90, frameRate: '24/1', frameCount: 24, videoCodec: 'h264', audioCodec: null },
    labels: [], collections: [], legacyIds: [], generations: [{ ...generationMetadata(snapshot, 'creation-snapshot'), snapshotSha256: hash }],
    analysis: [], characters: [], tags: [], availability: { status: 'local-only', urls: [], license: null } };
  const config = { schemaVersion: 1, projectId: 'fixture-project', bucket: 'fixture-private-clips', location: 'US-CENTRAL1', credentialFile: 'data/fixture-key.json',
    monthlyBudgetUsd: 100, headroomUsd: 1, maximumMonthlyDownloadBytes: 1024 ** 3, authorization: { scope: 'Synthetic offline test', at: new Date().toISOString() },
    rates: { checkedAt: new Date().toISOString(), storageUsdPerGiBMonth: 1, classAUsdPerRequest: .001, classBUsdPerRequest: .001, downloadUsdPerGiB: 1 } };
  privateJson(path.join(repo, 'data/clips/cloud/config.json'), config);
  privateJson(path.join(repo, `catalog/clips/${id}.json`), clip);
  const objects = new Map(), bodies = new Map(), requests = [];
  function add(name, data) {
    const remote = { name, size: String(data.length), md5Hash: createHash('md5').update(data).digest('base64'),
      metadata: { sha256: sha(data) }, generation: '123', storageClass: 'STANDARD', timeCreated: '2026-01-01T00:00:00.000Z' };
    objects.set(name, remote); bodies.set(name, data); return remote;
  }
  const source = add(`clips/${id}/source.mp4`, bytes), generation = add(`generations/${id}/${sha(snapshotBytes)}.json`, snapshotBytes);
  const client = { checkPrivate: async () => {}, list: async prefix => [...objects.values()].filter(o => o.name.startsWith(prefix)),
    get: async name => objects.get(name), url: suffix => `https://fixture.invalid${suffix}`,
    request: async url => {
      const parsed = new URL(url); assert.equal(parsed.searchParams.get('generation'), '123');
      const name = decodeURIComponent(parsed.pathname.slice(3)); requests.push(name); return new Response(bodies.get(name));
    } };
  return { repo, id, bytes, clip, snapshot, snapshotBytes, hash, client, objects, bodies, requests, add, source, generation };
}

test('fetch restores into an empty media library with exact private evidence and no old receipts', async t => {
  const f = fixture(t), result = await fetchClip(f.id, f.repo, { client: f.client });
  assert.equal(result.sourceAlreadyPresent, false); assert.equal(result.snapshots, 1);
  assert.deepEqual(fs.readFileSync(resolveClip(f.id, f.repo)), f.bytes); verifyClipSnapshots(f.clip, f.repo);
  assert.deepEqual(fs.readFileSync(path.join(f.repo, `data/clips/${f.id}/generations/${f.hash}.json`)), f.snapshotBytes);
  assert.equal(fs.statSync(resolveClip(f.id, f.repo)).mode & 0o777, 0o444);
  const repeat = await fetchClip(f.id, f.repo, { client: f.client }); assert.equal(repeat.sourceAlreadyPresent, true);
  assert.equal(f.requests.filter(n => n === f.source.name).length, 1);
});
test('large streamed restores get a bounded transfer deadline beyond the metadata timeout', async t => {
  const f = fixture(t), c = JSON.parse(fs.readFileSync(path.join(f.repo, 'data/clips/cloud/config.json'))), deadlines = [];
  t.mock.method(AbortSignal, 'timeout', milliseconds => { deadlines.push(milliseconds); return new AbortController().signal; });
  const client = new Gcs(c, f.repo, async (url, options) => {
    assert.equal(options.timeoutMs, undefined, 'Internal transfer controls are not passed to fetch');
    return new Response(null, { status: 503 });
  }, async () => ({ projectId: c.projectId, accessToken: 'fixture', expiresIn: 3600 }));
  await client.request(client.url());
  await assert.rejects(download(client, { ...f.source, size: String(2 * 1024 ** 3) }, path.join(f.repo, 'large-restore')), /HTTP 503/);
  assert.equal(deadlines[0], 120000); assert.ok(deadlines[1] > deadlines[0] && deadlines[1] <= 3600000);
  await assert.rejects(client.request(client.url(), { timeoutMs: Infinity }), /Invalid cloud request timeout/);
  assert.equal(fs.existsSync(path.join(f.repo, 'large-restore')), false);
});
test('missing or mismatched snapshot evidence blocks installation of the media', async t => {
  const f = fixture(t); f.objects.delete(f.generation.name);
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /snapshot is missing/);
  assert.throws(() => resolveClip(f.id, f.repo), /unavailable/);
  f.objects.set(f.generation.name, f.generation);
  f.clip.generations[0].model = 'changed-model'; privateJson(path.join(f.repo, `catalog/clips/${f.id}.json`), f.clip);
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /differs from catalog evidence/);
  assert.throws(() => resolveClip(f.id, f.repo), /unavailable/);
});
test('corrupt or oversized downloads are rejected with no partial master or staging files', async t => {
  const f = fixture(t); f.bodies.set(f.source.name, Buffer.alloc(f.bytes.length));
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /checksum verification/);
  assert.throws(() => resolveClip(f.id, f.repo), /unavailable/);
  assert.equal(fs.existsSync(path.join(f.repo, `data/clips/${f.id}/generations`)), false);
  f.bodies.set(f.source.name, Buffer.alloc(f.bytes.length + 1));
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /reserved byte count/);
  assert.deepEqual(fs.readdirSync(path.join(f.repo, 'data/clips/cloud/restore-staging')), []);
});
test('conflicting local master or snapshot is preserved and fails before installing new evidence', async t => {
  const f = fixture(t), file = path.join(f.repo, `data/clips/${f.id}/source.mp4`);
  fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, 'existing local content');
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /conflicts/);
  assert.equal(fs.readFileSync(file, 'utf8'), 'existing local content'); assert.equal(f.requests.length, 0);
  fs.rmSync(file); const snapshot = path.join(path.dirname(file), `generations/${f.hash}.json`);
  fs.mkdirSync(path.dirname(snapshot)); fs.writeFileSync(snapshot, 'existing private evidence');
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /conflicts/);
  assert.equal(fs.readFileSync(snapshot, 'utf8'), 'existing private evidence'); assert.equal(fs.existsSync(file), false);
});
test('privacy failure and exhausted download allowance stop before downloading', async t => {
  const f = fixture(t); const check = f.client.checkPrivate;
  f.client.checkPrivate = async () => { throw new Error('Private access could not be verified'); };
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /Private access/); assert.equal(f.requests.length, 0);
  f.client.checkPrivate = check;
  const configPath = path.join(f.repo, 'data/clips/cloud/config.json'), c = JSON.parse(fs.readFileSync(configPath));
  c.maximumMonthlyDownloadBytes = 1; privateJson(configPath, c);
  await assert.rejects(fetchClip(f.id, f.repo, { client: f.client }), /allowance/); assert.equal(f.requests.length, 0);
});
test('catalog recovery works without any local catalog and stages validated clip and use records', async t => {
  const f = fixture(t), bytes = gzipSync(JSON.stringify({ schemaVersion: 1, clips: [f.clip], uses: [] }));
  f.add(`catalog/${sha(bytes)}.json.gz`, bytes);
  fs.rmSync(path.join(f.repo, 'catalog'), { recursive: true });
  const choices = await catalogs(f.repo, { client: f.client }); assert.equal(choices.length, 1); assert.equal(choices[0].sha256, sha(bytes));
  const output = 'data/workspace/recovered';
  const result = await recoverCatalog(sha(bytes), output, f.repo, { client: f.client });
  assert.equal(result.clips, 1); assert.equal(result.uses, 0);
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(f.repo, output, `catalog/clips/${f.id}.json`))), f.clip);
  assert.equal(fs.existsSync(path.join(f.repo, 'catalog')), false);
  await assert.rejects(recoverCatalog(sha(bytes), output, f.repo, { client: f.client }), /new directory/);
  await assert.rejects(recoverCatalog(sha(bytes), '../escape', f.repo, { client: f.client }), /escapes/);
});
test('catalog recovery refuses malformed schemas, duplicate IDs and unresolved uses', async t => {
  const f = fixture(t);
  for (const catalog of [
    { schemaVersion: 1, scope: { kind: 'project', projectId: '../escape' }, clips: [f.clip], uses: [] },
    { schemaVersion: 1, clips: [{ ...f.clip, id: '../escape' }], uses: [] },
    { schemaVersion: 1, clips: [f.clip, f.clip], uses: [] },
    { schemaVersion: 1, clips: [], uses: [{ clipId: f.id, id: 'unknown' }] },
  ]) {
    const bytes = gzipSync(JSON.stringify(catalog)); f.add(`catalog/${sha(bytes)}.json.gz`, bytes);
    await assert.rejects(recoverCatalog(sha(bytes), 'data/workspace/invalid', f.repo, { client: f.client }));
    assert.equal(fs.existsSync(path.join(f.repo, 'data/workspace/invalid')), false);
  }
});
test('catalog recovery identifies a project subset in its receipt', async t => {
  const f = fixture(t), scope = { kind: 'project', projectId: 'film-a' };
  const bytes = gzipSync(JSON.stringify({ schemaVersion: 1, scope, clips: [f.clip], uses: [] }));
  f.add(`catalog/${sha(bytes)}.json.gz`, bytes);
  const result = await recoverCatalog(sha(bytes), 'data/workspace/project-catalog', f.repo, { client: f.client });
  assert.deepEqual(result.scope, scope);
});
