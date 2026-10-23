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

### A small prop leaving the body fails in-shot even in close-up
Two Quality takes asked for a wireless earbud to be taken out of an ear (a close-up with the hand
already at the ear, and a two-shot). In the close-up the fingers fiddled for three seconds, the hand
dropped with the earbud still in, and the earbud then vanished between two frames with no hand-off;
in the two-shot the hand went to the ear and came away with the earbud still in place. The look-up and
smile that followed were usable in both.
**Apply:** the removal note holds at prop scale: film the hand at the ear and, separately, the state
after; bridge them with a cutaway (the other person's reaction) and land a click on the cut. If the
beat must be seen, anchor the first frame with the prop already out and in the fingers, and ask only
for a look and a lowered hand.
Source: claude-code · Balcony · 2026-10-19

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

### "Quiet, natural, continuous conversation" comes back as legible, scene-apt lines
Six Quality takes with audio, each prompting background pairs to talk "quietly and naturally"
with no topic given, returned clear English dialogue in five of five rooms (café, tram, park,
laundromat, bar): weather, errands, the size of a sheet, the light. Whisper transcribed all of
it at no_speech_prob 0.00-0.03. The lines fitted their rooms and even rhymed across takes
(rain in the morning, "after all that rain" at noon). A foreground character told not to speak
did not speak in any take. The one line asked to be "too soft to make out" (the lead at a night
bus stop) was not audible at all: Whisper hallucinated a stock phrase (no_speech_prob 0.43,
avg_logprob -1.80) and the spectrogram showed traffic only.
**Apply:** when the background's words are wanted, ask for audible natural conversation and
let the model pick the topic; when a line must be inaudible, expect silence, not a murmur, and
filter Whisper by no_speech_prob and avg_logprob before trusting a caption.
Source: claude-code · Walla · 2026-10-08

### "She does not speak" is ignored: Veo lip-syncs the foreground face, with or without audio
Six audio takes of a listening woman with talkers behind her: in five of six she visibly
mouthed one of the background's lines. Dense face strips every second frame against Whisper's
word stamps help locate the motion, but a brief window in profile still needs playback review.
Three silent retakes
(no audio generation, the talkers named as the only speakers, "her lips stay closed and still,
she never speaks, mouths words, laughs or hums") did not fix it: one take mouthed words for 80
frames with no sound at all, one grinned open-mouthed for two seconds, one held for 66 frames
and then talked. Removing the dialogue track does not remove the mouth animation.
**Apply:** for a character who must stay silent among talkers, plan the cut before buying: use
the head of the take (her lips held in every take for the first 2 to 3 s), keep her in profile
or looking down when the lines land, or give her mouth business (a cup, a glass). Read her lips
on a 2-frame strip against the word stamps before accepting any range, and stop each room's
audio before her first line so the tail does not leak a syllable.
Source: claude-code · Walla · 2026-10-08

### A long two-clause line loses its second clause
A 19-word line with a colon in the middle ("And you, sweet voice below: the night keeps you the way a
ring keeps a stone") came back with the first clause clear (2.3–5.2 s) and the rest as mouth motion with
unintelligible sound to about 5.9 s; two Whisper models agreed, and the spectrogram showed weak,
unstructured harmonics after the clause. Three other lines of 12–15 words in the same film were delivered
verbatim, so the risk is the length and the pause, not the vocabulary.
**Apply:** keep a spoken line to one clause of about a dozen words per take, put the payload words first,
and split a longer verse across two takes or two speakers. Transcribe every dialogue take before cutting.
Source: claude-code · Balcony · 2026-10-19

## Cost behavior

### Every submission bills
Filter rejections, hangs and duration round-ups all count. Plan about 30% over
clip arithmetic. Use the maintained provider specifications for current estimates.
The ledger keeps a failed attempt reserved until evidence says otherwise.
Source: claude-code · 2026-05 to 2026-10

### Stills plus programmatic motion for stillness beats, Veo for narrative
A no-character stillness beat (landscape, explainer insert) is Nano stills plus
local motion at zero Veo cost; a narrative beat needs Veo for every shot, because
stills with motion read as a slideshow there.
Source: claude-code · 2026-06 to 2026-08

### Veo letters a scale bar even when told not to, and fuses the arrow into it
Four straight-down find takes with "a scale bar with plain alternating black and white segments and no numbers,
then a small plastic north arrow": one bar carried "P 8", one bar and arrow were a single striped pointer, one
placed no arrow, one was clean. A book-ended look-down take briefly doubled the bar while the hand placed it.
Three deterministic letter-removal rules on the moving bar failed (a shadowed white box defeated the white test;
the relaxed rule bleached stripes); the photograph frame was fixed with two hand-placed boxes in seconds.
**Apply:** plan the photograph as the frame that carries the bar, and cut the live reveal before the bar if it is
lettered; a one-frame box fill beats a per-frame patch.
Source: claude-code · October · 2026-10-08

### A transport error on poll is not a failed take
Two of seventeen polls ended with `fetch failed` after the operation had completed; re-polling the same operation
downloaded the take. Nothing was resubmitted.
Source: claude-code · October · 2026-10-08

### Stage the contact geometry before a pie-in-face gag
In House Special, a prompt-only upright pie instruction produced a horizontal tin below the face and an upward cream burst. A new starting frame placed the tin vertically at nose height with a visible approach gap; the replacement carried it into the face and withdrew it while leaving cream behind. The angle and prompt also changed, so this is an observed production correction, not an isolated model comparison.
**Apply:** inspect the actual contact geometry densely. Preserve the failed take, make the approach explicit in the starting frame, and trim later identity drift independently of whether the gag works.
Source: Codex · House Special · 2026-10-17

### Block the eyeline in the anchor's geometry, not in the prompt
Three courtyard takes of a man "looking up toward the balcony" had him looking anywhere but at her, because the
anchors put the balcony behind him: with his face to camera he could only face away from it. Re-blocked with the
camera at his side, low, the balcony in the upper corner he faces and her at the rail, and again from her point of
view looking down over the balustrade, every take held the gaze (and she was in his frame). The same wide also grew
spectacle glints on his small face from about two seconds in (two eye highlights at that scale read as glasses).
**Apply:** if a character must look at something, put it in the frame on the side they face; keep a wide's use short
when the face is small.
Source: claude-code · Balcony · 2026-10-19

### "Beautifully" invites singing
A line asked for "warmly and beautifully" came back sung (flat sustained harmonic bands on a spectrogram) and lost its
second clause after a colon. The retake asked for "her ordinary speaking voice, warm and clear, not singing and not
chanting, every word spoken plainly to the end of the sentence", with the line rewritten as one sentence, and came back
spoken and complete (gliding harmonics; Whisper verbatim).
Source: claude-code · Balcony · 2026-10-19

### Veo puts a prop back where it belongs
"He holds the earbud in his fingers, then lets his hand drop out of frame" became the hand rising to the ear and the
earbud going back in, then the look-up and smile with it in place. The retake used an anchor with no earbud anywhere
(chained off the first one: "change only this: the hand and the earbud are gone, the ear is bare") and nothing to do
but look up and smile; the earbud-in-fingers moment came from a 44-frame palindrome loop of the first take's clean
head. The close-up of her turning to find him also ended with her turning to the lens with a surprised face (the
eye-contact habit); only the first 2.4 s, the look up and to the side, were usable.
**Apply:** removals land on the cut; after the cut, give the model nothing to restore; expect the lens-look and keep
the clean head.
Source: claude-code · Balcony · 2026-10-19

### A locked-off high angle became a push-in and grew a second balcony
From her point of view over the balustrade, Veo pushed in slowly despite "the camera does not move", and as it did it
invented a lit balustrade along the top edge (about 9% of the height by 7 s) and legs between the balusters at the
bottom. The push itself was a gift (it ends on his face mid-line). A bottom-anchored `zoompan` 1.0 to 1.15 across the
segment plus a soft shade over the bottom sixth hid the band. `crop` cannot do this: its w/h expressions are evaluated
once, so a per-frame zoom written with `n` silently renders no zoom; `zoompan` with `in` is the per-frame tool.
Source: claude-code · Balcony · 2026-10-19

### Device dialogue can animate the visible speaker
In Perpetual Check, an earbud whisper and a phone's single-word verdict both came
with early mouth movement on the character in frame. Later ranges held the face
quietly. The edit used those ranges and placed the extracted device voices over
them, while keeping the final on-camera line synchronized to its native picture.
**Apply:** inspect the mouth during device speech. When the take contains a clean
quiet range, separate the sound cue from the picture before buying another take.
Source: Codex · Perpetual Check · 2026-10-22
