# THE LODGER — Production Cycle (tooling spec v1, 2026-08-19)

> **STATUS 2026-08-20: BUILT.** All six tools exist in `tools/vertical/` and are smoke-tested
> (text-pass validated pixel-true vs the locked title treatment; assemble produced a clean
> 1080×1920 @ 24/1 concat with still-zoompan + black segments; gate ran plumbing on an archived
> clip; gen-runner --plan expands the real Ep 1 manifest to $9.88 projected). Ep 1 shakedown is
> next — start at `episodes/ep01-build-runbook.md`. One design delta from this spec: Veo accepts
> only first/last-frame anchors (no style refs), so identity on anchorless shots rides on locks;
> and submission stays agent-side via MCP (gen-runner does specs/record/poll around it).

**Goal:** 20–40 episodes means the *cycle* is the product. We build the tooling first, then run
Episode 1 through it as the shakedown. Every episode after that should be: write script →
fill manifest → run the kit → make the human calls the kit surfaces → ship.

**Design principles**
1. **Manifest-driven.** The shooting script stays a human document; a per-episode
   `episode.json` is the machine-readable source of truth the tools consume. No tool ever
   parses prose.
2. **Reuse, don't duplicate.** The repo already has the hard parts: Veo submit/poll
   (`reference_veo_submit_pipeline`: MCP `submit_veo_generation` → poll-dl/`shot.cjs`), QA
   (`tools/clip-qa.py`, `tools/clone-check.py`, `tools/frame-qa.py`, `tools/anchor-drift.py`),
   `normalize-clip`, `add-timestamp.py`, `tools/gcp/share.cjs`, EL via MCP
   (`generate_tts/music/sound_effect`), nano via `tools/nano-banana.cjs`, `costlog.py`/BQ
   reconcile. The kit is orchestration + config, not new capability.
3. **Doctrine encoded, not re-argued.** One gen per shot; no auto-reroll (regen requires an
   explicit `--retake SHOT` and either the shot's `protected_retake` flag or an override);
   clone-check mandatory on `motion: true` shots; gates flag + recommend, humans decide.
4. **Human gates are features.** Casting, VO auditions, keep/edit-around/reroll calls, and the
   final watch stay manual on purpose. The kit's job is to make each gate a 5-minute decision
   with everything laid out.

## Layout

```
tools/vertical/                    # generic engine (future series reuse it)
  ep-scaffold.py                   # new episode: workspace dirs + manifest from template
  gen-runner.py                    # manifest → Veo submissions → poll → clips/ + job ids/costs
  gate-runner.py                   # per-clip acceptance gate → verdicts + gate-report.md
  text-pass.py                     # captions + title/end stamps (PIL soft-shadow renderer)
  assemble-ep.py                   # timeline → concat filter master + debug copy + 720p share
  ep-report.py                     # status + spend rollup → appends to episode doc
series/the-lodger/
  series-config.json               # canon paths, locks, caption/title style, voices, caps
  episodes/epNN-*.md               # human shooting scripts (unchanged)
data/workspace/lodger-epNN/
  episode.json                     # per-episode manifest (the machine source of truth)
  refs/ frames/ clips/ final/ scratch/
```

## series-config.json (sketch)

```json
{
  "series": "the-lodger",
  "format": {"w": 1080, "h": 1920, "fps": 24, "target_seconds": [60, 90]},
  "era_suffix": "Rural eastern North Carolina, summer 1934, Great Depression era, period-correct detail. Cinematic photoreal, shallow depth of field, tall 9:16 composition, subject centered. No on-screen text, no titles, no captions, no watermarks.",
  "canon_dir": "series/the-lodger/canon",
  "locks": {"VASCARI_LOCK": "<verbatim>", "CORA_LOCK": "<verbatim>"},
  "caption_style": {"font": "Hoefler Text", "band": [0.55, 0.65], "fill": "#F1E9DA",
                     "vo_italic": true, "max_chars": 30, "shadow": {"blur": 7, "dx": 4, "dy": 5}},
  "title_style":   {"main_pt": 0.062, "sub_pt": 0.0205, "y_main": 0.578, "y_sub": 0.636},
  "voices": {"cora_vo": "TBD after audition"},
  "audio": {"theme": "canon/audio/theme_lamplight.mp3", "stings": {"dread": "...", "swell": "..."}},
  "budget": {"per_episode_usd": 22, "veo_overhead": 1.3},
  "veo": {"model": "veo-3.1-prod", "generateAudio": true, "aspect": "9:16"}
}
```

## episode.json (manifest sketch)

```json
{
  "episode": 1, "slug": "lodger-ep01", "title": "The Stranger at Dusk",
  "shots": [{
    "id": "S7", "seconds": 8, "use": [0.0, 5.5],
    "prompt": "…{{VASCARI_LOCK}}…",             
    "refs": ["canon/char_vascari_full.png", "canon/env_entry_hall.png"],
    "anchors": {"first": "refs/S7_A.png", "last": "refs/S7_B.png"},
    "motion": true, "dialogue": null, "protected_retake": false,
    "qa_context": "exactly two people — one woman seen from behind, one man in the doorway; no third figure; no reflections in the door glass; door opens once",
    "status": "pending", "job_id": null, "verdicts": {}
  }],
  "vo":       [{"id": "V1", "text": "Papa always said nothing good knocks after dark.", "t": 0.0}],
  "captions": "derived from vo[] + shots[].dialogue unless overridden",
  "stamps":   {"title_over": "S1", "title_at": [4.0, 7.5], "end_card": "Episode Two — House Rules"},
  "audio":    [{"type": "sfx", "name": "triple_knock", "sync": "S5.flinch"}],
  "timeline": [{"clip": "S0:=S7[2.5s excerpt]"}, {"clip": "S1"}, "…"]
}
```

## Components — responsibilities, reuse, build order

| # | Tool | Does | Reuses | Notes |
|---|---|---|---|---|
| 1 | `ep-scaffold.py` | workspace dirs + manifest template + doc stub | workspace convention | trivial, build first |
| 2 | `text-pass.py` | burn captions (VO italic / dialogue regular) + title & end stamps from manifest onto rendered picture | PIL soft-text (promoted from ep01 scratch) | **zero-spend testable today** on canon plates |
| 3 | `gen-runner.py` | expand prompt templates (`{{LOCK}}` + era suffix), submit spaced, poll, download, write job_id/cost/status back to manifest | MCP `submit_veo_generation`, poll-dl/`shot.cjs` pattern | `--plan` prints without submitting; `--shot S7` targets one; `--retake` guarded per doctrine; pre-flight `frame-qa`/`anchor-drift` on any shot with anchors |
| 4 | `gate-runner.py` | per new clip: normalize → clip-qa (with manifest `qa_context`) → clone-check if `motion` → transcribe-vs-dialogue if dialogue → verdicts into manifest + `gate-report.md` (flag, timestamp, strip path, recommended treatment) | clip-qa.py, clone-check.py, normalize-clip, MCP transcribe | report IS the keep/edit/reroll queue for Stephen |
| 5 | `assemble-ep.py` | timeline → concat **filter** (24fps, stereo, setpts hygiene per ffmpeg-knowledge) → picture lock → audio layering (VO/SFX/theme, −6 dB duck under speech) → master + `add-timestamp` debug copy + 720p `share.cjs` link | splice/concat lessons, audio-src-anchor rule | audio times recomputed from shot+src anchors after trims |
| 6 | `ep-report.py` | shot status table + spend rollup (manifest costs + cost-ledger QA calls + BQ note) + gate summary → appends to episode doc + memory-ready summary line | cost-report.cjs, bq.cjs | run at wrap |

**Build order = the table order.** 1–2 are pure-local (buildable and testable with zero spend);
3–4 get dry-run modes tested against archived clips (e.g., a personal-best clip re-gated) so the
wiring is proven before a single new Veo dollar; 5–6 close the loop.

## The cycle, once built (per episode)

1. Write `epNN` shooting script (human) → fill `episode.json`.
2. `ep-scaffold` → nano anchors/plates as needed (nano stays interactive — it's creative).
3. **GATE (human):** any new canon (faces, sets, wardrobe) → Stephen approves.
4. EL: VO lines + any new SFX (voice fixed in series-config after the Ep 1 audition).
5. `gen-runner` (pre-flights anchors, submits, polls, downloads).
6. `gate-runner` → **GATE (human):** keep / edit-around / retake queue.
7. `assemble-ep` → **GATE (human):** watch debug copy, give `src X` notes → trims → re-assemble.
8. Sound pass → master → `ep-report` → commit + archive per convention.

## Acceptance criteria (the Ep 1 shakedown)

- Episode 1 is built end-to-end with **every generation, gate verdict, trim, and dollar
  recorded in `episode.json`** — no state living only in chat scrollback.
- Manual touchpoints during the run ≤ the four GATEs above.
- A second episode can be started by copying the manifest template and writing prose — no code
  changes required. (That's the real test; Ep 2's script exists by then.)

## Open items

- VO voice audition (needs Stephen's ears) — happens at cycle step 4 of the Ep 1 run.
- S7 book-end anchors — built during the Ep 1 run at step 2 (all plates are already canon).
- `series-config.json` gets written when tooling starts; locks copy from `canon/locks.md`.
