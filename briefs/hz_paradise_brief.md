# HELLZAPOPPIN' LIVE! at The Paradise Theater
## Production brief — v1 overnight 2026-07-23/24 · **v2 rebuilt 2026-07-24 from user review notes**

**Series:** Hellzapoppin' — first episode fully helmed by Claude (creative implementation end-to-end).
**Source spine:** `~/Downloads/the-gods-spine-v1.md` (concept developed jointly in UI chat).
**Format:** 9:16, 1080x1920 native, 24fps, **71.0s** (v1 was 77.9; cap 90). No upscale (per standing rule).
**Master:** `data/workspace/hz-paradise/final/hz_paradise_v2b.mp4` (v1 master retained alongside)
**Published:** *(pending review)*

### v2 in one paragraph
All six review notes addressed: the banner now fills the frame and burns away like flash paper (real Veo);
the gods cutaways are real film with the heckler visibly enthroned in the seat the spotlight later finds;
a new seize-in-the-stands beat makes the stagehand grab legible; the hat-conjure is cut and the wind-up
reshot bareheaded (hat stays fallen on the boards); the hook now visibly RIPS him off his feet on film —
caught at the very top of the inhale, not one syllable out (Veo's added vocal muted, cut rides to the peak);
and the post-close is rebuilt around the user's palm reference — ringed trunk, terracotta pot, and a vintage
microphone the palm pointedly does not need. New darker dialogue; curtain recast DEEP (Deep Ray) with one
deliberate slip back into v1's Monty on "You always know." Palm closeup is a programmatic still-push after
Veo twice inserted a human hand tending the fronds (stills-for-stillness doctrine).

### v2 numbers
| Item | Value |
|---|---|
| Veo | 12 submissions, 64 Veo-s (incl. 1 palm reroll — the only reroll) → **$6.40** |
| Nano Banana Pro | 16 generations (full-bleed banner, gods series, anchors, palm/mic plate) → ~$2.40 |
| QA (anchor-drift 3, clip-qa 10, clone-check 5, ledgered) | → **$2.82** |
| ElevenLabs | 9 TTS takes (new dialogue + deep-curtain casting), 3 SFX — subscription credits |
| **v2 cash** | **≈ $11.62** · **cumulative ≈ $24.07 of $100** |

### v2 dialogue (post-close)
CURTAIN *(deep — Deep Ray)*: "They fed the hook again tonight." · PALM: "I know." ·
CURTAIN *(the slip — v1's Monty)*: "You always know." · PALM: "The pot gets heavier." · *snap.*

---

## The piece

An act tries to start; a heckler in the highest balcony kills it — three times, the heckles
shrinking as they grow deadlier (3.0s → 1.1s → 0.5s of audio: "Sir, I have heard finer singing
from a hinge!" → "The wire." → "No."). The stagehands drag him down; the house, having fed on
his executions, goes silent with hunger for his next one. At the top of his enormous wind-up,
the hook takes him — not one syllable escapes. The spotlight climbs the empty house to his
empty seat in the gods. After hours, the curtain (Loading Dock's face, same fabric-fold
physiognomy) asks the potted palm what it thought of the show. The palm — the series' first
venue, returned as furniture — says "No." Work light snaps off.

**Venue rename** (restriction: not "The Gods", must end in "Theater"): **The Paradise Theater.**
*Paradis* is the French theater term for exactly those highest cheapest seats (Les Enfants du
Paradis); the brief's joke — the venue named for the people farthest from the stage — survives
one layer down, and the banner reads HELLZAPOPPIN at Paradise. The word "gods" never appears
in a prompt (literal-deity RAI risk); the balcony is "the highest balcony" throughout.

## Numbers

| Item | Value |
|---|---|
| Veo | 12 clips, 74 Veo-s, **zero failed submissions, zero rerolls** → **$7.40** |
| Nano Banana Pro | ~22 generations (plates, characters, anchors, spotlight series) → ~$3.30 |
| QA (clip-qa / clone-check / anchor-drift, ledgered) | 32 calls → **$1.75** |
| ElevenLabs | 13 TTS takes, 3 music stings, 9 SFX — subscription credits |
| **Cash total** | **≈ $12.45** of $100 budget |

## Review links (7-day)
- 720p review copy and debug-overlay copy uploaded to `gs://vg-veo-0137184346/hz-paradise/`
  (signed URLs in session notes; regenerate anytime with `tools/gcp/share.cjs`).

## Casting
- **Heckler:** Daniel (`onwK4e9ZLuTAKqWW03F9`) — dry, unhurried; distance chain
  (highpass 280 / lowpass 4200 / hall echo) for the balcony acoustic. Bill takes archived.
- **Curtain:** Monty (`tUVMjP56ZNYXlKLsRXbo`) — spectral centroid 3566 vs archived Loading Dock
  curtain 3547 (0.5% — either the original voice or indistinguishable). Original voice ID was
  unrecoverable from the legacy job store.
- **Palm:** River (`SAz9YHcvj6GT2YYXdXww`) — small, papery, unbothered. Does not imitate the
  heckler's "No." — same word, different instrument.

## Gate results → treatments (no auto-rerolls; ladder honored)
| Clip | Flags | Treatment |
|---|---|---|
| s1 tenor | clone twin during exit (6.6s+), both detectors | trim to 0.2–5.8 (dup excluded); deflate→cut is faster comedy anyway |
| s2a tableau | "magician moves" = my over-strict context; he performs a presentation walk | keep 0–2.05; cut early so his pose matches s2b's start (anti-teleport) |
| s2b drop | "ghosting" = motion blur + upright-pivot recovery (clone-check clean) | keep 0.3–2.4; her scramble-collapse serves "The wire." |
| s2c house turn | crowd morph in tail; unprompted camera pull-back | keep 2.0–4.8 — the pull-back reads as the house opening toward the gods |
| s3 placard | placard-scale morph early; edge-double at 6.4 | keep 2.6–6.3 (both excluded); placard hides his whole torso — a gift |
| s4a charge | extra figure early, smoke-ghost, late manager-twin | keep 0.2–4.6, ends on the manager alone holding his point (the ellipsis) |
| s4b deposit | hat flicker inside the stumble | keep; invisible at speed |
| s5a house lean | crowd morph tail | keep 0.2–2.3 (jeers→hush) |
| s5b wind-up | "mask-like pale face" | keep full 8s — that IS the heckler's design |
| s6 hook t1/t2 | both takes walk him off politely instead of yanking | **edit-around:** t2 pole-arrival 0–1.15 → hard cut → t2's own empty tail, snatch SFX on the cut. The yank happens between frames |
| s8 post-close | fold-mouth shifts at 5.5–6.5 | keep — the curtain is speaking there |

## Audio design (the engine)
Stings die mid-phrase at each heckle; heckles land in the silence they create. House sound
dies to true silence at the hook and never returns — spotlight climb, seat, black are silent.
Post-close is settle-creaks + one pipe clank. No stinger on the hook (one wood-slide-snatch,
per spine). Whisper QA on the master: all 7 lines land within 0.2s of plan; four phantom
"No."s in the transcript proved to be a Whisper repetition-loop hallucination (verified empty
in isolated re-transcription) plus one legitimate stagehand "OOF."

## Decisions queued for morning (full list: workspace `DECISIONS.md`)
1. Venue name "The Paradise Theater" — approve or rename (banner regen is one nano + rebuild).
2. Suno→ElevenLabs sting swap (consolidation rule) — confirm.
3. Blind voice casting (I can't listen): Daniel/Monty/River — swap is a one-line edit-script
   change; all alternates preserved in `audio/casting/`.
4. Hook staging via cut rather than in-frame yank — watch and judge.
5. s7 spotlight-travel pacing (2.2s/station) and the gray→warm regrade of the gods cutaways.

## Workspace
`data/workspace/hz-paradise/` — refs/ frames/ clips/ prerender/ audio/ final/ scratch/.
Edit script: `scratch/edit_v1.cjs` (segments + layers tables; EDIT_LOG.md has timecode map).
Debug copy for trim dictation: `final/hz_paradise_v1b_debug.mp4` (edit-time overlay).

## Lessons (recorded to memory)
- Fast-removal gags: Veo fills 4s by *walking* the removal — stage the mover's arrival on
  film, put the removal itself in a hard cut with SFX. Faster, funnier, free.
- anchor-drift's "no visible mover" rule caught exactly this before the first submission —
  the pole-added frame A is why both takes at least delivered a usable arrival.
- Whisper repetition-loop: repeated short words ("No.") prime phantom duplicates in later
  sparse audio — verify with isolated-window re-transcription before touching the mix.

## YouTube description (draft, per concise-descriptions convention)
The act everyone wanted is the one the show devours before it starts.
HELLZAPOPPIN' LIVE! at The Paradise Theater — where the seats talk back.
Creative direction: Stephen (a][ productions) · Implementation: Claude Code ·
Video: Google Veo · Frames: Nano Banana Pro · Voices & music: ElevenLabs · Assembly: ffmpeg
#vaudeville #aifilm #comedy #shorts
