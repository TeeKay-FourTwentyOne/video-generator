# Washing Day

Second test film for the tooling pass, October 2026. Two independent builds from
this brief, Claude Code first and then Codex, each assessing and improving the
production tools as it goes. 1080 x 1920 (9:16), 24 fps, 30 to 45 seconds.
Total authorized provider spend per build: $20, including reference images,
video, QA and incidental storage. Existing providers only. Native review export
first; 4K and publication are separate decisions.

## The film

A deep, narrow courtyard in a sun-struck hill town: five floors of balconies
around a shaft of hard blue sky, laundry lines crossing it at several heights.
On the top balcony an old woman pins out white sheets as she has for sixty
years. A gust takes one corner of a sheet; the pin gives; the sheet tears free
and tumbles upward through the lines and out of the shaft into the open sky.
She watches it go. Then, instead of chasing it, she unpins the next sheet and
lets it rise, and the next. The last shot is from above the rooftops: sheets
lifting out of one courtyard, white against the blue, the sea beyond.

The film does not explain her. Nothing is lost; something is released. The
first escape is an accident, the rest are a decision, and the cut between the
two beats carries the whole story.

## World and register

- Photoreal, daylight, late morning. Not a miniature. 35 mm feel, locked-off
  framings and slow rises; no handheld shake.
- Palette: ochre and rose plaster, green shutters, black iron balconies, white
  linen, one hard blue square of sky. One small red garment on her line stays
  pinned throughout as the thing that remains.
- Air is the lead performer: cloth bellies, snaps and tumbles; swifts cross the
  sky; dust and light in the shaft.
- No text anywhere: no shop signs, house numbers, posters or labels. No
  patterned or printed linen.

## Continuity

- One courtyard, one woman, one escaping sheet at a time. Her balcony is the
  top floor, screen left when looking up the shaft; all other balconies are
  empty. No other people in any shot.
- The woman: small, in her seventies, grey hair under a plain blue headscarf,
  black dress, flowered apron, strong lined hands, no glasses, no jewellery.
  Her face appears in the medium shots, so the reference frame must show it
  clearly, embedded in the balcony scene, never as a portrait.
- Lines: exactly four, crossing the shaft between the second and fifth floors.
  White sheets and the one red garment only. Count sheets and lines in every
  anchor and every take; Veo multiplies clusters.
- Sky: clear, no clouds, so cuts between shots that see the sky stay seamless.
- A freed sheet never falls back and never carries a pin. Once she unpins a
  sheet, it lifts on its own; she does not throw it.
- The light does not change across the film. The sound moves from courtyard
  routine (pins, a far radio, swifts) to open air (wind, cloth, silence).

## Coverage

Each generated take is 6 or 8 seconds, chosen per shot; the table gives the
intended edit length, not the take. Anchors are nano-generated from one
canonical courtyard plate (looking up the shaft) and one character reference.
Local trims, inserts and the editor's fades replace defective action; do not
reroll blindly. Finish with a short title on black.

| Shot | Edit s | Purpose | Technique |
| --- | ---: | --- | --- |
| S01 | 4 | Vertical wide up the shaft: lines, sheets, the blue square, the woman tiny on the top balcony pinning | First-frame anchor; native audio candidate (pins, radio, swifts) |
| S02 | 5 | Medium on the balcony: she pins a sheet; the wind rises and the sheet bellies | First-frame anchor; her face established; native audio candidate |
| S03 | 4 | Close: the pin strains; one corner tugs free | Book-end: first frame pinned, last frame one corner free (the irreversible beat) |
| S04 | 6 | The sheet tears loose and tumbles upward through the lines, camera rising with it | First-frame anchor; the join to S05 lands inside the tumbling |
| S05 | 6 | Continuous: the sheet clears the shaft into open sky, the courtyard falling away below | Join from S04 (extend-clip, seam-check); silent |
| S06 | 5 | Medium: she watches it go, a beat, then unpins the next sheet and lets it rise | First-frame anchor; book-end optional (sheet pinned to sheet lifting) |
| S07 | 8 | Wide from above the roofs: sheets rising one after another out of the courtyard; the sea beyond | First-frame anchor; cap at four or five sheets in the air |
| T01 | 3 | Title on black: "Washing Day" | Local render |

Total about 41 seconds. If a join will not hold, S04 and S05 become a hard cut
on the sheet clearing the top line; if S07's count drifts, trim to the clean
range or cut it as a single sheet rising past the camera.

## Sound

No speech. Native Veo audio is welcome where foley is the point (S01, S02,
possibly S06), mixed under a local original score; silent takes elsewhere.
The score is sparse and plucked, airy rather than warm: the wind and the cloth
lead, the instrument answers. Near-silence at the moment the pin gives. Measure
loudness and true peak; the agent reports that it has not listened in real time.

## Budget and model choices

| Item | Estimate |
| --- | ---: |
| Seven Veo Quality takes, mostly silent 1080p, two with native audio | $12 to $15 |
| Plate, character reference, seven to nine anchors (about $0.14 each) | $1.60 |
| Claude vision QA (anchor checks, clip-qa, clone-check, seam checks) | $0.50 |
| Infrastructure reserve | $0.30 |
| Retakes and alternates | the remainder |

Reserve everything in one ledger before buying anything. Quality for shots that
carry the woman; model choice serves the shot elsewhere. One planned attempt
per shot; a retake needs a reviewed defect and a changed cause.

## What this build should exercise in the tools

Book-ends with first and last frames (S03), a seamless join (S04 to S05) with
`tools/seam-check.py`, anchor-drift across a hard cut (S02 to S06, same
balcony), native audio mixed with a local score, six-second takes, the editor's
fades and local title, `film poll --wait`, image reconciliation, and the field
notes. Record every friction point, fix what is safe to fix, and leave the rest
as findings in the delivery record.

## Delivery and review contract

Deliver the native review export under `data/workspace/washing-day-<agent>/final/vN/`
with `review.html`, `delivery.json`, a timecode overlay copy, the acceptance
decisions and the budget ledger. Check full decode, dimensions, exact frame
count, source hashes, audio loudness and peaks. Inspect counts (lines, sheets,
people) in every take and examine frames densely around the pin giving, the
join, and the unpinning. Technical checks do not confer artistic approval.
Nothing is upscaled, published or committed without a separate decision.

## Delivery records

Each build appends a dated section here: workspace, export path and length,
model and take choices, edit decisions, spend estimate, residual defects, tool
findings and changes, and what was left for the director to decide.

## Claude Code build (Fable 5.1), 2026-10-03

Workspace `data/workspace/washing-day-claude/`. Native review export `final/v3/film.mp4`
(926 frames, 38.58 s, 1080 x 1920, 24 fps, AAC 48 kHz stereo) with `review.html`,
`delivery.json`, the overlay copy `film_debug.mp4`, hash-bound decisions under `qa/` and the
ledger `budget.json`. v1 and v2 are preserved intermediate cuts (S03 in-point, limiter guard).

Model and take choices: seven Veo 3.1 Quality 1080p takes from nano anchors (a plate looking
up the shaft, a scene-embedded character reference that doubles as the S02 anchor, fresh
anchors for S03, S04, S06, S07; S05 anchored on S04's frame 120); S01 (6 s) and S02 (8 s)
with native audio, the rest silent; S03 was the one retake (the book-end take invented a hand
with a second clothespin, the first-frame-only retake released the sheet). Edit: S01 0-95,
S02 0-103, S03-v2 60-143, S04 0-119, S05 0-155, S06 24-167, S07 0-149, local title 72 frames;
fade-in on S01, fade-out on S07. The S04→S05 join passed `seam-check` at A:119 → B:0
(ratio 1.10, velocity ratio 1.12). Sound: local score and air (`recipes/score.py`) mixed with
the two native tracks by the new `tools/production/mix.mjs`; −16.0 LUFS, LRA 9.2, −2.1 dBTP
measured on the delivered file; not listened to in real time by the agent.

Spend estimate (list-price / saved-usage, not invoice-confirmed): Veo $14.40 (8 attempts),
images $1.25 (9 attempts, 2 rejected), Claude QA $0.46 (20 calls), reserve $0.30:
**$16.41 of $20 committed**. Nothing upscaled, published or committed.

Residual defects: S03's release whips right rather than up; S04's sheet is a twisting ribbon
hovering near the line before S05 carries it out; S07's second sheet emerges without fully
rising in the used range; S02's camera is lower than "across the shaft"; the S01 native track
is nearly silent (local peg clicks added); her line carried two sheets, not three.

Tool findings and changes: `film image` batches with spacing and `--reconcile`;
`film review --overlay`; `tools/production/mix.mjs` with tests; production doc, harness notes
and field notes updated (book-end displacement invites an invented agent; palette-only
references get pasted as content; anchor the continuation at the busy frame; native audio on
distant wides may come back silent). Left for the director: the decision queue in
`data/workspace/washing-day-claude/plan.md` (S03 release direction, S04 length, S07 count,
S02 out-point, score levels, title), plus 4K and publication.


## Codex delivery record — 2026-10-03

Independent native draft at `data/workspace/washing-day-codex/final/v1/`:
`film.mp4`, `review.html`, `delivery.json` and `film_debug.mp4`. The complete cut
is 33.67 seconds, 808 frames, 1080 x 1920, 24 fps. The source brief, plan history,
anchors, original takes, rejected alternates, edit, score stems, acceptance
records and QA evidence remain in that workspace. No Fable/Claude footage or
project assets were opened. The appended written record in this shared brief
was encountered during the initial brief read; that was disclosed separately.

The cut holds on the courtyard routine, makes the first escape a before/after
peg insert, follows one sheet upward, then returns to her look and deliberate
unpinning gesture. It cuts before the generated throw into three sheets already
airborne over the roofs and sea. The additional releases are implied. A sparse
original local plucked score, air and cloth accompany the native S01/S02 audio.
The pin break has a short dip in the bed and one local peg clack. The final title
is three seconds on black with frame-addressed fades.

Both generated S03 release takes invented an extra peg and hand; both complete
S06 releases lifted or threw the sheet and returned it to the line. These ranges
were rejected. Clean states and a pre-throw range support the editorial ellipses.
The silent S04 cloth shot was reversed locally to obtain upward entry and
recession. Its exact decoded frame 156 supplied S05's anchor; the cut uses frame
155 followed by S05 frame zero. The seam is MARGINAL photometrically (ratio 2.189)
and passes motion continuity (velocity ratio 1.149), with a slight boundary
change retained. The finale starts after early cloth materialization artifacts.

Remaining visual compromises: four laundry levels include extra pulley-return
strands; the tiny opening figure has a wrist detail; generated courtyard views
have approximate spatial continuity. The release actions are not shown as clean
continuous mechanics. These are draft caveats, not waived continuity requirements.

Budget committed including the $0.30 infrastructure reserve: $18.610983 of $20.
This comprises $15.60 for nine video takes, $2.093630 for fifteen reference-image
calls and $0.617353 for metered QA. Costs use saved provider usage and configured
rates; they are estimates, not invoices. All costs were reserved before calls;
submitted operations were polled rather than blindly resubmitted.

Full film and timecode-copy decode, dimensions, exact frame counts and source
hash checks passed. Delivery AAC measures -18.0 LUFS, 5.6 LU loudness range and
-2.4 dBTP. The native browser player reports the expected dimensions/duration and
successfully seeks to shot boundaries. No real-time listening occurred; no claim
of audible no-speech verification or artistic approval is made.

Repository improvements: decoded-frame `film join-anchor` with hash provenance;
`anchor-drift --mode=return-shot` with required elapsed-action context; a local
original score recipe; and a loopback review server that supports HTTP byte ranges.
The server resolves the observed generic-server seek failure. Production build and
24 offline tests passed, plus two anchor-context tests and the final editor checks.
See `docs/craft/field-notes/2026-10-03-washing-day-codex.md` for findings. Source
publication, 4K and video publication remain separate decisions.
