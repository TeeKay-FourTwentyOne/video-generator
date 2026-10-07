# Image anchor field notes (Nano Banana Pro)

Route: `npm run film -- image` (bounded, ledger-tracked, three references) or
`tools/nano-banana.cjs` for the full flag set. Pre-generation checks:
`tools/frame-qa.py`, `tools/anchor-drift.py`; skills `book-end`, `nano-banana`.

### Name what to preserve; describe only what changes
Prose overrides a plate and a character lock unless the canonical elements are
named ("plain slat wall, no tools hanging"); unnamed surfaces grow props.
References go before the prompt text.
Source: claude-code · 2026-05 to 2026-07

### Chaining locks pose; regenerate for a new pose
With the prior frame as reference the model preserves the pose pathologically:
right for adding or removing a small object or changing an expression, wrong for
a new stance or body angle, even with an explicit rotation prompt.
**Apply:** chain for detail edits; regenerate fresh from plate plus character refs
for a new pose and describe it from scratch.
Source: claude-code · 2026-04 to 2026-07

### Nano re-stages the whole canvas; it cannot do surgery or shrink what it drew
Three of three "surgical edit" trials drifted face and props; a chained request to
replace an oversized socket with a small one kept it full size.
**Apply:** make masked edits programmatically with a pixel-diff proof. A plate that
never appears on screen only needs a clone-stamp patch, because downstream anchors
re-render from it.
Source: claude-code · several productions · 2026-08; Borrowed Light · 2026-10-03

### Rapid batches get HTTP 429
Back-to-back requests are rate limited. The maintained image route refuses to
retry on its own; a 429 is evidence the request was never accepted.
**Apply:** space requests about ten seconds apart; re-request under a new ID.
Source: claude-code · 2026-08; Borrowed Light · 2026-10-03

### Film-stock and vintage words bake in text
"Photograph", "Kodak" and similar fabricate film-stock edge text; "silent film"
and vintage styling bake in title cards.
**Apply:** use lighting and lens language; forbid text explicitly.
Source: claude-code · 2026-06 to 2026-08

### Show the face in the ref if the face appears in shot
Profile or back references only when the face never turns to camera.
Source: claude-code · 2026-07

### Book-end frame hygiene
Veo interpolates pixels: any prop whose position differs between the two anchors
slides, even impossibly; near-identical endpoints give a near-static clip; for a
"crosses frame" move, frame A belongs at the entry edge (partway across reads as
an exit). Keep identical objects spaced, not clustered, or their count changes.
**Apply:** run `frame-qa` on each anchor against its refs and `anchor-drift` on
the pair before spending a Veo second.
Source: claude-code · 2026-04 to 2026-08

### Composite sprites give pixel-identical subjects across anchors
Keying a magenta hero sprite onto plates keeps the subject pixel-identical across
anchors; Nano re-stages, programmatic compositing does not.
Source: claude-code · 2026-08

### Lock scale and facing across framings
Pin the subject's scale and facing against a fixed anchor (a planter, a doorway),
and state sizes in the prompt ("the machine is as tall as the planter is wide"),
or wide-to-close cuts pop and flip.
Source: claude-code · 2026-08; Borrowed Light · 2026-10-03

### Two references hold a design across scales
A plate plus a character sheet, with the prompt restating the full design each
time, held a robot's look from wide to macro, including which side panel carries
its scratch.
Source: claude-code · Borrowed Light · 2026-10-03

### Living-painting accretion
Chain add-only off the previous frame and hold the light. A light change is a
global redraw, so migrate lighting programmatically.
Source: claude-code · The Other Window, The Surveyor's Table · 2026-06

### Sparse reads as authored
Negative space plus one or two symbols; clutter reads AI-generated.
Source: claude-code · 2026-07

### Compose around impossible bodies
Conceal with a cloak, a prop or an angle; never ask a model to render absence.
Source: claude-code · 2026-08

### A "palette only" reference gets pasted in as content
Asking for a new rooftop view "with the same materials and palette as the reference"
while passing the courtyard plate returned a collage: the plate's balcony and line
were pasted across the top third above the sea. The same prompt with no reference
gave the intended view.
**Apply:** for a genuinely new framing, describe the palette in words and pass no
image; references are for things that must reappear.
Source: claude-code · Washing Day · 2026-10-03

### Scene-embedded character references pass and double as the first anchor
A medium shot of an elderly woman pinning laundry, from across the shaft with the
railing, line and shutters in frame, was accepted as a Veo first frame on every
attempt and held her face, headscarf and apron through the take; a fresh regeneration
of the same framing with a new pose (looking up) stayed consistent enough for a
hard cut back to the balcony (anchor-drift across-cut PASS).
**Apply:** make the character reference the first balcony anchor itself; regenerate
fresh from plate plus character for the later pose instead of chaining.
Source: claude-code · Washing Day · 2026-10-03

### Say what hangs on the line, item by item
"White sheets" plus a red shirt produced an extra small white vest in one attempt;
naming the exact items ("only the one red shirt and the two white sheets, nothing
else hangs on the line") removed it. The plate also decided the census (two sheets
on her line instead of the three asked for) and the later anchors followed the plate.
**Apply:** count on the plate before writing the medium shots, and enumerate the
line's contents in every prompt.
Source: claude-code · Washing Day · 2026-10-03

