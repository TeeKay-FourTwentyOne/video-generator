# Seam Findings — extending a shot across a Veo generation boundary

Project: seamless-joins. All numbers below were measured 2026-08-17 at $0.00
generation spend, on clips already on disk. Every number carries the command
that produced it. Measurement tool: `tools/seam-check.py` (270px-wide grayscale
proxy, mean-abs adjacent-frame delta, A+B-combined baseline — see the tool's
docstring for the exact conventions; absolute RATIOs change with the baseline
convention, sweep argmins do not).

Source material: `data/workspace/hz-paradise/clips/` — `s4bv5_toss.mp4` →
`s5bv5_swell.mp4` → `s6v5_trapdoor.mp4`, a shipped pixel chain (each clip
generated with the previous clip's last frame as its first-frame anchor),
1080x1920, 24 fps, 192/192/144 frames.

## 0. Control: the editing stack is exonerated

Split the uncut `s5bv5_swell.mp4` at frame 96 and rejoin three ways; if the
joiner itself moved the number, nothing downstream would be attributable.

```bash
ffmpeg -y -v error -i s5bv5_swell.mp4 -vf "select='lt(n\,96)'"  -vsync 0 -an -c:v libx264 -preset fast -crf 18 A1.mp4
ffmpeg -y -v error -i s5bv5_swell.mp4 -vf "select='gte(n\,96)'" -vsync 0 -an -c:v libx264 -preset fast -crf 18 A2.mp4
# demuxer:  printf "file 'A1.mp4'\nfile 'A2.mp4'\n" > list.txt && ffmpeg -f concat -safe 0 -i list.txt -c copy out_demux.mp4
# filter:   ffmpeg -i A1.mp4 -i A2.mp4 -filter_complex "[0:v]setpts=PTS-STARTPTS,fps=24,settb=AVTB,setsar=1[v0];[1:v]setpts=PTS-STARTPTS,fps=24,settb=AVTB,setsar=1[v1];[v0][v1]concat=n=2:v=1:a=0[v]" -map "[v]" -c:v libx264 -preset fast -crf 18 out_filter.mp4
# splice:   node tools/splice.cjs render A1.mp4 A2.mp4 out_splice.mp4 --cut-a=4.0 --cut-b=0 --xfade=0 --mode=hard
python3 tools/seam-check.py --at 96 <each>
```

| target | frames | RATIO | verdict |
|---|---|---|---|
| uncut original | 192 | **1.106** (seam 6.932 / median 6.267) | PASS |
| concat demuxer `-c copy` | 192 | 1.118 | PASS |
| concat filter | 192 | 1.120 | PASS |
| splice.cjs `--mode=hard` | 192 | 1.120 | PASS |

All three routes return exactly 192 frames and sit within 0.02 of the uncut
baseline. **Everything measured below is genuinely the generator's doing.**

One real defect: with AUDIO streams present (production clips always have
audio), concat demuxer + `-c copy` corrupts the video container metadata —
`r_frame_rate` 24/1 → **120/1**, `avg_frame_rate` → 786432/65573 — while
leaving all 192 frames intact (decoded pixels score identically, 1.118).
Video-only (`-an`) inputs escape it. `.claude/rules/ffmpeg-knowledge.md`
prescribed the demuxer as canonical; fixed 2026-08-17 to prefer the concat
filter.

## 1. B's frame 0 REGENERATES A's final frame → end A at anchor − 1

`s5bv5_swell` was generated with `s4bv5_toss`'s last frame (index 191) as its
first-frame anchor. Sweeping A's end index against B frame 0:

```bash
for AI in 188 189 190 191; do
  python3 tools/seam-check.py --pair s4bv5_toss.mp4:$AI s5bv5_swell.mp4:0
done
```

| A ends at | RATIO | seam_delta |
|---|---|---|
| 188 | 2.446 | 7.409 |
| 189 | 1.639 | 4.964 |
| **190** | **0.945** | **2.861** |
| 191 (the anchor frame) | 1.589 | 4.814 |

Clean argmin at **190 = anchor_index − 1**. B's frame 0 is a re-render of the
SAME moment as A's frame 191, not the next moment: keeping A's frame 191 and
cutting to B duplicates a beat (RATIO 1.59 — the join reads as a stutter).

**Process rule: when B is anchored on A's frame N, A's cut ends at N−1.**

(Baseline-convention note: the same sweep computed with an A-only baseline
gives 1.98/1.14/1.92 — different absolute values, same argmin. seam-check.py
uses the A+B combined baseline; state the convention with any number.)

## 2. The headline defect: VEO RESTARTS FROM REST

```bash
python3 tools/seam-check.py --pair s4bv5_toss.mp4:190 s5bv5_swell.mp4:0
# CHANNEL A (photometric): seam_delta 2.861  neighbour_median 3.028  RATIO 0.945  PASS
# CHANNEL B (kinematic):   base_a 3.257  base_b 0.799  VELOCITY_RATIO 0.245      FAIL
#   B head deltas: 1.33 0.65 0.82 0.43 0.52 0.71 0.80 1.06 0.77 1.35 1.99 3.22
```

A's tail runs at motion energy ~3.03–3.58 (median 3.257). B opens at 1.33,
collapses to 0.43–0.82 for ~9 frames, and only regains A's velocity (3.22) by
frame 12 — a **~0.4s near-freeze at the start of every continuation**. That
stall IS the visible "skip", and it is structurally invisible to every
boundary-pair metric in this repo (PSNR, splice.cjs's score, anchor-drift):
the boundary pair itself is photometrically fine (RATIO 0.945); the defect
lives in B's INTERIOR. VELOCITY_RATIO was 0.245–0.245 across ALL cut choices
in the §1 sweep — no choice of cut point can fix it.

This is why the gate is two-channel and never blended: a join can pass
photometrically and fail kinematically, and the failures need different
treatments (cut choice vs head-trim/velocity prompting).

## 3. Head-trim recovery: a genuine both-channels pass window exists

Holding A's end at 190 and sweeping B's start index:

```bash
for BI in $(seq 0 12); do
  python3 tools/seam-check.py --pair s4bv5_toss.mp4:190 s5bv5_swell.mp4:$BI --json
done
```

| B starts at | RATIO | VELOCITY_RATIO | verdict |
|---|---|---|---|
| 0 | 0.945 | 0.245 | FAIL (kin) |
| 1 | 1.028 | 0.245 | FAIL (kin) |
| 2 | 1.079 | 0.253 | FAIL (kin) |
| 3 | 1.095 | 0.325 | FAIL (kin) |
| 4 | 1.139 | 0.413 | FAIL (kin) |
| **5** | **1.160** | **0.610** | **PASS** |
| **6** | **1.205** | **0.988** | **PASS** |
| **7** | **1.253** | **1.415** | **PASS** |
| **8** | **1.369** | **1.750** | **PASS** |
| **9** | **1.451** | **1.974** | **PASS** |
| 10 | 1.585 | 2.391 | FAIL (photo+kin) |
| 11 | 1.919 | 2.731 | FAIL (photo+kin) |
| 12 | 1.900 | 3.025 | FAIL (photo+kin) |

The channels disagree in opposite directions — trimming B's head repairs
velocity (0.245 → 0.988 by B-start 6) while degrading photometric continuity
(0.945 → 1.9 by 12) — and they intersect in a real pass window at **B-start
5–9, sweet spot 6**. The reason the trim is photometrically cheap is the
stall itself: because Veo restarted from rest, B's frames 0–6 barely moved,
so B's frame 6 is still close to A's frame 190. The defect funds its own
repair.

**Process rule (this motion regime): end A at anchor−1, start B at ~6
(≈0.25s head-trim), then gate with seam-check — both channels.** The trim
cost is ~6 frames of B's 8s, i.e. ~3% of the clip.

## 4. The low-motion regime: best cut still fails

`s5bv5_swell.mp4:AI → s6v5_trapdoor.mp4:0`, same sweep:

| A ends at | RATIO | VELOCITY_RATIO |
|---|---|---|
| 188 | 3.822 | 0.238 |
| 189 | 3.238 | 0.239 |
| **190** | **2.941** | **0.252** |
| 191 | 3.339 | 0.280 |

Argmin is again at anchor−1 = 190 (the rule generalises), but the best value
is a genuine FAIL on both channels: A's tail is slowing (base_a ~2.1), B
opens near-static (base_b 0.53), and the photometric seam (3.164) is ~3x the
local median (1.076). In low-motion regimes the anchor mismatch that motion
would hide is fully visible, AND the restart stall compounds it. Consistent
with the working hypothesis that joins hide best at motion nulls — but note
this pair's B (trapdoor) opens on a different blocking beat, so part of the
3x is content divergence, not just the stall. The cycle-2 anchor-binding A/B
is the controlled version of this question.

## 5. The gate: tools/seam-check.py

Two channels, reported separately, NEVER blended:

- **CHANNEL A (photometric):** RATIO = seam_delta / median(neighbour deltas),
  pass band **[0.6, 1.5]**, two-sided. Two-sided matters: a duplicate frame
  scores ~0.05 — a one-sided "smaller is better" gate (like splice's
  PSNR ≥ 35, `.claude/skills/splice/SKILL.md`) actively REWARDS a frozen
  duplicate frame, which is itself a skip. PSNR ≥ 35 is additionally
  unreachable on real Veo motion footage.
- **CHANNEL B (kinematic):** VELOCITY_RATIO = base_b / base_a (medians of 11
  adjacent-deltas per side), pass band **[0.5, 2.0]**, plus B's raw first-12
  delta series for eyeballing the ramp shape.
- **Near-static branch:** when the pooled neighbour median < 0.5, relative
  ratios divide noise; the gate switches to ABSOLUTE seam delta (fail > 2.0)
  and says so.

Calibration (uncut s5bv5_swell, seam 96): seam 6.932 / median 6.267 / RATIO
1.106 at 270px; 540px cross-check agrees (RATIO 0.980). Defect fixtures and
expected bands: `tests/fixtures/seam/` (`./run-fixtures.sh`, fully offline) —
clean 1.120/PASS, duplicate 0.052/FAIL, dropped-frame 1.842/FAIL, unrelated
hard cut 25.78/FAIL, 12px translation 2.92/FAIL.

## 6. Traps confirmed this cycle (do not rediscover)

- **Last-frame extraction off-by-one** (was TECHNIQUES.md:518): `-frames:v 1`
  overrides `-update 1` and emits the FIRST frame of the sseof window.
  Correct form (now `tools/last-frame.sh`):
  `ffmpeg -y -v error -sseof -0.5 -i A.mp4 -update 1 out.png` — NO -frames:v.
  Verified by md5 on `data/video/veo_1777264585289_czj59h.mp4`: correct form
  f187b50589c09c6428c425ef65c85724 = `select='eq(n\,143)'` ground truth;
  with `-frames:v 1`: 6ffd4462f40ad2e3b25d288398a61873 (wrong frame).
- **concat demuxer container corruption** (§0): audio-interleave-dependent;
  r_frame_rate 120/1. Use the concat filter.
- **Do NOT use `splice.cjs --align` or `--trim-a`**: splice_align.py's
  `warp()` clamps the crop origin so translation is a structural no-op at
  scale 1.0, and `detect_core` stores the REQUESTED offset rather than a
  tested one, which splice.cjs:358-367 then bakes into the render. Alignment
  claims from those flags are unverified fiction.
- **Anchor frames come from the RAW mp4** — never after normalize-clip (it
  re-encodes and can rescale; the extracted frame then no longer matches what
  a continuation must reproduce).
- **Billing**: every submission bills, at the floor-snapped duration ({4,6,8}
  only); both MCP entry points default to quality/8s (a bare call bills
  $1.60–$3.20); a third ungated client lives at
  `data/workspace/mine-too/scratch/shot.cjs`; aliases `veo-3.1-fast-prod` /
  `veo-3.1-prod` (bare `veo-3.1-fast` is a dead preview model). PRICING.md's
  cheap tiers were wrong on every row until 2026-08-17; the export-verified
  rates now live in PRICING.md and `tools/veo-budget.py` (hard $10.00 cap,
  append-before-submit). Reconcile at project end via `tools/gcp/bq.cjs`
  (~5h lag — it cannot guard live; a prior self-estimate undercounted 2x).

## 7. ANSWERED (cycle 2, 2026-08-17): the anchor does NOT bind on fast

Two 4s silent first-frame-only continuations of `s4bv5_toss.mp4`'s true last
frame (frame 191 via `tools/last-frame.sh`, RAW mp4), `veo-3.1-fast-prod`,
9:16, same motion-only prompt, measured with
`data/workspace/seamless-joins/scratch/measure.py` (frame-0 PSNR/MAE + a
B-start 0–12 `seam-check --pair` sweep against A:190):

| arm | seed | B[0] vs anchor | seam RATIO @k0 | VR @k0 | sweep pass window |
|---|---|---|---|---|---|
| 720p | 2481 | **25.5 dB / MAE 7.30** | 2.775 | 0.445 | **NONE** (ratio rises 2.8→5.6 with trim) |
| 1080p | 1137 | **18.5 dB / MAE 16.32** | 2.201 | 0.328 | **NONE** (ratio 1.8–3.2 everywhere) |

What actually happens: the anchor binds IDENTITY, WARDROBE and SET —
appearance the prompt never mentioned is reproduced exactly — but not
GEOMETRY. Both arms restage the composition (subject larger, head near frame
top, coat drape and cloth texture re-drawn). The restage is **non-rigid**: no
global translation within ±12 px and no uniform scale in 0.84–1.16×
reduces the mismatch (mean signed diff 0.39 — not a grade shift), so no
aligner could rescue it, retroactively confirming §6's `--align` verdict.
This replicates church-grim's 1080p anchor-demotion on the QUALITY model
(2026-07-20) and extends it: on FAST it happens at 720p too.

Two distinct kinematic failures, only one of which head-trim can fix:

- **restart-ramp** (1080p arm; also the shipped chain in §2): opens ~0.3× and
  ramps back over ~12 frames. Trimming into the ramp works when the clip
  eventually reaches A's velocity.
- **slow-run** (720p arm, NEW): B runs FLAT at ~0.45× of A's tail velocity
  (head deltas ~1.4 vs A's ~3.2, no ramp in 13 frames). A flat series has
  nothing to trim into — head-trim is structurally useless here. Words in the
  prompt ("continues at the same speed from the very first frame") did not
  carry velocity.

RAI note: the first 720p attempt (seed 1137, the seed that PASSED at 1080p)
was output-filtered — `raiMediaFilteredCount 1`, support code 29310472. The
output filter is stochastic per-sample; budget for retries. Vertex's message
says blocked videos are not charged; the $0.32 stays on the ledger until the
BQ reconcile proves it either way.

**Verdict: pixel-chaining on `veo-3.1-fast-prod` is dead at both
resolutions.** Every artifact is preserved in `tests/fixtures/extend-clip/`
(paid, non-regenerable; offline repro commands in its manifest.json).

## 8. Open (cycle 3, one paid question, $0.80): does QUALITY bind at 720p?

The one remaining live hypothesis, from church-grim (2026-07-20, observed
near pixel-exact but never instrumented): `veo-3.1-prod` at **720p** binds
first-frame anchors tightly, and 1080p is where demotion begins. One 4s
silent 720p quality arm ($0.80), same anchor, same prompt, same
measure.py, decides it. If it binds (≥ ~35 dB): extend-clip becomes
"quality-720p only", and the same clip's VR answers whether quality also
fixes the velocity handoff (if VR still fails, the head-trim sweep on a
BOUND B is exactly the calibrated §3 machinery). If it does not bind:
the pixel-chain premise is dead on every current door, and extend-clip's
"joins are invisible only at motion nulls" constraint graduates from
working hypothesis to doctrine — stop spending.
