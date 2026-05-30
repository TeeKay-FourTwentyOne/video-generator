# Post-Training — "AI Explains AI" explainer

**Slug:** `post-training` · **Series:** AI Explains AI (sibling to model-weights, named-tensors, ai-explains-steg)
**Format:** vertical 9:16, native-4K master, ~2:00–2:15 · 100% programmatic (numpy + PIL + ffmpeg), no Veo
**Voice:** ElevenLabs Bella, `mood=contemplative, speed=1.0` (after a tighten pass; the slowed 0.80 pass made it ~3:20)
**Started:** 2026-05-30 · **10 beats** (RLHF absorbs the calibration footnote; DPO absorbs the wrinkle)

## Through-line
A model's behavior is a **fixed budget of probability mass over a space of possible answers.**
Post-training never adds mass — it **redistributes** it. One amber curve, area held constant
every frame (`np.trapezoid` renorm), morphs through each method. The honest spine: *a taller
peak means more **likely**, not more **correct**.* The lone exception is distillation, which is
fenced as the one move that genuinely adds a new mode.

## Honesty guardrails (non-negotiable)
- Persistent corner caption: **"NOTIONAL — a 1-D stand-in for a distribution over ~128k tokens (e.g. Llama-3)"**
- Dashed steel-blue **ghost** of the base distribution pinned behind every later stage → makes "what got lost" visible
- Axes are abstract ("space of possible answers"), never implying measured token probabilities
- VO stays in the illustrative register ("picture…", "roughly", "notionally")
- The two measured insets (calibration, pass@k) are the ONLY place with real ticks, drawn in pure PIL

## Visual gestures (each method = a distinct verb on the same curve)
| Method | Gesture | Color |
|---|---|---|
| Base | wide lumpy ridge | amber |
| SFT | slide right + mild tighten, still lumpy | amber |
| RLHF | spike into one tall peak; side-bumps wither; KL "leash" spring to ghost | amber |
| DPO | split — chosen lobe up, rejected down, gap widens | amber |
| Constitutional | RLHF press, harmful left bump carved cleanly; fed by a "constitution" card | amber |
| RLVR | funnel onto thin verified band far right | green |
| Distillation | a NEW violet hill rises where base had none; area tag ticks past 1 (fenced) | violet |

Sampling-dot heartbeat at each settled state (dots rain + pile into a histogram echoing the curve).

## VO script (10 beats, tightened, speed 1.0)
1. **Cold open** — "Every answer a model could give has some probability — a curve over all of them, showing where it places its bets. The one rule for everything that follows: this budget is fixed. Training moves it around; it can't make more." *("area = 1")*
2. **Base** — "Fresh from pre-training, that curve is wide and lumpy. It learned to continue the whole internet — so it spreads its bet across many plausible answers."
3. **SFT** — "First, we show it thousands of good examples. Its bets slide toward helpful, answer-shaped responses and tighten up — but stay lumpy. It's imitating many good answers, not picking one." *(chip: InstructGPT)*
4. **RLHF + calibration footnote** — "Now a model learns human taste, and we push for high scores. The favored answer grows into one tall, narrow peak; the rest fade. A leash keeps it near where it started. But here's the catch — a taller peak isn't a righter answer. The model just grows more confident… not more correct." *(KL leash; calibration inset late; "a taller peak ≠ more correct")*
5. **DPO + wrinkle** — "There's a shortcut: skip the scorer, skip the training loop. Just show a preferred answer and a rejected one, and widen the gap. But it only optimizes the gap — so sometimes both sink, and probability leaks where you never asked." *(chip: Zephyr-7B; "likelihood displacement" late)*
6. **Constitutional AI** — "You don't even need a person choosing. Another model can — guided by a short written constitution of plain rules. Same sculpting, a different hand on the wheel: harmful answers carved away, without collapsing into 'I can't help.'" *(chip: Claude / Constitutional AI)*
7. **RLVR** — "In the reasoning era, when we can actually check the answer — does the math work, do the tests pass? — we reward only the verified ones. The curve funnels onto that thin, correct band." *(chip: DeepSeek-R1)*
8. **RLVR crossover (thesis — hold longest)** — "It wins on the first try. But sample it many times, and the wider base model still reaches answers this sharp version gave up. Reinforcement mostly sharpens what was already there." *(pass@k inset)*
9. **Distillation (fenced exception)** — "One method breaks the rule. Distillation — a smaller model copies a bigger teacher. A genuinely new skill can appear… a new hill, where the base had none. Everything else moves mass around; this adds it." *(violet hill; area tag ticks past 1)*
10. **Closing** — "One fixed budget, pushed around six different ways — and, just once, added to. Post-training reshapes which answers are likely… far more than it invents new ones." *("reshapes WHICH answers are likely — it rarely adds NEW ones")*

## Render notes
- Author in 1080-space, SS=2; master 4K via native re-render (decide at finalization; ESRGAN fallback)
- VO-first: generate Bella → Whisper transcribe → snap beat boundaries to sentence-gap word landings
- Per-beat ~0.22s dip-to-black; concat demuxer; ambient pad bed ~13% under; soft settle/snap/funnel SFX
- numpy 2.4 → `np.trapezoid` (NOT `np.trapz`); matplotlib ABI-broken → insets in pure PIL
