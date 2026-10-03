/** Original 32.5-second cue sheet, synchronized to the reviewed edit. */
import fs from 'node:fs';
const events = [];
const add = (voice, at, length, midi, amp, pan = 0) => events.push({ voice, at, length, midi, amp, pan });
add('air', 0, 32.5, 60, .025, 0);
for (const [at, length, notes] of [[0, 5.5, [40, 47, 54]], [4, 7, [40, 55, 59]], [14.2, 8, [36, 43, 50, 55]], [21, 11.5, [36, 43, 52, 59]]])
  notes.forEach((n, i) => add('pad', at + i * .015, Math.min(length, 32.5 - at - i * .015), n, .023, (i - 1.5) * .23));
// The clocklike phrase pauses before the choice. Its warmer return retains the unresolved ninth.
for (const [at, midi] of [[1.1, 76], [2.1, 71], [3.5, 78], [5.1, 79], [6.5, 76], [8.2, 71], [9.8, 78],
  [16.6, 64], [17.4, 67], [18.2, 71], [19, 74], [20, 76], [21.2, 79], [23.0, 78],
  [25, 76], [26.1, 71], [27.5, 78], [29, 79]]) add('bell', at, 2.6, midi, .075, Math.sin(at) * .32);
for (let at = .35; at < 9.5; at += .75) add('tick', at, .08, 84, .019, -.25);
// Restrained machine movement, brass contact and a pulse through the root.
for (const [at, length, midi, amp] of [[.4, 2.7, 43, .024], [4.5, .7, 57, .018], [7.1, .65, 54, .019],
  [10.15, 1.15, 59, .028], [15.3, 1.1, 40, .012], [25.5, .5, 52, .01]]) add('servo', at, length, midi, amp, -.25);
add('tick', 12.04, .11, 75, .085, .15);
add('bell', 12.06, 1.7, 52, .045, .1);
for (const [at, midi] of [[14.1, 48], [14.9, 55], [15.6, 62]]) add('bell', at, 2.2, midi, .044, .12);
const cue = { schemaVersion: 1, title: 'What remains', duration: 32.5,
  origin: 'Original local oscillator synthesis, including foley; no recordings, samples or generation API',
  intent: 'Mechanical repetition gives way to a spacious C major ninth; the upper phrase stays unresolved. Near-silence at the decision.',
  editBoundaries: [0, 3.5, 10, 12, 16.5, 24.5, 32.5], events };
if (!process.argv[2]) throw new Error('Specify a new cue JSON output path');
fs.writeFileSync(process.argv[2], JSON.stringify(cue, null, 2) + '\n', { flag: 'wx' });
