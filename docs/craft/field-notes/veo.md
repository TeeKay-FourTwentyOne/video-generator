# Veo field notes

Current adapter and rates: `docs/production.md`, `mcp/video-generator/src/production/veo-spec.ts`.
Basics (entrance motion on static starts, VFX-heavy prompts): `../veo-techniques.md`.

## Filters and rejections

### A filtered take used to look like a hang
Silent RAI trips on submission looked like hung operations in older tooling; the
maintained poll now reports filtered or empty output as a terminal failure. The
reservation stays until evidence says otherwise.
**Apply:** if an operation never completes, inspect its record before any new attempt.
Source: claude-code · several productions · 2026-05 to 2026-09

### Near-portrait anchors trip; scene-embedded poses do not
A reference frame that reads as a portrait of a person is rejected; the same
character mid-wide, in the set, with props visible and the body angled, passes.
**Apply:** anchor characters in-scene. When a submission fails with no prompt
reason, suspect the input image and re-stage it wider before rewriting prose.
Source: claude-code · Hellzapoppin series · 2026-05

### Character macros trip the third-party-content filter
A chest close-up of a toy-like robot including its head was refused ("interests of
third-party content providers", support code 35561575). The same anchor cropped to
lamp, gripper and panel, with the prompt written about objects rather than a
character, was accepted.
**Apply:** for macro inserts, crop identity features out of the anchor and describe objects.
Source: claude-code · Borrowed Light · 2026-10-03

### Schematic faces trip even when small
A rounded head with dot eyes tripped Veo at small size (Nano renders it fine).
Faceless or blank seam-face forms animate fine and read more authored.
**Apply:** probe a schematic face early with one cheap attempt; plan a faceless or
all-stills fallback.
Source: claude-code · SECONDS, Dunham Hall · 2026-06

### Prose words trip independently of the picture
Body or clothing words on a sensitive first frame; "destroyed", "enemy",
"deserve" in combat aftermath; age words combined with body parts; and, in
dialogue, a prohibition plus an ambiguous listener plus "unreadable" (output
filter 15236754).
**Apply:** motion-only prose on sensitive frames; neutral nouns; role-neutral
descriptions; an explicit adult listener; keep dialogue verbatim and recast the
framing as a benign transaction.
Source: claude-code · several productions · 2026-06 to 2026-09

### Crowds and morbid clusters hang or trip
A dense humanoid pile wider than four or five figures tripped even faceless;
corpse and severed prose clustered RAI hangs.
**Apply:** cap crowd width; pre-bake a stills fallback at scoping for morbid beats.
Source: claude-code · 2026-07 to 2026-08

## Motion behavior

### Veo restores what the character "should" have
In a locked-off wide, an EMPTY chest socket was relit for about five seconds
despite a dark anchor and a prompt that said it stays dark. A featureless dome
head asked to "tilt up" stretched into an egg.
**Apply:** when a signature light or prop must stay absent, keep the character
small or in silhouette and do not ask featureless heads to move. If it happens,
repair locally and deterministically: track the ring with a gradient-vote circle
detector, paste the dark socket from a clean frame with a feathered mask, and
paste only on frames where the artifact is detected
(`tools/production/recipes/borrowed-light-fable-socket-fix.py`).
Source: claude-code · Borrowed Light · 2026-10-03

### Veo escalates in the last quarter of a take
A "glow spreads through the branches" prompt became a radial lightning burst from
4.8 s of 8; an approach walk ended in an unasked turn; the other draft's opening
take invented a lamp lift after four seconds.
**Apply:** schedule the beat inside the first two thirds of the take, expect to cut
before the end, and buy eight seconds to use five. Both Borrowed Light drafts used
about 68% of generated seconds.
Source: claude-code · Borrowed Light · 2026-10-03

### Removal and transfer gags fail in-shot
Veo walks a yank or snatch off politely; a prop that must leave a hand or socket
in-shot morphs (arm and bulb geometry changed during extraction in the other
draft); "the payload is the transformation" gags read as mush and fight the filter.
**Apply:** film the mover's arrival, land the removal on a hard cut with a sound
effect, and show the result already in place. The ellipsis is the technique.
Source: claude-code · Floss, Spider Arrest, Borrowed Light · 2026-09 to 2026-10

### Visible-cut endpoints
When a book-end must come apart, the last frame has to show two clearly separated
pieces, or Veo presses them back together.
Source: claude-code · 2026-08

### A reused last frame continues the previous motion
Using one shot's last frame as the next shot's anchor makes Veo continue the walk
rather than start the new beat.
**Apply:** compose a fresh anchor for a re-framed beat.
Source: claude-code · 2026-09

### First-frame anchors do not pixel-bind, and the join still works
A first-frame anchor restages geometry slightly on Fast and Quality alike.
Measured after human review on 2026-08-18: a one-frame restage reads as motion
inside a busy move and as a cut on a held beat.
**Apply:** land every join inside busy motion, end the first clip one frame before
the anchor, and gate with `tools/seam-check.py` (photometric and kinematic channels
reported separately). Door and prop pixel-binds are not a working technique.
Source: claude-code · Seamless Clip Joins, Personal Best · 2026-08

### Last-frame-only requests fail and still bill
A request with only a last frame errors (the adapter now refuses it locally).
Use first-only or first-plus-last.
Source: claude-code · 2026-07

### Identity drifts when a subject appears twice or is partly hidden
A character seen both real and in a reflection can drift in both copies; body
parts hidden by water or spray are re-invented across generations with size and
orientation drift.
**Apply:** keep the reflection face visible in the last frame; keep the subject
fully visible at any boundary; occlusion hides seams and breeds drift.
Source: claude-code · 2026-08

### Fast drifts gender; Quality for identity shots; skip Fast drafts
Specify gender explicitly on the Fast model. When identity is load-bearing use
Quality. A Fast "draft pass" rarely transfers: generate on Quality and iterate on
the image anchors instead.
Source: claude-code · 2026-06 to 2026-08

### Walla comes back as dialogue
"Indistinct conversation" returns fully legible lines.
**Apply:** transcribe every ambient-talk take, then keep, caption or bury it.
Source: claude-code · 2026-09

### Capitals and era words render as text
An ALL-CAPS word becomes a giant sign; "silent film" or vintage styling bakes in
title cards (Nano as well).
**Apply:** sentence case throughout and a closing no-text line; never ask for an
era's text style unless text is wanted.
Source: claude-code · 2026-06

### Book-end return frames
With identical first and last frames the motion returns to the anchor near frame
136 of 144 (6 s) and 88 of 96 (4 s); `matchscan.py` finds the cut frame and tail freezes.
Source: claude-code · 2026-07

### A displaced prop between book-end frames gets an invented agent
A pin-and-sheet close-up was book-ended with a last frame in which the clothespin
had restaged a little along the cord (the frame pair passed anchor-drift). Veo
explained the displacement by bringing in a hand with a second clothespin to re-pin
the corner, and the sheet never came free. The first-frame-only retake with a
gust-only prompt released the sheet on its own, though a hand still brushed the
sheet's edge for about fifteen frames early in the take.
**Apply:** when the end state can be reached by wind, gravity or light alone, prefer
first frame only and describe the force; if a last frame is used, the only thing
that may differ is the thing that moves, and "no hands, no people" belongs in the
prompt even for an object close-up.
Source: claude-code · Washing Day · 2026-10-03

### Continuation joins hold at the busy frame, not at the end of the take
A rising camera move decayed in energy through its eight seconds (mean frame delta
7.8 at frame 84 to 2.7 at 190). Anchoring the continuation on frame 120, where the
motion was still busy and the subject fully visible, gave seam-check PASS at
A:119 → B:0 (photometric ratio 1.10, velocity ratio 1.12); every head trim made it
worse (3 frames MARGINAL, 9 frames FAIL) because the restage grows as B plays.
**Apply:** scan the first clip's per-frame motion energy, anchor the continuation
where it is still high, end A at anchor minus one, and start B at frame 0.
Source: claude-code · Washing Day · 2026-10-03

### Cloth in a locked-off medium shot stays legible; cloth in a rising wide stretches
Across the balcony medium shots (pinning, a gust, unpinning, the sheet lifting out of
frame) the cloth, the hands and the red shirt held for the whole take; the same sheet
seen from below while the camera rose became a long twisted ribbon that stayed near
the line instead of climbing away. The rooftop wide let a second sheet emerge but
fused the two after about six seconds.
**Apply:** give cloth gags a locked camera and a human-scale frame; buy eight seconds
for the wide and plan to use the first six.
Source: claude-code · Washing Day · 2026-10-03

## Native audio

### Native audio is the default for on-camera lines
Keep audio generation on with explicit sound cues in the prompt; use ElevenLabs
only for narrator, computer or disembodied voices. Suppress native audio for a
stated reason, such as a silent film with a composed score or a budget that
cannot carry the doubled per-second rate (Borrowed Light).
Source: claude-code · 2026-06 to 2026-10

### Composite tests need their own mini-mix
An insert test delivered without a bed reads as a wrong-voice attribution bug.
Ship it as a mix (line about −16.5 dBFS RMS, bed about −23 ducked).
Source: claude-code · Floss · 2026-09

### Native courtyard ambience came back nearly silent
A locked-off wide with "clothespin clicks, swifts, a muffled radio far below" in the
prompt returned an almost silent air bed (−43 LUFS integrated, 0.7 LU range); the
balcony medium with cloth and pins returned a usable track (−20 LUFS) with a hard
cloth transient. Both carried no music lines or speech-like striations on a
spectrogram (the agent did not listen in real time).
**Apply:** treat native audio on distant wides as a maybe; keep the foley close to
the camera, and plan local clicks and cloth for the wide.
Source: claude-code · Washing Day · 2026-10-03

## Cost behavior

### Every submission bills
Filter rejections, hangs and duration round-ups all count. Plan about 30% over
clip arithmetic. Dated rates live in `veo-spec.ts`; a 2K Nano image is about
$0.14. The maintained ledger keeps a failed attempt reserved until evidence says otherwise.
Source: claude-code · 2026-05 to 2026-10

### Stills plus programmatic motion for stillness beats, Veo for narrative
A no-character stillness beat (landscape, explainer insert) is Nano stills plus
local motion at zero Veo cost; a narrative beat needs Veo for every shot, because
stills with motion read as a slideshow there.
Source: claude-code · 2026-06 to 2026-08
