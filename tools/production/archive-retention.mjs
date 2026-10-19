#!/usr/bin/env node
/** Remove reviewed edit derivatives from one verified archive; never select sources. */
import fs from 'node:fs/promises';
import { constants } from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { inventory, verifyArchive, MANIFEST } from './archive.mjs';
import { safePath, portablePath } from './record-schema.mjs';

const json = value => JSON.stringify(value, null, 2) + '\n';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const requireValue = (value, message) => { if (!value) throw new Error(message); };
const exists = file => fs.lstat(file).then(() => true, e => { if (e.code === 'ENOENT') return false; throw e; });
const read = async (repo, file) => JSON.parse(await fs.readFile(await safePath(repo, file), 'utf8'));
const video = /\.(mp4|mov|mkv|webm)$/;

function removable(file) {
  return portablePath(file) && (
    /^(final|finish)\/.+/.test(file) && video.test(file) ||
    /^edit\/(?:[^/]+\/)*soundtrack[^/]*\.(wav|flac|mp3|m4a)$/.test(file));
}

function probeMaster(file, decode = false) {
  const probe = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height', '-of', 'json', file], { encoding: 'utf8' });
  requireValue(!probe.error && probe.status === 0, 'Cannot probe retained master');
  const s = JSON.parse(probe.stdout).streams?.[0];
  requireValue(Math.min(s?.width, s?.height) >= 2160 && Math.max(s?.width, s?.height) >= 3840,
    'Retained master must be at least UHD 4K');
  if (decode) {
    const r = spawnSync('ffmpeg', ['-v', 'error', '-xerror', '-i', file, '-f', 'null', '-'], { encoding: 'utf8' });
    requireValue(!r.error && r.status === 0, 'Retained master failed full decode');
  }
}

async function checkFile(file, entry) {
  const handle = await fs.open(file, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const before = await handle.stat(), digest = createHash('sha256');
    requireValue(before.isFile(), 'Expected a regular retained or removed file');
    for await (const chunk of handle.createReadStream({ autoClose: false })) digest.update(chunk);
    const after = await handle.stat();
    requireValue(before.ino === after.ino && before.size === after.size && before.mtimeMs === after.mtimeMs &&
      before.ctimeMs === after.ctimeMs && after.size === entry.bytes && (after.mode & 0o7777) === entry.mode &&
      digest.digest('hex') === entry.sha256, `File changed: ${entry.path}`);
  } finally { await handle.close(); }
}

export async function planRetention(repo, selection) {
  requireValue(selection.schemaVersion === 1 && /^[a-z0-9][a-z0-9._-]*$/.test(selection.slug), 'Invalid retention selection');
  requireValue(typeof selection.dependencyReview === 'string' && selection.dependencyReview.trim(), 'Dependency review is required');
  requireValue(selection.master && portablePath(selection.master.path) && /^final\//.test(selection.master.path) &&
    video.test(selection.master.path) && /^[a-f0-9]{64}$/.test(selection.master.sha256), 'Explicit final master path and hash required');
  const verified = await verifyArchive(repo, selection.slug);
  const archive = verified.destination;
  const manifest = await read(repo, `${archive}/${MANIFEST}`);
  const entries = new Map(manifest.inventory.entries.filter(e => e.kind === 'file').map(e => [e.path, e]));
  const master = entries.get(selection.master.path);
  requireValue(master?.sha256 === selection.master.sha256, 'Retained master hash mismatch');
  probeMaster(await safePath(repo, `${archive}/${master.path}`));
  requireValue(Array.isArray(selection.remove) && selection.remove.length, 'An exact nonempty removal list is required');
  const seen = new Set();
  const remove = selection.remove.map(item => {
    requireValue(item && removable(item.path) && item.path !== master.path && !seen.has(item.path), 'Unsafe, duplicate or protected removal path');
    requireValue(typeof item.reason === 'string' && item.reason.trim(), 'Each removal needs a reason');
    seen.add(item.path);
    const entry = entries.get(item.path);
    requireValue(entry, `Removal file is absent from verified inventory: ${item.path}`);
    return { ...entry, reason: item.reason };
  }).sort((a, b) => a.path.localeCompare(b.path, 'en'));
  return { schemaVersion: 1, slug: selection.slug, archive, beforeInventorySha256: verified.inventorySha256,
    master, dependencyReview: selection.dependencyReview, remove,
    files: remove.length, bytes: remove.reduce((n, e) => n + e.bytes, 0) };
}

async function receiptPath(repo, relative) {
  requireValue(portablePath(relative) && relative.startsWith('data/release-receipts/'), 'Receipts must be outside archives under data/release-receipts');
  return safePath(repo, relative);
}

async function writeJournal(directory, state) {
  const temporary = path.join(directory, 'transaction.tmp');
  const handle = await fs.open(temporary, 'w', 0o600);
  try { await handle.writeFile(json(state)); await handle.sync(); } finally { await handle.close(); }
  await fs.rename(temporary, path.join(directory, 'transaction.json'));
}

async function locked(repo, operation) {
  const lockPath = await safePath(repo, 'data/.workspace-archive.lock');
  const lock = await fs.open(lockPath, 'wx', 0o600).catch(e => {
    if (e.code === 'EEXIST') throw new Error('Another archive operation holds the lock'); throw e;
  });
  try { return await operation(); } finally { await lock.close(); await fs.unlink(lockPath); }
}

export async function applyRetention(repo, plan, receipt) {
  const directory = await receiptPath(repo, receipt);
  requireValue(!(await exists(directory)), 'Receipt destination already exists; inspect its transaction before recovery');
  return locked(repo, async () => {
    const fresh = await planRetention(repo, { schemaVersion: 1, slug: plan.slug, master: plan.master,
      dependencyReview: plan.dependencyReview, remove: plan.remove });
    requireValue(JSON.stringify(fresh) === JSON.stringify(plan), 'Retention plan is stale or altered');
    const root = await safePath(repo, plan.archive);
    const seal = path.join(root, MANIFEST), oldBytes = await fs.readFile(seal);
    const old = JSON.parse(oldBytes), removed = new Set(plan.remove.map(e => e.path));
    const nextInventory = { ...old.inventory, entries: old.inventory.entries.filter(e => !removed.has(e.path)) };
    const next = { ...old, createdAt: new Date().toISOString(), inventory: nextInventory,
      inventorySha256: hash(JSON.stringify(nextInventory)) };
    probeMaster(await safePath(repo, `${plan.archive}/${plan.master.path}`), true);
    await fs.mkdir(path.dirname(directory), { recursive: true });
    await fs.mkdir(directory, { mode: 0o700 });
    await fs.writeFile(path.join(directory, 'before-manifest.json'), oldBytes, { flag: 'wx', mode: 0o600 });
    await fs.writeFile(path.join(directory, 'plan.json'), json(plan), { flag: 'wx', mode: 0o600 });
    const state = { schemaVersion: 1, phase: 'prepared', archive: plan.archive,
      beforeInventorySha256: plan.beforeInventorySha256, afterInventorySha256: next.inventorySha256,
      moved: [], purged: [] };
    await writeJournal(directory, state);
    let resealed = false;
    try {
      for (const entry of plan.remove) {
        const from = await safePath(repo, `${plan.archive}/${entry.path}`);
        const to = await safePath(repo, `${receipt}/quarantine/${entry.path}`);
        await checkFile(from, entry);
        await fs.mkdir(path.dirname(to), { recursive: true });
        await fs.rename(from, to);
        state.moved.push(entry.path);
        await writeJournal(directory, state);
        await checkFile(to, entry);
      }
      requireValue(JSON.stringify(await inventory(root)) === JSON.stringify(nextInventory), 'Retained archive changed during cleanup');
      const temporary = path.join(directory, 'after-manifest.tmp');
      await fs.writeFile(temporary, json(next), { flag: 'wx', mode: (await fs.stat(seal)).mode & 0o7777 });
      await fs.rename(temporary, seal); resealed = true;
      const verified = await verifyArchive(repo, plan.slug);
      await fs.writeFile(path.join(directory, 'after-manifest.json'), json(next), { flag: 'wx', mode: 0o600 });
      state.phase = 'verified-awaiting-purge';
      await writeJournal(directory, state);
      return { ...verified, removedFiles: plan.files, removedBytes: plan.bytes, receipt, phase: state.phase };
    } catch (error) {
      // Restore only files moved by this transaction; never overwrite a concurrent writer.
      for (const file of [...state.moved].reverse()) {
        const from = await safePath(repo, `${receipt}/quarantine/${file}`);
        const to = await safePath(repo, `${plan.archive}/${file}`);
        requireValue(!(await exists(to)), `Rollback conflict; preserve receipt: ${file}`);
        await fs.rename(from, to);
      }
      if (resealed) await fs.writeFile(seal, oldBytes);
      state.phase = 'rolled-back'; await writeJournal(directory, state);
      throw error;
    }
  });
}

export async function purgeRetention(repo, receipt) {
  const directory = await receiptPath(repo, receipt);
  return locked(repo, async () => {
    const state = await read(repo, `${receipt}/transaction.json`);
    const plan = await read(repo, `${receipt}/plan.json`);
    requireValue(['verified-awaiting-purge', 'complete'].includes(state.phase), 'Transaction is not verified for purge');
    requireValue(state.archive === plan.archive && state.beforeInventorySha256 === plan.beforeInventorySha256 &&
      JSON.stringify(state.moved) === JSON.stringify(plan.remove.map(e => e.path)), 'Transaction and plan disagree');
    const verified = await verifyArchive(repo, plan.slug);
    requireValue(verified.destination === plan.archive && verified.inventorySha256 === state.afterInventorySha256, 'Archive changed before purge');
    await checkFile(await safePath(repo, `${plan.archive}/${plan.master.path}`), plan.master);
    for (const entry of plan.remove) {
      requireValue(removable(entry.path) && entry.path !== plan.master.path, 'Unsafe removal receipt');
      requireValue(!(await exists(await safePath(repo, `${plan.archive}/${entry.path}`))), 'Removed file reappeared in archive');
      const file = await safePath(repo, `${receipt}/quarantine/${entry.path}`);
      if (await exists(file)) await checkFile(file, entry);
    }
    for (const entry of plan.remove) {
      const file = await safePath(repo, `${receipt}/quarantine/${entry.path}`);
      if (await exists(file)) { await checkFile(file, entry); await fs.unlink(file); }
      if (!state.purged.includes(entry.path)) state.purged.push(entry.path);
      await writeJournal(directory, state);
    }
    // Only empty directories are removable; unexpected content remains for inspection.
    const quarantine = await safePath(repo, `${receipt}/quarantine`);
    if (await exists(quarantine)) {
      const empty = async dir => {
        for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
          requireValue(entry.isDirectory() && !entry.isSymbolicLink(), 'Unexpected quarantine content');
          await empty(path.join(dir, entry.name));
        }
        await fs.rmdir(dir);
      };
      await empty(quarantine);
    }
    state.phase = 'complete'; await writeJournal(directory, state);
    return { ...verified, removedFiles: plan.files, removedBytes: plan.bytes, receipt, phase: state.phase };
  });
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  const [action, file, receipt, ...extra] = process.argv.slice(2);
  try {
    requireValue(file && !extra.length && (action === 'apply' ? receipt : !receipt) &&
      ['plan', 'apply', 'purge'].includes(action), 'Usage: archive-retention.mjs plan SELECTION_JSON | apply PLAN_JSON RECEIPT_DIR | purge RECEIPT_DIR');
    const repo = process.cwd();
    const result = action === 'plan' ? await planRetention(repo, await read(repo, file)) : action === 'apply'
      ? await applyRetention(repo, await read(repo, file), receipt) : await purgeRetention(repo, file);
    console.log(json(result));
  } catch (error) { console.error(error.message.replaceAll(process.cwd(), '.')); process.exitCode = 1; }
}
