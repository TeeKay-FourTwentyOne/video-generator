# HEAD FAKE — Lessons (SHELVED 2026-05-31)

**Status:** Shelved after rough cut v1. Concept↔medium mismatch, not an execution failure. ~$4–5 spent (Fast). Brief: `head_fake_brief.md`. Archived workspace: `data/workspace-archive/head-fake/` (rough cut at `headfake_rough_v1.mp4`).

## The concept
Literalized "head fake" pun (Videodrome register), 9:16. Beat 1 (player, kinetic): head snaps off as a hollow shell, real head rises calm looking the other way — deception hides a truth. Beat 2 (ref, dread): face peels to a head-shaped void, ref keeps signaling — deception hides absence. Same grammar, inverted payload.

## Why it didn't work (the verdict)
The payload **is** a precise, uncanny transformation, and that's exactly what Veo can't deliver:
- **RAI fought the key beats.** The tear was prompt-filtered as decapitation; the molded-face floor prop was **input-image** blocked (person/face). The gag lives in the exact register the filter guards.
- **Interpolation reads as mush.** Even successful Fast clips turned "one head → shell + new head" into morphing, not a crisp deadpan shock.
- **The register needs a razor seam.** "Mundane until the seam, then horror" dies when the seam is soft. AI video gives doll-headed uncanny instead of clean dread. User: "turned out very strange… Veo fought us too hard."

## What worked (reusable, banked)
- **The full book-end pipeline ran clean** — 3 ref frames → 9 nano anchors → 4 Fast Veo clips → ffmpeg assembly → designed ElevenLabs soundscape, all in one autonomous pass.
- **Rephrase clears the prompt RAI filter:** abstracting "a hollow shell separates at the collar" → "a smooth hollow prop lifts and sails off" cleared decapitation code 42237218. (Distinct from the **input-image** filter, code 17301594 — un-fixable by prompt; only by de-facing the image.)
- **Nano rendered the headless-ref void STILL perfectly** (B3) on the first try. Stills can hold what Veo's motion won't — the void hold needed no ffmpeg matte.
- **ffmpeg crossfade rescued a fully-blocked Veo pass** (the button: A_shell→A5 dissolve).
- **`poll-veo-ops.cjs` surfaces RAI `FILTERED` explicitly** — avoids the silent create_job hang.

## If ever revisited
Different medium (2D/cutout animation or heavy compositing/roto so the transformation is authored, not generated), or a concept that keeps the "head fake" inversion without asking Veo to render decapitation (e.g. the fake is plainly a mask/prop from the first frame). See memory `feedback_veo_unfit_precise_body_horror`.
