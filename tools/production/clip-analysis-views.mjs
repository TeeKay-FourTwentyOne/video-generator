/** Rebuildable private discovery, explicit reviewed projection and cleanup readiness. */
import fs from 'node:fs';
import path from 'node:path';
import { REPO, safePath, readJson, readClip, listClips, listUses, mediaPath, publicText, updateClip, hashFile, verifyClipSnapshots } from './clip-library.mjs';
import { assert, sha, now, validHash, privateJson, runPath, listRuns, verifyRun, verifyFile, configFor, BASELINE, SEMANTIC, withLock, filesUnder } from './clip-analysis-store.mjs';
import { seconds } from './clip-analysis-process.mjs';
import { validateBackupSet, formatSignature } from './clip-backup-set.mjs';
import { validateVector } from './clip-analysis-adapters.mjs';

const local = (repo, name) => safePath(repo, `data/clips/analysis/${name}`);
const escape = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const extractorIdentity = m => sha(Object.fromEntries(Object.entries(m.tools).filter(([key]) => key !== 'catalogEvidenceSha256')));
export function reviewPath(id, hash, repo = REPO) {
  assert(validHash(hash), 'Invalid review hash'); readClip(id, repo); return safePath(repo, `data/clips/${id}/reviews/${hash}.json`);
}
export function validateReview(r, repo = REPO) {
  assert(r?.schemaVersion === 1 && r.reviewedBy === 'human' && Number.isFinite(Date.parse(r.reviewedAt)) && typeof r.privacyReviewed === 'boolean', 'Review needs an explicit human review record');
  const m = verifyRun(r.clipId, r.runId, repo), file = path.join(runPath(r.clipId, r.runId, repo), 'manifest.json');
  assert(hashFile(file) === r.manifestSha256, 'Review refers to another analysis manifest');
  assert(r.steps && Object.keys(r.steps).every(s => Object.hasOwn(m.steps, s)) && Array.isArray(r.corrections), 'Invalid reviewed steps or corrections');
  for (const [step, decision] of Object.entries(r.steps)) assert(typeof decision.accepted === 'boolean' && typeof decision.reason === 'string' && decision.reason.trim(), 'A review decision requires a reason');
  for (const correction of r.corrections) {
    assert(validHash(correction.observationSha256) && typeof correction.text === 'string' && correction.text.trim() && typeof correction.reason === 'string' && correction.reason.trim(), 'Correction must reference an original observation');
    const originals = SEMANTIC.flatMap(step => {
      const f = path.join(runPath(r.clipId, r.runId, repo), 'steps', step, `${step}.json`);
      return fs.existsSync(f) ? readJson(f).observations ?? [] : [];
    });
    assert(originals.some(o => sha(o) === correction.observationSha256), 'Correction references an unknown observation');
  }
  if (r.summary !== undefined) {
    assert(Object.keys(r.summary).every(k => ['description', 'tags'].includes(k)) && (r.summary.description === null || typeof r.summary.description === 'string')
      && Array.isArray(r.summary.tags) && r.summary.tags.every(t => typeof t === 'string'), 'Public summary is not allowlisted');
    for (const text of [r.summary.description, ...r.summary.tags].filter(t => t !== null)) assert(publicText(text) === text && text.length <= 2000, 'Public projection contains private or invalid text');
  }
  return m;
}
export function recordReview(r, repo = REPO) {
  validateReview(r, repo); const hash = sha(r); privateJson(reviewPath(r.clipId, hash, repo), r, true); return { reviewSha256: hash, clipId: r.clipId, runId: r.runId };
}
export function project(id, runId, review, repo = REPO) {
  assert(review.clipId === id && review.runId === runId && review.privacyReviewed === true, 'Projection requires privacy review of this exact run');
  const m = validateReview(review, repo); recordReview(review, repo);
  assert(review.summary, 'Select an explicit reviewed summary');
  const timing = readJson(path.join(runPath(id, runId, repo), 'steps/timing/timing.json')), video = timing.streams.find(s => s.type === 'video');
  const ref = { schemaVersion: 1, runId, manifestSha256: review.manifestSha256, inputSha256: m.input.sha256,
    extractor: m.extractor, evidenceType: 'measured-and-reviewed', measured: { fullDecode: m.steps.decode.state === 'complete', videoFrames: video.frames, timeBase: video.timeBase },
    reviewedDescription: review.summary.description, reviewedTags: review.summary.tags, privacyReviewed: true };
  // No raw OCR, transcript, embeddings, paths, source tags or private presence are projected.
  updateClip(id, { analysisRefs: [ref] }, repo); return { clipId: id, runId, projected: true };
}
function presence(clip, repo) {
  return { localMaster: fs.existsSync(mediaPath(clip, repo)), remote: 'unknown-until-cloud-verification' };
}
export async function buildSearch(repo = REPO) {
  const clips = listClips(repo), rows = [], sources = [], coverage = [];
  for (const clip of clips) {
    const add = row => rows.push({ clipId: clip.id, ...row });
    for (const h of clip.analysis) {
      if (h.summary) add({ evidenceType: 'historical-analysis', text: h.summary, startSeconds: null, endSeconds: null, attribution: h.source });
      if (h.transcript) add({ evidenceType: 'historical-transcript', text: h.transcript, startSeconds: null, endSeconds: null, attribution: h.source });
      for (const f of h.frames) add({ evidenceType: 'historical-analysis', text: f.text, startSeconds: f.seconds, endSeconds: f.seconds, attribution: h.source });
    }
    for (const g of clip.generations) if (g.prompt) add({ evidenceType: 'creation-prompt', text: g.prompt, startSeconds: null, endSeconds: null, attribution: g.source });
    for (const runId of listRuns(clip.id, repo)) {
      const m = verifyRun(clip.id, runId, repo), dir = runPath(clip.id, runId, repo), manifestSha256 = hashFile(path.join(dir, 'manifest.json'));
      sources.push({ clipId: clip.id, runId, manifestSha256 });
      const previewFile = path.join(dir, 'steps/preview/preview.mp4'), preview = fs.existsSync(previewFile) ? path.relative(repo, previewFile) : null;
      const previewInfoFile = path.join(dir, 'steps/preview/preview.json'), previewInfo = fs.existsSync(previewInfoFile) ? readJson(previewInfoFile) : null;
      coverage.push({ clipId: clip.id, runId, kind: clip.kind, states: Object.fromEntries(Object.entries(m.steps).map(([k, v]) => [k, v.state])),
        required: m.config.required, passes: Object.fromEntries(Object.entries(m.steps).map(([k, v]) => [k, { reason: v.reason, coverage: v.coverage }])),
        bytes: m.artifacts.reduce((s, a) => s + a.bytes, 0), preview, presence: presence(clip, repo) });
      const sceneFile = path.join(dir, 'steps/signal/scenes.json');
      if (fs.existsSync(sceneFile)) for (const s of readJson(sceneFile).streams) for (const span of s.spans) add({ runId, manifestSha256, evidenceType: 'measured-signal',
        text: `Scene span; ${s.consecutiveDuplicateFrames} consecutive duplicate frames in stream; ${s.cuts.length} cut candidates`, streamIndex: s.streamIndex,
        startSeconds: seconds(span.startPts, s.timeBase), endSeconds: span.endPts ? seconds(span.endPts, s.timeBase) : null, preview });
      for (const step of SEMANTIC) {
        const file = path.join(dir, 'steps', step, `${step}.json`); if (!fs.existsSync(file)) continue;
        for (const o of readJson(file).observations ?? []) {
          if (o.vector) validateVector(o.vector, m.config.adapters[step]?.settings.vectorDimensions);
          add({ runId, manifestSha256, observationSha256: sha(o), evidenceType: step === 'embeddings' || step === 'audio-content' ? 'similarity-candidate' : 'model-observation',
          extractor: step, text: o.text, originalText: o.originalText, normalizedText: o.normalizedText, startSeconds: o.startSeconds, endSeconds: o.endSeconds,
          streamIndex: o.streamIndex, frameIndices: o.frameIndices, confidence: o.confidence, preview,
          previewStartSeconds: previewInfo ? o.startSeconds - previewInfo.previewOriginSourceSeconds : null,
          previewEndSeconds: previewInfo ? o.endSeconds - previewInfo.previewOriginSourceSeconds : null,
          timingWarning: o.timingWarning ?? null, vadIntersections: o.vadIntersections,
          negativeFindingsSupported: false,
          sampledFrames: (o.frameIndices ?? []).map(i => {
            const f = previewInfo?.samples.find(f => f.streamIndex === o.streamIndex && f.frameIndex === i);
            assert(f, 'Indexed observation references a missing sampled frame');
            return { ...f, path: path.relative(repo, path.join(dir, 'steps/preview', f.path)) };
          }), sampling: previewInfo?.coverage ?? null, generation: o.generation,
          ...(o.vector ? { vector: o.vector, modelIdentitySha256: sha(m.config.adapters[step]) } : {}) });
        }
      }
      const reviewDir = safePath(repo, `data/clips/${clip.id}/reviews`);
      if (fs.existsSync(reviewDir)) for (const name of fs.readdirSync(reviewDir).sort()) {
        if (!/^[a-f0-9]{64}\.json$/.test(name)) throw new Error('Invalid review artifact');
        const review = readJson(safePath(reviewDir, name)); assert(sha(review) === name.slice(0, -5), 'Review hash mismatch');
        if (review.runId !== runId) continue;
        validateReview(review, repo);
        for (const c of review.corrections) add({ runId, manifestSha256, evidenceType: 'human-correction', revisesObservationSha256: c.observationSha256, text: c.text, preview, startSeconds: null, endSeconds: null });
      }
    }
  }
  const index = { schemaVersion: 1, builtAt: now(), catalogSha256: sha(clips), sources, rows };
  privateJson(local(repo, 'search.json'), index);
  privateJson(local(repo, 'coverage.json'), { schemaVersion: 1, builtAt: now(), clips: clips.length, analyzedClips: new Set(coverage.map(r => r.clipId)).size, runs: coverage });
  const body = coverage.map(r => `<tr><td>${escape(r.clipId.slice(0, 17))}</td><td>${escape(r.kind)}</td><td>${Object.entries(r.states).map(([k, v]) => `${escape(k)}: ${escape(v)}${r.passes[k].coverage?.sampledFrames !== undefined ? ` (${r.passes[k].coverage.sampledFrames} sampled frames)` : ''}`).join('<br>')}</td><td>${(r.bytes / 1048576).toFixed(1)} MiB</td><td>${r.preview ? `<a href="../../../${escape(r.preview)}">Preview</a>` : 'Needs review'}</td></tr>`).join('');
  const html = '<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; media-src \'self\'; img-src \'self\'"><title>Private clip analysis coverage</title>'
    + '<style>body{background:#15191f;color:#eef3f8;font:14px system-ui;padding:24px}table{border-collapse:collapse}td,th{padding:12px;border-bottom:1px solid #445;text-align:left}a{color:#8de2ed}</style>'
    + `<h1>Clip analysis coverage</h1><p>${clips.length} catalog clips; ${new Set(coverage.map(r => r.clipId)).size} analyzed. Pending and review states are not completed acceptance.</p><table><tr><th>Clip</th><th>Kind</th><th>Passes</th><th>Retained size</th><th>Review</th></tr>${body}</table>`;
  fs.mkdirSync(path.dirname(local(repo, 'coverage.html')), { recursive: true, mode: 0o700 }); fs.writeFileSync(local(repo, 'coverage.html'), html, { mode: 0o600 });
  return { rows: rows.length, runs: sources.length, search: 'data/clips/analysis/search.json', dashboard: 'data/clips/analysis/coverage.html' };
}
function loadSearch(repo) {
  const index = readJson(local(repo, 'search.json')); assert(index.schemaVersion === 1 && index.catalogSha256 === sha(listClips(repo)), 'Private search index is stale; rebuild it');
  const expected = listClips(repo).flatMap(c => listRuns(c.id, repo).map(runId => `${c.id}/${runId}`)).sort();
  assert(sha(expected) === sha(index.sources.map(s => `${s.clipId}/${s.runId}`).sort()), 'Private search index omits an analysis run; rebuild it');
  for (const s of index.sources) assert(hashFile(path.join(runPath(s.clipId, s.runId, repo), 'manifest.json')) === s.manifestSha256, 'Indexed analysis manifest changed');
  return index;
}
export function searchPrivate(query, repo = REPO) {
  const words = String(query).normalize('NFKC').toLowerCase().split(/\s+/).filter(Boolean); assert(words.length > 0, 'Provide search terms');
  return loadSearch(repo).rows.filter(r => words.every(w => `${r.text} ${r.normalizedText ?? ''}`.normalize('NFKC').toLowerCase().includes(w)))
    .slice(0, 200).map(({ vector, ...r }) => ({ ...r, presence: presence(readClip(r.clipId, repo), repo) }));
}
export function neighbors(id, runId, repo = REPO) {
  const rows = loadSearch(repo).rows.filter(r => r.vector), query = rows.filter(r => r.clipId === id && r.runId === runId);
  assert(query.length, 'No provisioned embeddings for this run');
  for (const r of rows) validateVector(r.vector);
  const cosine = (a, b) => { validateVector(b, a.length); return a.reduce((n, v, i) => n + v * b[i], 0); };
  return rows.filter(r => r.clipId !== id).flatMap(r => {
    const matching = query.filter(q => q.modelIdentitySha256 === r.modelIdentitySha256);
    if (!matching.length) return [];
    const { vector, ...rest } = r; return [{ ...rest, similarity: Math.max(...matching.map(q => cosine(q.vector, vector))), interpretation: 'Candidate similarity, not probability or proof of shared source bytes' }];
  }).sort((a, b) => b.similarity - a.similarity).slice(0, 40);
}
export function rankEmbeddings(vector, candidates, modelId, dimensions = vector.length) {
  validateVector(vector, dimensions);
  return candidates.filter(r => r.modelIdentitySha256 === modelId).map(({ vector: v, ...r }) => {
    validateVector(v, dimensions);
    return { ...r, similarity: v.reduce((s, n, i) => s + n * vector[i], 0), interpretation: 'Uncalibrated text/image similarity candidate' };
  }).sort((a, b) => b.similarity - a.similarity).slice(0, 40);
}
export async function similarText(query, supplied, repo = REPO, { runIds } = {}) {
  assert(typeof query === 'string' && query.trim(), 'Provide a text query'); const config = configFor(supplied);
  if (runIds !== undefined) assert(Array.isArray(runIds) && runIds.length > 0
    && runIds.every(id => /^run_[a-f0-9]{64}$/.test(id)), 'Provide explicit run identities for bounded retrieval');
  const index = loadSearch(repo), modelId = sha(config.adapters.embeddings);
  const candidates = index.rows.filter(r => r.vector && r.modelIdentitySha256 === modelId && (!runIds || runIds.includes(r.runId)));
  assert(candidates.length, 'Index has no embeddings from this exact pinned model configuration');
  return withLock(repo, 'model-worker', async () => {
    const parent = local(repo, 'queries'); fs.mkdirSync(parent, { recursive: true, mode: 0o700 });
    const dir = fs.mkdtempSync(path.join(parent, 'query-'));
    const vector = await (await import('./clip-analysis-adapters.mjs')).embedText(query, config, dir);
    return rankEmbeddings(vector, candidates, modelId, config.adapters.embeddings.settings.vectorDimensions)
      .map(r => ({ ...r, presence: presence(readClip(r.clipId, repo), repo) }));
  });
}
export function validatePilot(pilot, repo = REPO) {
  assert(pilot?.schemaVersion === 1 && pilot.reviewedBy === 'human' && Number.isFinite(Date.parse(pilot.reviewedAt))
    && Array.isArray(pilot.samples) && pilot.samples.length >= 24 && new Set(pilot.samples.map(s => s.clipId)).size === pilot.samples.length, 'Profile freeze requires a reviewed 24-clip pilot');
  const config = configFor(pilot.config);
  assert(pilot.qualificationVersion === 2, 'Semantic qualification requires versioned speech and retrieval review evidence');
  assert([...BASELINE, 'ocr', 'transcript', 'observations', 'embeddings'].every(s => config.required.includes(s)), 'Cleanup profile must cover baseline, OCR, speech, visual meaning and retrieval');
  const labels = new Set(); let extractorSha256;
  for (const sample of pilot.samples) {
    const m = verifyRun(sample.clipId, sample.runId, repo);
    extractorSha256 ??= extractorIdentity(m);
    assert(extractorIdentity(m) === extractorSha256, 'Pilot mixes extractor/runtime versions; rerun with the frozen candidate');
    assert(m.configSha256 === sha(config) && hashFile(path.join(runPath(sample.clipId, sample.runId, repo), 'manifest.json')) === sample.manifestSha256,
      'Pilot sample does not match the selected profile and manifest');
    assert(sample.accepted === true && sample.timingReviewed === true && sample.semanticReviewed === true && sample.usefulnessReviewed === true
      && Array.isArray(sample.labels) && typeof sample.notes === 'string', 'Pilot sample has unresolved human review');
    assert(config.required.every(s => ['complete', 'needs-review', 'not-applicable'].includes(m.steps[s].state)), 'Pilot has an unrun required pass');
    for (const step of ['ocr', 'observations', 'embeddings']) assert(m.steps[step].coverage?.sampledFrames > 0, 'Pilot visual pass has no sampled-frame evidence');
    assert(m.steps.observations.coverage.observations > 0
      && m.steps.embeddings.coverage.observations === m.steps.embeddings.coverage.sampledFrames,
    'Pilot lacks descriptions or per-sample retrieval vectors');
    if (m.steps.transcript.state !== 'not-applicable') assert(m.steps.transcript.coverage?.speechEvidenceVersion === 2,
      'Pilot speech lacks qualified VAD and original-time evidence');
    assert(sample.reviewSha256 && validHash(sample.reviewSha256), 'Pilot sample needs a separate immutable human review');
    const review = readJson(reviewPath(sample.clipId, sample.reviewSha256, repo));
    assert(sha(review) === sample.reviewSha256 && review.runId === sample.runId && review.manifestSha256 === sample.manifestSha256, 'Pilot review identity mismatch');
    validateReview(review, repo);
    assert(config.required.filter(s => m.steps[s].state === 'needs-review').every(s => review.steps[s]?.accepted === true), 'Pilot has an unaccepted model pass');
    sample.labels.forEach(x => labels.add(x));
  }
  for (const label of ['portrait', 'landscape', 'short', 'long', 'speech', 'music', 'silence', 'no-audio', 'visible-text', 'people', 'animation', 'static', 'moving', 'cuts', 'known-defects'])
    assert(labels.has(label), `Pilot lacks reviewed coverage: ${label}`);
  assert(['rotation', 'HDR', 'VFR', 'corruption', 'silent-audio', 'no-audio', 'delayed-audio', 'silence-gaps', 'failed-asr', 'changed-pins', 'incompatible-vectors', 'interrupted-run'].every(k => pilot.fixtures?.some(f => {
    if (f.case !== k || f.passed !== true) return false;
    const evidence = evidenceFile(f.evidence, repo);
    return evidence.passed === true && evidence.case === k;
  })), 'Pilot needs verified edge-case fixtures');
  assert(pilot.retrieval?.reviewed === true && typeof pilot.retrieval.acceptanceCriteria === 'string' && pilot.retrieval.acceptanceCriteria.trim()
    && Array.isArray(pilot.retrieval.queries) && pilot.retrieval.queries.length > 0, 'Retrieval targets must come from a labeled, reviewed pilot');
  for (const q of pilot.retrieval.queries) {
    assert(typeof q.query === 'string' && q.query.trim() && q.accepted === true && Array.isArray(q.expectedMatches)
      && (q.expectedMatches.length > 0 || q.expectedNoMatch === true)
      && Array.isArray(q.falseMatches) && Array.isArray(q.missedEvents) && Array.isArray(q.timingErrors)
      && typeof q.notes === 'string' && q.notes.trim(), 'Retrieval query needs labeled matches, misses, timing errors and a review decision');
    const evidence = evidenceFile(q.evidence, repo);
    assert(evidence.query === q.query && evidence.configSha256 === sha(config) && Array.isArray(evidence.results), 'Retrieval evidence does not match the reviewed query/profile');
    for (const match of q.expectedMatches) assert(pilot.samples.some(s => s.clipId === match.clipId && s.runId === match.runId)
      && Number.isFinite(match.startSeconds) && Number.isFinite(match.endSeconds) && match.endSeconds >= match.startSeconds, 'Retrieval label lacks a pilot source-time range');
  }
  return { profileSha256: sha(pilot), configSha256: sha(config), extractorSha256 };
}
export function freezeProfile(pilot, repo = REPO) {
  const result = validatePilot(pilot, repo); privateJson(local(repo, `profiles/frozen-${result.profileSha256}.json`), pilot, true); return result;
}
function evidenceFile(entry, repo) {
  assert(entry && typeof entry.path === 'string' && entry.path.startsWith('data/') && validHash(entry.sha256)
    && Number.isSafeInteger(entry.bytes), 'Missing private audit evidence');
  const file = safePath(repo, entry.path); verifyFile(file, entry); return readJson(file);
}
export function readiness(policy, repo = REPO, { verification } = {}) {
  assert(policy?.schemaVersion === 1 && validHash(policy.backupSetSha256) && validHash(policy.profileSha256)
    && Array.isArray(policy.clips) && policy.clips.length > 0, 'Invalid cleanup-readiness policy');
  const blockers = [], block = message => blockers.push(message); let set, pilot, audit, access, index;
  const attempt = (label, f) => { try { return f(); } catch { block(label); return null; } };
  const setFile = safePath(repo, `data/clips/cloud/backup-sets/${policy.backupSetSha256}.json`);
  set = attempt('Complete backup-set manifest is missing or invalid', () => { assert(hashFile(setFile) === policy.backupSetSha256, 'hash'); return validateBackupSet(readJson(setFile)); });
  pilot = attempt('Reviewed frozen extraction profile is missing or invalid', () => { const p = readJson(local(repo, `profiles/frozen-${policy.profileSha256}.json`)); assert(sha(p) === policy.profileSha256, 'hash');
    const validated = validatePilot(p, repo); return { ...p, frozenExtractorSha256: validated.extractorSha256 }; });
  if (!verification || verification.backupSetSha256 !== policy.backupSetSha256 || !set || verification.members !== set.objects.length
    || verification.bucket !== set.bucket || !Number.isFinite(Date.parse(verification.verifiedAt)) || Date.now() - Date.parse(verification.verifiedAt) > 3600000 || Date.parse(verification.verifiedAt) > Date.now())
    block('Current remote-generation verification is required; run cloud readiness');
  index = attempt('A current locally retained search index is required', () => loadSearch(repo));
  audit = attempt('Dependency audit evidence is missing or changed', () => evidenceFile(policy.dependencyAudit, repo));
  access = attempt('Independent recovery access evidence is missing or changed', () => evidenceFile(policy.accessEvidence, repo));
  if (access?.independentlyRecoverable !== true || !Number.isFinite(Date.parse(access?.reviewedAt))) block('Off-machine access recovery has not been attested');
  const locationsFile = safePath(repo, 'data/clips/locations.json'), locations = fs.existsSync(locationsFile) ? readJson(locationsFile) : null;
  if (!audit || audit.catalogSha256 !== sha(listClips(repo)) || audit.usesSha256 !== sha(listUses(repo)) || audit.locationsSha256 !== sha(locations))
    block('Dependency audit does not cover the current catalog, uses and historical locations');
  for (const entry of [policy.dependencyAudit, policy.accessEvidence]) if (!set?.objects.some(o => o.sha256 === entry?.sha256 && o.bytes === entry?.bytes)) block('Audit/access evidence is not included in this backup set');
  if (pilot) {
    const file = local(repo, `profiles/frozen-${policy.profileSha256}.json`);
    if (!set?.objects.some(o => o.sha256 === hashFile(file))) block('Frozen pilot review is not backed up');
  }
  const rehearsalDir = safePath(repo, 'data/clips/cloud/rehearsals'), rehearsals = fs.existsSync(rehearsalDir)
    ? fs.readdirSync(rehearsalDir).filter(n => n.endsWith('.json')).map(n => readJson(safePath(rehearsalDir, n))) : [];
  const rows = [], proposed = [];
  const retainedBytes = attempt('Retained metadata/analysis footprint could not be measured', () => {
    const roots = [safePath(repo, 'catalog'), local(repo, '.')];
    for (const clip of listClips(repo)) for (const kind of ['analysis', 'reviews', 'generations']) roots.push(safePath(repo, `data/clips/${clip.id}/${kind}`));
    return roots.reduce((total, root) => total + filesUnder(root).reduce((n, f) => n + fs.statSync(path.join(root, f)).size, 0), 0);
  });
  for (const item of policy.clips) {
    const reasons = [], fail = x => reasons.push(x); let clip, m;
    try { clip = readClip(item.clipId, repo); m = verifyRun(item.clipId, item.runId, repo); } catch { fail('Missing or corrupt catalog/analysis evidence'); }
    if (clip && m) {
      if (!pilot || m.configSha256 !== sha(configFor(pilot.config))) fail('Run does not use the frozen required profile');
      if (pilot && extractorIdentity(m) !== pilot.frozenExtractorSha256) fail('Run does not use the frozen extractor/runtime versions');
      const manifestHash = hashFile(path.join(runPath(clip.id, m.runId, repo), 'manifest.json'));
      const member = set?.clips.find(c => c.clipId === clip.id);
      if (member?.catalogSha256 !== sha(clip)) fail('Backup catalog differs from current clip metadata');
      if (!set?.objects.some(o => o.clipId === clip.id && o.runId === m.runId && o.kind === 'analysis-manifest' && o.sha256 === manifestHash)) fail('Required analysis run is not backed up');
      for (const a of m.artifacts) if (!set?.objects.some(o => o.clipId === clip.id && o.runId === m.runId && o.artifactPath === a.path && o.sha256 === a.sha256 && o.bytes === a.bytes)) fail('Required artifact is not backed up');
      let review;
      if (item.reviewSha256) try { review = readJson(reviewPath(clip.id, item.reviewSha256, repo)); assert(sha(review) === item.reviewSha256, 'hash'); validateReview(review, repo);
        assert(set?.objects.some(o => o.sha256 === hashFile(reviewPath(clip.id, item.reviewSha256, repo))), 'review backup');
      } catch { review = null; fail('Human review is invalid or not backed up'); }
      for (const step of m.config.required) {
        const state = m.steps[step];
        if (state.state === 'needs-review' && !(review?.runId === m.runId && review.steps[step]?.accepted === true)) fail(`Unresolved required review: ${step}`);
        else if (!['complete', 'not-applicable', 'needs-review'].includes(state.state)) fail(`Required pass unfinished: ${step}`);
      }
      if (!index?.sources.some(s => s.clipId === clip.id && s.runId === m.runId && s.manifestSha256 === manifestHash)) fail('Required run is absent from the local search index');
      const preview = path.join(runPath(clip.id, m.runId, repo), 'steps/preview/preview.mp4'); if (!fs.existsSync(preview)) fail('A verified seekable preview must remain local');
      const format = formatSignature(clip, m, repo), types = [...new Set(m.artifacts.map(a => path.extname(a.path)))];
      if (!rehearsals.some(r => r.backupSetSha256 === policy.backupSetSha256
        && Number.isFinite(Date.parse(r.restoredAt)) && Date.parse(r.restoredAt) <= Date.now()
        && r.support?.transitiveEvidenceVerified === true
        && r.emptyRootRecovery && r.hashesVerified && r.fullDecode && r.searchRebuilt
        && r.formats?.some(f => f.formatSignature === format && types.every(type => f.artifactTypes.includes(type))))) fail('No successful recovery rehearsal for this format and artifact set');
      const dependency = audit?.clips?.find(d => d.clipId === clip.id);
      if (!dependency || !['activeEditsReviewed', 'archivesReviewed', 'originalPathsReviewed', 'alternatesReviewed', 'sharedSourcesReviewed'].every(k => dependency[k] === true)) fail('Source/edit/archive dependency review is incomplete');
      for (const use of listUses(repo).filter(u => u.clipId === clip.id && u.status === 'planned')) {
        const decision = dependency?.pendingUses?.find(d => d.useId === use.id);
        if (!decision || !['restores-by-clip-id', 'materialized-verified', 'confirmed-inactive'].includes(decision.resolution)) fail('Pending edit dependency is unresolved');
        else try { evidenceFile(decision.evidence, repo); assert(set?.objects.some(o => o.sha256 === decision.evidence.sha256), 'backup'); } catch { fail('Pending edit dependency evidence is missing or unbacked'); }
      }
      const source = mediaPath(clip, repo);
      try { verifyFile(source, clip); } catch { fail('Original master is absent or its identity changed'); }
      try { verifyClipSnapshots(clip, repo); } catch { fail('Local creation evidence is missing or changed'); }
      if (!reasons.length) proposed.push({ clipId: clip.id, path: path.relative(repo, source), sha256: clip.sha256, bytes: clip.bytes,
        backupSetSha256: policy.backupSetSha256, runId: m.runId, preserve: 'Analysis, previews, catalog, reviews and all historical workspace/archive copies' });
    }
    rows.push({ clipId: item.clipId, ready: reasons.length === 0, blockers: [...new Set(reasons)] });
  }
  if (!Number.isSafeInteger(policy.retention?.maximumBytes) || retainedBytes === null || retainedBytes > policy.retention.maximumBytes) block('Retained analysis exceeds the reviewed storage plan');
  const report = { schemaVersion: 1, createdAt: now(), ready: blockers.length === 0 && rows.every(r => r.ready), blockers: [...new Set(blockers)], rows,
    retainedBytes, retentionScope: 'All local catalog, analysis, search, reviews, creation snapshots and retained analysis attempts; excludes original media and workspace copies',
    proposedCleanup: blockers.length ? [] : proposed, proposedSavingsBytes: blockers.length ? 0 : proposed.reduce((s, p) => s + p.bytes, 0),
    authorization: 'Report only. Explicit cleanup authorization is still required; no deletion is performed.' };
  privateJson(local(repo, 'cleanup-readiness.json'), report); return report;
}
export async function viewsMain(verb, args, repo = REPO) {
  if (verb === 'index' && !args.length) return buildSearch(repo);
  if (verb === 'search' && args.length) return searchPrivate(args.join(' '), repo);
  if (verb === 'neighbors' && args.length === 2) return neighbors(args[0], args[1], repo);
  if (verb === 'project' && args.length === 3) return project(args[0], args[1], readJson(safePath(repo, args[2])), repo);
  if (verb === 'record-review' && args.length === 1) return recordReview(readJson(safePath(repo, args[0])), repo);
  if (verb === 'freeze-profile' && args.length === 1) return freezeProfile(readJson(safePath(repo, args[0])), repo);
  if (verb === 'readiness' && args.length === 1) return readiness(readJson(safePath(repo, args[0])), repo);
  if (verb === 'review-template' && args.length === 2) {
    const m = verifyRun(args[0], args[1], repo); return { schemaVersion: 1, clipId: args[0], runId: args[1],
      manifestSha256: hashFile(path.join(runPath(args[0], args[1], repo), 'manifest.json')), reviewedBy: 'human', reviewedAt: null, privacyReviewed: false,
      steps: Object.fromEntries(Object.entries(m.steps).filter(([, s]) => s.state === 'needs-review').map(([k]) => [k, { accepted: false, reason: '' }])), corrections: [], summary: { description: null, tags: [] } };
  }
  if (verb === 'status' && !args.length) {
    const file = local(repo, 'queue.json'), queue = fs.existsSync(file) ? readJson(file) : { jobs: [] };
    return { jobs: queue.jobs.length, states: (await import('./clip-analysis.mjs')).queueCounts(queue.jobs),
      coverage: fs.existsSync(local(repo, 'coverage.json')) ? readJson(local(repo, 'coverage.json')) : null };
  }
  throw new Error('Invalid private analysis view arguments');
}
