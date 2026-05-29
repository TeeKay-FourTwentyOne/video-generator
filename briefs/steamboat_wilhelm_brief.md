# STEAMBOAT WILHELM — Shooting Script v2

**Date:** 2026-05-27 (v2 — landscape, return-to-cartoon, single music bed)
**Slug:** `steamboat-wilhelm` — workspace `data/workspace/steamboat-wilhelm/`
**Format:** **16:9 landscape**, 4K final (Real-ESRGAN ×2 from 1080)
**Runtime target:** ~52s (5 shots — descent through 4 styles, then return to cartoon for the button)
**Pipeline:** Veo 3.1 (Fast default; 2 Standard pre-allocated) book-ended off nano-banana poster frames

---

## Logline

A jaunty 1928-style cartoon riverboat captain spins his wheel — and the world
style-shifts beneath him. Cartoon → Keaton silent → noir → *Apocalypse Now*
upriver. The same cheery 1928 whistle plays cheerfully through every world,
increasingly wrong as the visuals darken. On the final spin the world snaps back
to the safe original cartoon — same animals, same gags — and then the cabin door
creaks open. A voice from the dark: *"The horror. The horror."* The cartoon
doesn't protect him.

## Tone

Whimsical homage that turns. The descent runs cartoon → silent → noir → dread,
but the *music never changes* — the refusal of the soundtrack to acknowledge the
visuals is the joke and the dread. The fifth spin returns the visuals to the safe
cartoon world; the horror reaches him there too. The cartoon was never a shelter.

## Public Domain & IP Position

- *Steamboat Willie* (1928) and the 1928 Mickey Mouse character design entered
  U.S. public domain 2024-01-01. We are making an **homage**, not a reproduction.
- "Mickey Mouse" name / branding — never used.
- Character is **Steamboat Wilhelm**, visually distinct from PD Mickey (different
  proportions and features; peaked captain's cap, not the small flat sailor's cap;
  no round ears).
- "Steamboat Bill" (the tune Willie whistles) is PD; we use a whistled / calliope
  arrangement as our continuous music bed.
- Keaton's *Steamboat Bill Jr.* (1928) is PD — same era, fair to reference.
- "The horror. The horror." is PD (Conrad, *Heart of Darkness*, 1899).
- *Apocalypse Now* (1979) is under copyright — we reference the *upriver-twilight
  visual register*, not specific shots, characters, or music. No Doors.

---

## The Formal Conceit — THE WHEEL AS STYLE-CHANGER

Every shot is on the same riverboat wheelhouse, framed on Wilhelm at the wheel
(landscape 16:9 — wide enough for the deck-business gags to live in the same
frame as Wilhelm). He spins the wheel; the world style-shifts. Four descending
worlds, then a return:

| # | World | Visual register |
|---|-------|-----------------|
| 1 | 1928 rubber-hose cartoon | B&W, rubbery limbs, sync'd cartoon foley, cheery whistle |
| 2 | 1928 silent live-action (Keaton) | B&W silent-film grain, slapstick background |
| 3 | 1940s noir | High contrast, rain on wet wood, neon-on-water, smoke |
| 4 | *Apocalypse Now* upriver register | Color 35mm grain, twilight, mist, jungle pressing in |
| 5 | **1928 cartoon (return)** | Back to S1's exact register — and the cabin door opens. |

## Beats Preserved from *Steamboat Willie*

So the homage is unmistakable, S1 hits these specific Willie cues:

- **Whistling "Steamboat Bill"** while turning the wheel — Willie's opening beat.
- **The iconic heel-bounce** in rhythm with the whistle — Willie's signature body language.
- **A goat chewing sheet music** — Willie's most-quoted background gag.
- **A cow's tail plucked like a banjo / a chicken in a steam valve** — the animals-as-instruments register Willie established.
- **A cargo crane swinging a load aboard** in the background — winks at the Minnie-lifted-aboard beat without introducing the character.
- **A parrot on a perch** in the wheelhouse — Willie's mocking parrot. Present in S1 and again in S5.

S5 returns to the same cartoon staging — same animals, same parrot, same crane,
same whistle, same heel-bounce. The familiarity is what makes the door wrong.

## The Continuity Prop — THE HAT

Wilhelm wears a **white peaked captain's cap with a black brim and a simple round
brass badge**. The hat is the only physical object that survives every style
transition unchanged. Deliberately *not* the small flat sailor's cap from the 1928
short — keeps us visually distinct from PD Mickey.

## Wilhelm's Reaction Arc

The face is the audience's anchor. The descent is told on him:

| World | His face |
|-------|----------|
| 1. Cartoon | Whistling, grinning, big-eyed, gloved hands tapping the wheel, heel-bouncing on the beat |
| 2. Keaton | Stoneface double-take. Slow blink. Lifts the hat 1cm and replaces it. |
| 3. Noir | Mouth firmer. Eyes shadowed under the brim. Watching the river, not driving. |
| 4. Apocalypse Now | Stopped moving. Just staring forward. Sweat. The hat darker. |
| 5. Cartoon return | A flicker of relief — eyes widen, the near-grin returning — *then* the door creaks open behind him and the relief curdles. |

---

## Music — ONE 1928 whistled / calliope cue, unchanged across all five shots

The same cheery whistled "Steamboat Bill" (PD) with light calliope and cartoon
percussion plays *continuously through every world*. Volume holds steady, tempo
doesn't darken when the visuals do. By S4 — the same bouncy whistle floating over
twilight mist on the Nung — it is genuinely unsettling. In S5 the tune finally
matches its world again, which makes the door-opening worse.

**Generate once** as a single ~52s ElevenLabs bed and lay it under the whole
timeline. Do not regenerate per shot — it has to sound like the same recording.

**At the cabin door mid-S5:** the whistle continues for one extra bar after the
door creaks open, then cuts dead mid-phrase. Silence. The VO. Black.

## The Cabin Door — planted from S1, opens in S5

A **CABIN DOOR** is visible in the wheelhouse background of *every* shot — same
position (camera-left, behind Wilhelm), same dimensions, restyled per world. It
is never the focus and never opens until the final shot. In S4 it may catch a
faint glint or draft to draw the eye.

In S5 (cartoon return) it **creaks open** behind Wilhelm. The interior is **pitch
black** — wrong for the cartoon world, where everything should be drawn and
shaded. A hoarse, frail male VO from the dark:

> "The horror. The horror."

We never see who. Hold on Wilhelm's curdled face / the black doorway. Cut to black.

---

## Shot List

| # | World | Beat | Veo | Dur |
|---|-------|------|-----|-----|
| S1 | 1928 cartoon | Wilhelm at the wheel, whistling "Steamboat Bill," heel-bouncing in rhythm. **Background:** goat chewing sheet music, cow's tail plucked like a banjo, chicken jammed in a steam valve, parrot on a perch, cargo crane swinging a load aboard. Cabin door visible camera-left. He grabs the wheel and gives it a big rubbery spin. | Fast | ~10s |
| S2 | Keaton silent | Hard cut on the spin. Same wheel, same hat — Wilhelm is now a real man in B&W silent-film grain. **Background:** a deckhand slips on a wet plank, a barrel rolls past, a crate of chickens bursts open. Wilhelm gives a flat stoneface double-take. He spins the wheel. *(Music: same cheerful whistle continues — already wrong here.)* | Fast | ~10s |
| S3 | 1940s noir | Hard cut. Boat passes a dark dock under rain. Wet wood, neon-on-water, smoke. **Background:** a stevedore under a streetlamp lighting a cigarette; a woman in a wet coat watching the boat pass. Wilhelm's eyes are shadowed under the brim. He grips the wheel and turns it slow. *(Whistle continues, increasingly off.)* | **Standard** | ~12s |
| S4 | Apocalypse Now upriver | Hard cut. Twilight on the river. Mist. Color 35mm grain. **Background on the lower deck:** a soldier smoking, a radio crackling, a surfboard lashed to the rail, eyes on the trees. Wilhelm is dead-still at the wheel, staring forward. The cabin door catches a faint glint. He raises his hands and spins the wheel one last time. *(Whistle still going.)* | **Standard** | ~12s |
| S5 | Cartoon return + button | Hard cut. We're back in S1's cartoon world — same animals, parrot, crane, staging. A flicker of relief crosses Wilhelm's face; the heel-bounce nearly resumes. The whistle plays one more bar. The **cabin door creaks open** behind him. The interior is pitch black — wrong for the cartoon. The whistle cuts dead mid-phrase. Wilhelm slowly turns. VO from the dark: *"The horror. The horror."* Cut to black. | Fast | ~8s |

**Total:** ~52s. End card optional ("STEAMBOAT WILHELM", white serif on black, ~2s).

### Standard allocation

- **S3 noir** — rain on wet wood + neon-on-water reflections + low-key lighting.
- **S4 Apocalypse Now** — mist + low-light color + character stillness + the cabin-door glint.

S1, S2, S5 on Fast. S5 can re-use S1's poster plate with surgical edits (door
opens, face curdles) — a cheap shot to produce.

---

## Poster Frames (book-end)

Camera: medium, slightly low, on Wilhelm at the wheel inside the wheelhouse,
**landscape 16:9**. Wide enough for the deck-business gags to live in the same
frame as Wilhelm. **Wheel position, stance, hat, cabin-door placement** locked
across all five worlds.

- **Char ref** — Wilhelm, three views (front / 3⁄4 / profile). Same cap.
- **Hat ref** — high-res still of the captain's cap, for frame-edit repair.
- **Wheelhouse master plates ×5** — same locked landscape composition styled in
  each register (cartoon / Keaton / noir / jungle / cartoon-return). The
  cartoon-return plate is a copy of the cartoon plate with door opened and
  interior black-keyed.
- **Per-shot Frame A / Frame B** — A is start, B is end (mid-wheel-spin).
- **Cross-style transitions** — Frame B of S1 (cartoon, mid-spin) is frame-edited
  into Frame A of S2 (Keaton silent, same pose, same hat, new style). Same A→B
  convention across S2→S3, S3→S4, S4→S5. The transition *is* the style change
  happening on the same pose.
- **S5's door** — Frame B of S5 = same as Frame A but with the cabin door fully
  open and the interior a flat black void.

Run `tools/frame-qa.py` on every A/B pair before submitting to Veo.

---

## Risk Register

- **1928 cartoon style on Veo** — shaky. If S1 drifts toward 3D or modern flat 2D,
  fall back to nano stills + programmatic motion (wheel-spin as still pan/scale;
  heel-bounce as a 2-frame loop). Treat S1 as a probe shot.
- **Hat drift across styles** — known Veo issue. Frame-edit the hat back in on any
  A/B that drifts. Hat survival is non-negotiable.
- **Identity drift across 5 registers** — char-lock + same-pose endpoints + the hat carry it.
- **PD / Mickey adjacency** — Wilhelm's design must be unmistakably ours. No round
  ears under the hat; different proportions; different features.
- **Cartoon return must feel exactly like S1** — same animals, same crane, same
  parrot, same lighting. The familiarity is what makes the door wrong. Re-use S1's
  plate as the basis for S5's plate; don't regenerate from scratch.
- **"The horror" voice** — hoarse, whispered, male, from the dark. ElevenLabs male
  voice tuned to high tension + low energy + atmospheric processing.
- **Apocalypse Now register without infringement** — reference the *register*
  (twilight, mist, jungle, river), not specific shots/characters. The surfboard
  is a wink, not a quote. No Doors music.
- **Music consistency** — the bouncy 1928 whistle through noir/jungle must sound
  like the *same recording* in every shot. Generate once, lay under the whole
  timeline; do not regenerate per shot.

## Cost Estimate

- ~52 Veo-seconds (counting every submission incl. rerolls / RAI hits / round-up) → ~$5 Veo Fast + ~$3 Veo Standard ≈ **$8 Veo**
- ~14–18 nano images (char + hat + 5 master plates + per-shot A/B + S5 open-door variant) → **$2.5–3**
- TTS (one line) + 1 long music cue (single PD whistle bed) + SFX → **~$1**
- QA Anthropic (frame-qa + clip-qa where autonomous) → **~$1–2**

**Rough total: $12.5–17.5.**

## Working Doctrine

Fast-default; Standard pre-allocated for S3 and S4 only. One generation per shot.
Keep / edit-rescue / flag-skip — no autonomous rerolls, no extra Standard.
Imperfect clips get shown to the user, not silently re-rolled. Decisions queued
for end-of-build review.
