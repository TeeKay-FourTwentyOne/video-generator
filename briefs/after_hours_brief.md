# AFTER HOURS — Shooting Script v1

**Date:** 2026-05-28
**Slug:** `after-hours` — workspace `data/workspace/after-hours/`
**Format:** **16:9 landscape**, 4K final (Real-ESRGAN ×2 from 1080)
**Runtime target:** ~2:00 (120s)
**Pipeline:** Veo 3.1 (Fast default; 3 Quality pre-allocated) book-ended off nano-banana poster frames; ~30% of runtime is held nano stills with ambient soundscape; designed-from-scratch sound design, `generateAudio=false` on every Veo shot

---

## Logline

Two old men sit one stool apart at the counter of an American diner at 2 a.m. closing. The waitress is offscreen, mopping. They don't speak. After a long quiet one of them slides his hand across the formica. After a longer quiet the other puts his hand over it. The OPEN sign clicks off outside. They stay.

## Tone

Hopper-register stillness with the warmth that Hopper never quite gives. Wenders / Jarmusch slowness. The piece is plain-spoken and sincere — no irony, no twist, no body-horror beat. The only event is a hand moving a few inches. The piece has to earn that gesture across two minutes of held quiet, and it has to land it without underlining.

Nothing in the piece *announces* what the two men are to each other. Brothers, lifelong friends, the only two regulars who outlived everyone else, lovers — whichever the viewer brings is the right one. The piece is about the **gesture** and the **companionship**, not about identity. Don't write any prompt or beat that resolves the ambiguity.

## Public Domain & IP Position

- "Nighthawks" (Hopper, 1942) is referenced as a *visual register* only. Composition is deliberately different — we shoot **from behind the counter**, a straight counter (not Hopper's wraparound bar), no large picture window in the background, no dome roof. Different shot, same emotional weather.
- No music quoted. Score is original ElevenLabs Music.
- No named brands in the diner — generic neon "OPEN," generic coffee, generic menu board. Hand-built signage via nano if any text appears.

---

## The Formal Conceit — ONE LOCKED MASTER + TWO INSERTS

The piece lives in **one camera angle** for ~85% of its runtime: a locked landscape two-shot of the counter, the two men one stool apart, the pass-through glow on the right, the window-neon spill on the left, the offscreen mopping audible on the left. That's the whole grammar.

Two close inserts break it, both at the formica counter level:
1. **The cold-coffee insert** — early. A cup, a still hand near it, the man not drinking. Establishes that time is passing and nothing is being said.
2. **The gesture insert** — the climax. Hand slides. Hand covers. We never cut to faces during this; the gesture has to read on the hands alone.

One exterior bookend — establishing at the head, "OPEN" sign clicking off at the tail.

## The Two Men

Both **late 70s, American, working-class, present-day**. They look like they've come from somewhere that closed early.

- **MAN A** — taller, thinner, weathered face, white hair short and combed, clean-shaven, dark windbreaker over a button-down. The man who slides his hand first.
- **MAN B** — shorter, rounder, white walrus mustache, ball cap on the counter beside him, faded canvas work jacket. The man who covers it.

Different builds and different face hair are deliberate so Veo doesn't conflate them across shots. Char-lock both before any shot, with three views each (front / 3/4 / profile).

## The Diner

Small, narrow, late-50s American counter joint that's been kept open through the decades. **Six stools at a straight counter** running camera-left to camera-right; behind the counter, a pass-through window into the kitchen with warm tungsten light spilling out. **Stainless napkin holders, sugar shakers, ceramic mugs, formica counter, swivel stools with red vinyl tops.** Behind the men (over their shoulders in the master), a window onto the street — through it, a vertical neon "OPEN" sign in cool red.

Time of day: **2 a.m., closing.** All booths empty. House lights dimmed; only the pass-through and the window-neon light the room. Faint kitchen-fan hum, faint traffic outside.

The waitress — never seen on camera. We hear the mop, the bucket wheel squeak once, the swish of fabric as she passes. Once she enters frame as **a single arm reaching in to pour fresh coffee**, no face. Her sole presence in the piece is offscreen care.

## Continuity

- **Wardrobe lock** across all shots (char ref clothing; do not let Veo re-style).
- **Cup positions** lock across shots; pre-place in nano plates.
- **Light direction** — pass-through warm from right, neon cool from left — same every shot.
- **Counter level** — both inserts must match the master's counter-line so the cuts feel like the same room.

## Sound Design — silence is the score

No music for the first ~80 seconds. The piece breathes on:

- Mop swish + bucket wheel squeak (waitress, offscreen left)
- Kitchen fan hum (steady low)
- Fluorescent buzz (faint, intermittent)
- Coffee pour (the waitress's arm shot)
- Ceramic on formica (each time a cup is set down)
- Stool creak (one, near the start, when Man B shifts weight)
- Distant muffled traffic + occasional distant car passing through
- Neon hum (window, the cool buzz)

Music enters **only at the gesture insert** — Cue 1, very quiet, builds across the after-master and the OPEN-sign-off, finishes under the title card. One cue total.

**Cue 1 (the only music):** slow sparse solo fingerstyle nylon-string guitar, key of C, ~60 BPM, melodic line that never resolves to tonic, occasional high piano note from offstage as if from a different room. Ry Cooder / Bill Frisell / Daniel Lanois register. Length ~50s. Enters at video t≈1:20, lasts to end. Generated once via ElevenLabs Music.

`generateAudio=false` on **every** Veo shot. All sound is designed in post.

---

## Shot List

| # | Beat | Veo | Dur | Audio events |
|---|------|-----|-----|--------------|
| S1 | **Exterior establishing.** Front of the diner at night. Neon "OPEN" in the window, two seated silhouettes visible through it from a respectful distance across the street. Held wide. | Fast | 4s | distant traffic, neon hum, faint kitchen-fan through window |
| S2 | **Master interior** — locked landscape two-shot. Both men at the counter, one stool apart, both staring forward at the back-bar. Cups in front of each. Man B shifts on his stool — one small creak. Otherwise still. | **Quality** | 8s | stool creak, fan, mop swish off-left |
| S3 | **Held still on master** (PIL still of S2 last frame + Veo-loop ambient, no character motion) — time passing, the quiet of the room. | (still) | 10s | fan, mop swish (further away), one ceramic-on-formica from off-right |
| S4 | **Insert — Man A's cold coffee.** Close on his cup; his weathered hand resting on the counter near it, not lifting. Slight wisp of steam absent (coffee has gone cold). | Fast | 6s | fan, distant car passing |
| S5 | **Master — the near-look.** Man A turns his head a few degrees toward Man B, doesn't quite reach a look, returns to forward. Man B doesn't notice. | **Quality** | 8s | fan, neon hum, the soft scrape of a mop entering its bucket |
| S6 | **Held still on master** (PIL still of S5 last frame + ambient). Longer hold. | (still) | 12s | fan, distant traffic, a faint chair-scrape from the kitchen |
| S7 | **The waitress's arm.** From off-left, a woman's hand and forearm reach in with a coffee pot, top up Man A's cup, then Man B's cup, then withdraw. Faces unseen. The men barely react. | Fast | 8s | coffee pour ×2, pot set down off-frame, soft "thanks" murmured by Man B (no head turn) |
| S8 | **Held still on master** (PIL still of S7 last frame) — both men now have fresh cups. Man B lifts his and drinks. Held. | (still + 1 Veo motion loop) | 10s | sip, ceramic on formica, fan |
| S9 | **The gesture insert.** Close on the counter between them. Man A's hand slides a few inches across the formica toward Man B. After a beat — long enough to feel — Man B's hand enters from the right and comes to rest over Man A's. Both hands still. | **Quality** | 8s | fan, the soft drag of a hand across formica, the very first quiet notes of **Cue 1** enter under the second hand |
| S10 | **Master — after.** Both men still facing forward. Hands joined on the counter between them, just visible at the bottom of frame. Held. Neither looks at the other. | Fast | 8s | Cue 1 continues, fan recedes, neon hum recedes |
| S11 | **Exterior — closing.** Front of the diner from across the street again. The OPEN sign in the window clicks off mid-shot. Inside, the two silhouettes remain. | Fast | 6s | the click of the OPEN sign, Cue 1 continues, late-night street |
| S12 | **Held exterior** (PIL still of S11 last frame). The diner darker now, only the kitchen pass-through glow inside. They're still there. | (still) | 8s | Cue 1 continues, distant traffic |
| S13 | **Title card.** White serif "AFTER HOURS," small, lower-center, on black. Cue 1 finishes mid-phrase, then silence. | (still) | 4s | Cue 1 tail then silence |

**Total:** ~100s of clip + 4s title card ≈ 104s. Comfortable in the 120s target with room for breath at the edges. Veo total: ~56s.

### Quality allocation

- **S2** — the master must read as a real locked-camera shot of a real room; this is the shot the whole piece sits on.
- **S5** — the "near-look." Subtle facial performance from Man A in a held two-shot. Veo Fast tends to over-act small turns; Quality holds the restraint.
- **S9** — the gesture. The shot the piece exists to land. No compromise.

S1, S4, S7, S10, S11 on Fast. S3, S6, S8, S12 are PIL stills with ambient — no Veo cost at all.

---

## Poster Frames (book-end)

- **Char refs ×2** — Man A and Man B, three views each (front / 3/4 / profile), seated-at-counter wardrobe, plain neutral lighting.
- **Diner master plate** — the locked landscape composition, fully lit per the scene, both men placed at their stools, all props in their locked positions. Use this plate as the Frame A for S2, S3, S5, S6, S8, S10.
- **Exterior plate** — front of the diner at night, "OPEN" lit, the two silhouettes visible through the window. Use for S1, S11, S12.
- **Counter detail plate** — close-up of the formica counter section between the two stools, with both men's hands resting on it, both cups in their locked positions. Frame A for S9.
- **Coffee-cup plate** — close-up of Man A's cup with his hand near it. Frame A for S4.
- **Waitress-arm plate** — counter with a woman's arm and coffee pot reaching in. Frame A for S7.
- **OPEN-sign-on / OPEN-sign-off plates** — exterior, S11 needs both as Frame A and Frame B respectively, for the click-off moment.
- **Per-shot Frame A / Frame B** — A is start, B is end. Run `tools/frame-qa.py` on every A/B pair before submitting to Veo.

The two men's wardrobe and seating posture must be **pixel-identical** across plates that share the master angle. Same wardrobe means: if Man A's jacket is unzipped halfway in S2, it's still unzipped halfway in S5, S8, S10. Build the master plate first, copy-edit it for each shot's specific changes.

---

## Risk Register

- **Two old men in long held two-shot** — Veo can drift face features across shots. Char-lock both, use 3/4 view consistently, accept tiny wardrobe drift, fix face drift via frame-edit if needed.
- **Restraint at this scale** — Veo Fast tends to add unprompted blinks, gestures, look-arounds. Prompt explicitly: "minimal movement, slow blinking only, no head turns unless described, no hand gestures unless described." Quality for S2/S5/S9 because restraint is the performance.
- **The "near-look" S5** — Veo may overshoot the head turn (making it a full look, which kills the beat) or undershoot (no movement read at all). Quality + explicit prompt: "Man A turns his head approximately 15 degrees to his right, holds for one beat, returns to forward. Eyes do not move to look at the other man."
- **The gesture S9** — the entire piece. Frame A: both hands on counter, apart. Frame B: hands joined. Prompt the motion between. Quality. Have a fallback: if Veo can't deliver, build the hand-slide and hand-cover as two separate 3-4s Veo segments + a brief PIL still bridge.
- **Hopper proximity** — must not read as a "Nighthawks" copy. Reviewer should check the master plate against Hopper before approving it. Counter perspective (we're behind the counter looking out, not from the street looking in), shape of room, absence of round bar — all distinct from Hopper.
- **Veo native audio sneaking in** — `generateAudio=false` on every shot or our designed soundscape collides with mumbles, plates clinking, ambient that we didn't author. Triple-check this flag.
- **The waitress's arm S7** — Veo may try to show her face. Frame A: counter with her arm reaching in, her body cropped at the elbow above frame. Prompt: "The waitress's face and head are never visible. Only her right arm enters frame from the upper left, holding a coffee pot, pours into each cup, withdraws." Char-ref a generic older-woman forearm so the skin tone and sleeve stay consistent.
- **Cue 1 entrance timing** — must enter under the second hand at S9, not on the cut. ElevenLabs music will have a soft beginning anyway; trim Cue 1's actual onset to align with the second hand landing.
- **Empty diner read** — if Veo populates the booths with extras, the piece collapses. Master plate must show empty booths and prompt explicitly: "no other patrons, no other staff, no other customers, no figures visible in the background."
- **Ambiguity preservation** — the piece must NOT resolve what the two men are to each other. No wedding rings on adjacent fingers, no shared name on coats, no signal either way. Wardrobe and props neutral. Performances neutral but warm.

## Cost Estimate

- ~56 Veo-sec (counting every submission including rerolls / RAI hits / round-up) → ~$1.5–2 Veo Fast + ~$3–4 Veo Quality ≈ **$5–6 Veo**
- ~14–18 nano images (char refs ×2 ×3 views, master plate, exterior plate, counter plate, cup plate, arm plate, sign plates, per-shot A/B) → **$2.5–3.5**
- 1 music cue (~50s) + ~10 SFX → **$1.5–2**
- QA Anthropic (frame-qa across A/B pairs, clip-qa where autonomous) → **$1–2**

**Rough total: $10–13.5.**

## Working Doctrine

Fast-default. Quality pre-allocated for S2, S5, S9 only — no extra Quality without conversation. One generation per shot. Keep / edit-rescue / flag-skip — no autonomous rerolls. The piece sits or falls on the gesture; if S9 doesn't land on first try, that's the one shot we re-do thoughtfully (re-shot or built from two halves), not the rest. Imperfect clips elsewhere get shown to the user before regenerating; small wardrobe drifts across held two-shots are forgivable, since the audience is locked on the faces and hands.

The piece is short. Build sequentially: refs → master plate → S2 (the bet on the whole piece) → review → S9 (the bet on the ending) → review → fill in around them. If S2 and S9 work, everything else falls into place.
