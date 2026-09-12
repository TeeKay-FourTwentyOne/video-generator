# SPIDER ARREST — brief (v1 draft)

**Format:** 9:16 social short, 23.1 s, 720p master (native; no upscale until review). Built 2026-09-12, 01:20–03:00, autonomous.
**Title (working):** SPIDER ARREST. **Workspace:** `data/workspace/spider-arrest/` · **Master:** `final/spider_arrest_v1_720.mp4` · **Review link:** `final/links.md` (7-day signed URL) · **Debug copy:** `scratch/spider_arrest_v1_720_debug.mp4`
**Status:** v1 draft awaiting Stephen's watch. Decision queue below.

## Concept (as briefed)
A man is arrested in an alley. He smirks and offers his wrists; the cuffs go on. Then he unfolds extra spider-style legs from his own legs and scurries off into the dark, tittering. Not scary: jarring and funny. Part 1 builds tension, cinematic; Part 2 is the punchline in a different look. Budget $30. "Pushing into the amusingly uncanny and what Veo can produce around SFX."

## Three structural calls made autonomously (reversible at review)
1. **The extra legs are his own legs, multiplied**: same charcoal trousers, same oxfords, splayed spider-style. Funnier and RAI-safer than chitinous legs, and it is exactly Veo's limb-multiplication habit used on purpose. Six legs, not eight: nano gave six and the count is not the joke.
2. **The officer is faceless throughout** (back to camera, hands only). One identity to hold; no face or insignia in a front-facing frame to trip the input-image classifier. Zero RAI trips in five submissions.
3. **Two registers, hard-cut on the cuff click.** Part 1: prestige crime drama (sodium/teal, shallow focus, slow push-ins, drone under). Part 2: red-blue patrol-strobe, low wide lens, handheld, SFX only. The music stops dead on the click.

## Shape (v1)
| t | shot | beat |
|---|---|---|
| 0.00 | fade up, S1 wide 0→5.2 | man alone mid-alley; officer walks in from foreground, stops in front of him |
| 5.21 | S2 OTS medium 0.3→6.6 | head down → head lifts → smirk → offers wrists |
| 11.54 | S3 insert 0→1.4 | cuffs ratchet shut (click, click) |
| 12.96 | S4 wide-low strobe 0→4.8 | register break; he grins; legs unfold one pair at a time from 2.1 s; six-leg splay by 4.3 s |
| 17.79 | S5 2.75→4.6 | mid-spin blur → many-legged scurry into the dark |
| 19.67 | button 3.5 s | programmatic hold on the empty alley over the officer's shoulder, strobe pulsing, distant titter; fade out |

## How it was made
- **Plate + hero** (nano, text-only, both first try), then every anchor from (hero + plate). S1/S3/S5 first-frame-only; S2/S4 book-ended with chained last frames. Pre-gen gate: anchor-drift on every pair (S4 pair flagged a dumpster slide → re-chained with set dressing pinned → PASS; S5 pair flagged HIGH, nano re-staged the foreground officer when adding the figure → S5 went first-frame-only). frame-qa skipped; frames eyeballed at 540px.
- **Veo:** 5 × Quality 720p, native audio on. No RAI trips, no rerolls. Post-gen: clip-qa + clone-check on all five, transcribe on S1/S2/S4/S5.
- **Sound:** Veo native beds normalized per clip to absolute LUFS (−25/−22 Part 1, −18 Part 2, S1 rumble ducked −9 dB under the drone), ElevenLabs drone (−23, hard stop at 12.9 s), EL cuff click, unfold clicks, skitter, two titters; Veo's own laugh from S5 (0.85–2.75 s) lifted as a layer bridging the S4→S5 cut. Limiter 0.80, level=false, 192k oversampled. Master −18.9 LUFS, −1.2 dBFS peak.
- **Assembler:** `scratch/assemble.py` + `scratch/edl_v1.json` (concat filter, per-clip bed targets, duck ramps, SFX at absolute LUFS, music with hard stop, master fade). Button: `scratch/button.py` (still → push + 2 Hz red/blue pulse + grain).

## Gens (all Quality 720p, audio on; ops + seeds in `scratch/ops.txt`)
S1 6 s (first-frame) · S3 4 s (first-frame) · S2 8 s (book-end A2→B2) · S4 8 s (book-end A1→B2) · S5 8 s (first-frame). 5 submissions, 5 kept (all edit-rescued by trim).

## Cost (≈ $17.0 of $30)
Veo 34 s × $0.40 = **$13.60** (`data/veo-budget-spider-arrest.tsv`, pot cap $25) · nano 13 calls ≈ $2.10 (4 more 429'd, unbilled) · Anthropic QA $1.31 (cost-ledger) · ElevenLabs 1 music + 6 SFX on plan.

## Decision queue for review
1. **S5 (the exit) is the weak gen.** During his spin Veo swapped the black shirt for a white shirt + tie and his arms came un-cuffed as he laughed at camera; a patrol car materializes at the far end from 4.8 s. v1 cuts in mid-blur (2.75 s) and out at 4.6 s so none of it is on screen, but the exit is only 1.9 s. *Recommend:* one reroll ($3.20, pot has $11.40) with wardrobe/cuffs pinned in the prose ("black shirt, no tie, handcuffed wrists held together throughout, never turns to face camera") — or keep the short exit; it does read as speed.
2. **S4 second officer.** A uniformed figure walks through the background from 4.9 s; v1 ends S4 at 4.8 s. Nothing to do unless you want a longer six-leg hold (then reroll S4).
3. **Button is a still.** The programmatic hold over the officer's shoulder reads as a new angle; if it feels dead, a 4 s Veo empty-alley gen is $1.60.
4. **Officer wardrobe.** Veo dressed him in a uniform shirt in S1; S2 anchors were regenerated to match, but S4/S5 show a rain jacket at the frame edge. Cosmetic under the strobe.
5. **Length 23.1 s of a 30 s cap.** Room to lengthen S2's wrist-offer hold or the button if the rhythm wants it.
6. After picture lock: watermark + 4K upscale (disk is at 97%, 16 GB free — clear space first).

## Lessons
- Fast full-body spins under strobe re-invent wardrobe and props (shirt, tie, cuffs) even with a first-frame anchor; cut in on the blur, and pin wardrobe/props in the motion prose, not just the anchor.
- Long holds in a busy strobe-lit set breed background figures (a second cop at 4.9 s). Plan the usable window at ≤ 5 s on wide holds.
- Chaining nano to ADD a large mid-frame figure to an empty plate re-staged the foreground (officer size/position, lamp color); anchor-drift caught it pre-spend. Adding small props chains cleanly; adding a person does not.
- Whisper hallucinates "Thank you for watching" (and a Japanese equivalent) on Veo ambient beds; check `no_speech_prob` before believing a transcript.

## Description draft (trim before posting)
He offered his wrists. He did not offer his legs.
A 23-second short built with Veo 3.1, Nano Banana and ElevenLabs. #ai #veo #short #comedy
