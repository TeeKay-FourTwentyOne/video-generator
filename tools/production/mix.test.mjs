import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { validateMix, trackFilter, mixdown, measure } from './mix.mjs';

const tone = (file, hz, seconds, gainDb) => execFileSync('ffmpeg', ['-v', 'error', '-n', '-f', 'lavfi', '-i', `sine=frequency=${hz}:sample_rate=48000:duration=${seconds}`,
  '-af', `volume=${gainDb}dB,aformat=channel_layouts=stereo`, '-c:a', 'pcm_s16le', file]);

test('mix validation refuses unsafe ids, non-integer frames, hot gains and late starts', () => {
  const base = { schemaVersion: 1, fps: 24, frames: 48, tracks: [{ id: 'a', source: 'a.wav' }] };
  assert.deepEqual(validateMix(base), { targetLufs: -16, truePeakDbtp: -1.5 });
  assert.throws(() => validateMix({ ...base, tracks: [{ id: '../x', source: 'a.wav' }] }), /safe id/);
  assert.throws(() => validateMix({ ...base, tracks: [{ id: 'a', source: 'a.wav', inFrame: 1.5 }] }), /integer frame/);
  assert.throws(() => validateMix({ ...base, tracks: [{ id: 'a', source: 'a.wav', gainDb: 30 }] }), /gainDb/);
  assert.throws(() => validateMix({ ...base, tracks: [{ id: 'a', source: 'a.wav', atFrame: 48 }] }), /after the picture/);
  assert.throws(() => validateMix({ ...base, master: { truePeakDbtp: 1 } }), /truePeakDbtp/);
  assert.throws(() => trackFilter({ id: 'a', source: 'a.wav', fadeOutFrames: 4 }, 0, 24), /explicit frames/);
  assert.match(trackFilter({ id: 'a', source: 'a.wav', inFrame: 24, frames: 48, atFrame: 12, gainDb: -6 }, 2, 24),
    /^\[2:a\]aformat.*atrim=start_sample=48000:end_sample=144000,asetpts=PTS-STARTPTS,volume=-6dB,adelay=delays=24000S\|24000S:all=1\[t2\]$/);
});
test('mixdown places frame-trimmed tracks, masters to target loudness under the true-peak ceiling, and never overwrites', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'mix-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  tone(path.join(root, 'bed.wav'), 220, 3, -20);
  tone(path.join(root, 'hit.wav'), 880, 1, -12);
  const mix = { schemaVersion: 1, fps: 24, frames: 72, master: { targetLufs: -18, truePeakDbtp: -2 }, tracks: [
    { id: 'bed', source: 'bed.wav', atFrame: 0, frames: 72, fadeOutFrames: 12 },
    { id: 'hit', source: 'hit.wav', inFrame: 0, frames: 12, atFrame: 24, gainDb: -3, highpassHz: 300 }] };
  const report = mixdown(root, mix, 'mix.wav');
  assert.equal(report.seconds, 3);
  const probe = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=sample_rate,channels:format=duration', '-of', 'json', path.join(root, 'mix.wav')], { encoding: 'utf8' });
  const info = JSON.parse(probe);
  assert.equal(info.streams[0].sample_rate, '48000'); assert.equal(info.streams[0].channels, 2);
  assert.ok(Math.abs(Number(info.format.duration) - 3) < .002);
  assert.ok(Math.abs(report.after.integratedLufs + 18) < 1, `integrated ${report.after.integratedLufs}`);
  assert.ok(report.after.truePeakDbtp <= -2, `true peak ${report.after.truePeakDbtp}`);
  assert.throws(() => mixdown(root, mix, 'mix.wav'), /Refusing to overwrite/);
  assert.equal(measure(path.join(root, 'mix.wav')).integratedLufs, report.after.integratedLufs);
});
