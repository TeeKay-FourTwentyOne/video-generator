# Clip Acceptance Gate

**Every Veo generation passes this gate before it is accepted into the edit.** The gate is a *discovery* step — it surfaces defects with timestamps and a recommended treatment so a keep / edit-around / reroll decision is made deliberately. It does **not** auto-reroll (see `no-auto-reroll`).

The motivating failure: a transient **subject-duplication clone** in MINE TOO shot6 (a second copy of the man merged into him over ~0.5s during a cross-frame move) survived a full review pass — eyeballed motion-strips, `clip-qa`, *and* an adversarial frame reviewer all missed it, because it lives inside a fast-motion window. Detectors that sample evenly and tolerate motion can't see this class. The gate exists so it can't ship silently again.

## The gate, per clip

### Before generating (frame-only — zero Veo spend)
1. **`frame-qa`** — each anchor frame vs its canonical refs (wardrobe/plate/prop drift).
2. **`anchor-drift`** — the anchor *pair* (first→last) and any hard-cut boundary (slide / pop / materialize).

Fix on the frames and re-gen the frames; never spend a Veo second on an anchor pair that fails these.

### Generate
Generate directly on **Quality** (per `skip-fast-draft`). One generation per shot (per `autonomous-build-doctrine`).

### After generating, BEFORE accepting the clip
Run, in order, and record the verdict per clip:

| # | Check | Tool | Catches | Run when |
|---|---|---|---|---|
| 1 | container/encode | `normalize-clip`, `analyze-clip` (ffmpeg) | wrong bars/fps/black/freeze | always (cheap) |
| 2 | general anomalies | **`clip-qa`** | object materialize/vanish, ghost objects, flicker, impossible trajectory | always when building autonomously; on motion/VFX shots even under user-review |
| 3 | **subject duplication** | **`clone-check`** | clone / ghost-twin / merge / extra-limb during motion | **any shot with subject motion** (stand, walk, turn, reach across frame) — mandatory; this is the class a human eye and clip-qa both miss |
| 4 | dialogue | `transcribe` / `analyze_dialogue_clip` | wrong/garbled/missing line | any shot with native Veo dialogue |

`clip-qa` and `clone-check` are **complementary, not redundant** — clip-qa is general + high-precision (motion-tolerant, so it lets clones through); clone-check is duplication-specific + high-recall (motion-gated dense sampling). Run **both**.

**Persistent set-dressing & props (the MINE TOO shot5 picture-frame miss).** clip-qa catches a prop *materializing / morphing / multiplying within a clip* — **but only if told it shouldn't be there.** Two process rules:
1. **Feed clip-qa explicit "what should NOT be present" context**, not just what should. clip-qa's default bias is to assume an occluded/early-frame object was always there; naming the empty surface ("the windowsill is EMPTY in the establishing shots — no frame should appear/multiply/morph") flips a silent pass into a HIGH flag.
2. **A prop that's absent in the establishing shots but present after a detour reads as a POP across the re-establishing cut** — single-clip clip-qa can't see that. Run **`anchor-drift --mode=across-cut`** comparing the **establishing interior frame vs the re-establishing shot's first anchor**, with `--static="the <surface> and its dressing (count/positions)"`. If you deliberately add set-dressing mid-piece, **seed it into the establishing frames too**, or it pops.

### Decide treatment (the keep / edit-around / reroll ladder)
For each flagged clip, surface the **flag + timestamp + recommended treatment**, then choose — do not silently reroll:

1. **Keep** — no flag at/above `medium`, or the flag is cosmetic and doesn't block the beat (per `accept-and-adapt`).
2. **Edit around** — flag is confined to a clip end → `trim_before` / `trim_after` to the clean range; or re-cut so the cut lands before the defect; or mask with a reframe / SFX. Cheapest real fix.
3. **Reroll** — flag is mid-essential-action and un-trimmable. Re-gen, and change what *causes* the artifact (for clones: slow the move, split the action into two shorter shots, or pin a single body with tighter book-end anchors).

## One-pass runner

```bash
CLIP=data/workspace/<proj>/clips/shotN.mp4
CTX="<the generation prompt, or: exactly ONE man, no mirror, ...>"

python3 tools/clip-qa.py     "$CLIP" --context="$CTX" --fail-on=medium   # general anomalies
python3 tools/clone-check.py "$CLIP" --context="$CTX" --fail-on=medium   # subject duplication (motion shots)
# exit 3 from either → inspect the saved .qa-strip.png / .clone-strip.png, then pick a treatment
```

For a batch, loop the clips; any clip that returns exit 3 goes to the decision ladder, the rest are accepted.

## Reconciliation with existing doctrine

- **`no-auto-reroll`** holds: the gate flags and recommends; it never rerolls on its own.
- **`skip-clip-qa-for-user-review`** is refined, not removed: `clip-qa`'s *general* scan can still be skipped on calm, static, user-reviewed clips — but **`clone-check` runs on every motion-bearing shot regardless**, because the duplication class is exactly what the human watch misses (it was caught here only by luck). Treat clone-check as the non-negotiable post-gen check for motion.
- **`accept-and-adapt`** governs the keep decision: a `low`/cosmetic flag that doesn't break the gag is a keep.

## Cross-links
- `clone-check` · `clip-qa` · `anchor-drift` · `frame-qa` · `normalize-clip` · `book-end` skills.
- Lessons: `no-auto-reroll`, `skip-fast-draft`, `accept-and-adapt`, `autonomous-build-doctrine`, `clipqa-motionblur-falsepos`, `clipqa-overflags-face-morph`.
