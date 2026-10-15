/** Resumable local clip analysis. JSON evidence is authoritative; no implicit network. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { randomUUID } from 'node:crypto';
import { REPO, safePath, readJson, listClips, readClip, resolveClip, hashFile, mediaPath } from './clip-library.mjs';
import { VERSION, BASELINE, SEMANTIC, STEPS, configFor, runIdentity, runPath, verifyRun, withLock, privateJson,
  fileIdentity, verifyFile, filesUnder, assert, sha, now, checkSpace, validateManifest } from './clip-analysis-store.mjs';
import { resolveBinary, toolVersion } from './clip-analysis-process.mjs';
import { extractors } from './clip-analysis-extract.mjs';
import { validateAdapter, semantic, pinAdapters, setupOcr } from './clip-analysis-adapters.mjs';

export function toolIdentity(config) {
  const tools = { platform: `${os.type()} ${os.release()} ${os.arch()}`, implementation: {} };
  for (const name of ['ffmpeg', 'ffprobe']) {
    const binary = resolveBinary(name); tools[name] = { binary, sha256: hashFile(binary), version: toolVersion(binary) };
  }
  for (const name of ['clip-analysis', 'clip-analysis-store', 'clip-analysis-process', 'clip-analysis-extract', 'clip-analysis-adapters', 'clip-analysis-speech'])
    tools.implementation[`${name}.mjs`] = hashFile(path.join(REPO, `tools/production/${name}.mjs`));
  for (const [step, adapter] of Object.entries(config.adapters)) validateAdapter(step, adapter);
  return tools;
}
function verifyStep(dir, receipt, identity, step) {
  assert(receipt.runId === identity.runId && receipt.step === step && receipt.inputSha256 === identity.input.sha256
    && ['complete', 'not-applicable', 'needs-review'].includes(receipt.state), 'Step receipt identity mismatch');
  assert(receipt.state === 'complete' || typeof receipt.reason === 'string' && receipt.reason.trim(), 'Step status needs a reason');
  assert(Array.isArray(receipt.outputs), 'Step receipt has no output inventory');
  const names = new Set();
  for (const a of receipt.outputs) { assert(!names.has(a.path) && a.path !== 'receipt.json', 'Invalid step output inventory'); names.add(a.path); verifyFile(safePath(dir, a.path), a); }
  const actual = filesUnder(dir).filter(f => f !== 'receipt.json');
  assert(actual.length === names.size && actual.every(f => names.has(f)), 'Undeclared step artifact');
  return receipt;
}
export async function analyzeClip(id, repo = REPO, { config: supplied = {}, retry = false, recover = false, progress = () => {}, tools: suppliedTools } = {}) {
  const config = configFor(supplied), tools = suppliedTools ?? toolIdentity(config);
  return withLock(repo, id, async () => {
    const clip = readClip(id, repo), source = resolveClip(id, repo), identity = runIdentity(clip, config, { ...tools, catalogEvidenceSha256: sha(clip) });
    const dir = runPath(id, identity.runId, repo), stateFile = path.join(dir, 'state.json');
    fs.mkdirSync(dir, { recursive: true, mode: 0o700 }); checkSpace(dir, config.limits);
    if (fs.existsSync(path.join(dir, 'manifest.json'))) { const m = verifyRun(id, identity.runId, repo); resolveClip(id, repo); return { clipId: id, runId: m.runId, status: 'complete', reused: true }; }
    let state = fs.existsSync(stateFile) ? readJson(stateFile) : { ...identity, createdAt: now(), inputVerifiedBefore: true, steps: Object.fromEntries(STEPS.map(s => [s, { state: 'pending', reason: 'Not yet run' }])) };
    assert(state.runId === identity.runId && sha(state.config) === sha(config), 'Existing analysis state conflicts with this run');
    privateJson(stateFile, state);
    let baselineFailed = false;
    for (const step of STEPS) {
      const finalDir = path.join(dir, 'steps', step), receiptFile = path.join(finalDir, 'receipt.json');
      if (fs.existsSync(receiptFile)) {
        state.steps[step] = verifyStep(finalDir, readJson(receiptFile), identity, step); privateJson(stateFile, state); continue;
      }
      assert(!fs.existsSync(finalDir), 'Incomplete step installation; preserve and inspect the conflicting directory');
      if (baselineFailed) continue;
      const audioAbsent = ['transcript', 'audio-content'].includes(step) && state.steps.audio.state === 'not-applicable';
      if (SEMANTIC.includes(step) && !config.adapters[step] && !audioAbsent) { state.steps[step] = { state: 'pending', reason: 'Local adapter and pinned weights have not been provisioned' }; continue; }
      if (state.steps[step].state === 'failed' && !retry) { if (BASELINE.includes(step)) baselineFailed = true; continue; }
      const attempt = path.join(dir, 'attempts', step, randomUUID()); fs.mkdirSync(attempt, { recursive: true, mode: 0o700 });
      const startedAt = now(), context = { repo, clip, source, config, tools, runDir: dir, dir: attempt, commands: [] };
      state.steps[step] = { state: 'running', startedAt, attempt: path.relative(dir, attempt) }; privateJson(stateFile, state);
      progress({ clipId: id, runId: identity.runId, step, state: 'running' });
      try {
        const result = BASELINE.includes(step) ? await extractors[step](context) : await withLock(repo, 'model-worker', () => semantic(step, context), { recover });
        const receipt = { schemaVersion: 1, runId: identity.runId, inputSha256: clip.sha256, step, ...result,
          startedAt, completedAt: now(), elapsedMs: Date.now() - Date.parse(startedAt), commands: context.commands,
          outputs: filesUnder(attempt).map(p => ({ path: p, ...fileIdentity(safePath(attempt, p)) })) };
        privateJson(path.join(attempt, 'receipt.json'), receipt, true);
        verifyStep(attempt, receipt, identity, step);
        fs.mkdirSync(path.dirname(finalDir), { recursive: true, mode: 0o700 }); fs.renameSync(attempt, finalDir);
        state.steps[step] = receipt;
      } catch (error) {
        const failure = { state: 'failed', reason: error.message, startedAt, failedAt: now(), commands: context.commands, attempt: path.relative(dir, attempt) };
        privateJson(path.join(attempt, 'failure.json'), failure, true); state.steps[step] = failure;
        if (BASELINE.includes(step)) baselineFailed = true;
      }
      state.updatedAt = now(); privateJson(stateFile, state); progress({ clipId: id, runId: identity.runId, step, state: state.steps[step].state });
    }
    privateJson(stateFile, state);
    if (Object.values(state.steps).some(s => ['failed', 'running'].includes(s.state)) || config.required.some(s => state.steps[s].state === 'pending'))
      return { clipId: id, runId: identity.runId, status: 'incomplete', steps: Object.fromEntries(STEPS.map(s => [s, { state: state.steps[s].state, reason: state.steps[s].reason }])) };
    resolveClip(id, repo); // Hash again after all extraction, before an atomic completion manifest.
    assert(sha(readClip(id, repo)) === sha(clip), 'Catalog evidence changed during extraction; rerun with the new evidence identity');
    for (const name of ['ffmpeg', 'ffprobe']) assert(hashFile(tools[name].binary) === tools[name].sha256, 'Analysis executable changed during extraction');
    const technical = readJson(path.join(dir, 'steps/probe/technical.json'));
    const artifacts = filesUnder(path.join(dir, 'steps')).map(p => ({ path: `steps/${p}`, step: p.split('/')[0], ...fileIdentity(safePath(dir, `steps/${p}`)) }));
    assert(artifacts.reduce((s, a) => s + a.bytes, 0) <= config.limits.maxOutputBytes, 'Completed run exceeds the retained output limit');
    const manifest = { ...identity, status: 'complete', createdAt: state.createdAt, completedAt: now(), catalogSha256: sha(clip),
      inputVerifiedBefore: true, inputVerifiedAfter: true, steps: state.steps, artifacts,
      timeBases: technical.streams.filter(s => s.time_base).map(s => ({ streamIndex: s.index, timeBase: s.time_base })),
      warnings: STEPS.filter(s => state.steps[s].state !== 'complete').map(s => ({ step: s, state: state.steps[s].state, reason: state.steps[s].reason })) };
    validateManifest(manifest); privateJson(path.join(dir, 'manifest.json'), manifest, true); verifyRun(id, identity.runId, repo);
    return { clipId: id, runId: identity.runId, status: 'complete', requiredReview: config.required.filter(s => state.steps[s].state === 'needs-review'), bytes: artifacts.reduce((s, a) => s + a.bytes, 0), reused: false };
  }, { recover });
}

export function inventory(repo = REPO, { verify = false } = {}) {
  const clips = listClips(repo), locationsFile = safePath(repo, 'data/clips/locations.json'), locations = fs.existsSync(locationsFile) ? readJson(locationsFile) : null;
  const historical = [], byId = new Map(clips.map(c => [c.id, c]));
  for (const [relative, mapping] of Object.entries(locations?.locations ?? {})) {
    const row = { path: relative, clipId: mapping.id, status: 'unverified', kindCandidate: /\/(final|review)\//.test(relative) ? 'delivery' : /\/(edit|scratch)\//.test(relative) ? 'derived' : 'unknown' };
    try {
      const file = safePath(repo, relative), clip = byId.get(mapping.id);
      if (!clip) row.status = 'unresolved-catalog-id';
      else if (!fs.existsSync(file)) row.status = 'missing-historical-copy';
      else if (fs.statSync(file).size !== clip.bytes || mapping.bytes !== clip.bytes) row.status = 'size-mismatch';
      else if (verify) row.status = hashFile(file) === clip.sha256 ? 'hash-verified' : 'hash-mismatch';
      else row.status = 'present-unverified';
    } catch { row.status = 'unsafe-or-unreadable-path'; }
    historical.push(row);
  }
  const kinds = {}, rows = [];
  for (const clip of clips) {
    kinds[clip.kind] = (kinds[clip.kind] ?? 0) + 1;
    const present = fs.existsSync(mediaPath(clip, repo)); let valid = null;
    if (verify && present) { try { resolveClip(clip.id, repo); valid = true; } catch { valid = false; } }
    rows.push({ clipId: clip.id, kind: clip.kind, classificationEvidence: clip.kind === 'unknown' ? 'Unknown retained for analysis' : 'Existing attributed catalog classification',
      localMaster: present, hashVerified: valid, bytes: clip.bytes, ...clip.technical, historicalAnalysis: clip.analysis.length,
      generationRecords: clip.generations.length, snapshots: clip.generations.filter(g => g.snapshotSha256).length });
  }
  const report = { schemaVersion: 1, createdAt: now(), catalogSha256: sha(clips), uniqueClips: clips.length, kinds,
    bytes: clips.reduce((s, c) => s + c.bytes, 0), durationSeconds: clips.reduce((s, c) => s + c.technical.durationSeconds, 0),
    locationsSha256: locations ? sha(locations) : null, historicalCopies: historical,
    locationReconciliation: 'Historical paths retained; kind candidates are path hints, not generation evidence. Content verification is explicit, never inferred from mtime', rows };
  privateJson(safePath(repo, 'data/clips/analysis/inventory.json'), report); return report;
}
export function pilotPlan(repo = REPO) {
  const clips = listClips(repo), selected = new Map();
  const choose = (criterion, predicate, sort = (a, b) => a.id.localeCompare(b.id)) => {
    const candidates = clips.filter(predicate).sort(sort), clip = candidates.find(c => !selected.has(c.id)) ?? candidates[0];
    if (clip) { const row = selected.get(clip.id) ?? { clipId: clip.id, criteria: [], labels: {}, reviewed: false }; row.criteria.push(criterion); selected.set(clip.id, row); }
  };
  choose('portrait', c => c.technical.height > c.technical.width);
  choose('landscape', c => c.technical.width > c.technical.height);
  choose('short', c => c.technical.durationSeconds < 10);
  choose('long', c => c.technical.durationSeconds >= 60, (a, b) => a.technical.durationSeconds - b.technical.durationSeconds);
  choose('audio-present', c => c.technical.audioCodec !== null);
  choose('no-audio', c => c.technical.audioCodec === null);
  for (const [criterion, re] of Object.entries({ speech: /speech|dialogue|speaking/i, music: /music|song|instrument/i, 'visible-text': /sign|title|text/i,
    people: /person|people|woman|man\b/i, animation: /animation|animated/i, static: /static|still|locked/i, moving: /moving|tracking|running/i,
    cuts: /cut|montage/i, 'known-defect': /defect|morph|flicker|distort/i })) choose(`${criterion}-historical-candidate`, c => re.test(JSON.stringify(c.analysis)));
  for (const clip of [...clips].sort((a, b) => (['source', 'unknown'].includes(b.kind) - ['source', 'unknown'].includes(a.kind)) || a.id.localeCompare(b.id))) {
    if (selected.size >= Math.min(24, clips.length)) break;
    if (!selected.has(clip.id)) selected.set(clip.id, { clipId: clip.id, criteria: ['coverage-fill'], labels: {}, reviewed: false });
  }
  const plan = { schemaVersion: 1, createdAt: now(), catalogSha256: sha(clips), samples: [...selected.values()],
    requiredHumanLabels: ['speech', 'music', 'silence', 'visible-text', 'people-or-animation', 'static-or-moving', 'cuts', 'known-defects'],
    requiredFixtureCases: ['rotation', 'HDR', 'VFR', 'corruption', 'silent-audio', 'no-audio'],
    acceptance: 'Not approved. Historical descriptions only nominate candidates; inspect and label actual evidence before freezing a profile.' };
  privateJson(safePath(repo, 'data/clips/analysis/pilot-plan.json'), plan); return plan;
}
export async function enqueue(ids, repo = REPO, config = {}) {
  return withLock(repo, 'queue', async () => {
    const normalized = configFor(config), tools = toolIdentity(normalized), file = safePath(repo, 'data/clips/analysis/queue.json');
    const queue = fs.existsSync(file) ? readJson(file) : { schemaVersion: 1, jobs: [] };
    assert(queue.schemaVersion === 1 && Array.isArray(queue.jobs), 'Invalid analysis queue');
    for (const id of ids) {
      const clip = readClip(id, repo), identity = runIdentity(clip, normalized, { ...tools, catalogEvidenceSha256: sha(clip) });
      if (!queue.jobs.some(j => j.clipId === id && j.runId === identity.runId)) queue.jobs.push({ clipId: id, runId: identity.runId,
        config: normalized, tools, state: 'pending', queuedAt: now(), priority: ['source', 'unknown'].includes(clip.kind) ? 0 : 1 });
    }
    queue.jobs.sort((a, b) => a.priority - b.priority || a.queuedAt.localeCompare(b.queuedAt)); privateJson(file, queue);
    return { queued: queue.jobs.length, pending: queue.jobs.filter(j => j.state === 'pending').length, queue: path.relative(repo, file) };
  });
}
function supersedeFailed(queue, completed) {
  for (const prior of queue.jobs) {
    if (prior === completed || prior.state !== 'failed' || prior.clipId !== completed.clipId || prior.supersededBy) continue;
    if (!prior.config.required.every(s => completed.config.required.includes(s))
      || !Object.keys(prior.config.adapters).every(s => Object.hasOwn(completed.config.adapters, s))) continue;
    // Preserve the failure, result and attempts. Only a verified completed successor
    // covering at least the same passes can remove it from the outstanding work count.
    prior.supersededBy = { runId: completed.runId, at: now(), reason: 'A verified completed run covers the failed run\'s required and configured passes' };
  }
}
export function queueCounts(jobs) {
  return { ...Object.fromEntries(['pending', 'running', 'complete', 'failed'].map(s => [s, jobs.filter(j => j.state === s && !j.supersededBy).length])),
    superseded: jobs.filter(j => j.supersededBy).length };
}
export async function adoptRun(id, runId, repo = REPO) {
  return withLock(repo, 'queue', async () => {
    const m = verifyRun(id, runId, repo), clip = readClip(id, repo);
    assert(m.input.sha256 === clip.sha256 && m.input.bytes === clip.bytes, 'Completed run belongs to another source');
    const file = safePath(repo, 'data/clips/analysis/queue.json'), queue = fs.existsSync(file) ? readJson(file) : { schemaVersion: 1, jobs: [] };
    let job = queue.jobs.find(j => j.clipId === id && j.runId === runId);
    if (!job) {
      const { catalogEvidenceSha256, ...tools } = m.tools;
      job = { clipId: id, runId, config: m.config, tools, state: 'complete', queuedAt: now(), finishedAt: m.completedAt, priority: 0,
        result: { clipId: id, runId, status: 'complete', adoptedVerifiedRun: true } }; queue.jobs.push(job);
    } else {
      assert(job.state !== 'running', 'Cannot adopt a run owned by a worker');
      if (job.state !== 'complete') {
        (job.history ??= []).push({ state: job.state, result: job.result, error: job.error, finishedAt: job.finishedAt });
        job.result = { clipId: id, runId, status: 'complete', adoptedVerifiedRun: true }; delete job.error;
      }
      job.state = 'complete'; job.finishedAt = m.completedAt;
    }
    supersedeFailed(queue, job); privateJson(file, queue); return { adopted: runId, states: queueCounts(queue.jobs) };
  });
}
export async function workQueue(repo = REPO, { limit = 1, retry = false, recover = false, progress = () => {} } = {}) {
  assert(Number.isSafeInteger(limit) && limit > 0, 'Queue worker needs a positive limit');
  return withLock(repo, 'queue', async () => {
    const file = safePath(repo, 'data/clips/analysis/queue.json'), queue = readJson(file); let processed = 0;
    for (const job of queue.jobs) {
      if (processed >= limit) break;
      if (job.supersededBy || job.state === 'complete' || job.state === 'failed' && !retry) continue;
      processed++;
      if (job.state === 'failed') (job.history ??= []).push({ state: job.state, result: job.result, error: job.error, finishedAt: job.finishedAt });
      delete job.error; delete job.result;
      job.state = 'running'; job.startedAt = now(); privateJson(file, queue);
      try {
        const current = toolIdentity(job.config);
        assert(sha(current) === sha(job.tools), 'Queued extractor changed; enqueue a new configuration instead of changing this job');
        const out = await analyzeClip(job.clipId, repo, { config: job.config, tools: current, retry, recover, progress });
        assert(out.runId === job.runId, 'Queued input evidence changed; enqueue a new run');
        job.state = out.status === 'complete' ? 'complete' : 'failed'; job.result = out;
        if (job.state === 'complete') supersedeFailed(queue, job);
      } catch (e) { job.state = 'failed'; job.error = e.message; }
      job.finishedAt = now(); privateJson(file, queue);
    }
    return { processed, states: queueCounts(queue.jobs) };
  }, { recover });
}

export async function analysisMain(args, repo = REPO) {
  const [verb, ...rest] = args, flags = Object.fromEntries(rest.filter(s => s.startsWith('--')).map(s => { const i = s.indexOf('='); return i < 0 ? [s.slice(2), true] : [s.slice(2, i), s.slice(i + 1)]; }));
  const positional = rest.filter(s => !s.startsWith('--'));
  const allowed = { inventory: ['verify'], 'pilot-plan': [], run: ['config', 'retry', 'recover'], enqueue: ['config'], work: ['limit', 'retry', 'recover'],
    verify: [], adopt: [], status: [], index: [], search: [], neighbors: [], 'similar-text': ['config'], 'setup-ocr': [], pin: [], project: [], readiness: [], 'freeze-profile': [], 'review-template': [], 'record-review': [] };
  if (!verb || verb === 'help') return { commands: ['analysis inventory [--verify]', 'analysis pilot-plan', 'analysis run CLIP_ID [--config=PRIVATE.json] [--retry] [--recover]',
    'analysis enqueue all|CLIP_ID... [--config=PRIVATE.json]', 'analysis work --limit=N [--retry] [--recover]', 'analysis verify CLIP_ID RUN_ID', 'analysis adopt CLIP_ID RUN_ID',
    'analysis setup-ocr', 'analysis pin PRIVATE_CONFIG.json PRIVATE_OUTPUT.json', 'analysis status', 'analysis index', 'analysis search QUERY', 'analysis similar-text QUERY --config=PRIVATE.json',
    'analysis neighbors CLIP_ID RUN_ID', 'analysis review-template CLIP_ID RUN_ID', 'analysis record-review REVIEW.json', 'analysis freeze-profile PILOT_REVIEW.json',
    'analysis project CLIP_ID RUN_ID REVIEW.json', 'analysis readiness PRIVATE_POLICY.json'], network: false, deletion: 'No deletion command' };
  assert(allowed[verb] && Object.keys(flags).every(f => allowed[verb].includes(f)), 'Unknown analysis command or option');
  const config = flags.config ? readJson(safePath(repo, flags.config)) : {};
  const progress = e => process.stderr.write(JSON.stringify(e) + '\n');
  if (verb === 'inventory' && !positional.length) { const r = inventory(repo, { verify: !!flags.verify }); return { ...r, rows: r.rows.length, historicalCopies: r.historicalCopies.length, report: 'data/clips/analysis/inventory.json' }; }
  if (verb === 'pilot-plan' && !positional.length) return pilotPlan(repo);
  if (verb === 'setup-ocr' && !positional.length) return setupOcr(repo);
  if (verb === 'pin' && positional.length === 2) { const target = safePath(repo, positional[1]); assert(positional[1].startsWith('data/'), 'Pinned configuration stays private'); privateJson(target, pinAdapters(readJson(safePath(repo, positional[0]))), true); return { profile: positional[1] }; }
  if (verb === 'run' && positional.length === 1) return analyzeClip(positional[0], repo, { config, retry: !!flags.retry, recover: !!flags.recover, progress });
  if (verb === 'enqueue' && positional.length) return enqueue(positional[0] === 'all' && positional.length === 1 ? listClips(repo).map(c => c.id) : positional, repo, config);
  if (verb === 'work' && !positional.length) return workQueue(repo, { limit: Number(flags.limit ?? 1), retry: !!flags.retry, recover: !!flags.recover, progress });
  if (verb === 'verify' && positional.length === 2) { const m = verifyRun(...positional, repo); return { clipId: m.input.clipId, runId: m.runId, artifacts: m.artifacts.length, verified: true }; }
  if (verb === 'adopt' && positional.length === 2) return adoptRun(positional[0], positional[1], repo);
  if (verb === 'similar-text' && positional.length && flags.config) return (await import('./clip-analysis-views.mjs')).similarText(positional.join(' '), config, repo);
  if (['status', 'index', 'search', 'neighbors', 'project', 'readiness', 'freeze-profile', 'review-template', 'record-review'].includes(verb))
    return (await import('./clip-analysis-views.mjs')).viewsMain(verb, positional, repo);
  throw new Error('Invalid analysis arguments; run clips analysis help');
}
