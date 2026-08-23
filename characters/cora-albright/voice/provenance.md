# Cora voice — clone provenance

**Current voice:** `qgVHCjozdBwKCEAWjZCa` — "Cora Albright (Lodger native v2)", created
2026-08-22. **Status: APPROVED + LOCKED (Stephen, 2026-08-22).** This is Cora's voice for
series VO and dub-rescue going forward; changes need Stephen's sign-off (casting tier).

## Why a clone of a Veo voice

Stephen liked Veo's native read on lodger-ep01 S9 ("Three dollars a week, with board.
Supper's at six.") better than any EL library voice, and wanted that Cora for series VO and
future dub-rescue. Veo native voices drift between generations, so the voice was captured
once into an EL instant clone rather than re-rolled per episode.

## Sample set (v2)

All samples cleaned with EL Voice Isolator (rain/room removed; spectrally verified — black
gaps, harmonics intact). Speaker match verified with resemblyzer d-vector cosine.

| file | origin | line | cos vs S9 |
|---|---|---|---|
| `01_s9_three_dollars.wav` | Ep1 S9 gen (the reference) | "Three dollars a week…" | 1.000 |
| `02_h1_six_rooms.wav` | harvest H1 | "Six rooms, and a porch…" | 0.860 |
| `03_h4_cicadas.wav` | harvest H4 | "Summer nights, the cicadas…" | 0.798 |
| `04_h5_ledger.wav` | harvest H5 | "Papa kept the ledger…" | 0.822 |
| `05_h6_mud_road.wav` | harvest H6 | "When it rains, the road…" | 0.809 |

~27s voiced total. **Rejected spares** (still same-voice range, kept on disk at
`data/workspace/lodger-ep01/scratch/voice-harvest/`): H2 (0.770), H3 (0.782) — lowest
similarity + lowest mutual coherence; available if the clone ever needs more data.

## Harvest recipe (repeatable for any native-voice character)

1. Re-use the exact conditions that produced the loved voice: same first-frame anchor
   (`refs/S9_first_mcu.png`), same character lock verbatim, same voice descriptor ("a soft
   North Carolina accent, quiet and unhurried"), same scene/lighting register.
2. Stage a **quiet room** — prompt "Sound: her voice close and quiet in a still room; no
   music; no rain" — so takes come back near-clean.
3. Six 8s Veo Quality gens, phonetically varied in-character lines (~$6 attempt-counted).
   All six returned word-perfect.
4. EL Voice Isolator per take (min input 4.6s; returns 320kbps mono mp3).
5. resemblyzer cosine vs the reference + full pairwise matrix; keep the coherent cluster,
   drop outliers. Same-speaker heuristic: ≥0.75-0.80.
6. IVC with the curated set via `POST /v1/voices/add`.

## History

- **v2** `qgVHCjozdBwKCEAWjZCa` (2026-08-22) — 5 samples, ~27s. **Current, approved.**
- **v1** `3BzNSK5G0D5BPbRDtoDZ` (2026-08-22) — S9-only 4s seed. Proof of concept; Stephen:
  "I dig both [V1/V7 reads]." Deleted from EL after v2 approval (recreatable from
  `samples/01_s9_three_dollars.wav`).
- **sarah** `EXAVITQu4vr4xnSDxMaL` (EL library) — draft v1 VO cast, rejected 2026-08-22.
