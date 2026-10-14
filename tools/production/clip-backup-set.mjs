/** Complete immutable backup membership, generation-pinned verification and empty-root recovery. */
import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { REPO, safePath, readJson, validateClip, validateUse, verifyClipSnapshots, hashFile, readClip } from './clip-library.mjs';
import { assert, validHash, privateJson, sha, now, verifyRun, runPath, artifactPath, configFor } from './clip-analysis-store.mjs';
import { loadConfig, Gcs, locked, hashes, verifyObject, reserve } from './clip-cloud.mjs';
import { download } from './clip-cloud-restore.mjs';
import { execute, resolveBinary } from './clip-analysis-process.mjs';

const base = 'data/clips/cloud';
const local = (repo, name) => safePath(repo, `${base}/${name}`);
const fields = o => Object.fromEntries(['name', 'sha256', 'bytes', 'md5Hash', 'kind', 'clipId', 'runId', 'artifactPath', 'snapshotSha256', 'reviewSha256', 'role'].filter(k => o[k] !== undefined).map(k => [k, o[k]]));

export function objectTarget(o) {
  if (o.kind === 'analysis-support') {
    assert(['dependency-audit', 'pilot-review', 'access-attestation', 'retention-plan'].includes(o.role)
      && o.name === `support/${o.sha256}.json`, 'Invalid analysis support member');
    return `data/clips/analysis/support/${o.sha256}.json`;
  }
  if (o.kind === 'catalog') {
    assert(o.name === `catalog/${o.sha256}.json.gz`, 'Invalid catalog backup member'); return `${base}/catalog/${o.sha256}.json.gz`;
  }
  assert(/^clip_[a-f0-9]{64}$/.test(o.clipId ?? ''), 'Invalid backup member clip identity');
  if (o.kind === 'analysis-review') {
    assert(validHash(o.reviewSha256) && /^run_[a-f0-9]{64}$/.test(o.runId ?? '') && o.name === `reviews/${o.clipId}/${o.sha256}.json`, 'Invalid analysis review member');
    return `data/clips/${o.clipId}/reviews/${o.reviewSha256}.json`;
  }
  if (o.kind === 'media') {
    const match = new RegExp(`^clips/${o.clipId}/source(\\.mp4|\\.mov|\\.webm|\\.mkv|\\.m4v|\\.avi)$`).exec(o.name);
    assert(match && o.clipId === `clip_${o.sha256}`, 'Invalid media backup member'); return `data/clips/${o.clipId}/source${match[1]}`;
  }
  if (o.kind === 'generation-snapshot') {
    assert(validHash(o.snapshotSha256) && o.name === `generations/${o.clipId}/${o.sha256}.json`, 'Invalid snapshot backup member');
    return `data/clips/${o.clipId}/generations/${o.snapshotSha256}.json`;
  }
  assert(['analysis-manifest', 'analysis-artifact'].includes(o.kind) && /^run_[a-f0-9]{64}$/.test(o.runId ?? ''), 'Unsupported backup payload');
  artifactPath('/backup-validation-root', o.artifactPath);
  assert(o.name === `analysis/${o.clipId}/${o.runId}/${o.artifactPath}`
    && (o.kind === 'analysis-manifest' ? o.artifactPath === 'manifest.json' : /^steps\/[a-z-]+\//.test(o.artifactPath)), 'Unsafe analysis backup member');
  return `data/clips/${o.clipId}/analysis/${o.runId}/${o.artifactPath}`;
}
export function validateBackupSet(set) {
  assert(set?.schemaVersion === 1 && typeof set.bucket === 'string' && Array.isArray(set.objects) && Array.isArray(set.clips)
    && set.objects.length > 0, 'Invalid complete backup set');
  const names = new Set(), targets = new Set(), clips = new Set();
  for (const c of set.clips) {
    assert(c.clipId === `clip_${c.sha256}` && validHash(c.sha256) && validHash(c.catalogSha256) && !clips.has(c.clipId)
      && Number.isSafeInteger(c.bytes) && c.bytes > 0, 'Invalid backup-set clip identity'); clips.add(c.clipId);
  }
  for (const o of set.objects) {
    const target = objectTarget(o);
    assert(validHash(o.sha256) && Number.isSafeInteger(o.bytes) && o.bytes >= 0 && /^\d+$/.test(o.generation ?? '')
      && /^[A-Za-z0-9+/]{22}==$/.test(o.md5Hash ?? '') && !names.has(o.name) && !targets.has(target), 'Invalid or duplicate backup object');
    if (!['catalog', 'analysis-support'].includes(o.kind)) assert(clips.has(o.clipId), 'Backup object is not a member of a known clip');
    names.add(o.name); targets.add(target);
  }
  assert(set.objects.filter(o => o.kind === 'catalog').length === 1, 'Backup set needs exactly one catalog');
  for (const c of set.clips) {
    const media = set.objects.filter(o => o.kind === 'media' && o.clipId === c.clipId);
    assert(media.length === 1 && media[0].sha256 === c.sha256 && media[0].bytes === c.bytes && media[0].name.endsWith(`source${c.extension}`), 'Backup set is missing its original master');
    const manifests = set.objects.filter(o => o.kind === 'analysis-manifest' && o.clipId === c.clipId);
    for (const o of set.objects.filter(o => ['analysis-artifact', 'analysis-review'].includes(o.kind) && o.clipId === c.clipId))
      assert(manifests.some(m => m.runId === o.runId), 'Analysis artifact has no backup manifest');
  }
  return set;
}
export async function sealBackupSet(plan, remote, repo, config, client) {
  const set = validateBackupSet({ schemaVersion: 1, bucket: config.bucket, clips: plan.clipRecords,
    objects: plan.objects.map(o => ({ ...fields(o), generation: verifyObject(o, remote.get(o.name)).generation })).sort((a, b) => a.name.localeCompare(b.name)) });
  const bytes = Buffer.from(JSON.stringify(set, null, 2) + '\n'), hash = (await import('node:crypto')).createHash('sha256').update(bytes).digest('hex');
  const relative = `${base}/backup-sets/${hash}.json`, file = safePath(repo, relative); privateJson(file, set, true);
  const object = { name: `backup-sets/${hash}.json`, localPath: relative, ...hashes(file), kind: 'backup-set' };
  reserve(repo, config, { storedBytes: [...remote.values()].reduce((s, o) => s + Number(o.size), 0) + object.bytes,
    classA: 3, classB: 3, action: 'seal-complete-backup-set' });
  const present = await client.get(object.name), actual = verifyObject(object, present ?? await client.upload(object));
  const receipt = { schemaVersion: 1, sha256: hash, object: object.name, generation: actual.generation, verifiedAt: now(), bucket: config.bucket,
    objects: set.objects.length, clips: set.clips.length };
  privateJson(local(repo, 'last-backup-set.json'), receipt); return receipt;
}
async function loadRemoteSet(hash, repo, config, client) {
  assert(validHash(hash), 'Specify a valid backup-set SHA-256');
  reserve(repo, config, { classB: 3, action: 'backup-set-preflight' }); await client.checkPrivate();
  const name = `backup-sets/${hash}.json`, remote = await client.get(name);
  assert(remote && Number(remote.size) > 0 && Number(remote.size) <= 64 * 1024 * 1024, 'Backup-set manifest unavailable or oversized');
  verifyObject({ name, sha256: hash, bytes: Number(remote.size), md5Hash: remote.md5Hash }, remote);
  const file = local(repo, `backup-sets/${hash}.json`);
  if (fs.existsSync(file)) assert(hashFile(file) === hash, 'Local backup-set manifest is corrupt');
  else {
    reserve(repo, config, { classB: 1, downloadBytes: Number(remote.size), action: 'download-backup-set' });
    fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 }); const tmp = `${file}.${randomUUID()}.part`;
    try { await download(client, remote, tmp); fs.linkSync(tmp, file); } finally { fs.rmSync(tmp, { force: true }); }
  }
  const set = validateBackupSet(readJson(file)); assert(set.bucket === config.bucket, 'Backup set belongs to another destination');
  return { set, remote };
}
async function verifyMembers(set, repo, config, client) {
  reserve(repo, config, { storedBytes: set.objects.reduce((s, o) => s + o.bytes, 0), classB: set.objects.length + 1, action: 'verify-complete-backup-set' });
  for (const o of set.objects) verifyObject(o, await client.get(o.name));
  await client.checkPrivate();
}
export async function verifySet(hash, repo = REPO, { client } = {}) {
  return locked(repo, async () => {
    const config = loadConfig(repo); client ??= new Gcs(config, repo);
    const { set, remote } = await loadRemoteSet(hash, repo, config, client); await verifyMembers(set, repo, config, client);
    const receipt = { schemaVersion: 1, backupSetSha256: hash, backupSetGeneration: remote.generation, bucket: config.bucket,
      verifiedAt: now(), members: set.objects.length, verification: 'Current remote generation, SHA-256 metadata, MD5 and byte length for every member' };
    privateJson(local(repo, `verification/${hash}.json`), receipt); return receipt;
  });
}
function installCatalog(file, root, set) {
  let catalog;
  try { catalog = JSON.parse(gunzipSync(fs.readFileSync(file), { maxOutputLength: 256 * 1024 * 1024 })); }
  catch { throw new Error('Backup catalog failed bounded decoding'); }
  assert(catalog.schemaVersion === 1 && Array.isArray(catalog.clips) && Array.isArray(catalog.uses), 'Invalid backup catalog');
  const ids = new Map(), uses = new Set();
  for (const c of catalog.clips) {
    validateClip(c); assert(!ids.has(c.id), 'Duplicate catalog clip'); ids.set(c.id, c);
    const expected = set.clips.find(x => x.clipId === c.id);
    assert(expected && sha(c) === expected.catalogSha256 && c.sha256 === expected.sha256 && c.bytes === expected.bytes, 'Catalog differs from backup-set clip evidence');
    for (const g of c.generations.filter(g => g.snapshotSha256)) assert(set.objects.some(o => o.clipId === c.id && o.snapshotSha256 === g.snapshotSha256), 'Backup set omits required creation evidence');
    privateJson(safePath(root, `catalog/clips/${c.id}.json`), c, true);
  }
  assert(ids.size === set.clips.length, 'Backup catalog membership mismatch');
  for (const u of catalog.uses) {
    assert(ids.has(u.clipId) && !uses.has(u.id), 'Unresolved or duplicate catalog use'); validateUse(u, ids.get(u.clipId)); uses.add(u.id);
    privateJson(safePath(root, `catalog/uses/${u.id}.json`), u, true);
  }
  return catalog;
}
export function formatSignature(clip, manifest, repo = REPO) {
  const dir = runPath(clip.id, manifest.runId, repo), p = readJson(path.join(dir, 'steps/probe/technical.json'));
  const t = readJson(path.join(dir, 'steps/timing/timing.json'));
  return sha({ extension: clip.extension, streams: p.streams.map(s => ({ type: s.codec_type, codec: s.codec_name, pixelFormat: s.pix_fmt,
    transfer: s.color_transfer, rotated: s.side_data_list?.some(d => Number(d.rotation ?? 0) !== 0) ?? false,
    vfr: t.streams.find(x => x.streamIndex === s.index)?.variableFrameTiming ?? false })) });
}
export async function recoverSet(hash, output, ids, repo = REPO, { client, rehearse = false } = {}) {
  return locked(repo, async () => {
    assert(Array.isArray(ids) && ids.length && new Set(ids).size === ids.length, 'Select explicit clips for bounded recovery');
    const target = safePath(repo, output);
    assert(output.startsWith('data/workspace/') && !fs.existsSync(target), 'Recovery requires a new directory under data/workspace');
    const config = loadConfig(repo); client ??= new Gcs(config, repo);
    const { set, remote } = await loadRemoteSet(hash, repo, config, client);
    assert(ids.every(id => set.clips.some(c => c.clipId === id)), 'Selected clip is absent from the backup set');
    const selected = set.objects.filter(o => ['catalog', 'analysis-support'].includes(o.kind) || ids.includes(o.clipId));
    reserve(repo, config, { storedBytes: set.objects.reduce((s, o) => s + o.bytes, 0), classB: selected.length * 2,
      downloadBytes: selected.reduce((s, o) => s + o.bytes, 0), action: 'recover-complete-backup-members' });
    const parent = local(repo, 'restore-staging'); fs.mkdirSync(parent, { recursive: true, mode: 0o700 });
    const stage = fs.mkdtempSync(path.join(parent, 'set-'));
    try {
      for (const o of selected) {
        const actual = verifyObject(o, await client.get(o.name)), file = safePath(stage, objectTarget(o));
        fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 }); await download(client, actual, file);
      }
      const catalogObject = selected.find(o => o.kind === 'catalog'); installCatalog(safePath(stage, objectTarget(catalogObject)), stage, set);
      const rehearsed = [];
      for (const id of ids) {
        const clip = readClip(id, stage); verifyClipSnapshots(clip, stage);
        const runs = selected.filter(o => o.clipId === id && o.kind === 'analysis-manifest');
        for (const o of runs) {
          const m = verifyRun(id, o.runId, stage);
          assert(m.input.sha256 === clip.sha256 && m.input.bytes === clip.bytes, 'Restored analysis references different original bytes');
          const members = selected.filter(x => x.clipId === id && x.runId === o.runId && x.kind === 'analysis-artifact');
          assert(members.length === m.artifacts.length && m.artifacts.every(a => members.some(x => x.artifactPath === a.path && x.sha256 === a.sha256 && x.bytes === a.bytes)), 'Backup set does not close over all analysis dependencies');
          rehearsed.push({ clipId: id, runId: o.runId, formatSignature: formatSignature(clip, m, stage),
            artifactTypes: [...new Set(m.artifacts.map(a => path.extname(a.path)))].sort() });
        }
        for (const ref of clip.analysisRefs ?? []) assert(runs.some(o => o.runId === ref.runId && o.sha256 === ref.manifestSha256), 'Restored catalog analysis reference is unresolved');
        if (rehearse) {
          const dir = safePath(stage, `data/rehearsal/${id}`); fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
          await execute(resolveBinary('ffmpeg'), ['-nostdin', '-v', 'error', '-xerror', '-err_detect', 'explode', '-protocol_whitelist', 'file,pipe',
            '-i', safePath(stage, `data/clips/${id}/source${clip.extension}`), '-map', '0:v?', '-map', '0:a?', '-f', 'null', '-'], { dir, config: configFor(), commands: [] });
        }
      }
      const search = await (await import('./clip-analysis-views.mjs')).buildSearch(stage);
      const receipt = { schemaVersion: 1, backupSetSha256: hash, backupSetGeneration: remote.generation, restoredAt: now(), clips: ids,
        objects: selected.length, bytes: selected.reduce((s, o) => s + o.bytes, 0), hashesVerified: true, emptyRootRecovery: true,
        fullDecode: rehearse, searchRebuilt: true, searchRows: search.rows, formats: rehearsed, accessIndependence: 'Requires separate off-machine access attestation' };
      privateJson(path.join(stage, 'recovery.json'), receipt, true);
      fs.mkdirSync(path.dirname(target), { recursive: true, mode: 0o700 }); fs.mkdirSync(target, { mode: 0o700 });
      for (const name of fs.readdirSync(stage)) fs.renameSync(path.join(stage, name), path.join(target, name));
      if (rehearse) privateJson(local(repo, `rehearsals/${hash}-${sha(ids)}.json`), receipt, true);
      return { ...receipt, output };
    } finally { fs.rmSync(stage, { recursive: true, force: true }); }
  });
}
export async function backupMain(verb, args, repo = REPO) {
  if (verb === 'verify-set' && args.length === 1) return verifySet(args[0], repo);
  if (verb === 'recover-set' && args.length >= 3) {
    assert(args.filter(a => a.startsWith('--')).every(a => a === '--rehearse'), 'Unknown recovery option');
    const positional = args.filter(a => !a.startsWith('--')); return recoverSet(positional[0], positional[1], positional.slice(2), repo, { rehearse: args.includes('--rehearse') });
  }
  if (verb === 'backup-sets' && !args.length) return locked(repo, async () => {
    const c = loadConfig(repo), client = new Gcs(c, repo); reserve(repo, c, { classA: 2, classB: 3, action: 'list-complete-backups' }); await client.checkPrivate();
    return (await client.list('backup-sets/')).map(o => { const match = /^backup-sets\/([a-f0-9]{64})\.json$/.exec(o.name);
      assert(match, 'Unexpected backup-set object'); verifyObject({ name: o.name, sha256: match[1], bytes: Number(o.size), md5Hash: o.md5Hash }, o);
      return { sha256: match[1], bytes: Number(o.size), generation: o.generation }; });
  });
  if (verb === 'readiness' && args.length === 1) {
    const policy = readJson(safePath(repo, args[0])), verification = await verifySet(policy.backupSetSha256, repo);
    return (await import('./clip-analysis-views.mjs')).readiness(policy, repo, { verification });
  }
  throw new Error('Invalid complete-backup command arguments');
}
