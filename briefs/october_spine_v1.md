# OCTOBER — production spine v1

a][ productions · monthly etymology series · 2026-10-07
Handoff target: Claude Code (NBP → Veo → ffmpeg). Written to survive without the director present.

**Published:** https://youtube.com/shorts/RS4rwMg_xlk (2026-10-08, v5 4K master, 51.5 s). Description: two Festus passages on *mundus* (Cato via Festus, *De verborum significatu*) with translations, combined with the production credits.

**Status (2026-10-07):** pulled into the repository the day it was written. Director notes received the same day: (1) runtime cut to **45–60 s** (the spine below is 85 s); (2) the excavation is specifically a **pit**, visually darker than the scene around it, oozing with what is essentially filth: a living swamp in the middle of a normal scene, and the establishing shots must show it. The Claude Code adaptation (beat sheet at ~55 s, swamp-pit visual spec, shot and anchor plan, budget, decision queue) lives in the workspace plan `data/workspace/october/plan.md`; a dated section is added to this brief per draft. The spine text below is unchanged.

---

## 1. Concept

An excavation. A small crew digs a trench at a forest edge over several days, compressed into one piece by the light going from afternoon to night. Each layer yields a war: a spent cartridge case near the surface, then a lead ball, then an iron arrowhead, then a bronze spearhead, each one older, each one handled as evidence — gloved, scale bar, photographed, bagged. Under the oldest layer is a cut stone slab, blank. They lift it properly, tripod and straps. Beneath it is clear noon sky while the site is at dusk. Nobody climbs through, nobody drops anything in, nobody touches it. The lead sets the scale bar and north arrow at the edge of the hole and photographs the sky as a feature. At night the site sits under its tarp with one corner lit blue from below, and on the finds table a fifth bag, empty and sealed, lies at the end of the row.

Nothing is stated. The argument is the procedure: wars are strata, handled with gloves; under all of them is one unspoiled thing; the method records it and leaves it open. The viewer assembles three facts alone — the finds get older as the trench gets deeper; the stone comes off and does not go back; the sky is never touched.

Source: October 5, mundus patet — the day the Romans lifted the stone off a vaulted pit called by the same word as the sky, and nothing could be fought, levied, launched or married while it stood open. The piece draws on that thematically and never names it on screen.

---

## 2. Format

- Canvas 1080×1920 (9:16), 24 fps, H.264 (high, yuv420p) + AAC 48 kHz stereo.
- Runtime 85.0 s (2040 frames). Not built to loop; it ends.
- On-screen text: none until the end card. No labels, dates, or captions anywhere in the body. Finds tags are turned face down (§5, §8).
- Veo generations in 9:16 if Flow offers it for the model in use; otherwise 16:9 framed for a center 9:16 crop, with the action held in the middle third.

---

## 3. Beat sheet

| # | Time (s) | Frames | Content | Source | Light |
|---|---|---|---|---|---|
| A1 | 0.0–8.0 | 0–191 | site wide; crew troweling in trench | V1 | late afternoon |
| B1 | 8.0–15.0 | 192–359 | find unit: brass cartridge case | V2 → F1 → V9 | late afternoon |
| B2 | 15.0–22.0 | 360–527 | find unit: lead ball | V3 → F2 → V9 | lower sun |
| B3 | 22.0–29.0 | 528–695 | find unit: iron arrowhead | V4 → F3 → V9 | dusk |
| B4 | 29.0–36.0 | 696–863 | find unit: bronze spearhead | V5 → F4 → V9 | dusk |
| C1 | 36.0–39.0 | 864–935 | trowel rings on stone | V7 | dusk |
| C2 | 39.0–45.0 | 936–1079 | slab cleared and exposed | V8 | dusk |
| C3 | 45.0–45.5 | 1080–1091 | still: the slab photographed | F0 | — |
| C4 | 45.5–52.0 | 1092–1247 | tripod lift; blue light under the slab | V10 | blue hour |
| D1 | 52.0–56.0 | 1248–1343 | three faces lit from below | V11 | blue hour |
| D2 | 56.0–61.0 | 1344–1463 | look-down: the hole, clouds moving | V12 composite on F5 rim | — |
| D3 | 61.0–63.5 | 1464–1523 | scale bar and north arrow placed at the hole's edge | V13 (or V9-style composite) | blue hour |
| D4 | 63.5–64.0 | 1524–1535 | still: the sky photographed as a feature | F5 | — |
| D5 | 64.0–68.0 | 1536–1631 | reverse: the hatch from the sky side, tiny, a face in it | V14 composite on V12 | — |
| D6 | 68.0–71.0 | 1632–1703 | faces again, holding; breeze lifting hair | V11 (later portion) | blue hour |
| E1 | 71.0–76.0 | 1704–1823 | night wide; tarp corner lit from beneath | V16 | night |
| E2 | 76.0–81.0 | 1824–1943 | finds table; fifth bag placed, empty | V17 | work light |
| E3 | 81.0–85.0 | 1944–2039 | end card | Pillow | — |

Find unit internal timing (7.0 s each): reveal + scale bar placed 4.0 s → 2 black frames → still 12 frames → 2 black frames → bagging 2.5 s. Identical structure four times; the repetition is the point. Keep the unit timing in one table in the script.

Stills (F0–F5) are cut in hard with 2 black frames either side and a shutter click. No flash frame, no zoom, no border.

Tolerances: if a reveal clip needs more than 4.0 s to read, extend that unit to 8.0 s and shift everything after; D-section timing may flex ±1.0 s per beat to let the breeze shot breathe. Runtime is then recomputed.

---

## 4. The site and crew — visual spec

### Site
Square trench ~2 m on a side, straight vertical walls, string lines along the edges, cut into a meadow at the edge of a deciduous forest. Folding table under a small white canopy beside it; on the table: clear plastic finds bags, a clipboard, a sieve, a battery work light (night). Buckets. Documentary field-archaeology look: muted colors, overcast-bright, nothing cinematic. If NBP returns golden hour or bokeh, regenerate.

### Strata (soil color per layer; this is how depth reads)
- B1: dark brown topsoil.
- B2: mid brown.
- B3: orange-brown clay.
- B4: pale grey clay.
- C: the slab sits in the grey clay.

### Crew — three, described identically in every prompt
- **W** — an older woman with grey hair tied back, in a dark field jacket. The lead. She lifts, she places the bar at the hole, she looks in from the reverse.
- **M** — a bearded man in an olive cap.
- **Y** — a young woman with a braid.
All in muted field clothes, knee pads, blue nitrile gloves. Gloves on in every B/C/D shot; the hand is always gloved.

### The slab
Flat, square, cut, ~70 cm on a side, plain grey, smooth, worn at one edge, no markings. The only made thing in the trench and it says nothing.

### The hole
Square, the slab's footprint, grey clay rim. Through it: clear blue sky, a few small white cumulus drifting slowly. Noon light. The site around it is blue hour or night. Nothing from above ever appears in the blue: no dust, no drip, no hand, no tool, no face except in the reverse shot, where the face is on the pit side looking in.

### Tools seen
WHS-style 4-inch pointing trowel, soft brush, black-and-white photographic scale bar (10 cm segments), small plastic north arrow, clear zip finds bags, paper tags (face down), metal tripod with hand winch and two flat straps.

---

## 5. Footage plan

Nano Banana Pro plates first (site, crew sheet, slab, hole, stills), then Veo motion passes with first/last-frame bookends, then assembly.

### Global prompt rules
- Clean physical description, no poetic language.
- Every Veo prompt ends with: `No music, no speech. No on-screen text, no captions, no watermark.`
- Every prompt carries an audio line.
- Fixed shots say `Camera is fixed, no camera movement.` Nothing else about the camera.
- Never use: director, film, shoot, bullet, rifle, weapon, gun, blade, flash, grid, hatch, portal, cosmos. The archaeological words (cartridge case, lead ball, arrowhead, spearhead, finds, trench, trowel, scale bar) are the vocabulary.
- Crew descriptors are reused verbatim (§4). Veo must never see the word "archaeologist" as a costume cue — the gloves, trowels and trench do that.
- Veo will try to render text on tags, clipboards and the scale bar. Tags are specified face down; the clipboard is specified blank; if text appears anywhere, regenerate or crop.

### NBP plates
- **P1 — site wide.** Late afternoon, forest edge, the trench with string lines, canopy and table, three crew kneeling in it. Overcast-bright, muted, documentary.
- **P2 — crew sheet.** W, M and Y as described, three-quarter and profile, flat light. Used to derive every first frame that shows a face.
- **P3 — slab exposed.** Straight down: the grey slab fully cleared in pale grey clay, trowel and brush at the edge. Dusk.
- **P4 — slab lifted.** Eye level at trench edge: tripod over the trench, straps taut, the slab raised ~30 cm, blue daylight shining up through the gap onto its underside and the trench walls. Last frame for V10.
- **P5 — the hole.** Straight down: square opening in grey clay, blue sky with small clouds through it, scale bar and north arrow on the clay at its edge. This is both the F5 still and the rim plate for the D2 composite.
- **P6 — night wide.** The site at night, tarp over the trench weighted with stones, canopy, work light on the table, one tarp corner folded back and blue light shining up out of the trench.
- **F0–F4 — finds photographs.** Straight down, flat even light, each object in situ on its layer's soil with scale bar and north arrow beside it: F0 the slab (no object, just the slab with bar), F1 green-corroded brass cartridge case, F2 small grey lead ball, F3 dark iron arrowhead, F4 green bronze spearhead. Documentary finds photography; nothing styled.

### Veo clips (8 s each, audio on)

**V1 — site establishing** (first frame P1) → A1
> Late afternoon at the edge of a deciduous forest. A square excavation trench about two meters on a side with straight walls and string lines along its edges. Three people in muted field clothes, knee pads and blue nitrile gloves kneel in the trench, scraping the floor with small pointed trowels and tipping loose soil into buckets: an older woman with grey hair tied back in a dark field jacket, a bearded man in an olive cap, a young woman with a braid. A folding table under a small white canopy stands beside the trench. Leaves move slightly in a light breeze. Camera is fixed, no camera movement. Audio: trowels scraping soil, birdsong, light wind in leaves. No music, no speech. No on-screen text, no captions, no watermark.

**V2 — find 1, brass** → B1
> Close-up, looking down at the floor of an excavation trench in late afternoon light, dark brown topsoil. A blue nitrile-gloved hand scrapes the soil with a small pointed steel trowel and uncovers a spent brass cartridge case, corroded green. The hand sets the trowel aside, places a small black-and-white photographic scale bar on the soil beside the cartridge case, then a small plastic north arrow, and withdraws out of frame. Camera is fixed, looking down, no camera movement. Audio: trowel scraping soil, distant birdsong. No music, no speech. No on-screen text, no captions, no watermark.

**V3 — find 2, lead ball** → B2
Same prompt with: `lower, warmer late afternoon light, mid brown soil` and `uncovers a small grey lead ball`.

**V4 — find 3, iron arrowhead** → B3
Same prompt with: `dusk light, orange-brown clay soil` and `uncovers a dark corroded iron arrowhead`.

**V5 — find 4, bronze spearhead** → B4
Same prompt with: `dusk light, pale grey clay soil` and `uncovers a green-corroded bronze spearhead`.

Selection window for V2–V5: 4.0 s that includes the uncovering and the bar being placed; the hand must be out of frame on the last frame so the cut to the still is clean.

**V9 — bagging, generic** → used in B1–B4
> Close-up at the edge of an excavation trench. A blue nitrile-gloved hand drops a small dark object into a clear plastic bag held open by another blue nitrile-gloved hand; the bag is pressed closed. Camera is fixed, no camera movement. Audio: crinkle of plastic, faint birdsong. No music, no speech. No on-screen text, no captions, no watermark.

One generation, 2.5 s window, reused four times unchanged. The object is deliberately unreadable at this size; the procedure is what repeats. Grade the four uses to match each unit's light.

**V7 — the ring** (first frame: grey clay floor) → C1
> Close-up, looking down at the floor of an excavation trench at dusk, pale grey clay soil. A blue nitrile-gloved hand scrapes with a small pointed steel trowel. The trowel strikes something hard under the soil and stops. The hand pauses, then scrapes again in the same place and exposes a small patch of flat, smooth grey stone. Camera is fixed, looking down, no camera movement. Audio: trowel scraping soil, then a sharp ring when the steel strikes stone. No music, no speech. No on-screen text, no captions, no watermark.

Veo's ring will be wrong; it is replaced (§6). The picture beat is the stop.

**V8 — clearing the slab** (first frame: patch exposed; last frame P3) → C2
> Looking down at the floor of an excavation trench at dusk. Two pairs of blue nitrile-gloved hands brush and scrape pale grey clay soil away from a flat, square, cut stone slab about seventy centimeters on a side, until its whole smooth surface and worn edges are exposed. The slab is plain grey with no markings. Camera is fixed, looking down, no camera movement. Audio: brushing, scraping, quiet wind. No music, no speech. No on-screen text, no captions, no watermark.

**V10 — the lift** (first frame: tripod over slab; last frame P4) → C4
> An excavation trench at dusk, seen from eye level at the trench edge. A metal tripod with a hand winch stands over the trench, and two flat straps run under a flat square grey stone slab set in the trench floor. An older woman with grey hair tied back in a dark field jacket turns the winch slowly and the slab rises straight up a few centimeters at a time. As it lifts, bright blue daylight shines upward through the gap beneath it and lights the underside of the slab and the trench walls. A bearded man in an olive cap and a young woman with a braid watch without moving. Camera is fixed, no camera movement. Audio: winch clicking, strap creak, wind. No music, no speech. No on-screen text, no captions, no watermark.

If Veo turns the daylight into a lamp or a glow effect, generate the lift without the light and add the light in compositing from P4's underside.

**V11 — faces lit from below** (first frame derived from P2) → D1, D6
> Close-up at dusk of three people kneeling at the edge of a square opening in the floor of an excavation trench, looking down into it: an older woman with grey hair tied back in a dark field jacket, a bearded man in an olive cap, a young woman with a braid. Their faces are lit from below by bright blue daylight coming up through the opening. Around them the trench is in dusk shadow. A light breeze from below stirs their hair upward. They do not speak and do not move except to breathe. Camera is fixed, no camera movement. Audio: a soft steady rush of air, distant birds. No music, no speech. No on-screen text, no captions, no watermark.

Take rule: mouths closed throughout, no one reaches toward the opening. If someone reaches, choose another window; the hand that does not enter is the piece.

**V12 — sky plate** → D2 (behind the P5 rim), D5 (behind the reverse)
> Clear blue sky with a few small white cumulus clouds drifting slowly from left to right. Nothing else in frame. Camera is fixed, no camera movement. Audio: a soft steady rush of air. No music, no speech. No on-screen text, no captions, no watermark.

Loop or reverse-extend as needed. The clouds must move; a still sky reads as a reflection.

**V13 — scale bar at the hole** (first frame: P5 without bar; last frame P5) → D3
> Looking straight down at the floor of an excavation trench at dusk. In the center of the floor is a square opening about seventy centimeters on a side; through it, bright blue daylight sky with small white clouds. A blue nitrile-gloved hand enters from the right and sets a small black-and-white photographic scale bar on the grey clay at the edge of the opening, then a small plastic north arrow beside it, and withdraws out of frame. Camera is fixed, looking down, no camera movement. Audio: soft tap of plastic on soil, a steady rush of air. No music, no speech. No on-screen text, no captions, no watermark.

Fallback if the sky-through-the-floor confuses Veo: generate the hand placing the bar on plain grey clay (no opening) and composite it over the P5 rim plate with the V12 sky masked into the square. Composite rather than merge.

**V14 — worm's-eye for the reverse** → D5 (as a composite element)
> Camera lies on the floor of an excavation trench at dusk, looking straight up. The trench walls of brown soil rise on all four sides to a square of dim evening sky. An older woman with grey hair tied back in a dark field jacket leans over the edge of the trench and looks down at the camera, holding still. Camera is fixed, no camera movement. Audio: wind, distant birds. No music, no speech. No on-screen text, no captions, no watermark.

Assembly makes this the reverse shot: mask V14 to its square, scale it to about 6% of frame height, place it off-center on the V12 sky plate, slight softening on the square's edge. From the sky side the pit is a tiny dark square with a face in it. Do not make it bigger to be legible; the scale is the shot.

**V16 — night wide** (first frame P6) → E1
> Night at the edge of a deciduous forest. A small archaeological excavation: a square trench covered with a blue tarp weighted with stones, a folding table under a small white canopy beside it, a single battery work light on the table. One corner of the tarp is folded back and bright blue daylight shines upward out of the trench there, lighting the underside of the canopy. Nobody in frame. Camera is fixed, no camera movement. Audio: crickets, light wind, a faint steady rush of air. No music, no speech. No on-screen text, no captions, no watermark.

**V17 — the fifth bag** → E2
> Night, close on a folding table under a small white canopy, lit by a battery work light. Four small clear plastic bags lie in a row, each holding one small object: a green-corroded brass cartridge case, a small grey lead ball, a dark iron arrowhead, a green bronze spearhead. Paper tags on the bags lie face down. A blue nitrile-gloved hand sets a fifth clear plastic bag, empty and sealed, at the end of the row and withdraws out of frame. Camera is fixed, looking down at a slight angle, no camera movement. Audio: crinkle of plastic, crickets. No music, no speech. No on-screen text, no captions, no watermark.

Order on the table is excavation order, left to right, newest to oldest, then the empty bag. If Veo scrambles the order, regenerate; if a tag shows text, regenerate.

Generation count: 13 Veo clips (V1–V5, V7–V14, V16–V17; V6 and V15 do not exist), plus P1–P6 and F0–F5 from NBP. If the credit budget tightens, V13 becomes the composite fallback (saves one) and V14 can be cropped from a V11 take where W is alone in frame (saves one). Do not cut a find unit; four wars is the escalation.

---

## 6. Audio design

- **Ambience bed.** One continuous bed under the whole piece, built from the Veo ambiences: V1's afternoon birds, V11's air, V16's crickets, with slow crossfades so the day's progression is audible without cuts. Normalize the bed to −26 LUFS. This is the one piece where the cuts are hidden in sound rather than exposed; the site is continuous and the days are not.
- **Foley per beat** on top of the bed: trowel scrape, plastic crinkle, winch click, strap creak, taken from each clip's own Veo audio where clean, replaced from library where not.
- **The ring (C1).** Replace Veo's. One struck-stone resonance, steel on dense stone: a short bright transient with a tonal tail of ~1.2 s, peak −10 dBFS. Library hit preferred; synthesize as a fallback (two or three decaying partials around 2–4 kHz over a short noise burst). It is the only hard, clean sound in the first 36 s and it should feel like it.
- **Shutter click.** One dry mirrorless shutter sample at frame 0 of every still (F0–F5), six total, −16 dBFS. Identical each time.
- **The air.** From the first frame of C4 (the gap opening) a soft steady rush of air rises under everything and never leaves, through the night wide, the table, and the end card. It cuts with the picture at frame 2039. Keep it low, −30 LUFS; it should be noticed only when it stops.
- **No music.** Suno is not used. ElevenLabs is not used. No speech anywhere.
- **Master.** Set levels per the above, cap at −1 dBTP, no program-wide loudness normalization.

---

## 7. End card (E3)

Pillow, 4.0 s, black.

- Line 1: `OCTOBER` — the series face, size and placement matching the previous installments (see §11).
- Line 2, proposed: the Latin word for the pit, with its three senses (world, sky, pit), as a dictionary line.

Line 2 does not go on screen until it is verified against Lewis & Short on Perseus and the wording is locked (§11). If it cannot be verified in time, the card is line 1 only. No other text. The air continues under the card and cuts on the last frame.

---

## 8. Assembly (Claude Code)

1. **Plates (NBP).** P1–P6, F0–F5. Lock the crew look from P2 before any Veo first frame is derived.
2. **Footage prep (ffmpeg).** For each Veo clip: trim to window → conform to 1080×1920 (crop if generated 16:9) → grade for its light slot (§3, last column). Four uses of V9 graded separately.
3. **Composites.** D2: P5 as rim plate, blue square masked, V12 behind it. D5: V14 masked to its square, scaled to ~6% frame height, placed on V12, edge softened. D3 fallback as described in §5. Composite, never merge.
4. **Stills.** F0–F5 each held 12 frames with 2 black frames before and after; shutter click aligned to frame 0 of the still.
5. **End card.** Pillow render; line 2 only if verified.
6. **Audio.** Bed → foley → ring → shutters → air, per §6.
7. **Concat** per the beat table. Encode H.264 high / CRF 16 / yuv420p / 24 fps, AAC 48 kHz 192 kbps.
8. Keep the beat durations and the find-unit internal timing in one table in the script so a tolerance shift propagates.

---

## 9. QA — on a phone

- Strata: soil color steps darker-to-paler across B1–B4 in the correct order; the four finds are visibly different objects and visibly older left to right on the table.
- No legible text anywhere in the body: tags, clipboard, scale bar, bags. Frame-step V17.
- Gloves on in every hand shot. Hands out of frame on the last frame of every reveal.
- The sky: nothing from above ever appears in the blue — frame-step D2, D3, D4. Clouds move in D2 and D5.
- D1/D6: mouths closed, nobody reaches.
- D5: the square is small; a viewer should find it, not be shown it.
- C4: the slab rises straight; it does not tilt or swing.
- E2: five bags, the fifth empty and sealed, correct order.
- The air is audible under the end card and stops on the last frame.
- Light continuity: afternoon → dusk → blue hour → night, never reversing between adjacent beats.

---

## 10. Decisions and reasoning

- **Finds, not weapons in use.** The wars are in the dirt, handled with gloves as evidence. Nothing is wielded; the piece never has to reframe around moderation, and the crew's neutrality is the register.
- **Four units, identical structure.** The viewer learns the procedure by its third repetition so that its fifth application — to the sky — lands as method, not as a joke. Same bagging clip four times for the same reason.
- **Newest first.** The dig goes down through time, so the escalation runs backward: our war is the shallowest.
- **Dusk above, noon below.** A reflection cannot be a different hour. The time mismatch is the cheapest and most complete proof that the hole is open, and it is the source idea exactly: the sky's twin on its own clock.
- **Nobody goes through, nothing goes in.** The piece is about looking. The hand that stops short keeps the sky unspoiled, and the stone staying off is the only "forever" in it.
- **The reverse shot is tiny.** From the sky side the human world is a flaw in something very large; making the square readable would make it a doorway.
- **The empty fifth bag.** The procedure completes. A catalogued sky with nothing in the bag is the method's honest result, and it is the last thing the viewer sees before the card.
- **One continuous ambience bed.** Unlike the hard-cut pieces, the site is one place across several days; the sound carries the days so the picture doesn't have to.
- **No music, no speech, no text in the body.** The only voice is the method's.
- **Documentary texture.** Overcast, muted, flat. If the dig looks like a film set, the strata stop being evidence.
- **Prior art.** Turrell's Skyspaces (a square aperture to sky, viewers below looking up; this piece inverts it into the floor), Kapoor's *Descent into Limbo* (a hole in a floor that reads as something else), and the field-archaeology register of *The Dig* (2021). Acknowledge the lineage in the description if it comes up; the divergence is the procedure and the direction of the look.

---

## 11. Open items

1. End card: match the series' established face, size, placement and duration from the previous installments before rendering; line 2 wording verified on Perseus (Lewis & Short, *mundus*) or dropped.
2. Runtime: 85 s is longer than some prior installments; confirm it sits inside the series' norm or tighten B-units to 6.5 s (saves 2 s) before trimming anything else.
3. V13 — direct generation vs. composite fallback, decided on what Veo returns.
4. The ring — library hit vs. synthesized, decided by ear.
5. Cartridge case — if Veo balks at the object, substitute a corroded steel helmet fragment for find 1 and update F1 and V17 to match.
6. 9:16 availability in Flow for the model in use.

Everything else is decided.


---

## 12. Claude Code draft (v1 built 2026-10-07/08; v4 and v5 revisions 2026-10-08 after the director's notes)

Workspace `data/workspace/october/` (ignored); review package `final/v1/` (`film.mp4`, `review.html`, `film_debug.mp4`).
v5: 51.5 s, 1080×1920, 24 fps, −21 LUFS, peak −1.9 dBFS; 4K master (2160×3840, x2 Real-ESRGAN) built 2026-10-08. Eighteen Veo 3.1 takes, all used; forty-six
Nano Banana Pro references; local sound (ElevenLabs effects, synthesised ring, shutter and air); no music, no speech.
About $30.30 of the $50 authorization.

What changed from this spine, by the director's decisions: the excavation is a large modern stepped dig the size
of half a field (people shoulder-deep, ladders, wheelbarrows, a sieve, the canopy at the rim) with dark wet earth,
black puddles and one black oily pool in the sondage at the deepest point, where the slab sits; the register is
cinematic (low golden sun, dust, 85 mm close-ups of the three crew, a slow drift on the high wide); find 2 is a
corroded Roman gladius laid in a foam tray; the end table carries recovered rifles of several eras along its back;
the series card "October 2026" opens the piece and there is no end card. Four finds, the ring, the clearing, the
lift, the faces lit from below, the opening with the sky, the bar placed at its edge, the sky photographed, the
night and the fifth bag are all kept. On the director's notes the reverse became a 1.5 s coda after the film
fades to black, with the figure at the rim just barely moving (a worm's-eye take composited into the square),
and the bar placement cuts to the photograph while the hand is still lowering the bar.
