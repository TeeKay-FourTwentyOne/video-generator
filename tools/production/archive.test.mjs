import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { MANIFEST, planArchive, archiveWorkspace, verifyArchive } from './archive.mjs';

async function fixture(t) {
  const repo = await fs.mkdtemp(path.join(os.tmpdir(), 'film-archive-'));
  t.after(() => fs.rm(repo, { recursive: true, force: true }));
  const source = path.join(repo, 'data/workspace/example-v1');
  const target = path.join(repo, 'data/workspace-archive/example-v1');
  await fs.mkdir(path.join(source, 'final/v1'), { recursive: true });
  await fs.mkdir(path.join(source, 'final/v2-4k'), { recursive: true });
  await fs.mkdir(path.join(source, 'empty'));
  await fs.writeFile(path.join(source, 'final/v1/film.mp4'), 'native preserved');
  await fs.writeFile(path.join(source, 'final/v2-4k/film.mp4'), 'published preserved');
  await fs.writeFile(path.join(source, '.local-note'), 'hidden files preserved', { mode: 0o600 });
  return { repo, source, target };
}

test('archive plans without mutation and preserves all versions, empty directories and modes', async t => {
  const { repo, source, target } = await fixture(t);
  const before = await fs.stat(path.join(source, 'final/v1/film.mp4'));
  const plan = await planArchive(repo, 'example-v1');
  assert.equal(plan.inventory.entries.filter(e => e.kind === 'file').length, 3);
  await assert.rejects(fs.stat(path.join(source, MANIFEST)), { code: 'ENOENT' });
  await assert.rejects(fs.stat(path.dirname(target)), { code: 'ENOENT' });
  const result = await archiveWorkspace(repo, 'example-v1');
  assert.equal(result.archived, true); assert.equal(result.files, 3);
  assert.equal(result.inventorySha256, plan.inventorySha256);
  await assert.rejects(fs.stat(source), { code: 'ENOENT' });
  assert.equal((await fs.stat(path.join(target, 'final/v1/film.mp4'))).ino, before.ino);
  assert.equal((await fs.stat(path.join(target, '.local-note'))).mode & 0o777, 0o600);
  assert.equal((await fs.stat(path.join(target, 'empty'))).isDirectory(), true);
  assert.equal((await verifyArchive(repo, 'example-v1')).verified, true);
});

test('archive refuses an existing destination without changing either tree', async t => {
  const { repo, source, target } = await fixture(t);
  await fs.mkdir(target, { recursive: true });
  await assert.rejects(archiveWorkspace(repo, 'example-v1'), /already exists/);
  assert.equal(await fs.readFile(path.join(source, '.local-note'), 'utf8'), 'hidden files preserved');
  assert.deepEqual(await fs.readdir(target), []);
});

test('archive refuses symlinks and path escapes', async t => {
  const { repo, source } = await fixture(t);
  for (const slug of ['..', '../example-v1', '/example-v1', 'example/v1', '']) {
    await assert.rejects(planArchive(repo, slug), /slug/);
  }
  await fs.symlink(path.join(repo, 'outside'), path.join(source, 'external'));
  await assert.rejects(archiveWorkspace(repo, 'example-v1'), /link or special file/);
  await fs.unlink(path.join(source, 'external'));
  await fs.symlink(path.join(source, 'final/v1/film.mp4'), path.join(source, MANIFEST));
  await assert.rejects(planArchive(repo, 'example-v1'), /regular file/);
});

test('archive refuses symlinked destination parents', async t => {
  const { repo } = await fixture(t);
  await fs.mkdir(path.join(repo, 'elsewhere'));
  await fs.symlink(path.join(repo, 'elsewhere'), path.join(repo, 'data/workspace-archive'));
  await assert.rejects(archiveWorkspace(repo, 'example-v1'), /real directory/);
  assert.deepEqual(await fs.readdir(path.join(repo, 'elsewhere')), []);
});

test('verification detects same-size edits, added files, missing files and changed permissions', async t => {
  const { repo, target } = await fixture(t);
  await archiveWorkspace(repo, 'example-v1');
  const file = path.join(target, '.local-note');
  const original = await fs.readFile(file);
  await fs.writeFile(file, Buffer.alloc(original.length, 120));
  await assert.rejects(verifyArchive(repo, 'example-v1'), /mismatch/);
  await fs.writeFile(file, original);
  await fs.writeFile(path.join(target, 'extra'), 'unrecorded');
  await assert.rejects(verifyArchive(repo, 'example-v1'), /mismatch/);
  await fs.unlink(path.join(target, 'extra'));
  await fs.unlink(file);
  await assert.rejects(verifyArchive(repo, 'example-v1'), /mismatch/);
  await fs.writeFile(file, original, { mode: 0o600 });
  await fs.chmod(file, 0o644);
  await assert.rejects(verifyArchive(repo, 'example-v1'), /mismatch/);
  await fs.chmod(file, 0o600);
  assert.equal((await verifyArchive(repo, 'example-v1')).verified, true);
});

test('archive resumes a sealed source but refuses a stale seal', async t => {
  const { repo, source } = await fixture(t);
  const plan = await planArchive(repo, 'example-v1');
  await fs.writeFile(path.join(source, MANIFEST), JSON.stringify(plan));
  await fs.writeFile(path.join(source, 'late-edit'), 'changed after sealing');
  await assert.rejects(archiveWorkspace(repo, 'example-v1'), /mismatch/);
  await fs.unlink(path.join(source, 'late-edit'));
  assert.equal((await archiveWorkspace(repo, 'example-v1')).verified, true);
});

test('archive respects another operation lock and rejects invalid manifests', async t => {
  const { repo, source } = await fixture(t);
  const lock = path.join(repo, 'data/.workspace-archive.lock');
  await fs.writeFile(lock, 'held');
  await assert.rejects(archiveWorkspace(repo, 'example-v1'), /holds the lock/);
  assert.equal(await fs.readFile(lock, 'utf8'), 'held');
  await fs.unlink(lock);
  const plan = await planArchive(repo, 'example-v1');
  plan.inventory.entries[0].path = '../../outside';
  await fs.writeFile(path.join(source, MANIFEST), JSON.stringify(plan));
  await assert.rejects(archiveWorkspace(repo, 'example-v1'), /Invalid archive manifest/);
});
