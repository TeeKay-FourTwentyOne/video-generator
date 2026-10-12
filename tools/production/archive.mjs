#!/usr/bin/env node
/** Intact, local workspace archival. No deletion, provider calls or Git actions. */
import fs from 'node:fs/promises';
import { constants } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const MANIFEST = 'workspace-archive-manifest.json';
const digest = value => createHash('sha256').update(value).digest('hex');
const mode = stat => stat.mode & 0o7777;
const exists = async file => fs.lstat(file).then(() => true, error => {
  if (error.code === 'ENOENT') return false;
  throw error;
});

function checkSlug(slug) {
  if (typeof slug !== 'string' || !/^[a-z0-9][a-z0-9._-]*$/.test(slug)) {
    throw new Error('Expected one lowercase project slug, not a path');
  }
}

// Refuse symlinked ancestors as well as symlinks inside the project.
async function directory(root, relative, create = false) {
  let current = root;
  for (const part of relative.split('/')) {
    current = path.join(current, part);
    if (create) await fs.mkdir(current).catch(error => { if (error.code !== 'EEXIST') throw error; });
    const stat = await fs.lstat(current);
    if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`Not a real directory: ${relative}`);
  }
  return current;
}

async function fileEntry(file, relative) {
  const handle = await fs.open(file, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const before = await handle.stat();
    if (!before.isFile()) throw new Error(`Not a regular file: ${relative}`);
    const hash = createHash('sha256');
    for await (const chunk of handle.createReadStream({ autoClose: false })) hash.update(chunk);
    const after = await handle.stat();
    if (before.size !== after.size || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs) {
      throw new Error(`File changed during inventory: ${relative}`);
    }
    return { path: relative, kind: 'file', mode: mode(after), bytes: after.size, sha256: hash.digest('hex') };
  } finally { await handle.close(); }
}

export async function inventory(root) {
  const entries = [];
  async function walk(relative) {
    const names = (await fs.readdir(path.join(root, relative))).sort();
    for (const name of names) {
      const child = relative ? `${relative}/${name}` : name;
      const file = path.join(root, child), stat = await fs.lstat(file);
      if (stat.isSymbolicLink() || (!stat.isFile() && !stat.isDirectory())) {
        throw new Error(`Unsupported link or special file: ${child}`);
      }
      if (child === MANIFEST) {
        if (!stat.isFile()) throw new Error('Archive manifest must be a regular file');
        continue; // The manifest explicitly excludes only itself.
      }
      if (stat.isDirectory()) {
        entries.push({ path: child, kind: 'directory', mode: mode(stat) });
        await walk(child);
      } else entries.push(await fileEntry(file, child));
    }
  }
  await walk('');
  return { rootMode: mode(await fs.lstat(root)), entries };
}

function summary(manifest) {
  return { source: manifest.source, destination: manifest.destination,
    files: manifest.inventory.entries.filter(e => e.kind === 'file').length,
    directories: manifest.inventory.entries.filter(e => e.kind === 'directory').length,
    bytes: manifest.inventory.entries.reduce((n, e) => n + (e.bytes ?? 0), 0),
    inventorySha256: manifest.inventorySha256 };
}

function validateManifest(manifest, slug) {
  if (manifest.schemaVersion !== 1 || manifest.slug !== slug ||
      manifest.source !== `data/workspace/${slug}` || manifest.destination !== `data/workspace-archive/${slug}` ||
      manifest.excludedPath !== MANIFEST || !Array.isArray(manifest.inventory?.entries) ||
      digest(JSON.stringify(manifest.inventory)) !== manifest.inventorySha256) {
    throw new Error('Invalid archive manifest');
  }
}

async function verifyDirectory(root, slug) {
  const file = path.join(root, MANIFEST), stat = await fs.lstat(file);
  if (!stat.isFile() || stat.isSymbolicLink()) throw new Error('Archive manifest must be a regular file');
  const manifest = JSON.parse(await fs.readFile(file, 'utf8'));
  validateManifest(manifest, slug);
  const current = await inventory(root);
  if (JSON.stringify(current) !== JSON.stringify(manifest.inventory)) {
    throw new Error('Archive inventory mismatch: files, directories, permissions or content changed');
  }
  return manifest;
}

export async function planArchive(repoRoot, slug) {
  checkSlug(slug);
  const repo = await fs.realpath(repoRoot);
  const source = `data/workspace/${slug}`, destination = `data/workspace-archive/${slug}`;
  const root = await directory(repo, source);
  if (await exists(path.join(repo, 'data/workspace-archive'))) await directory(repo, 'data/workspace-archive');
  if (await exists(path.join(repo, destination))) throw new Error('Archive destination already exists; verify it instead');
  if (await exists(path.join(root, MANIFEST))) return verifyDirectory(root, slug);
  const snapshot = await inventory(root);
  return { schemaVersion: 1, slug, source, destination, createdAt: new Date().toISOString(),
    excludedPath: MANIFEST, inventory: snapshot, inventorySha256: digest(JSON.stringify(snapshot)) };
}

export async function archiveWorkspace(repoRoot, slug) {
  checkSlug(slug);
  const repo = await fs.realpath(repoRoot);
  await directory(repo, 'data');
  const lockPath = path.join(repo, 'data/.workspace-archive.lock');
  const lock = await fs.open(lockPath, 'wx', 0o600).catch(error => {
    if (error.code === 'EEXIST') throw new Error('Another archive operation holds the lock');
    throw error;
  });
  let destination, reserved = false, moved = false;
  try {
    const manifest = await planArchive(repo, slug);
    const source = path.join(repo, manifest.source);
    await directory(repo, 'data/workspace-archive', true);
    destination = path.join(repo, manifest.destination);
    // Reserve a new empty target. POSIX rename atomically replaces our empty
    // directory; an existing target is never merged, overwritten or numbered.
    await fs.mkdir(destination); reserved = true;
    const seal = path.join(source, MANIFEST);
    if (!(await exists(seal))) await fs.writeFile(seal, JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
    await verifyDirectory(source, slug);
    await fs.rename(source, destination); moved = true;
    await verifyDirectory(destination, slug);
    return { archived: true, verified: true, ...summary(manifest) };
  } finally {
    // On a failed move, remove only our empty reservation. Preserve the source
    // and its seal for inspection/retry. Never copy-and-delete across devices.
    if (reserved && !moved) await fs.rmdir(destination).catch(() => {});
    await lock.close();
    await fs.unlink(lockPath);
  }
}

export async function verifyArchive(repoRoot, slug) {
  checkSlug(slug);
  const repo = await fs.realpath(repoRoot);
  const root = await directory(repo, `data/workspace-archive/${slug}`);
  return { verified: true, ...summary(await verifyDirectory(root, slug)) };
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  const [action, slug, ...extra] = process.argv.slice(2);
  try {
    if (!['plan', 'apply', 'verify'].includes(action) || !slug || extra.length) {
      throw new Error('Usage from repository root: node tools/production/archive.mjs plan|apply|verify SLUG');
    }
    const result = action === 'plan' ? { dryRun: true, ...summary(await planArchive(process.cwd(), slug)) }
      : action === 'apply' ? await archiveWorkspace(process.cwd(), slug) : await verifyArchive(process.cwd(), slug);
    console.log(JSON.stringify(result, null, 2));
  } catch (error) { console.error(error.message.replaceAll(process.cwd(), '.')); process.exitCode = 1; }
}
