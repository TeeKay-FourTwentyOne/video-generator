---
name: clone-check
description: Scan a generated video clip for SUBJECT DUPLICATION — a clone / ghost-twin / merge / extra-limb where Veo briefly renders a SECOND copy of the same subject during fast motion (standing, crossing frame, turning) that splits off and merges back. Lives ~0.3-0.6s inside a motion window, so even-cadence QA reads it as "a person walking" and lets it through. Use after every Veo generation, alongside clip-qa, before accepting the clip. Motion-gated dense sampling + a high-recall duplication-specific vision pass catches what clip-qa misses.
allowed-tools: Read, Bash
---

# clone-check

Veo-style generators, during **fast subject motion**, sometimes render a **second copy of the same subject** — a duplicate body / ghost twin that peels off the original and **merges back** a few frames later, or a doubled / extra limb that flickers in mid-gesture. It is one of the most common Veo failures on shots where a character **stands up, crosses the frame, or turns quickly**.

It is also one of the easiest to **miss in QA**, because it is *transient* (≈0.3–0.6s) and lives *inside* a motion window:

- **clip-qa misses it.** clip-qa samples evenly at ~0.3s and runs a deliberately motion-*tolerant*, high-precision prompt ("do NOT flag normal motion… prefer no flag"). A clone that spans 2–3 frames of a fast move gets rationalized as "the man walking." (On the validation clip below, clip-qa *and* a downstream adversarial reviewer both let it through, calling it "physique drift.")
- **ffmpeg can't see it.** No scene-cut, no freeze, no black frame — the motion is continuous.
- **A motion-strip eyeballed at sparse cadence misses it.** The double falls between your thumbnails, or shows in one frame that reads as motion blur.

This skill is the dedicated catcher. It (1) builds a **motion-energy curve** for the clip, (2) finds the **high-motion window(s)** where clones happen, (3) **densely re-samples** them (~0.12s) so a transient double lands in several consecutive frames, and (4) runs a **duplication-specific, high-recall** vision pass that *counts the subject per frame* and rules out blur/reflection/shadow.

## When to use

- **After every Veo generation that contains subject motion** — anyone who stands, walks, lunges, turns, reaches across frame, or where two of the same character could plausibly be confused. Run it *with* clip-qa, before the clip is accepted into the edit (see `.claude/rules/clip-acceptance-gate.md`).
- **Whenever a clip "feels" briefly wrong on a move** but single frames look fine — this localizes it.
- Skip it only for shots with **no subject motion at all** (a held static tableau, a landscape, a programmatic/stills clip).

## Quick start

```bash
# Single-subject shot. Context fixes the expected count and names any reflective surface.
python3 tools/clone-check.py data/workspace/<proj>/clips/shotN.mp4 \
  --context="A man stands and crosses to the window. Exactly ONE man the whole time. No mirror." \
  --fail-on=medium
# exit 3 → duplication at/above medium → decide treatment (trim or reroll); exit 0 → clean, accept

# Two intended characters? Tell it, so a real second person isn't flagged.
python3 tools/clone-check.py clip.mp4 --expected=2 --context="Two dancers, a man and a woman."

# Suspect a very brief artifact, or want belt-and-suspenders coverage:
python3 tools/clone-check.py clip.mp4 --whole --step=0.1
```

## How it works (and how to tune it)

| stage | what it does |
|---|---|
| motion profile | extracts coarse frames (`--coarse-step`, 0.30s), computes mean abs pixel-diff vs the previous frame → an energy curve. Free, local. |
| windowing | thresholds the curve at `median + K*MAD` (`--motion-k`, default 1.0). Contiguous hot samples merge into windows, padded by `--window-margin` (0.4s). |
| dense sampling | re-samples inside the windows at `--step` (0.12s) with **accurate** timestamps, capped at `--max-frames` (48), prioritizing frames nearest the motion peak. |
| vision | tiles dense frames into labeled grids (≤15 each) and asks Claude to **count distinct instances of the subject per frame** and flag count > expected, ruling out blur/reflection/shadow. |

- **Catching more (high recall):** lower `--motion-k` (e.g. 0.5) to open more windows, or `--whole` to sample the entire clip. Lower `--step` (0.10) for sub-0.4s artifacts.
- **Cost / speed:** the motion pass is free; the vision pass is Opus-billed (~$0.05–0.12/clip, 1–3 grids). `--model=sonnet` is cheaper but, as with clip-qa, treat a *clean* Sonnet result as advisory.

## Flags

| Flag | Default | Purpose |
|---|---|---|
| `--expected=N` | 1 | Expected count of the primary subject in frame. |
| `--step=S` | 0.12 | Dense sample interval. Lower catches briefer doubles. |
| `--coarse-step=S` | 0.30 | Motion-profile interval. |
| `--motion-k=K` | 1.0 | Window sensitivity (median + K·MAD). Lower = more windows. |
| `--window-margin=S` | 0.4 | Padding around each motion window. |
| `--whole` | off | Ignore gating; densely sample the whole clip. |
| `--max-frames=N` | 48 | Cap on dense frames (chunked into grids of 15). |
| `--context[-file]` | — | Intent context: expected count + any intended 2nd character + presence/absence of a mirror. |
| `--model / --model-id` | opus | Vision model. |
| `--save-strip / --no-save-strip` | adjacent `<name>.clone-strip[-N].png` | Save the dense composite(s) — **look at these when a flag is ambiguous.** |
| `--json` | off | JSON only. |
| `--fail-on=LEVEL` | — | Exit 3 at/above `high\|medium\|any`. |

Exit codes match clip-qa: `0` clean · `1` API/internal · `2` usage · `3` doubling at/above `--fail-on`.

## Output

```json
{
  "subject": "the man at the table",
  "expected_count": 1,
  "max_count_observed": 2,
  "doublings": [
    {"timestamp_range": [1.85, 2.33], "peak_count": 2, "kind": "clone_body",
     "severity": "high", "confidence": 0.95,
     "ruled_out": "not blur — two separate heads, each with its own posed arms, ~1m apart",
     "description": "A second copy of the man appears at frame-right and merges with the original by 2.3s."}
  ],
  "clean_ranges": [{"start": 0.0, "end": 1.6}],
  "recommendation": "regenerate"
}
```

**`kind`:** `clone_body` (full duplicate) · `ghost_twin` (faint/partial split) · `merge` (two converge into one) · `extra_limb` (duplicated arm/leg). **Timestamps are clip-local** (0-based) — add the shot's start offset for the assembled timeline.

## Treatment vocabulary (decide AFTER it flags — do not auto-reroll)

- **`trim_before:<t>` / `trim_after:<t>`** — the double is confined to one end; cut to the clean side. Cheapest fix; often the double is during an entrance/exit you can lose. *(For mine-too shot6 the double sits in the middle of the cross-to-window action, so trimming around it loses the blind-pull — hence "regenerate" there. But you can also re-cut the shot to end before the stand, or hard-cut to a closer angle.)*
- **`regenerate`** — the double is mid-essential-action. Re-roll the shot; to *prevent* recurrence, slow the move (it's fast lateral motion that triggers cloning), split the stand and the cross into two shorter generations, or book-end with first+last anchors that pin a single body through the move.
- **Per doctrine** (`no-auto-reroll`), the gate **surfaces** the flag with its timestamp and a recommended treatment; the keep / edit-around / reroll call is made deliberately, not silently.

## Disambiguation & known limits

- **Motion blur is the main false-positive risk.** The prompt rules it out (a real clone has its *own* head and separately-posed limbs in a *different* position; blur is one head with a directional smear), and dense sampling helps — but when a flag is borderline, **open the saved `.clone-strip` and confirm two distinct bodies** before spending a reroll. (See the `clipqa-motionblur-falsepos` lesson.)
- **Reflections:** if the shot has a mirror / window-as-mirror / water, **say so in `--context`** so a legitimate reflection isn't read as a twin.
- **Motion gating can miss a clone in a low-motion frame** (rare — clones ride motion). If a clip feels wrong but comes back clean, re-run with `--whole --step=0.1`.
- **Single-clip only**, like clip-qa. Cross-shot continuity is `anchor-drift`/`splice`.

## Validated

Built and validated on **MINE TOO shot6** (2026-06-28):
- **True positive:** flagged `clone_body` **high**, conf 0.95, at **1.85–2.33s local (33.9–34.4s assembled)** — a second copy of the man entering frame-right and merging as he crosses to the window. This is the exact artifact a human reviewer caught and that clip-qa + an adversarial frame reviewer both **missed** (read as "physique drift").
- **No false positives:** shot1 (near-static), shot5 (a real reach-and-place move), shot7 (seated) all returned `max_count 1`, zero doublings, `use_as_is` — so it does not cry wolf on genuine motion.

## Integration

- **`clip-qa`** — general anomaly scan (materialization, ghost objects, flicker). Runs the same step; **does not reliably catch subject duplication during motion — that's this skill's job.** Run both.
- **`anchor-drift`** — pre-generation frame-pair gate (slide/pop). clone-check is post-generation.
- **`.claude/rules/clip-acceptance-gate.md`** — the per-generation gate that sequences anchor-drift (pre) → clip-qa + clone-check (post) → keep/trim/reroll, before any clip enters the edit.
