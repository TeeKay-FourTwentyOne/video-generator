---
name: living-painting
description: Build a long-form, slowly-evolving "living painting" — a fixed framed scene (e.g. a figure beside a portal-mirror, or any composition with independently-evolving regions) that changes over many minutes or a full hour, assembled from a SMALL library of seamless-looping Veo clips rather than continuous generation. Use for gallery "slow TV", ambient wall pieces, hour-long durational video, or any "hang it in a frame and let it evolve" concept on a tight budget.
allowed-tools: Read, Bash, Glob, Write, Edit
---

# Living Painting (slow-evolving long-form via a looped clip library)

A "living painting" is a long (minutes→hour), low-motion, landscape video designed to hang in a frame and evolve almost imperceptibly. The defining constraint: **you cannot continuously generate an hour of Veo** (3600s × $0.10/Veo-sec ≈ $360, and Veo caps at 8s). The whole craft is making a **small library of seamless-looping clips** (~12–20) read as continuous, never-repeating evolution. Slowness is the friend — slow cross-dissolves between still-ish states look intentional and painterly, not cheap.

First built as **The Other Window** (2026-06-20): a back-turned Hammershøi woman in a quiet room beside a mirror that is a *portal* onto worlds that change; the room migrates dawn→night while the mirror cycles six unrelated worlds; one moth threads them. Brief: `briefs/the_other_window_brief.md`. Working build scripts live in that workspace's `scratch/` and are copied here under `scripts/` as templates.

## When to use

- "A painting that slowly evolves over an hour", gallery slow-TV, ambient wall art, a frame hooked to a screen.
- Any composition with **regions that evolve on different clocks** (foreground vs a window/mirror/sky).
- Budget is tight and runtime is long → the looped-library approach is the *only* feasible path, and it happens to suit the meditative register.

## The architecture: independent zones on desynced clocks

Split the frame into **zones**, each its own slowly-morphing image sequence, composited together. Give each zone its **own clock**, and make the clocks **non-commensurate** (different counts, different dissolve lengths) so their transitions never coincide — that desync is what makes the hour feel alive rather than timed.

The Other Window's two zones:
- **Foreground (slow clock):** the room + figure, one arc across the whole hour (e.g. daylight dawn→night, ~5 states × ~12 min, 30s cross-dissolves).
- **Portal/mirror (faster clock):** a fixed maskable region showing a *different* world that cycles (e.g. 6 worlds × ~10 min, 40s dissolves).

Order the portal worlds to **rhyme without locking** with the foreground arc (warm→cold worlds against dawn→night room → dark worlds land in the dark room).

## Pipeline (end to end)

### 1. Establish the fixed plate + measure the portal
- Generate the master plate with **nano-banana** (`tools/nano-banana.cjs`, `=`-form flags). Keep it restrained — clutter reads as AI. Forbid text explicitly ("Absolutely no text, no lettering, no numbers anywhere").
- If there's a portal (mirror/window/screen), **measure its actual rendered opening** — do NOT trust nominal coords. Draw a % grid on the plate, read the rectangle, then verify by drawing the rect back / compositing a test world into it. Glass is often too dark/warm to auto-threshold; eyeball + verify-by-redraw is fastest. Lock the rect (e.g. `x,y,w,h @2560×1440`); mask once, reuse for every world/state.

### 2. Generate the state library (stills)
- **Foreground light/season states:** CHAIN each new state off the master plate (`--ref=master.png`) so the composition — and crucially the portal position — stays **pixel-locked**. Chaining locks pose/geometry (good here); it lets light/color change while keeping the mirror put. Verify mirror-lock by overlaying the portal rect on every state.
- **Worlds (portal content):** generate fresh. **Veo Fast only accepts 16:9 / 9:16 — NOT 1:1** (the MCP enum lies). For a portrait portal, generate worlds at **9:16** and cover-crop into the rect (keep the subject centered so it survives the crop).
- **Mix-and-match:** for "no long repeats", give each foreground state ≥2 *distinct* actions (e.g. curtain-billow vs inward-settle) via different book-end endpoints (chain a "B" frame per action).

### 3. Generate the motion (Veo Fast, book-ended)
- `submit_veo_generation`, model **`veo-3.1-fast-prod`** (bare alias 404s), `generateAudio:false` (you layer your own bed), 1080p.
- **Worlds (faceless):** firstFrame == lastFrame == same still → clean seamless loop.
- **Figure (face/identity present):** use **two near-identical book-ends** (A→B), 6s, and close the loop with an xfade — identical A=A over a full clip idle-morphs faces. A back-turned figure is much safer (no face to morph) and dodges OTS identity drift.
- Poll/download with `tools/gcp/poll-veo-ops.cjs` → `tools/gcp/dl.cjs`. Inspect every clip yourself (contact strips); trust your eye over clip-qa's over-flagging.

### 4. Loop-unit library (the anti-repetition engine) — `scripts/build_zones.py`
From each short clip derive several **seamless loop-units** so reuse never reads as a loop:
- **Time-stretch** 2–4×: `minterpolate=mci` for continuous flow (water, clouds, sand) — smooth but slow to compute; plain `setpts` for textural shimmer (foliage, particles) — judder hidden by texture. Cap ~3× (mci hallucinates beyond 4×).
- **Ping-pong** (forward+reverse concat) for NON-directional motion (wind, water surface) — frame-exact loop, no xfade needed. NEVER ping-pong directional motion (a wave un-breaks).
- **Self-xfade** (clip xfaded with itself) to hide a residual seam on directional clips.
Build a **varied block** per state/world by `xfade`-chaining several units (interleave the two actions), then self-xfade the block so it loops seamlessly, then `-stream_loop` it to fill the hold. A ~4-min block of 6 varied units, looped, beats a 22s loop ×30.

### 5. Assemble each zone as a full-length track, then composite ONCE
- Build each zone as its own full-hour video = looped blocks joined by slow `xfade` at the state/world boundaries. Use a **single chained-xfade filtergraph** per zone (cumulative offsets) — one encode pass, not incremental re-encodes.
- **Composite the zones once** with a fixed filtergraph: scale foreground to canvas; cover-crop the world into the locked portal rect (dim ~3% + `gblur=0.6` so it sits behind glass); overlay a **static glass PNG** (faint flipped-room reflection ~10% + bevel + a corner sheen — sells "mirror" not "TV"). See `scripts/composite.sh`.
- Per-zone-full-then-composite (NOT per-state-composite-then-concat) keeps the clocks decoupled and maps 1:1 to a future live state-machine.

### 6. Audio bed — `scripts/build_audio.py`
Wordless, evolving, ElevenLabs only (in-quota ≈ free). Two clocks like the image: **pads track the foreground** (one per light state, crossfaded at its boundaries), **weather ambiences track the portal** (one per world, crossfaded ON the visual dissolves), plus sparse **bells at each world-change**. Generate short stems, loop/`acrossfade` to fill, master with `loudnorm=I=-18:TP=-1.5`.

### 7. Encode
`libx264 -crf 20 -tune film -g 48 -keyint_min 48 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart` + `-c:a aac -b:a 192k -shortest`. Fixed 2s GOP = clean loop-restart on a gallery player. Est ~1.5–4 GB/hr at 1440p.

## Cost discipline

An hour at $20 = ~200 Veo-sec of unique motion, reused ~18×. The render itself is **free** (ffmpeg compute). Budget goes to ~12–20 Veo Fast clips + nano stills; audio is in-quota. Add a 2nd figure-action per state (~$3) only if "no repeats" needs it. See [[feedback_veo_bills_attempts]].

## Gotchas (hard-won — see also the linked memories)

- **Veo rejects 1:1** → 9:16 worlds, cover-cropped. [[project_the_other_window]]
- **Measure the real portal rect**; nominal coords drift. Mask once, reuse.
- **Chain foreground states** off one plate to keep the portal pixel-locked across light changes.
- **Moth/small-motif legibility at portal scale**: a portal may be only ~500px inside a 2560 frame — size small motifs generously and confirm in a proof composite before generating the rest.
- **Prove on a slice first.** Build a 2–4 min proof (1 foreground state + 2 worlds + audio) end-to-end before committing the hour-long render (~2 hr compute, multi-GB). Validate: portal reads as glass, dissolve is dreamy, loops hide, motif is visible, no face-morph.
- **mci is the slow part** of the full render; setpts where texture allows.
- Review **locally**, don't push to GCS. [[feedback_local_review_no_gcp]]

## Future direction: indefinite generation with memory

The v1 architecture *is* the runtime: a per-zone **state machine** over a reusable **clip library**. v1 = play a fixed order once. Live = keep a growing library keyed by `(zone, state, motif-tags)` + a small JSON state, emit the next unit at hold-end via a transition policy, and generate fresh units in the background under a cost budget. The compositing/looping never changes. A traveling motif (the moth) can be the "memory cursor" carrying continuity (and visible wear) across procedurally-selected worlds.
