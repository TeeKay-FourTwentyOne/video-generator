import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { REPO, importClip, run, readJson, hashFile, readClip } from './clip-library.mjs';
import { audioMapping, normalizeSpeech } from './clip-analysis-speech.mjs';
import { validateVector, validateObservations, pinAdapters } from './clip-analysis-adapters.mjs';
import { rankEmbeddings, buildSearch, searchPrivate, project, validatePilot, recordReview, freezeProfile, similarText } from './clip-analysis-views.mjs';
import { analyzeClip } from './clip-analysis.mjs';
import { configFor, runPath, verifyRun, sha, privateJson, fileIdentity, BASELINE } from './clip-analysis-store.mjs';
import { execute, resolveBinary } from './clip-analysis-process.mjs';

const stream = { index: 2, sample_rate: '48000', time_base: '1/48000', start_time: '1' };
const frames = [{ pts: '96000', nb_samples: '48000' }, { pts: '240000', nb_samples: '48000' }];
const mapping = () => audioMapping(frames, stream, 64000);
const token = (text, from, to, rawFrom = from) => ({ id: 10, bytesHex: Buffer.from(text).toString('hex'), p: .7,
  special: false, offsets: { from, to }, rawOffsets: { from: rawFrom, to: rawFrom + to - from } });
const raw = () => ({ schemaVersion: 2, contract: 'whisper.cpp-original-time-v1', sampleRate: 16000, sampleCount: 64000,
  timing: { unit: 'milliseconds', segments: 'original-resampled-audio', tokens: 'original-resampled-audio', rawTokens: 'vad-processed-audio' },
  language: { hypothesis: 'en', confidence: null }, vad: [{ from: 0, to: 1000 }, { from: 3000, to: 4000 }],
  transcription: [{ text: ' Door opens', offsets: { from: 3000, to: 4000 }, tokens: [token(' Door', 3000, 3500, 1000), token(' opens', 3500, 4000, 1500)] }] });
const context = { sourceSha256: 'a'.repeat(64), model: 'fixture' };

test('speech uses first decoded PTS, keeps silence gaps and maps shortened token offsets separately', () => {
  const m = mapping(), output = normalizeSpeech(raw(), m, context), o = output.observations[0];
  assert.equal(m.sourceOriginSeconds, 2); // Container start_time is intentionally different.
  assert.deepEqual(m.gaps.map(g => [g.startSeconds, g.endSeconds]), [[3, 5]]);
  assert.equal(o.startSeconds, 5); assert.equal(o.endSeconds, 6);
  assert.equal(o.tokens[0].startSeconds, 5); assert.equal(o.tokens[0].rawOffsets.from, 1000);
  assert.equal(o.words[0].startSeconds, 5); assert.equal(o.words[1].endSeconds, 6);
  assert.equal(Number(o.sourceStart.numerator) / Number(o.sourceStart.denominator), 5);
  assert.deepEqual(output.report.vadSpans.map(s => [s.startSeconds, s.endSeconds]), [[2, 3], [5, 6]]);
  assert.throws(() => normalizeSpeech({ ...raw(), timing: { ...raw().timing, tokens: 'vad-processed-audio' } }, m, context), /timestamp contract/);
  assert.throws(() => audioMapping(frames, stream, 32000), /duration/);
  assert.throws(() => audioMapping([{ pts: '0', nb_samples: '48000' }, { pts: '24000', nb_samples: '48000' }], stream, 32000), /Overlapping/);
});
test('empty ASR, no VAD, unavailable word timing and invalid output remain distinct evidence', () => {
  const empty = normalizeSpeech({ ...raw(), vad: [], transcription: [] }, mapping(), context);
  assert.equal(empty.report.asrState, 'empty-transcript'); assert.equal(empty.report.vadState, 'no-speech-detected');
  assert.equal(empty.report.contentClassification.music, 'unrun'); assert.equal(empty.report.contentClassification.sungVocals, 'unrun');
  const speechWithoutText = normalizeSpeech({ ...raw(), transcription: [] }, mapping(), context);
  assert.equal(speechWithoutText.report.vadState, 'speech-candidates');
  const r = raw(); r.transcription[0].tokens[0].offsets = null;
  const output = normalizeSpeech(r, mapping(), context);
  assert.equal(output.observations[0].words[0].timingState, 'unavailable');
  assert.equal(output.observations[0].words[0].startSeconds, undefined);
  for (const change of [{ vad: [], transcription: raw().transcription }, { transcription: null }, { sampleCount: 1 }])
    assert.throws(() => normalizeSpeech({ ...raw(), ...change }, mapping(), context));
  const outOfBounds = raw(); outOfBounds.transcription[0].offsets.to = 9000;
  assert.throws(() => normalizeSpeech(outOfBounds, mapping(), context), /exceeds/);
  const crossing = raw(); crossing.transcription[0].tokens[0].offsets = { from: 500, to: 3500 };
  const warning = normalizeSpeech(crossing, mapping(), context).observations[0].words[0];
  assert.equal(warning.timingState, 'ambiguous-vad-gap'); assert.equal(warning.vadIntersections.length, 2);
  // Silero's final 512-sample probability window can extend beyond real audio.
  // Keep the original estimate without exposing imaginary source samples.
  const padded = raw(); padded.sampleCount = 62613; padded.vad = [{ from: 100, to: 3940 }];
  padded.transcription = [{ text: ' End.', offsets: { from: 3400, to: 3940 }, tokens: [token(' End.', 3400, 3950)] }];
  const boundedMapping = { ...mapping(), sampleCount: 62613 }, bounded = normalizeSpeech(padded, boundedMapping, context);
  const end = bounded.observations[0], word = end.words[0];
  assert.equal(end.rawOffsets.to, 3940); assert.equal(word.rawOffsets.to, 3950);
  assert.equal(word.timingState, 'ambiguous-source-boundary');
  assert.equal(word.endSeconds, boundedMapping.sourceOriginSeconds + 62613 / 16000);
  assert.equal(Number(word.sourceEnd.numerator) / Number(word.sourceEnd.denominator), word.endSeconds);
  assert.ok(word.boundaryAdjustment.endTrimmedMilliseconds > 36);
  padded.transcription[0].tokens[0].offsets.to = 3960;
  assert.throws(() => normalizeSpeech(padded, boundedMapping, context), /exceeds/);
});
test('retrieval rejects malformed vectors and mismatched dimensions within a model identity', () => {
  for (const vector of [[], [0, 0], [NaN, 1], [Infinity], [2, 0], [1, 0, 0]]) assert.throws(() => validateVector(vector, 2));
  const candidate = { clipId: 'fixture', modelIdentitySha256: 'same', vector: [1, 0], startSeconds: 7, endSeconds: 7, previewStartSeconds: 2, preview: 'private/preview.mp4' };
  assert.equal(rankEmbeddings([1, 0], [candidate], 'same')[0].previewStartSeconds, 2);
  assert.equal(rankEmbeddings([1, 0], [candidate], 'changed-pins').length, 0);
  assert.throws(() => rankEmbeddings([1, 0], [{ ...candidate, vector: [1, 0, 0] }], 'same'), /dimensions/);
});
test('visual evidence rejects unordered windows and a falsely extended action interval', () => {
  const samples = [{ streamIndex: 0, frameIndex: 0, seconds: 2 }, { streamIndex: 0, frameIndex: 5, seconds: 3 }];
  const o = { ...context, evidenceType: 'model-observation', streamIndex: 0, startSeconds: 2, endSeconds: 3, text: 'A door', frameIndices: [0, 5],
    confidence: { source: 'fixture', value: null, interpretation: 'uncalibrated model score' } };
  const args = { sourceSha256: context.sourceSha256, step: 'observations', streams: [{ index: 0, start_time: '2', duration: '5' }], samples };
  validateObservations({ schemaVersion: 1, observations: [o] }, args);
  for (const change of [{ frameIndices: [5, 0] }, { endSeconds: 4 }, { frameIndices: [0, 0] }])
    assert.throws(() => validateObservations({ schemaVersion: 1, observations: [{ ...o, ...change }] }, args));
});
test('Python windows overlap once, preserve stream identity and avoid a redundant final singleton', () => {
  const script = `import importlib.util
s=importlib.util.spec_from_file_location('models', 'tools/production/clip-analysis-model.py')
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
frames=[dict(streamIndex=0,frameIndex=i,seconds=i) for i in range(7)]
assert [[f['frameIndex'] for f in w] for w in m.temporal_windows(frames,4)] == [[0,1,2,3],[3,4,5,6]]
frames.append(dict(streamIndex=1,frameIndex=0,seconds=0))
assert len(list(m.temporal_windows(frames,4)))==3
try: list(m.temporal_windows([frames[1],frames[0]],4)); raise AssertionError('accepted unordered frames')
except ValueError: pass
`;
  run('python3', ['-B', '-c', script], { cwd: REPO });
});

function fixture(t) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'semantic-test-'));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  const source = path.join(repo, 'delayed.mkv');
  run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=blue:s=96x64:r=8:d=6',
    '-itsoffset', '2', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono:d=4', '-c:v', 'libx264', '-c:a', 'pcm_s16le', '-output_ts_offset', '5', source]);
  const clip = importClip(source, {}, repo), executable = path.join(repo, 'speech-fixture');
  fs.writeFileSync(executable, `#!${process.execPath}\nconst fs=require('fs'); const [request,out]=process.argv.slice(2); const r=JSON.parse(fs.readFileSync(request));
const raw=${JSON.stringify(raw())}; raw.sampleCount=fs.statSync(r.audioFile).size/4; fs.writeFileSync(out,JSON.stringify(raw));\n`, { mode: 0o700 });
  const weights = path.join(repo, 'synthetic-weights'); fs.writeFileSync(weights, 'No real model');
  const config = pinAdapters({ limits: { minFreeBytes: 1024 * 1024, timeoutSeconds: 60, maxOutputBytes: 64 * 1024 * 1024 },
    adapters: { transcript: { kind: 'whisper.cpp', executable, files: [executable, weights],
      identity: { runtimeRevision: 'fixture-v1', model: 'synthetic speech evidence', license: 'fixture', quantization: 'none', preprocessing: 'mono 16000' },
      settings: { modelFile: weights, vadModelFile: weights, bridgeSource: executable, timestampContract: 'whisper.cpp-original-time-v1',
        vadThreshold: .5, vadMinSpeechMs: 250, vadMinSilenceMs: 100, vadPadMs: 30, vadOverlapSeconds: .1 } } } });
  return { repo, clip, source, executable, config };
}
test('delayed nonzero-start audio survives resampling, private search, projection and changed pins', async t => {
  const f = fixture(t), first = await analyzeClip(f.clip.id, f.repo, { config: f.config });
  assert.equal(first.status, 'complete', JSON.stringify(first));
  const dir = runPath(f.clip.id, first.runId, f.repo), m = verifyRun(f.clip.id, first.runId, f.repo);
  const speech = readJson(path.join(dir, 'steps/transcript/transcript.json'));
  assert.equal(speech.reports[0].mapping.sourceOriginSeconds, 7);
  assert.equal(speech.observations[0].startSeconds, 10);
  await buildSearch(f.repo); const matches = searchPrivate('Door', f.repo);
  assert.equal(matches[0].startSeconds, 10); assert.equal(matches[0].previewStartSeconds, 5);
  const review = { schemaVersion: 1, clipId: f.clip.id, runId: first.runId, manifestSha256: hashFile(path.join(dir, 'manifest.json')),
    reviewedBy: 'human', reviewedAt: new Date().toISOString(), privacyReviewed: false, steps: {}, corrections: [], summary: { description: 'Synthetic fixture', tags: [] } };
  assert.throws(() => project(f.clip.id, first.runId, review, f.repo), /privacy review/);
  project(f.clip.id, first.runId, { ...review, privacyReviewed: true }, f.repo);
  const projected = readClip(f.clip.id, f.repo);
  assert.ok(!JSON.stringify(projected).includes('Door opens')); assert.equal(projected.analysis.length, 0);
  fs.appendFileSync(f.executable, '\n// changed fixture\n');
  await assert.rejects(analyzeClip(f.clip.id, f.repo, { config: f.config }), /hash or size mismatch/);
  const pinned = pinAdapters(f.config); assert.notEqual(sha(pinned), sha(f.config));
  assert.equal(m.steps.transcript.coverage.speechEvidenceVersion, 2);
});
test('offline model sandbox denies an attempted socket even to loopback', { skip: process.platform !== 'darwin' }, async t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'analysis-network-test-')); t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  await execute(resolveBinary(process.execPath), ['-e', "const s=require('net').connect(9,'127.0.0.1');s.on('error',e=>process.exit(e.code==='EPERM'?0:1));s.on('connect',()=>process.exit(2));"],
    { dir, config: configFor({ limits: { minFreeBytes: 1024, timeoutSeconds: 10 } }), commands: [] }, { networkDenied: true });
});
test('raw OCR, speech and visual prose cannot flow into the public projection', async t => {
  const f = fixture(t), script = path.join(f.repo, 'private-observations.cjs');
  fs.writeFileSync(script, `const fs=require('fs');const[rp,op]=process.argv.slice(2);const r=JSON.parse(fs.readFileSync(rp));
const text='raw_'+r.step+'_private_fixture', visual=r.step!=='transcript';const f=r.samples[0];const s=r.streams.find(s=>s.codec_type===(visual?'video':'audio'));
const time=visual?f.seconds:Number(s.start_time);const o={sourceSha256:r.sourceSha256,evidenceType:'model-observation',streamIndex:s.index,startSeconds:time,endSeconds:time,text,
confidence:{source:'fixture',value:null,interpretation:'uncalibrated model score'},...(visual?{frameIndices:[f.frameIndex]}:{}),...(r.step==='ocr'?{originalText:text,boxNormalized:[0,0,1,1]}:{})};
fs.writeFileSync(op,JSON.stringify({schemaVersion:1,observations:[o]}));`);
  const a = { kind: 'json-command', executable: process.execPath, files: [script], settings: { args: [script] },
    identity: { runtimeRevision: 'fixture', model: 'fixture', license: 'fixture', quantization: 'none', preprocessing: 'none' } };
  const config = pinAdapters({ ...f.config, adapters: { ocr: a, transcript: structuredClone(a), observations: structuredClone(a) } });
  const out = await analyzeClip(f.clip.id, f.repo, { config }); assert.equal(out.status, 'complete', JSON.stringify(out));
  await buildSearch(f.repo); assert.equal(searchPrivate('private_fixture', f.repo).length, 3);
  const review = { schemaVersion: 1, clipId: f.clip.id, runId: out.runId,
    manifestSha256: hashFile(path.join(runPath(f.clip.id, out.runId, f.repo), 'manifest.json')), reviewedBy: 'human', reviewedAt: new Date().toISOString(),
    privacyReviewed: true, steps: {}, corrections: [], summary: { description: 'Reviewed synthetic pattern', tags: [] } };
  project(f.clip.id, out.runId, review, f.repo);
  assert.ok(!JSON.stringify(readClip(f.clip.id, f.repo)).includes('private_fixture'));
  assert.throws(() => project(f.clip.id, out.runId, { ...review, summary: { ...review.summary, observations: ['raw fixture'] } }, f.repo), /allowlisted/);
});

test('freeze needs exact independent reviews and retained fixture/query evidence after 24 successful runs', async t => {
  const f = fixture(t), script = path.join(f.repo, 'visual-fixture.cjs');
  fs.writeFileSync(script, `const fs=require('fs');const[rp,op]=process.argv.slice(2);const r=JSON.parse(fs.readFileSync(rp));
if(r.step==='text-query'){fs.writeFileSync(op,JSON.stringify({schemaVersion:1,vector:[1,0]}));process.exit(0);}
const samples=r.step==='embeddings'?r.samples:r.samples.slice(0,1);
const observations=samples.map(f=>({sourceSha256:r.sourceSha256,evidenceType:'model-observation',streamIndex:f.streamIndex,
startSeconds:f.seconds,endSeconds:f.seconds,frameIndices:[f.frameIndex],text:'Synthetic test pattern',
confidence:{source:'fixture',value:null,interpretation:'uncalibrated model score'},
...(r.step==='ocr'?{originalText:'Synthetic test pattern',boxNormalized:[0,0,1,1]}:{}),...(r.step==='embeddings'?{vector:[1,0]}:{})}));
fs.writeFileSync(op,JSON.stringify({schemaVersion:1,observations}));`);
  const visual = { kind: 'json-command', executable: process.execPath, files: [script], settings: { args: [script] },
    identity: { runtimeRevision: 'fixture', model: 'fixture', license: 'fixture', quantization: 'none', preprocessing: 'none' } };
  const weights = path.join(f.repo, 'synthetic-weights');
  const embeddings = { ...visual, kind: 'openclip', files: [script, weights],
    settings: { script, runtimeFiles: [script], weights, modelConfig: weights, tokenizerFile: weights, vectorDimensions: 2 } };
  const config = pinAdapters({ ...f.config, required: [...BASELINE, 'ocr', 'transcript', 'observations', 'embeddings'],
    adapters: { ...f.config.adapters, ocr: visual, observations: structuredClone(visual), embeddings } });
  const labels = ['portrait', 'landscape', 'short', 'long', 'speech', 'music', 'silence', 'no-audio', 'visible-text', 'people', 'animation', 'static', 'moving', 'cuts', 'known-defects'];
  const pilot = { schemaVersion: 1, qualificationVersion: 2, reviewedBy: 'human', reviewedAt: new Date().toISOString(), config, samples: [], fixtures: [] };
  const reviews = [];
  for (let i = 0; i < 24; i++) {
    const media = path.join(f.repo, `sample-${i}.mkv`);
    run('ffmpeg', ['-v', 'error', '-i', f.source, '-c', 'copy', '-metadata', `comment=synthetic-fixture-${i}`, media]);
    const clip = importClip(media, {}, f.repo), result = await analyzeClip(clip.id, f.repo, { config });
    assert.equal(result.status, 'complete', JSON.stringify(result));
    const manifestSha256 = hashFile(path.join(runPath(clip.id, result.runId, f.repo), 'manifest.json'));
    pilot.samples.push({ clipId: clip.id, runId: result.runId, manifestSha256, reviewSha256: null,
      accepted: true, timingReviewed: true, semanticReviewed: true, usefulnessReviewed: true,
      labels: i ? [] : labels, notes: 'Synthetic gate fixture, not an assessment of actual footage' });
    reviews.push({ schemaVersion: 1, clipId: clip.id, runId: result.runId, manifestSha256, reviewedBy: 'human',
      reviewedAt: pilot.reviewedAt, privacyReviewed: false, corrections: [],
      steps: Object.fromEntries(['ocr', 'transcript', 'observations', 'embeddings'].map(s => [s, { accepted: true, reason: 'Synthetic review fixture only' }])) });
  }
  assert.throws(() => validatePilot(pilot, f.repo), /separate immutable human review/);
  pilot.samples.forEach((sample, i) => { sample.reviewSha256 = recordReview(reviews[i], f.repo).reviewSha256; });
  const evidence = (name, value) => {
    const relative = `data/evidence/${name}.json`, file = path.join(f.repo, relative); privateJson(file, value);
    return { path: relative, ...fileIdentity(file) };
  };
  for (const name of ['rotation', 'HDR', 'VFR', 'corruption', 'silent-audio', 'no-audio', 'delayed-audio', 'silence-gaps', 'failed-asr', 'changed-pins', 'incompatible-vectors', 'interrupted-run'])
    pilot.fixtures.push({ case: name, passed: true, evidence: evidence(name, { case: name, passed: true, method: 'Synthetic gate fixture only' }) });
  const first = pilot.samples[0], query = 'synthetic blue pattern';
  await buildSearch(f.repo);
  const boundedResults = await similarText(query, config, f.repo, { runIds: [first.runId] });
  assert.ok(boundedResults.length > 0 && boundedResults.every(r => r.runId === first.runId));
  assert.ok(boundedResults.every(r => Number.isFinite(r.previewStartSeconds) && r.sampledFrames.length === 1));
  await assert.rejects(similarText(query, config, f.repo, { runIds: ['invalid'] }), /explicit run identities/);
  pilot.retrieval = { reviewed: true, acceptanceCriteria: 'Synthetic gate exercise: one source-bound positive and one negative case', queries: [
    { query, accepted: true, expectedMatches: [{ clipId: first.clipId, runId: first.runId, startSeconds: 0, endSeconds: 0 }],
      falseMatches: [], missedEvents: [], timingErrors: [], notes: 'Synthetic positive label', evidence: evidence('query-positive', { query, configSha256: sha(config), results: [] }) },
    { query: 'synthetic negative', accepted: true, expectedNoMatch: true, expectedMatches: [], falseMatches: [], missedEvents: [], timingErrors: [],
      notes: 'Synthetic negative label', evidence: evidence('query-negative', { query: 'synthetic negative', configSha256: sha(config), results: [] }) },
  ] };
  assert.equal(validatePilot(pilot, f.repo).configSha256, sha(config));
  const wrongReview = structuredClone(pilot); wrongReview.samples[0].reviewSha256 = pilot.samples[1].reviewSha256;
  assert.throws(() => validatePilot(wrongReview, f.repo));
  const unreviewed = structuredClone(pilot); unreviewed.retrieval.reviewed = false;
  assert.throws(() => validatePilot(unreviewed, f.repo), /reviewed pilot/);
  const wrongQuery = structuredClone(pilot); wrongQuery.retrieval.queries[0].query = 'unrecorded query';
  assert.throws(() => validatePilot(wrongQuery, f.repo), /does not match/);
  const frozen = freezeProfile(pilot, f.repo);
  assert.ok(fs.existsSync(path.join(f.repo, `data/clips/analysis/profiles/frozen-${frozen.profileSha256}.json`)));
  fs.appendFileSync(path.join(f.repo, pilot.fixtures[0].evidence.path), '\n');
  assert.throws(() => validatePilot(pilot, f.repo), /hash or size mismatch/);
});
