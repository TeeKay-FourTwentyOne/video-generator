---
name: extend-clip
description: Extend a shot across a Veo generation boundary — generate clip B as a pixel-chained continuation of clip A and join them with no visible cut, jump, or skip. Use when a single action must run longer than one generation allows. The join point is known A PRIORI by construction (B is anchored on A's last frame), so do NOT use the splice skill here — splice searches for an UNKNOWN join point and prefers low-motion plateaus, which is exactly backwards for continuations (a low-motion B opening is the defect, not the join point). Gates every join with tools/seam-check.py: two channels, photometric and kinematic, never blended.
allowed-tools: Read, Bash
---

# Extend Clip

Continue shot A with a fresh generation B so the pair reads as one shot.
Everything here is calibrated in `docs/seam-findings.md` (2026-08-17); the
budget rules are hard project constraints.

## Why this is not splice

| | splice | extend-clip |
|---|---|---|
| join point | UNKNOWN — searched for | KNOWN by construction (B[0] ≈ A[anchor]) |
| scoring | one-sided PSNR + low-motion plateau bonus | two-sided RATIO + velocity match |
| low motion at the join | rewarded (robust to timing shifts) | **the defect** — Veo restarts from rest |

A one-sided photometric gate rewards a frozen duplicate frame, which is
itself a skip. Never use `splice.cjs --align` / `--trim-a` (structural no-op
+ untested offsets baked into the render — see seam-findings §6).

## The process

1. **Extract A's true last frame from the RAW mp4** (never after
   normalize-clip):
   ```bash
   tools/last-frame.sh data/workspace/<proj>/clips/A.mp4 anchor.png
   ```
   (`-frames:v 1` variants emit the wrong frame — that's why this wrapper
   exists.)
2. **Budget preflight — before EVERY submission, through any entry point:**
   ```bash
   python3 tools/veo-budget.py preflight --model fast --seconds 4 \
     --resolution 720p --audio no --note "B continuation of <shot>"
   ```
   Abort on non-zero. Then submit with every parameter EXPLICIT (model
   `veo-3.1-fast-prod` or `veo-3.1-prod` — never bare `veo-3.1-fast`;
   durationSeconds in {4,6,8}; generateAudio; resolution) — a bare call
   defaults to quality/8s and bills $1.60–$3.20. First-frame-only
   conditioning; lastFrame-only is invalid and still bills.
3. **Prompt describes MOTION ONLY, continuing at speed** — never re-describe
   the frame contents (the anchor already carries position; the open question
   is whether words can carry velocity).
4. **Cut rule: A ends at anchor − 1.** B's frame 0 REGENERATES the anchored
   moment (same instant, not the next); keeping A's anchor frame duplicates a
   beat. Verified argmin: RATIO 1.64/0.94/1.59 at A-end 189/190/191 on a
   frame-191 anchor.
5. **Expect the restart stall and trim it.** Veo opens continuations from
   near-rest: ~0.25 of A's tail velocity, ramping back over ~12 frames — a
   ~0.4s visible hitch that no boundary-pair metric sees. In the calibrated
   high-motion case the fix is a B head-trim: both-channels pass window at
   B-start 5–9, sweet spot 6 (~0.25s). The stall makes the trim
   photometrically cheap — B barely moves while stalled.
6. **Gate the join — both channels, never blended:**
   ```bash
   python3 tools/seam-check.py --pair A.mp4:190 B.mp4:6
   ```
   Photometric RATIO band [0.6, 1.5]; kinematic VELOCITY_RATIO band
   [0.5, 2.0]; near-static shots switch to an absolute-delta branch
   automatically. Exit 3 = do not ship the join. Regression fixtures:
   `tests/fixtures/seam/run-fixtures.sh` (offline, free).
7. **Join with the concat filter or `splice.cjs --mode=hard`** — not concat
   demuxer `-c copy`, which corrupts the container (r_frame_rate 120/1) when
   audio is present.

## Status / supported constraints (update as cycles land)

- **Calibrated on**: the hz-paradise pixel chain (repo's shipped footage).
  The anchor−1 rule and the stall are measured facts there.
- **PENDING cycle 2 (~$0.72 A/B)**: does a supplied anchor PNG actually bind
  B[0] on `veo-3.1-fast-prod` at 720p/1080p? Branches specified in
  seam-findings §7. Until it lands, treat pixel-chaining as unproven on
  fresh generations.
- **Working hypothesis, not yet doctrine**: if prompt language cannot carry
  velocity and head-trimming cannot recover it in low-motion regimes
  (swell→trapdoor failed at every cut: best RATIO 2.94, VR 0.25), the honest
  rule becomes "**joins are invisible only at motion nulls**" — plan cut
  points at natural pauses, or spend the join on a deliberate reframe cut.
  Do not re-litigate with new spend once the evidence is in.

## Money

Hard cap **$10.00 for the life of the project**, enforced by
`tools/veo-budget.py` (append-before-submit; ledger `data/veo-budget.tsv`;
`status` subcommand). Anthropic-billed QA (clip-qa/frame-qa) is a separate
ledger. Reconcile at project end with `tools/gcp/bq.cjs` (~5h lag).
