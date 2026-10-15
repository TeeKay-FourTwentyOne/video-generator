/** Approved duplicate reclamation only. This never removes the last local copy. */
import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { REPO, safePath, readJson, readClip, listClips, listUses, mediaPath, hashFile, resolveClip } from './clip-library.mjs';
import { assert, validHash, verifyFile, fileIdentity, privateJson, sha, now, withLock } from './clip-analysis-store.mjs';
import { locked } from './clip-cloud.mjs';
import { verifySet, validateBackupSet } from './clip-backup-set.mjs';

const SCOPE = 'canonical-duplicates-with-retained-local-originals';
const decisionKeys = ['activeEditsReviewed', 'archivesReviewed', 'originalPathsReviewed', 'alternatesReviewed', 'sharedSourcesReviewed'];
function allocation(file) {
  const result = spawnSync('python3', [path.join(REPO, 'tools/production/clip-disk-usage.py')],
    { input: JSON.stringify([file]), encoding: 'utf8', timeout: 30000, maxBuffer: 1048576 });
  assert(result.status === 0, 'Allocation measurement failed; inspect the file before proposing removal');
  const values = JSON.parse(result.stdout);
  assert(values.length === 1 && (values[0].privateBytes === null || Number.isSafeInteger(values[0].privateBytes)
    && values[0].privateBytes >= 0), 'Invalid exclusive allocation result');
  return values[0];
}
function currentDigests(repo) {
  return { catalogSha256: sha(listClips(repo)), usesSha256: sha(listUses(repo)),
    locationsSha256: sha(readJson(safePath(repo, 'data/clips/locations.json'))) };
}
function checkAudit(reference, set, repo) {
  assert(reference?.path?.startsWith('data/'), 'Provide the private dependency audit');
  const file = safePath(repo, reference.path); verifyFile(file, reference);
  assert(set.objects.some(o => o.sha256 === reference.sha256 && o.bytes === reference.bytes
    && o.kind === 'analysis-support' && o.restorePaths?.includes(reference.path)), 'Dependency audit must be recoverable from this backup set');
  const audit = readJson(file), digests = currentDigests(repo);
  assert(Object.keys(digests).every(k => audit[k] === digests[k]), 'Dependency audit is stale');
  return audit;
}
function checkRecovery(recoveryRef, accessRef, set, setHash, repo) {
  const readEvidence = ref => {
    assert(ref?.path?.startsWith('data/workspace/'), 'Provide private recovery evidence');
    const file = safePath(repo, ref.path); verifyFile(file, ref); return readJson(file);
  };
  const recovery = readEvidence(recoveryRef), access = readEvidence(accessRef);
  assert(recovery.backupSetSha256 === setHash && ['emptyRootRecovery', 'hashesVerified', 'fullDecode', 'searchRebuilt',
    'normalFetchVerified', 'editRangeVerified', 'sourceRecovered'].every(k => recovery[k] === true)
    && recovery.support?.transitiveEvidenceVerified === true
    && Number.isFinite(Date.parse(recovery.restoredAt)) && Date.parse(recovery.restoredAt) <= Date.now(),
  'Current backup set needs independent source, evidence, search, decode, fetch and edit recovery evidence');
  assert(access.independentlyRecoverable === true && Number.isFinite(Date.parse(access.reviewedAt))
    && Date.parse(access.reviewedAt) <= Date.now(), 'Independent recovery access is not attested');
  assert(set.objects.some(o => o.kind === 'analysis-support' && o.sha256 === accessRef.sha256
    && o.bytes === accessRef.bytes && o.restorePaths?.includes(accessRef.path)), 'Access attestation is not backed up');
}
function checkEntry(entry, set, audit, repo) {
  const clip = readClip(entry.clipId, repo), source = mediaPath(clip, repo);
  assert(entry.path === path.relative(repo, source) && entry.sha256 === clip.sha256 && entry.bytes === clip.bytes,
    'Cleanup target differs from the canonical master');
  verifyFile(source, entry);
  const member = set.objects.find(o => o.kind === 'media' && o.clipId === clip.id);
  assert(member && member.sha256 === entry.sha256 && member.bytes === entry.bytes && member.generation === entry.generation,
    'Cleanup master is not the pinned backup member');
  assert(set.clips.find(c => c.clipId === clip.id)?.catalogSha256 === sha(clip), 'Backed catalog differs from current clip');
  const decision = audit.clips?.find(c => c.clipId === clip.id);
  assert(decision && decisionKeys.every(k => decision[k] === true) && Array.isArray(decision.canonicalPathReferences)
    && decision.canonicalPathReferences.length === 0, 'Canonical path dependencies remain unresolved');
  for (const use of listUses(repo).filter(u => u.clipId === clip.id && u.status === 'planned'))
    assert(decision.pendingUses?.some(p => p.useId === use.id && p.resolution === 'verified-local-copy'), 'Planned use is not covered by duplicate recovery');
  const locations = readJson(safePath(repo, 'data/clips/locations.json')).locations;
  assert(Array.isArray(entry.retainedCopies) && entry.retainedCopies.length > 0, 'A retained local original is required');
  for (const copy of entry.retainedCopies) {
    assert(copy.path !== entry.path && !copy.path.startsWith('data/clips/') && locations[copy.path]?.id === clip.id
      && locations[copy.path]?.bytes === clip.bytes && copy.sha256 === clip.sha256 && copy.bytes === clip.bytes, 'Unverified retained-copy mapping');
    verifyFile(safePath(repo, copy.path), copy);
  }
  return { clip, source };
}
function readSet(hash, repo) {
  assert(validHash(hash), 'Provide a complete backup-set identity');
  const file = safePath(repo, `data/clips/cloud/backup-sets/${hash}.json`);
  assert(hashFile(file) === hash, 'Backup-set hash mismatch'); return validateBackupSet(readJson(file));
}
export async function planDuplicates(policy, output, repo = REPO, options = {}) {
  assert(policy?.schemaVersion === 1 && policy.scope === SCOPE && Array.isArray(policy.clipIds)
    && policy.clipIds.length > 0 && new Set(policy.clipIds).size === policy.clipIds.length, 'Select an explicit duplicate-only batch');
  assert(output.startsWith('data/workspace/') && output.endsWith('.json'), 'Cleanup manifest must stay in the private workspace');
  const target = safePath(repo, output); assert(!fs.existsSync(target), 'Use a new immutable cleanup manifest');
  const verification = await verifySet(policy.backupSetSha256, repo, options);
  return locked(repo, async () => {
    const set = readSet(policy.backupSetSha256, repo), audit = checkAudit(policy.dependencyAudit, set, repo);
    checkRecovery(policy.recoveryEvidence, policy.accessEvidence, set, policy.backupSetSha256, repo);
    const locations = readJson(safePath(repo, 'data/clips/locations.json')).locations, entries = [];
    for (const id of policy.clipIds) {
      const c = readClip(id, repo), file = mediaPath(c, repo), stat = fs.lstatSync(file);
      const retainedCopies = [];
      for (const [relative, mapping] of Object.entries(locations).sort(([a], [b]) => a.localeCompare(b))) {
        if (mapping.id !== id || relative.startsWith('data/clips/') || mapping.bytes !== c.bytes) continue;
        try { verifyFile(safePath(repo, relative), c); retainedCopies.push({ path: relative, sha256: c.sha256, bytes: c.bytes }); } catch { /* Keep changed copies out of the proposal. */ }
      }
      const entry = { clipId: id, path: path.relative(repo, file), sha256: c.sha256, bytes: c.bytes,
        allocation: allocation(file), allocatedBytes: stat.blocks * 512, generation: set.objects.find(o => o.kind === 'media' && o.clipId === id)?.generation,
        device: stat.dev, inode: stat.ino, retainedCopies };
      checkEntry(entry, set, audit, repo); entries.push(entry);
    }
    const manifest = { schemaVersion: 1, scope: SCOPE, createdAt: now(), backupSetSha256: policy.backupSetSha256,
      dependencyAudit: policy.dependencyAudit, recoveryEvidence: policy.recoveryEvidence, accessEvidence: policy.accessEvidence,
      digests: currentDigests(repo), verification, entries,
      logicalBytes: entries.reduce((n, e) => n + e.bytes, 0), allocatedBytes: entries.reduce((n, e) => n + e.allocatedBytes, 0),
      estimatedReclaimableBytes: entries.every(e => e.allocation.privateBytes !== null) ? entries.reduce((n, e) => n + e.allocation.privateBytes, 0) : null,
      limitations: 'Allocated blocks may be shared by filesystem clones or snapshots; actual free space must be measured after removal.',
      retained: 'Every listed historical original, catalog, preview, analysis, review, creation snapshot and cloud object.',
      semanticQualification: 'Deferred only for explicitly approved duplicate reclamation; this is not last-local-copy readiness.',
      authorization: 'Approval must name the exact SHA-256 of this manifest. No removal has occurred.' };
    privateJson(target, manifest, true);
    return { manifest: output, ...fileIdentity(target), clips: entries.length, logicalBytes: manifest.logicalBytes,
      allocatedBytes: manifest.allocatedBytes, estimatedReclaimableBytes: manifest.estimatedReclaimableBytes };
  });
}
export async function applyDuplicates(manifestPath, approvalPath, repo = REPO, options = {}) {
  assert(manifestPath.startsWith('data/workspace/') && approvalPath.startsWith('data/workspace/'), 'Cleanup inputs must stay private');
  const manifestFile = safePath(repo, manifestPath), approvalFile = safePath(repo, approvalPath);
  const manifestHash = hashFile(manifestFile), manifest = readJson(manifestFile), approval = readJson(approvalFile);
  assert(approval.schemaVersion === 1 && approval.approvedBy === 'user' && approval.scope === SCOPE
    && approval.manifestSha256 === manifestHash && Number.isFinite(Date.parse(approval.approvedAt))
    && Date.parse(approval.approvedAt) <= Date.now(), 'Explicit approval of this exact duplicate manifest is required');
  assert(manifest.schemaVersion === 1 && manifest.scope === SCOPE && Array.isArray(manifest.entries) && manifest.entries.length > 0
    && new Set(manifest.entries.map(e => e.path)).size === manifest.entries.length, 'Invalid duplicate cleanup manifest');
  const verification = await verifySet(manifest.backupSetSha256, repo, options);
  return locked(repo, async () => {
    assert(hashFile(manifestFile) === manifestHash, 'Approved manifest changed');
    const set = readSet(manifest.backupSetSha256, repo), audit = checkAudit(manifest.dependencyAudit, set, repo);
    checkRecovery(manifest.recoveryEvidence, manifest.accessEvidence, set, manifest.backupSetSha256, repo);
    assert(sha(currentDigests(repo)) === sha(manifest.digests), 'Catalog or dependency mappings changed after approval');
    for (const entry of manifest.entries) checkEntry(entry, set, audit, repo);
    const receiptPath = `data/clips/cloud/cleanup/${manifestHash}-${randomUUID()}.jsonl`, file = safePath(repo, receiptPath);
    fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
    const fd = fs.openSync(file, 'wx', 0o600), receipt = event => { fs.writeSync(fd, JSON.stringify({ at: now(), ...event }) + '\n'); fs.fsyncSync(fd); };
    const free = () => { const s = fs.statfsSync(repo); return s.bavail * s.bsize; }, before = free();
    let removed = 0;
    try {
      receipt({ event: 'approved', manifestPath, manifestSha256: manifestHash, approvalSha256: hashFile(approvalFile), verification, freeBytes: before });
      for (const entry of manifest.entries) await withLock(repo, entry.clipId, async () => {
        const writerLock = safePath(repo, `data/clips/.locks/${entry.clipId}`); fs.mkdirSync(path.dirname(writerLock), { recursive: true });
        fs.mkdirSync(writerLock); // A concurrent catalog/import writer blocks removal.
        try {
          const { source } = checkEntry(entry, set, audit, repo), stat = fs.lstatSync(source);
          assert(stat.dev === entry.device && stat.ino === entry.inode, 'Master was replaced after the cleanup proposal');
          const quarantine = `${source}.cleanup-${randomUUID()}`;
          receipt({ event: 'rename-intent', clipId: entry.clipId, path: entry.path, quarantine: path.relative(repo, quarantine), sha256: entry.sha256, bytes: entry.bytes });
          fs.renameSync(source, quarantine);
          try {
            verifyFile(quarantine, entry);
            assert(entry.retainedCopies.some(c => resolveClip(entry.clipId, repo) === safePath(repo, c.path)), 'Local clip resolution failed after staging removal');
            for (const copy of entry.retainedCopies) verifyFile(safePath(repo, copy.path), copy);
            fs.unlinkSync(quarantine); removed++;
            receipt({ event: 'removed', clipId: entry.clipId, path: entry.path, sha256: entry.sha256, bytes: entry.bytes });
          } catch (error) {
            if (fs.existsSync(quarantine) && !fs.existsSync(source)) { fs.linkSync(quarantine, source); fs.unlinkSync(quarantine); }
            throw error;
          }
        } finally { fs.rmdirSync(writerLock); }
      });
      const after = free(); receipt({ event: 'complete', removed, freeBytes: after, measuredFreeSpaceChange: after - before });
      return { removed, receipt: receiptPath, freeBytesBefore: before, freeBytesAfter: after, measuredFreeSpaceChange: after - before };
    } catch (error) { receipt({ event: 'stopped', removed, reason: error.message }); throw error; }
    finally { fs.closeSync(fd); }
  });
}
export async function cleanupMain(verb, args, repo = REPO) {
  if (verb === 'cleanup-plan' && args.length === 2) return planDuplicates(readJson(safePath(repo, args[0])), args[1], repo);
  if (verb === 'cleanup-apply' && args.length === 2) return applyDuplicates(args[0], args[1], repo);
  throw new Error('Invalid duplicate cleanup command');
}
