/** Restore immutable media and evidence without relying on local media or old receipts. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { Readable, Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { REPO, safePath, readJson, readClip, mediaPath, canonical, generationMetadata,
  verifyClipSnapshots, validateClip, validateUse } from './clip-library.mjs';
import { readSnapshot, snapshotHash } from './generation-snapshot.mjs';
import { loadConfig, Gcs, locked, privateJson, reserve, hashes, verifyObject } from './clip-cloud.mjs';

const base = 'data/clips/cloud';
const maxCatalogBytes = 64 * 1024 * 1024;
const maxSnapshotBytes = 4 * 1024 * 1024;
const same = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
function storedBytes(repo, minimum = 0) {
  const file = safePath(repo, `${base}/last-sync.json`);
  return fs.existsSync(file) ? Math.max(readJson(file).bytes, minimum) : minimum;
}
function identity(remote, name, sha256, bytes) {
  if (!/^[a-f0-9]{64}$/.test(sha256 ?? '') || !Number.isSafeInteger(bytes) || bytes < 1
      || !/^[A-Za-z0-9+/]{22}==$/.test(remote?.md5Hash ?? ''))
    throw new Error('Invalid cloud restore identity');
  return verifyObject({ name, sha256, bytes, md5Hash: remote.md5Hash }, remote);
}
function existing(target, remote) {
  if (!fs.existsSync(target)) return false;
  const actual = hashes(target);
  if (actual.bytes !== Number(remote.size) || actual.sha256 !== remote.metadata.sha256 || actual.md5Hash !== remote.md5Hash)
    throw new Error('Existing restore destination conflicts with verified cloud bytes; never overwrite it');
  return true;
}
export async function download(client, remote, target) {
  const url = client.url(`/o/${encodeURIComponent(remote.name)}?alt=media&generation=${remote.generation}`);
  const response = await client.request(url);
  if (!response.ok) throw new Error(`Cloud restore failed (HTTP ${response.status}; details withheld)`);
  const sha = createHash('sha256'), md5 = createHash('md5'); let bytes = 0;
  try {
    await pipeline(Readable.fromWeb(response.body), new Transform({ transform(chunk, _, callback) {
      bytes += chunk.length;
      if (bytes > Number(remote.size)) return callback(new Error('Restore exceeded the reserved byte count'));
      sha.update(chunk); md5.update(chunk); callback(null, chunk);
    } }), fs.createWriteStream(target, { flags: 'wx', mode: 0o600 }));
    if (bytes !== Number(remote.size) || sha.digest('hex') !== remote.metadata.sha256 || md5.digest('base64') !== remote.md5Hash)
      throw new Error('Restored bytes failed checksum verification');
  } catch (e) { fs.rmSync(target, { force: true }); throw e; }
}
function install(staged, target, remote, mode) {
  if (existing(target, remote)) return;
  fs.mkdirSync(path.dirname(target), { recursive: true, mode: 0o700 });
  fs.chmodSync(staged, mode);
  try { fs.linkSync(staged, target); }
  catch (e) { if (e.code !== 'EEXIST') throw e; existing(target, remote); }
}
function stageDir(repo) {
  const parent = safePath(repo, `${base}/restore-staging`);
  fs.mkdirSync(parent, { recursive: true, mode: 0o700 });
  return fs.mkdtempSync(path.join(parent, 'restore-'));
}

export async function fetchClip(id, repo = REPO, { client } = {}) {
  return locked(repo, async () => {
    const c = loadConfig(repo), clip = readClip(id, repo), target = mediaPath(clip, repo);
    client ??= new Gcs(c, repo);
    reserve(repo, c, { storedBytes: storedBytes(repo, clip.bytes), classA: 2, classB: 8, action: 'fetch-preflight' });
    await client.checkPrivate();
    const name = `clips/${id}/source${clip.extension}`, source = await client.get(name);
    identity(source, name, clip.sha256, clip.bytes);
    const sourcePresent = existing(target, source);
    const prefix = `generations/${id}/`, snapshots = await client.list(prefix);
    for (const s of snapshots) {
      const match = new RegExp(`^${prefix}([a-f0-9]{64})\\.json$`).exec(s.name);
      if (!match || Number(s.size) > maxSnapshotBytes) throw new Error('Unexpected generation snapshot object');
      identity(s, s.name, match[1], Number(s.size));
    }
    // Always inspect the remote snapshots: their object names hash file bytes, while
    // catalog snapshot IDs hash canonical JSON. Do not guess that mapping.
    const downloadBytes = (sourcePresent ? 0 : clip.bytes) + snapshots.reduce((sum, s) => sum + Number(s.size), 0);
    reserve(repo, c, { classB: snapshots.length + 1, downloadBytes, action: 'fetch-download' });
    const stage = stageDir(repo), installs = [], restoredSnapshots = new Set();
    try {
      for (const [index, remote] of snapshots.entries()) {
        const staged = path.join(stage, `snapshot-${index}.json`);
        await download(client, remote, staged);
        const snapshot = readSnapshot(staged), hash = snapshotHash(snapshot);
        const matching = clip.generations.filter(g => g.snapshotSha256 === hash);
        if (matching.some(g => !same(g, { ...generationMetadata(snapshot, 'creation-snapshot'), snapshotSha256: hash })))
          throw new Error('Restored generation snapshot differs from catalog evidence');
        const file = safePath(repo, `data/clips/${id}/generations/${hash}.json`);
        existing(file, remote);
        if (restoredSnapshots.has(hash)) throw new Error('Duplicate canonical generation snapshot in cloud backup');
        restoredSnapshots.add(hash); installs.push({ staged, target: file, remote, mode: 0o400 });
      }
      if (clip.generations.some(g => g.snapshotSha256 && !restoredSnapshots.has(g.snapshotSha256)))
        throw new Error('Required generation snapshot is missing from the cloud backup');
      if (!sourcePresent) {
        const staged = path.join(stage, 'source');
        await download(client, source, staged); installs.push({ staged, target, remote: source, mode: 0o444 });
      }
      // Validate every download and all pre-existing targets before installing anything.
      for (const item of installs) install(item.staged, item.target, item.remote, item.mode);
      if (!existing(target, source)) throw new Error('Restored master disappeared before verification');
      verifyClipSnapshots(readClip(id, repo), repo);
      const receipt = { schemaVersion: 1, restoredAt: new Date().toISOString(), clipId: id,
        path: path.relative(repo, target), sourceAlreadyPresent: sourcePresent, snapshots: snapshots.length,
        downloadedBytes: downloadBytes, verification: 'SHA-256, server MD5, byte length, pinned generation and creation-snapshot identity',
        bucket: c.bucket, objects: [source, ...snapshots].map(o => ({ name: o.name, generation: o.generation,
          sha256: o.metadata.sha256, md5Hash: o.md5Hash, bytes: Number(o.size) })) };
      privateJson(safePath(repo, `${base}/restores/${id}/${randomUUID()}.json`), receipt);
      return receipt;
    } finally { fs.rmSync(stage, { recursive: true, force: true }); }
  });
}

export async function catalogs(repo = REPO, { client } = {}) {
  return locked(repo, async () => {
    const c = loadConfig(repo); client ??= new Gcs(c, repo);
    reserve(repo, c, { storedBytes: storedBytes(repo), classA: 2, classB: 4, action: 'list-catalog-backups' });
    await client.checkPrivate();
    return (await client.list('catalog/')).map(o => {
      const match = /^catalog\/([a-f0-9]{64})\.json\.gz$/.exec(o.name);
      if (!match) throw new Error('Unexpected catalog backup object');
      identity(o, o.name, match[1], Number(o.size));
      return { sha256: match[1], bytes: Number(o.size), createdAt: o.timeCreated ?? null, generation: o.generation };
    }).sort((a, b) => (b.createdAt ?? '').localeCompare(a.createdAt ?? '') || a.sha256.localeCompare(b.sha256));
  });
}

export async function recoverCatalog(sha256, output, repo = REPO, { client } = {}) {
  return locked(repo, async () => {
    if (!/^[a-f0-9]{64}$/.test(sha256 ?? '')) throw new Error('Specify the SHA-256 from cloud catalogs');
    const target = safePath(repo, output);
    if (!target.startsWith(path.join(repo, 'data/workspace') + path.sep) || fs.existsSync(target))
      throw new Error('Recover catalog into a new directory under data/workspace');
    const c = loadConfig(repo); client ??= new Gcs(c, repo);
    reserve(repo, c, { storedBytes: storedBytes(repo), classB: 4, action: 'recover-catalog-preflight' });
    await client.checkPrivate();
    const name = `catalog/${sha256}.json.gz`, remote = await client.get(name);
    identity(remote, name, sha256, Number(remote?.size));
    if (Number(remote.size) > maxCatalogBytes) throw new Error('Catalog backup exceeds the supported size');
    reserve(repo, c, { classB: 1, downloadBytes: Number(remote.size), action: 'recover-catalog-download' });
    const stage = stageDir(repo);
    try {
      const compressed = path.join(stage, 'catalog.json.gz'); await download(client, remote, compressed);
      let catalog;
      try { catalog = JSON.parse(gunzipSync(fs.readFileSync(compressed), { maxOutputLength: 256 * 1024 * 1024 })); }
      catch { throw new Error('Catalog backup could not be decoded; details withheld'); }
      if (catalog.schemaVersion !== 1 || !Array.isArray(catalog.clips) || !Array.isArray(catalog.uses))
        throw new Error('Invalid catalog backup');
      const ids = new Map(), useIds = new Set();
      for (const clip of catalog.clips) {
        validateClip(clip); if (ids.has(clip.id)) throw new Error('Duplicate clip in catalog backup'); ids.set(clip.id, clip);
      }
      for (const use of catalog.uses) {
        if (!ids.has(use.clipId) || useIds.has(use.id)) throw new Error('Unresolved or duplicate use in catalog backup');
        validateUse(use, ids.get(use.clipId)); useIds.add(use.id);
      }
      for (const clip of catalog.clips) privateJson(path.join(stage, `catalog/clips/${clip.id}.json`), clip);
      for (const use of catalog.uses) privateJson(path.join(stage, `catalog/uses/${use.id}.json`), use);
      fs.mkdirSync(path.join(stage, 'catalog/uses'), { recursive: true, mode: 0o700 });
      fs.mkdirSync(path.join(stage, 'catalog/clips'), { recursive: true, mode: 0o700 });
      const receipt = { schemaVersion: 1, restoredAt: new Date().toISOString(), sha256, bytes: Number(remote.size),
        md5Hash: remote.md5Hash, generation: remote.generation, clips: ids.size, uses: useIds.size, output,
        verification: 'SHA-256, server MD5, byte length, pinned generation, catalog schemas and use references' };
      privateJson(path.join(stage, 'recovery.json'), receipt);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      // Exclusive creation prevents replacing even an empty existing directory.
      fs.mkdirSync(target, { mode: 0o700 });
      for (const name of fs.readdirSync(stage)) fs.renameSync(path.join(stage, name), path.join(target, name));
      return receipt;
    } finally { fs.rmSync(stage, { recursive: true, force: true }); }
  });
}
