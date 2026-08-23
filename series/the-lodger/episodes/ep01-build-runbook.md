# EP 1 BUILD RUNBOOK
> **v2 RESTRUCTURE BUILT 2026-08-22** — 60.75s at `final/ep01_v2_review.mp4`; queue at
> `flag-queue-v2.md`. Notes for next time: (1) `gate-runner` now **merges** verdicts at save time
> instead of rewriting the manifest wholesale — it previously clobbered concurrent edits when run
> in the background, silently reverting trim windows; (2) it also has a `--shot ID` flag for
> gating one clip; (3) `gen-runner` supports a **per-shot** `resolution` key; (4) `audio-anchor`
> ducks under *all* non-italic captions now, not only `D*`-sourced ones; (5) nano 429s on
> back-to-back calls — space them.

# (v1 runbook below) — "The Stranger at Dusk"
### Prep completed 2026-08-20. Production session RUN 2026-08-20 (autonomous): **draft v1 built — 63.5s** (`data/workspace/lodger-ep01/final/ep01_review.mp4` + debug + 720p signed URL). Voice cast: sarah (delegated GATE 0; reversible). S6+S8 rerolled on spec failures (composed anchors), S12 protected retake used (output-RAI → transaction recast, dialogue verbatim). Decisions + evidence: `data/workspace/lodger-ep01/flag-queue.md`. **Next: GATE 2 — Stephen watches.** Sound draft is IN the cut (stems re-run cheaply after picture notes).

Everything creative and structural is locked and QA'd. The build is: pick a voice, generate
audio, run 12 Veo gens through the kit, gate, cut, mix, review. Zero Veo dollars spent so far.

## State of the world

| Thing | State |
|---|---|
| Shooting script | `ep01-the-stranger-at-dusk.md` v1.4 (era: summer 1934, eastern NC) |
| **Manifest (drives everything)** | `data/workspace/lodger-ep01/episode.json` — 12 Veo shots + 1 still, prompts final, planned 62s cut, $9.88 Veo projected vs $22 cap |
| Canon (13 files) | `series/the-lodger/canon/` — cast refs (Vascari ×3, Cora ×3 aged-down), house plate, entry hall, parlor, chair still, title ref, locks.md, stock-shots.md |
| Anchors (4, all QA'd) | `data/workspace/lodger-ep01/refs/` — S7_A + S7_B (book-end, anchor-drift **PASS**), S12_first, S9_first_mcu. frame-qa verdicts recorded; one caveat below. |
| Production kit (smoke-tested) | `tools/vertical/`: ep-scaffold · text-pass · gen-runner · gate-runner · assemble-ep · ep-report + `series/the-lodger/series-config.json` |
| VO audition (8 samples) | `data/workspace/lodger-ep01/scratch/vo-audition/` — see GATE 0 |
| Spend so far | nano 30 ≈ $4.50 · QA ≈ $1.60 · EL plan credits · **Veo $0.00** |

## The build sequence

**GATE 0 — Stephen casts Cora's voice.** Play the 8 samples (V1 hook + V7 button per voice):
`open data/workspace/lodger-ep01/scratch/vo-audition/` — candidates:
- **sarah** (`EXAVITQu4vr4xnSDxMaL`) — young, reassuring, confident: the *capable* read
- **alicia** (`OOk3INdXVLRmSaQoAX9D`) — calm narrative: the *telling-it-afterward* read
- **jessica** (`cgSgspJ2msm6clMCkdW9`) — youngest, brightest: the *romance-lead* read
- **merv** (`nCUo6wOgqVDAktRxhDA4`) — intense young: the dark horse, most *guarded*

No true Southern female in the cached roster — if none of these sit right, search the EL voice
library for a "US southern female narrative" voice and add it. Write the winner into
`series-config.json → voices.cora_vo`. Note: the intimate/low-energy profile slows delivery
(speed_factor 0.855) — if reads feel draggy, regenerate with `speed: 1.1–1.15`.

**1. Final VO (MCP `generate_tts`, 7 lines from manifest `vo[]`).** Moods: V1–V4
intimate/t.55/e.25 · V5–V6 mysterious/t.6/e.3 · V7 intimate/t.7/e.15. Save paths into
`vo[].file` AND as `audio[]` stems `{file, t, gain_db: 0}`.

**2. Music + SFX (MCP).** Prompts live in manifest `audio[]`: theme_lamplight
(`generate_music`, 75s), rain_bed (EL SFX caps ~20s — generate loopable, tile ×4 in the mix),
knock_triple, coin_set, lamp_gutter, sting_dread (`generate_sound_effect`). Record file paths.

**3. Veo generation (the kit + MCP).**
```
python3 tools/vertical/gen-runner.py --series series/the-lodger --manifest data/workspace/lodger-ep01/episode.json --plan     # sanity
python3 tools/vertical/gen-runner.py ... --specs                                                                              # writes scratch/submit-specs.json
# agent: submit each spec via MCP submit_veo_generation (space ~30s apart), then:
python3 tools/vertical/gen-runner.py ... --record S1=<op> S2=<op> ...                                                         # stamps ops + costs
python3 tools/vertical/gen-runner.py ... --poll                                                                               # polls + downloads clips/
```
Notes: 8s gens (S7/S8/S12) need the GCS storageUri path — config's `veoGcsBucket` handles it.
A silent RAI trip looks like a hang (toggle Vertex AI API per memory to reconcile). Poll caps at
~17 min/run — rerun on TIMEOUT. Every submission attempt is costed on `--record`.

**4. Gate.**
```
python3 tools/vertical/gate-runner.py --manifest data/workspace/lodger-ep01/episode.json
```
→ normalize + probe + clip-qa (per-shot contexts baked in) + clone-check (motion shots;
S7 expects 2 subjects) → `gate-report.md`. Dialogue shots (S8/S9/S12): MCP
`analyze_dialogue_clip` vs the manifest line; record in `verdicts.dialogue_check`. On any clone
flag: full-res frames are the arbiter, never tool confidence.

**GATE 1 — flag queue.** Keep / edit-around / retake per report. **S12 carries the one
pre-authorized retake** (`--retake S12`); anything else needs Stephen. Trims → update `use`.

**5. Cut + text.**
```
python3 tools/vertical/assemble-ep.py --series series/the-lodger --manifest .../episode.json --out final/ep01_picture.mp4
# re-anchor vo[].t / captions / sfx syncs from SRC timestamps against computed_timeline (audio-src-anchor)
python3 tools/vertical/text-pass.py --series series/the-lodger --manifest .../episode.json --video .../final/ep01_picture.mp4 --out .../final/ep01_review.mp4
python3 tools/add-timestamp.py data/workspace/lodger-ep01/final/ep01_review.mp4
node tools/gcp/share.cjs <720p copy>            # signed URL for remote review
```

**GATE 2 — Stephen watches** (debug copy; notes as `src X, edit Y`). Apply → picture lock.

**6. Sound + master.** `assemble-ep ... --stems` (mix plan lives in manifest `audio[]`:
theme in ~9s, OUT at the condition, sting at black; rain bed under all; duck −6 dB under
speech; **no footstep foley for him, ever** — S10 note). Then text-pass onto the mix → master.

**7. Wrap.** `ep-report --write` · BQ reconcile next day (`tools/gcp/bq.cjs`) · update series
README index + memory · commit. **GATE 3 — final approval** → upscale only after approval
(no-4K-before-review) → upload → add `**Published:** URL` to the brief → archive-workspace.

## Known caveats (decided, not surprises)

1. **S7_B has no visible door leaf** (swung out of view) — the swing is Veo's to render;
   anchor-drift passed it as motivated. Watch the swing at gate; fallback (in manifest notes):
   regen S7_B with the leaf flat against the right wall.
2. **S2/S6 run anchorless by design** (she's small/turned/from-behind) — if identity breaks,
   compose first-frames from canon and flag for a decided retake.
3. **Veo native voice varies per gen** — his descriptor is in every dialogue prompt; keep lines
   short; EL dub-over is the edit-rescue, not a re-roll chase.
4. **Veo static starts** — S5/S13 have micro-motion written in; expect ~1s lead-in, absorbed by
   `use` windows.
5. Prompts are RAI-clean; the S9 "steps back to admit" beat deliberately never voices an
   invitation (threshold lore stays open).
