# BROKEN RECORD — brief (overnight v1, 2026-07-22)

**Mandate:** overnight autonomous build; "another visual / audio illusion effects video"; 9:16; 30–70s; series-or-standalone = my call. Goal set: complete v1 tonight. **No 4K until user review** (house standard).

## Decision: standalone, not FALSE COLOR Ep.3

- FALSE COLOR Ep.1 (built, phone-validated) and Ep.2 "Magenta" v3 (built 2026-05-31) are both **awaiting review/ship** — a third unshipped episode helps nothing.
- The June 29 `false-color-motion` POC (Rotating Snakes / Ouchi) has an **unresolved perceptual gate** — "does static drift land on the user's phone?" was never answered. Not a foundation for an overnight build.
- Benham/Fechner (color from B/W flicker) was considered and rejected for tonight: sustained 4–10 Hz black/white flicker is squarely in the photosensitivity band; needs a user-scoped session, not an autonomous ship.
- Chosen: the most robust passive auditory illusion there is, audio-led where the shelf is visual-led.

## Concept

**BROKEN RECORD** — the **speech-to-song illusion** (Diana Deutsch, 1995). A spoken phrase, looped unaltered, flips from speech to song by ~rep 6 for most listeners; afterwards the *original sentence* sounds sung forever. The piece performs it, proves the stimulus never changed, and names it.

The loop phrase is self-refuting: the voice repeats **"I am not singing"** (or nearest scored winner) while it inexorably becomes song. The physical claim on screen stays true; the percept betrays it. That's the FALSE-COLOR-ethos payoff (percept with no physical referent) in a standalone wrapper.

Secondary visual echo: staring at the static looping words induces wordform satiation (the words start *looking* wrong) — one quiet aside names it.

## Honesty contract (verified in code, stated on screen)

1. One synthetic voice (ElevenLabs), **one take, unedited** — provenance stated on the setup card and in credits.
2. Every repetition is a **byte-identical copy** of the same segment of that take (asserted in QA on the master WAV).
3. The final replay is the **same take** again, unaltered.
4. Uniform gain only on the voice — no EQ/compression/pitch work. **No audiowmark** (it would vary between reps and break claim #2 on a spectrogram; precedent: FULL DISCLOSURE).
5. On-screen pitch trace is the actual YIN f0 of the actual segment.

## Structure (~60s, 1080×1920@60, full-range sRGB recipe)

1. **0–6** cards: "sound on." → claim card ("a synthetic voice. one take, unedited. nothing about the recording will change.")
2. **6–11** full sentence plays once, plain caption.
3. **11–36** the last words loop ×~12, constant gap. Live f0 trace retraces the identical curve every rep + rep tally. Aside ~rep4: "(nothing is changing.)" Staff-lines + noteheads bloom under the same curve ~rep8 (reframe, not alteration). Satiation aside ~rep10.
4. **36–40** hard cut to black + silence: "the recording never changed." / "you did."
5. **40–46** replay of the original sentence (same take); span underlines as it passes.
6. **46–58** "it will never sound like speech again." / "the speech-to-song illusion · Diana Deutsch, 1995" / title card **BROKEN RECORD** + a][ productions + synthesis credit.
7. **58–60** fade to the opening black → Shorts auto-loop replays the piece; second viewing opens already-sung.

## Build plan

- TTS: 2–3 voices × candidate sentences × 2 takes (S1 "This is my speaking voice. I am not singing." primary; alts scored). High-stability settings, natural speed.
- YIN f0 tracker (numpy): score spans on within-syllable pitch stability, distinct levels, range, rhythm → pick winner. Selection is measured, not vibes.
- Audio master in numpy: intro sentence · loop block (segment+gap ×N byte-identical) · silence · replay · silence. Uniform gain to ~−16 LUFS. 48k stereo WAV.
- Renderer: contract.py constants; PIL sprite text (no drawtext); raw-pipe rgb24 → ffmpeg; static dither; Ep.2 encode + VUI bsf tag fix; faststart.
- QA gates: rep byte-identity; ffprobe 4× color tags/60fps/duration; caption safe-zone (top/middle only); no flicker content; loudness measured; loop-seam frame match open↔close.
- Deliver: 1080×1920 master + 720p review copy + signed URL. **No 4K.**

## Cost

ElevenLabs subscription credits (~a few hundred); $0 Veo; QA vision $0 (no Veo footage). Effectively free.

## Build results (v1, 2026-07-22 overnight)

- **Master:** `final/broken_record_v1.mp4` — 1080×1920@60, 55.92s, −16.4 LUFS. Review res only; **no 4K run.**
- **Voice casting (measured, 8 takes / 4 voices):** winner `br_sarah_s1_slow_t1` (Sarah, EL native speed 0.85, stability 0.8, no post-processing). YIN f0: final phrase = held ~B♭3 ("I am not," 0.4s hold) → C4 ("sing-") → falling-fifth cadence to F3 ("-ing."), with Sarah's own theatrical rest before "singing" — the loop unit has an internal rhythmic figure for free. River/Eric too flat; Jessica's tail wandered.
- **Loop:** 1.311s segment, 1.867s cycle (112 frames), ×12 reps, all byte-identical in the master WAV (asserted); replay bit-identical to intro (asserted). Hard cut lands the exact frame the 12th phrase ends (twin audio/video cut).
- **QA:** all 18 gates PASS — 4/4 color tags (pc / bt709 / iec61966-2-1 / bt709), faststart, rep visual identity (mean diff 0.05 = codec noise), rep audio NMSE −47.6 dB post-AAC, true digital silence at "you did.", loop seam open≈close (0.19 mean diff).
- **Cost:** ~$0 (8 short TTS casting calls on subscription credits, ~360 credits; zero Veo; zero QA-vision).
- **Review (7-day signed URL, 720p):** uploaded to `gs://vg-veo-0137184346/broken-record/broken_record_v1_review720.mp4`
- **What only the user can judge (the instrument):** does the flip land by ~rep 6, and does the replay at 39s sing. Levers if weak: more reps / longer gap / different span (S2–S4 texts unexplored) / re-cast.

## Description draft (concise)

> A voice repeats a four-word sentence twelve times. The recording never changes. Around the sixth repetition, something in you will decide it is a song. Then you'll hear the original sentence again — and lose the ability to hear it as speech.
>
> The speech-to-song illusion (Diana Deutsch, 1995), performed on you, with the receipts on screen: the pitch trace redraws the identical curve every repetition.
>
> The voice is synthetic. The illusion is yours.
>
> #audioillusion #speechtosong #perception

## Review round 1 → v2 (2026-07-23)

**v1 verdict (user, on phone):** well-made, concept liked, illusion didn't land — "sing-songy before the repetition… never really became more singing like." Diagnosis: v1 casting **maximized** notehood (held notes, slow speed, theatrical pause) = pre-spent the transformation; no distance left to travel.

**Audition rounds:** (1) A–D reel, natural-speed plain reads — user: C (Sarah natural) and D closest, still no flip. (2) Strict transformability scoring (levelness / glide / grid-fit per Tierney, Falk & Rathcke): ALL EL takes glide 12–44 st/s vs <8 needed — EL prosody is continuous micro-glide; measurement says the medium fights this mechanism. (3) VTE pivot reel built (E "unchanged" ×33, F "again" ×52, Warren protocol) as a fallback mechanism. (4) **User ran the canonical-control test** (Deutsch's official demo) and judged **C closest to the real thing → v2 built on C at their direction.** Lesson recorded: the strict metric ranked C low; the instrument outranks the proxy.

**v2:** `final/broken_record_v2.mp4` — take `br_sarah_s1_t1` (pure default synthesis, not even a speed param), segment 1.041s, cycle 1.333s, **14 reps**, gap 0.30s (the reel feel), 51.25s total, −17.2 LUFS. Note levels for this take: 52.6 / 56.0 / 57.8 st (aside wording now derived from measured count). All 18 gates pass. VTE reel parked as pocket pivot if v2 still doesn't land.

## v2.1 + 4K (2026-07-23)

- **User note on v2:** the two sentences run together → **v2.1** inserts 0.30s of true silence at the boundary zero-crossing (perceived ~0.45s with natural decay), identically in intro and replay, so replay==intro stays bit-exact and the loop is untouched. Verified: one 0.301s quiet run in the intro play; all 18 gates pass; 51.85s.
- **Honesty bookkeeping:** inserting a pause is an arrangement edit, so the claim card dropped "one take. no edits." → now two bulletproof lines ("a synthetic voice will speak. / nothing about the recording will change."). One-take provenance stays in the description/credits.
- **Native 4K:** full pipeline parameterized `BR_SCALE=2` → 2160×3840 re-render (contract layout, render geometry/type, QA dims all scale; single-frame check verified before the long encode). No ESRGAN, per house recipe for programmatic pieces.
- Build gotcha for the shelf: `set -e` + `$([ cond ] && echo suffix)` in an assignment kills the script silently when the condition is false — Ep.2's build.sh carries the same landmine. Use an `if`.

## Risks & mitigations

- **TTS prosody too dynamic to flip** → generate multiple takes/voices, score f0 plateaus, pick best; worst case the loop reads hypnotic-rhythmic rather than overtly melodic — piece still lands via replay contrast. Levers if review says weak: more reps, different span, different voice.
- **Span cut clicks** → cut at zero-crossings/silences, 3ms micro-fades baked into the segment (reps stay identical).
- **User is the instrument** → v1 ships for phone review before any upscale.
