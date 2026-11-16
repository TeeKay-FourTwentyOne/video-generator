/** Post-publication local clip offload. Called only after a complete verified sync. */
import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { safePath, readJson, readClip, mediaPath, hashFile, VIDEO_EXTENSIONS } from './clip-library.mjs';
import { hashes, privateJson, verifyObject } from './clip-cloud.mjs';
import { assert, withLock } from './clip-analysis-store.mjs';
import { validateShape, sha256, portablePath } from './record-schema.mjs';
import { inventory, verifyArchive, MANIFEST } from './archive.mjs';
import { backupScope } from './clip-backup-scope.mjs';

const json = value => JSON.stringify(value, null, 2) + '\n';
const stamp = () => new Date().toISOString();
const stateRoot = projectId => `data/clips/cloud/projects/${projectId}/offload`;
const present = file => fs.lstatSync(file, { throwIfNoEntry: false }) !== undefined;
const relative = (repo, file) => path.relative(repo, file).split(path.sep).join('/');

export function publishedProject(repo, projectId) {
  assert(projectId !== undefined, 'Post-publication sync requires --project PROJECT_ID');
  backupScope(projectId);
  const recordPath = `briefs/${projectId}/production.json`, file = safePath(repo, recordPath);
  const bytes = fs.readFileSync(file), record = JSON.parse(bytes);
  validateShape(record);
  assert(record.projectId === projectId && record.status === 'published'
    && ['user-confirmed', 'public-page-verified'].includes(record.publication?.evidence),
  'Post-publication offload requires a published project record');
  const masters = record.artifacts.filter(a => a.publishedMaster && a.retention !== 'removed-intermediate');
  assert(masters.length === 1 && record.publication.artifactVersion === masters[0].version,
    'Post-publication offload requires one identified published master');
  const workspace = record.workspace;
  assert(workspace && ['active', 'archive-planned', 'archived-verified'].includes(workspace.state),
    'Post-publication offload requires an active or verified archived workspace');
  const archived = workspace.state === 'archived-verified';
  assert(new RegExp(`^data/${archived ? 'workspace-archive' : 'workspace'}/[a-z0-9][a-z0-9._-]*$`).test(workspace.path),
    'Unexpected project workspace locator');
  const root = safePath(repo, workspace.path), master = masters[0];
  assert(fs.lstatSync(root).isDirectory(), 'Project workspace is absent');
  assert(archived ? record.archive?.manifestPath === `${workspace.path}/${MANIFEST}` : !present(path.join(root, MANIFEST)),
    'Finish or reconcile the existing archive transaction before offload');
  assert(hashFile(safePath(root, master.path)) === master.sha256, 'Published master changed or is unavailable');
  const protectedPaths = new Set(record.artifacts.map(a => `${workspace.path}/${a.path}`));
  return { projectId, recordPath, bytes, record, root, archived, workspace: workspace.path,
    slug: path.basename(root), master, protectedPaths };
}

function allowedCopy(file, clip, project, repo) {
  if (!portablePath(file)) return false;
  if (file === relative(repo, mediaPath(clip, repo))) return true;
  if (!file.startsWith(project.workspace + '/') || project.protectedPaths.has(file)) return false;
  const inside = file.slice(project.workspace.length + 1);
  // Delivery packages have their own retention transaction. Preserve all of them here.
  return !/^(final|finish)\//.test(inside) && VIDEO_EXTENSIONS.has(path.extname(file).toLowerCase());
}

function checkCopy(file, entry) {
  const before = fs.lstatSync(file);
  assert(before.isFile() && !before.isSymbolicLink(), 'Offload target must be a regular file');
  const actual = hashes(file), after = fs.lstatSync(file);
  assert(before.dev === after.dev && before.ino === after.ino && before.size === after.size
    && before.mtimeMs === after.mtimeMs && before.ctimeMs === after.ctimeMs,
  'Clip changed while verifying offload bytes');
  assert(actual.sha256 === entry.sha256 && actual.bytes === entry.bytes && actual.md5Hash === entry.md5Hash
    && (after.mode & 0o7777) === entry.mode, 'Offload copy differs from verified backup bytes');
}

async function clipLocks(repo, ids, action, index = 0) {
  if (index === ids.length) return action();
  return withLock(repo, ids[index], async () => {
    const dir = safePath(repo, `data/clips/.locks/${ids[index]}`);
    fs.mkdirSync(path.dirname(dir), { recursive: true });
    fs.mkdirSync(dir); // Existing import/catalog writers stop this transaction.
    try { return await clipLocks(repo, ids, action, index + 1); }
    finally { fs.rmdirSync(dir); }
  });
}

async function prepare(repo, project, plan, backupSet, remote, receiptPath) {
  const directory = safePath(repo, receiptPath), byHash = new Map(), candidates = new Map();
  for (const member of plan.objects.filter(o => o.kind === 'media')) {
    const object = { ...member, generation: verifyObject(member, remote.get(member.name)).generation };
    const clip = readClip(member.clipId, repo);
    assert(clip.sha256 === member.sha256 && clip.bytes === member.bytes, 'Clip catalog changed after sync');
    byHash.set(clip.sha256, { clip, object });
    const file = mediaPath(clip, repo);
    if (present(file)) candidates.set(relative(repo, file), { clip, object });
  }
  let beforeSeal;
  if (project.archived) {
    const verified = await verifyArchive(repo, project.slug);
    assert(project.record.archive?.inventorySha256 === verified.inventorySha256,
      'Public archive record does not match its current seal');
    beforeSeal = readJson(path.join(project.root, MANIFEST));
    for (const entry of beforeSeal.inventory.entries.filter(e => e.kind === 'file')) {
      const member = byHash.get(entry.sha256), file = `${project.workspace}/${entry.path}`;
      if (member && allowedCopy(file, member.clip, project, repo)) candidates.set(file, member);
    }
  } else {
    const sizes = new Set([...byHash.values()].map(x => x.clip.bytes));
    const walk = folder => {
      for (const name of fs.readdirSync(folder).sort()) {
        const file = path.join(folder, name), stat = fs.lstatSync(file);
        assert(!stat.isSymbolicLink() && (stat.isFile() || stat.isDirectory()), 'Unsupported project link or special file');
        const rel = relative(repo, file), inside = rel.slice(project.workspace.length + 1);
        if (stat.isDirectory()) { if (!/^(final|finish)(\/|$)/.test(inside)) walk(file); }
        else if (sizes.has(stat.size) && VIDEO_EXTENSIONS.has(path.extname(name).toLowerCase())) {
          const member = byHash.get(hashFile(file));
          if (member && allowedCopy(rel, member.clip, project, repo)) candidates.set(rel, member);
        }
      }
    };
    walk(project.root);
  }
  const entries = [...candidates].sort(([a], [b]) => a.localeCompare(b)).map(([file, { clip, object }], index) => {
    const stat = fs.lstatSync(safePath(repo, file));
    const entry = { path: file, clipId: clip.id, sha256: clip.sha256, bytes: clip.bytes, md5Hash: object.md5Hash,
      generation: object.generation, object: object.name, mode: stat.mode & 0o7777,
      quarantine: `${receiptPath}/quarantine/${index}${clip.extension}` };
    checkCopy(safePath(repo, file), entry); return entry;
  });
  let afterSeal, afterRecord = project.record;
  if (beforeSeal) {
    const removed = new Set(entries.map(e => e.path));
    const nextInventory = { ...beforeSeal.inventory, entries: beforeSeal.inventory.entries.filter(e => !removed.has(`${project.workspace}/${e.path}`)) };
    afterSeal = { ...beforeSeal, inventory: nextInventory, inventorySha256: sha256(JSON.stringify(nextInventory)) };
    afterRecord = { ...project.record, archive: { ...project.record.archive,
      inventorySha256: afterSeal.inventorySha256, verifiedDate: stamp().slice(0, 10) } };
  }
  fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
  fs.writeFileSync(path.join(directory, 'before-record.json'), project.bytes, { flag: 'wx', mode: 0o600 });
  fs.writeFileSync(path.join(directory, 'after-record.json'), json(afterRecord), { flag: 'wx', mode: 0o600 });
  if (beforeSeal) {
    fs.copyFileSync(path.join(project.root, MANIFEST), path.join(directory, 'before-archive.json'));
    privateJson(path.join(directory, 'after-archive.json'), afterSeal);
  }
  const manifest = { schemaVersion: 1, projectId: project.projectId, workspace: project.workspace,
    recordPath: project.recordPath, backupSetSha256: backupSet.sha256, createdAt: stamp(), entries,
    recordBeforeSha256: sha256(project.bytes), recordAfterSha256: sha256(json(afterRecord)),
    archiveBefore: beforeSeal?.inventorySha256 ?? null, archiveAfter: afterSeal?.inventorySha256 ?? null,
    archiveBeforeSha256: beforeSeal ? hashFile(path.join(directory, 'before-archive.json')) : null,
    archiveAfterSha256: afterSeal ? hashFile(path.join(directory, 'after-archive.json')) : null,
    archiveMode: beforeSeal ? fs.statSync(path.join(project.root, MANIFEST)).mode & 0o7777 : null,
    recoveryVerification: 'skipped-by-standing-user-instruction', dependencyVerification: 'skipped-by-standing-user-instruction',
    preserved: 'Published master and all final/finish deliveries; unbacked bytes, audio, references, metadata, analysis and other project workspaces.' };
  privateJson(path.join(directory, 'manifest.json'), manifest);
  return manifest;
}

/** Caller holds the cloud lock and has freshly verified every backup member. */
export async function offloadPublishedProject(repo, projectId, plan, backupSet, remote) {
  const project = publishedProject(repo, projectId), base = stateRoot(projectId);
  assert(plan.scope?.kind === 'project' && plan.scope.projectId === projectId
    && backupSet.scope?.projectId === projectId, 'Offload backup scope mismatch');
  const ids = plan.clipRecords.map(c => c.clipId).sort();
  assert(ids.length > 0 && new Set(ids).size === ids.length, 'Invalid offload clip membership');
  const archiveLock = safePath(repo, 'data/.workspace-archive.lock');
  const fd = fs.openSync(archiveLock, 'wx', 0o600);
  try { return await clipLocks(repo, ids, async () => {
    const pendingFile = safePath(repo, `${base}/pending.json`);
    let pointer, manifest;
    if (present(pendingFile)) {
      pointer = readJson(pendingFile);
      assert(new RegExp(`^${base}/[a-f0-9-]{36}$`).test(pointer.receipt), 'Invalid pending offload receipt');
      const file = safePath(repo, `${pointer.receipt}/manifest.json`);
      assert(hashFile(file) === pointer.manifestSha256, 'Offload manifest changed');
      manifest = readJson(file);
    } else {
      const receipt = `${base}/${randomUUID()}`;
      manifest = await prepare(repo, project, plan, backupSet, remote, receipt);
      pointer = { receipt, manifestSha256: hashFile(safePath(repo, `${receipt}/manifest.json`)) };
      privateJson(pendingFile, pointer);
    }
    const directory = safePath(repo, pointer.receipt), stateFile = path.join(directory, 'state.json');
    const state = present(stateFile) ? readJson(stateFile) : { phase: 'staging', moved: [], purged: [] };
    const save = () => privateJson(stateFile, { ...state, updatedAt: stamp() });
    assert(manifest.projectId === projectId && manifest.workspace === project.workspace
      && manifest.recordPath === project.recordPath && manifest.backupSetSha256 === backupSet.sha256,
    'Pending offload differs from the current project or verified backup set');
    assert(['staging', 'purging', 'complete'].includes(state.phase), 'Invalid offload transaction phase');
    const currentRecordHash = hashFile(safePath(repo, project.recordPath));
    assert([manifest.recordBeforeSha256, manifest.recordAfterSha256].includes(currentRecordHash),
      'Project record changed during offload; preserve the receipt for reconciliation');
    for (const [index, entry] of manifest.entries.entries()) {
      const clip = readClip(entry.clipId, repo);
      assert(ids.includes(entry.clipId) && allowedCopy(entry.path, clip, project, repo)
        && entry.quarantine === `${pointer.receipt}/quarantine/${index}${clip.extension}`, 'Offload receipt contains an out-of-scope path');
      verifyObject({ name: entry.object, bytes: entry.bytes, sha256: entry.sha256,
        md5Hash: entry.md5Hash, generation: entry.generation }, remote.get(entry.object));
      assert(clip.sha256 === entry.sha256 && clip.bytes === entry.bytes, 'Offload clip identity changed');
    }
    save();
    try {
      for (const entry of manifest.entries) {
        const from = safePath(repo, entry.path), to = safePath(repo, entry.quarantine);
        if (state.phase === 'staging') {
          assert(!(present(from) && present(to)), 'Both offload source and quarantine exist');
          if (present(from)) {
            checkCopy(from, entry); fs.mkdirSync(path.dirname(to), { recursive: true, mode: 0o700 });
            fs.renameSync(from, to);
          }
          assert(present(to), 'Offload copy is missing before purge'); checkCopy(to, entry);
          if (!state.moved.includes(entry.path)) state.moved.push(entry.path);
          save();
        } else {
          assert(!present(from), 'An offloaded copy reappeared before completion');
          if (present(to)) checkCopy(to, entry);
        }
      }
      if (project.archived) {
        const after = readJson(path.join(directory, 'after-archive.json'));
        assert(hashFile(path.join(directory, 'after-archive.json')) === manifest.archiveAfterSha256
          && after.inventorySha256 === manifest.archiveAfter
          && sha256(JSON.stringify(after.inventory)) === manifest.archiveAfter, 'Offload archive snapshot changed');
        assert(JSON.stringify(await inventory(project.root)) === JSON.stringify(after.inventory),
          'Retained archive changed during offload');
        const seal = path.join(project.root, MANIFEST), current = readJson(seal);
        assert([manifest.archiveBeforeSha256, manifest.archiveAfterSha256].includes(hashFile(seal)), 'Archive seal changed during offload');
        if (current.inventorySha256 !== manifest.archiveAfter) {
          privateJson(seal, after); fs.chmodSync(seal, manifest.archiveMode);
        }
        await verifyArchive(repo, project.slug);
        const afterRecord = fs.readFileSync(path.join(directory, 'after-record.json'));
        assert(sha256(afterRecord) === manifest.recordAfterSha256, 'Offload record snapshot changed');
        if (hashFile(safePath(repo, project.recordPath)) !== manifest.recordAfterSha256) {
          const file = safePath(repo, project.recordPath), mode = fs.statSync(file).mode & 0o7777;
          privateJson(file, JSON.parse(afterRecord)); fs.chmodSync(file, mode);
        }
      }
      assert(hashFile(safePath(project.root, project.master.path)) === project.master.sha256, 'Published master changed during offload');
      state.phase = 'purging'; save();
      for (const entry of manifest.entries) {
        const file = safePath(repo, entry.quarantine);
        if (present(file)) { checkCopy(file, entry); fs.unlinkSync(file); }
        if (!state.purged.includes(entry.path)) state.purged.push(entry.path);
        save();
      }
      state.phase = 'complete'; save();
      const result = { status: 'complete', projectId, receipt: pointer.receipt, backupSetSha256: backupSet.sha256,
        clips: new Set(manifest.entries.map(e => e.clipId)).size, removedFiles: manifest.entries.length,
        removedLogicalBytes: manifest.entries.reduce((n, e) => n + e.bytes, 0),
        archiveInventorySha256: manifest.archiveAfter, publishedMasterPreserved: true,
        recoveryVerification: manifest.recoveryVerification, dependencyVerification: manifest.dependencyVerification };
      privateJson(path.join(directory, 'completion.json'), result);
      privateJson(safePath(repo, `${base}/last.json`), result);
      fs.unlinkSync(pendingFile); return result;
    } catch (error) {
      state.lastError = error.message; save();
      throw new Error(`Post-publication offload interrupted; rerun the same sync to resume. Receipt: ${pointer.receipt}. ${error.message}`);
    }
  }); } finally { fs.closeSync(fd); fs.unlinkSync(archiveLock); }
}
