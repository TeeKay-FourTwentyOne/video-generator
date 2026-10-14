import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { importClip, run, readJson, hashFile, readClip } from './clip-library.mjs';
import { analyzeClip, enqueue, workQueue, adoptRun } from './clip-analysis.mjs';
import { configFor, runPath, verifyRun, privateJson, sha, withLock } from './clip-analysis-store.mjs';
import { readLines, seconds, resolveBinary } from './clip-analysis-process.mjs';
import { validateObservations } from './clip-analysis-adapters.mjs';
import { frameSelection } from './clip-analysis-extract.mjs';

const config = () => configFor({ limits: { minFreeBytes: 1024 * 1024, timeoutSeconds: 60, maxOutputBytes: 64 * 1024 * 1024 } });
function fixture(t, { audio = false, vfr = false } = {}) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'clip-analysis-test-'));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  const source = path.join(repo, 'input.mp4');
  run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=160x96:r=12:d=1.5',
    ...(audio ? ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', '1.5', '-c:a', 'aac'] : []),
    ...(vfr ? ['-vf', "select='not(mod(n,3))+not(mod(n,5))'", '-fps_mode', 'vfr'] : []),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source]);
  const clip = importClip(source, {}, repo);
  return { repo, source, clip, config: config() };
}
test('offline extraction covers actual VFR frames and audio; immutable reruns reuse all artifacts', async t => {
  const f = fixture(t, { vfr: true, audio: true }), original = hashFile(f.source);
  const savedFetch = globalThis.fetch; globalThis.fetch = () => { throw new Error('Offline extraction attempted network access'); };
  t.after(() => { globalThis.fetch = savedFetch; });
  const result = await analyzeClip(f.clip.id, f.repo, { config: f.config });
  assert.equal(result.status, 'complete', JSON.stringify(result));
  const m = verifyRun(f.clip.id, result.runId, f.repo), dir = runPath(f.clip.id, result.runId, f.repo);
  assert.equal(m.steps.decode.coverage.fullDecode, true);
  assert.equal(m.steps.audio.state, 'complete'); assert.equal(m.steps.transcript.state, 'pending');
  const timing = readJson(path.join(dir, 'steps/timing/timing.json'));
  assert.equal(timing.streams.find(s => s.type === 'video').variableFrameTiming, true);
  const frames = []; for await (const frame of readLines(path.join(dir, 'steps/timing/frames.jsonl.gz'))) if (frame.media_type === 'video') frames.push(frame);
  assert.ok(frames.every(f => /^\d+$/.test(f.pts) && f.timeBase));
  const preview = readJson(path.join(dir, 'steps/preview/preview.json'));
  assert.equal(preview.coverage.sourceFrames, frames.length);
  const before = hashFile(path.join(dir, 'manifest.json'));
  const repeat = await analyzeClip(f.clip.id, f.repo, { config: f.config }); assert.equal(repeat.reused, true);
  assert.equal(hashFile(path.join(dir, 'manifest.json')), before); assert.equal(hashFile(f.source), original);
  const artifact = path.join(dir, m.artifacts.find(a => a.path.endsWith('poster.jpg')).path); fs.appendFileSync(artifact, 'corruption');
  await assert.rejects(analyzeClip(f.clip.id, f.repo, { config: f.config }), /hash or size mismatch/);
});
test('no audio is explicitly not-applicable; changed settings create a separate run', async t => {
  const f = fixture(t), a = await analyzeClip(f.clip.id, f.repo, { config: f.config });
  assert.equal(a.status, 'complete', JSON.stringify(a));
  assert.equal(verifyRun(f.clip.id, a.runId, f.repo).steps.audio.state, 'not-applicable');
  const b = await analyzeClip(f.clip.id, f.repo, { config: { ...f.config, preview: { ...f.config.preview, gridSeconds: 0.5 } } });
  assert.notEqual(a.runId, b.runId); verifyRun(f.clip.id, a.runId, f.repo);
});
test('corrupt original bytes fail before extraction and never overwrite an existing result', async t => {
  const f = fixture(t), source = path.join(f.repo, f.clip.path); fs.chmodSync(source, 0o600); fs.appendFileSync(source, 'changed');
  await assert.rejects(analyzeClip(f.clip.id, f.repo, { config: f.config }), /hash changed/);
});
test('resource failures remain failed until an explicit retry, preserving private diagnostics', async t => {
  const f = fixture(t), tiny = { ...f.config, limits: { ...f.config.limits, maxFrames: 1 } };
  const failed = await analyzeClip(f.clip.id, f.repo, { config: tiny });
  assert.equal(failed.status, 'incomplete'); assert.equal(failed.steps.timing.state, 'failed');
  const dir = runPath(f.clip.id, failed.runId, f.repo), completed = hashFile(path.join(dir, 'steps/decode/receipt.json'));
  const before = fs.readdirSync(path.join(dir, 'attempts/timing')).length;
  await analyzeClip(f.clip.id, f.repo, { config: tiny }); assert.equal(fs.readdirSync(path.join(dir, 'attempts/timing')).length, before);
  const retry = await analyzeClip(f.clip.id, f.repo, { config: tiny, retry: true });
  assert.equal(retry.steps.timing.state, 'failed'); assert.equal(fs.readdirSync(path.join(dir, 'attempts/timing')).length, before + 1);
  assert.equal(hashFile(path.join(dir, 'steps/decode/receipt.json')), completed);
  assert.equal(fs.existsSync(path.join(dir, 'manifest.json')), false);
});
test('restart recovers installed receipts without repeating a completed extraction', async t => {
  const f = fixture(t), a = await analyzeClip(f.clip.id, f.repo, { config: f.config }); assert.equal(a.status, 'complete', JSON.stringify(a));
  const dir = runPath(f.clip.id, a.runId, f.repo), receipt = path.join(dir, 'steps/timing/receipt.json'), original = hashFile(receipt);
  // Simulate a crash between the atomic step installation and final manifest/state write.
  fs.rmSync(path.join(dir, 'manifest.json')); const state = readJson(path.join(dir, 'state.json')); state.steps.timing = { state: 'running' }; privateJson(path.join(dir, 'state.json'), state);
  const resumed = await analyzeClip(f.clip.id, f.repo, { config: f.config }); assert.equal(resumed.status, 'complete'); assert.equal(hashFile(receipt), original);
});
test('configured missing ASR/OCR never turns into silence or clean text detection', async t => {
  const f = fixture(t, { audio: true });
  await assert.rejects(analyzeClip(f.clip.id, f.repo, { config: { ...f.config, adapters: { ocr: { kind: 'json-command' } } } }), /provisioned/);
  const a = await analyzeClip(f.clip.id, f.repo, { config: { ...f.config, required: [...f.config.required, 'transcript'] } });
  assert.equal(a.status, 'incomplete'); assert.equal(a.steps.transcript.state, 'pending');
});
test('observations reject unsupported timestamps, unseen frames and fabricated certainty', () => {
  const input = { sourceSha256: 'a'.repeat(64), step: 'observations', streams: [{ index: 0, duration: '2' }], samples: [{ streamIndex: 0, frameIndex: 3, seconds: 0.25 }] };
  const row = { sourceSha256: input.sourceSha256, evidenceType: 'model-observation', streamIndex: 0, startSeconds: .25, endSeconds: .25, frameIndices: [3], text: 'A pattern',
    confidence: { source: 'fixture', value: .8, interpretation: 'uncalibrated model score' } };
  validateObservations({ schemaVersion: 1, observations: [row] }, input);
  for (const change of [{ endSeconds: 3 }, { frameIndices: [5] }, { confidence: { value: 1, interpretation: 'probability' } }])
    assert.throws(() => validateObservations({ schemaVersion: 1, observations: [{ ...row, ...change }] }, input));
  assert.equal(seconds('45000', '1/90000'), .5);
});
test('locks reject another live worker and cannot be force-recovered while it is alive', async t => {
  const f = fixture(t);
  await withLock(f.repo, 'fixture', async () => {
    await assert.rejects(withLock(f.repo, 'fixture', async () => {}), /lock exists/);
    await assert.rejects(withLock(f.repo, 'fixture', async () => {}, { recover: true }), /still owns/);
  });
});
test('queue deduplicates identical jobs and never counts a failed retry as complete', async t => {
  const f = fixture(t), limited = { ...f.config, limits: { ...f.config.limits, maxFrames: 1 } };
  await enqueue([f.clip.id, f.clip.id], f.repo, limited); await enqueue([f.clip.id], f.repo, limited);
  let queue = readJson(path.join(f.repo, 'data/clips/analysis/queue.json')); assert.equal(queue.jobs.length, 1);
  let out = await workQueue(f.repo, { limit: 1 }); assert.equal(out.states.failed, 1); assert.equal(out.states.complete, 0);
  out = await workQueue(f.repo, { limit: 1 }); assert.equal(out.processed, 0);
  out = await workQueue(f.repo, { limit: 1, retry: true }); assert.equal(out.states.failed, 1); assert.equal(out.states.complete, 0);
  await enqueue([f.clip.id], f.repo, f.config); out = await workQueue(f.repo, { limit: 1 }); assert.equal(out.states.complete, 1);
  queue = readJson(path.join(f.repo, 'data/clips/analysis/queue.json')); assert.equal(queue.jobs.length, 2);
  assert.equal(queue.jobs[0].state, 'failed'); assert.equal(out.states.failed, 0); assert.equal(out.states.superseded, 1);
  assert.equal(queue.jobs[0].supersededBy.runId, queue.jobs[1].runId);
  const adopted = await adoptRun(f.clip.id, queue.jobs[1].runId, f.repo); assert.equal(adopted.states.complete, 1);
  assert.equal(readJson(path.join(f.repo, 'data/clips/analysis/queue.json')).jobs[0].result.steps.timing.state, 'failed');
});
test('rotation is mapped into display previews and HDR conversion remains visibly unqualified', async t => {
  const f = fixture(t), rotated = path.join(f.repo, 'rotated.mp4');
  run('ffmpeg', ['-v', 'error', '-display_rotation', '90', '-i', f.source, '-c', 'copy', rotated]);
  const clip = importClip(rotated, {}, f.repo), out = await analyzeClip(clip.id, f.repo, { config: f.config });
  assert.equal(out.status, 'complete', JSON.stringify(out));
  const dir = runPath(clip.id, out.runId, f.repo), preview = JSON.parse(run('ffprobe', ['-v', 'error', '-show_streams', '-of', 'json', path.join(dir, 'steps/preview/preview.mp4')]));
  assert.ok(preview.streams[0].height > preview.streams[0].width);
  assert.equal(readJson(path.join(dir, 'steps/preview/preview.json')).displayConversion.autorotate, true);
  const hdr = path.join(f.repo, 'hdr.mp4'); run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=128x96:r=8:d=1',
    '-c:v', 'libx264', '-x264-params', 'colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc', hdr]);
  assert.equal(JSON.parse(run('ffprobe', ['-v', 'error', '-show_streams', '-of', 'json', hdr])).streams[0].color_transfer, 'smpte2084', 'Fixture must carry an actual HDR transfer tag');
  const h = importClip(hdr, {}, f.repo), hOut = await analyzeClip(h.id, f.repo, { config: f.config }); assert.equal(hOut.status, 'complete', JSON.stringify(hOut));
  const manifest = verifyRun(h.id, hOut.runId, f.repo); assert.equal(manifest.steps.preview.state, 'needs-review');
  assert.equal(fs.existsSync(path.join(runPath(h.id, hOut.runId, f.repo), 'steps/preview/preview.mp4')), false);
});
test('hash-consistent corrupt input fails probing/decoding and cannot seal a complete run', async t => {
  const f = fixture(t), bytes = fs.readFileSync(f.source).subarray(0, 600), source = path.join(f.repo, 'broken.mp4'); fs.writeFileSync(source, bytes);
  const hash = hashFile(source), id = `clip_${hash}`, record = { ...readClip(f.clip.id, f.repo), id, sha256: hash, bytes: bytes.length };
  privateJson(path.join(f.repo, `catalog/clips/${id}.json`), record);
  const master = path.join(f.repo, `data/clips/${id}/source.mp4`); fs.mkdirSync(path.dirname(master), { recursive: true }); fs.writeFileSync(master, bytes);
  const result = await analyzeClip(id, f.repo, { config: f.config }); assert.equal(result.status, 'incomplete'); assert.equal(result.steps.probe.state, 'failed');
  assert.equal(fs.existsSync(path.join(runPath(id, result.runId, f.repo), 'manifest.json')), false);
});
test('changed adjacent evidence and undeclared completed payloads fail closed', async t => {
  const f = fixture(t), evidence = path.join(f.repo, 'data/workspace/fixture/request.json');
  privateJson(evidence, { note: 'Original historical evidence' }); const sha256 = hashFile(evidence);
  const profile = { ...f.config, evidence: [{ clipId: f.clip.id, path: 'data/workspace/fixture/request.json', sha256, join: 'verified-hash', reason: 'Synthetic explicit mapping' }] };
  privateJson(evidence, { note: 'Changed historical evidence' });
  const failed = await analyzeClip(f.clip.id, f.repo, { config: profile }); assert.equal(failed.status, 'incomplete'); assert.equal(failed.steps.evidence.state, 'failed');
  const good = await analyzeClip(f.clip.id, f.repo, { config: f.config }), dir = runPath(f.clip.id, good.runId, f.repo);
  fs.writeFileSync(path.join(dir, 'steps/probe/unlisted.json'), '{}'); assert.throws(() => verifyRun(f.clip.id, good.runId, f.repo), /Undeclared/);
});
test('ASR and OCR runtime failures stay failed across retries instead of becoming empty success', async t => {
  const f = fixture(t, { audio: true }), script = path.join(f.repo, 'failed-detector.mjs'); fs.writeFileSync(script, 'process.exit(1);\n');
  const executable = resolveBinary(process.execPath), adapter = { kind: 'json-command', executable, executableSha256: hashFile(executable),
    files: [{ path: script, sha256: hashFile(script), bytes: fs.statSync(script).size }], settings: { args: [script] },
    identity: { runtimeRevision: 'fixture-v1', model: 'synthetic failing detector', license: 'test fixture', quantization: 'not applicable', preprocessing: 'none' } };
  const profile = { ...f.config, adapters: { ocr: adapter, transcript: adapter } };
  const first = await analyzeClip(f.clip.id, f.repo, { config: profile }); assert.equal(first.status, 'incomplete');
  assert.equal(first.steps.ocr.state, 'failed'); assert.equal(first.steps.transcript.state, 'failed');
  const again = await analyzeClip(f.clip.id, f.repo, { config: profile, retry: true });
  assert.equal(again.steps.ocr.state, 'failed'); assert.equal(again.steps.transcript.state, 'failed');
  assert.equal(fs.existsSync(path.join(runPath(f.clip.id, first.runId, f.repo), 'manifest.json')), false);
});
test('dense cut/grid sampling stays within FFmpeg expression parser depth and keeps selected frames', () => {
  const indices = Array.from({ length: 120 }, (_, i) => i * 2);
  const output = run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=64x64:r=240:d=1',
    '-vf', `select=${frameSelection(indices)}`, '-fps_mode', 'passthrough', '-f', 'framemd5', '-']);
  assert.equal(output.split('\n').filter(line => line.trim() && !line.startsWith('#')).length, indices.length);
});
