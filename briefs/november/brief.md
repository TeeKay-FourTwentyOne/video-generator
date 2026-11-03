# NOVEMBER — production spine v1

[Current production record](README.md).

This document preserves the retained creative and production history. Dated plans and technical observations describe their original sessions; the current record states only supported production facts.

a][ productions · monthly etymology series · 2026-11-02
Handoff target: Claude Code (NBP → Veo → ElevenLabs SFX → ffmpeg). Written to survive without the director present.

**Published:** https://youtube.com/shorts/1X6r40Ld7Hw (recorded 2026-11-02, user-confirmed; v3 4K master, 42.2 s). Description: `description.md` (the Vegetius, Pliny, Theodosian and Hesiod passages with the credits).

**Status (2026-11-02):** pulled into the repository the day it was written. Director notes received the same day: open with the series card ("November 2026", 1.5 s, the October card recipe) and no end card; use the spine as a general guide but focus the first section on the **winter preparation of the ship** as wordless, brief detail shots (the plug, etc.); focus on **the man and the woman**, whose relationship deteriorates quickly after the homecoming (he drinks heavily and misses the sea; she works around him), still wordless; the director leans to **no music** (ambient wind and life), open to a suggestion; runtime about 45 s; reshoots expected on the relationship beats. The Claude Code adaptation (beat sheet at 44.75 s, the agent's additions, image and sound plan, decision queue) lives in the workspace plan `data/workspace/november/plan.md`; a dated section is added to this brief per draft. The spine text below is unchanged.

---

## 1. Concept

A small harbor town on the Roman Mediterranean, the second week of November. The sea is closing for the winter. Before dawn the Pleiades go out over the western water. The last ship comes in under a grey sky and lowers its sail. A crew hauls the hull up the slipway on rollers, packs stones around it, and the sailor works the bilge plug out of the bottom so the winter rain will drain instead of rot the wood. Then a wide shot: the beach lined with hulls, the harbor water empty. At dusk he walks up the hill with the long steering oar on his shoulder; a goose crosses the lane in front of him.

His wife opens the door. They hold each other. The door shuts on the wind. At the household shrine a small bronze goddess stands holding a ship's rudder, and a bronze rattle is shaken once. He hangs the steering oar on pegs over the hearth, in the smoke.

Then the winter. Rain on the harbor. He sits at the small window with a cup, looking down at a sea he can't use. Behind him she works at the loom. Later, darker, he pours again; she carries a water jar and has to step around his legs; he doesn't move. Last image: the oar over the fire, the smoke climbing round its blade. Four months of this. Nothing is said.

Nothing is stated. The sea closing is relief and loss in one gesture; the homecoming is joy and the start of a different weather. The goddess on the shelf holds a rudder all winter while the man's real one blackens over the fire.

Sources the piece draws on, never named in the body:
- **Vegetius, *Epitoma rei militaris* 4.39** — the winter setting of the Pleiades troubles shipping with storms from November; *ex die igitur tertio idus Novembres usque in diem sextum idus Martias maria clauduntur* ("so from the 11th of November until the 10th of March the seas are closed"). **Verified** (Latin Library; monumenta.ch; Müller's Steiner edition reads *Iduum Novembrium … Iduum Martiarum*, same sense).
- **Hesiod, *Works and Days* 618–632** — when the Pleiades plunge into the misty sea: haul the ship up, pack it round with stones, draw the bilge-plug so the rain won't rot it, stow the tackle and the sail, hang the steering oar over the smoke. **Verified** (Evelyn-White, Perseus). Greek, not Roman; it supplies the practice and stays off screen.
- **Isis-Fortuna** — the common Roman household statuette: Isis's crown and dress-knot, Fortuna's cornucopia and ship's rudder; the rudder also marks Isis as patron of navigation. **Verified** (Getty 71.AB.180; Met; Toledo 2006.97, whose label places such figures in household shrines).
- **Calendar of 354, November page** — a linen-clad priest of Isis with a sistrum, pomegranates, and a goose below. The goose is the wink (§3, A7). The page's couplet is **unverified** against a critical edition and is not used on screen.
- **The Isia, Oct 28–Nov 3** — Isis's search for Osiris ending in the finding and the rejoicing. The reunion (B1–B2) is the finding; the winter is what the myth leaves out.

---

## 2. Format

- Canvas 1080×1920 (9:16), 24 fps, H.264 (high, yuv420p) + AAC 48 kHz stereo.
- Runtime 45.0 s (1080 frames). Not built to loop; it ends on the series end card.
- On-screen text: none until the end card.
- Veo generations in 9:16 if Flow offers it for the model in use; otherwise 16:9 framed for a center 9:16 crop, with the action held in the middle third.
- Fixed camera in every shot. The pace comes from holds, not from movement.

---

## 3. Beat sheet

| # | Time (s) | Frames | Content | Source | Light |
|---|---|---|---|---|---|
| A1 | 0.0–3.0 | 0–71 | pre-dawn: the western sea, the Pleiades low over the water, fading as the sky pales | V1 + programmatic stars | pre-dawn |
| A2 | 3.0–7.0 | 72–167 | the last ship rows into the harbor, its square sail coming down | V2 | grey morning |
| A3 | 7.0–11.5 | 168–275 | the crew hauls the hull up the slipway on log rollers | V3 | grey morning |
| A4 | 11.5–13.5 | 276–323 | stones packed against the hull | V4 | overcast |
| A5 | 13.5–17.0 | 324–407 | close: the sailor works the wooden plug out of the hull bottom; water runs out onto the shingle | V5 | overcast |
| A6 | 17.0–20.0 | 408–479 | wide: hulls hauled up along the beach, the harbor water empty | V6 | late afternoon, grey |
| A7 | 20.0–24.0 | 480–575 | dusk: he walks up a steep lane with the steering oar on his shoulder; a goose crosses in front of him; he steps around it | V7 | dusk |
| B1 | 24.0–27.5 | 576–659 | inside: she opens the door, he comes in, they hold each other; the door swings shut behind him | V8 | dusk outside, hearth inside |
| B2 | 27.5–29.0 | 660–695 | the shrine niche: the bronze figurine with her rudder, an oil lamp; her hand shakes the bronze rattle once | V9 | lamp |
| B3 | 29.0–31.0 | 696–743 | he lifts the oar onto pegs above the hearth; smoke rises round the blade | V10 | hearth |
| C1 | 31.0–35.5 | 744–851 | days later, rain: he sits at the small window with a cup, looking down at the harbor; behind him she works at the upright loom | V11 | grey, rain |
| C2 | 35.5–39.0 | 852–935 | later, dimmer: he refills the cup from a jug; she carries a water jar and steps around his outstretched legs; he doesn't move | V12 | dim, rain |
| C3 | 39.0–42.0 | 936–1007 | the oar over the hearth at night, smoke climbing past the blade | V13 (or V10 tail) | night, hearth |
| E | 42.0–45.0 | 1008–1079 | end card | Pillow | — |

Proportions: wintering A1–A7 is 24.0 s, the reunion B1–B3 is 7.0 s, the winter C1–C3 is 11.0 s. The reunion is deliberately the shortest section.

Hard cuts throughout. Time passes through light, not transitions: pre-dawn → grey day → dusk → lamp → rain-grey → night. Light never reverses between adjacent beats within a section.

Tolerances: A3 and A5 may each run to +1.0 s if the action needs it to read; take the time out of A6 and C3 (minimum 2.0 s each) so the runtime holds at 45.0. B1 does not extend; brief is the instruction. Keep the beat table as one structure in the script so any shift propagates.

---

## 4. Look, places, people

### Look
Naturalistic and documentary. Overcast Mediterranean winter light, muted color, soft contrast, real textures (wet shingle, tarred wood, rough wool, plaster). Nothing staged, nothing epic. No golden hour, no lens flare, no bokeh showpieces, no slow motion. If any plate or clip looks like a historical epic, regenerate. The register is a quiet film about weather.

### The harbor
A small provincial port, not a city. A short stone quay; a curving beach of grey shingle and sand with a timber slipway; a handful of wooden merchant ships about 15 m long, dark tarred hulls, a single mast with a square sail; ropes, log rollers, piled stones. Behind, a steep hillside of small stone houses with plastered walls and terracotta roof tiles, a few bare trees. Grey winter sea. No temples, no lighthouse, no monuments, no soldiers, no banners.

### The house
One main room. Rough plastered stone walls, packed-earth floor with a few flagstones. An open hearth with a low stone curb and smoke rising to a hole in the roof; above it, two wooden pegs in the wall. A small square window with a wooden shutter, looking down over roofs to the harbor. An upright loom against the wall, warp hanging with clay loom weights. A small arched niche in the wall (the household shrine) holding a bronze figurine and a clay oil lamp. A wooden stool, a clay wine jug, a plain clay cup, a clay water jar.

### The figurine (Isis-Fortuna)
A bronze statuette about 15 cm tall of a standing woman in a draped robe knotted at the chest, a small disk between two horns on her head, a horn of plenty in her left arm and a ship's steering oar in her right hand, its blade resting on the base. Dark green-brown patina. It sits in the niche beside the lamp in B2 and is visible, small and soft, in the background of C1 if the framing allows.

### The rattle (sistrum)
A bronze hand rattle: a narrow loop-shaped frame on a short handle, three loose metal rods passing through the frame. Shaken once, in B2, by her hand.

### The steering oar
A long wooden steering oar, about three meters, with a broad flat blade at one end and a short crosswise tiller handle at the top. Weathered, dark with tar near the blade. It is the same object in A7, B3 and C3, and the oar is always described this way in prompts: never just "oar" (Veo will give a rowing oar).

### The people — described identically in every prompt
- **SAILOR** — a man in his mid-forties, weathered sunburned face, short dark beard going grey, cropped hair, a belted undyed wool tunic, thick forearms. Indoors he keeps the tunic and adds nothing.
- **WIFE** — a woman in her late thirties, dark hair pinned up under a plain cloth, a long undyed wool dress, a pale linen shawl. Practical, unhurried.
- **CREW** — four or five men in belted wool tunics, bare-legged, hauling and lifting. Never in close-up.
- **The goose** — one white domestic goose, A7 only.

Everyone barefoot or in simple leather sandals. No jewelry, no armor, no togas.

---

## 5. Footage plan

NBP plates first (harbor, house, people, figurine), then Veo motion passes with first/last-frame bookends where continuity matters, then assembly.

### Global prompt rules
- Clean physical description, no poetic language. Mood is never described; behavior is.
- Every Veo prompt opens with the look line, and ends with the close line, both verbatim.
- Fixed shots say `Camera is fixed, no camera movement.` Nothing else about the camera.
- Never use: Roman, Rome, legion, gladiator, goddess, Isis, temple, epic, cinematic, drunk, drunken, sad, lonely, melancholy, angry, argument, rudder (say "steering oar"), sistrum (describe the rattle). "Ancient Mediterranean" is the period cue; clothing and objects do the rest.
- People and objects are described verbatim from §4 every time they appear.
- No speech anywhere. Veo will want the reunion and the window scenes to talk. Mouths closed or still; if anyone speaks, regenerate or choose another window.
- If text, carved letters or graffiti appear on walls, hulls or pottery, regenerate.

**Look line:**
> Naturalistic footage of an ancient Mediterranean harbor town in late autumn. Overcast winter light, muted colors, soft contrast, real textures, nothing staged.

**Close line:**
> Camera is fixed, no camera movement. No music, no speech. No on-screen text, no captions, no watermark.

### NBP plates
- **P0 — pre-dawn sea.** Looking west over open grey sea from a low headland, deep blue pre-dawn sky clearing toward the horizon, no moon, no stars rendered (they are added programmatically), the dark edge of the shore at the bottom. First frame for V1.
- **P1 — harbor, morning.** The harbor per §4 from a slight height: quay, beach, slipway, three ships already hauled up, one ship in the water near the mouth with its sail half set, houses on the hill behind. First frame for V2.
- **P2 — slipway.** Eye level at the slipway: the tarred hull at the waterline on log rollers, ropes running up the beach to the crew. First frame for V3.
- **P3 — hulls ashore.** P1 re-made with every ship hauled up the beach, stones packed round each hull, the harbor water empty. Afternoon grey. Plate for V6 and the master continuity reference for the beach.
- **P4 — crew and couple sheet.** SAILOR, WIFE, and two CREW per §4, three-quarter and profile, flat light. Every first frame with a face derives from this.
- **P5 — the lane.** A steep stone-paved lane between plastered houses at dusk, the harbor glimpsed below. First frame for V7.
- **P6 — the room.** The house interior per §4, wide, from just inside the door: hearth with pegs above it, loom, window, niche with figurine and lamp. Hearth lit. The master continuity reference for every interior shot.
- **P7 — the niche.** Close on the shrine niche: the figurine per §4, the clay oil lamp lit, rough plaster. First frame for V9.
- **P8 — the window.** From inside, the SAILOR seated on a stool at the small window in three-quarter back view, cup in hand, rain on the roofs and the grey harbor beyond; the WIFE soft in the background at the loom. First frame for V11.

Lock P4 and P6 before deriving any interior or character first frame.

### Veo clips (8 s each, audio on)

**V1 — the western sea** (first frame P0) → A1
> [look line] Looking west over a calm grey sea from a low headland before dawn. The deep blue sky slowly grows paler. Small waves move on the water; a faint line of surf at the shore below. Nothing else moves. Audio: low wind, small waves on stone. [close line]

Stars are composited in assembly (§8). Veo must not render stars; if it does, regenerate or mask the sky.

**V2 — the last ship** (first frame P1) → A2
> [look line] A small harbor on a grey morning. A wooden merchant ship about fifteen meters long, with a dark tarred hull and a single mast, comes slowly into the harbor under oars while two men lower its square sail. Three other ships are already pulled up on the beach. Small stone houses with terracotta roofs on the hill behind. Audio: oars in water, ropes creaking, wind, gulls far off. [close line]

**V3 — the haul** (first frame P2; last frame: hull clear of the water on the rollers) → A3
> [look line] At the waterline of a shingle beach, five men in belted wool tunics haul a wooden ship with a dark tarred hull up a timber slipway on log rollers, pulling on thick ropes and leaning their whole weight back. The hull slides slowly up out of the shallow water. Audio: wet wood grinding on rollers, ropes straining, men's effort breaths, small waves. [close line]

Take rule: the hull must move uphill and clear the water. Men grunt, nobody speaks. If Veo floats the ship or reverses it, regenerate.

**V4 — the stones** → A4
> [look line] Close at the side of a dark tarred wooden hull resting on a shingle beach. Two men in belted wool tunics carry flat grey stones and wedge them tightly against the hull, one after another. Audio: stones knocking on stones, wind. [close line]

**V5 — the plug** (first frame: SAILOR's hands on the plug, from P4) → A5
> [look line] Close, low down at the underside of a dark tarred wooden hull resting on stones on a shingle beach. The weathered hands of a man in his mid-forties grip a round wooden plug set in the bottom planks, twist it and work it loose, and pull it out. Water runs out of the hole in a steady stream onto the wet shingle. He holds the plug and watches the water. Audio: wood squeak as the plug turns, water running onto stones, wind. [close line]

This is the keystone image of the piece. Take rule: the water must run out of the hole after the plug comes free, and keep running to the end of the window. If Veo cannot do it, generate the hands pulling the plug and composite the water stream from a separate pass. Composite, never merge.

**V6 — the beach** (first frame P3) → A6
> [look line] A shingle beach in a small harbor in late afternoon, grey light. A row of wooden ships with dark tarred hulls rests on the beach, pulled up out of the water, stones packed round each hull. The water of the harbor is empty and grey, small waves only. Nobody in frame. Audio: wind, small waves, a gull far off. [close line]

Take rule: no boat on the water, not one. The empty water is the shot.

**V7 — the lane and the goose** (first frame P5) → A7
> [look line] Dusk on a steep stone-paved lane between plastered stone houses on a hillside above a harbor. A man in his mid-forties with a weathered sunburned face, a short dark beard going grey and a belted undyed wool tunic walks slowly up the lane toward the camera, carrying on his shoulder a long wooden steering oar about three meters long with a broad flat blade and a short crosswise handle at the top. A white domestic goose waddles across the lane in front of him; he pauses and steps around it, and walks on. Audio: footsteps on stone, the goose's feet, wind, the sea below. [close line]

Take rule: the oar is a steering oar (broad blade, crosswise handle), not a rowing oar. He must not look at the camera. The goose is unremarked by him beyond the step around.

**V8 — the door** (first frame from P6 at the door, WIFE from P4) → B1
> [look line] Inside a small stone house at dusk, hearth firelight on the walls. A woman in her late thirties with dark hair pinned up under a plain cloth, a long undyed wool dress and a pale linen shawl opens the wooden door. A man in his mid-forties with a weathered face, a short dark beard going grey and a belted undyed wool tunic stands in the doorway with a long wooden steering oar on his shoulder. He leans the oar against the wall inside the door and they hold each other closely for a long moment, her hand at the back of his neck. Behind them the door swings shut on the wind. They do not speak. Audio: wind outside, then the door closing, then the fire crackling. [close line]

Take rule: brief, real, unperformed. No kiss staged for the camera, no speech, no tears. The door closing must be audible and on picture; it is the sound cut of the piece (§6).

**V9 — the niche** (first frame P7) → B2
> [look line] Close on a small arched niche in a plastered stone wall, lit by a small clay oil lamp. In the niche stands a bronze statuette about fifteen centimeters tall of a standing woman in a draped robe knotted at the chest, a small disk between two horns on her head, a horn of plenty in her left arm and a ship's steering oar in her right hand. A woman's hand comes into frame holding a small bronze hand rattle, a narrow loop-shaped frame on a short handle with three loose metal rods through it, shakes it once, and withdraws. Audio: one bright metallic shimmer of the rattle, the lamp, the fire. [close line]

Use 1.5 s that includes the single shake and the withdrawal. If the figurine's attributes drift (lost oar, lost horn), regenerate; the oar in her hand is the only reason this shot exists.

**V10 — the oar over the hearth** (first frame from P6 at the hearth) → B3, and its tail → C3 fallback
> [look line] Inside a small stone house, an open hearth with a low stone curb, a fire burning and smoke rising to a hole in the roof. Two wooden pegs are set in the wall above the hearth. A man in his mid-forties with a short dark beard going grey and a belted undyed wool tunic lifts a long wooden steering oar with a broad flat blade and lays it across the two pegs above the fire, settles it, and steps out of frame. The oar rests over the hearth with the smoke rising round its blade. Audio: wood on wood as the oar settles, the fire. [close line]

**V11 — the window** (first frame P8) → C1
> [look line] Inside a small stone house on a grey rainy day. A man in his mid-forties with a weathered face, a short dark beard going grey and a belted undyed wool tunic sits on a wooden stool at a small square window, a plain clay cup in his hand, looking down at the grey harbor and the wet roofs below. He drinks slowly and keeps looking out. Behind him, softer, a woman in her late thirties with dark hair pinned up under a plain cloth works at an upright loom with clay weights, passing the thread and beating it down. Neither speaks. Audio: steady rain on roof tiles, the regular soft thud of the loom, a cup set down on wood. [close line]

**V12 — the legs** → C2
> [look line] Inside a small stone house, late in a rainy day, dimmer light. A man in his mid-forties with a short dark beard going grey sits on a stool by a small window with his legs stretched out across the floor. He pours wine from a clay jug into a plain clay cup. A woman in her late thirties with dark hair pinned up under a plain cloth and a pale linen shawl carries a heavy clay water jar across the room and has to step around his legs. He does not move them and does not look at her. She does not look at him. Audio: rain, wine pouring, her footsteps, the jar set down. [close line]

Take rule for C1 and C2: friction by accumulation only. No raised voice, no gesture of anger, no tears, no confrontation, no one storming out. He takes up the room; she works around it. The first acceptable take is the take; do not regenerate toward more misery or toward reconciliation.

**V13 — the oar at night** → C3
> [look line] Night inside a small stone house. A long wooden steering oar rests on two wooden pegs above an open hearth, the fire low, smoke climbing slowly past the broad blade toward a hole in the roof. The room around is dark. Nobody in frame. Audio: the fire, rain on the roof, the soft thud of a loom off to one side. [close line]

Credit budget: V13 can be cut from V10's tail (after the man steps out) with a darker grade, saving one generation. V4 can be dropped by extending A3 and A5 if credits tighten; do not cut A5 or A6.

Generation count: 13 Veo clips (12 if V13 comes from V10), NBP plates P0–P8.

---

## 6. Audio design

- **Ambience beds.** Two worlds and one door between them.
  - Exterior bed (A1–A7): wind, small waves on shingle, a gull far off, built from the Veo clips' own ambience with slow crossfades across the hard cuts. Normalize to about −26 LUFS.
  - Interior bed (B1–C3): hearth crackle; from C1 on, steady rain on roof tiles. About −30 LUFS.
- **The door (B1).** The exterior bed runs under the start of B1 through the open door. On the frame the door shuts, the wind and sea drop hard to the interior bed. That cut is the sea closing, made audible. No other moment in the piece is that abrupt.
- **Foley** from each clip's Veo audio where clean, replaced with ElevenLabs where not: oars in water, ropes and rollers, effort breaths (never words), stones knocking, the plug's wood squeak and the water running out (A5, the loudest foley in A), footsteps on the lane, the goose's feet, oar on pegs, cup on wood, wine pouring, the loom.
- **The loom.** From C1 the loom's soft regular thud is the only rhythm in the room and carries under C3. It is her, working, unstated.
- **The rattle (B2).** One shake, a bright metallic shimmer, peak about −14 dBFS. The only made sound in the piece; it occurs once.
- **The goose.** No honk is required. If the A7 take has one, use the same goose honk take selected for AUGUST, so the series shares one goose.
- **No speech, no music.** Suno is not used.
- **Into the end card:** rain and the loom continue under the card at the interior level and cut on the last frame.
- **Master:** cap −1 dBTP, no program-wide loudness normalization.

### ElevenLabs SFX (generate 3–4 variants, pick by ear; every prompt ends `No music, no speech.`)

| ID | Prompt | Duration | Use |
|---|---|---|---|
| X1 | A wooden plug twisted and pulled out of the bottom of a wooden boat hull, a short wet wooden squeak, then water running out in a steady stream onto wet pebbles, close up. No music, no speech. | 4 s | A5, if Veo's is unusable |
| X2 | A heavy wooden door in a small stone house swinging shut on a windy evening, a solid wooden thud and latch, close. No music, no speech. | 1.5 s | B1 door, if Veo's is thin |
| X3 | A small ancient bronze hand rattle with loose metal rods shaken once, a single bright metallic shimmer, close up, dry. No music, no speech. | 1.5 s | B2 |
| X4 | Steady rain on terracotta roof tiles heard from inside a small stone room, an open fire crackling softly nearby. No music, no speech. | 15 s | C1–E bed |
| X5 | An upright wooden weaving loom, the soft regular thud of the weaving sword beating the thread down, slow and steady. No music, no speech. | 10 s | C1–E |
| X6 | Wind and small waves on a shingle beach in winter, a gull far off. No music, no speech. | 20 s | A bed fill |

---

## 7. End card (E)

Pillow, 3.0 s, black.

- Line 1: `NOVEMBER` — the series face, size, placement and duration matching previous installments (see §10).
- Line 2, proposed: `maria clauduntur` — "the seas are closed," from Vegetius 4.39. **Verified** against three texts (§1). Lowercase, set as a quotation in the series' secondary style, no translation on screen.

If the series card does not carry a line 2 by convention, drop it; the Vegetius line goes in the description instead.

---

## 8. Assembly (Claude Code)

1. **Plates (NBP).** P0–P8. Lock P4 (people) and P6 (room) before any interior or face first frame.
2. **The Pleiades (A1).** Render the cluster programmatically from real catalog positions (the six or seven naked-eye stars, relative brightness by magnitude, correct shape and orientation for a western setting seen from the Mediterranean). Place it low over the horizon in the V1 sky, small (the cluster spans about one degree; keep it a small knot of points, not a feature). Soft point sources with a faint bloom. Over the 3.0 s, fade the stars in step with the brightening sky so they go out into dawn; do not animate them sinking. No other stars. This is the "winter setting of the Pleiades" that closes the sea, and it should be findable rather than presented.
3. **Footage prep (ffmpeg).** Trim to window → conform to 1080×1920 (crop if 16:9) → grade per the light column in §3. Keep the grade naturalistic: lift nothing, crush nothing, no teal-and-orange.
4. **Composites.** A5 water stream if needed (§5). A1 stars. Composite, never merge.
5. **End card.** Pillow; series face per §10; line 2 only if the series uses one.
6. **Audio.** Beds → door cut → foley → rattle → loom → master, per §6.
7. **Concat** per the beat table. Encode H.264 high / CRF 16 / yuv420p / 24 fps, AAC 48 kHz 192 kbps.
8. Keep beat durations, the light slots, and the SFX placements in one structure in the script so a tolerance shift propagates.

---

## 9. QA — on a phone

- Nobody speaks, anywhere. Frame-step B1, C1, C2 for mouth movement.
- The steering oar reads as a steering oar (broad blade, crosswise handle) in A7, B3 and C3, and is the same object in all three.
- A5: the plug comes out and the water runs.
- A6: no boat on the water.
- A7: the goose crosses and is stepped around; he never looks at the lens.
- B1: the door shuts on picture, and the sound drops with it.
- B2: the figurine holds the steering oar and the horn of plenty; the rattle is shaken once.
- C1/C2: no anger, no confrontation, no tears. He doesn't move his legs. She doesn't look at him.
- A1: the Pleiades are small, correctly shaped, and fade out; no other stars.
- No legible text or letters anywhere in the body.
- Nothing reads as a historical epic: no soldiers, no temples, no monumental architecture, no heroic lighting.
- Light continuity per §3; the interior is consistent with P6 across B1–C3 (hearth, pegs, loom, window, niche in the same places).
- Watch once in a dark room with earbuds (the door cut, the loom) and once on the speaker in daylight (the plug water and the rattle must still read).

---

## 10. Open items

1. **End card.** Match the series' established face, size, placement and duration from the previous installments before rendering (3.0 s is planned; adjust and recompute if the series card is longer). Confirm whether line 2 is used.
2. **AUGUST goose honk.** If A7 carries a honk, pull the AUGUST take once that is selected.
3. **A5 water.** Veo-native vs composited stream, decided on the first take.
4. **9:16 availability** in Flow for the model in use.
5. **V13** as its own generation vs. V10's tail, decided by credits and by whether V10's tail holds still long enough.

Everything else is decided.

---

## 11. Publishing

**Title:** NOVEMBER

**Description (draft):**

> From the eleventh of November to the tenth of March, the seas are closed. — Vegetius, *Epitoma rei militaris* 4.39
>
> NOVEMBER (2026), 45 seconds. a][ productions.
>
> Made with Google Veo (via Flow), Nano Banana Pro, ElevenLabs sound effects, Claude (Anthropic) via Claude Code, and ffmpeg.
>
> November, from *novem*, nine: the ninth month of the old Roman year, now the eleventh. When the Pleiades set, the ships were hauled ashore and the steering oar hung over the smoke (Hesiod, *Works and Days* 618–632). The goddess on the shelf is Isis-Fortuna, who holds a rudder; her festival of the ship reopened the sea in March.

Hashtags and the Reels cross-post are the director's call. Thumbnail: A5 (the plug and the water) or C1 (the window).

---

## 12. Decisions and reasoning

- **Roman, provincial, small.** The closing rituals can be literal only in period, and Isis belongs there. A small town keeps it a film about a household; a grand port turns it into spectacle.
- **The plug as the closure.** Pulling the plug out of a hull you've just dragged ashore is a physical act of shutting down that looks like its opposite: the boat is opened so it can rest. It's the one image that says "closed for the season" with no help.
- **The oar comes home.** The sea's instrument moves into the house and hangs over the fire all winter. The man comes with it. Both are now in the room, both out of use.
- **The figurine holds a rudder.** Isis-Fortuna's attribute is a steering oar. The goddess on the shelf holds one all winter while the real one blackens in the smoke. Unstated; findable.
- **The reunion is the finding.** The Isia ends in the rejoicing at the finding. The myth stops there; the piece keeps going for four months. The reunion is short because the finding is short.
- **Friction by accumulation.** No explosion, by direction. He sits, drinks, looks at the water, takes up the floor; she works around him. The viewer supplies their own winter. Anything louder would be a different film and would turn him into a villain, which he isn't.
- **The door is the sound cut.** Wind and sea drop to the hearth when the door shuts. The sea closing is heard before it's understood.
- **The loom.** Her work is the only rhythm in the second half. It never stops, including under the card.
- **The goose.** The Calendar of 354's November page has a goose at the priest of Isis's feet. Here it crosses a lane and is stepped around. A wink to the series for anyone who's watched AUGUST, invisible to anyone who hasn't.
- **The Pleiades fade rather than set.** Their winter setting is what closes the sea in Vegetius. A sinking star field reads as an effect; stars going out into a grey dawn reads as weather.
- **No music, no speech.** The only made sound is the rattle, once, at the shrine.
- **Prior-art check skipped** at the director's direction.

---

## 13. Draft v1 (Claude Code, 2026-11-02)

Built the same day as the spine, autonomously after the director's notes. 1082 frames (45.08 s): the series card, then
seventeen segments from sixteen Veo 3.1 takes (1080×1920, nine of them silent, seven with native audio), every take kept at
its first attempt. Changes from the spine, all the agent's: the Pleiades opener dropped for the ship's details; the lane
walked away from the camera; the oar already leaning inside the door at the homecoming; the winter extended to six beats
(the window, the pour, the step over his legs, his hand on the beached hull in the rain, the night with him asleep and
her still at the loom, the oar in the smoke); no music. Open on the status page: the beach in the rain (keep or cut), the
haul in which the hull barely moves, the man who watches her step over his legs instead of looking away, the goose that
follows him instead of crossing, and the ending (the close of the oar, or the empty room at night). The workspace plan
`data/workspace/november/plan.md` holds the beat sheet, the gate record and the reshoot queue.

**v2 (2026-11-02):** the director's three notes on v1 applied, no new generation: the ship shot ends as the sail comes
down (source frame 98), the haul plays reversed so the men back away from the hull on the ropes (a local render of the
same take, its forward sound kept), and the step over his legs starts mid-step (source frame 111). 1013 frames, 42.2 s.

**v3 and the 4K master (2026-11-02):** the director's continuity note on v2 applied (the plug before the stones, so the
stones packed round the hull do not vanish when the plug comes out); approved ("Excellent work") and finished the same day.
The 4K master is the fast native-2x model per assembled segment, blended 50/50 with a Lanczos pass (the model alone
etched the wet hull and the wool), BT.709 tagged, with the approved soundtrack muxed unchanged. Delivered for upload.
