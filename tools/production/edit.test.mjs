import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { createLedger } from '../../mcp/video-generator/dist/production/ledger.js';
import { configurationSummary } from '../../mcp/video-generator/dist/tools/config.js';
import { validateEdit, assemble as assembleEdit, review as reviewEdit, validateFinish, registerFinishClips, finish as finishEdit } from './edit.mjs';
import { command, hashFile, localPath } from './film.mjs';
const assemble = (root, version) => assembleEdit(root, version, { catalogRoot: root });
const review = (root, version) => reviewEdit(root, version, { catalogRoot: root });

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
test('segment fades are frame-addressed, length-preserving and validated', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'film-fade-'));
  try {
    for (const folder of ['clips', 'qa', 'edit', 'final']) fs.mkdirSync(path.join(root, folder));
    const write = (p, obj) => fs.writeFileSync(path.join(root, p), JSON.stringify(obj));
    createLedger(path.join(root, 'budget.json'), 1, 'Offline synthetic fixture');
    const source = path.join(root, 'clips', 'bright.mp4');
    command('ffmpeg', ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'color=c=white:size=90x160:rate=24:duration=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source]);
    const sha256 = hashFile(source);
    const plan = { schemaVersion: 1, title: 'Fade fixture', width: 90, height: 160, fps: 24, shots: [{ id: 'S01', beat: 'White card with fades', frames: 12 }] };
    write('film.json', plan);
    write('qa/S01.json', { sha256, decision: 'keep', startFrame: 0, endFrameExclusive: 24, notes: 'Synthetic white card' });
    const segment = { shotId: 'S01', source: 'clips/bright.mp4', sha256, inFrame: 0, frames: 12, decisionFile: 'qa/S01.json', fadeInFrames: 4, fadeOutFrames: 4 };
    write('edit/v1.json', { schemaVersion: 1, segments: [segment] });
    assert.throws(() => validateEdit(root, { schemaVersion: 1, segments: [{ ...segment, fadeInFrames: 9 }] }, plan), /fit inside/);
    assert.throws(() => validateEdit(root, { schemaVersion: 1, segments: [{ ...segment, fadeOutFrames: -1 }] }, plan), /fit inside/);
    assert.equal(assemble(root, 'v1').frames, 12);
    const raw = path.join(root, 'frames.gray');
    command('ffmpeg', ['-v', 'error', '-n', '-i', path.join(root, 'final/v1/film.mp4'), '-f', 'rawvideo', '-pix_fmt', 'gray', raw]);
    const frames = fs.readFileSync(raw), size = 90 * 160;
    const mean = i => frames.subarray(i * size, (i + 1) * size).reduce((a, b) => a + b, 0) / size;
    assert.ok(mean(0) < 24, 'first frame fades from black'); assert.ok(mean(6) > 200, 'middle frame is untouched'); assert.ok(mean(11) < 40, 'last frame fades to black');
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});
test('finish cuts a verified delivery again from 2x counterparts, copies its soundtrack and refuses every drift', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'film-finish-'));
  try {
    for (const folder of ['clips', 'qa', 'edit', 'final']) fs.mkdirSync(path.join(root, folder));
    const write = (p, obj) => fs.writeFileSync(path.join(root, p), JSON.stringify(obj));
    createLedger(path.join(root, 'budget.json'), 1, 'Offline synthetic fixture');
    const render = (name, size, rate = 24, duration = 1, pattern = 'testsrc2') => {
      const file = path.join(root, 'clips', name);
      command('ffmpeg', ['-v', 'error', '-n', '-f', 'lavfi', '-i', `${pattern}=size=${size}:rate=${rate}:duration=${duration}`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file]);
      return file;
    };
    const a = render('a.mp4', '90x160'), b = render('b.mp4', '90x160', 24, 1, 'testsrc');
    render('a-2x.mp4', '180x320'); render('b-2x.mp4', '180x320', 24, 1, 'testsrc');
    render('a-long.mp4', '180x320', 24, 2); render('a-30.mp4', '180x320', 30, .8); render('a-wide.mp4', '180x300'); render('a-small.mp4', '90x160');
    command('ffmpeg', ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', '-ac', '2', '-ar', '48000', path.join(root, 'edit', 'score.wav')]);
    const plan = { schemaVersion: 1, title: 'Finish fixture', width: 90, height: 160, fps: 24,
      shots: [{ id: 'S01', beat: 'Moving pattern', frames: 12 }, { id: 'S02', beat: 'Second pattern with a fade', frames: 10 }] };
    write('film.json', plan);
    write('qa/S01.json', { sha256: hashFile(a), decision: 'keep', startFrame: 0, endFrameExclusive: 24, notes: 'Reviewed fixture frames' });
    write('qa/S02.json', { sha256: hashFile(b), decision: 'keep', startFrame: 0, endFrameExclusive: 24, notes: 'Reviewed fixture frames' });
    write('edit/v1.json', { schemaVersion: 1, segments: [
      { shotId: 'S01', source: 'clips/a.mp4', sha256: hashFile(a), inFrame: 4, frames: 12, decisionFile: 'qa/S01.json' },
      { shotId: 'S02', source: 'clips/b.mp4', sha256: hashFile(b), inFrame: 2, frames: 10, decisionFile: 'qa/S02.json', fadeOutFrames: 3 }],
      audio: { path: 'edit/score.wav', sha256: hashFile(path.join(root, 'edit', 'score.wav')) } });
    assert.equal(assemble(root, 'v1').frames, 22);
    // A synced publication-text copy beside the base, as sync-description leaves it.
    const text = 'Fixture description\nhttps://example.invalid/repo\n';
    fs.writeFileSync(path.join(root, 'final/v1/description.txt'), text);
    const base = JSON.parse(fs.readFileSync(path.join(root, 'final/v1/delivery.json'), 'utf8'));
    base.description = { path: 'final/v1/description.txt', repositorySource: 'briefs/fixture/description.md', sha256: createHash('sha256').update(text).digest('hex') };
    fs.writeFileSync(path.join(root, 'final/v1/delivery.json'), JSON.stringify(base));
    const [idA, idB] = base.edit.segments.map(s => s.clipId);
    const map = (counterparts, name = 'edit/finish.json') => { write(name, { schemaVersion: 1, counterparts }); return name; };
    const good = map({ [idA]: 'clips/a-2x.mp4', [idB]: 'clips/b-2x.mp4' });
    const validate = (file, version = 'v1-2x') => validateFinish(root, 'v1', version, file, { catalogRoot: root });
    assert.throws(() => validate(good, 'v1'), /must differ/);
    assert.throws(() => validate(map({ [idA]: 'clips/a-2x.mp4' }, 'edit/missing.json')), /Missing counterpart for S02/);
    assert.throws(() => validate(map({ [idA]: 'clips/a-long.mp4', [idB]: 'clips/b-2x.mp4' }, 'edit/long.json')), /frame count differs for S01: 48 vs 24/);
    assert.throws(() => validate(map({ [idA]: 'clips/a-30.mp4', [idB]: 'clips/b-2x.mp4' }, 'edit/rate.json')), /frame rate differs/);
    assert.throws(() => validate(map({ [idA]: 'clips/a-wide.mp4', [idB]: 'clips/b-2x.mp4' }, 'edit/wide.json')), /aspect ratio differs/);
    assert.throws(() => validate(map({ [idA]: 'clips/a-small.mp4', [idB]: 'clips/b-2x.mp4' }, 'edit/small.json')), /share one frame size|smaller than the base/);
    const registered = registerFinishClips(root, 'v1', 'v1-2x', good, { catalogRoot: root });
    assert.equal(registered.clipIds.length, 2);
    const result = await finishEdit(root, 'v1', 'v1-2x', good, { catalogRoot: root });
    assert.equal(result.frames, 22); assert.equal(result.width, 180); assert.equal(result.height, 320);
    assert.deepEqual(result.checks, { fullDecode: true, dimensions: true, frameCount: true, colorTags: true, baseHash: true, counterpartHashes: true, audioPackets: true, audioPcm: true });
    assert.equal(result.base.sha256, base.sha256);
    assert.equal(fs.readFileSync(path.join(root, 'final/v1-2x/description.txt'), 'utf8'), text);
    const delivery = JSON.parse(fs.readFileSync(path.join(root, 'final/v1-2x/delivery.json'), 'utf8'));
    const video = delivery.probe.streams.find(s => s.codec_type === 'video');
    assert.deepEqual([video.color_range, video.color_space, video.color_primaries, video.color_transfer], ['tv', 'bt709', 'bt709', 'bt709']);
    assert.equal(delivery.finishing.baseVersion, 'v1'); assert.equal(delivery.finishing.baseSha256, base.sha256);
    assert.equal(delivery.finishing.audio.packetsSha256.base, delivery.finishing.audio.packetsSha256.output);
    assert.equal(delivery.finishing.audio.pcmSha256.base, delivery.finishing.audio.pcmSha256.output);
    assert.deepEqual(delivery.finishing.segments.map(s => [s.baseClipId, s.counterpart, s.inFrame, s.frames]),
      [[idA, 'clips/a-2x.mp4', 4, 12], [idB, 'clips/b-2x.mp4', 2, 10]]);
    assert.deepEqual(delivery.description, { ...base.description, path: 'final/v1-2x/description.txt' });
    assert.equal(delivery.edit.segments.length, 2); assert.equal(delivery.artisticApproval, false);
    const uses = fs.readdirSync(path.join(root, 'catalog/uses')).map(f => JSON.parse(fs.readFileSync(path.join(root, 'catalog/uses', f), 'utf8')));
    const finishUses = uses.filter(u => u.editVersion === 'finish/v1-2x');
    assert.equal(finishUses.length, 2);
    assert.ok(finishUses.every(u => u.status === 'rendered' && u.outputSha256 === result.sha256 && registered.clipIds.includes(u.clipId)));
    const master = JSON.parse(fs.readFileSync(path.join(root, `catalog/clips/clip_${result.sha256}.json`), 'utf8'));
    assert.equal(master.kind, 'delivery'); assert.equal(master.technical.width, 180);
    // A finished version is a delivery like any other: its review package builds from the same record shape.
    assert.equal(review(root, 'v1-2x').shots, 2);
    assert.throws(() => validate(good), /EEXIST/);
    fs.appendFileSync(path.join(root, 'final/v1/film.mp4'), 'changed');
    assert.throws(() => validate(good, 'v1-again'), /Base delivery hash changed/);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});
