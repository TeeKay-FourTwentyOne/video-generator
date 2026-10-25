/** Explicit private Cloud Storage backup. Ordinary clip commands remain offline. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import { gzipSync } from 'node:zlib';
import { spawn } from 'node:child_process';
import { REPO, safePath, readJson, listClips, listUses, mediaPath, readClip, canonical,
  verifyClipSnapshots } from './clip-library.mjs';
import { listRuns, verifyRun, runPath, configReference, sha as recordDigest } from './clip-analysis-store.mjs';
import { SUPPORT_ROLES, supportPath, verifySupportClosure } from './clip-backup-support.mjs';
import { readSnapshot, snapshotHash } from './generation-snapshot.mjs';
import { backupScope, validateBackupScope, backupStatePath } from './clip-backup-scope.mjs';

const require = createRequire(import.meta.url);
const { getAccessToken } = require('../gcp/auth.cjs');
const BASE = 'data/clips/cloud';
const GiB = 2 ** 30;
const chunkBytes = 1024 * 1024;
const digest = x => createHash('sha256').update(x).digest('hex');
const stamp = () => new Date().toISOString();

function local(repo, name) { return safePath(repo, `${BASE}/${name}`); }
export function privateJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const tmp = `${file}.${randomUUID()}.tmp`;
  try { fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + '\n', { flag: 'wx', mode: 0o600 }); fs.renameSync(tmp, file); }
  finally { fs.rmSync(tmp, { force: true }); }
}
export function validateConfig(c) {
  if (c?.schemaVersion !== 1 || !/^[a-z][a-z0-9-]{4,61}[a-z0-9]$/.test(c.projectId ?? '')
      || !/^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$/.test(c.bucket ?? '') || c.location !== 'US-CENTRAL1')
    throw new Error('Invalid private cloud configuration');
  if (!c.credentialFile?.startsWith('data/') || !c.authorization?.scope || !c.authorization?.at)
    throw new Error('Cloud credentials and explicit authorization are required in the ignored configuration');
  for (const key of ['monthlyBudgetUsd', 'headroomUsd', 'maximumMonthlyDownloadBytes'])
    if (!Number.isFinite(c[key]) || c[key] <= 0) throw new Error('Invalid cloud operating limit');
  if (c.headroomUsd >= c.monthlyBudgetUsd) throw new Error('Operating headroom consumes the entire budget');
  if (c.uploadConcurrency !== undefined && (!Number.isInteger(c.uploadConcurrency) || c.uploadConcurrency < 1 || c.uploadConcurrency > 32))
    throw new Error('Upload concurrency must be between 1 and 32');
  if (c.uploadTransport !== undefined && !['fetch', 'curl'].includes(c.uploadTransport)) throw new Error('Unknown upload transport');
  for (const key of ['storageUsdPerGiBMonth', 'classAUsdPerRequest', 'classBUsdPerRequest', 'downloadUsdPerGiB'])
    if (!Number.isFinite(c.rates?.[key]) || c.rates[key] <= 0) throw new Error('Verified cloud rates are required');
  const age = Date.now() - Date.parse(c.rates.checkedAt);
  if (!Number.isFinite(age) || age < -86400000 || age > 90 * 86400000) throw new Error('Refresh cloud pricing in the ignored configuration');
  return c;
}
export function loadConfig(repo = REPO) { return validateConfig(readJson(local(repo, 'config.json'))); }

export function hashes(file) {
  const sha = createHash('sha256'), md5 = createHash('md5'), buffer = Buffer.alloc(1024 * 1024);
  const fd = fs.openSync(file, 'r'); let bytes = 0;
  try { for (let n; (n = fs.readSync(fd, buffer, 0, buffer.length, null));) { const part = buffer.subarray(0, n); sha.update(part); md5.update(part); bytes += n; } }
  finally { fs.closeSync(fd); }
  return { bytes, sha256: sha.digest('hex'), md5Hash: md5.digest('base64') };
}
/** Repository-relative POSIX path (safePath rejects backslashes on Windows). */
const rel = (repo, file) => path.relative(repo, file).split(path.sep).join('/');
function selectCatalog(repo, projectId) {
  const allClips = listClips(repo), allUses = listUses(repo);
  const used = new Set(allUses.filter(u => u.projectId === projectId).map(u => u.clipId));
  const clips = projectId === undefined ? allClips : allClips.filter(c => c.collections.includes(projectId) || used.has(c.id));
  if (projectId !== undefined && !clips.length) throw new Error('No catalog clips associated with this project');
  const ids = new Set(clips.map(c => c.id));
  // Retain the use history of selected shared clips, but no unresolved uses from other clips.
  const uses = projectId === undefined ? allUses : allUses.filter(u => ids.has(u.clipId) || u.projectId === projectId);
  if (uses.some(u => !ids.has(u.clipId))) throw new Error('Catalog changed during backup inventory; retry the plan');
  return { clips, uses };
}
export function buildPlan(repo = REPO, progress = () => {}, { allowAbsent = false, projectId } = {}) {
  const scope = backupScope(projectId), selected = selectCatalog(repo, projectId), { clips, uses } = selected, objects = [];
  const previousSets = new Map();
  function previousSet(priorScope) {
    const pointerFile = safePath(repo, backupStatePath('last-backup-set.json', priorScope));
    if (previousSets.has(pointerFile)) return previousSets.get(pointerFile);
    if (!fs.existsSync(pointerFile)) { previousSets.set(pointerFile, null); return null; }
    const pointer = readJson(pointerFile);
    if (!/^[a-f0-9]{64}$/.test(pointer.sha256 ?? '')) throw new Error('Missing verified complete backup-set identity');
    const file = local(repo, `backup-sets/${pointer.sha256}.json`);
    if (hashes(file).sha256 !== pointer.sha256) throw new Error('Backup-set hash mismatch');
    const set = readJson(file), savedScope = validateBackupScope(set.scope);
    if (set.bucket !== loadConfig(repo).bucket || set.schemaVersion !== 1) throw new Error('Backup-set destination mismatch');
    if (savedScope.kind !== priorScope.kind || savedScope.projectId !== priorScope.projectId) throw new Error('Backup-set scope mismatch');
    previousSets.set(pointerFile, set); return set;
  }
  for (const [index, clip] of clips.entries()) {
    const file = mediaPath(clip, repo), name = `clips/${clip.id}/source${clip.extension}`;
    if (fs.existsSync(file)) {
      const h = hashes(file);
      if (h.sha256 !== clip.sha256 || h.bytes !== clip.bytes) throw new Error(`Local master checksum mismatch: ${clip.id}`);
      objects.push({ name, localPath: rel(repo, file), ...h, clipId: clip.id, kind: 'media' });
    } else {
      let prior;
      // A project's prior set takes precedence; a verified whole-library set can bootstrap it.
      for (const priorScope of allowAbsent ? [scope, ...(projectId === undefined ? [] : [backupScope()])] : []) {
        const candidate = previousSet(priorScope)?.objects?.find(o => o.name === name && o.kind === 'media' && o.clipId === clip.id);
        if (candidate?.sha256 === clip.sha256 && candidate.bytes === clip.bytes && /^\d+$/.test(candidate.generation ?? '')) { prior = candidate; break; }
      }
      if (!prior)
        throw new Error(`Missing unverified local master: ${clip.id}; deliberate absence requires --allow-absent and a complete backup set`);
      objects.push({ ...prior, localPath: null, absentLocal: true });
    }
    verifyClipSnapshots(clip, repo);
    const folder = safePath(repo, `data/clips/${clip.id}/generations`);
    if (fs.existsSync(folder)) for (const name of fs.readdirSync(folder).sort()) {
      if (!/^[a-f0-9]{64}\.json$/.test(name)) throw new Error('Unexpected file in private generation snapshots');
      const file = safePath(repo, `data/clips/${clip.id}/generations/${name}`), h = hashes(file);
      const canonicalHash = snapshotHash(readSnapshot(file));
      if (`${canonicalHash}.json` !== name) throw new Error('Private snapshot filename disagrees with canonical evidence');
      // Snapshot IDs describe canonical JSON; the backup preserves exact file bytes separately.
      objects.push({ name: `generations/${clip.id}/${h.sha256}.json`, localPath: rel(repo, file), ...h, kind: 'generation-snapshot', clipId: clip.id, snapshotSha256: canonicalHash });
    }
    const runs = listRuns(clip.id, repo);
    for (const ref of clip.analysisRefs ?? []) if (!runs.includes(ref.runId)) throw new Error('Public analysis reference has no retained private run');
    for (const runId of runs) {
      const m = verifyRun(clip.id, runId, repo), dir = runPath(clip.id, runId, repo), prefix = `analysis/${clip.id}/${runId}`;
      const ref = configReference(readJson(path.join(dir, 'manifest.json')));
      if (ref && !objects.some(o => o.kind === 'analysis-inventory' && o.sha256 === ref.sha256)) {
        const h = hashes(safePath(repo, ref.path));
        objects.push({ name: `inventories/${ref.sha256}.json`, localPath: ref.path, ...h, kind: 'analysis-inventory' });
      }
      for (const a of [{ path: 'manifest.json' }, ...m.artifacts]) {
        const file = safePath(dir, a.path), h = hashes(file);
        objects.push({ name: `${prefix}/${a.path}`, localPath: rel(repo, file), ...h, clipId: clip.id, runId,
          artifactPath: a.path, kind: a.path === 'manifest.json' ? 'analysis-manifest' : 'analysis-artifact' });
      }
    }
    const reviews = safePath(repo, `data/clips/${clip.id}/reviews`);
    if (fs.existsSync(reviews)) for (const name of fs.readdirSync(reviews).sort()) {
      if (!/^[a-f0-9]{64}\.json$/.test(name)) throw new Error('Unexpected private analysis review');
      const file = safePath(reviews, name), review = readJson(file), h = hashes(file);
      if (recordDigest(review) !== name.slice(0, -5) || review.clipId !== clip.id || !runs.includes(review.runId)) throw new Error('Analysis review identity mismatch');
      objects.push({ name: `reviews/${clip.id}/${h.sha256}.json`, localPath: rel(repo, file), ...h,
        kind: 'analysis-review', clipId: clip.id, runId: review.runId, reviewSha256: name.slice(0, -5) });
    }
    if (index % 100 === 0) progress({ phase: 'hash-local', verified: index + 1, clips: clips.length });
  }
  const supportFile = safePath(repo, projectId === undefined ? 'data/clips/analysis/support.json'
    : `data/clips/analysis/projects/${projectId}.support.json`);
  if (fs.existsSync(supportFile)) {
    const support = readJson(supportFile);
    if (support.schemaVersion !== 1 || !Array.isArray(support.files)) throw new Error('Invalid explicit analysis support allowlist');
    for (const entry of support.files) {
      supportPath(entry.path);
      if (!SUPPORT_ROLES.includes(entry.role)) throw new Error('Unsupported backup support payload');
      const file = safePath(repo, entry.path), h = hashes(file);
      if (h.sha256 !== entry.sha256 || h.bytes !== entry.bytes) throw new Error('Selected backup support evidence changed');
      const name = `support/${h.sha256}${path.extname(entry.path)}`, prior = objects.find(o => o.name === name);
      if (prior) {
        if (!prior.restorePaths.includes(entry.path)) prior.restorePaths.push(entry.path);
      } else objects.push({ name, localPath: rel(repo, file), ...h, kind: 'analysis-support', role: entry.role, restorePaths: [entry.path] });
    }
    for (const o of objects.filter(o => o.restorePaths)) o.restorePaths.sort();
    verifySupportClosure(objects, repo);
  }
  if (recordDigest(selected) !== recordDigest(selectCatalog(repo, projectId))) throw new Error('Catalog changed during backup inventory; retry the plan');
  const bytes = gzipSync(Buffer.from(JSON.stringify(canonical({ schemaVersion: 1, scope, clips, uses }))), { level: 9 });
  const sha = digest(bytes), relative = `${BASE}/catalog/${sha}.json.gz`, file = safePath(repo, relative);
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  if (!fs.existsSync(file)) fs.writeFileSync(file, bytes, { flag: 'wx', mode: 0o600 });
  const h = hashes(file);
  if (h.sha256 !== sha) throw new Error('Local catalog backup checksum mismatch');
  objects.push({ name: `catalog/${sha}.json.gz`, localPath: relative, ...h, kind: 'catalog' });
  const plan = { schemaVersion: 1, scope, createdAt: stamp(), clips: clips.length, uses: uses.length, objects,
    clipRecords: clips.map(c => ({ clipId: c.id, sha256: c.sha256, bytes: c.bytes, extension: c.extension, catalogSha256: recordDigest(c) })),
    bytes: objects.reduce((sum, o) => sum + o.bytes, 0) };
  privateJson(safePath(repo, backupStatePath('plan.json', scope)), plan);
  return plan;
}

export function assertPrivateBucket(c, bucket, policy) {
  if (bucket.name !== c.bucket || bucket.location !== c.location || bucket.storageClass !== 'STANDARD'
      || bucket.iamConfiguration?.publicAccessPrevention !== 'enforced'
      || bucket.iamConfiguration?.uniformBucketLevelAccess?.enabled !== true
      || bucket.versioning?.enabled === true || bucket.autoclass?.enabled === true
      || (c.projectNumber && String(bucket.projectNumber) !== String(c.projectNumber)))
    throw new Error('Bucket does not match the authorized private Standard storage configuration');
  if (!Array.isArray(policy.bindings) || policy.bindings.some(b => b.members?.some(m => ['allUsers', 'allAuthenticatedUsers'].includes(m))))
    throw new Error('Bucket policy contains public access or could not be verified');
}
export function verifyObject(expected, actual) {
  if (actual?.name !== expected.name || Number(actual.size) !== expected.bytes || actual.md5Hash !== expected.md5Hash
      || actual.metadata?.sha256 !== expected.sha256 || !/^\d+$/.test(actual.generation ?? '') || actual.storageClass !== 'STANDARD'
      || expected.generation !== undefined && actual.generation !== expected.generation)
    throw new Error(`Cloud object checksum or identity mismatch: ${expected.name}`);
  return actual;
}
export function estimate(c, month) {
  return month.peakStoredBytes / GiB * c.rates.storageUsdPerGiBMonth + month.reservedOperationsUsd
    + month.reservedDownloadBytes / GiB * c.rates.downloadUsdPerGiB;
}
export function reserve(repo, c, { storedBytes = 0, classA = 0, classB = 0, downloadBytes = 0, action }, now = stamp()) {
  for (const n of [storedBytes, classA, classB, downloadBytes]) if (!Number.isSafeInteger(n) || n < 0) throw new Error('Invalid cloud reservation');
  const file = local(repo, 'ledger.json');
  const ledger = fs.existsSync(file) ? readJson(file) : { schemaVersion: 1, projectId: c.projectId, bucket: c.bucket, months: {} };
  if (ledger.schemaVersion !== 1 || ledger.projectId !== c.projectId || ledger.bucket !== c.bucket) throw new Error('Cloud ledger belongs to another destination');
  if (!ledger.months || typeof ledger.months !== 'object' || Array.isArray(ledger.months)) throw new Error('Invalid cloud ledger');
  const monthKey = now.slice(0, 7), old = ledger.months[monthKey] ?? { peakStoredBytes: 0, reservedOperationsUsd: 0, reservedDownloadBytes: 0, entries: [] };
  if (!Number.isSafeInteger(old.peakStoredBytes) || old.peakStoredBytes < 0
      || !Number.isSafeInteger(old.reservedDownloadBytes) || old.reservedDownloadBytes < 0
      || !Number.isFinite(old.reservedOperationsUsd) || old.reservedOperationsUsd < 0 || !Array.isArray(old.entries))
    throw new Error('Invalid monthly cloud ledger; do not reset uncertain reservations');
  const month = { ...old, peakStoredBytes: Math.max(old.peakStoredBytes, storedBytes),
    reservedOperationsUsd: old.reservedOperationsUsd + classA * c.rates.classAUsdPerRequest + classB * c.rates.classBUsdPerRequest,
    reservedDownloadBytes: old.reservedDownloadBytes + downloadBytes };
  if (month.reservedDownloadBytes > c.maximumMonthlyDownloadBytes || estimate(c, month) + c.headroomUsd > c.monthlyBudgetUsd)
    throw new Error('Cloud action exceeds the monthly operating budget or download allowance');
  month.entries = [...old.entries, { at: now, action, storedBytes, classA, classB, downloadBytes }];
  ledger.months[monthKey] = month; privateJson(file, ledger);
  return { month: monthKey, estimatedReservedUsd: estimate(c, month), monthlyBudgetUsd: c.monthlyBudgetUsd,
    headroomUsd: c.headroomUsd, freeTierAssumed: false };
}

export class Gcs {
  constructor(c, repo = REPO, fetcher = fetch, tokenProvider = getAccessToken) { this.c = c; this.repo = repo; this.fetcher = fetcher; this.tokenProvider = tokenProvider; }
  async request(url, options = {}) {
    const target = new URL(url);
    if (target.protocol !== 'https:' || target.hostname !== 'storage.googleapis.com' || target.username || target.password || target.port)
      throw new Error('Refusing cloud credentials outside the Storage API');
    const { timeoutMs = 120000, ...fetchOptions } = options;
    if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1000 || timeoutMs > 3600000)
      throw new Error('Invalid cloud request timeout');
    if (!this.auth || this.expiresAt < Date.now() + 60000) {
      try { this.auth = await this.tokenProvider(safePath(this.repo, this.c.credentialFile)); }
      catch { throw new Error('Cloud authentication failed; credential details withheld'); }
      if (this.auth.projectId !== this.c.projectId) throw new Error('Credential project differs from cloud configuration');
      this.expiresAt = Date.now() + this.auth.expiresIn * 1000;
    }
    const idempotent = !options.method || ['GET', 'HEAD'].includes(options.method)
      || options.method === 'PUT' && options.headers?.['Content-Length'] === '0';
    for (let attempt = 0; ; attempt++) {
      const started = Date.now();
      try { return await this.fetcher(url, { ...fetchOptions, redirect: 'manual', signal: AbortSignal.timeout(timeoutMs),
        headers: { ...fetchOptions.headers, Authorization: `Bearer ${this.auth.accessToken}` } }); }
      catch (e) {
        const file = local(this.repo, 'transport-errors.jsonl'); fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
        fs.appendFileSync(file, JSON.stringify({ at: stamp(), method: options.method ?? 'GET', endpoint: target.pathname,
          elapsedMs: Date.now() - started, errorName: e.name, causeCode: e.cause?.code }) + '\n', { mode: 0o600 });
        if (!idempotent || attempt >= 2) throw new Error('Cloud transport interrupted; resume the existing sync');
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }
  }
  url(suffix = '') { return `https://storage.googleapis.com/storage/v1/b/${encodeURIComponent(this.c.bucket)}${suffix}`; }
  async json(url, options) {
    const r = await this.request(url, options);
    if (!r.ok) throw new Error(`Cloud metadata request failed (HTTP ${r.status}; details withheld)`);
    return r.json();
  }
  async checkPrivate() {
    const bucket = await this.json(this.url()), policy = await this.json(this.url('/iam'));
    assertPrivateBucket(this.c, bucket, policy); return bucket;
  }
  async list(prefix = '') {
    const objects = []; let token;
    do {
      const q = new URLSearchParams({ maxResults: '1000', fields: 'items(name,size,md5Hash,crc32c,generation,metadata,storageClass,timeCreated),nextPageToken' });
      if (prefix) q.set('prefix', prefix);
      if (token) q.set('pageToken', token);
      const page = await this.json(this.url(`/o?${q}`)); objects.push(...(page.items ?? [])); token = page.nextPageToken;
    } while (token);
    return objects;
  }
  async get(name) {
    const r = await this.request(this.url(`/o/${encodeURIComponent(name)}`));
    if (r.status === 404) return null;
    if (!r.ok) throw new Error(`Cloud object lookup failed (HTTP ${r.status}; details withheld)`);
    return r.json();
  }
  sessionUri(uri) {
    const u = new URL(uri);
    if (u.protocol !== 'https:' || u.hostname !== 'storage.googleapis.com' || u.username || u.password || u.port
        || u.pathname !== `/upload/storage/v1/b/${this.c.bucket}/o` || !u.searchParams.get('upload_id'))
      throw new Error('Invalid resumable upload session endpoint');
    return uri;
  }
  async upload(o) {
    const file = safePath(this.repo, o.localPath), sessionFile = local(this.repo, `sessions/${digest(o.name)}.json`);
    let session = fs.existsSync(sessionFile) ? readJson(sessionFile) : null, failures = 0, starts = 0;
    if (session && (session.bucket !== this.c.bucket || session.name !== o.name || session.sha256 !== o.sha256 || session.bytes !== o.bytes))
      throw new Error('Upload session identity mismatch');
    const fd = fs.openSync(file, 'r');
    try {
      while (true) {
        let offset = 0;
        if (session) {
          const r = await this.request(this.sessionUri(session.uri), { method: 'PUT', headers: { 'Content-Length': '0', 'Content-Range': `bytes */${o.bytes}` } });
          if (r.ok) { const result = verifyObject(o, await r.json()); fs.rmSync(sessionFile, { force: true }); return result; }
          if ([404, 410].includes(r.status)) {
            const existing = await this.get(o.name);
            if (existing) { verifyObject(o, existing); fs.rmSync(sessionFile, { force: true }); return existing; }
            session = null; fs.rmSync(sessionFile, { force: true });
          } else if (r.status === 308) offset = uploadedOffset(r, o.bytes);
          else throw new Error(`Upload recovery failed (HTTP ${r.status}; session retained)`);
        }
        if (!session) {
          if (++starts > 3) throw new Error('Upload session retry limit; resume later');
          const q = new URLSearchParams({ uploadType: 'resumable', name: o.name, ifGenerationMatch: '0' });
          let r;
          try { r = await this.request(`https://storage.googleapis.com/upload/storage/v1/b/${this.c.bucket}/o?${q}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Upload-Content-Length': String(o.bytes), 'X-Upload-Content-Type': contentType(o.name) },
            body: JSON.stringify({ name: o.name, contentType: contentType(o.name), md5Hash: o.md5Hash,
              cacheControl: 'private, no-store', metadata: { sha256: o.sha256 } }) }); }
          catch (e) {
            // An unreturned session URI cannot be resumed. Recover a completed object first;
            // otherwise a bounded new session still uses the no-replacement precondition.
            const existing = await this.get(o.name);
            if (existing) return verifyObject(o, existing);
            if (starts >= 3) throw e;
            continue;
          }
          if (r.status === 412) return verifyObject(o, await this.get(o.name));
          if (!r.ok) throw new Error(`Upload initiation failed (HTTP ${r.status}; details withheld)`);
          session = { bucket: this.c.bucket, name: o.name, sha256: o.sha256, bytes: o.bytes, uri: this.sessionUri(r.headers.get('location')) };
          privateJson(sessionFile, session);
        }
        try {
          while (offset < o.bytes) {
            const buffer = Buffer.alloc(Math.min(chunkBytes, o.bytes - offset));
            const n = fs.readSync(fd, buffer, 0, buffer.length, offset);
            if (n !== buffer.length) throw new Error('Local file changed during upload');
            const options = { method: 'PUT', headers: { 'Content-Length': String(n),
              'Content-Type': contentType(o.name), 'Content-Range': `bytes ${offset}-${offset + n - 1}/${o.bytes}` }, body: buffer };
            const uri = this.sessionUri(session.uri);
            const r = this.c.uploadTransport === 'curl' ? await curlPut(uri, options, this.repo) : await this.request(uri, options);
            if (r.ok) { const result = verifyObject(o, await r.json()); fs.rmSync(sessionFile, { force: true }); return result; }
            if (r.status !== 308) throw new Error(`Upload interrupted (HTTP ${r.status}; session retained)`);
            const next = uploadedOffset(r, o.bytes);
            if (next <= offset || next > offset + n) throw new Error('Unexpected resumable upload offset');
            offset = next;
          }
          throw new Error('Upload finalization was not confirmed');
        } catch (e) { if (++failures >= 3) throw e; /* Query the retained session before sending more bytes. */ }
      }
    } finally { fs.closeSync(fd); }
  }
}
/** Native HTTP/2 option for hosts where Node's upload connections are unreliable.
 * Session capabilities stay in private files, never process arguments; redirects are not followed.
 */
export async function curlPut(uri, options, repo, spawnProcess = spawn) {
  const stem = local(repo, `requests/${randomUUID()}`), config = `${stem}.curl`, headersFile = `${stem}.headers`, bodyFile = `${stem}.body`;
  fs.mkdirSync(path.dirname(stem), { recursive: true, mode: 0o700 });
  const text = [`url = ${JSON.stringify(uri)}`, ...Object.entries(options.headers).map(([k, v]) => `header = ${JSON.stringify(`${k}: ${v}`)}`)].join('\n') + '\n';
  fs.writeFileSync(config, text, { flag: 'wx', mode: 0o600 });
  try {
    const args = ['--config', config, '--http2', '--silent', '--show-error', '--proto', '=https', '--request', 'PUT', '--upload-file', '-',
      '--connect-timeout', '20', '--max-time', '120', '--dump-header', headersFile, '--output', bodyFile, '--write-out', '%{http_code}'];
    const child = spawnProcess('curl', args, { stdio: ['pipe', 'pipe', 'pipe'] }); let codeText = '';
    child.stdout.on('data', b => { codeText += b; }); child.stderr.resume(); child.stdin.on('error', () => {});
    const finished = new Promise((resolve, reject) => { child.on('error', () => reject(new Error('Native upload transport could not start')));
      child.on('close', code => code === 0 ? resolve() : reject(new Error(`Native upload interrupted (curl exit ${code}); session retained`))); });
    child.stdin.end(options.body); await finished;
    const status = Number(codeText), headers = new Headers();
    for (const line of fs.readFileSync(headersFile, 'utf8').split(/\r?\n/)) {
      if (/^HTTP\//.test(line)) { for (const key of [...headers.keys()]) headers.delete(key); continue; }
      const i = line.indexOf(':'); if (i > 0) headers.append(line.slice(0, i), line.slice(i + 1).trim());
    }
    if (!Number.isInteger(status) || status < 200 || status > 599) throw new Error('Native upload returned an invalid HTTP status');
    const body = fs.existsSync(bodyFile) ? fs.readFileSync(bodyFile) : null;
    return new Response([204, 205, 304].includes(status) ? null : body, { status, headers });
  } finally { for (const file of [config, headersFile, bodyFile]) fs.rmSync(file, { force: true }); }
}
function uploadedOffset(response, size) {
  const range = response.headers.get('range');
  if (!range) return 0;
  const match = /^bytes=0-(\d+)$/.exec(range), offset = match ? Number(match[1]) + 1 : NaN;
  if (!Number.isSafeInteger(offset) || offset < 0 || offset > size) throw new Error('Invalid resumable upload range');
  return offset;
}
function contentType(name) {
  if (name.endsWith('.gz')) return 'application/gzip';
  if (name.endsWith('.json')) return 'application/json';
  if (name.endsWith('.jpg')) return 'image/jpeg';
  if (name.endsWith('.png')) return 'image/png';
  if (name.endsWith('.html')) return 'text/html';
  if (name.endsWith('.vtt')) return 'text/vtt';
  if (/\.(log|txt|md|py|mjs|js|yaml|yml|csv|tsv|srt)$/.test(name)) return 'text/plain';
  return ({ '.mp4': 'video/mp4', '.m4v': 'video/mp4', '.mov': 'video/quicktime', '.webm': 'video/webm', '.mkv': 'video/x-matroska', '.avi': 'video/x-msvideo' })[path.extname(name)] ?? 'application/octet-stream';
}
export async function locked(repo, action) {
  const dir = local(repo, '.lock'); fs.mkdirSync(path.dirname(dir), { recursive: true, mode: 0o700 });
  try { fs.mkdirSync(dir); } catch (e) { if (e.code === 'EEXIST') throw new Error('Cloud sync lock exists; confirm the previous process has stopped before recovering it'); throw e; }
  try { privateJson(path.join(dir, 'owner.json'), { pid: process.pid, startedAt: stamp() }); return await action(); }
  finally { fs.rmSync(dir, { recursive: true }); }
}
export async function sync(repo = REPO, { progress = () => {}, client, plan, allowAbsent = false, projectId } = {}) {
  const requestedScope = backupScope(projectId);
  if (plan && projectId !== undefined && (validateBackupScope(plan.scope).kind !== 'project' || plan.scope.projectId !== projectId))
    throw new Error('Supplied backup plan does not match the requested project');
  return locked(repo, async () => {
    const c = loadConfig(repo); plan ??= buildPlan(repo, progress, { allowAbsent, projectId }); client ??= new Gcs(c, repo);
    const scope = validateBackupScope(plan.scope ?? requestedScope);
    reserve(repo, c, { storedBytes: plan.bytes, classA: 20, classB: 20, action: 'sync-preflight' });
    await client.checkPrivate();
    const remote = new Map((await client.list()).map(o => [o.name, o]));
    const pending = [];
    for (const o of plan.objects) {
      if (remote.has(o.name)) {
        const actual = verifyObject(o, remote.get(o.name));
        privateJson(local(repo, `receipts/${digest(o.name)}.json`), { verifiedAt: stamp(), bucket: c.bucket, ...actual });
      } else {
        if (o.absentLocal || !o.localPath) throw new Error('Absent local master is missing from the verified remote backup');
        pending.push(o);
      }
    }
    const storedBytes = [...remote.values()].reduce((s, o) => s + Number(o.size), 0) + pending.reduce((s, o) => s + o.bytes, 0);
    const budget = reserve(repo, c, { storedBytes, classA: pending.length * 3 + 20, classB: pending.length * 4 + 20, action: 'sync' });
    progress({ phase: 'upload', pending: pending.length, skipped: plan.objects.length - pending.length, bytes: storedBytes, ...budget });
    let uploaded = 0, uploadedBytes = 0, index = 0, failure;
    // Stop claiming new files after a worker fails; await all in-flight receipts before releasing the lock.
    await Promise.all(Array.from({ length: Math.min(c.uploadConcurrency ?? 4, pending.length) }, async () => {
      while (!failure && index < pending.length) {
        const o = pending[index++];
        try {
          const actual = verifyObject(o, await client.upload(o));
          privateJson(local(repo, `receipts/${digest(o.name)}.json`), { verifiedAt: stamp(), bucket: c.bucket, ...actual });
          uploaded++; uploadedBytes += o.bytes;
          if (uploaded % 25 === 0 || uploaded === pending.length) progress({ phase: 'upload', uploaded, pending: pending.length, uploadedBytes });
        } catch (e) { failure ??= e; }
      }
    }));
    if (failure) throw failure;
    await client.checkPrivate();
    const final = new Map((await client.list()).map(o => [o.name, o]));
    for (const o of plan.objects) verifyObject(o, final.get(o.name));
    const backupSet = await (await import('./clip-backup-set.mjs')).sealBackupSet(plan, final, repo, c, client);
    const receipt = { schemaVersion: 1, scope, completedAt: stamp(), bucket: c.bucket, clips: plan.clips, objects: plan.objects.length,
      bytes: plan.bytes, uploaded, skipped: plan.objects.length - uploaded, privateAccessVerified: true,
      verification: 'Local SHA-256 or explicitly absent verified backup member; server MD5, byte length, SHA-256 metadata and generation; final remote inventory', budget, backupSet };
    privateJson(safePath(repo, backupStatePath('last-sync.json', scope)), receipt); return receipt;
  });
}
export async function restore(id, output, repo = REPO, { client } = {}) {
  return locked(repo, async () => {
    const c = loadConfig(repo), clip = readClip(id, repo), target = safePath(repo, output);
    if (!target.startsWith(path.join(repo, 'data/workspace') + path.sep) || path.extname(target) !== clip.extension)
      throw new Error('Restore into a new file under data/workspace with the original extension');
    if (fs.existsSync(target) || fs.existsSync(`${target}.cloud.json`)) throw new Error('Restore destination already exists');
    client ??= new Gcs(c, repo);
    const known = fs.existsSync(local(repo, 'last-sync.json')) ? readJson(local(repo, 'last-sync.json')).bytes : clip.bytes;
    reserve(repo, c, { storedBytes: known, classB: 4, downloadBytes: clip.bytes, action: 'restore' });
    await client.checkPrivate();
    const name = `clips/${clip.id}/source${clip.extension}`, remote = await client.get(name);
    if (!remote || remote.metadata?.sha256 !== clip.sha256 || Number(remote.size) !== clip.bytes || !remote.md5Hash
        || remote.storageClass !== 'STANDARD' || !/^\d+$/.test(remote.generation))
      throw new Error('Restore source differs from catalog identity');
    fs.mkdirSync(path.dirname(target), { recursive: true });
    const tmp = `${target}.${randomUUID()}.part`, bytes = clip.bytes;
    try {
      await (await import('./clip-cloud-restore.mjs')).download(client, remote, tmp);
      fs.linkSync(tmp, target); // Atomic installation without replacing any existing file.
      const receipt = { restoredAt: stamp(), clipId: id, sha256: clip.sha256, bytes, bucket: c.bucket, object: name, generation: remote.generation, output };
      privateJson(`${target}.cloud.json`, receipt); return receipt;
    } finally { fs.rmSync(tmp, { force: true }); }
  });
}
function syncOptions(args, { status = false } = {}) {
  const options = {}, seen = new Set();
  for (let i = 0; i < args.length; i++) {
    const arg = args[i], key = arg.split('=')[0];
    if (seen.has(key)) throw new Error('Duplicate cloud option');
    seen.add(key);
    if (arg === '--allow-absent' && !status) options.allowAbsent = true;
    else if (key === '--project') {
      options.projectId = arg === '--project' ? args[++i] : arg.slice('--project='.length);
      if (options.projectId === undefined) throw new Error('Specify a project ID after --project');
      backupScope(options.projectId);
    } else throw new Error('Unknown cloud option; use --project PROJECT_ID and optionally --allow-absent for plan/sync');
  }
  return options;
}

export async function cloudMain(args, repo = REPO) {
  const [verb, ...rest] = args, progress = e => process.stderr.write(JSON.stringify(e) + '\n');
  if (!verb || verb === 'help') return { commands: ['cloud plan', 'cloud sync', 'cloud status', 'cloud restore CLIP_ID data/workspace/PROJECT/restore/source.mp4',
    'cloud fetch CLIP_ID', 'cloud catalogs', 'cloud recover-catalog SHA256 data/workspace/PROJECT/recovered-catalog',
    'cloud plan [--project PROJECT_ID] [--allow-absent]', 'cloud sync [--project PROJECT_ID] [--allow-absent]',
    'cloud status [--project PROJECT_ID]', 'cloud backup-sets', 'cloud verify-set SHA256',
    'cloud recover-set SHA256 data/workspace/PROJECT/recovery CLIP_ID... [--rehearse]', 'cloud readiness PRIVATE_POLICY.json',
    'cloud cleanup-plan PRIVATE_POLICY.json PRIVATE_MANIFEST.json', 'cloud cleanup-apply PRIVATE_MANIFEST.json PRIVATE_APPROVAL.json'],
    configuration: `${BASE}/config.json`, network: 'sync, restore, fetch, catalogs, recover-catalog, backup-sets, verify-set, recover-set, readiness and cleanup commands only', privacy: 'Private IAM access; no public or signed URLs' };
  if (verb === 'plan') {
    const options = syncOptions(rest), c = loadConfig(repo), plan = buildPlan(repo, progress, options);
    return { scope: plan.scope, clips: plan.clips, objects: plan.objects.length, bytes: plan.bytes, storageUsdPerMonth: plan.bytes / GiB * c.rates.storageUsdPerGiBMonth,
      monthlyBudgetUsd: c.monthlyBudgetUsd, plan: backupStatePath('plan.json', plan.scope), network: false };
  }
  if (verb === 'sync') return sync(repo, { progress, ...syncOptions(rest) });
  if (['backup-sets', 'verify-set', 'recover-set', 'readiness'].includes(verb)) return (await import('./clip-backup-set.mjs')).backupMain(verb, rest, repo);
  if (['cleanup-plan', 'cleanup-apply'].includes(verb)) return (await import('./clip-cleanup.mjs')).cleanupMain(verb, rest, repo);
  if (verb === 'restore' && rest.length === 2) return restore(rest[0], rest[1], repo);
  if (verb === 'fetch' && rest.length === 1) return (await import('./clip-cloud-restore.mjs')).fetchClip(rest[0], repo);
  if (verb === 'catalogs' && !rest.length) return (await import('./clip-cloud-restore.mjs')).catalogs(repo);
  if (verb === 'recover-catalog' && rest.length === 2) return (await import('./clip-cloud-restore.mjs')).recoverCatalog(rest[0], rest[1], repo);
  if (verb === 'status') {
    const scope = backupScope(syncOptions(rest, { status: true }).projectId);
    const c = loadConfig(repo), file = safePath(repo, backupStatePath('last-sync.json', scope)), jobFile = local(repo, 'runner.json');
    const job = scope.kind === 'library' && fs.existsSync(jobFile) ? readJson(jobFile) : null;
    let running = false;
    if (job && !['complete', 'failed'].includes(job.phase)) {
      try { process.kill(job.pid, 0); running = true; } catch (e) { if (e.code === 'EPERM') running = true; }
    }
    return { configured: true, scope, monthlyBudgetUsd: c.monthlyBudgetUsd, lastSync: fs.existsSync(file) ? readJson(file) : null,
      initialBackup: job ? { phase: job.phase, running, startedAt: job.startedAt, updatedAt: job.updatedAt,
        uploadedObjects: job.verifiedUploadReceipts, totalObjects: job.totalObjects, uploadedBytes: job.verifiedUploadedBytes,
        totalBytes: job.totalBytes, error: job.error, restoreVerified: job.restoreVerified } : null,
      note: 'Local receipts and job status; cloud sync rechecks current remote integrity and privacy' };
  }
  throw new Error('Unknown cloud command; run npm run clips -- cloud help');
}
