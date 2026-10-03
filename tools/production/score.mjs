/** Deterministic, cue-addressed stereo synthesis. No samples, downloads or APIs. */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { wav } from '../scene-lab/tour-score.mjs';

export function synthesize(cue) {
  const rate = 48000, duration = cue.duration;
  if (!(duration >= 1 && duration <= 120) || !Array.isArray(cue.events)) throw new Error('Invalid score duration/events');
  const count = Math.round(duration * rate), left = new Float32Array(count), right = new Float32Array(count);
  let seed = 421;
  const noise = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 2147483648 - 1; };
  for (const e of cue.events) {
    const { at, length, amp, pan = 0, midi = 60, voice } = e;
    if (![at, length, amp, pan, midi].every(Number.isFinite) || at < 0 || length <= 0 || at + length > duration + .001
        || amp < 0 || amp > .5 || Math.abs(pan) > 1 || !['pad', 'bell', 'tick', 'air', 'servo'].includes(voice))
      throw new Error('Invalid audio cue');
    const f = 440 * 2 ** ((midi - 69) / 12), start = Math.round(at * rate), end = Math.min(count, Math.round((at + length) * rate));
    const lg = Math.cos((pan + 1) * Math.PI / 4), rg = Math.sin((pan + 1) * Math.PI / 4);
    let filtered = 0;
    for (let i = start; i < end; i++) {
      const t = (i - start) / rate, phase = 2 * Math.PI * f * t;
      let v;
      if (voice === 'bell') v = (1 - Math.exp(-t / .006)) * Math.exp(-t / .85)
        * (Math.sin(phase) + .24 * Math.exp(-t / .3) * Math.sin(phase * 2.003) + .06 * Math.sin(phase * 4.017));
      if (voice === 'pad') v = Math.min(1, t / 1.1) * Math.min(1, (length - t) / 1.5)
        * (Math.sin(phase + .012 * Math.sin(t * 1.3)) + .18 * Math.sin(phase * 2.0002));
      if (voice === 'tick') v = Math.exp(-t / .014) * (noise() * .45 + Math.sin(phase) * .55);
      if (voice === 'servo') v = Math.sin(Math.PI * t / length) ** 2
        * (.55 * Math.sin(phase + 5 * Math.sin(t * 13)) + .2 * Math.sin(phase * 2.1));
      if (voice === 'air') { filtered = .997 * filtered + .003 * noise(); v = filtered * 5 * Math.sin(Math.PI * t / length); }
      v *= Math.min(1, (length - t) / .025) * amp;
      left[i] += v * lg; right[i] += v * rg;
    }
  }
  // Cross-channel reflections. Descending traversal prevents feedback accumulation.
  for (const [seconds, gain] of [[.139, .16], [.277, .085], [.419, .04]]) {
    const delay = Math.round(seconds * rate);
    for (let i = count - 1; i >= delay; i--) { left[i] += right[i - delay] * gain; right[i] += left[i - delay] * gain; }
  }
  let peak = 0;
  for (let i = 0; i < count; i++) {
    const t = i / rate, fade = Math.min(1, t / .25) * Math.min(1, (duration - t) / 1.4);
    left[i] *= fade; right[i] *= fade;
    peak = Math.max(peak, Math.abs(left[i]), Math.abs(right[i]));
  }
  if (peak > .9) throw new Error('Score exceeds headroom; lower cue amplitudes');
  return { left, right, sampleRate: rate, duration, peak };
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    const cue = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
    const score = synthesize(cue);
    fs.writeFileSync(process.argv[3], wav(score), { flag: 'wx' });
    console.log(JSON.stringify({ duration: score.duration, samples: score.left.length, peak: score.peak, paidRequests: 0 }));
  } catch (e) { console.error(e.message); process.exitCode = 1; }
}
