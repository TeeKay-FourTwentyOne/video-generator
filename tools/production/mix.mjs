#!/usr/bin/env node
/** Frame-addressed soundtrack assembly for the production editor. Local FFmpeg only; no network, no paid work.
 *
 *   node tools/production/mix.mjs WORKSPACE MIX_JSON OUTPUT_WAV [--report=JSON]
 *
 * MIX_JSON (workspace-relative paths, integer frames at the film's fps):
 * {
 *   "schemaVersion": 1, "fps": 24, "frames": 984,
 *   "tracks": [
 *     { "id": "S01-native", "source": "clips/S01-v1.mp4", "inFrame": 0, "frames": 96, "atFrame": 0,
 *       "gainDb": -6, "fadeInFrames": 6, "fadeOutFrames": 12, "highpassHz": 80, "lowpassHz": 12000 },
 *     { "id": "score", "source": "edit/score.wav", "atFrame": 0 }
 *   ],
 *   "master": { "targetLufs": -16, "truePeakDbtp": -1.5 }
 * }
 * Every track is trimmed by frame (2000 samples per frame at 48 kHz / 24 fps), placed at `atFrame`, optionally
 * faded and filtered, then summed without normalization. The sum is measured (EBU R128), a single static gain
 * brings it to `targetLufs`, and a true-peak limiter holds `truePeakDbtp`. Measurements before and after mastering
 * go to the report. The output refuses to overwrite. Listening remains a separate, human step.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const RATE = 48000;
const run = (args, input) => {
  const p = spawnSync('ffmpeg', ['-v', 'info', '-nostats', ...args], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, input });
  if (p.error || p.status !== 0) throw new Error(`ffmpeg failed: ${p.error?.message || p.stderr.slice(-2000)}`);
  return p.stderr;
};
export function resolveIn(root, relative) {
  if (typeof relative !== 'string' || !relative || path.isAbsolute(relative)) throw new Error('Mix paths must be workspace-relative');
  const p = path.resolve(root, relative);
  if (!p.startsWith(root + path.sep)) throw new Error('Mix path escapes workspace');
  return p;
}
const isFrames = n => Number.isInteger(n) && n >= 0;
export function validateMix(mix) {
  if (mix?.schemaVersion !== 1 || ![24, 25, 30].includes(mix.fps) || !Number.isInteger(mix.frames) || mix.frames < 1
      || !Array.isArray(mix.tracks) || !mix.tracks.length) throw new Error('Invalid mix: schemaVersion 1, fps, positive frames and tracks required');
  if (RATE % mix.fps) throw new Error('Frame rate must divide 48000 samples per second');
  const ids = new Set();
  for (const t of mix.tracks) {
    if (typeof t.id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(t.id) || ids.has(t.id)) throw new Error('Each track needs a unique safe id');
    ids.add(t.id);
    if (typeof t.source !== 'string') throw new Error(`Track ${t.id} needs a source`);
    for (const k of ['inFrame', 'frames', 'atFrame', 'fadeInFrames', 'fadeOutFrames'])
      if (t[k] !== undefined && !isFrames(t[k])) throw new Error(`Track ${t.id}: ${k} must be a nonnegative integer frame count`);
    if (t.frames !== undefined && t.frames < 1) throw new Error(`Track ${t.id}: frames must be positive`);
    if (t.gainDb !== undefined && !(Number.isFinite(t.gainDb) && t.gainDb <= 24)) throw new Error(`Track ${t.id}: gainDb must be a finite number up to +24`);
    for (const k of ['highpassHz', 'lowpassHz']) if (t[k] !== undefined && !(Number.isFinite(t[k]) && t[k] > 0)) throw new Error(`Track ${t.id}: ${k} must be positive`);
    if ((t.atFrame ?? 0) >= mix.frames) throw new Error(`Track ${t.id} starts after the picture ends`);
  }
  const m = mix.master ?? {};
  if (m.targetLufs !== undefined && !(Number.isFinite(m.targetLufs) && m.targetLufs < 0)) throw new Error('master.targetLufs must be negative');
  if (m.truePeakDbtp !== undefined && !(Number.isFinite(m.truePeakDbtp) && m.truePeakDbtp <= 0)) throw new Error('master.truePeakDbtp must be at most 0');
  return { targetLufs: m.targetLufs ?? -16, truePeakDbtp: m.truePeakDbtp ?? -1.5 };
}
export function trackFilter(t, index, fps) {
  const spf = RATE / fps, inFrame = t.inFrame ?? 0;
  const chain = [`[${index}:a]aformat=sample_fmts=fltp:sample_rates=${RATE}:channel_layouts=stereo`];
  chain.push(t.frames ? `atrim=start_sample=${inFrame * spf}:end_sample=${(inFrame + t.frames) * spf}` : `atrim=start_sample=${inFrame * spf}`);
  chain.push('asetpts=PTS-STARTPTS');
  if (t.highpassHz) chain.push(`highpass=f=${t.highpassHz}`);
  if (t.lowpassHz) chain.push(`lowpass=f=${t.lowpassHz}`);
  if (t.fadeInFrames) chain.push(`afade=t=in:st=0:d=${t.fadeInFrames / fps}`);
  if (t.fadeOutFrames) {
    if (!t.frames) throw new Error(`Track ${t.id}: fadeOutFrames needs an explicit frames length`);
    chain.push(`afade=t=out:st=${(t.frames - t.fadeOutFrames) / fps}:d=${t.fadeOutFrames / fps}`);
  }
  if (t.gainDb) chain.push(`volume=${t.gainDb}dB`);
  const delay = (t.atFrame ?? 0) * spf;
  chain.push(`adelay=delays=${delay}S|${delay}S:all=1`);
  return chain.join(',') + `[t${index}]`;
}
export function measure(file) {
  const log = run(['-i', file, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-']);
  const num = re => { const m = re.exec(log); return m ? Number(m[1]) : null; };
  return { integratedLufs: num(/I:\s+(-?[\d.]+) LUFS/), loudnessRangeLu: num(/LRA:\s+(-?[\d.]+) LU/), truePeakDbtp: num(/Peak:\s+(-?[\d.]+) dBFS/) };
}
export function mixdown(root, mix, output) {
  const master = validateMix(mix);
  const out = resolveIn(root, output);
  if (fs.existsSync(out)) throw new Error('Refusing to overwrite an existing mix; choose a new output name');
  const inputs = mix.tracks.flatMap(t => ['-i', resolveIn(root, t.source)]);
  const filters = mix.tracks.map((t, i) => trackFilter(t, i, mix.fps));
  const totalSamples = mix.frames * (RATE / mix.fps);
  const sum = `${mix.tracks.map((_, i) => `[t${i}]`).join('')}amix=inputs=${mix.tracks.length}:normalize=0:duration=longest,apad,atrim=end_sample=${totalSamples}[sum]`;
  const raw = out.replace(/\.wav$/i, '') + '.premaster.wav';
  if (fs.existsSync(raw)) throw new Error('Refusing to overwrite an existing premaster');
  run(['-n', ...inputs, '-filter_complex', [...filters, sum].join(';'), '-map', '[sum]', '-c:a', 'pcm_s24le', raw]);
  const before = measure(raw);
  if (before.integratedLufs === null || before.integratedLufs < -70) throw new Error('Premaster is silent or unmeasurable; check track ranges');
  const gainDb = Math.round((master.targetLufs - before.integratedLufs) * 100) / 100;
  // The limiter works on sample peaks; inter-sample peaks and the delivery codec (AAC) overshoot by a few
  // tenths of a dB, so the ceiling handed to it sits 0.5 dB under the requested true-peak target.
  const limit = 10 ** ((master.truePeakDbtp - .5) / 20);
  // Static gain then a true-peak limiter (level=false keeps it from re-normalizing); attack/release in ms.
  run(['-n', '-i', raw, '-af', `volume=${gainDb}dB,alimiter=limit=${limit.toFixed(4)}:attack=3:release=60:level=false`, '-c:a', 'pcm_s24le', out]);
  const after = measure(out);
  return { output, premaster: path.relative(root, raw), frames: mix.frames, seconds: mix.frames / mix.fps, gainDb, master, before, after,
    note: 'Computational measurement only; listening review is a separate human step.' };
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const [root, mixFile, output, ...flags] = process.argv.slice(2);
    if (!root || !mixFile || !output) throw new Error('Usage: mix.mjs WORKSPACE MIX_JSON OUTPUT_WAV [--report=JSON]');
    const base = path.resolve(root);
    const mix = JSON.parse(fs.readFileSync(resolveIn(base, mixFile), 'utf8'));
    const report = mixdown(base, mix, output);
    for (const f of flags) {
      const m = /^--report=(.+)$/.exec(f);
      if (!m) throw new Error(`Unknown option: ${f}`);
      fs.writeFileSync(resolveIn(base, m[1]), JSON.stringify({ mixFile, ...report }, null, 2) + '\n', { flag: 'wx' });
    }
    console.log(JSON.stringify(report, null, 2));
  } catch (e) { console.error(JSON.stringify({ error: e.message })); process.exitCode = 1; }
}
