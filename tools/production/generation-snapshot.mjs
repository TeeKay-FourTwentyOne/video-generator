/** Private creation-time evidence. No provider calls, credentials, prices or media payloads. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';

const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
  ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
export const snapshotHash = snapshot => createHash('sha256').update(JSON.stringify(canonical(snapshot))).digest('hex');

export function readSnapshot(file) {
  let snapshot;
  // Parser diagnostics can quote private prompt text. Report the problem without those excerpts.
  try { snapshot = JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch { throw new Error('Generation snapshot is unreadable; restore original request evidence'); }
  return validateSnapshot(snapshot);
}

export function validateSnapshot(snapshot) {
  if (snapshot?.schemaVersion !== 1 || snapshot.evidence !== 'creation-snapshot'
      || typeof snapshot.prompt !== 'string' || !snapshot.prompt.trim()
      || typeof snapshot.provider !== 'string' || !snapshot.provider
      || !(snapshot.model === null || typeof snapshot.model === 'string' && !!snapshot.model)
      || !(snapshot.requestedModel === null || typeof snapshot.requestedModel === 'string')
      || !(snapshot.seed === null || Number.isSafeInteger(snapshot.seed))
      || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(snapshot.requestId ?? '')
      || !/^[a-f0-9]{64}$/.test(snapshot.fingerprint ?? '')
      || typeof snapshot.createdAt !== 'string' || !Number.isFinite(Date.parse(snapshot.createdAt))
      || !snapshot.parameters || typeof snapshot.parameters !== 'object' || Array.isArray(snapshot.parameters)
      || !Array.isArray(snapshot.sources)
      || snapshot.sources.some(s => !s || typeof s.role !== 'string' || !s.role || !/^[a-f0-9]{64}$/.test(s.sha256)
        || !Number.isSafeInteger(s.bytes) || s.bytes < 1))
    throw new Error('Invalid generation snapshot; preserve original request evidence');
  return snapshot;
}

/** Atomic, no-clobber install. A repeat may verify identical evidence, never replace it. */
export function writeSnapshot(file, snapshot) {
  validateSnapshot(snapshot);
  const verify = () => {
    if (snapshotHash(readSnapshot(file)) !== snapshotHash(snapshot))
      throw new Error('Generation snapshot conflicts with saved evidence; never overwrite it');
  };
  if (fs.existsSync(file)) { verify(); return; }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.${randomUUID()}.tmp`;
  try {
    const fd = fs.openSync(tmp, 'wx', 0o600);
    try { fs.writeFileSync(fd, JSON.stringify(snapshot, null, 2) + '\n'); fs.fsyncSync(fd); }
    finally { fs.closeSync(fd); }
    fs.chmodSync(tmp, 0o400);
    try { fs.linkSync(tmp, file); }
    catch (e) { if (e.code !== 'EEXIST') throw e; verify(); }
  } finally { fs.rmSync(tmp, { force: true }); }
}

export function snapshotPath(budgetFile, requestId) {
  if (typeof requestId !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(requestId))
    throw new Error('Generation snapshot needs a stable request ID');
  return path.join(path.dirname(budgetFile), 'operations', `${requestId}.request.json`);
}

/** Call after reservation but before auth, uploads or generation. Pass resolved controls. */
export function saveGenerationSnapshot(budgetFile, input) {
  const snapshot = JSON.parse(JSON.stringify({ schemaVersion: 1, evidence: 'creation-snapshot',
    provider: input.provider, requestId: input.requestId, fingerprint: input.fingerprint,
    createdAt: new Date().toISOString(), prompt: input.prompt, requestedModel: input.requestedModel ?? null,
    model: input.model ?? null, seed: input.seed ?? null, parameters: input.parameters,
    sources: input.sources ?? [], api: input.api ?? null }));
  writeSnapshot(snapshotPath(budgetFile, input.requestId), snapshot);
  return snapshot;
}

/** Missing snapshots are historical unknowns; never manufacture one during recovery. */
export function readGenerationSnapshot(budgetFile, requestId, expected = {}) {
  const file = snapshotPath(budgetFile, requestId);
  if (!fs.existsSync(file)) {
    if (expected.snapshotSha256) throw new Error('Recorded generation snapshot is missing; restore original evidence');
    return undefined;
  }
  const snapshot = readSnapshot(file);
  if (snapshot.requestId !== requestId || ['provider', 'fingerprint', 'model'].some(k => expected[k] !== undefined && expected[k] !== snapshot[k])
      || expected.snapshotSha256 && expected.snapshotSha256 !== snapshotHash(snapshot))
    throw new Error('Generation snapshot does not match the saved operation');
  return snapshot;
}
