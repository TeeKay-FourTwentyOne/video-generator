import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { command, hashFile } from './film.mjs';
import { joinAnchor } from './join-anchor.mjs';

test('continuation frame is exact, hash-bound and excludes its duplicate from the preceding cut', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'join-anchor-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const source = path.join(root, 'source.mkv');
  command('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=64x96:r=24:d=1',
    '-c:v', 'ffv1', source]);
  const before = hashFile(source);
  const record = joinAnchor(root, 'source.mkv', 12, 'anchor.png');
  const expected = path.join(root, 'expected.png');
  command('ffmpeg', ['-v', 'error', '-i', source, '-vf', 'trim=start_frame=12:end_frame=13',
    '-frames:v', '1', expected]);
  assert.equal(hashFile(expected), record.sha256);
  assert.equal(hashFile(source), before);
  assert.equal(record.sourceSha256, before);
  assert.equal(record.sourceFrames, 24);
  assert.deepEqual(record.precedingSegment, { endFrameExclusive: 12, lastFrame: 11 });
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root, 'anchor.png.json'))), record);
  assert.throws(() => joinAnchor(root, 'source.mkv', 12, 'anchor.png'), /overwrite/);
  for (const frame of [0, -1, 1.5, 24, NaN])
    assert.throws(() => joinAnchor(root, 'source.mkv', frame, 'invalid.png'), /frame/i);
  assert.equal(fs.existsSync(path.join(root, 'invalid.png')), false);
  assert.throws(() => joinAnchor(root, '../escape.mkv', 1, 'new.png'), /escapes/);
  fs.symlinkSync(source, path.join(root, 'linked.mkv'));
  assert.throws(() => joinAnchor(root, 'linked.mkv', 1, 'new.png'), /Symlink/);
});
