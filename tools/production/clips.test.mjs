import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { importClip, resolveClip, readClip, listClips, recordUse, listUses, analytics, hashFile, run,
  generationMetadata, updateClip, search, validateClip, atomicJson, readJson } from './clip-library.mjs';
import { main, extract } from './clips.mjs';
import { migrate } from './clip-import.mjs';
import { assemble, validateEdit, review } from './edit.mjs';
import { createLedger } from '../../mcp/video-generator/dist/production/ledger.js';
import { downloadVeoVideo } from '../../mcp/video-generator/dist/clients/veo.js';

function fixture(t) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'clips-test-'));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  const source = path.join(repo, 'data/video/motion with spaces.mp4'); fs.mkdirSync(path.dirname(source), { recursive: true });
  run('ffmpeg', ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'testsrc2=size=90x160:rate=24:duration=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source]);
  return { repo, source };
}
test('content identity deduplicates copies, survives relocation and isolates immutable masters', t => {
  const { repo, source } = fixture(t), original = hashFile(source);
  const a = importClip(source, { labels: ['Motion'], tags: ['color'] }, repo);
  assert.equal(a.id, `clip_${original}`);
  const copy = path.join(repo, 'copy.mov'); fs.copyFileSync(source, copy);
  assert.equal(importClip(copy, { labels: ['Duplicate'] }, repo).id, a.id);
  assert.equal(listClips(repo).length, 1);
  const master = resolveClip(a.id, repo);
  assert.notEqual(fs.statSync(master).ino, fs.statSync(source).ino);
  fs.appendFileSync(source, 'changed'); assert.equal(hashFile(master), original);
  assert.equal(search('duplicate', repo)[0].id, a.id);
  assert.throws(() => resolveClip('../escape', repo), /Invalid clip ID/);
  fs.chmodSync(master, 0o644); fs.appendFileSync(master, 'tampered');
  assert.throws(() => resolveClip(a.id, repo), /hash changed/);
  assert.throws(() => importClip(copy, {}, repo), /master hash mismatch/);
});
test('public metadata projects only known fields and withholds sensitive prompts without logging values', t => {
  const { repo, source } = fixture(t);
  const privateValue = ['gs:', '', 'private-fixture-bucket', 'operation'].join('/');
  const g = generationMetadata({ prompt: `Use ${privateValue}`, model: 'fixture', apiKey: 'ignored', budget: 25 });
  assert.equal(g.promptStatus, 'withheld'); assert.equal(g.prompt, null); assert.equal(g.promptId, null);
  const clip = importClip(source, { generations: [g], privateOperation: privateValue }, repo);
  assert.ok(!JSON.stringify(clip.record).includes(privateValue));
  const bad = structuredClone(clip.record); bad.technical.privatePath = privateValue;
  assert.throws(() => validateClip(bad), /unknown field/);
  bad.technical = clip.record.technical; bad.availability.urls = ['https://example.com/clip?signature=private'];
  assert.throws(() => validateClip(bad), /unsigned public/);
  const symlinkRepo = path.join(repo, 'link-test'); fs.mkdirSync(symlinkRepo); fs.symlinkSync(repo, path.join(symlinkRepo, 'catalog'));
  assert.throws(() => importClip(source, {}, symlinkRepo), /Symlink/);
});
test('extract copies exactly the requested frames, refuses overwrite and leaves usage counts unchanged', t => {
  const { repo, source } = fixture(t), clip = importClip(source, {}, repo);
  const out = 'data/workspace/example/edit/portion.mp4';
  const result = extract(clip.id, 5, 7, out, repo);
  assert.equal(result.frames, 7); assert.equal(hashFile(source), clip.sha256);
  assert.equal(listUses(repo).length, 0);
  assert.throws(() => extract(clip.id, 5, 7, out, repo), /exists/);
  assert.throws(() => extract(clip.id, 23, 2, 'data/workspace/example/bad.mp4', repo), /exceeds/);
  assert.throws(() => extract(clip.id, 1.5, 7, out, repo), /integer/);
});
test('catalog edits render accepted ranges, retain clip IDs and publish one idempotent use per occurrence', t => {
  const { repo, source } = fixture(t), clip = importClip(source, { generations: [generationMetadata({ prompt: 'A moving pattern.', model: 'synthetic' })] }, repo);
  const root = path.join(repo, 'data/workspace/fixture');
  for (const dir of ['qa', 'edit', 'final']) fs.mkdirSync(path.join(root, dir), { recursive: true });
  createLedger(path.join(root, 'budget.json'), 1, 'Synthetic local fixture');
  const plan = { schemaVersion: 1, title: 'Fixture', width: 90, height: 160, fps: 24, shots: [{ id: 'S1', frames: 12, beat: 'Pattern' }] };
  atomicJson(path.join(root, 'film.json'), plan);
  atomicJson(path.join(root, 'qa/keep.json'), { decision: 'keep', notes: 'Reviewed synthetic fixture', sha256: clip.sha256, startFrame: 2, endFrameExclusive: 20 });
  const edit = { schemaVersion: 1, segments: [{ shotId: 'S1', clipId: clip.id, inFrame: 4, frames: 12, decisionFile: 'qa/keep.json' }] };
  atomicJson(path.join(root, 'edit/v1.json'), edit);
  assert.equal(validateEdit(root, edit, plan, { catalogRoot: repo }).frames, 12);
  assert.throws(() => validateEdit(root, { ...edit, segments: [{ ...edit.segments[0], source: 'clips/source.mp4' }] }, plan, { catalogRoot: repo }), /either/);
  const result = assemble(root, 'v1', { catalogRoot: repo }); assert.equal(result.frames, 12);
  assert.equal(review(root, 'v1', { catalogRoot: repo }).shots, 1);
  assert.equal(readJson(path.join(root, 'final/v1/delivery.json')).edit.segments[0].clipId, clip.id);
  const use = listUses(repo)[0]; assert.equal(use.clipId, clip.id); assert.equal(use.status, 'rendered');
  recordUse(use, repo); assert.equal(listUses(repo).length, 1);
  const stats = analytics(repo).rows[0]; assert.equal(stats.renderedUses, 1); assert.equal(stats.sourceSecondsUsed, .5);
  assert.equal(analytics(repo).byPrompt[0].renderedUses, 1);
  assert.equal(analytics(repo).byPrompt[0].clips.length, 1);
  assert.throws(() => recordUse({ ...use, range: { ...use.range, length: 30 } }, repo), /exceeds/);
});
test('historical migration is idempotent, preserves originals, imports evidence and reports missing clips', async t => {
  const { repo, source } = fixture(t), sha256 = hashFile(source);
  const root = path.join(repo, 'data/workspace/old-film');
  fs.mkdirSync(path.join(root, 'clips'), { recursive: true });
  fs.copyFileSync(source, path.join(root, 'clips/take.mp4'));
  atomicJson(path.join(repo, 'docs/clip-metadata/clips.json'), { clips: { old: { clip_id: 'old', path: 'data/video/motion with spaces.mp4',
    frames: { overall_summary: 'A synthetic pattern.', descriptions: [] }, provenance: { veo_prompt: 'Move the pattern.' }, tags: ['synthetic'] },
    missing: { clip_id: 'missing', path: 'data/video/missing.mp4' } } });
  atomicJson(path.join(repo, 'docs/clip-metadata/characters.json'), { characters: [{ character_id: 'char_1', clip_ids: ['old'], name: 'Pattern', description: 'Synthetic colors' }] });
  const edit = { segments: [{ shotId: 'MISSING', source: 'clips/missing.mp4', sha256: 'a'.repeat(64), inFrame: 0, frames: 4 },
    { shotId: 'S1', source: 'clips/take.mp4', sha256, inFrame: 3, frames: 9 }] };
  atomicJson(path.join(root, 'edit/v1.json'), edit);
  const before = fs.statSync(source).mtimeMs;
  const report = migrate(repo); assert.equal(report.uniqueClips, 1); assert.equal(report.duplicateFiles, 1); assert.equal(report.unresolvedMetadata.length, 1);
  assert.equal(listClips(repo)[0].characters[0].name, 'Pattern');
  assert.equal(listUses(repo)[0].status, 'planned'); assert.equal(analytics(repo).rows[0].renderedUses, 0);
  assert.equal(listUses(repo)[0].timelineStartFrame, 4, 'missing footage must not shift subsequent timeline positions');
  const snapshot = JSON.stringify([listClips(repo), listUses(repo)]);
  migrate(repo); assert.equal(JSON.stringify([listClips(repo), listUses(repo)]), snapshot);
  assert.equal(hashFile(source), sha256); assert.equal(fs.statSync(source).mtimeMs, before);
  // A metadata-only checkout validates without ffprobe or original media.
  fs.rmSync(path.join(repo, 'data'), { recursive: true, force: true });
  assert.equal((await main(['validate'], repo)).valid, true);
});
test('planned uses upgrade once, reject conflicting ranges and count prompt evidence only once per clip', t => {
  const { repo, source } = fixture(t);
  const clip = importClip(source, { generations: [generationMetadata({ prompt: 'Pattern' }, 'legacy-job'), generationMetadata({ prompt: 'Pattern' }, 'film-plan')] }, repo);
  const planned = { clipId: clip.id, projectId: 'fixture', editVersion: 'v1', segmentIndex: 0, shotId: 'S1', status: 'planned',
    evidence: 'saved-frame-edit', range: { unit: 'frames', start: 0, length: 12, fps: 24 }, timelineStartFrame: 0, outputSha256: null };
  recordUse(planned, repo);
  const rendered = recordUse({ ...planned, status: 'rendered', outputSha256: clip.sha256 }, repo);
  assert.equal(listUses(repo).length, 1); assert.equal(analytics(repo).byPrompt[0].renderedUses, 1);
  assert.throws(() => recordUse({ ...rendered, range: { ...rendered.range, length: 10 } }, repo), /different content/);
  assert.throws(() => recordUse({ ...planned, range: { ...planned.range, start: 1.2 } }, repo), /integer ranges/);
});
test('Veo retrieval writes the shared master and returns its ID without a workspace copy', async t => {
  const { repo, source } = fixture(t);
  const bytes = fs.readFileSync(source);
  const result = await downloadVeoVideo({ done: true, operationName: 'fixture-operation', video: { bytesBase64Encoded: bytes.toString('base64') } },
    { catalogRoot: repo, request: { prompt: 'A synthetic pattern.', model: 'synthetic', seed: 7 } });
  assert.equal(result.clipId, `clip_${hashFile(source)}`);
  assert.match(result.path, /^data\/clips\/clip_/);
  assert.equal(readClip(result.clipId, repo).generations[0].seed, 7);
  assert.equal(fs.readdirSync(path.join(repo, 'data/clips/.incoming')).length, 0);
});
