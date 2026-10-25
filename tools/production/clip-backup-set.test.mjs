import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { importClip, run, readJson, hashFile, readClip, recordUse, listClips, listUses, updateClip } from './clip-library.mjs';
import { analyzeClip } from './clip-analysis.mjs';
import { configFor, privateJson, verifyRun, runPath, sha } from './clip-analysis-store.mjs';
import { buildSearch, project, recordReview, readiness, freezeProfile, searchPrivate } from './clip-analysis-views.mjs';
import { buildPlan, sync, hashes } from './clip-cloud.mjs';
import { recoverSet, verifySet, validateBackupSet, objectTarget } from './clip-backup-set.mjs';
import { planDuplicates, applyDuplicates } from './clip-cleanup.mjs';
import { verifySupportClosure } from './clip-backup-support.mjs';

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
  assert.equal(set.objects.filter(o => o.kind === 'analysis-inventory').length, 1);
  const runDir = runPath(f.clip.id, f.result.runId, f.repo); fs.writeFileSync(path.join(runDir, 'private-unlisted.txt'), 'not an allowed backup artifact');
  assert.ok(!buildPlan(f.repo).objects.some(o => o.localPath?.endsWith('private-unlisted.txt')));
  const empty = path.join(f.repo, 'empty-machine'); fs.mkdirSync(empty); privateJson(path.join(empty, 'data/clips/cloud/config.json'), f.c);
  const recovered = await recoverSet(first.backupSet.sha256, 'data/workspace/recovery', [f.clip.id], empty, { client: f.client, rehearse: true });
  assert.equal(recovered.fullDecode, true); assert.equal(recovered.emptyRootRecovery, true);
  assert.equal(recovered.backupSetSha256, first.backupSet.sha256);
  assert.equal(recovered.support.transitiveEvidenceVerified, true);
  const root = path.join(empty, recovered.output); verifyRun(f.clip.id, f.result.runId, root);
  assert.equal(hashFile(path.join(root, f.clip.path)), f.clip.sha256); assert.ok(readJson(path.join(root, 'data/clips/analysis/search.json')).sources.length > 0);
  await assert.rejects(recoverSet(first.backupSet.sha256, 'data/workspace/recovery', [f.clip.id], empty, { client: f.client }), /new directory/);
  const receipt = await verifySet(first.backupSet.sha256, f.repo, { client: f.client }); assert.equal(receipt.members, set.objects.length);
});
test('a project set restores its complete source and analysis without the unrelated library or global support', async t => {
  const f = await fixture(t); updateClip(f.clip.id, { collections: ['film-a'] }, f.repo);
  // The selected run is immutable even if public collection metadata was added afterward.
  privateJson(path.join(f.repo, 'data/clips/analysis/support.json'), { schemaVersion: 1, files: [
    { path: 'data/workspace/unrelated/absent.json', sha256: 'a'.repeat(64), bytes: 1, role: 'dependency-audit' },
  ] });
  const evidencePath = 'data/workspace/film-a/evidence.json'; privateJson(path.join(f.repo, evidencePath), { case: 'project fixture' });
  privateJson(path.join(f.repo, 'data/clips/analysis/projects/film-a.support.json'), { schemaVersion: 1,
    files: [{ path: evidencePath, ...hashes(path.join(f.repo, evidencePath)), role: 'dependency-audit' }] });
  const synced = await sync(f.repo, { client: f.client, projectId: 'film-a' });
  assert.equal(fs.existsSync(path.join(f.repo, 'data/clips/cloud/last-backup-set.json')), false);
  const set = validateBackupSet(readJson(path.join(f.repo, `data/clips/cloud/backup-sets/${synced.backupSet.sha256}.json`)));
  assert.deepEqual(set.scope, { kind: 'project', projectId: 'film-a' });
  assert.ok(set.objects.some(o => o.kind === 'analysis-inventory'));
  assert.throws(() => validateBackupSet({ ...set, scope: { kind: 'project', projectId: '../escape' } }), /Invalid project ID/);
  assert.throws(() => validateBackupSet({ ...set, scope: { kind: 'library', projectId: 'film-a' } }), /Invalid backup scope/);
  const empty = path.join(f.repo, 'project-recovery-machine'); fs.mkdirSync(empty);
  privateJson(path.join(empty, 'data/clips/cloud/config.json'), f.c);
  const recovered = await recoverSet(synced.backupSet.sha256, 'data/workspace/recovered', [f.clip.id], empty, { client: f.client, rehearse: true });
  assert.deepEqual(recovered.scope, set.scope); assert.equal(recovered.fullDecode, true);
  assert.equal(hashFile(path.join(empty, recovered.output, evidencePath)), hashFile(path.join(f.repo, evidencePath)));
  verifyRun(f.clip.id, f.result.runId, path.join(empty, recovered.output));
  assert.equal((await verifySet(synced.backupSet.sha256, f.repo, { client: f.client })).scope.projectId, 'film-a');
});
test('support recovery restores original mappings and rejects missing transitive evidence or conflicting targets', async t => {
  const f = await fixture(t), childPath = 'data/workspace/qualification/fixture.json', parentPath = 'data/workspace/qualification/pilot.json';
  privateJson(path.join(f.repo, childPath), { case: 'synthetic', passed: true });
  const child = { path: childPath, ...hashes(path.join(f.repo, childPath)), role: 'qualification-evidence' };
  privateJson(path.join(f.repo, parentPath), { evidence: { path: childPath, sha256: child.sha256, bytes: child.bytes },
    samples: [{ clipId: f.clip.id, runId: f.result.runId, manifestSha256: hashFile(path.join(runPath(f.clip.id, f.result.runId, f.repo), 'manifest.json')) }] });
  const parent = { path: parentPath, ...hashes(path.join(f.repo, parentPath)), role: 'pilot-review' };
  const locationsPath = 'data/clips/locations.json';
  privateJson(path.join(f.repo, locationsPath), { schemaVersion: 1, locations: { 'data/workspace/fixture/source.mp4': { id: f.clip.id, bytes: f.clip.bytes } } });
  const locations = { path: locationsPath, ...hashes(path.join(f.repo, locationsPath)), role: 'historical-locations' };
  const support = path.join(f.repo, 'data/clips/analysis/support.json');
  privateJson(support, { schemaVersion: 1, files: [parent, locations] });
  assert.throws(() => buildPlan(f.repo), /Transitive support evidence/);
  privateJson(support, { schemaVersion: 1, files: [parent, child, locations] });
  const plan = buildPlan(f.repo);
  assert.throws(() => verifySupportClosure(plan.objects.filter(o => o.kind !== 'analysis-manifest'), f.repo), /Referenced analysis manifest/);
  const synced = await sync(f.repo, { client: f.client });
  const empty = path.join(f.repo, 'another-machine'); fs.mkdirSync(empty); privateJson(path.join(empty, 'data/clips/cloud/config.json'), f.c);
  const recovered = await recoverSet(synced.backupSet.sha256, 'data/workspace/recovered', [f.clip.id], empty, { client: f.client, rehearse: true });
  const root = path.join(empty, recovered.output);
  assert.equal(hashFile(path.join(root, childPath)), child.sha256);
  assert.equal(hashFile(path.join(root, locationsPath)), locations.sha256);
  assert.equal(recovered.support.restoredPaths, 3);
  const set = readJson(path.join(f.repo, `data/clips/cloud/backup-sets/${synced.backupSet.sha256}.json`));
  set.objects.find(o => o.role === 'pilot-review').restorePaths.push(f.clip.path);
  assert.throws(() => validateBackupSet(set), /Unsafe recovery support path|Conflicting/);
});
test('isolated qualification fixtures recover their catalog, source, inventory and complete declared run', async t => {
  const f = await fixture(t), prefix = 'data/workspace/qualification/fixture-library';
  const runRelative = `data/clips/${f.clip.id}/analysis/${f.result.runId}`;
  const manifest = verifyRun(f.clip.id, f.result.runId, f.repo);
  const raw = readJson(path.join(f.repo, runRelative, 'manifest.json'));
  const paths = [`catalog/clips/${f.clip.id}.json`, f.clip.path, `${runRelative}/manifest.json`, raw.configRef.path,
    ...manifest.artifacts.map(a => `${runRelative}/${a.path}`)];
  const files = paths.map(relative => {
    const target = `${prefix}/${relative}`, absolute = path.join(f.repo, target);
    fs.mkdirSync(path.dirname(absolute), { recursive: true }); fs.copyFileSync(path.join(f.repo, relative), absolute);
    return { path: target, ...hashes(absolute), role: 'qualification-evidence' };
  });
  const evidencePath = 'data/workspace/qualification/evidence.json';
  privateJson(path.join(f.repo, evidencePath), { clipId: f.clip.id, runId: f.result.runId,
    manifestSha256: hashFile(path.join(f.repo, runRelative, 'manifest.json')) });
  files.push({ path: evidencePath, ...hashes(path.join(f.repo, evidencePath)), role: 'qualification-evidence' });
  const supportFile = path.join(f.repo, 'data/clips/analysis/support.json');
  privateJson(supportFile, { schemaVersion: 1, files: files.filter(f => !f.path.endsWith('poster.jpg')) });
  assert.throws(() => buildPlan(f.repo), /Nested qualification fixture dependency/);
  privateJson(supportFile, { schemaVersion: 1, files });
  const plan = buildPlan(f.repo);
  verifySupportClosure(plan.objects.filter(o => o.kind !== 'analysis-manifest'), f.repo);
  const synced = await sync(f.repo, { client: f.client });
  const empty = path.join(f.repo, 'fixture-recovery-machine'); fs.mkdirSync(empty);
  privateJson(path.join(empty, 'data/clips/cloud/config.json'), f.c);
  const recovered = await recoverSet(synced.backupSet.sha256, 'data/workspace/recovered', [f.clip.id], empty, { client: f.client });
  const nested = path.join(empty, recovered.output, prefix);
  verifyRun(f.clip.id, f.result.runId, nested);
  assert.equal(hashFile(path.join(nested, f.clip.path)), f.clip.sha256);
  assert.equal(recovered.support.transitiveEvidenceVerified, true);
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
test('a new recovery reuses verified cloud downloads and rejects altered failed-cache bytes', async t => {
  const f = await fixture(t), synced = await sync(f.repo, { client: f.client });
  const name = [...f.objects.keys()].find(n => n.endsWith('poster.jpg')), body = f.bodies.get(name);
  f.bodies.set(name, body.subarray(0, 20));
  await assert.rejects(recoverSet(synced.backupSet.sha256, 'data/workspace/failed', [f.clip.id], f.repo, { client: f.client }), /checksum verification/);
  const parent = path.join(f.repo, 'data/clips/cloud/failed-recoveries');
  const cache = path.join(parent, fs.readdirSync(parent)[0]);
  const set = readJson(path.join(f.repo, `data/clips/cloud/backup-sets/${synced.backupSet.sha256}.json`));
  const cached = set.objects.find(o => fs.existsSync(path.join(cache, objectTarget(o)))); assert.ok(cached);
  f.bodies.set(name, body); f.calls.length = 0;
  const recovered = await recoverSet(synced.backupSet.sha256, 'data/workspace/resumed', [f.clip.id], f.repo,
    { client: f.client, downloadCache: cache, rehearse: true });
  assert.ok(recovered.reusedCloudDownloadObjects > 0); assert.ok(recovered.reusedCloudDownloadBytes > 0);
  assert.equal(recovered.resumedFromFailedSet, synced.backupSet.sha256);
  assert.equal(f.calls.includes(cached.name), false); assert.ok(fs.existsSync(path.join(cache, 'failure.json')));
  fs.appendFileSync(path.join(cache, objectTarget(cached)), 'altered');
  await assert.rejects(recoverSet(synced.backupSet.sha256, 'data/workspace/invalid-cache', [f.clip.id], f.repo,
    { client: f.client, downloadCache: cache }), /Cached recovery bytes failed checksum/);
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
test('duplicate cleanup requires exact approval, current remote bytes and retained originals before any removal', async t => {
  const f = await fixture(t), scope = 'canonical-duplicates-with-retained-local-originals';
  const original = 'data/workspace/original/source.mp4';
  fs.mkdirSync(path.dirname(path.join(f.repo, original)), { recursive: true });
  fs.copyFileSync(path.join(f.repo, f.clip.path), path.join(f.repo, original));
  const locations = { schemaVersion: 1, locations: { [original]: { id: f.clip.id, bytes: f.clip.record.bytes } } };
  privateJson(path.join(f.repo, 'data/clips/locations.json'), locations);
  const save = (name, value) => { const relative = `data/workspace/cleanup/${name}.json`; privateJson(path.join(f.repo, relative), value);
    return { path: relative, ...hashes(path.join(f.repo, relative)) }; };
  const dependencyAudit = save('audit', { catalogSha256: sha(listClips(f.repo)), usesSha256: sha(listUses(f.repo)), locationsSha256: sha(locations),
    clips: [{ clipId: f.clip.id, activeEditsReviewed: true, archivesReviewed: true, originalPathsReviewed: true,
      alternatesReviewed: true, sharedSourcesReviewed: true, canonicalPathReferences: [], pendingUses: [] }] });
  const accessEvidence = save('access', { independentlyRecoverable: true, reviewedAt: new Date().toISOString(), fixture: true });
  privateJson(path.join(f.repo, 'data/clips/analysis/support.json'), { schemaVersion: 1,
    files: [{ ...dependencyAudit, role: 'dependency-audit' }, { ...accessEvidence, role: 'access-attestation' }] });
  const synced = await sync(f.repo, { client: f.client });
  const recoveryEvidence = save('recovery', { backupSetSha256: synced.backupSet.sha256, restoredAt: new Date().toISOString(), fixture: true,
    emptyRootRecovery: true, hashesVerified: true, fullDecode: true, searchRebuilt: true, normalFetchVerified: true,
    editRangeVerified: true, sourceRecovered: true, support: { transitiveEvidenceVerified: true } });
  const policy = { schemaVersion: 1, scope, clipIds: [f.clip.id], backupSetSha256: synced.backupSet.sha256,
    dependencyAudit, accessEvidence, recoveryEvidence };
  const planned = await planDuplicates(policy, 'data/workspace/cleanup/manifest.json', f.repo, { client: f.client });
  let approval = save('approval', { schemaVersion: 1, scope, approvedBy: 'user', approvedAt: new Date().toISOString(), manifestSha256: 'a'.repeat(64) });
  await assert.rejects(applyDuplicates(planned.manifest, approval.path, f.repo, { client: f.client }), /exact duplicate manifest/);
  approval = save('approval', { schemaVersion: 1, scope, approvedBy: 'user', approvedAt: new Date().toISOString(), manifestSha256: planned.sha256 });
  fs.chmodSync(path.join(f.repo, original), 0o600); fs.appendFileSync(path.join(f.repo, original), 'changed');
  await assert.rejects(applyDuplicates(planned.manifest, approval.path, f.repo, { client: f.client }), /hash or size mismatch/);
  assert.equal(hashFile(path.join(f.repo, f.clip.path)), f.clip.sha256);
  fs.copyFileSync(path.join(f.repo, f.clip.path), path.join(f.repo, original));
  const remote = f.objects.get(`clips/${f.clip.id}/source.mp4`), generation = remote.generation; remote.generation = '999999';
  await assert.rejects(applyDuplicates(planned.manifest, approval.path, f.repo, { client: f.client }), /checksum or identity/);
  remote.generation = generation;
  const result = await applyDuplicates(planned.manifest, approval.path, f.repo, { client: f.client });
  assert.equal(result.removed, 1); assert.equal(fs.existsSync(path.join(f.repo, f.clip.path)), false);
  assert.equal(hashFile(path.join(f.repo, original)), f.clip.sha256); assert.ok(fs.existsSync(path.join(f.repo, result.receipt)));
  verifyRun(f.clip.id, f.result.runId, f.repo);
  await assert.rejects(applyDuplicates(planned.manifest, approval.path, f.repo, { client: f.client }), /ENOENT/);
});
