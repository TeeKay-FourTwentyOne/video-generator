/** Explicit recovery mappings and transitive evidence closure. No network. */
import fs from 'node:fs';
import path from 'node:path';
import { safePath, readJson, readClip, mediaPath } from './clip-library.mjs';
import { assert, validHash, verifyFile, privateJson, verifyRun, configReference } from './clip-analysis-store.mjs';

export const SUPPORT_ROLES = ['dependency-audit', 'pilot-review', 'access-attestation', 'retention-plan',
  'historical-locations', 'qualification-evidence', 'source-recovery', 'relationship-evidence', 'recovery-policy'];
export const SUPPORT_EXTENSION = /\.(json|jsonl|txt|log|md|mjs|py|gz|jpg|png|html|mp4|mov|webm|mkv|m4v|avi)$/;
export function supportPath(relative) {
  assert(typeof relative === 'string' && (relative.startsWith('data/workspace/')
    || relative.startsWith('data/clips/analysis/') || relative === 'data/clips/locations.json')
    && relative.split('/').every(p => p && p !== '.' && p !== '..')
    && SUPPORT_EXTENSION.test(relative), 'Unsafe recovery support path');
  return relative;
}
export function evidenceReferences(value) {
  const found = [];
  const visit = v => {
    if (!v || typeof v !== 'object') return;
    // Absolute runtime pins describe separately provisioned dependencies, not
    // portable evidence. Explicit data paths must close over the backup set.
    if (typeof v.path === 'string' && v.path.startsWith('data/') && validHash(v.sha256)) found.push(v);
    for (const child of Object.values(v)) visit(child);
  };
  visit(value); return found;
}
export function verifySupportClosure(objects, repo, allObjects = objects) {
  const support = objects.filter(o => o.kind === 'analysis-support'), byPath = new Map();
  for (const o of support) for (const p of o.restorePaths ?? []) {
    supportPath(p);
    assert(!byPath.has(p), 'Conflicting support recovery paths'); byPath.set(p, o);
    verifyFile(safePath(repo, p), o);
  }
  // Qualification fixtures may have their own isolated catalog and library.
  // Keep that namespace intact and require its entire declared run, not just a
  // JSON report naming a manifest that happens to exist on the original disk.
  const fixtureManifests = [];
  for (const [relative, member] of byPath) {
    const match = /^(data\/workspace\/.+)\/data\/clips\/(clip_[a-f0-9]{64})\/analysis\/(run_[a-f0-9]{64})\/manifest\.json$/.exec(relative);
    if (!match) continue;
    const [, prefix, clipId, runId] = match, root = safePath(repo, prefix);
    const clip = readClip(clipId, root), manifest = verifyRun(clipId, runId, root);
    const requireMember = (p, identity) => {
      const entry = byPath.get(`${prefix}/${p}`);
      assert(entry && (!identity || entry.sha256 === identity.sha256 && entry.bytes === identity.bytes),
        'Nested qualification fixture dependency is missing from the explicit recovery mapping');
      verifyFile(safePath(root, p), entry);
    };
    requireMember(`catalog/clips/${clipId}.json`);
    requireMember(path.relative(root, mediaPath(clip, root)), manifest.input);
    for (const artifact of manifest.artifacts) requireMember(`data/clips/${clipId}/analysis/${runId}/${artifact.path}`, artifact);
    const reference = configReference(readJson(safePath(repo, relative)));
    if (reference) requireMember(reference.path, reference);
    fixtureManifests.push({ clipId, runId, sha256: member.sha256, prefix });
  }
  for (const [source] of byPath) {
    if (!source.endsWith('.json')) continue;
    const record = readJson(safePath(repo, source));
    const namespace = fixtureManifests.filter(m => source.startsWith(`${m.prefix}/`)).sort((a, b) => b.prefix.length - a.prefix.length)[0]?.prefix;
    const checkIdentities = value => {
      if (!value || typeof value !== 'object') return;
      if (value.clipId && value.runId && value.manifestSha256) {
        assert([...allObjects.filter(m => m.kind === 'analysis-manifest'), ...fixtureManifests].some(m => m.clipId === value.clipId
          && m.runId === value.runId && m.sha256 === value.manifestSha256), 'Referenced analysis manifest is missing from the complete backup');
        if (value.reviewSha256) assert(allObjects.some(m => m.kind === 'analysis-review' && m.clipId === value.clipId
          && m.runId === value.runId && m.reviewSha256 === value.reviewSha256), 'Referenced human review is missing from the complete backup');
      }
      for (const child of Object.values(value)) checkIdentities(child);
    };
    checkIdentities(record);
    for (const ref of evidenceReferences(record)) {
      const relative = namespace ? `${namespace}/${ref.path}` : ref.path;
      const member = byPath.get(relative);
      assert(member && member.sha256 === ref.sha256 && (ref.bytes === undefined || member.bytes === ref.bytes),
        'Transitive support evidence is missing from the explicit recovery mapping');
      verifyFile(safePath(repo, relative), member);
    }
  }
  return { files: support.length, restoredPaths: byPath.size, transitiveEvidenceVerified: true };
}
export function installSupport(objects, repo, objectTarget, allObjects = objects) {
  const files = [];
  for (const o of objects.filter(o => o.kind === 'analysis-support')) {
    const source = safePath(repo, objectTarget(o)); verifyFile(source, o);
    for (const relative of o.restorePaths ?? []) {
      const target = safePath(repo, supportPath(relative));
      fs.mkdirSync(path.dirname(target), { recursive: true, mode: 0o700 });
      if (fs.existsSync(target)) verifyFile(target, o); else fs.copyFileSync(source, target, fs.constants.COPYFILE_EXCL);
      files.push({ path: relative, sha256: o.sha256, bytes: o.bytes, role: o.role });
    }
  }
  const result = verifySupportClosure(objects, repo, allObjects);
  if (files.length) privateJson(safePath(repo, 'data/clips/analysis/recovered-support.json'), { schemaVersion: 1, files }, true);
  return result;
}
