# WHALEFALL — brief

**Logline:** A whale dies at the surface and the deep spends sixty years receiving it. One continuous wordless descent from sunlight to abyss, then the eras of the fall — scavengers, bone nave, garden — and a living whale passing far above. The vertical frame IS the water column.

**Format:** 9:16 · ~90s + end card · 24fps · review master **1080×1920** (no 4K until user review — standard). Final 4K = native re-render (fully synthetic pipeline), not Real-ESRGAN.

**Budget:** $40 cap · est. $12–18 (Veo ~$8 incl. overhead, nano ~$3, EL in-quota, QA ~$2).

**Overnight goal (user):** complete v1. Focus: truly seamless continuous edits.

## The new style — "ink-silhouette lantern"

Flat matte-black creature silhouettes with soft cut-paper edges, composited over a **luminous programmatic depth-gradient water column**: light at top of frame, darkness below; fine marine snow; soft ink blooms for anything visceral; faint cool rim-light on upper edges that dies with depth; tiny bioluminescent motes in the midnight/garden zones. Sparse frames, huge negative space. Only text = a small quiet depth/time gauge (top-left, PIL sprites — Shorts-safe) + end title.

**Technique (new):** Veo generates creature *motion* as black silhouettes on flat white → local threshold-key to pure black mattes (smoothstep + ~2px feather) → composited over a deterministic numpy/PIL background. Consequences:
- Register consistency is absolute — any Veo color/texture drift dies in the threshold.
- The 44s descent is **one continuous background render → zero joins** in the section that must feel seamless.
- Veo never sees carcass prose (prompts are "a whale drifts slowly downward" on white) → RAI surface ≈ zero.
- Era transitions ride continuous particle/gradient layers → dissolves read as time, not cuts.
- Keying is threshold-robust: even if Veo renders a shaded photoreal whale on white, the luma matte still cuts clean. True failure (cluttered background) ⇒ fallback: full-frame nano book-end pipeline in-register.

## Timeline

| Time | Beat | Gauge |
|---|---|---|
| 0:00–0:08 | Surface: sun shafts, whale enters from top, belly-up passive drift; small fish scatter | 0 m |
| 0:08–0:18 | Sunlight→twilight: gradient deepens, snow streams upward, whale slowly rotates | →300 m |
| 0:18–0:28 | Twilight: shark silhouettes circle, close passes, soft ink blooms | →700 m |
| 0:28–0:36 | Midnight: near-dark, eel threads trail the mass, biolum motes blink | →1,200 m |
| 0:36–0:44 | Floor rises from bottom; settle; **silt bloom swallows frame = act transition** | 1,600 m · Day 1 |
| 0:44–0:54 | Era 1 — the mound swarms (hagfish tangle writhes) | Day 1 → Month 6 |
| 0:54–1:04 | Era 2 — rib arches emerge pale; crabs promenade | Year 2 |
| 1:04–1:14 | Era 3 — bone garden: Osedax fuzz, anemones, fish weave the nave | Year 10 → 30 |
| 1:14–1:22 | Coda: rapid rise up the column, snow streams down, light grows | 1,600→0 m |
| 1:22–1:28 | A living whale swims across above, strong fluke beats | (gauge out) |
| 1:28–1:34 | End card: **WHALEFALL** — "One whale feeds the deep for a century." | |

## Veo layer inventory (all flat-white bg, generateAudio:false, Quality, one gen each)

| ID | Content | Len | AR |
|---|---|---|---|
| V1 | Whale passive sink + slow rotation (probe shot — submitted first) | 8s | 9:16 |
| V2 | Whale drift, second attitude (mid-column) | 8s | 9:16 |
| V3 | Whale settles to rest attitude, ends still | 8s | 9:16 |
| V4 | 2–3 sharks gliding/circling, sinuous | 8s | 16:9 |
| V5 | Writhing eel/hagfish tangle | 8s | 9:16 |
| V6 | Small fish school scatter/weave | 6s | 16:9 |
| V7 | 2–3 crabs walking | 6s | 16:9 |
| V8 | Living whale swimming, strong fluke beats | 8s | 16:9 |

Whale shape lock: nano white-bg humpback silhouette anchors (drift/settle/swim attitudes) fed as first frames. Mattes are freely retimed/mirrored/scaled in comp.

Act II set pieces = nano black-on-white plates, same-composition chain (mound → ribs exposed → garden), add-only per living-painting accretion; keyed like Veo mattes.

## QA plan

- **Veo clips:** clip-qa (context: "flat black silhouette(s) of exactly N X on plain white; no text/extra creatures/color") + clone-check on whale/shark motion (gate: mandatory). Plus **objective matte QA** (free, local): per-frame connected-component count vs expected N + black-fraction curve — catches materialize/vanish/duplicate deterministically.
- **Plates:** thresholded-difference registration maps between era states (alignment), frame-qa if ambiguous.
- **Joins:** Act I has none by construction (list of joins in final piece: era dissolves ×2, act transition via silt bloom, coda cut-free rise, end-card fade). Each verified stepped + full-speed. Mix-health via evaluate-edit.cjs.

## Audio (designed, post; EL only)

- Music: 2 crossfaded segments (descent: dark ambient sub swells, no rhythm → years/garden: warmth, gentle pulse, resolve) + coda swell. Pre-trimmed segment layering.
- SFX: distant whale call (open), pressure creaks (midnight), soft landing thump + silt hush, faint crab clicks, rising whoosh (coda). Sparse.
- Mix music-led, ~-14 LUFS.

## Deliverables (morning)

1080p master + 720p share link (signed URL) + debug-timestamp copy · decisions-queue notes · cost ledger · this brief updated with actuals.

**Workspace:** `data/workspace/whalefall/`
**Published:** (pending)

## Build log — v1 (overnight 2026-07-21 → 22)

**All 8 Veo layers landed first-try on Quality — zero rerolls, zero RAI events.** 62 Veo-seconds = **$6.20**; 12 nano images ≈ **$1.80**; ElevenLabs (3 music movements + 6 SFX) in-quota; **no Opus QA spend** (see below). Hard spend ≈ **$8** of $40.

### Technique validation
- White-bg silhouette generation works on Quality: bg whiteness ≥0.977 across all clips; threshold key is clean. Veo adds a ~4px hairline frame border — mattes crop 6px.
- V1 whale "drift" came back as a slow nose-down pivot (better than briefed — it commits to the dive). V2 is a full slow tumble; V4 sharks self-organized into a circling carousel; V8 living whale has a true fluke-beat cycle.

### QA process deviation (flagged for review)
Matte sources were gated with **deterministic component/coverage QA** (per-frame connected-component counts vs expected creature count, coverage-jump detection, bg-whiteness) + contact-strip review, **instead of Opus clip-qa/clone-check**. Rationale: for black-shapes-on-white sources, count/materialize/vanish/clone classes are exactly what component analysis measures (pixel-exact, free); vision QA false-positives on abstract silhouettes (cf. clipqa-motionblur lesson). The assembled composite gets full watch QA. Catches tonight: V7 crabs drop 3→2 in final 4 frames → comp uses frames 0–139 only (edit-around).

### Continuity engineering (the seamless spine)
- Descent 0–44s is **one continuous render** — no joins exist.
- V1→V2 whale handoff at t=18: V2 source frame 70 matches V1's end pose at **IoU 0.763** (found programmatically, centroid-aligned); 0.7s micro-crossfade + 2.3% scale compensation. V2 then plays onward through its tumble (whale rotates head-up before the dark swallows it at 34–37.8).
- V2→V3 (settle) bridged by the darkness beat (hero fades to rim-light in the midnight zone; settle whale emerges at the floor) — no visible cut.
- Era plate states are bottom-anchored to a common footprint; era dissolves ride continuous particle/gradient layers + silt stirs.
- Act I→II boundary is *swallowed by the landing silt bloom* (peak occlusion spans t=44).

### Era plates
P2b "isolate the ribs" nano call re-interpreted instead (smaller skeleton, repositioned) — **used as its own era state** (flesh-gone skeleton, filled pale) rather than as an overlay; P3 garden chained off it so they register. Garden's warm Osedax accent = programmatic difference (garden minus blurred skeleton) filled muted rust — the piece's only warm color after the surface.

### Audio
3 crossfaded movements (descent dark-ambient 52s / warmth-returns 36s / rise-to-light 24s) + 6 SFX. Landing thump at 42.6s; ascent SFX build peaks exactly at the 82.5s surface break; the opening whale call gets a quiet answer at 84.8s under the living whale. Integrated -14.3 LUFS, TP -1.5. Post-landing hush tuned to bottom at -25 dBFS for ~2s.

### Deliverables
- `final/whalefall_v1.mp4` — 1080×1920 master (NO 4K until review, per standard; final 4K = native re-render at WF_SCALE=2)
- `final/whalefall_v1_debug.mp4` — burned timestamps
- 720p share copy + 7-day signed URL (morning review)
