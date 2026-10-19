import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { importClip, run, readJson, readClip, hashFile, recordUse } from './clip-library.mjs';
import { configFor, privateJson, runPath, verifyRun } from './clip-analysis-store.mjs';
import { configureDefault, processProject, checkProject, workflowMain } from './clip-analysis-workflow.mjs';

function fixture(t) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'clip-workflow-test-'));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  const config = configFor({ limits: { minFreeBytes: 1024 * 1024, timeoutSeconds: 60, maxOutputBytes: 64 * 1024 * 1024 } });
  const add = (color, collections = ['fixture']) => {
    const source = path.join(repo, `${color}.mp4`);
    run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', `color=c=${color}:s=160x96:r=12:d=1`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source]);
    return { ...importClip(source, { collections }, repo), source };
  };
  const setDefault = (selected = config) => {
    privateJson(path.join(repo, 'data/profile.json'), selected);
    return configureDefault('data/profile.json', repo);
  };
  return { repo, config, add, setDefault };
}

test('import retains private, immutable, idempotent requests without running analysis', t => {
  const f = fixture(t), clip = f.add('red');
  const dir = path.join(f.repo, `data/clips/analysis/intake/${clip.id}`);
  const first = fs.readdirSync(dir); assert.equal(first.length, 1);
  const file = path.join(dir, first[0]), original = hashFile(file), stat = fs.statSync(file);
  assert.equal(stat.mode & 0o777, 0o600);
  assert.equal(readJson(file).clipId, clip.id);
  importClip(clip.source, { collections: ['fixture'] }, f.repo);
  assert.equal(hashFile(file), original); assert.equal(fs.statSync(file).ino, stat.ino);
  assert.equal(fs.existsSync(path.join(f.repo, `data/clips/${clip.id}/analysis`)), false);
  importClip(clip.source, { collections: ['second-project'] }, f.repo);
  assert.equal(fs.readdirSync(dir).length, 2); assert.equal(hashFile(file), original);
  const current = fs.readdirSync(dir).find(name => !first.includes(name));
  fs.appendFileSync(path.join(dir, current), 'corrupt');
  assert.throws(() => importClip(clip.source, {}, f.repo), /intake conflicts/);
  assert.equal(hashFile(clip.source), clip.sha256);
});

test('project processing covers unused takes and reused clips, verifies artifacts and refreshes search', async t => {
  const f = fixture(t), selected = f.add('red'), unused = f.add('blue'), reused = f.add('yellow', ['other']), unrelated = f.add('green', ['other']);
  recordUse({ clipId: reused.id, projectId: 'fixture', editVersion: 'edit/v1', segmentIndex: 0, shotId: 'S01', status: 'planned',
    evidence: 'saved-frame-edit', range: { unit: 'frames', start: 0, length: 6, fps: 12 }, timelineStartFrame: 0, outputSha256: null }, f.repo);
  f.setDefault();
  const fetch = globalThis.fetch; globalThis.fetch = () => { throw new Error('Unexpected network'); }; t.after(() => { globalThis.fetch = fetch; });
  const before = checkProject('fixture', f.repo); assert.equal(before.status, 'incomplete'); assert.equal(before.counts.pending, 3);
  const result = await processProject('fixture', f.repo);
  assert.equal(result.status, 'complete', JSON.stringify(result)); assert.equal(result.clips, 3);
  assert.deepEqual(new Set(result.rows.map(r => r.clipId)), new Set([selected.id, unused.id, reused.id]));
  assert.equal(result.humanReview, 'not-asserted'); assert(result.rows.every(r => r.steps.ocr === 'pending' && r.steps.transcript === 'not-applicable'));
  assert.equal(fs.existsSync(path.join(f.repo, `data/clips/${unrelated.id}/analysis`)), false);
  assert.equal(readJson(path.join(f.repo, 'data/clips/analysis/coverage.json')).analyzedClips, 3);
  const hashes = result.rows.map(r => hashFile(path.join(runPath(r.clipId, r.runId, f.repo), 'manifest.json')));
  const again = await processProject('fixture', f.repo); assert(again.attempts.every(a => a.reused));
  assert.deepEqual(again.rows.map(r => hashFile(path.join(runPath(r.clipId, r.runId, f.repo), 'manifest.json'))), hashes);
  assert.equal(checkProject('fixture', f.repo).status, 'complete');
  const row = result.rows[0], manifest = verifyRun(row.clipId, row.runId, f.repo);
  fs.appendFileSync(path.join(runPath(row.clipId, row.runId, f.repo), manifest.artifacts.find(a => a.path.endsWith('poster.jpg')).path), 'corrupt');
  const invalid = checkProject('fixture', f.repo); assert.equal(invalid.status, 'incomplete'); assert.equal(invalid.counts.invalid, 1);
});

test('missing profiles and unprovisioned required passes remain blockers with no silent fallback', async t => {
  const f = fixture(t), clip = f.add('red');
  assert.throws(() => checkProject('fixture', f.repo), /No default analysis profile/);
  const config = { ...f.config, required: [...f.config.required, 'observations'] };
  const result = await processProject('fixture', f.repo, { config });
  assert.equal(result.status, 'incomplete'); assert.equal(result.rows[0].steps.observations, 'pending');
  const intake = fs.readdirSync(path.join(f.repo, `data/clips/analysis/intake/${clip.id}`));
  assert.equal(intake.filter(n => n.endsWith('.complete.json')).length, 0);
  await assert.rejects(workflowMain(['process-project', 'fixture', '--check', '--retry'], f.repo), /cannot retry/);
  await assert.rejects(workflowMain(['process-project', '../escape'], f.repo), /Invalid project ID/);
});

test('read-only checks detect changed config and catalog evidence without reinterpreting old runs', async t => {
  const f = fixture(t), clip = f.add('red'); f.setDefault();
  const complete = await processProject('fixture', f.repo), old = complete.rows[0];
  const original = hashFile(path.join(runPath(clip.id, old.runId, f.repo), 'manifest.json'));
  const altered = { ...f.config, threads: 3 };
  const changed = checkProject('fixture', f.repo, { config: altered });
  assert.equal(changed.status, 'incomplete'); assert.notEqual(changed.rows[0].runId, old.runId);
  assert.equal(fs.existsSync(runPath(clip.id, changed.rows[0].runId, f.repo)), false);
  importClip(clip.source, { labels: ['New catalog evidence'] }, f.repo);
  assert.equal(checkProject('fixture', f.repo).status, 'incomplete');
  assert.equal(hashFile(path.join(runPath(clip.id, old.runId, f.repo), 'manifest.json')), original);
  assert.equal(readClip(clip.id, f.repo).labels[0], 'New catalog evidence');
  const policy = readJson(path.join(f.repo, 'data/clips/analysis/workflow.json'));
  fs.appendFileSync(path.join(f.repo, policy.configRef.path), 'changed');
  assert.throws(() => checkProject('fixture', f.repo), /hash or size mismatch/);
});
