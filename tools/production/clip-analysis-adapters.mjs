/** Local adapter contract. Provisioning is explicit; execution denies network access. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { randomUUID } from 'node:crypto';
import { REPO, readJson, hashFile, safePath } from './clip-library.mjs';
import { assert, validHash, fileIdentity, verifyFile, privateJson, configFor, filesUnder } from './clip-analysis-store.mjs';
import { execute, resolveBinary, seconds } from './clip-analysis-process.mjs';
import { transcribe } from './clip-analysis-speech.mjs';

const kinds = { ocr: ['apple-vision', 'json-command'], transcript: ['whisper.cpp', 'json-command'], observations: ['mlx-vlm', 'json-command'],
  embeddings: ['openclip', 'json-command'], 'audio-content': ['clap', 'json-command'] };
// Runtime package names need not follow the narrower artifact-path alphabet.
// Explicitly provisioned directories still reject links and special files.
export function provisionedFiles(dir) {
  assert(fs.lstatSync(dir).isDirectory(), 'Pinned runtime root must be a regular directory');
  return fs.readdirSync(dir).sort().flatMap(name => {
    const file = path.join(dir, name), st = fs.lstatSync(file);
    assert(!st.isSymbolicLink(), 'Pinned runtime directories cannot contain symlinks');
    if (st.isDirectory()) return provisionedFiles(file);
    assert(st.isFile(), 'Pinned runtime contains a special file');
    return [file];
  });
}
export function validateAdapter(step, a) {
  assert(kinds[step]?.includes(a?.kind) && typeof a.executable === 'string' && path.isAbsolute(a.executable)
    && validHash(a.executableSha256) && Array.isArray(a.files) && a.files.length > 0, 'Adapter must be explicitly provisioned and hash-pinned');
  for (const key of ['runtimeRevision', 'model', 'license', 'quantization', 'preprocessing'])
    assert(typeof a.identity?.[key] === 'string' && a.identity[key].trim(), `Missing adapter identity: ${key}`);
  assert(a.settings && typeof a.settings === 'object' && !Array.isArray(a.settings), 'Missing adapter settings');
  verifyFile(a.executable, { ...fileIdentity(a.executable), sha256: a.executableSha256 });
  for (const file of a.files) {
    assert(path.isAbsolute(file.path) && validHash(file.sha256), 'Invalid pinned model/runtime file'); verifyFile(file.path, file);
  }
  for (const root of a.settings.runtimeRoots ?? []) {
    assert(path.isAbsolute(root), 'Runtime roots must be absolute');
    const actual = provisionedFiles(root), expected = new Set(a.files.filter(f => f.path.startsWith(root + path.sep)).map(f => f.path));
    assert(actual.length === expected.size && actual.every(p => expected.has(p)), 'Runtime file inventory changed; pin a new profile');
  }
  if (a.kind === 'whisper.cpp') {
    for (const key of ['modelFile', 'vadModelFile', 'bridgeSource']) assert(a.files.some(f => f.path === a.settings[key]), 'Whisper, VAD and bridge source must all be pinned');
    assert(a.settings.timestampContract === 'whisper.cpp-original-time-v1', 'Whisper requires the qualified original-time bridge');
    for (const key of ['vadThreshold', 'vadMinSpeechMs', 'vadMinSilenceMs', 'vadPadMs', 'vadOverlapSeconds'])
      assert(Number.isFinite(a.settings[key]) && a.settings[key] >= 0, 'Pin explicit VAD settings');
    assert(a.settings.vadThreshold > 0 && a.settings.vadThreshold < 1 && a.settings.vadOverlapSeconds <= 1, 'Invalid VAD thresholds');
  }
  if (['mlx-vlm', 'openclip', 'clap'].includes(a.kind)) {
    assert(a.files.some(f => f.path === a.settings.script), 'Python adapter implementation must be pinned');
    assert(a.settings.runtimeFiles?.length > 0 && a.settings.runtimeFiles.every(p => a.files.some(f => f.path === p)), 'Pin the installed runtime package files, not only the Python executable');
  }
  if (a.kind === 'mlx-vlm') {
    assert(path.isAbsolute(a.settings.modelPath ?? '') && fs.statSync(a.settings.modelPath).isDirectory(), 'MLX model must be a local directory');
    for (const p of filesUnder(a.settings.modelPath)) assert(a.files.some(f => f.path === path.join(a.settings.modelPath, p)), 'All MLX model files must be pinned');
    assert(Number.isInteger(a.settings.windowFrames) && a.settings.windowFrames >= 2 && a.settings.windowFrames <= 32
      && Number.isInteger(a.settings.imageSide) && a.settings.imageSide >= 224 && a.settings.imageSide <= 1024
      && Number.isInteger(a.settings.maxTokens) && a.settings.maxTokens > 0 && a.settings.maxTokens <= 2000
      && Number.isInteger(a.settings.seed), 'Pin bounded visual windows, image preprocessing and generation settings');
  }
  if (['openclip', 'clap'].includes(a.kind)) assert(a.files.some(f => f.path === a.settings.weights), 'Embedding weights must be local and pinned');
  if (a.kind === 'openclip') {
    assert(a.files.some(f => f.path === a.settings.modelConfig) && a.files.some(f => f.path === a.settings.tokenizerFile), 'Pin matching OpenCLIP configuration and tokenizer');
    assert(Number.isSafeInteger(a.settings.vectorDimensions) && a.settings.vectorDimensions > 0 && a.settings.vectorDimensions <= 100000,
      'Pin expected embedding dimensions');
  }
  if (a.kind === 'clap') assert(a.files.some(f => f.path === a.settings.ffmpeg), 'CLAP decoding executable must be pinned');
  return a;
}
export function pinAdapters(input) {
  const config = configFor(input);
  for (const [step, a] of Object.entries(config.adapters)) {
    a.executable = resolveBinary(a.executable); a.executableSha256 = hashFile(a.executable);
    // The author selects files/directories. No package installation or model download is implicit.
    const paths = (a.files ?? []).flatMap(f => {
      const p = path.resolve(typeof f === 'string' ? f : f.path);
      return fs.statSync(p).isDirectory() ? provisionedFiles(p) : [p];
    });
    a.files = [...new Set(paths)].sort().map(p => ({ path: p, ...fileIdentity(p) }));
    validateAdapter(step, a);
  }
  return config;
}
export function validateVector(vector, dimensions) {
  assert(Array.isArray(vector) && vector.length > 0 && vector.length <= 100000 && vector.every(Number.isFinite)
    && (dimensions === undefined || vector.length === dimensions), 'Invalid or incompatible embedding dimensions');
  const norm = Math.hypot(...vector);
  assert(Number.isFinite(norm) && norm > 0 && Math.abs(norm - 1) < 0.001, 'Embedding vector must be finite and unit normalized');
  return vector;
}
export function validateObservations(payload, { sourceSha256, step, streams, samples, vectorDimensions }) {
  assert(payload?.schemaVersion === 1 && Array.isArray(payload.observations) && payload.observations.length <= 100000,
    'Adapter did not return structured observations');
  if (payload.state === 'not-applicable') throw new Error('An adapter cannot substitute not-applicable for an empty or failed detector');
  const sampleMap = new Map(samples.map(f => [`${f.streamIndex}:${f.frameIndex}`, f]));
  for (const o of payload.observations) {
    const stream = streams.find(s => s.index === o.streamIndex);
    assert(stream && o.sourceSha256 === sourceSha256 && o.evidenceType === 'model-observation', 'Observation source or stream identity mismatch');
    assert(typeof o.text === 'string' && o.text.trim() && Number.isFinite(o.startSeconds) && Number.isFinite(o.endSeconds)
      && o.endSeconds >= o.startSeconds, 'Invalid observation time range or text');
    const start = Number(stream.start_time ?? 0), duration = Number(stream.duration);
    assert(o.startSeconds >= start - 0.05 && (!Number.isFinite(duration) || o.endSeconds <= start + duration + 0.1), 'Observation exceeds source presentation range');
    assert(o.confidence && typeof o.confidence.source === 'string' && o.confidence.interpretation === 'uncalibrated model score'
      && (o.confidence.value === null || Number.isFinite(o.confidence.value) && o.confidence.value >= 0 && o.confidence.value <= 1), 'Observation confidence is not qualified');
    if (['ocr', 'observations', 'embeddings'].includes(step)) {
      assert(Array.isArray(o.frameIndices) && o.frameIndices.length > 0, 'Visual observation has no sampled-frame evidence');
      const evidence = o.frameIndices.map(i => sampleMap.get(`${o.streamIndex}:${i}`));
      assert(evidence.every(Boolean) && evidence.every((f, i) => !i || f.frameIndex > evidence[i - 1].frameIndex && f.seconds > evidence[i - 1].seconds), 'Visual observation references unseen or unordered frames');
      assert(Math.abs(o.startSeconds - evidence[0].seconds) < 0.001 && Math.abs(o.endSeconds - evidence.at(-1).seconds) < 0.001, 'Visual observation does not match sampled timestamps');
    }
    if (step === 'ocr') {
      // Apple Vision reports normalized box edges a few 1e-9 outside [0, 1] (float noise on a frame-edge box); tolerate
      // that much and no more, so a genuinely out-of-frame box still fails.
      const edgeNoise = 1e-6;
      assert(typeof o.originalText === 'string' && o.originalText === o.text && Array.isArray(o.boxNormalized) && o.boxNormalized.length === 4
        && o.boxNormalized.every(v => Number.isFinite(v) && v >= -edgeNoise && v <= 1 + edgeNoise), 'Invalid OCR text or bounding box');
    }
    if (step === 'embeddings') validateVector(o.vector, vectorDimensions);
    else if (o.vector !== undefined) validateVector(o.vector);
  }
  return payload;
}
export async function semantic(step, c) {
  const technical = readJson(path.join(c.runDir, 'steps/probe/technical.json'));
  const previewFile = path.join(c.runDir, 'steps/preview/preview.json'), preview = fs.existsSync(previewFile) ? readJson(previewFile) : { samples: [] };
  if (['transcript', 'audio-content'].includes(step) && !technical.streams.some(s => s.codec_type === 'audio'))
    return { state: 'not-applicable', reason: 'Verified input contains no audio stream', coverage: { presence: 'absent' } };
  const a = validateAdapter(step, c.config.adapters[step]);
  if (['ocr', 'observations', 'embeddings'].includes(step) && !preview.samples.length)
    return { state: 'needs-review', reason: 'No qualified display frames available for this visual adapter', coverage: { sampledFrames: 0 } };
  const samples = preview.samples.map(f => ({ ...f, path: path.join(c.runDir, 'steps/preview', f.path) }));
  // Intentionally excludes creation prompts, catalog descriptions and film plans.
  const request = { schemaVersion: 1, step, sourceSha256: c.clip.sha256, source: c.source, samples,
    streams: technical.streams.map(s => ({ index: s.index, codec_type: s.codec_type, time_base: s.time_base, start_time: s.start_time, duration: s.duration })),
    settings: a.settings, identity: a.identity };
  const requestFile = path.join(c.dir, 'request.json'), output = path.join(c.dir, `${step}.json`);
  privateJson(requestFile, request);
  if (a.kind === 'whisper.cpp') {
    privateJson(output, await transcribe(c, a, technical.streams));
  } else {
    const args = a.kind === 'apple-vision' ? [requestFile, output]
      : a.kind === 'json-command' ? [...(a.settings.args ?? []), requestFile, output] : [a.settings.script, requestFile, output];
    await execute(a.executable, args, c, { networkDenied: true });
  }
  const payload = validateObservations(readJson(output), { sourceSha256: c.clip.sha256, step, streams: technical.streams, samples, vectorDimensions: a.settings.vectorDimensions });
  // Recheck pinned files after execution as well, before sealing any result.
  validateAdapter(step, a);
  const empty = payload.observations.length === 0;
  return { state: 'needs-review', reason: empty ? 'Detector completed with no observations; absence of text or speech requires pilot review' : 'Model observations await human usefulness and timing review',
    coverage: { observations: payload.observations.length, sampledFrames: samples.length, sampling: preview.coverage ?? null, model: a.identity,
      firstPassPromptBlind: true, inference: true, emptyResult: empty,
      ...(payload.speechEvidenceVersion ? { speechEvidenceVersion: payload.speechEvidenceVersion, streams: payload.reports.map(r => ({ streamIndex: r.streamIndex, asrState: r.asrState, vadState: r.vadState, vadSpans: r.vadSpans.length, timingWarnings: r.timingWarnings.length, contentClassification: r.contentClassification })) } : {}),
      ...(payload.coverage ? { modelSampling: payload.coverage } : {}),
      limitations: 'Sampled observations cannot exclude unseen actions or unheard content; missing passes are not negative findings' } };
}
export async function setupOcr(repo = REPO) {
  assert(process.platform === 'darwin', 'Apple Vision setup requires macOS');
  const source = path.join(REPO, 'tools/production/clip-analysis-ocr.swift'), hash = hashFile(source);
  const dir = safePath(repo, `data/tools/clip-analysis/ocr-${hash}`); fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  const executable = path.join(dir, 'ocr'), config = configFor();
  if (!fs.existsSync(executable)) {
    const build = path.join(dir, 'build', randomUUID()); fs.mkdirSync(build, { recursive: true, mode: 0o700 });
    // Swift's cache creates transient symlink locks. Keep that disposable compiler cache
    // outside the artifact tree, whose path validation deliberately rejects all symlinks.
    await execute(resolveBinary('swiftc'), ['-O', '-module-cache-path', path.join(dir, 'module-cache'), source, '-o', path.join(build, 'ocr')], { dir: build, config, commands: [] });
    fs.linkSync(path.join(build, 'ocr'), executable);
  }
  const adapter = { kind: 'apple-vision', executable, executableSha256: hashFile(executable), files: [{ path: source, ...fileIdentity(source) }],
    identity: { runtimeRevision: `${os.type()} ${os.release()} / Apple Vision revision 3`, model: 'Apple Vision text recognition revision 3',
      license: 'Apple platform framework', quantization: 'OS managed; not exposed', preprocessing: 'oriented SDR keyframes; accurate OCR; language detection; no language correction' }, settings: {} };
  const result = configFor({ adapters: { ocr: adapter } }); validateAdapter('ocr', adapter);
  const output = safePath(repo, 'data/clips/analysis/profiles/apple-vision-v1.json'); privateJson(output, result);
  return { profile: path.relative(repo, output), network: false, downloads: false };
}
export async function embedText(text, config, dir) {
  const a = validateAdapter('embeddings', config.adapters.embeddings);
  assert(a.kind === 'openclip', 'Text similarity needs the pinned OpenCLIP adapter');
  const request = path.join(dir, 'query.json'), output = path.join(dir, 'query-vector.json');
  privateJson(request, { schemaVersion: 1, step: 'text-query', text, settings: a.settings });
  await execute(a.executable, [a.settings.script, request, output], { dir, config, commands: [] }, { networkDenied: true });
  const result = readJson(output);
  assert(result.schemaVersion === 1, 'Invalid query embedding contract');
  validateVector(result.vector, a.settings.vectorDimensions);
  validateAdapter('embeddings', a); return result.vector;
}
