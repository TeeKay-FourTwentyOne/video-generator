# TANGO — brief v1 (for a fresh session)

[Current production record](README.md).

a][ productions · 2026-11-04 · chosen by the director from the same workshop as EVERY WAY HOME, to be built after it.

## 1. Concept

Homage to Zbigniew Rybczyński's *Tango* (1981), which took him a year of hand rotoscoping: one small room, one fixed
camera, and over the course of the film some thirty-six people enter, each repeating a private action on their own loop
(a boy climbs in for a ball, a woman dresses, a man eats soup, a couple makes love, a thief, a baby, a drunk), none of
them touching, until the room is full of people who do not see each other, and then it empties again.

Ours: one empty room plate, 16:9, about sixty seconds. Around twenty characters, each generated **alone** against that
plate as a looping action of four to eight seconds, keyed out by difference matte, and scheduled by code so that no two
bodies ever occupy the same floor at the same time. They are added one at a time until the room is full, then subtracted
one at a time until it is empty. The accumulation is the film; the emptying is the ending.

What only this pairing can do: Veo gives twenty photoreal performances in one lit room that no shoot could stage, and
code gives the exactness Veo cannot: pixel-identical room, hard non-collision, loop-perfect timing, and the slow
arithmetic of the build-up and the thinning-out.

## 2. Format

- 1920×1080 (16:9), 24 fps, H.264 high + AAC 48 kHz stereo. About 60 s. 4K is 3840×2160 by the standard 2x counterpart.
- One fixed camera, slightly high, a small room that fills the frame edge to edge: door on one wall, a window, a bed, a
  table, a cot or crib, a cupboard. Photoreal, muted, a period feel without period words in prompts (they bake in text).
- Wordless. Sound is the sum of the loops' own native audio, each on its own loop, so the room's noise accumulates and
  thins with the people. No music.

## 3. The technique, proven on EVERY WAY HOME (2026-11-04)

- **Plate-anchored anchors.** One nano plate; every character's first frame is the plate with that character added
  (nano from the plate reference), then **pinned to the plate programmatically** inside a diff mask
  (`data/workspace/every-way-home-v1/recipes/anchors.py`) so the room is pixel-identical across all anchors.
- **Loops by book-end.** Each character take uses the same frame as first and last (Veo returns to the anchor around
  frame 88 of 96 for 4 s and 136 of 144 for 6 s; cut the loop there, not at the last frame). The *last* frame is only
  approximate; the *first* is exact. A ping-pong of a still head is a free fallback for a character who only stands.
- **Danger, measured:** a same-frame book-end of a standing figure produced an invented second person walking in
  (EVERY WAY HOME take H). Give every loop a real action with a described force, and probe two or three loops before
  buying twenty.
- **Difference mattes against the plate**, cleaned (close/open, drop small components, feather), stacked at alpha 1
  here (these are solid people, not ghosts), in painter's order by depth (floor contact y).
  `recipes/layers.py` in the same workspace renders a whole film from a JSON layer list (from/at/until, alpha, fades,
  loops with ping-pong); promote it to `tools/` first (handoff below).
- **Scheduling by code.** For each loop, extract the per-frame body mask; compute each pair's overlap over all phase
  offsets; choose entry frames and loop phases so that no two masks ever overlap (a small constraint search; twenty
  characters is tractable). Depth order by floor contact resolves the remaining occlusions. Entry and exit of each
  character happen at the loop's own door-crossing or by a hard pop at an occluded moment, as *Tango* does.
- **Known finish issue:** at 100% the matte carries a faint light rim where Veo's edge light sits inside the matte
  band. Tighten `lo`/dilation for the finishing pass; verify on 100% crops, not thumbnails.

## 4. Plan of work

1. Plate (nano), 16:9, with the furniture placed so there are 6–8 distinct "stations" (door, window, bed, table, cot,
   cupboard, floor center, corner). Keep it sparse; the people are the clutter.
2. Character sheet: twenty one-line actions, each tied to a station and a loop length, each an action a body can repeat
   without reading as a glitch (eat, dress, rock the cot, sweep, climb through the window for a ball, read, pace, change
   a bulb, carry a tray across, argue with nobody). No touching, no two at one station at once, mixed ages, two or three
   children (watch the age-word filter: describe by size and clothing).
3. Probe: three loops (one seated, one crossing, one at the window). Check the matte, the loop return frame, the
   invented-second-person failure. Then buy the rest in two waves.
4. Schedule, render, mix, assemble, review on the status page.

## 5. Budget shape (list, before contingency; amounts stay in the ledger)

Twenty loops at 6 s Quality with audio plus three probes, images for one plate and twenty anchors, contingency of
about 30% for filter trips and rerolls. Roughly three times EVERY WAY HOME. Authorize before the first paid request.

## 6. Handoff: promote the compositor

Target: `tools/ghost-layers.py` (or `tools/layers.py`) from `data/workspace/every-way-home-v1/recipes/layers.py`
(restore a copy from the archive; the workspace is sealed). Keep: plate from file or temporal median, difference matte
with cleaning, per-layer from/at/until/alpha/fades/loop/ping-pong, forward-only readers with hold-last, reader
termination (never `wait()` on a reader whose tail was not consumed), sidecar JSON with source hashes. Add for Tango:
alpha 1 with painter's order by a per-layer depth key, a `--matte-out` dump for the scheduler, and a `--start/--frames`
window for quick checks. Acceptance: re-render EVERY WAY HOME's `edit/layers-v2.json` from a restored copy and match
the retained `clips/FILM-v2.mp4` to within encoder noise (about 1/255 mean).

## 7. Status

- 2026-11-04: brief written at the director's request after EVERY WAY HOME shipped; nothing generated; build in a fresh session.
