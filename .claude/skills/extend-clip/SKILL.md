---
name: extend-clip
description: Extend a shot across a Veo generation boundary — make clip B continue clip A with no visible cut, jump, or skip. Use when a single action must run longer than one generation allows. MEASURED DOCTRINE (2026-08-17): pixel-chaining does NOT work on any current door — first-frame anchors restage geometry on fast AND quality, so joins are invisible only at motion nulls; plan the boundary, don't chase the bind. The join point is known A PRIORI by construction (B is anchored on A's last frame), so do NOT use the splice skill here — splice searches for an UNKNOWN join point and prefers low-motion plateaus, which is exactly backwards for continuations (a low-motion B opening is the defect, not the join point). Gates every join with tools/seam-check.py: two channels, photometric and kinematic, never blended.
allowed-tools: Read, Bash
---

# Extend Clip

Continue shot A with a fresh generation B so the pair reads as one shot.
Everything here is calibrated in `docs/seam-findings.md` (2026-08-17); the
budget rules are hard project constraints.

## DOCTRINE (measured, closed — do not re-litigate with spend)

**Joins are invisible only at motion nulls.** A first-frame anchor does not
pixel-bind B[0] on any current model/resolution (evidence below), so a
continuation across a generation boundary always carries a geometric
restage pop, and mid-motion it also carries a velocity mismatch. Plan the
extension instead:

1. **Write the boundary into the action**: end A at a natural pause — a
   settle, a held look, a completed gesture — and open B from that same
   still beat. Low motion hides the restage worst-case least badly, but
   even the best low-motion cut measured on shipped footage failed the gate
   (swell→trapdoor RATIO 2.94, VR 0.25) — so verify, never assume.
2. **Or spend the join on a deliberate reframe cut**: a cut that reads as
   editorial intent (new angle, new framing) is invisible BECAUSE it is
   visible — continuity of action, not of pixels, carries it. This is the
   reliable path for mid-motion extensions.
3. Either way, **gate the result with seam-check** (below). Exit 3 = the
   join ships as a visible skip; re-plan the boundary, don't reroll B.

## Why this is not splice

| | splice | extend-clip |
|---|---|---|
| join point | UNKNOWN — searched for | KNOWN by construction (B[0] ≈ A[anchor]) |
| scoring | one-sided PSNR + low-motion plateau bonus | two-sided RATIO + velocity match |
| low motion at the join | rewarded (robust to timing shifts) | **the defect** — a stalled or restaged B opening |

A one-sided photometric gate rewards a frozen duplicate frame, which is
itself a skip. Never use `splice.cjs --align` / `--trim-a` (structural no-op
+ untested offsets baked into the render — see seam-findings §6).

## The machinery (for any attempted continuation, and for gating joins)

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
   Abort on non-zero. Then submit with every parameter EXPLICIT (model,
   durationSeconds in {4,6,8}, generateAudio, resolution — never bare
   `veo-3.1-fast`, a dead alias) — a bare call defaults to quality/8s and
   bills $1.60–$3.20. First-frame-only conditioning; lastFrame-only is
   invalid and still bills. RAI note: the output filter is
   (seed, resolution)-correlated — seed 1137 filtered at 720p on BOTH
   models (code 29310472) while passing at 1080p; on a 720p trip, burn a
   different seed, not a rephrase.
3. **Prompt describes MOTION ONLY, continuing at speed** — never re-describe
   the frame contents. Measured: this prose carries velocity on QUALITY
   (VR 0.64, no restart) but not on fast (VR 0.33–0.45, stall or slow-run).
   It does not carry geometry on either.
4. **Cut rule: A ends at anchor − 1.** B's frame 0 REGENERATES the anchored
   moment (same instant, not the next); keeping A's anchor frame duplicates a
   beat. Verified argmin: RATIO 1.64/0.94/1.59 at A-end 189/190/191 on a
   frame-191 anchor.
5. **Read B's head delta series before trimming.** Three measured shapes:
   - **restart-ramp** (fast-1080p; the shipped hz-paradise chain): B opens
     ~0.3× and ramps back over ~12 frames. Head-trim works: calibrated pass
     window at B-start 5–9, sweet spot 6 (~0.25s) — but only when the
     anchor actually bound (it did on the shipped chain's same-model loop;
     it did not on any measured A/B arm).
   - **slow-run** (fast-720p): FLAT ~0.45× with no ramp — nothing to trim
     into; head-trim is structurally useless.
   - **restage-drift** (quality-720p): velocity fine (VR 0.63–0.76 at every
     trim) but photometric RATIO rises monotonically with trim (1.97 → 5.72)
     because B's restaged geometry diverges from A as it plays — no trim
     exists. This is why kinematic health alone must never pass a join.
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

## Status / supported constraints (project CLOSED 2026-08-17)

- **Calibrated on**: the hz-paradise pixel chain (repo's shipped footage).
  The anchor−1 rule and the restart stall are measured facts there.
- **MEASURED cycle 2 ($1.04): `veo-3.1-fast-prod` does NOT pixel-bind a
  first-frame anchor at 720p OR 1080p.** Identity/wardrobe/set bind;
  geometry restages non-rigidly (25.5 / 18.5 dB vs the conditioning PNG; no
  head-trim pass window; no rigid transform recovers it). Motion-only prose
  did not carry velocity (VR 0.45 / 0.33).
- **MEASURED cycle 3 ($1.60 incl. one RAI retry): `veo-3.1-prod` QUALITY at
  720p does NOT bind either** — 25.56 dB / gray MAE 7.27, the same restage
  magnitude as fast-720p, non-rigid (best transform = identity). Church-grim's
  observed near-pixel-exact bind does not reproduce under instrumentation.
  NEW: quality does NOT restart from rest — VR 0.64, flat head series, the
  kinematic channel passes at every trim. The two models fail on OPPOSITE
  channels, which is why the gate is two-channel and never blended.
- **DOCTRINE (graduated from hypothesis, cycle 3): joins are invisible only
  at motion nulls.** Pixel-chaining is unavailable on every current door.
  Evidence: seam-findings §7–§8; paid artifacts in
  `tests/fixtures/extend-clip/` (non-regenerable — do not delete). Do not
  re-litigate with new spend.

## Money

Hard cap **$10.00 for the life of the project**, enforced by
`tools/veo-budget.py` (append-before-submit; ledger `data/veo-budget.tsv`;
`status` subcommand). Final ledger 2026-08-17: **$2.64 committed** ($1.52 if
the two RAI-blocked arms reconcile as unbilled — deferred, export lag).
Anthropic-billed QA (clip-qa/frame-qa) is a separate ledger. Reconcile at
project end with `tools/gcp/bq.cjs` (~5h+ lag).
