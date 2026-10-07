# Borrowed Light

Original test film for the repository review, October 2026. Delivered: 32.5 seconds,
1080 x 1920 (9:16), 24 fps. Total authorized provider spend: $20, including
reference images, video, QA and incidental storage. No new providers or libraries.

## Release status

**Status:** Shipped (2026-10-06; confirmed by the user). Two versions were
published from this brief, one per agent:

**YouTube Short — original Codex/Astra version:** https://youtube.com/shorts/w9qSEj9i69w
**YouTube Short — Claude (Fable 5.1) version:** https://youtube.com/shorts/mbAgckAWQB4

Both links were supplied by the user; public availability was not independently
verified by either agent.

## Synopsis

A maintenance machine enters a dead greenhouse. It finds a tree whose roots end
in an empty lamp socket. The machine removes its own chest lamp and plants it.
Light climbs the branches and spreads through the tower. In the final wide shot,
the machine remains dark: it can see by the light it has given away.

The camera starts distant, approaches the irreversible choice through increasingly
close framing, then returns to the opening scale. The film does not announce a
moral or restore the machine's lamp. Giving changes its surroundings, not its loss.

## Visual and sonic continuity

- Hand-built cinematic miniature: weathered blue enamel, brass, smoked glass,
  oxidized greenhouse ribs. Amber practical light against deep teal night.
- One machine only: squat rectangular petrol-blue body, two short brass arms
  ending in two-prong grippers, two narrow caterpillar tracks, small cream ceramic
  head with one black horizontal viewing slit. One round amber lamp in its chest.
  A diagonal pale scratch crosses its left body panel. No face, mouth or clothing.
- One dry tree in a low round planter, inside a tall arched greenhouse tower.
  The base has one empty brass socket. No other plants before the transfer.
- After the transfer, the chest socket stays dark and empty. No duplicate lamps,
  machines or grippers. The tree's light is motivated from its base upward.
- No speech. Local original score and foley move from a repeating mechanical
  pulse to an imperfect, warmer rhythm. A short near-silence surrounds the transfer.

## Coverage

| Shot | Edit seconds | Purpose |
| --- | ---: | --- |
| S01 | 3.5 | Vertical wide: the small lamp enters an enormous dark structure. |
| S02 | 6.5 | Medium: the machine discovers the empty socket beneath the dry tree. |
| S03 | 2 | Close insert: the gripper takes hold of the only chest lamp. |
| S04 | 4.5 | Low close-up after an ellipsis: the lamp is seated; light enters the roots. |
| S05 | 8 | Rising close-to-wide: warm light travels through bare branches. |
| S06 | 8 | Return wide: the greenhouse is alive with light; the machine is a silhouette. |

Each generated take is eight seconds, allowing an edit decision after inspection.
First-frame anchors establish character, geography and the before/after states.
Local insert shots or trims may replace defective action; do not reroll blindly.
The blocking board, image prompts, operation records, budget, source clips,
timeline, review decisions and versioned exports live in
`data/workspace/borrowed-light-v1/`.

The initial 44-second plan tightened to 32.5 after footage review. S01 developed
an unwanted lamp lift after four seconds; S03 changed arm and bulb geometry during
extraction. The edit removes those ranges and uses a deliberate action ellipsis.
S04's anchor is a local crop of S05's actual first frame, which makes its placement
match without buying another transfer attempt. Two rejected generated S04 anchors
remain preserved. The v2 export adds local opening/closing fades and an end title;
v1 retains the unadorned picture edit.

## Delivery and cost

Primary film: `data/workspace/borrowed-light-v1/final/v2/film.mp4`.
Review player and delivery manifest are adjacent. 780 frames, H.264, 24 fps,
48 kHz stereo AAC. The original local score is titled **What remains**.

Usage-based estimate: $9.60 for six silent Veo Quality takes, $0.982746 for seven
Google reference-image attempts, and $0.217076 for sixteen Claude QA calls.
Including a retained $0.40 infrastructure reserve: **$11.199822 of $20**.
These are saved-usage/list-price estimates, not invoice-confirmed charges.
Rejected references and discarded footage are included. No new provider or library
was used. No assets were deleted during production.

## Review contract

Check full decode, dimensions, exact frame count, source hashes, audio peaks and
loudness. Inspect each take for object-count and prop continuity, and examine
frames densely around lamp transfer and hard cuts. Technical checks do not confer
artistic approval. Preserve the native review export; publication and 4K finishing
are separate decisions. The supplied release URL and current status are recorded above.

The native export passed full decode, frame-count, dimensions and source checks.
Measured audio: -19.00 LUFS, -5.89 dBTP, 5.2 LU range; zero-offset correlation with
the prepared soundtrack was 0.99993. Source contact sheets, dense motion windows,
the final overview and full-size title were inspected. Real-time playback and
audible listening were not certified: the computer-use session had no available
browser and native window lookup failed. Some generated microgeometry varies
between shot scales; the film does not demonstrate a continuous mechanical transfer.

## Independent Claude draft (Fable 5.1), 2026-10-03

A second first draft built from this brief without consulting the delivery above,
to exercise the same production path. Workspace: `data/workspace/borrowed-light-fable/`.
Native review export: `final/v1/film.mp4` (790 frames, 32.92 s, 1080 x 1920, 24 fps,
AAC 48 kHz stereo), with `review.html`, `delivery.json` and a `film_debug.mp4`
timecode/frame overlay. Same six-shot structure plus a local end title; all six
takes are Veo 3.1 Quality, silent, 1080p, from nano-generated first-frame anchors
(no last frames: the lamp removal lands in the S03/S04 cut). Original local score
and foley **By Given Light** (`recipes/score.py`, deterministic numpy synthesis;
regular mechanical pulse, near-silence across the transfer, imperfect warm rhythm
with climbing bells). Measured -15.9 LUFS integrated, -3.2 dBTP, 0.99996
zero-offset correlation with the prepared soundtrack.

Edit decisions: S01 cut at 3.33 s before a stray orb in the dark crown; S03 is a
retake (S03-v2) after the first submission was rejected by Veo's third-party-content
filter on the head-bearing macro anchor, solved with a head-free crop of the same
anchor; S05 cut at 4.58 s as the crown flares, before Veo's radial burst; S06's
re-lit chest socket was repaired locally with a tracked, feathered paste of the dark
socket (`recipes/s06-fix.py`, proof strips kept). The machine's head stretches while
tilting in S06 and is flagged for review. Estimated spend $11.79 of $20, including
one rejected Veo attempt retained at full reservation and a $0.30 infrastructure
reserve; list-price/saved-usage estimates, not invoice-confirmed. Real-time
playback and listening were not certified by the agent.
After the director's approval a 4K master was made locally (`final/v1/film_4k.mp4`,
2160 x 3840, 790 frames, audio packets identical to the native export) with the
fast x2 model that produced the earlier 2026 masters; crops verified at 100%.

**Published:** https://youtube.com/shorts/mbAgckAWQB4 (2026-10-06, link supplied
by the user; this is the Claude version, distinct from the Codex/Astra Short above).

## Side-by-side comparison cut and Astra 4K master, 2026-10-03 (evening)

Astra's `final/v2/film.mp4` was upscaled with the same per-segment recipe as the Claude
master (`final/v2/upscale-4k/run.sh`: Real-ESRGAN realesr-animevideov3-x2, stream concat,
native AAC muxed in) to `data/workspace/borrowed-light-v1/final/v2/film_4k.mp4`
(2160 x 3840, 780 frames). A 16:9 comparison piece, 3840 x 2160, 24 fps, 56.5 s, plays
both drafts side by side (Astra left, Claude right) with an intro, three cards timed to the
shots, a numbers table and credits: workspace `data/workspace/borrowed-light-compare/`
(`cards.json` holds all on-screen copy and timings; `recipes/build.py` and `recipes/mix.sh`
are mirrored in `tools/production/recipes/borrowed-light-compare-*`). Delivery
`final/v2/borrowed-light-compare_4k.mp4` (128.5 s) with a 1080p copy beside it; v2 adds two 36 s
freeze interludes in which both panels hold on the same frame while the spine quotes the brief,
Astra's prompt and Claude's prompt verbatim for the machine (film 4.5 s) and for the light
climbing the tree (film 20.5 s). v1 (56.5 s, no interludes) is kept. Sound alternates: Astra's
score to the transfer near-silence, Claude's from there to the end, Astra's second half under
the outro cards; -16.2 LUFS integrated. Facts on the cards come from each workspace's QA
decisions, ledgers, prompts and this brief. Astra may append review notes as a further card.
Not published.
