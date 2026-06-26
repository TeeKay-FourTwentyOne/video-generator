---
name: anchor-drift
description: Pre-generation check for Veo book-end frames — catch the "impossible slide" and "pop-in" artifacts before spending a Veo generation. Veo interpolates between a first-frame and a last-frame and will SLIDE, MORPH, MATERIALIZE, or POP any object whose position/scale/count/orientation differs between the two frames it's handed, even when impossible (a placed prop gliding with nothing pushing it; a new object blinking into existence; a doll appearing at a cut). Use on any book-end anchor pair, and on any hard-cut boundary, whenever supposedly-static objects (placed props, machine output, background figures, accumulating items) must hold still or match across a cut. Both failures are frame-only — detectable with zero Veo spend. Pair with frame-qa (which checks a single frame vs its refs); anchor-drift checks a frame PAIR for motion Veo will invent.
allowed-tools: Read, Bash, Glob
---

# anchor-drift

Veo book-end generation interpolates between a **first** anchor frame and a **last** anchor frame. It has no notion of object permanence — it only morphs pixels from A toward B. So **any object whose position, scale, count, or orientation differs between the two anchors gets animated**, with no regard for physics:

- A placed copy at position X in frame A and X′ in frame B → Veo **slides** it from X to X′ across the table with nothing pushing it.
- An object absent in A but present in B → Veo **materializes** it mid-clip (or slides it in from an edge).
- The same mismatch at a **hard cut** (last frame of shot N vs first frame of shot N+1) → the object **pops** into existence or **jumps** position at the cut.

These are invisible in per-frame QA (each frame looks fine on its own) and invisible to ffmpeg scene/freeze/black detectors (they don't model objects). They only exist in the *delta* between two frames — and they're **intent-dependent**: the identical motion is correct on a living character and wrong on an inert prop. So detection needs (1) the frame pair and (2) a declaration of what's supposed to be static.

This skill is that check, and it runs **before** you generate — catch a drift on the frames and you never spend the Veo second.

## When to use

- **Every book-end anchor pair** where the clip contains objects that should stay put or only be added: placed props, machine/factory output, accumulating items, crowds/background figures, anything set down and meant to be inert.
- **Every hard-cut boundary** between two shots that share a static element (a prop, a count of objects, a set dressing). Run it on shot N's last frame vs shot N+1's first frame.
- After a fix, to confirm the drift is gone (regression check).

Skip it when nothing in the shot is meant to be static (a fully organic, freely-moving scene), or for a one-off establishing shot with no continuity neighbor and no inert props.

## The two modes

| mode | frame A | frame B | predicts |
|------|---------|---------|----------|
| `within-clip` (default) | clip's FIRST anchor | clip's LAST anchor | **slide / morph / materialize** during interpolation |
| `across-cut` | shot N LAST frame | shot N+1 FIRST frame | **pop / jump** at the cut |

## The tool

`tools/anchor-drift.py` sends the frame pair to Claude vision with a **static spec** (what must not change) and a **motivated spec** (what's allowed to move, and its mover). It returns, per differing object: the change type, predicted artifact, severity, and the concrete frame fix. Differences caused by a listed mover (e.g. a gripper carrying an object) are deliberately NOT flagged.

```bash
# within a clip — the placed copies must hold; only a gripper-carried copy may move
python3 tools/anchor-drift.py FIRST.png LAST.png --mode=within-clip \
  --static="every felt copy already on the table (count and positions)" \
  --motivated="the grey gripper arm and one single copy held in its gripper" \
  --fail-on=medium

# across a cut — shot N's last frame vs shot N+1's first frame must agree
python3 tools/anchor-drift.py SHOTN_LAST.png SHOTN1_FIRST.png --mode=across-cut \
  --static="the felt copies on the table (count and positions)" \
  --motivated="the gripper arm" --fail-on=medium
```

Exit codes: `0` pass · `3` violation at/above `--fail-on` · `1` API error · `2` usage error. Use `--json` for machine output. Default model is opus (most reliable for visual diffs); Claude-billed, ~$0.02–0.05/call.

**Write good specs.** The `--static` list is what makes it work — name the inert objects and that their *count and positions* must hold. The `--motivated` list prevents false positives — name every legitimate mover and what it carries, so the tool doesn't flag the gripper (or a walking character, a falling object, etc.). With no specs it still runs but flags any unexplained motion, which over-reports.

## The fix vocabulary (what the tool tells you to do)

- **Slide (within-clip):** pin the object to its **identical** position/scale/orientation in both anchors. Generate the last frame by **chaining off the first and only ADDING** new objects — never reposition an existing one.
- **Materialize (within-clip):** a new object must enter via a **visible mover** (e.g. carried in by the gripper, present in both frames attached to it), or don't add it in this clip — add it at a later cut where a reframe masks the count change.
- **Pop / jump (across-cut):** make the boundary frames **agree** — shot N must END on the same count/positions that shot N+1 BEGINS with. (Equivalently: bump one side's count to match the other.)
- **Masked count change:** a count jump is acceptable across a cut that also **reframes hard** (wide→close) or **jumps time** — the reframe hides it. It is NOT acceptable across a same-framing cut (wide→wide), where it reads as a doll popping in.

## Key principle: payload vs pop (and it's mode-dependent)

The decisive test for a *newly appeared* object is **"is a mover holding it?"** A new object **held by / in contact with an allowed mover** (a gripper, a hand) is the mover's **payload** — the mover brought it in; that is NOT a pop. A new object that appears **unattached on a static surface** (table, floor, shelf) with nothing touching it IS a pop. For *placement*: the mover must be **in contact with the object in BOTH anchor frames** (holding it aloft in the first, still touching it mid-release in the last); a detached/empty mover over a resting object means the placement isn't motivated and Veo will pop/slide it.

**Crucial caveat — the payload relaxation is WITHIN-CLIP only.** Within a clip the mover moves *smoothly*, so it can carry a payload in. **A hard cut is instantaneous — it carries nothing.** So across a cut, the mover's *own* state must also match: if the gripper is empty in shot N's last frame and holding a doll **aloft** in shot N+1's first frame, the doll **teleports into its grip** and the rigid gripper **snaps to a new shape** — a jarring jump, even though the doll is "held." The fix for a machine that delivers across cuts: don't. Either (a) keep each delivery wholly **within one clip** (mover enters and acts between the anchors), or (b) **reframe** at the cut (wide→closer) so the mover leaves frame and its state-change is masked. The latter is usually cleaner and often a better edit.

## Validated

Built and hardened on the "SECONDS" shot-4 frames (2026-06-25):
- **Old (broken) frames — correctly FLAGGED:** `across-cut` s3_b(1) → s4_a(2 on table): high, "doll materializes at the cut." `within-clip` s4_a(2) → s4_b(4): high count 2→4 **plus** a front doll sliding toward the maker (medium). The gripper and the active sewing character were correctly ignored.
- **Fix iteration (the skill as a gate):** four cheap nano regens, each caught by the skill before any Veo spend — (1) cut matched by chaining shot-4's first frame off shot-3's last; (2) copy 2 made unambiguously **airborne in the gripper** (an earlier version read as a 2nd resting doll → still flagged); (3) gripper kept **in contact mid-release** in the last frame so the placement is motivated (a detached/empty gripper over a resting doll → still flagged).
- **Round 2 — the mover-state jump:** the "fixed" version still played jarringly: the gripper went empty (shot 3 end) → holding a doll **aloft** (shot 4 start), so a doll teleported into the air and the gripper morphed across the cut. The skill's *first* version PASSED this (the payload relaxation was wrongly applied across the cut). Hardened the `across-cut` rule (mover state must match too) → it now FLAGS it HIGH: *"the mover changes form from a nozzle to a claw"* and *"the doll moves from seated on the stool to dangling in mid-air."*
- **Resolution — reframe:** rather than fight Veo to deliver a copy across a hard cut, shot 4 was re-conceived as a **closer two-shot** (the maker turning to regard its inert double, no gripper). The wide→closer cut now resolves to `across-cut` **PASS** ("gripper leaves frame, masked by reframe; low") and `within-clip` **PASS** (copy pinned, maker is the active mover).

The point: the skill turned an invisible-in-stills, expensive-in-Veo defect into a per-iteration frame fix — and the hard cases pushed the rule itself to be correct (payload OK within a clip, never across a cut).

## Interaction with other skills

- **frame-qa** validates ONE frame against its canonical refs (wardrobe/plate/prop drift). anchor-drift validates a frame PAIR for motion Veo will invent between them. Run frame-qa first (each frame is on-model), then anchor-drift (the pair won't drift).
- **book-end** is the generation pattern this guards. anchor-drift is the pre-Veo gate for its anchor pairs and the cut boundaries between its clips.
- **clip-qa** is the post-generation backstop (materialization/ghost-limbs/flicker in the rendered clip). anchor-drift catches the subset that's predictable from frames, before spending the generation.
