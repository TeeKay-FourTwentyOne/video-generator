# Hall of Memories — first implementation review

## Current focus — complete polis scene, 2026-09-26

The user switched focus from the factory test to a complete first draft of the
children talking inside the polis, beginning after the factory cut and ending
when the older resident joins. See `hall_of_memories_polis_scene.md` for the
new draft dialogue and staging. New choices remain provisional.

The local run is `data/workspace/hall-of-memories/polis-draft-v1/`. It contains
15 dialogue lines across 39.875 seconds, with three children and an elder. The
elder's first reply closes this segment; no Hall visit or historical explanation
is included. The factory endpoint still needs to match the opening hand gesture.

The scene uses a persistent Blender court and articulated rounded graphite
avatars with yellow-orange eye glow. Motion is sampled at eight poses per second
within 24 fps. Native output is 1920 × 1080. Temporary voices use installed local
speech, with original atmosphere and Foley. Optional captions remain separate.
There are no new image, video or voice provider calls or charges. The prior
fifteen unmetered image calls remain recorded without a known dollar total.

An editable animation is saved with 957 timeline frames, constant-interpolation
pose keys and a relative link to the sound mix. Factory media and the deferred
ending work are preserved. The selected complete review is
`polis-draft-v1/edit-v2/index.html` under the Hall workspace, with 1080p and 720p
movies, a PCM master and the full screenplay. The editable animation is
`polis-draft-v1/animation-v3/polis-animation.blend`. All final exports passed full
decode, frame count, raster and audio-duration checks. Visual sampling caught
and corrected an abrupt entrance and accidental earlier background visibility
of the elder. All earlier camera positions were then checked for that issue.
This is a complete first draft pending user review, not a final design or
performance approval.

## Earlier work

Prepared 2026-09-23 following authorization to make a very rough, high-level board
and choose audition directions autonomously. The treatment and handoff remain
authoritative for accepted story decisions. This note distinguishes proposals,
implementation evidence and subsequent dated user approvals.

## User clarification after this review

At minimum, the factory framing story and The Exchange must be photorealistic.
The factory should evoke a stereotypically depressed workspace; The Exchange
should feel more cinematic. Generating the entire film with Veo is cost prohibitive.

The board primarily tests broad flow, staging, framing and transitions. Its
paper-theatre aesthetic was also an assistant proposal, not merely neutral
placeholder styling. That proposal is superseded for these two passages. Their
geometric figures and materials should now be read only as blocking. Final looks
elsewhere remain open; none was approved by approving the creation of auditions.

Proposed next look tests: a flat, fluorescent, grey-green/beige factory with tired
surfaces and unflattering light; a firelit Exchange with richer skin/material
detail, controlled shadows and deliberate depth. These specific lighting and
palette choices are proposals within the user's two required registers. Test
representative still frames before expanding motion production. Local movement
of layers and cameras can support selected shots; convincing human acting may
need selective generated motion or another performance method. No paid call or
ceiling is authorized by this clarification.

## Factory robot refinement — 2026-09-24

Latest user direction: make the robots darker grey and smoothly rounded, with
brighter, more orange yellow eyes that glow unnaturally. The new revision is at
`data/workspace/hall-of-memories/factory-robot-style-v2/`: selected images are
`F01-rounded-robots.png` and `R01-straight-on-close.png`, with an `index.html`
review page. On 2026-09-24 the user accepted this revision with "Perfect."
The selected frames establish the approved rounded dark-grey robot look,
bright yellow/orange glow and contrast against the photographic factory.
The earlier faceted proposal is superseded
as the intended design direction, while its files remain preserved.

The user also specified robot coverage: roughly one or two establishing views,
then predominantly straight-on close-ups from neck or shoulder level upward.
Editing should make their positions relative to the man and machinery clear.
The frontal close-up auditions that instruction. It does not lock the exact
camera marks or remove action/prop coverage elsewhere in the scene. The visual
approval does not approve motion cadence, casting, chapter timing or spending.

The user also deferred ending style decisions until work begins on that
sequence. The Exchange and ending frames remain provisional; their review does
not block beginning the factory.

This revision used three built-in image calls, including a wide preservation pass
against the original photographic frame, for eight look-frame calls cumulatively.
Exact charges remain unknown. The initial rounded candidate and exact prompts
are retained locally. No Veo or changes to the Exchange/end frames.

Earlier revision history follows.

The user requested that Factory 1 retain its photographic man and setting while
the robots become visibly unreal and match the polis inhabitants. They will give
feedback on the end frames after this is finalized. Keep current work focused on
Factory 1; the Exchange remains pending review.

The targeted revision is
`data/workspace/hall-of-memories/factory-robot-style-v1/F01-unreal-robots.png`.
It uses the original F01 as edit target and the polis circle board as a character
design reference: plain grey faceted bodies, broad heads, yellow eyes, no mouths,
and deliberately simplified surface shading. The man and workshop remain
photographic. The visible contrast and common character family are required;
this exact faceted design is still an audition awaiting user feedback.

One additional built-in image edit completed; five calls cumulatively, with
unknown exact charges. The prompt, reference hashes and ledger are retained in
that local run. All four earlier look-frame images are unchanged. F02 has not
yet been regenerated to match this new direction. No Veo or end-frame generation.

## Initial final-look frame auditions

The user subsequently explicitly requested proceeding with final-look frame
generation. Four frames are saved under
`data/workspace/hall-of-memories/look-frames-v1/`, with `index.html` for comparison,
`prompts.md` for the exact prompt set and `README.md` for review notes.

- `images/F01-factory-wide.png`: flat fluorescent realism, a weary worker and two
  physically plausible grey supervisors in a worn workshop.
- `images/F02-factory-timer.png`: a closer frame using F01 as the continuity
  reference, with the impossible yellow-eyed timer on the workstation.
- `images/E01-exchange-wide.png`: cinematic firelit ensemble, chief resisting,
  clearly adult daughter guarded, victorious warrior pressing his demand.
- `images/E02-exchange-emerald.png`: a closer frame using E01 as the continuity
  reference; the same woman attends to the jewel without an approving smile.

These are intended photographic finish references, not flow-only placeholders.
All remain pending user review. Four built-in `image_gen` calls completed, without
retries. Exact billing and model identity were not exposed; the local ledger
records four unmetered requests, not a zero-dollar cost. No Veo was invoked.
The still-generation request does not establish a ceiling for chapter production.

Native outputs are 1672 by 941, approximately 16:9, preserved without alteration.
The prompted dimensions were 2048 by 1152; exact delivery framing remains pending.
Direct visual review supports the lighting-register distinction and recognizable
identity within each pair. These images do not establish calibrated set geometry
or motion continuity. The factory's mechanical robots belong to the child's
legend and do not lock the polis avatars' final material treatment.

The emerald's requested asymmetric six-sided form and pale diagonal inclusion
did not resolve exactly; E02 is a scene-look reference, not the canonical jewel.
The timer still needs recognizable timing controls and locally composed text.
The Exchange currently uses a familiar rugged period-film vocabulary, which
remains reviewable. Existing rough board and motion tests are preserved unchanged.

## First blocking review package

`data/workspace/hall-of-memories/auditions-v2/index.html` contains the board,
playable auditions, native 1080p review copies, smaller 720p copies and comparison
notes. Exact PCM-audio masters, editable stems, cue times, source recipe and
checks remain beside them. Earlier local studies are retained separately.

The board contains twelve broad beats and a provisional 5:14 total. It is not a
shot list or a complete rough animatic. Chapter boundaries and ceilings remain
open; the chapter planning floor is not treated as spending authorization.
New provider calls and charges for this work: zero.

## Directions used in the first blocking audition

- Oxide factory, dull brass, paper-cut human bodies. The factory test uses a
  six-second routine lead-in and the accepted working dialogue through the
  gesture cut. It omits the later, more elaborate control relocations and wrong
  doors. The board reserves more time for the eventual opening.
- Chalk-grey, mouthless inhabitants beneath a split, displaced sky disc. Acting
  is in hands and posture. Shared worker/child joint positions anchor the cut.
- A pale Hall with narrow vertical ribs and a stepped forecourt, reused for the
  final crowd. Its architecture is deliberately austere, not a circuit diagram.
- An uneven emerald prism with a diagonal pale inclusion. A moving camera leaves
  the Hall; the view resolves into a facet and then physical material, before
  receding into a rock cutaway. The scale handoff is conceptual and the cutaway
  is schematic. Actual geological movement belongs to a later audition.
- A proposed ordinary record framed by a shared table and an empty chair. The
  blue-grey record figure is visually separate from the oxide factory worker.
  No biography or explanation of humanity's final choice has been selected.
- Prefer holding the unmoving crowd through the infant passage. Compare a return
  to the clothed adult daughter on furs with exactly the same sound and duration.
  The comparison changes the picture placement only. Outside perception remains
  undesigned, and the crowd's upward gaze is a blocking choice rather than a
  commitment to a screen or sky projection.

## Review limits and next decisions

Stock adult speech is a timing placeholder, not casting. The infant, party walla
and Hall voices are original wordless synthesis, not recordings of distress.
Sound recognition and emotional effect require listening review; the current
sound is not a proposed final performance. The Hall's recurring material is
reused at the end. Its first single voice has a two-second solitary pause.

The 24 fps ending has a quarter-second of sample-exact silence in its PCM master.
The review package records physical stillness, causal cue order, format and final
black/silence checks. Sampled visual review corrected an early scale jump at the
facet transition and clarified the crowd's upward gaze. Technical checks do not
approve the edit or establish emotional success.

The initial review proposed addressing the visual registers, factory reveal,
scale transition and ending placement. Subsequent decisions above supersede
that review order: ending style is now deferred. Refine the rough animatic as
chapters develop and establish the active production scope and ceiling before
paid motion generation. The initial local blocking involved no paid generation;
later still-generation calls are recorded above. No 4K finishing, publication,
commit or push has occurred for this film.

## Recommended production entry — 2026-09-24

Assistant recommendation, not a newly authorized production run: begin inside
Chapter 1 with a short excerpt of the ordinary-workday routine. First develop a
frontal robot reaction close-up, then cut it against one controlled human lever
action and a clipboard or clock insert. Roughly 15–20 seconds is a useful test
scope, not the locked opening duration. Preserve the opening's clock-in and stool
beats when assembling the full sequence. Use machinery sound without narration
for this excerpt, as required by the opening's story logic.

This is the smallest useful test of the approved realism contrast, restrained
robot performance and editing-based spatial continuity. The human hand/lever
action is the main technical uncertainty: test discrete poses/local animation
before deciding whether that shot warrants selective generated motion. Existing
stills are finish references, not calibrated rigs or complete motion assets.

Next develop the timer contradiction: its appearance, eyes and exact notice
can be controlled locally, while accepted working dialogue supplies the timing.
The timer prop needs refinement and F02 still contains the superseded robots.
The duplicate worker, disappearing door and gesture match are later factory
tasks. The circle needs age distinctions, setting and voice choices; the Hall
needs its architecture, individual record and sound. Geology/return depend on
the canonical jewel and coherent scale treatment. Exchange and ending style
review can remain deferred. No new generation or chapter spending is initiated
by this recommendation.

## Factory motion study — production instruction, 2026-09-24

The user authorized proceeding with the short factory test, with a new final-cut
constraint: robots do not appear at the beginning of the chapter, appear only
sparsely until the last two thirds, and ramp toward the end. Exact reveal times
remain open. This supersedes placing a robot reaction inside the initial
work-routine excerpt; the robot performance is developed separately.

The run is `data/workspace/hall-of-memories/factory-motion-v1/`. Seven built-in
image calls prepared a robot-free wide, lever reference, separate lever/hand
foreground and machine background, clock insert, and separate robot foreground
and photographic background. All calls completed; exact charges were not exposed.
That is fifteen built-in image calls cumulatively, including prior look work.
No Veo, paid audio generation or paid analysis was used.

Local production tests an 18-second routine without robots or narration and a
separate six-second frontal robot performance. The routine begins at the
workstation; clock-in and stool adjustment remain for the complete opening.
The lever and robot use eight held poses per second in a 24 fps edit. A native
1664 × 936 crop preserves image scale, with smaller review copies. The worker
wide remains a held photograph; the lever uses one rigid hand/forearm/lever
layer, and the robot makes a planar head tilt. These are bounded performance
tests, not a claim of complete human rigging or finished chapter footage.

Exact prompts, original plates, source recipe, timing, sound stems and billing
uncertainty are retained locally. Motion cadence, pacing and sound remain for
user review. Ending work stays deferred.

Selected review: `factory-motion-v1/edit-v3/index.html`. The two prior local
renders are retained internally. The selected edit fixes frame-exact assembly,
the clock hand's alpha and the robot's neck backing. Both masters and all four
MP4 review copies passed full decoding, duration/frame-count, raster and audio
checks. Sampled picture review includes every second of the opening and the
robot's full-resolution maximum tilt; listening review is still pending.
