import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createLedger } from '../../mcp/video-generator/dist/production/ledger.js';
import { configurationSummary } from '../../mcp/video-generator/dist/tools/config.js';
import { validateEdit, assemble, review } from './edit.mjs';
import { command, hashFile, localPath } from './film.mjs';

test('configuration presence never exposes historical aliases, unknown fields or nested secrets', () => {
  const marker = 'synthetic-private-value';
  const result = configurationSummary({ claudeKey: marker, veoApiKey: marker, unknown: { nested: marker }, empty: '' });
  assert.deepEqual(result, { claudeKey: true, veoApiKey: true, unknown: true, empty: false });
  assert.ok(!JSON.stringify(result).includes(marker));
});
test('artifact paths refuse traversal and absolute paths', () => {
  assert.throws(() => localPath('/tmp/film-fixture', '../outside'), /escapes/);
  assert.throws(() => localPath('/tmp/film-fixture', '/absolute'), /relative/);
});
test('artifact paths refuse symlink escapes, including nonexistent outputs', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'film-links-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.symlinkSync(os.tmpdir(), path.join(root, 'outside'));
  assert.throws(() => localPath(root, 'outside/new-file.json'), /Symlink/);
  fs.symlinkSync(path.join(os.tmpdir(), 'does-not-exist-production-fixture'), path.join(root, 'broken'));
  assert.throws(() => localPath(root, 'broken/new-file.json'), /Symlink/);
});
test('real local edit enforces reviewed ranges, preserves sources and refuses overwrite', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'film-edit-'));
  try {
    for (const folder of ['clips', 'qa', 'edit', 'final']) fs.mkdirSync(path.join(root, folder));
    const write = (p, obj) => fs.writeFileSync(path.join(root, p), JSON.stringify(obj));
    createLedger(path.join(root, 'budget.json'), 1, 'Offline synthetic fixture');
    const source = path.join(root, 'clips', 'source with spaces.mp4');
    command('ffmpeg', ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'testsrc2=size=90x160:rate=24:duration=1',
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source]);
    const sha256 = hashFile(source);
    const plan = { schemaVersion: 1, title: 'Offline fixture', width: 90, height: 160, fps: 24,
      shots: [{ id: 'S01', beat: 'Visible motion for a real decode test', frames: 12 }] };
    write('film.json', plan);
    write('qa/S01.json', { sha256, decision: 'keep', startFrame: 2, endFrameExclusive: 22, notes: 'Reviewed fixture frames' });
    const edit = { schemaVersion: 1, segments: [{ shotId: 'S01', source: 'clips/source with spaces.mp4',
      sha256, inFrame: 4, frames: 12, decisionFile: 'qa/S01.json' }] };
    write('edit/v1.json', edit);
    assert.deepEqual(validateEdit(root, edit, plan), { frames: 12, seconds: .5 });
    const bad = structuredClone(edit); bad.segments[0].inFrame = 20;
    assert.throws(() => validateEdit(root, bad, plan), /reviewed clean range/);
    const result = assemble(root, 'v1');
    assert.equal(result.frames, 12); assert.equal(hashFile(source), sha256);
    assert.throws(() => assemble(root, 'v1'), /EEXIST/);
    assert.equal(review(root, 'v1').shots, 1);
    assert.throws(() => review(root, 'v1'), /Review exists/);
    const html = fs.readFileSync(path.join(root, 'final/v1/review.html'), 'utf8');
    assert.ok(html.includes('film.mp4')); assert.ok(html.includes('data-time="0"'));
    write('qa/S01.json', { sha256, decision: 'keep', notes: 'Missing range must fail' });
    assert.throws(() => validateEdit(root, edit, plan), /acceptance/);
    fs.appendFileSync(source, 'changed');
    assert.throws(() => validateEdit(root, edit, plan), /hash changed/);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});
