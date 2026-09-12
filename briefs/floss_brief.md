# FLOSS — brief

**Format:** 9:16 social short, 28.67 s, 4K (2160×3840) upscaled from 720p. Built 2026-09-11, 10:00–18:00 with review rounds.
**Title:** FLOSS. **Workspace:** `data/workspace-archive/floss/` · **Master:** `final/floss_v4_wm_720.mp4` → `final/floss_v4_4k.mp4`
**Published:** https://youtube.com/shorts/Ego0tAYQaRY (2026-09-11; description used substantially as drafted, trimmed by Stephen) · 4K delivered 2026-09-11 18:06 via share.cjs (7-day links, gs://vg-veo-0137184346/floss/) · 4K verified 2160×3840 / 688 f / 28.67 s (2x Real-ESRGAN → Lanczos; the tool's default 4x was resampled to 3x) · audiowmark decode after upscale conf 1.35

## Concept
A woman Auguste clown twists one green modelling balloon into an animal, three times, from the identical starting frame in a real one-ring tent. Veo cannot conserve a balloon: one becomes three to five, and she presents a two-headed giraffe, a wishbone and a paperclip with total delight. Floss — the cotton candy Stephen photographed at a ballgame on 2026-07-08 because its crease looked like a mouth — heckles from the lower-left corner on his stick, eyeless, deadpan. The stinger is the real photo brought to life: "Anyway. I'm on a stick."

Same engine as STILL JUGGLING (the heckler counts the model's failures), but this time the heckler was **generated separately and inserted** into finished footage — the technical stretch of the piece.

## Shape (v4)
| t | beat |
|---|---|
| 0.00 | c3 held first frame 1 s; Floss pops up: "Oh, good. Balloon animals. My favorite." |
| 3.70 | "Oh, that's a giraffe. No." on the quarter-second real giraffe, ahead of her "A giraffe!" (7.24) |
| 8.40 | "It has two heads." over the reset cut to c2 |
| 10.70 | after her early "A dog!": "She called it. Nothing's happened." |
| 13.60 | on her glance down and the one-handed Y: "What? That's a wishbone!" |
| 19.50 | c1, one balloon becomes three: "That was one balloon!" |
| 22.85 | the giant loop: "That's a paperclip." She lowers it through his corner and ta-das |
| 25.17 | hard cut: the real photo (IMG_9872), the actual cotton candy says "Anyway. I'm on a stick." End 28.67 |

## How it was made
- **One plate, two layers.** Nano tent plate; clown hero sprite (magenta key) composited on it → the clown anchors; Floss sprite (green key, from the real photos) composited on the *empty* plate in the lower-left → the Floss anchors. Locked camera on both.
- **Clown clips:** 3 × 8 s Quality 720p, first-frame only, native audio (balloon squeaks + she says the animal's name). All kept, no rerolls; clone-check clean 3/3; clip-qa flagged only balloon multiplication (the premise).
- **Floss lines:** 1 probe + 7 lines, 4 s each, Veo-native voice, Floss alone in frame (no human face to steal the line). 8/8 verbatim on first generation. Voice: ~220 Hz, ~0.55 s/word deadpan.
- **Insert without a chroma key:** `scratch/diffmatte.py` — colour keys fail under warm tent light (pink goes peach, the red curb reads pink). Working matte = the anchor's own silhouette aligned per frame on the lower "jaw" rows against the anchor's pixels (search ±30 px; he drifts up to 26 px as he leans in), gated so prior pixels must differ from the plate outside a deep core (kills the "dark cap"), unioned with blurred diff-vs-plate evidence for the lifted lip, then close/open/fill/largest-component. Full-res crops were the arbiter: three earlier matte versions passed at phone size and failed at 100%.
- **Assembly:** `scratch/assemble.py` + `edl_v2.json` — clip-relative line placement in her silent gaps (voice-band scan), hand-puppet pop-in/out per line, each line trimmed to its speech; bed −23 LUFS ducked under lines at −16.5; calliope bed (ElevenLabs music) −24, ends on the stinger cut. Master −17.7 LUFS, −1.4 dBFS peak. audiowmark payload `FLOSS-2026-09-11`, decode conf 1.48 at 720p.

## Gens
c1 dog 8 s · c2 dog fast+glance 8 s · c3 giraffe 8 s · f0 probe 4 s · f1–f6 lines 4 s · f7 stinger 4 s (real-photo anchor). All Quality 720p, audio on. 11 submissions, 11 kept.

## Cost (Veo $22.40 of $25; ≈ $25 all-in)
Veo 56 s × $0.40 = **$22.40** (pre-logged in `data/veo-budget-floss.tsv`) · nano 3 calls ≈ $0.45 · QA vision ≈ $1.50 · ElevenLabs music 36 s on plan.

## Lessons
- A separately generated talker can be inserted into locked-camera footage with no chroma backdrop if both layers come from one plate; the matte is a shape prior plus difference evidence, not colour.
- Show insert tests with the inserted character's own audio mixed and the base ducked, or the viewer diagnoses a Veo attribution bug that isn't there.
- Veo clowns talk when told not to; scan the voice band and place lines in the gaps.
- The real photo the character came from is a free, perfect stinger anchor.
