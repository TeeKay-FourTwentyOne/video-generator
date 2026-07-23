# Cherries Thawing — brief

**Logline:** A photoreal moving still-life. A clear glass mixing bowl of frozen cherries thaws on a countertop. No action, no hands, nothing eaten. The only event is the thaw itself.

**Format:** 9:16 vertical · 32s (4 Veo clips × 8s) · 4K final · static locked camera.

**Look (approved 2026-06-28):** Photorealistic, *not* painterly. Soft natural daylight from frame-left (window). Muted, desaturated, cool palette — restrained and quiet. Neutral pale matte countertop, soft out-of-focus neutral background, shallow depth of field. Clear round glass mixing bowl. Cherries are deep *muted* garnet (never candy-red).

## The thaw arc (5 nano anchors → 4 book-ended Veo clips)

| Anchor | State |
|--------|-------|
| 0 | Fully frozen — cherries crusted in white freezer rime + ice crystals, pale, matte; glass lightly fogged. |
| 1 | Frost begins to melt — rime turns to a wet sheen; first faint condensation beads on the cold glass. |
| 2 | Glossy wet — frost gone, cherries darkened to muted garnet, skins reflective; condensation droplets on glass. |
| 3 | First juice — a thin muted-red pool of meltwater/juice at the bowl bottom (visible through glass); condensation streaks running down the glass; cherries settle slightly. |
| 4 | Full thaw — glossy deep cherries sitting in a shallow pool of muted pink-red juice; glass streaked with run-down condensation; a bead about to fall. |

Clips: Veo book-end interpolates 0→1, 1→2, 2→3, 3→4.

## Continuity method
- Anchor 0 generated fresh (sets composition / bowl / cherry arrangement / light).
- Anchors 1–4 **chained off the previous frame** (nano img2img), add-only state delta. Name what to PRESERVE (bowl, every cherry's position, counter, background, **lighting**), describe only what CHANGES. Hold lighting identical across all anchors (a nano light-change forces a global redraw that breaks the pixel-lock).
- Pose-lock is desired here — the cherries must not move.

## QA gate
- `frame-qa` each anchor vs anchor 0 (preserve = cherry positions/count + bowl + light; change = the melt delta).
- `anchor-drift --mode=within-clip` each consecutive pair. static = "bowl, every cherry's position/count, the countertop, the lighting". motivated = "frost melting, surfaces wetting, juice level rising, condensation forming/running".
- `clip-qa` each generated clip. context = "exactly one bowl, fixed number of cherries in fixed positions; ONLY frost/wetness/juice should change; no cherry should appear, vanish, multiply, or move; no hands; no camera movement."
- `clone-check` N/A — no subject (person) motion.

## Veo
- Quality, 8s, 9:16, `generateAudio: false` (designed soundscape in post).
- Prompt = melt motion ONLY between the two anchor states. Explicitly: locked tripod, no camera move, no hands, no person, just the bowl. No text.

## Audio (designed, no music)
- Room-tone bed (low fridge hum, faint clock) full length.
- Soft frost crackle in first ~10s.
- Meltwater **drips** — sparse mid-piece, accelerating toward the end (the payoff).
- Near-subliminal warm drone underneath, very low level.
- ElevenLabs SFX + drone, mixed in post; Veo native audio suppressed.

## Cost estimate
~$10–13 (4 Veo 8s clips + ~5–10 nano gens + QA Opus calls + ElevenLabs SFX + upscale compute).

**Workspace:** `data/workspace/cherries-thawing/`
**Published:** (pending)
