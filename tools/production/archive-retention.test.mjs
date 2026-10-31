import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { archiveWorkspace, verifyArchive, MANIFEST } from './archive.mjs';
import { planRetention, applyRetention, purgeRetention } from './archive-retention.mjs';

async function fixture(t) {
  const repo = await fs.realpath(await fs.mkdtemp(path.join(os.tmpdir(), 'film-retention-')));
  t.after(() => fs.rm(repo, { recursive: true, force: true }));
  const source = path.join(repo, 'data/workspace/example-v1');
  const root = path.join(repo, 'data/workspace-archive/example-v1');
  for (const dir of ['final/v1', 'final/v2-4k', 'sources', 'edit', 'refs', 'renders/cache', 'qa', 'audio']) await fs.mkdir(path.join(source, dir), { recursive: true });
  const master = path.join(source, 'final/v2-4k/film.mp4');
  const r = spawnSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=2160x3840:r=24',
    '-frames:v', '1', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', master]);
  assert.equal(r.status, 0, r.stderr?.toString());
  await fs.writeFile(path.join(source, 'final/v1/film.mp4'), 'superseded render');
  await fs.writeFile(path.join(source, 'final/v1/delivery.json'), '{"historical":true}');
  await fs.writeFile(path.join(source, 'edit/soundtrack-v1.wav'), 'derived mix');
  await fs.writeFile(path.join(source, 'edit/score.wav'), 'original music');
  await fs.writeFile(path.join(source, 'sources/take.mp4'), 'original take');
  await fs.writeFile(path.join(source, 'refs/portrait.png'), 'original reference');
  for (const file of ['renders/cache/pass.mp4', 'qa/edge-test.mp4', 'audio/master.wav',
    'audio/V1-stem.wav', 'renders/source.mp4']) await fs.writeFile(path.join(source, file), `fixture ${file}`);
  const sha256 = createHash('sha256').update(await fs.readFile(master)).digest('hex');
  await archiveWorkspace(repo, 'example-v1');
  const selection = { schemaVersion: 1, slug: 'example-v1', master: { path: 'final/v2-4k/film.mp4', sha256 },
    dependencyReview: 'Original takes, score, reference and edit metadata retained. Only derived media selected.',
    remove: [{ path: 'final/v1/film.mp4', reason: 'superseded edit' }, { path: 'edit/soundtrack-v1.wav', reason: 'intermediate mix' }] };
  const receipt = 'data/release-receipts/example/retention';
  return { repo, root, selection, receipt };
}

test('retention plan is read-only; apply preserves sources, metadata and master, and purge is repeatable', async t => {
  const { repo, root, selection, receipt } = await fixture(t);
  const before = await fs.readFile(path.join(root, MANIFEST));
  const plan = await planRetention(repo, selection);
  assert.equal(plan.files, 2);
  assert.deepEqual(await fs.readFile(path.join(root, MANIFEST)), before);
  await assert.rejects(fs.stat(path.join(repo, receipt)), { code: 'ENOENT' });
  const applied = await applyRetention(repo, plan, receipt);
  assert.equal(applied.phase, 'verified-awaiting-purge');
  assert.equal((await verifyArchive(repo, selection.slug)).verified, true);
  await assert.rejects(fs.stat(path.join(root, 'final/v1/film.mp4')), { code: 'ENOENT' });
  assert.equal(await fs.readFile(path.join(root, 'sources/take.mp4'), 'utf8'), 'original take');
  assert.equal(await fs.readFile(path.join(root, 'edit/score.wav'), 'utf8'), 'original music');
  assert.equal(await fs.readFile(path.join(root, 'final/v1/delivery.json'), 'utf8'), '{"historical":true}');
  assert.equal((await purgeRetention(repo, receipt)).phase, 'complete');
  await assert.rejects(fs.stat(path.join(repo, receipt, 'quarantine')), { code: 'ENOENT' });
  assert.equal((await purgeRetention(repo, receipt)).phase, 'complete');
  assert.deepEqual(await fs.readFile(path.join(repo, receipt, 'before-manifest.json')), before);
});

test('selection refuses source media, metadata, traversal, duplicates, wrong master and a selected master', async t => {
  const { repo, selection } = await fixture(t);
  for (const file of ['sources/take.mp4', 'refs/portrait.png', 'edit/score.wav', 'final/v1/delivery.json',
    '../elsewhere.mp4', 'final/v2-4k/film.mp4']) {
    await assert.rejects(planRetention(repo, { ...selection, remove: [{ path: file, reason: 'remove' }] }));
  }
  await assert.rejects(planRetention(repo, { ...selection, remove: [...selection.remove, selection.remove[0]] }), /duplicate/);
  await assert.rejects(planRetention(repo, { ...selection, master: { ...selection.master, sha256: 'a'.repeat(64) } }), /hash mismatch/);
  await assert.rejects(planRetention(repo, { ...selection, dependencyReview: '' }), /Dependency review/);
});

test('explicit hashed custom derivatives use the same verified quarantine and purge transaction', async t => {
  const { repo, root, selection, receipt } = await fixture(t);
  const extra = [];
  for (const [file, derivativeClass] of [['renders/cache/pass.mp4', 'render-cache'],
    ['qa/edge-test.mp4', 'qa-render'], ['audio/master.wav', 'complete-mix']]) {
    const sha256 = createHash('sha256').update(await fs.readFile(path.join(root, file))).digest('hex');
    extra.push({ path: file, sha256, derivativeClass, reason: 'Reviewed regenerable derivative; inputs retained' });
  }
  const plan = await planRetention(repo, { ...selection, remove: [...selection.remove, ...extra] });
  assert.equal(plan.files, 5);
  await applyRetention(repo, plan, receipt);
  assert.equal((await purgeRetention(repo, receipt)).removedFiles, 5);
  for (const item of extra) await assert.rejects(fs.stat(path.join(root, item.path)), { code: 'ENOENT' });
  for (const file of ['audio/V1-stem.wav', 'renders/source.mp4', 'sources/take.mp4'])
    assert.ok((await fs.stat(path.join(root, file))).isFile());
  assert.equal((await verifyArchive(repo, selection.slug)).verified, true);
});

test('custom derivative review cannot omit hashes or authorize source, stem or metadata paths', async t => {
  const { repo, root, selection } = await fixture(t);
  const file = 'renders/cache/pass.mp4';
  const sha256 = createHash('sha256').update(await fs.readFile(path.join(root, file))).digest('hex');
  const item = { path: file, sha256, derivativeClass: 'render-cache', reason: 'Reviewed cache' };
  for (const bad of [{ ...item, sha256: undefined }, { ...item, sha256: 'a'.repeat(64) },
    { ...item, derivativeClass: undefined }, { ...item, derivativeClass: 'anything' },
    { ...item, path: 'sources/take.mp4' }, { ...item, path: 'renders/source.mp4' },
    { ...item, path: 'refs/portrait.png' }, { ...item, path: 'final/v1/delivery.json' },
    { ...item, path: 'audio/V1-stem.wav', derivativeClass: 'complete-mix' }])
    await assert.rejects(planRetention(repo, { ...selection, remove: [bad] }));
});

test('stale or changed plans, unsafe receipt paths and archive locks fail before removal', async t => {
  const { repo, root, selection, receipt } = await fixture(t);
  const plan = await planRetention(repo, selection);
  await assert.rejects(applyRetention(repo, { ...plan, bytes: plan.bytes + 1 }, receipt), /stale or altered/);
  await assert.rejects(applyRetention(repo, plan, 'data/workspace-archive/receipt'), /outside archives/);
  await fs.writeFile(path.join(repo, 'data/.workspace-archive.lock'), 'held');
  await assert.rejects(applyRetention(repo, plan, receipt), /holds the lock/);
  await fs.unlink(path.join(repo, 'data/.workspace-archive.lock'));
  await fs.writeFile(path.join(root, 'final/v1/film.mp4'), 'changed render');
  await assert.rejects(applyRetention(repo, plan, receipt), /mismatch/);
  assert.equal(await fs.readFile(path.join(root, 'final/v1/film.mp4'), 'utf8'), 'changed render');
});

test('a mid-move failure rolls back moved files and preserves the original seal', async t => {
  const { repo, root, selection, receipt } = await fixture(t);
  const plan = await planRetention(repo, selection), original = fs.rename;
  fs.rename = async (from, to) => {
    if (from === path.join(root, 'final/v1/film.mp4')) throw new Error('simulated move failure');
    return original(from, to);
  };
  try { await assert.rejects(applyRetention(repo, plan, receipt), /simulated move failure/); }
  finally { fs.rename = original; }
  assert.equal((await verifyArchive(repo, selection.slug)).inventorySha256, plan.beforeInventorySha256);
  assert.equal(JSON.parse(await fs.readFile(path.join(repo, receipt, 'transaction.json'))).phase, 'rolled-back');
  await assert.rejects(purgeRetention(repo, receipt), /not verified/);
});

test('purge refuses a changed quarantine file or archive; interrupted deletion resumes', async t => {
  const { repo, root, selection, receipt } = await fixture(t);
  const plan = await planRetention(repo, selection);
  await applyRetention(repo, plan, receipt);
  const q = path.join(repo, receipt, 'quarantine/edit/soundtrack-v1.wav');
  const bytes = await fs.readFile(q);
  await fs.writeFile(q, 'changed');
  await assert.rejects(purgeRetention(repo, receipt), /File changed/);
  await fs.writeFile(q, bytes);
  await fs.writeFile(path.join(root, 'unexpected'), 'writer');
  await assert.rejects(purgeRetention(repo, receipt), /mismatch/);
  await fs.unlink(path.join(root, 'unexpected'));
  const original = fs.unlink;
  fs.unlink = async file => {
    if (file === path.join(repo, receipt, 'quarantine/final/v1/film.mp4')) throw new Error('simulated unlink failure');
    return original(file);
  };
  try { await assert.rejects(purgeRetention(repo, receipt), /simulated unlink failure/); }
  finally { fs.unlink = original; }
  assert.equal((await purgeRetention(repo, receipt)).phase, 'complete');
});

test('symlink substitutions and an existing receipt are refused', async t => {
  const { repo, root, selection, receipt } = await fixture(t);
  const plan = await planRetention(repo, selection);
  await fs.mkdir(path.join(repo, receipt), { recursive: true });
  await assert.rejects(applyRetention(repo, plan, receipt), /already exists/);
  await fs.rmdir(path.join(repo, receipt));
  await fs.unlink(path.join(root, 'final/v1/film.mp4'));
  await fs.symlink(path.join(root, 'sources/take.mp4'), path.join(root, 'final/v1/film.mp4'));
  await assert.rejects(applyRetention(repo, plan, receipt), /link or special/);
});
