# Hall of Memories — resume after the first jewel reveal

Superseded continuation status, 2026-09-27: begin with the
[Exchange handoff](hall_of_memories_exchange_handoff.md). The Hall and the new
121-second deep-time/alien segment are accepted working baselines, and the
available core is 306 seconds. This older note retains detailed Hall sources
and QA; its pending-review and next-deep-time instructions are historical.

Updated 2026-09-27. Read the [treatment](hall_of_memories_brief.md), the
[main handoff](hall_of_memories_handoff.md), and the
[Hall scene note](hall_of_memories_hall.md). Repository rules remain in
`AGENTS.md` and `CLAUDE.md`.

## Decision status and session boundary

The conversation and invitation are accepted working baselines. The user said
these polis scenes will be revised together once the core is complete. Preserve
that direction; do not reopen their design or request the same approval again.

The current session continued at the user's discretion from the updated
handoff. It drafted the complete Hall demonstration and withdrawal to the first
exterior jewel reveal. The new Hall segment is a first draft awaiting the user's
response. It does not lock the record, human design, voice quality, Hall sound,
jewel material or transition. A courteous delivery acknowledgment alone should
not be recorded as creative approval.

The available continuous core is 185.000 seconds:

1. The tellers: 39.875 seconds, accepted working baseline.
2. With one person: 46.250 seconds, accepted working baseline.
3. One whole life: 98.875 seconds, new Hall draft for review.

The third segment begins at context time 86.125 seconds. Both earlier segments
retain every picture frame and their original timing. The factory remains
outside this context review; its matched-gesture endpoint is unfinished.

## What the new segment establishes provisionally

The four figures enter the retained Hall from the previous threshold marks.
The elder selects Mara, an ordinary fictional adult. A blue cup with a pale chip
recurs through tea with her father, a private letter exposed to others, a bedside
visit, and the habit of setting out two cups after loss. The silent recipient
of the letter is a separate person from her father. The miniature record
characters and sparse fragments are a first local treatment, not factual
records or final human design. No age, date or demographic claim is established.

The child asks whether this is everything. The elder says: “Only moments.
Listen to what the Hall makes of the whole life.” The first derived voice has
its own beat and a visible child reaction. “One person?” / “One person.” Then
additional voices enter, cabinets activate, and the camera withdraws.
The records are not identified as conscious reconstructions; no torture
mechanism, moral score, extinction explanation or biological identity for the
elder is asserted. The history in the treatment remains ambiguous. An explicit elder interpretation
of humanity's disappearance has not yet been added to the three-scene dialogue;
consider that during the coordinated polis revision rather than treating this
draft as a complete exposition of the transhuman/biological split.

The exterior Hall view becomes an image on a green facet. Its image dissolves
as the camera reveals an uneven six-sided emerald-like housing embedded in
rock, with one pale diagonal inclusion. This is a conceptual change from
simulation to housing, not a corridor into a cave or an established external
sensor. GEM-01 remains provisional in shape, finish and physical scale, but
retain this exact mesh/inclusion as the current continuity asset.

End on the held jewel. No broad Earth cutaway, geological acceleration, aliens,
new human recurrence, feast, infant or final crowd has been produced. The film's
final quarter-second silence does not belong to this segment's boundary.

## Selected local artifacts

Paths are relative to `data/workspace/hall-of-memories/`.

| Purpose | Artifact |
| --- | --- |
| New segment and three-scene review page | `polis-hall-v1/edit-v1/index.html` |
| Hall native movie | `polis-hall-v1/edit-v1/review/polis-hall-1080p.mp4` |
| Three-scene native movie | `polis-hall-v1/edit-v1/review/polis-three-scenes-1080p.mp4` |
| Smaller movies | Corresponding `-720p.mp4` files in that review directory |
| PCM masters | `polis-hall-v1/edit-v1/masters/polis-hall.mov` and `polis-three-scenes.mov` |
| Editable stepped animation | `polis-hall-v1/animation-v1/polis-hall-animation.blend` |
| Native poses and frozen rendering source | `polis-hall-v1/render-v1/frames/` and `render-v1/recipe/` |
| Performance timing and combined offsets | `polis-hall-v1/timeline.json` and `master-timeline.json` |
| Separate stems and individual voices | `polis-hall-v1/audio/` and `audio/voices/` |
| First derived voice for later recurrence | `polis-hall-v1/audio/voices/mara-whole-life.wav` |
| Hall image used on the facet | `polis-hall-v1/assets/hall-facet.png` and `manifest.json` |
| Native export/context verification | `polis-hall-v1/edit-v1/qa/verification.json` |
| Actual visual/listening inspection scope | `polis-hall-v1/qa/final-review.md` |
| Animation comparison and acting audit | `polis-hall-v1/qa/baked-animation.json` and `recipe-acting.json` |
| Spend and preservation records | `polis-hall-v1/ledger.json` and `baseline-preservation.json` |
| Original conversation | `polis-draft-v1/edit-v2/index.html` |
| Accepted invitation and older context review | `polis-invitation-v1/edit-v1/index.html` |

The run-root Hall page links to its selected review. Internal `look-*` studies,
`audio-incomplete-v1` and `animation-internal-v1` are retained implementation
history, not alternate creative deliveries. Earlier media are preserved.
The preceding next-session handoff is retained under `polis-hall-v1/handoffs/`.

## Technical notes and actual review limits

The Hall has 791 native 1920 x 1080 source poses, held at eight poses per second
within 24 fps output: 2,373 frames. The complete context has 4,440 frames.
Its source sound contains 4,746,000 stereo samples at 48 kHz and peaks at
approximately -9.08 dBFS. Six stems separate dialogue, record fragments, first
voice, accumulation, atmosphere and Foley. The context contains 8,880,000
samples before AAC encoding, built from the three PCM masters with no
independent gain changes. No music is added.

All six exports passed full decoding, frame count, raster, rate and duration
checks. The native context picture matches all three decoded masters exactly,
and its PCM audio is the exact concatenation of those masters. Retained
baseline hashes are unchanged. Every source PNG passed integrity checks; no
unexpected black poses were found, and the final four seconds of source picture
are pixel-identical.

Visual inspection used small framing passes, native key frames and contact
sheets. The acting audit covers 68 speaking poses and checks head/face framing;
entry root separation stays above approximately 0.986 units. The saved animation
was compared with the retained recipe at all 791 poses, including camera,
geometry, cabinet-light strengths and facet fade, within a 0.0002 numeric
tolerance. Constant interpolation and the relative sound path were checked.

No real-time playback or listening assessment was possible through the available
tools. Voice recognition, distress performance and emotional effect remain
unverified by listening. Both record speech and Hall voices are temporary:
installed macOS synthesis and original procedural vowels, not actual human
suffering or cloned voices. Do not turn technical checks into a claim that the
sound was listened to or creatively approved.

Source is in `tools/hall-of-memories/polis_hall*`, with commands and dependencies
in that directory's README. Use `data/tools/upscale-venv/bin/python` for NumPy,
Pillow and FFmpeg preparation/finishing. Blender is the existing local 4.5 build.
The native recipe uses Cycles/Metal, seed 926 and 16 samples. No provider calls.

Recipe renders reconstruct geometry and poses; they do not consume manual edits
to the saved animation. The bake uses the frozen `render-v1/recipe/` source and
packs the Hall facet image. Keep the image hash, timing and recipe together.
To resume, use the frozen source with an unrendered frame range. Existing ranges
and changed rendering recipes are refused. Use a new version for revisions.

Identical PNG holds use hard links to reduce disk use. Do not modify a numbered
PNG in place: that could change every pose sharing its inode. Write changed
frames to a new version directory. The recipe stops at its storage reserve.
Check free space before another frame-heavy run and never remove retained media
or unrelated work merely to make room.

## Next action

Receive the user's reaction to this new Hall draft. Prioritize whether the
ordinary record registers, whether the solitary voice reads as human suffering,
and whether the simulation-to-jewel transition is intelligible. A requested
focused revision should produce a new complete segment/context version.

If the user asks to keep building the core, preserve this provisional draft and
choose one bounded deep-time section next. Begin from the exact jewel hold,
plan changes of scale, and audition the geological passage before a long render.
Do not assume final jewel dimensions, a literal software/external clock ratio,
or that these same children consciously watch every geological interval.
Keep the alien visit, later evolution, Exchange and ending as separate design
work unless the next scope explicitly includes them. Final polis polish remains
a coordinated later pass, as the user requested.

The first two polis drafts and this Hall draft each have zero new provider calls
and charges. Earlier fifteen built-in image calls remain unmetered with unknown
exact cost. No paid chapter ceiling is established; determine scope, ceiling and
ledger before paid production. The $20 chapter floor is not a demand to spend
on a local draft or permission for unlimited charges.

No 4K finish, publication, commit or push is part of this delivery. Preserve
unrelated Meridian House, ANGLES, episode-five, scene-lab and budget-tool work.
Any later source release follows privacy checks and the TK-421 identity rules.
