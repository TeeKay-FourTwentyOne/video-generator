# Video Generation Pricing Reference

Last updated: 2026-03-01

## Veo Video Generation (Vertex AI)

Rates verified against the GCP billing export 2026-08-17 (the previous
cheap-tier numbers in this file were wrong on every row). $/REQUESTED second:

| Tier | Resolution | Audio | $/sec | 4s | 6s | 8s |
|------|-----------|-------|-------|-----|-----|-----|
| fast (`veo-3.1-fast-prod`) | 720p | no | $0.08 | $0.32 | $0.48 | $0.64 |
| fast | 1080p | no | $0.10 | $0.40 | $0.60 | $0.80 |
| fast | 720p | yes | $0.10 | $0.40 | $0.60 | $0.80 |
| fast | 1080p | yes | $0.12 | $0.48 | $0.72 | $0.96 |
| quality (`veo-3.1-prod`) | any | no | $0.20 | $0.80 | $1.20 | $1.60 |
| quality | any | yes | $0.40 | $1.60 | $2.40 | $3.20 |

Billing rules (all verified against the export):
- **Every submission bills** — RAI-filtered and hung operations included.
- **Duration snaps by a floor rule and bills the snapped value** (a 7s request
  bills 8s). Only request durations in {4, 6, 8}.
- Model aliases: use `veo-3.1-fast-prod` / `veo-3.1-prod`. The bare alias
  `veo-3.1-fast` maps to a dead preview model (veo.ts:17); bare names 404.
- Both MCP entry points (`submit_veo_generation`, `create_job`) default to the
  QUALITY model at 8s with audio/resolution unsent — a bare call bills
  $1.60–$3.20. Pass `model`, `durationSeconds`, `generateAudio`, `resolution`
  explicitly on every call, and run `python3 tools/veo-budget.py preflight`
  first on budget-capped projects.

## Imagen Image Generation (Vertex AI)

| Model | $/image | Notes |
|-------|---------|-------|
| `imagen-3.0-generate-002` | ~$0.04 | Standard quality |
| `imagen-4.0-generate-001` | ~$0.06 | Best quality |

Used for: character lock reference images, first/last frame generation, environment references.

## ElevenLabs Audio

| Service | Cost | Notes |
|---------|------|-------|
| TTS | ~$0.30/1K chars | Varies by plan |
| Music generation | ~$0.05/sec | Short clips only |
| Sound effects | ~$0.02/sec | |

## Cost Estimation Formula

### Per-Shot Cost

```
draft_cost = num_drafts × duration × $0.08-0.12  (Veo 3.1 Fast; see tier table)
final_cost = 1 × duration × $0.40                (Veo 3.1 quality + audio)
frame_cost = num_reference_images × $0.04      (Imagen, if needed)
shot_total = draft_cost + final_cost + frame_cost
```

### Project Cost Estimate

```
video_cost    = num_shots × avg_shot_cost
audio_cost    = total_tts_chars / 1000 × $0.30 + music_seconds × $0.05
image_cost    = (num_characters + num_environments) × $0.04
────────────────────────────────────────────────────
total         = video_cost + audio_cost + image_cost
```

### Example Projects

| Project Type | Shots | Duration | Drafts/Shot | Est. Cost |
|-------------|-------|----------|-------------|-----------|
| Short (30s) | 4 | 8s each | 2 | ~$10-14 |
| Medium (60s) | 8 | 8s each | 2 | ~$22-28 |
| Long (2min) | 16 | 8s each | 2 | ~$44-56 |
| Long (2min, no drafts) | 16 | 8s each | 0 (3 finals) | ~$102-154 |

*Estimates include ~15-25% buffer for retries, reference images, and audio.*

## Draft-Then-Final Strategy

### How It Works

1. **Draft pass**: Generate with `veo-3.1-fast-prod` ($0.08–0.12/sec by res/audio) to preview compositions
2. **Review**: Pick drafts that work (composition, movement, framing)
3. **Final pass**: Re-generate with `veo-3.1-prod` ($0.40/sec with audio) using same seed OR extracted frames

### Seed Replay (Preferred)

The Veo API supports a `seed` parameter (uint32, range 0–4,294,967,295). Same seed + same prompt + same parameters = deterministic output. **Cross-model seed compatibility (Fast→Standard) needs testing** — may produce similar but not identical results.

### Frame Constraint (Fallback)

If seed replay doesn't transfer across models:
1. Extract first frame from good draft via `extract_frame`
2. Optionally extract last frame too
3. Re-generate with full model using those as `referenceImagePath` / `lastFramePath`
4. The expensive model adds quality while following the same visual structure

### API Parameters Not Yet Implemented

| Parameter | Type | Purpose |
|-----------|------|---------|
| `seed` | uint32 | Deterministic generation |
| `generateAudio` | boolean | Enable/disable native audio |
| `resolution` | string | "720p", "1080p", "4k" |

These need to be added to `mcp/video-generator/src/clients/veo.ts`.

## Sources

- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Veo API Reference](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation)
- [Veo 3 Pricing Updates (Google Blog)](https://developers.googleblog.com/veo-3-and-veo-3-fast-new-pricing-new-configurations-and-better-resolution/)
- [CostGoat Veo Calculator](https://costgoat.com/pricing/google-veo)
