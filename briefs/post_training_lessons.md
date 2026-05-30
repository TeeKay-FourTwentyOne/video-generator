# Post-Training explainer — lessons

Built 2026-05-30. `data/workspace/post-training/`. Final `final/post_training_v1_4k.mp4`
(2160×3840, 2:25). 100% programmatic (numpy/PIL/ffmpeg). See `post_training_brief.md`.

## Visualization
- **Conserved-area curve is the whole idea.** Renormalize the density every frame so total
  area is constant → "post-training redistributes a fixed budget, never adds" becomes a
  *provable on-screen fact*, not a caption. numpy 2.4 removed `np.trapz` — use **`np.trapezoid`**.
- **The dashed "ghost" of the base distribution behind every later stage is what makes the
  honest point land.** Entropy collapse / "what got lost" is invisible on a lone bell curve;
  the ghost spanning the full axis behind a tall spike makes it unavoidable. Highest-value element.
- **Card-occludes-curve layout.** In a vertical frame, a near-opaque rounded inset card (≈232/255)
  placed over the curve's upper half cleanly *occludes* it — no fiddly repositioning. The curve's
  base + ghost + dots peek below for context. Used for both honesty insets (calibration, pass@k).
- **Sample-dot "heartbeat":** pile sampled dots into a small histogram echoing the analytic curve
  → shows "sampling = drawing from this shape," height shown twice. Cheap, high payoff.
- **Each method = a distinct physical verb** (slide / spike+leash / split / press / funnel / new
  hill), so beats stay differentiable instead of "the peak just goes up again."
- States as 6 fixed gaussian slots (mu,sig,amp); morph = per-slot lerp; amp→0 removes a hill.
  Keeps every transition continuous. One global V_SCALE so heights are honestly comparable.

## Tooling gotchas
- **matplotlib is ABI-broken against numpy 2.4.4** on the project interpreter — import warns/crashes.
  Draw charts in **pure PIL**; trivial for reliability diagrams + monotone crossover curves, and
  it's the one honest place for real ticks.
- **Avenir Next has no `✓` or `→` glyph** (renders as tofu) — draw checkmarks/arrows as strokes
  (`common.check_mark`, `common.arrow`). Menlo (mono) *does* have `→`, fine for the area tag.
- **Probe-mode rendering** (a handful of stills across each beat) validates composition in seconds
  before committing the ~35-min full frame render. Always probe first.
- **fade_env per clip + concat = dip-to-black transitions for free** — no crossfade filter needed.

## VO / pacing
- **The `speed` param's direction is the trap.** speed>1 = FASTER. To slow down go BELOW 1. The
  prior "rushed" explainers ran speed 1.1–1.2 thinking mood would slow it — it didn't. Bella,
  contemplative: speed 0.80 ≈ 135 wpm, 1.0 ≈ 158 wpm, 1.12 ≈ 188 wpm. See [[feedback_tts_speed_param]].
- **Never eyeball runtime from word count.** Estimated ~250 words / ~110s; actual ~400 words / 3:20
  at the slow pace. **Generate VO first, ffprobe real durations, THEN scope runtime.** The whole
  shot-timing pipeline keys off measured VO durations anyway.
- Tighten + speed 1.0 (vs slow + verbose) was the right runtime lever: 3:20 → 2:15 while staying
  unrushed (lighter content reads fine quicker).

## Finishing
- **Lanczos > Real-ESRGAN for synthetic content.** The 1080 master is already SS=2 anti-aliased;
  ESRGAN softens text + smears the dark gradient (cf. FALSE COLOR note) and would take hours for
  2:25. `ffmpeg scale=...:flags=lanczos` = ~2 min, clean, and still unlocks YouTube's higher 4K
  upload bitrate (helps dark gradients avoid banding). [[feedback_disk_hygiene_video_project]]

## Process
- Research + viz-design ran as a multi-agent **workflow** (judged 5 viz concepts; "Probability
  Landscape" won 8.3) + a separate adversarial fact-check workflow over on-screen claims.
- **Fact-check workflow ballooned to 334 claims** because claim-extraction was too generous
  (pulled citation-level facts) and every verifier shared the label "verify". Next time: cap
  extraction to load-bearing on-screen claims and give each agent a per-claim label.
