/** Private, immutable analysis evidence. No provider or cloud dependencies. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { randomUUID } from 'node:crypto';
import { REPO, safePath, canonical, digest, hashFile, readJson, assertId } from './clip-library.mjs';

export const VERSION = 'clip-analysis/1';
export const BASELINE = ['evidence', 'probe', 'decode', 'timing', 'signal', 'audio', 'preview'];
export const SEMANTIC = ['ocr', 'transcript', 'observations', 'embeddings', 'audio-content'];
export const STEPS = [...BASELINE, ...SEMANTIC];
export const STATES = ['pending', 'running', 'complete', 'not-applicable', 'failed', 'needs-review'];
export const sha = value => digest(JSON.stringify(canonical(value)));
export const now = () => new Date().toISOString();
export const validHash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
export const assert = (ok, message) => { if (!ok) throw new Error(message); };
export function privateJson(file, value, immutable = false) {
  const bytes = Buffer.from(JSON.stringify(value, null, 2) + '\n');
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  if (fs.existsSync(file) && fs.readFileSync(file).equals(bytes)) return;
  const tmp = `${file}.${randomUUID()}.tmp`;
  try {
    fs.writeFileSync(tmp, bytes, { flag: 'wx', mode: 0o600 });
    if (immutable) fs.linkSync(tmp, file); else fs.renameSync(tmp, file);
  } finally { fs.rmSync(tmp, { force: true }); }
}
export function artifactPath(root, relative) {
  assert(typeof relative === 'string' && /^[A-Za-z0-9_./-]+$/.test(relative)
    && relative.split('/').every(p => p && p !== '.' && p !== '..'), 'Unsafe analysis artifact path');
  return safePath(root, relative);
}
export function runPath(id, runId, repo = REPO) {
  assertId(id); assert(/^run_[a-f0-9]{64}$/.test(runId ?? ''), 'Invalid analysis run ID');
  return safePath(repo, `data/clips/${id}/analysis/${runId}`);
}
export function fileIdentity(file) { return { sha256: hashFile(file), bytes: fs.statSync(file).size }; }
export function verifyFile(file, expected) {
  assert(fs.lstatSync(file).isFile(), 'Analysis artifact must be a regular file');
  const actual = fileIdentity(file);
  assert(actual.sha256 === expected.sha256 && actual.bytes === expected.bytes, 'Analysis artifact hash or size mismatch');
  return actual;
}
export function filesUnder(dir) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  for (const name of fs.readdirSync(dir).sort()) {
    const f = artifactPath(dir, name), st = fs.lstatSync(f);
    if (st.isDirectory()) out.push(...filesUnder(f).map(p => `${name}/${p}`));
    else { assert(st.isFile(), 'Unsupported analysis artifact'); out.push(name); }
  }
  return out;
}
export function configFor(input = {}) {
  const defaults = { schemaVersion: 1, profile: 'baseline-v1', required: BASELINE, threads: 2,
    limits: { timeoutSeconds: 1800, maxOutputBytes: 1024 ** 3, minFreeBytes: 8 * 1024 ** 3, maxFrames: 2000000 },
    signal: { sceneThreshold: 10, blackDuration: 0.1, blackPixelThreshold: 0.1, freezeSeconds: 1, freezeNoiseDb: -60, silenceDb: -50, silenceSeconds: 0.2 },
    preview: { maxSide: 640, gridSeconds: 1, maxKeyframes: 120, crf: 30, videoKbps: 600, audioKbps: 64 },
    adapters: {}, evidence: [] };
  assert(input && typeof input === 'object' && !Array.isArray(input), 'Invalid analysis configuration');
  assert(Object.keys(input).every(k => Object.hasOwn(defaults, k)), 'Unknown analysis setting');
  const config = { ...defaults, ...input };
  for (const k of ['limits', 'signal', 'preview']) {
    assert(Object.keys(input[k] ?? {}).every(key => Object.hasOwn(defaults[k], key)), `Unknown ${k} setting`);
    config[k] = { ...defaults[k], ...input[k] };
  }
  assert(config.schemaVersion === 1 && /^[a-z0-9-]+$/.test(config.profile ?? ''), 'Invalid analysis profile');
  assert(Array.isArray(config.required) && BASELINE.every(s => config.required.includes(s))
    && config.required.every(s => STEPS.includes(s)) && new Set(config.required).size === config.required.length, 'Invalid required analysis passes');
  assert(Number.isInteger(config.threads) && config.threads >= 1 && config.threads <= 16, 'Invalid analysis CPU limit');
  for (const [key, value] of Object.entries(config.limits)) assert(Number.isSafeInteger(value) && value > 0, `Invalid analysis limit: ${key}`);
  assert(config.preview.maxSide >= 64 && config.preview.maxSide <= 1920 && config.preview.maxSide % 2 === 0
    && Number.isInteger(config.preview.maxKeyframes) && config.preview.maxKeyframes >= 2 && config.preview.maxKeyframes <= 1000
    && config.preview.gridSeconds > 0 && config.preview.crf >= 0 && config.preview.crf <= 51
    && config.preview.videoKbps > 0 && config.preview.audioKbps > 0, 'Invalid preview limits');
  assert(Object.values(config.signal).every(Number.isFinite) && config.signal.sceneThreshold >= 0 && config.signal.sceneThreshold <= 100
    && config.signal.blackPixelThreshold >= 0 && config.signal.blackPixelThreshold <= 1 && config.signal.blackDuration >= 0
    && config.signal.freezeSeconds > 0 && config.signal.freezeNoiseDb < 0 && config.signal.silenceDb < 0 && config.signal.silenceSeconds > 0, 'Invalid signal thresholds');
  assert(config.adapters && typeof config.adapters === 'object' && !Array.isArray(config.adapters)
    && Object.keys(config.adapters).every(k => SEMANTIC.includes(k)), 'Unknown semantic adapter');
  assert(Array.isArray(config.evidence), 'Expected an explicit evidence allowlist');
  for (const e of config.evidence) {
    assertId(e.clipId);
    assert(typeof e.path === 'string' && e.path.startsWith('data/') && !e.path.startsWith('data/clips/')
      && /\.(json|jsonl|txt|md|yaml|yml|py|mjs|js|srt|vtt|csv|tsv)$/.test(e.path)
      && validHash(e.sha256) && ['verified-hash', 'unambiguous-historical-mapping'].includes(e.join)
      && typeof e.reason === 'string' && e.reason.trim(), 'Invalid adjacent evidence allowlist entry');
  }
  return canonical(config);
}
export function runIdentity(clip, config, tools) {
  const input = { clipId: clip.id, sha256: clip.sha256, bytes: clip.bytes };
  const identity = { schemaVersion: 1, extractor: VERSION, input, config, tools };
  return { ...identity, runId: `run_${sha(identity)}`, configSha256: sha(config) };
}
export function validateManifest(m) {
  assert(m?.schemaVersion === 1 && m.extractor === VERSION, 'Unsupported analysis manifest');
  assertId(m.input?.clipId);
  assert(m.input.clipId === `clip_${m.input.sha256}` && Number.isSafeInteger(m.input.bytes) && m.input.bytes > 0, 'Invalid analysis input');
  configFor(m.config); // Validate without adding future defaults to historical run identities.
  const identity = runIdentity({ id: m.input.clipId, ...m.input }, m.config, m.tools);
  assert(m.runId === identity.runId && m.configSha256 === identity.configSha256, 'Analysis configuration or run identity mismatch');
  assert(m.status === 'complete' && m.inputVerifiedBefore === true && m.inputVerifiedAfter === true, 'Incomplete analysis manifest');
  assert(m.steps && Object.keys(m.steps).length === STEPS.length && STEPS.every(s => Object.hasOwn(m.steps, s)), 'Missing analysis step states');
  assert(Array.isArray(m.artifacts) && m.artifacts.length > 0, 'Missing analysis artifacts');
  const paths = new Set();
  for (const a of m.artifacts) {
    artifactPath('/analysis-validation-root', a.path);
    assert(STEPS.includes(a.step) && a.path.startsWith(`steps/${a.step}/`) && validHash(a.sha256)
      && Number.isSafeInteger(a.bytes) && a.bytes >= 0 && !paths.has(a.path), 'Invalid or duplicate analysis artifact');
    paths.add(a.path);
  }
  for (const [step, state] of Object.entries(m.steps)) {
    assert(STATES.includes(state.state) && !['running', 'failed'].includes(state.state), 'Unfinished step cannot be sealed');
    if (state.state !== 'complete') assert(typeof state.reason === 'string' && state.reason.trim(), 'Analysis state requires a reason');
    if (m.config.required.includes(step)) assert(['complete', 'not-applicable', 'needs-review'].includes(state.state), 'Required analysis pass is unrun');
    if (state.state !== 'pending') assert(paths.has(`steps/${step}/receipt.json`), 'Missing step completion receipt');
  }
  assert(validHash(m.catalogSha256) && m.catalogSha256 === m.tools.catalogEvidenceSha256 && Array.isArray(m.timeBases) && m.timeBases.every(s => Number.isInteger(s.streamIndex)
    && /^\d+\/[1-9]\d*$/.test(s.timeBase)), 'Invalid analysis source timing');
  return m;
}
export function verifyRun(id, runId, repo = REPO) {
  const dir = runPath(id, runId, repo), m = validateManifest(readJson(path.join(dir, 'manifest.json')));
  assert(m.input.clipId === id && m.runId === runId, 'Analysis manifest path disagrees with identity');
  for (const a of m.artifacts) verifyFile(artifactPath(dir, a.path), a);
  for (const [step, state] of Object.entries(m.steps)) {
    if (state.state === 'pending') continue;
    const receipt = readJson(artifactPath(dir, `steps/${step}/receipt.json`));
    assert(sha(receipt) === sha(state) && receipt.runId === m.runId && receipt.step === step && receipt.inputSha256 === m.input.sha256,
      'Step receipt disagrees with the sealed analysis state');
    const declared = m.artifacts.filter(a => a.step === step && a.path !== `steps/${step}/receipt.json`);
    assert(Array.isArray(receipt.outputs) && declared.length === receipt.outputs.length && receipt.outputs.every(o => declared.some(a =>
      a.path === `steps/${step}/${o.path}` && a.sha256 === o.sha256 && a.bytes === o.bytes)), 'Step receipt output inventory disagrees with the manifest');
  }
  const actual = filesUnder(path.join(dir, 'steps')).map(p => `steps/${p}`);
  assert(actual.length === m.artifacts.length && actual.every(p => m.artifacts.some(a => a.path === p)), 'Undeclared analysis payload');
  return m;
}
export function listRuns(id, repo = REPO) {
  assertId(id); const dir = safePath(repo, `data/clips/${id}/analysis`);
  return fs.existsSync(dir) ? fs.readdirSync(dir).filter(n => /^run_[a-f0-9]{64}$/.test(n)
    && fs.existsSync(artifactPath(dir, `${n}/manifest.json`))).sort() : [];
}
export async function withLock(repo, key, action, { recover = false } = {}) {
  assert(/^[a-z0-9_-]+$/.test(key), 'Invalid analysis lock');
  const dir = safePath(repo, `data/clips/analysis/locks/${key}`);
  fs.mkdirSync(path.dirname(dir), { recursive: true, mode: 0o700 });
  if (recover && fs.existsSync(dir)) {
    const owner = readJson(path.join(dir, 'owner.json'));
    assert(owner.host === os.hostname() && Number.isSafeInteger(owner.pid) && owner.pid > 0, 'Cannot establish stale lock ownership');
    let alive = true;
    try { process.kill(owner.pid, 0); } catch (e) { if (e.code === 'ESRCH') alive = false; }
    assert(!alive, 'Analysis worker still owns this lock');
    fs.renameSync(dir, `${dir}-recovered-${randomUUID()}`);
  }
  try { fs.mkdirSync(dir); } catch (e) { if (e.code === 'EEXIST') throw new Error('Analysis lock exists; use --recover only after the prior worker stops'); throw e; }
  privateJson(path.join(dir, 'owner.json'), { pid: process.pid, host: os.hostname(), startedAt: now() });
  try { return await action(); } finally { fs.rmSync(dir, { recursive: true }); }
}
export function checkSpace(dir, limits) {
  const s = fs.statfsSync(dir);
  assert(s.bavail * s.bsize >= limits.minFreeBytes, 'Analysis stopped at the free-space reserve');
}
