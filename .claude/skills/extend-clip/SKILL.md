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
   python3 tools/veo-budget.py preflight --model quality --seconds 4 \
     --resolution 720p --audio no --note "B continuation of <shot>"
   ```
   Abort on non-zero. Then submit with every parameter EXPLICIT (model
   `veo-3.1-prod` at **720p** — fast measured as non-binding (status block
   below), and 1080p demotes anchors on both models; never bare `veo-3.1-fast`;
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
5. **Expect the restart stall and trim it — but check WHICH stall.** Two
   measured kinematic failure shapes (seam-findings §7):
   - **restart-ramp**: B opens ~0.3× of A's tail velocity and ramps back
     over ~12 frames. Head-trim works: calibrated pass window at B-start
     5–9, sweet spot 6 (~0.25s). The stall makes the trim photometrically
     cheap — B barely moves while stalled.
   - **slow-run**: B runs FLAT at ~0.45× with no ramp (cycle-2 720p fast
     arm). A flat head series has nothing to trim into — head-trim is
     structurally useless; reroll or fall back. Look at the B-head delta
     series before sweeping.
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
- **MEASURED cycle 2 (2026-08-17, $1.04 ledgered): `veo-3.1-fast-prod` does
  NOT pixel-bind a first-frame anchor at 720p OR 1080p.** Identity/wardrobe/
  set bind; geometry restages non-rigidly (25.5 / 18.5 dB vs the
  conditioning PNG; no head-trim pass window on either arm; no global
  translation or uniform scale recovers it). Motion-only "continue at the
  same speed" prose did not carry velocity (VR 0.45 / 0.33). **Do not
  attempt pixel-chained continuations on the fast model.** Evidence:
  seam-findings §7; paid artifacts in `tests/fixtures/extend-clip/`.
- **PENDING cycle 3 ($0.80, the last binding question)**: does `veo-3.1-prod`
  QUALITY at **720p** bind (church-grim 2026-07-20 observed near
  pixel-exact, never instrumented)? Until it lands, treat pixel-chaining as
  unavailable, full stop.
- **Working hypothesis, not yet doctrine**: if quality-720p also fails to
  bind — or binds but velocity cannot be carried or trimmed (slow-run
  shape) — the honest rule becomes "**joins are invisible only at motion
  nulls**" — plan cut points at natural pauses, or spend the join on a
  deliberate reframe cut (low-motion regime already failed every cut:
  swell→trapdoor best RATIO 2.94, VR 0.25). Do not re-litigate with new
  spend once cycle 3 is in.

## Money

Hard cap **$10.00 for the life of the project**, enforced by
`tools/veo-budget.py` (append-before-submit; ledger `data/veo-budget.tsv`;
`status` subcommand). Anthropic-billed QA (clip-qa/frame-qa) is a separate
ledger. Reconcile at project end with `tools/gcp/bq.cjs` (~5h lag).
