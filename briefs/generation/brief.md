# GENERATION — production spine v1

a][ productions · standalone conceptual piece (Halloween, second piece) · 2026-10-30
Writer: Claude Fable 5.1.

This is the historical production spine. The [decisions](decisions.md) and
[release handoff](handoff.md) record the approved variations and finished film.

Original handoff target: Claude Code (NBP → Veo → ffmpeg). Production implementation: Codex, using the maintained Google image and Veo adapters. Written to survive without the director present.

---

## 1. Concept

A backyard birthday party, July 1983, shot on a camcorder somebody set on a tripod and forgot. The same seven seconds of tape, played six times, each time one dub generation further from the original. Each copy is worse: softer, smearier, the color bleeding, the hiss doubled. And each copy has fewer people in it. Twenty-four, then twenty, then fifteen, then eight, then one, then nobody.

Nobody notices the first subtraction. On the third copy one woman looks at the empty chair beside her. On the fourth, the ones who are left have stopped eating and are turning to look around the yard. On the fifth there is only the woman, barely legible under the noise, moving fast, calling a name the hiss has eaten. The sixth copy is first-generation clean: hard sun, balloons on the fence, the cake on the table, the pool water moving, nobody. The tape runs to its end and the VCR goes blue.

Nothing is stated. The picture gets worse as the people go, and it gets perfect when they're gone. The viewer works out alone which of those was the loss.

Lineage: SCP-1733 (a broadcast that replays with the people inside it slowly aware of the loop) and SCP-1981 (a tape that is different every play, the subject worse off each time). This piece keeps the replay, the dawning awareness, and the degradation-as-record, and does it with dub generations instead of a curse.

---

## 2. Format

- Canvas 1080×1920 (9:16), **30 fps**, H.264 (high, yuv420p) + AAC 48 kHz (mono in a stereo container).
- Runtime 43.0 s (1290 frames). Not built to loop; it opens and closes on VCR blue, which is neutral.
- Footage window: 4:3, 1080×810, full canvas width, y 555–1365. Everything outside the window is #000000 for the entire runtime.
- Footage rendered at 640×480, dub-degraded (§7), upscaled to 1080×810 bilinear.
- On-screen text: the VCR's own `PLAY` on-screen display only (§4).
- No music, no title, no end card, no credits in the body.

---

## 3. Beat sheet

| # | Time (s) | Frames | Content | People | Picture | Source |
|---|---|---|---|---|---|---|
| — | 0.0–0.5 | 0–14 | VCR blue, silence | — | — | Pillow |
| G1 | 0.5–7.5 | 15–224 | the party; nothing wrong | 24 | gen 1 | V1 |
| — | 7.5–7.8 | 225–233 | snow | — | — | synth |
| G2 | 7.8–14.8 | 234–443 | the party; four fewer; nobody notices | 20 | gen 2 | V2 |
| — | 14.8–15.1 | 444–452 | snow | — | — | synth |
| G3 | 15.1–22.1 | 453–662 | W looks at the empty chair beside her; a man glances behind him; everyone else carries on | 15 | gen 3 | V3 |
| — | 22.1–22.4 | 663–671 | snow | — | — | synth |
| G4 | 22.4–29.4 | 672–881 | nobody is eating; people standing, turning, looking across the yard and at each other; one walks out of frame | 8 | gen 4 | V4 |
| — | 29.4–29.7 | 882–890 | snow | — | — | synth |
| G5 | 29.7–36.7 | 891–1100 | W alone; up from the table, turning, out of frame, back, calling; a chair goes over | 1 | gen 5 | V5 |
| — | 36.7–37.0 | 1101–1109 | snow | — | — | synth |
| G6 | 37.0–42.0 | 1110–1259 | the yard; nobody; pool water moving; balloons moving | 0 | **gen 1 (clean)** | V6 |
| — | 42.0–42.3 | 1260–1268 | snow (tape end) | — | — | synth |
| — | 42.3–43.0 | 1269–1289 | VCR blue, silence | — | — | Pillow |

Hard cuts everywhere, picture and sound. The snow gaps are the dubbing VCR between copies: full-frame noise with audio white noise. They are not black.

**Sync anchor.** Every copy starts on the same frame (the NBP plate for that generation, which is the party plate with people removed and nothing else changed). The first ~1.0 s of each copy should play the same: the same arm raising the same cup, the same kid at the pool edge. Divergence begins after that and grows with each generation. Choose Veo windows so the subtraction plate is frame 0 and the window runs 7.0 s.

**Subtraction order.** Not patterned. The exceptions: the birthday child goes in G2 (unremarked by anyone, including the camera); W is the last person left. Nobody reacts to who is missing, only to the fact of absence.

**W's escalation, calibrated.** "Frantic" happens inside seven seconds, on a fixed camera, under gen-5 noise. She is never close to the lens and never looks at it. The viewer sees a figure moving fast through a snowstorm and hears one voice under the hiss. That ceiling is what keeps it from being a performance.

Tolerances: G5 may run to 8.0 s if the take needs it for the exit-and-return; G6 does not extend (5.0 s is the beat). Keep the beat table as one structure in the script.

---

## 4. The tape — visual spec

### Page
- #000000 everywhere outside the window, every frame.

### Window
- 1080×810 at (0, 555). No border, no rounding, no shadow.

### VCR blue (head and tail)
- Full window fill #1a1aa8. Nothing on it.

### Snow (gaps)
- Full-window monochrome noise, uncorrelated per frame, with a slow horizontal tear band. Rendered at 640×480 and upscaled like everything else.

### VCR OSD: `PLAY`
- Burned at 640×480 scale, **after** the dub degradation (the OSD comes from the playback deck, not the tape, so it is clean on every copy). Top-left, x 28, y 24. Blocky VCR OSD face: a 7-segment-ish uppercase sans at 28 px, #ffffff with a 2 px #000000 edge. A small solid right-pointing triangle, 16 px, before the word, gap 8 px.
- Visible for the first 2.0 s of each copy, then off. Not on during snow or blue.
- No counter, no date stamp, no `SP`, no deck name. One word.

### The camcorder look (gen 1 target; §7 degrades from here)
- Early consumer tube camcorder: soft, slightly warm, highlights that bloom and streak vertically on hard white (paper plates, the pool, a white shirt), color a little oversaturated and a little wrong in the reds, mild vignetting. Hard July sun, high, short shadows. Camera on a tripod at chest height, slightly wide, fixed.
- Not film. Not "VHS aesthetic" presets. The look is a tube camera on a good day; the dub chain supplies the ruin.

### The scene (identical in all six clips)
- A suburban backyard: patchy lawn, chain-link fence along the back with a dozen balloons tied to it, a one-story house edge at the left, a concrete patio at the right with a sliding door. A long folding table with a paper tablecloth, paper plates, cups, a sheet cake with candles, mid-frame. Aluminum-and-webbing lawn chairs around it. A kiddie pool front-right. A charcoal grill at the back left with smoke. Nothing branded. No text on anything (no banner, no cake lettering, no shirts with words).

### The people (gen 1: twenty-four)
- A mix of adults and kids in 1983 summer clothes: shorts, tube socks, sundresses, a few feathered haircuts, one man in a polo with the collar up, kids in swimsuits. Ordinary; nobody styled.
- **W** — a woman in her thirties in a yellow sundress, dark hair in a ponytail, seated at the near end of the table. Described identically in every prompt that includes her. She is in all five populated copies; she is the only one in G5.
- The birthday child: a kid of seven or so in a paper crown, at the cake. Present in G1 only.

---

## 5. Footage plan

Six Veo generations; one base plate and five subtraction plates from Nano Banana Pro. All Veo clips: 8 s, 16:9 if 4:3 is unavailable, highest resolution, audio on, Veo 3-class via Flow. Center-cropped from 16:9 to 4:3 at assembly, so **keep the table and all the people inside the central 75% of the frame.**

### Global prompt rules
- Clean physical description, no poetic language.
- Every Veo prompt opens with the look line and the scene line, verbatim, and ends with the close line, verbatim.
- Never use: horror, eerie, creepy, haunted, ghost, vanish, disappear, missing, supernatural, scary, Halloween, VHS, glitch, found footage. The people are simply not in the plate; Veo is never told anyone is gone. The reactions are described as physical behavior only.
- Veo will want to put words on the cake, the balloons, or a shirt. The close line forbids text; if any appears, regenerate (the frame geometry is fixed by the plate, so cropping around it is not an option).
- W's descriptor is reused verbatim (§4).

**Look line:**
> Home video from an early 1980s consumer camcorder on a tripod at chest height, slightly wide lens, fixed. Soft image, slightly warm, bright highlights bloom, colors a little oversaturated, mild vignetting. Hard midday July sun, short shadows.

**Scene line:**
> A suburban backyard: patchy lawn, a chain-link fence along the back with a dozen balloons tied to it, the edge of a one-story house on the left, a concrete patio with a sliding glass door on the right, a long folding table with a paper tablecloth, paper plates, cups and a sheet cake with candles in the middle of the frame, aluminum lawn chairs around the table, a small inflatable kiddie pool in the right foreground, a charcoal grill with smoke at the back left.

**Close line:**
> Camera is fixed on a tripod, no camera movement. No music, no distinct speech. No on-screen text, no writing on the cake, balloons or clothing, no captions, no watermark.

### NBP plates

**P1 — gen-1 plate (24 people).** The scene line as a still, with twenty-four people as described in §4 in the middle of a party: eating, standing, kids at the pool, the birthday child at the cake in a paper crown, W at the near end of the table in a yellow sundress, ponytail, seated. Camcorder look. Take rule: the first plate where everyone reads as an ordinary person and the clothes read as 1983 is the plate. Lock it; everything derives from it.

**P2–P6 — subtraction plates.** Each is an edit of P1 removing people and changing nothing else. Removed people's chairs stay; their plates and cups stay on the table. The lawn under them is lawn.
- P2: remove 4 (including the birthday child). 20 remain.
- P3: remove 5 more. 15 remain.
- P4: remove 7 more. 8 remain.
- P5: remove 7 more. W alone, seated.
- P6: remove W. Nobody.

Check every plate against P1 pixel-for-pixel outside the removed figures: fence, balloons, table, pool, grill, shadows. Any drift in the set between plates reads as a cut, and the piece depends on it being the same yard.

### Veo clips

**V1 — the party** (first frame P1) → G1
> [look line] [scene line] Twenty-four people, adults and children, at a birthday party: some seated at the table eating cake, some standing talking in small groups, children playing at the edge of the kiddie pool, a child of about seven in a paper crown at the cake. A woman in her thirties in a yellow sundress with dark hair in a ponytail sits at the near end of the table. Ordinary party movement: eating, talking, laughing, a man raising a cup. Nobody looks at the camera. Audio: overlapping party chatter, children, a radio playing indistinctly, a lawnmower far away. [close line]

**V2 — four fewer** (first frame P2) → G2
> [look line] [scene line] Twenty people, adults and children, at a birthday party: some seated at the table eating cake, some standing talking in small groups, children playing at the edge of the kiddie pool. A woman in her thirties in a yellow sundress with dark hair in a ponytail sits at the near end of the table. Ordinary party movement: eating, talking, laughing, a man raising a cup. Nobody looks at the camera. Audio: overlapping party chatter, children, a radio playing indistinctly, a lawnmower far away. [close line]

Take rule: G2 must be indistinguishable in behavior from G1. Nobody pauses, nobody looks around. If the take has anyone reacting to anything, reject it.

**V3 — the chair** (first frame P3) → G3
> [look line] [scene line] Fifteen people at a birthday party, most of them eating and talking as before. A woman in her thirties in a yellow sundress with dark hair in a ponytail sits at the near end of the table; about two seconds in, she stops eating, turns her head and looks at the empty lawn chair beside her for a moment, then looks back at her plate. Near the grill, a man glances over his shoulder at the empty lawn behind him and turns back. Everyone else carries on. Nobody looks at the camera. Audio: party chatter, slightly thinner, children, a radio playing indistinctly, a lawnmower far away. [close line]

Two reactions, both small, both finished within the window. If more than two people react, choose another window or regenerate; G3 is the first crack, not the panic.

**V4 — the turn** (first frame P4) → G4
> [look line] [scene line] Eight people at a birthday party. Nobody is eating. Four are standing. They turn slowly and look across the yard, at the fence, at the patio door, at each other, as if listening. A woman in her thirties in a yellow sundress with dark hair in a ponytail stands up from the near end of the table and looks toward the house. One man walks out of the frame at the left edge and does not come back. Nobody looks at the camera. Audio: a few voices, low, a question asked and not answered, the radio still playing indistinctly, the lawnmower far away. [close line]

Reject if anyone walks toward the camera or looks at the lens, if anyone runs, or if the group clusters into a huddle (they should be spread out, each looking somewhere different).

**V5 — W** (first frame P5) → G5
> [look line] [scene line] One person: a woman in her thirties in a yellow sundress with dark hair in a ponytail, alone at a long table set for a party. She stands up fast, knocking her lawn chair over, turns in a full circle looking at the yard, walks quickly out of the frame at the right edge toward the patio, comes back into the frame, stops in the middle of the lawn and calls out a name toward the house, then toward the fence. Nobody answers. She does not look at the camera. Audio: her footsteps on the lawn, the chair falling, her voice calling a name, the radio playing indistinctly, the lawnmower far away. [close line]

Take rule: the first acceptable take is the take. Acceptable: she stays mid-distance, never approaches the lens, never looks at it, mouth movement is calling (not conversation), the chair goes over. Do not regenerate toward more distress; gen-5 noise will do most of the work, and a measured take under heavy noise reads worse than a histrionic one.

**V6 — the yard** (first frame P6) → G6
> [look line] [scene line] Nobody in frame. The balloons move on the fence in a light breeze. The water in the kiddie pool moves slightly. Smoke rises from the grill. The paper tablecloth lifts at one corner. The candles on the cake are lit. Audio: birds, a light breeze, the lawnmower far away, the radio playing indistinctly. [close line]

The candles are lit in G6 and nowhere else (in G1–G5 they are unlit; the cake is cut). Unremarked. If Veo cannot keep the cake continuous, drop the candle note rather than fight it.

---

## 6. Audio design

Camcorder mono, then dubbed as many times as the picture.

- **Source.** Each copy's own Veo audio, trimmed to the window. Discard any intelligible words; the prompts ask for none and the dub chain will bury what slips through, but check G4's "question" and G5's calling: a listener must hear a voice, never a word. If a word survives gen-5 processing, notch it or replace the syllables with a library crowd fragment.
- **Gen-1 target.** Band-limit 100 Hz–8 kHz, light compression, −23 LUFS integrated. Chatter sits on top; the radio and mower are far.
- **Dub chain (per generation).** One pass = band-limit a little narrower (top drops ~700 Hz per pass), add tape hiss (pink-ish, −48 dBFS at gen 1, +4 dB per pass), slight wow (0.3 Hz, ±0.06 semitones, growing), a touch of distortion, then re-normalize so the chatter stays near −23 LUFS while the floor rises under it. Apply the chain n times to copy n. By G5 the hiss is at about −28 dBFS and the top is near 4 kHz; W's voice reads as a voice through a wall.
- **The chatter thins on its own**: fewer people in the take means fewer voices in Veo's track. Do not pad with library crowd. G4's bed is a few low voices; G5's is one.
- **Snow gaps.** Full-band white noise at −20 dBFS, 0.3 s, hard in and out.
- **Blue.** Digital zero.
- **G6.** Gen-1 audio, no dub chain. Birds, breeze, the mower, the radio. The cleanest sound in the piece, and the only copy nobody is talking in.
- **No music.** Suno is not used. ElevenLabs is not used.
- **Master.** Per-copy levels as above, cap −1 dBTP, no program-wide normalization (the hiss ramp is the structure).

---

## 7. Assembly (Claude Code)

1. **Plates (NBP).** P1, then P2–P6 as edits of P1. Lock P1 before any Veo call. Diff each subtraction plate against P1 to confirm only people changed.
2. **Veo.** V1–V6 per §5. Windows: plate on frame 0, 7.0 s (G6 5.0 s).
3. **Footage prep, per clip:**
   a. Trim to window. Center-crop to 4:3. Scale to 640×480.
   b. Camcorder base (all clips, once): mild vertical highlight streak on pixels above ~240 luma (a 1D vertical blur of a thresholded highlight mask, added back at ~40%), slight warm shift, gentle vignette, 0.4 px blur. Light touch; Veo should have most of this from the look line.
   c. **Dub pass** (the heart of the piece), applied n times to copy n, G6 gets zero:
      - Split to Y and UV. Horizontal blur Y by 1.0 px; horizontal blur UV by 4 px and shift UV right by 1 px (chroma bleed and delay).
      - Luma: slight contrast loss (lift blacks ~3/255, pull whites ~5/255), gamma 1.03.
      - Horizontal line jitter: per scanline random offset, σ 0.3 px at gen 1, growing ×1.5 per pass.
      - Noise: monochrome grain σ 3 at gen 1, ×1.4 per pass; sparse dropout dashes (short bright horizontal lines, 1–2 px tall, random x, a handful per frame at gen 1, more each pass).
      - Head-switch band: the bottom ~8 lines tear horizontally by 2–10 px, worse each pass.
      - Encode/decode: libx264 at 640×480, 1200 kbps, GOP 15, no B-frames, preset fast, then decode. Each pass re-encodes the previous pass's output.
      Because the chain is literally applied n times, G5 is G1's ruin ×5, and no one has to hand-tune a "worn" look. Calibrate the per-pass constants so G5 is legible as a woman in a yellow dress moving fast, and not more legible than that.
   d. Upscale to 1080×810 bilinear. Burn `PLAY` (post-degradation, §4). Pad onto 1080×1920 black at (0, 555).
4. **Snow and blue** rendered at 640×480, same upscale, same pad.
5. **Audio** per §6, one WAV per copy at the copy's exact length; white noise for snow, zero for blue.
6. **Concat** per the beat table. Encode H.264 high / CRF 16 / yuv420p / 30 fps, AAC 48 kHz 192 kbps.
7. Keep the beat table, people counts, and dub-pass constants in one structure in the script so a G5 extension or a constant tweak propagates.

---

## 8. QA — on a real phone

- Window pixels outside the frame are 0,0,0 on every frame; blue is #1a1aa8 edge to edge.
- Each copy's first frame matches its plate; the first second of G1–G5 plays the same action.
- Counts: 24 / 20 / 15 / 8 / 1 / 0. Frame-step and count on each copy's cleanest frame.
- The set is identical across all six: fence, balloons, table, pool, grill, shadows. No drift.
- G2: no reactions at all. G3: exactly two small reactions, W's chair look included. G4: nobody eats, nobody runs, one exit left. G5: chair over, out right, back, calling; never near the lens, never at it. G6: nobody; things move.
- Degradation is monotonic G1→G5 and resets to clean at G6. Put G1 and G6 side by side; G6 should be at least as clean.
- Audio: hiss rises each copy; voices thin each copy; G5 is one voice and no words; G6 is clean and wordless; snow gaps are hard-edged; blue is silent.
- No text anywhere in the footage. `PLAY` only, and only for 2 s per copy.
- Watch on an OLED in a dark room with earbuds and once on a lit bus on the speaker. On the speaker G5's voice must still read as a voice.

---

## 9. Publishing

**Title:** GENERATION

**Original proposed description (superseded by [description.md](description.md)):**

> Copy of a copy of a copy. July 1983.
>
> GENERATION (2026), 43 seconds. a][ productions.
>
> Made with Google Veo (via Flow), Nano Banana Pro, Claude (Anthropic) via Claude Code, and ffmpeg. There is no tape, no party and no 1983; every copy is generated, and the generation loss is real — each one is the previous one re-encoded.
>
> After SCP-1733 and SCP-1981.
>
> https://github.com/TeeKay-FourTwentyOne/video-generator

Hashtags and the Reels cross-post are the director's call. No thumbnail work; any frame of G3 is the thumbnail.

---

## 10. Decisions and reasoning

- **The dub chain is real.** Each copy is actually re-encoded one more time than the last. The degradation is not a filter preset standing in for loss; it is loss. That is the same move as VERIFY's street-mapping texture and MOTION's 15 fps: the documentary ground has to be true for the one false thing to land.
- **Generation means both things.** Each copy is a dub generation and a separate Veo generation. The word in the title is doing both jobs and says so to nobody.
- **The clean last copy.** The picture gets worse as the people go and gets perfect when they are gone. A worse-and-worse chain ending in noise would say "entropy"; ending clean says the people were the noise. The viewer decides which reading they can live with.
- **The birthday child goes first, unremarked.** The party does not notice its own reason. Unstated, and the viewer who counts will find it.
- **Nobody reacts to who; only to that.** No one points at a chair and says a name. Absence is what registers, not identity. It keeps G3 and G4 from becoming acting.
- **W's ceiling.** Mid-distance, fixed camera, gen-5 noise, seven seconds, one voice with no words. Her panic is real and almost illegible, which is the only way panic can survive the restraint rule.
- **The camera is a tripod nobody comes back to.** It cannot pan to look for anyone. In G6 it is still running because there is no one to stop it; the tape ends because it ran out.
- **`PLAY` is the only text.** It is the playback deck's word, not the tape's, so it is clean on every copy, which quietly tells the viewer the ruin is in the tape and not in the TV.
- **Snow between copies, not black.** The gaps are the dubbing deck between files; blue at the ends is the deck with nothing loaded. Period-accurate, and black would read as editing.
- **No music, no speech, no title card.** The only voices are the party's, and they go one by one.
- **Prior art.** SCP-1733 and SCP-1981 as named; the analog-horror genre at large (Local 58, Gemini Home Entertainment, the Mandela Catalogue) trades on broadcast interruptions, entities, and lore. The divergence here: nothing interrupts the tape, nothing appears, the deck works perfectly, and the horror is arithmetic. Credit the SCP lineage in the description; do not pretend cursed tapes are new ground.

---

## 11. Open items (resolve on what Veo returns)

1. Whether Flow offers 4:3 for the model in use; if not, 16:9 with the action held in the central 75%.
2. Subtraction plates: NBP edit fidelity outside the removed figures. If P2–P6 drift, generate P6 (empty yard) first and add people to it in stages instead.
3. Dub-pass constants: calibrated so G5 is just legible. Decided by eye on a phone.
4. G5 length: 7.0 s if the exit-and-return fits, up to 8.0 s if not; recompute runtime.
5. The lit candles in G6: keep if the cake stays continuous across plates; drop otherwise.
6. Whether Veo's G4 "question" and G5 calling leave an intelligible word after gen-4/5 processing; notch or replace if so.

Everything else is decided.


## Production credit

Written by Claude Fable 5.1. Production and editing by Codex. The original spine is preserved unchanged in the private workspace. No credits appear inside the film.

https://github.com/TeeKay-FourTwentyOne/video-generator
