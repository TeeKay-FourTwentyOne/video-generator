import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { importClip, run, readJson, hashFile, readClip, recordUse, listClips, listUses } from './clip-library.mjs';
import { analyzeClip } from './clip-analysis.mjs';
import { configFor, privateJson, verifyRun, runPath, sha } from './clip-analysis-store.mjs';
import { buildSearch, project, recordReview, readiness, freezeProfile, searchPrivate } from './clip-analysis-views.mjs';
import { buildPlan, sync, hashes } from './clip-cloud.mjs';
import { recoverSet, verifySet, validateBackupSet } from './clip-backup-set.mjs';

async function fixture(t) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'analysis-backup-test-')); t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  const file = path.join(repo, 'fixture.mp4'); run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=128x96:r=8:d=1', '-c:v', 'libx264', file]);
  const clip = importClip(file, {}, repo), config = configFor({ limits: { minFreeBytes: 1048576 } });
  const result = await analyzeClip(clip.id, repo, { config }); assert.equal(result.status, 'complete', JSON.stringify(result));
  const c = { schemaVersion: 1, projectId: 'fixture-project', bucket: 'fixture-private-clips', location: 'US-CENTRAL1', credentialFile: 'data/fixture-key.json',
    monthlyBudgetUsd: 100, headroomUsd: 1, maximumMonthlyDownloadBytes: 1024 ** 3, authorization: { scope: 'Synthetic offline test', at: new Date().toISOString() },
    rates: { checkedAt: new Date().toISOString(), storageUsdPerGiBMonth: 1, classAUsdPerRequest: .001, classBUsdPerRequest: .001, downloadUsdPerGiB: 1 } };
  privateJson(path.join(repo, 'data/clips/cloud/config.json'), c);
  const objects = new Map(), bodies = new Map(), calls = [];
  const client = { checkPrivate: async () => {}, list: async (prefix = '') => [...objects.values()].filter(o => o.name.startsWith(prefix)),
    get: async name => objects.get(name), upload: async o => {
      const r = { name: o.name, size: String(o.bytes), md5Hash: o.md5Hash, metadata: { sha256: o.sha256 }, generation: String(objects.size + 1), storageClass: 'STANDARD' };
      objects.set(o.name, r); bodies.set(o.name, fs.readFileSync(path.join(repo, o.localPath))); return r;
    }, url: suffix => `https://fixture.invalid${suffix}`, request: async url => {
      const u = new URL(url), name = decodeURIComponent(u.pathname.slice(3)); calls.push(name);
      assert.equal(u.searchParams.get('generation'), objects.get(name).generation); return new Response(bodies.get(name));
    } };
  return { repo, c, clip, result, config, client, objects, bodies, calls };
}
test('complete sets restore analysis, previews, source and search into an empty root with pinned generations', async t => {
  const f = await fixture(t), first = await sync(f.repo, { client: f.client });
  assert.ok(first.backupSet.sha256); const setFile = path.join(f.repo, `data/clips/cloud/backup-sets/${first.backupSet.sha256}.json`);
  const set = validateBackupSet(readJson(setFile)); assert.ok(set.objects.some(o => o.kind === 'analysis-manifest'));
  const runDir = runPath(f.clip.id, f.result.runId, f.repo); fs.writeFileSync(path.join(runDir, 'private-unlisted.txt'), 'not an allowed backup artifact');
  assert.ok(!buildPlan(f.repo).objects.some(o => o.localPath?.endsWith('private-unlisted.txt')));
  const empty = path.join(f.repo, 'empty-machine'); fs.mkdirSync(empty); privateJson(path.join(empty, 'data/clips/cloud/config.json'), f.c);
  const recovered = await recoverSet(first.backupSet.sha256, 'data/workspace/recovery', [f.clip.id], empty, { client: f.client, rehearse: true });
  assert.equal(recovered.fullDecode, true); assert.equal(recovered.emptyRootRecovery, true);
  const root = path.join(empty, recovered.output); verifyRun(f.clip.id, f.result.runId, root);
  assert.equal(hashFile(path.join(root, f.clip.path)), f.clip.sha256); assert.ok(readJson(path.join(root, 'data/clips/analysis/search.json')).sources.length > 0);
  await assert.rejects(recoverSet(first.backupSet.sha256, 'data/workspace/recovery', [f.clip.id], empty, { client: f.client }), /new directory/);
  const receipt = await verifySet(first.backupSet.sha256, f.repo, { client: f.client }); assert.equal(receipt.members, set.objects.length);
});
test('absent masters need explicit complete-backup evidence and fresh remote checks; missing objects never become uploads', async t => {
  const f = await fixture(t); await sync(f.repo, { client: f.client });
  fs.rmSync(path.join(f.repo, f.clip.path));
  assert.throws(() => buildPlan(f.repo), /Missing unverified local master/);
  const plan = buildPlan(f.repo, () => {}, { allowAbsent: true }); assert.equal(plan.objects.find(o => o.kind === 'media').absentLocal, true);
  const repeat = await sync(f.repo, { client: f.client, allowAbsent: true }); assert.equal(repeat.uploaded, 0);
  const name = `clips/${f.clip.id}/source.mp4`, original = f.objects.get(name);
  f.objects.set(name, { ...original, generation: '999999' });
  await assert.rejects(sync(f.repo, { client: f.client, allowAbsent: true }), /checksum or identity/);
  f.objects.delete(name); await assert.rejects(sync(f.repo, { client: f.client, allowAbsent: true }), /missing from the verified remote backup/);
});
test('truncated analysis downloads and unsafe declared payloads cannot install a partial recovery', async t => {
  const f = await fixture(t), result = await sync(f.repo, { client: f.client });
  const name = [...f.objects.keys()].find(n => n.endsWith('poster.jpg')); f.bodies.set(name, f.bodies.get(name).subarray(0, 20));
  await assert.rejects(recoverSet(result.backupSet.sha256, 'data/workspace/broken', [f.clip.id], f.repo, { client: f.client }), /checksum verification/);
  assert.equal(fs.existsSync(path.join(f.repo, 'data/workspace/broken')), false);
  const set = readJson(path.join(f.repo, `data/clips/cloud/backup-sets/${result.backupSet.sha256}.json`));
  const artifact = set.objects.find(o => o.kind === 'analysis-artifact'); artifact.artifactPath = '../../config.json';
  assert.throws(() => validateBackupSet(set), /Unsafe/);
});
test('public projection requires exact reviewed text, retains raw private observations and rejects private fields', async t => {
  const f = await fixture(t), dir = runPath(f.clip.id, f.result.runId, f.repo);
  const review = { schemaVersion: 1, clipId: f.clip.id, runId: f.result.runId, manifestSha256: hashFile(path.join(dir, 'manifest.json')),
    reviewedBy: 'human', reviewedAt: new Date().toISOString(), privacyReviewed: true, steps: {}, corrections: [], summary: { description: 'Synthetic test pattern', tags: ['fixture'] } };
  assert.throws(() => project(f.clip.id, f.result.runId, { ...review, privacyReviewed: false }, f.repo), /privacy review/);
  assert.throws(() => project(f.clip.id, f.result.runId, { ...review, summary: { ...review.summary, transcript: 'Unreviewed text' } }, f.repo), /allowlisted/);
  assert.throws(() => project(f.clip.id, f.result.runId, { ...review, summary: { description: '/Users/example/private', tags: [] } }, f.repo), /private/);
  project(f.clip.id, f.result.runId, review, f.repo);
  const record = readClip(f.clip.id, f.repo); assert.equal(record.analysisRefs[0].reviewedDescription, 'Synthetic test pattern');
  assert.equal(record.availability.status, 'local-only'); assert.equal(record.analysis.length, 0);
  await buildSearch(f.repo); assert.ok(searchPrivate('Scene', f.repo).length > 0);
  const backup = await sync(f.repo, { client: f.client });
  assert.ok(readJson(path.join(f.repo, `data/clips/cloud/backup-sets/${backup.backupSet.sha256}.json`)).objects.some(o => o.kind === 'analysis-review'));
});
test('cleanup readiness blocks missing pilot, backup verification, independent access and pending edit dependencies', async t => {
  const f = await fixture(t), result = await sync(f.repo, { client: f.client }); await buildSearch(f.repo);
  recordUse({ clipId: f.clip.id, projectId: 'fixture', editVersion: 'v1', segmentIndex: 0, shotId: 'S1', status: 'planned', evidence: 'saved-frame-edit',
    range: { unit: 'frames', start: 0, length: 4, fps: 8 }, timelineStartFrame: 0, outputSha256: null }, f.repo);
  const policy = { schemaVersion: 1, backupSetSha256: result.backupSet.sha256, profileSha256: 'a'.repeat(64), clips: [{ clipId: f.clip.id, runId: f.result.runId }], retention: { maximumBytes: 100000000 } };
  const report = readiness(policy, f.repo); assert.equal(report.ready, false); assert.deepEqual(report.proposedCleanup, []);
  assert.ok(report.blockers.some(b => b.includes('remote-generation'))); assert.ok(report.rows[0].blockers.includes('Pending edit dependency is unresolved'));
  assert.throws(() => freezeProfile({ schemaVersion: 1, config: f.config, samples: [] }, f.repo), /24-clip/);
  assert.equal(hashFile(path.join(f.repo, f.clip.path)), f.clip.sha256);
});
