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

### Nano gives the character eye contact, and Veo opens the take on it
Six scene-embedded anchors of one woman "facing three-quarters toward the camera, her face
clearly visible" all came back with her looking into the lens, and every Veo take therefore
opened with a look at the camera (0.5 to 1.8 s) before she turned to her task. Across one film
the repeat read as a motif; it was not asked for.
**Apply:** when the character must not see the camera, write where her eyes are ("looking down
at the page", "looking at the two men") in the image prompt and again in the first line of the
Veo prompt; otherwise plan the head of each take as hers.
Source: claude-code · Walla · 2026-10-08

### Say what hangs on the line, item by item
"White sheets" plus a red shirt produced an extra small white vest in one attempt;
naming the exact items ("only the one red shirt and the two white sheets, nothing
else hangs on the line") removed it. The plate also decided the census (two sheets
on her line instead of the three asked for) and the later anchors followed the plate.
**Apply:** count on the plate before writing the medium shots, and enumerate the
line's contents in every prompt.
Source: claude-code · Washing Day · 2026-10-03

### References over 8 MiB are refused; batches want a pause between them
The bounded image route refuses a reference file larger than 8 MiB (a 2K PNG plate can be 8.5 MiB); a JPEG copy at
quality 95 (about 2.5 MiB) is accepted and held the plate's content. A batch launched the moment a previous batch
finished got HTTP 429 on its first request (no charge); twelve seconds between batches avoided it.
**Apply:** keep a `<id>-ref.jpg` beside any plate over 8 MiB and point later requests at it; sleep 12 s between batches.
Source: claude-code · October · 2026-10-07

### Chained edits remove well and add by restaging
"Use the reference as the exact base; change only this: the fifth bag is gone" returned the same frame with clean
tabletop where the bag was (pixel-identical elsewhere, drift PASS). "Change only this: a fifth bag lies at the end"
restaged the whole row (finds re-drawn, bags moved). A "camera lies on the floor looking up" prompt put a literal
DSLR on the floor. Dusk wides came back as overcast daylight twice; a programmatic grade applied to both frames of
the pair passed drift and read as dusk.
**Apply:** generate the fuller state first and chain the removal to get the first frame; crop or compose around
literalisms; grade for the hour locally when the generator ignores it.
Source: claude-code · October · 2026-10-07

### A courtyard plate, two in-scene character mediums and three references hold a whole balcony scene
One 9:16 plate (no people), then a medium of each character generated in the set with the plate as the
only reference, then every later anchor from plate plus one or both character mediums (three references):
the wide, a new bored pose, a close-up, a two-shot and the empty return frame all held wardrobe, hair,
earbud side and set geometry, and Veo accepted all six as first frames at the first attempt. The one
liberty: a balcony medium put a stone parapet in front of the real balustrade; a six-second shot did not
expose it.
**Apply:** plate first, character mediums second, everything else third; keep the plate as a JPEG under
8 MiB for the reference slot and spend the two remaining slots on the people in the shot.
Source: claude-code · Balcony · 2026-10-19

### A balcony close-up wants the rail in front; eyes off-lens needs a named target
"Standing at the balustrade, looking toward the right side of the frame, not at the camera" returned a man standing in
front of the balustrade (nothing under him) looking into the lens. "The camera is outside the balcony, level with it;
the broad stone top of the balustrade crosses the lower part of the frame in front of him, his hands resting on it;
his head turned to look at someone standing just out of frame beside him; his eyes are on her, never at the lens" came
back right at the first try. A chained edit on a close-up ("use the reference as the exact base; change only this:
the hand and the earbud are gone, the ear is bare, his chin lifted a little toward the balcony") held the framing and
made a clean first frame for a retake.
Source: claude-code · Balcony · 2026-10-19

### Multiple references can become a split composition
One Perpetual Check reaction anchor supplied with two references returned two
panels rather than one scene. A replacement used one character reference and
explicitly described one over-the-shoulder composition; it produced a single
usable frame. This is one production correction, not a controlled comparison.
**Apply:** inspect the whole composition before motion. Simplify the reference
set when the model treats the references as panels.
Source: Codex · Perpetual Check · 2026-10-22

### Twelve seconds inside a batch is not always enough
A four-request batch at 12 s spacing completed, but the third request of the next three-request batch (launched 12 s after a reference copy was made) got HTTP 429 with no charge; re-requested under a new ID at 20 s spacing it went through. Mirroring an anchor locally (PIL `ImageOps.mirror`) is a free fix when a point-of-view face comes back lit from the wrong side; keep the original with its asset record and point the shot at the mirrored copy.
Source: claude-code · Coming Attractions · 2026-10-25
