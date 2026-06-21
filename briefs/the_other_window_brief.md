# THE OTHER WINDOW — Living Painting (Production Brief v1)

**Date:** 2026-06-20
**Slug:** `the-other-window` — workspace `data/workspace/the-other-window/`
**Format:** 16:9 **landscape**, 2560×1440 @ 24fps, **3600s (one hour)**
**Use:** Gallery "slow TV" — a pre-rendered hour designed to hang in a picture frame like a slowly-evolving painting. Meditative, **wordless** (no dialogue, no titles).
**Pipeline:** Veo 3.1 **Fast** (book-ended off nano-banana stills) → mci/setpts stretch → ping-pong / self-xfade loop units → `-stream_loop` hold fills → per-zone hour → one fixed mirror-composite pass → ElevenLabs ambient bed/SFX. Built from a **small reusable clip library** (~12 Veo clips), not continuous novel generation.
**Budget:** $16.83 of $20 (see table). Veo bills every attempt; 30% reroll margin baked in.
**End-state:** the v1 architecture *is* the future runtime — a per-zone state machine over a clip library. v1 = run the engine once with a fixed policy and a frozen library.

---

## PROOF v1 REVISIONS (2026-06-20 — after the 180s proof slice)

Proof slice (`final/the_other_window_proof_v1.mp4`, FG-morning + beach→forest dissolve + audio bed, ~$3.80) validated the pipeline. User approved the direction ("really good"). Changes for the full build:

- **Portal geometry re-measured.** The brief's nominal rect was off (world sat low-right inside the frame). LOCKED: inner portal **(x=1712, y=96, w=516, h=694)** @2560×1440. Mask once, reuse.
- **Veo aspect:** Fast **rejects 1:1** (only 16:9 / 9:16). Worlds are generated at **9:16** and cover-cropped into the portrait portal (moth centered to survive the crop). FG room at 16:9.
- **Keep the billowing curtain.** Veo's large curtain billow was flagged as off-register; user *likes* it. Do not tame the FG curtain.
- **Significant change over the hour** + **mix-and-match (no long repeats):** within each ~12-min hold, don't loop one unit — interleave a small per-zone library of distinct action/world loop-units (+ ping-pong/reverse/speed variants), shuffled with no-immediate-repeat and slow xfades. Maps 1:1 to the future state machine.
- **Reusable from the proof:** `clips/fg_morning.mp4`, `clips/mw_beach.mp4`, `clips/mw_forest.mp4` (+ stills) carry forward into the library.
- Minor: worlds desaturate slightly to sit in the muted room; reflection/sheen tunable if the portal reads painting-ish.

---

## Logline

A painting of a contemplative woman alone in a still, grey Hammershøi interior. Beside her hangs a large mirror — but the mirror is not reflecting the room. It is a portal onto another world, and that world keeps changing. Over one hour the room's daylight migrates dawn → night on a slow clock while the mirror cycles, faster, through six unrelated worlds. A single pale-gold moth threads all of them, and at the end it comes home.

## Concept & register

The anchor is **Vilhelm Hammershøi's** grey Copenhagen interiors (Strandgade 30): a woman seen three-quarter-from-behind, alone in a near-empty muted room, *no narrative event*. This register is the whole solution — Hammershøi rooms already feel like time held still, so when the woman's loop repeats every ~12 minutes, a slow breath or a few-degree head-incline is indistinguishable from a painting that happens to breathe. The back-turned figure also dodges Veo's worst RAI and identity-drift traps (the face is never the load-bearing element).

Two secondary anchors: **Vermeer's** single soft lateral north-window light is the engine that lets one frame migrate dawn→night convincingly (we are animating Vermeer's light across an hour). The **Velázquez / Van Eyck / Rokeby mirror tradition** (a picture-within-the-picture that shows what the room cannot contain) makes the portal read as *art*, not VFX — which is what protects the meditative tone. We invert the tradition's logic: the mirror reveals *other* worlds, not more of this room.

Everything moves, gently, all the time — nothing is ever fully static — but slow and dreamlike. Restraint is mandatory: clutter reads as AI-generated and breaks the "real painting" spell.

## The painting (composition + fixed mirror geometry)

**Frame:** 2560×1440. A quiet Hammershøi room shot square-on, eye-level, **camera locked for the entire hour** — all motion is interior to the image.

**Room:** A single greyed-taupe (grey-green) plaster wall fills the upper two-thirds; a pale wood floor in soft perspective fills the lower third. The room is nearly bare. One tall multi-pane **window sits at the far-left edge** (x ≈ 0.00–0.10, only its right jamb, a sliver of glass, and a hanging muslin curtain visible) — the **single light source**, a north-window soft key raking rightward. The curtain is the one foreground motion alibi (it stirs without implying a person moved).

**The woman:** Seated **left-of-center** (x ≈ 0.18–0.46, y ≈ 0.30–0.92), **three-quarter-back view** — back of the shoulder, line of the neck, side of the jaw, *not a front face*. Simple ladder-back chair at a small bare table, body angled gently toward the window light. Dark hair gathered low; a plain long slate/charcoal-blue dress so she reads as one calm tonal block. Contemplative, near-still, gazing toward the window / middle distance — **pointedly not looking at the mirror** (she is unaware of the portal; this also keeps her eyeline from forcing a reflection relationship).

**The mirror:** Hangs in the **right third**, separated from the woman by a deliberate band of empty grey wall (x ≈ 0.46–0.55 — the breathing gap that makes the frame read as *authored*, not cluttered). A large rectangular wall mirror in a plain dark walnut frame, **hung flat and square** (axis-aligned → cleanly maskable). Its base sits above the woman's head height, so the two masses **never overlap** — there is no over-the-shoulder reflection of her, which sidesteps Veo's OTS identity-drift failure mode entirely. Three masses in asymmetric balance: the woman (lower-left dark mass), the mirror-portal (upper-right luminous cool window into elsewhere), and the empty grey wall + floor (the connective field).

**Fixed mirror geometry** (normalized 0–1, x right / y down — **constant for the whole hour** so one rectangular mask composites every world identically):

| Element | x-range | y-range | px @ 2560×1440 |
|---|---|---|---|
| **Outer frame** (walnut, on wall) | 0.615 – 0.865 | 0.205 – 0.635 | ≈ 1575–2214 × 295–914 (≈ 640 × 619) |
| **Inner portal** (the maskable glass) | 0.635 – 0.845 | 0.225 – 0.615 | **≈ 1626–2163 × 324–886 (≈ 538 × 562)** |

The **inner portal rectangle (≈538×562) is the mask**: every world clip is scaled/cropped into this exact region. The ~0.020 walnut band between outer and inner rects is matte, with a single subtle warm bevel highlight along the **left and top inner edges** (light comes from frame-left) selling the glass as recessed. A fixed faint glass-sheen gradient lives in the top-left corner. The frame throws a thin soft drop-shadow down-and-right onto the wall. Because the hang is square and flat, the inner rect is identical every frame — **mask once, reuse for all 6 worlds across all 5 daylight states.**

**Palette (constant base):** muted Hammershøi oil — greyed taupe / slate-grey-green walls, chalk-white trim, pale honey-to-ash floor, the woman a single slate-charcoal / dusty-blue mass, dark walnut frame. Low saturation, oil-paint not video.

## The hour's two clocks

Two **independent** clocks, both filled by looping short clips, deliberately **never aligned** so transitions never coincide and the piece feels alive rather than timed:

- **FOREGROUND (woman + room) — SLOW:** one arc across the hour, **5 daylight states** of ~696s each, joined by 30s xfades (state boundaries ≈ 696 / 1422 / 2148 / 2874 s).
- **MIRROR (portal) — FASTER:** **6 worlds** of ~567s each (≈9.4 min), joined by 40s dissolves.

5 states with 30s xfades vs 6 worlds with 40s dissolves → different counts and different dissolve lengths → the two clocks' transitions are mutually non-commensurate. Whenever the room is bright the worlds tend bright; as the room sinks to night the worlds sink to cold and dark — the clocks **rhyme without locking**.

## The 5 daylight states

Same locked composition; only light and the woman's micro-motion change. Each is **1 Veo clip @6s** with two *distinct, near-identical* book-end stills (NOT a frame-exact wrap — that idle-morphs faces; see pipeline).

| # | State | Light & mood | Woman's motion (Veo, motion-only) |
|---|---|---|---|
| 1 | **Dawn** | Cool blue-slate room, one warm rose-gold sliver raking from the left window. Lowest luminance, highest temp-split. Expectant, held breath. Portal already glows brighter than the sleeping room. | Curtain stirs imperceptibly; one slow shallow breath (faint shoulder rise); head inclines a few degrees and settles; dust drifts in the dawn band. |
| 2 | **Morning** | Whole room lifts to warm grey-cream; even lateral light models wall and woman; faint long shadows lean right. Most Vermeer-warm; cleanest read of the composition. Serene, awake. | Curtain breathes in/out; a single slow blink and a barely-perceptible head-turn a few degrees toward the window, then back; faint shoulder shift with breath; dust floats in the beam. |
| 3 | **Midday** | Brightest, flattest, near-shadowless chalk-grey wall; high ambient fill. Highest luminance, lowest contrast/saturation. The rest plateau — least eventful foreground so the mirror carries the midpoint. | Most still of the hour: one slow breath and one slow blink, **no head turn**. Faintest curtain stir. |
| 4 | **Dusk** | Long amber-gold light from the left; wall glows ochre left / falls to warm umber shadow right (mirror sits in gathering dusk-shadow, portal-glow clearly brightest). Richest, highest-saturation state. Bittersweet, valedictory. | Curtain stirs and settles in a warm draft; she slowly turns her head a few degrees away from the window toward the room — the one slightly larger, "more aware" movement of the hour — then her gaze lowers and she stills; dust glows in the low gold. |
| 5 | **Night** | Window dark blue-black; room lit only by one small warm amber lamp-pool off frame-left, falling off fast to deep blue-black. Lowest luminance, highest contrast, smallest lit area. **The mirror-portal is now the brightest thing in the frame**, its color-spill halo at its most visible. Intimate, mysterious. | Lamp-pool flickers very faintly; she breathes slowly, hands still on the table; one slow blink; dark curtain barely moves. Motion at its most reduced — the eye is drawn to the glowing mirror. |

Light states ride a temperature/luminance arc **on top of** the constant base palette: dawn (split-temp, low lum) → morning (warm cream, mid) → midday (cool-neutral, highest lum / lowest sat) → dusk (amber/ochre, highest sat) → night (blue-black + one amber pool, lowest lum / highest contrast).

## The 6 mirror worlds

Faceless → **identical 8s book-end is safe** (no face-morph risk). Ordered as a slow tonal descent (warm/open/bright → cold/enclosed/dark) that rhymes with the room's dawn→night, **bookended warm-to-warm** (beach gold → desert ember) with a cold trough in the middle, which both reads as a satisfying loop and seeds the final dissolve-to-her-room. Each world is one Veo clip with **the moth baked into the shot** (placed in a different screen position per world so a careful watcher tracks it migrating).

| # | World | Visual | Inherent motion (Veo, motion-only) | Loop | Moth placement | Portal color-spill / audio |
|---|---|---|---|---|---|---|
| 1 | **The Wide Shore** | Broad sunlit beach, mid-morning. Pale wet sand, a long low surf line, an immense soft-blue sky. Warmest, most open, biggest sky. | Waves roll in and slide back; foam advances/retreats; high clouds drift; moth rides the offshore wind low over the foam line. | **directional** — mci ×2, **no ping-pong**, self-xfade | low over the foam line, riding the wind | sea-teal halo. **W1** surf + faint gulls + wind. Bell: bright, short reverb. |
| 2 | **The Standing Wood** | Deep old forest. Tall straight trunks into soft green depth; a few warm light shafts on moss. Enclosed, vertical, intimate after the shore. | High leaves/branches sway; dappled light shifts on the floor; dust & pollen drift in the shafts; moth threads one light beam. | **textural** — setpts ×2, ping-pong ×2 | threading a green light-shaft between trunks | forest-green halo. **W2** wind in leaves + sparse distant birdsong. Bell: natural, medium decay. |
| 3 | **The Lamplit City at Dusk** | Quiet empty street at blue hour. Wet cobblestones, a row of warm amber streetlamps just lit against a cooling-blue sky, lit windows, faint mist. **No neon, no people, no cars, no signage.** The warm/cool **hinge**, and the one world that rhymes with her own lamplit interior — a deliberate near-miss foreshadowing the return-to-room. | Mist drifts down the street; lamp reflections shimmer on wet stone; lamplight breathes with an almost-imperceptible flicker; moth circles the nearest streetlamp. | **non-directional** — mci ×2, ping-pong ×2 | circling the nearest streetlamp | sodium-amber halo. **W3** faint distant city hum, no voices. Bell: slightly metallic/bright, dry. |
| 4 | **The White Field** | Empty snowfield under a flat pale sky, steady falling snow. A few far dark bare trees / low ridge for scale. First fully cold, desaturated world; max contrast for the gold moth. | Snow falls steadily and drifts; a thin veil of surface snow lifts and curls; far trees barely stir; moth crosses against the snow, the only warm color. | **falling snow reads either way** — mci ×3, ping-pong ×2 | a single warm speck crossing L→R | snow-blue halo. **W4** hushed near-silence + very faint icy wind (drops to ~−28 dB; pad most exposed). Bell: damped, muffled. |
| 5 | **The Blue Deep** | Underwater, mid-column, calm sea. Soft shafts filter from a far surface; suspended particles drift; deeper blue fades to dark below. Coldest, most enclosing — the "deep" of the cycle; the moth is most impossibly out of place. | Light shafts waver from above; particles drift and rise; the column sways with a slow current; moth glows faintly as it sinks and rises. | **particulate** — setpts ×2, ping-pong ×2 | sinking and rising in the blue current | deep-blue halo. **W5** muffled low tones + slow far bubbling. Whole weather bus gently lowpassed (submerged); pad slightly lowpassed too. Bell: heavily low-passed + long reverb. |
| 6 | **The Ember Desert at Night** | Still desert at night under a deep starfield. Cool blue dunes to the horizon; in the near foreground a single dying ember-glow breathing orange. Cold air, one surviving warmth — the bridge back to her night-lit room and the moth's homecoming. | Ember pulses/breathes; a few faint sparks lift and fade; fine sand drifts off the dune crests in a night wind; stars shimmer; moth hovers just above the ember, wings catching the orange. | **directional sand** — mci ×2, **no ping-pong**, self-xfade | hovering just above the ember | warm-ember halo. **W6** dry wind over open sand, low gusts, vast emptiness. Bell: dry, long air decay, slight up-detune (heat-shimmer), highest space reverb. |

**Portal color-spill** is the single chromatic element that does *not* belong to the room's daylight palette — each world casts a soft radial halo of its dominant hue ~40 px beyond the frame onto the grey wall. This is the visual carrier of the memory-motif (see below).

## The continuity motif (how it's introduced & echoes)

**The motif is a single small pale-gold moth** — luminous, the warm color of late-afternoon light, no bigger than a thumbprint. It is the one thing the same in every world. It is always small, always drifting, **never the subject** — you have to be watching for it. It is the proof the worlds are connected, that something has been traveling all along, and that the woman and the mirror were never really separate.

- **Introduced (Hour 0:00–~0:12, foreground, dawn):** a pale-gold moth drifts in from off-frame and rests on the rim of the window beside the mirror, or circles the unlit lamp once and settles. It is the warmest point of color in the cool dawn room — the eye finds it unprompted. *This is its home.*
- **Crosses the worlds (each mirror world, baked into that world's clip):** the identical moth appears small and drifting in every portal world in turn, in a different screen position and a different relationship to that world's motion each time (see the worlds table). A careful watcher tracks it migrating world to world; a glancer never notices.
- **Returns / closes the loop (final ~10–15 min):** the foreground reaches **night** and the woman is still; the mirror completes the **desert** and begins one last dissolve — but instead of cycling to a new unrelated world, **the portal resolves into HER OWN ROOM** seen from the mirror's side, dim and night-blue, with the moth drifting back across it toward the window. On the final foreground beat the same moth settles on the rim of her window again, exactly where it began, now lit by night instead of dawn. The "other world" behind the glass was this one all along. Rewards a full watch; invisible on a glance.
- **Audio sibling of the motif:** the **bell** is the room's voice answering each portal change — *the same bell sample* every time, re-pitched/EQ'd to belong to the incoming world (bright for beach, damped for snow, low-passed+reverb underwater…). The room "remembers" and answers each world the way the moth carries continuity through them. A fuller bell at ~3500s, as the room goes to night and the portal resolves to her own room, is the memory resolving.

**The color thread reinforces it:** each world's portal color-spill is allowed to faintly **linger on the wall after** that world ends (a teal cast remaining after the beach, etc.), so worlds quietly tint the room. At night, when the room is darkest, the portal-spill is the dominant color in the frame — by the hour's end the worlds have literally colored the room the woman sits in.

## The audio bed

ElevenLabs only (within the Creator 300k-credit quota ≈ free; well under the $20 cap, which Veo dominates). **Generate short seamless stems, loop in ffmpeg.** Total generated material ≈ 6–8 minutes for a 60-minute piece. Master to ~−18 LUFS integrated (gallery-quiet, long-listen safe), true-peak −1.5 dB.

Four buses, two clocks:

- **L1 — Interior drone/pad (slow, the room clock):** one sustained tonal pad in a warm slightly-melancholic modal key (D dorian / A-minor feel). The harmonic ground; never silent (~bed level, −16 LUFS). Its **timbre migrates across the hour to track the daylight arc** — realized as 5 pad stems (P1 dawn → P5 night) crossfaded over the full hour, one per ~720s light state, with the P_n→P_(n+1) acrossfade (60s) centered on each foreground daylight boundary.
- **L2 — Weather (faster, the portal clock):** the most active layer; cross-modally tracks whichever world the mirror shows. 6 world ambiences (W1–W6 above), each looped to fill its ~567s hold, acrossfading world→world **time-aligned to the visual dissolve** (audio xfade duration = visual dissolve duration = 40s). Sits ~−20 to −22 LUFS so it reads as "leaking through the glass," not the room's own sound.
- **L3 — Interior foley / memory punctuation (sparse):** a near-subliminal clock **tick** (~−30 dB, ~every 2s, deliberately *not* locked to any musical pulse) as the room's own time; plus the **single distant bell** struck at each of the 6 world-dissolves (recolored per incoming world — the motif) and a fuller bell at ~3500s.
- **L4 — Return/echo bus (future hook):** a long-reverb send fed only by the bell and by the transient edges of the weather crossfades. In v1 it is baked into the bell renders; documented as its own bus so the future memory engine can route "recalled" elements (an earlier world's surf faintly returning under a later world) through it as the literal audio implementation of memory.

**Anti-repetition** (keep an hour of loops from sounding looped): per-tile micro-detune (`atempo` 0.985–1.015) so no two passes are bit-identical; long self-crossfades (≥5s, `c1=tri:c2=tri`); a slow level+lowpass LFO per hold on a period (~90–130s) **not** a multiple of the loop length; and the three clocks (pad ~45s, weather ~35s, tick 2s) are mutually non-commensurate so the combined mix's true period is far longer than the hour. The 6 + 1 bells are the only "events" — their sparseness reads as composition, not artifact.

**ElevenLabs generation plan (~13 base + ~3 reroll, all in quota):**

- `generate_music` ×5 pads, `duration_seconds` 40–45, instrumental, low tension/energy:
  - P1 dawn — "slow sustained ambient drone pad, warm low strings + soft sine swell, D dorian, no percussion, no melody, gentle drift, first light, hopeful-melancholic, seamless loopable" — mood contemplative, tension 0.15, energy 0.10
  - P2 morning — "sustained warm ambient pad, slightly brighter major-leaning, airy high partials, calm midday stillness, no rhythm, no melody, seamless" — serene, 0.10 / 0.15
  - P3 dusk — "low warm ambient drone, amber dusk, faint detuned strings, descending harmonic settle, no rhythm, seamless" — bittersweet, 0.20 / 0.10
  - P4 night-approach — "deep slow ambient pad, cooler minor color, distant low cello, hushed, no rhythm/melody, seamless" — mysterious, 0.25 / 0.08
  - P5 night — "very low sustained sub-bass drone + soft pad, near-silent room at night, single held minor chord, no rhythm, seamless" — peaceful, 0.20 / 0.05
- `generate_sound_effect` ×6 weather, `duration_seconds` 22 (the SFX cap), prompt_influence ~0.4 — self-crossfade-looped to ~18s clean loops, tiled to ~567s: W1 surf+gulls+wind / W2 wind-in-leaves+sparse birdsong / W3 faint distant city hum (no voices) / W4 hushed near-silence+faint icy wind / W5 muffled underwater low tones+slow bubbling / W6 dry desert wind+low gusts.
- `generate_sound_effect` ×2 foley: **TICK** "single soft mechanical clock tick, dry, close, no reverb" (2s, tiled at −30 dB); **BELL** "single distant bell struck once, warm, long natural decay, contemplative" (8s) — **one master bell**; per-strike pitch/EQ done in ffmpeg per incoming world. Do **not** regenerate per world — same sample recolored *is* the memory motif.

## Technical pipeline

**Decision: render PER-ZONE FULL-HOUR layers first, then composite the two zones with ONE fixed mirror filtergraph pass** (not per-state-composite-then-concat). The two zones run on independent clocks that never align, so per-state composites would force cuts at the union of both zones' boundaries (messy). Building each zone as its own clean hour, then masking world-into-room once, keeps the clocks decoupled, makes the composite trivial, and maps 1:1 to the future state machine (each zone is one independent stream).

### 1. Seamless Veo loop units (book-ending)

Submit via MCP `submit_veo_generation`, **model `veo-3.1-fast-prod`** (the bare `veo-3.1-fast` alias 404s), `aspectRatio "16:9"`. Prompts **motion-only** — describe what *moves*, never body/clothing/age; no ALL-CAPS (renders as on-screen text); no "photograph"/film-stock/"silent film" cues (bake fake intertitles/text). Veo requires first+last OR first-only; **lastFrame-only fails** ("Frame interpolation requires both an input image and a last frame") and still bills.

- **Mirror worlds (faceless):** firstFrame == lastFrame == the **same** nano still. Identical 8s book-end is safe with no face on screen → concatenating copies has no spatial jump at the wrap. `veo_seconds = 8`.
- **Foreground woman (face on screen):** do **NOT** use identical first==last @8s — Veo idle-morphs faces (eyes/jaw drift) over a full 8s hold. Generate at **`veo_seconds = 6` with two distinct, near-identical nano stills** (same pose/light, only a hair-strand or shoulder shifted) and close the loop via xfade in the timeline, not a frame-exact wrap. Avoids the face-morph failure mode entirely.

`clip-qa` every Veo result before use: `python3 tools/clip-qa.py <video> --context=...` (download via `node tools/gcp/poll-veo-ops.cjs` → `node tools/gcp/dl.cjs`).

Hide any residual seam on a self-xfade'd unit:
```bash
ffmpeg -y -i clip.mp4 -i clip.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=1.5:offset=$(echo 'DUR-1.5'|bc)[v]" \
  -map "[v]" -an -c:v libx264 -crf 18 -pix_fmt yuv420p loopunit.mp4
# output length = 2*DUR - 1.5
```

### 2. Time-stretch (apply ONCE per short clip — never to the full hour)

```bash
# (A) minterpolate mci — synthesizes new frames, smooth. ~87s wall for 8s->24s @1440p.
ffmpeg -y -i loopunit.mp4 \
  -vf "setpts=3*PTS,minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" \
  -an -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p stretched_mci.mp4

# (B) plain setpts — re-times existing frames, ~2.4s for 8s->24s, but judders on continuous flow.
ffmpeg -y -i loopunit.mp4 -vf "setpts=3*PTS" -r 24 -an -c:v libx264 -crf 18 -pix_fmt yuv420p stretched_setpts.mp4
```
Per-zone: **mci** for continuous directional flow (waves, clouds, sand, snow); **setpts** is fine for textural shimmer (forest dapple, city wet-stone, underwater particulate) — texture hides the held-frame judder, saves compute. Foreground woman: **mci ×2 only** (3–4× balloons a blink/jaw micro-motion into rubbery uncanniness). Cap: 3× for mci-smooth content, 2× for setpts content; beyond 4× mci hallucinates.

### 3. Ping-pong (forward + reverse) — primary length multiplier, NON-directional motion only

```bash
ffmpeg -y -i stretched.mp4 -filter_complex \
  "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]" \
  -map "[v]" -an -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p pingpong.mp4
# output = exactly 2x input; both the internal turn AND the wrap are frame-exact, no xfade needed.
```
**Do NOT ping-pong directional motion** (a wave rolling in, sand blowing one way) — the reverse plays it backwards (wave un-breaks) and reads as obviously rewound. For those (beach, desert), loop via the self-xfade above. Chain: Veo 8s → stretch → ping-pong → seamless unit, then `-stream_loop` to fill the hold.

### 4. Mirror composite (validated end-to-end — one fixed pass)

Two static PNGs built **once** for the fixed geometry (inner portal ≈ x 1626 y 324 w 538 h 562):
```bash
# mask: white inside portal, black outside, feathered edge (no hard bezel jump)
ffmpeg -y -f lavfi -i "color=c=black:size=2560x1440" -frames:v 1 \
  -vf "drawbox=x=1626:y=324:w=538:h=562:color=white:t=fill,gblur=sigma=6" mirror_mask.png
# glass+bevel overlay (RGBA): faint sheen band + dark beveled frame edge
ffmpeg -y -f lavfi -i "color=c=black@0.0:size=2560x1440,format=rgba" -frames:v 1 \
  -vf "drawbox=x=1626:y=324:w=538:h=562:color=white@0.10:t=14,drawbox=x=1618:y=316:w=554:h=578:color=0x40342a@0.6:t=8" mirror_glass.png
```
Composite (foreground_hour = room layer; mirror_hour = full-frame world layer):
```bash
ffmpeg -y -i foreground_hour.mp4 -i mirror_hour.mp4 -loop 1 -i mirror_mask.png -loop 1 -i mirror_glass.png \
  -filter_complex "\
    [1:v]format=yuv420p,eq=brightness=-0.02:saturation=0.92,gblur=sigma=0.6[world]; \
    [2:v]format=gray,scale=2560:1440[m]; \
    [world][m]alphamerge[worldA]; \
    [0:v][worldA]overlay=0:0:format=auto[base]; \
    [0:v]format=rgba,eq=brightness=-0.25,gblur=sigma=8,hflip[refl]; \
    [refl][2:v]alphamerge[reflA];[reflA]colorchannelmixer=aa=0.12[reflF]; \
    [base][reflF]overlay=0:0[withrefl]; \
    [withrefl][3:v]overlay=0:0,format=yuv420p[out]" \
  -map "[out]" -an -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p mirror_composite.mp4
```
Believability knobs (sell "mirror not TV"): (a) the **flipped room-glass sheen at ~12%** — this is the key lever. NOTE: because the woman sits in the *opposite* (left) third, the hflip'd plate puts mostly **empty grey wall** into the glass — a dim, heavily-blurred *abstract* glass-reflection, **not** a recognizable double of the woman. This is intentional: it reads as real glass without ever creating an over-the-shoulder identity for Veo to drift. (b) gblur 0.6 + brightness −0.02 so the world is fractionally softer/dimmer than the room. (c) feathered mask edge. (d) the per-world **color-spill halo** is a separate soft radial glow of the world's dominant hue, fed ~40px beyond the frame onto the wall (add a feathered colored overlay keyed off the world's mean hue). Mirror rect is identical the entire hour → one fixed operation.

### 5. Timeline construction

**A) Foreground zone → `foreground_hour.mp4`** (2560×1440, 3600s): per state, 1 Veo woman clip (6s, distinct near-identical book-ends) → mci ×2 → self-xfade to a ~22.5s seamless unit → `-stream_loop` to fill the **696s** hold. Join the 5 fills with `xfade=transition=fade:duration=30:offset=696` chained s0→s1→…→s4 (the daylight migration). Build incrementally (s0+s1→tmp, tmp+s2→tmp…) to keep filtergraphs small and re-runnable.

**B) Mirror zone → `mirror_hour.mp4`** (2560×1440, 3600s, **full frame** — masking happens in step 4): per world, 1 Veo clip (8s, identical book-end) → mci/setpts stretch (per table) → ping-pong if non-directional / self-xfade if directional → unit → `-stream_loop` to fill the **~567s** hold. Join the 6 fills with slow `xfade=fade` (vary with `=dissolve`/`=smoothleft` for texture), duration **40** — the "portal changes worlds" dissolves. For the closing motif, the 6th→final dissolve resolves to the **her-room** plate (a dim night-blue nano still of the room seen from the mirror's side, with the moth drifting across — one extra nano + a short Veo or stills+ffmpeg drift clip; see shot list MW-return).

Because FG (5 states, 30s xfades) and MW (6 worlds, 40s xfades) differ in count and dissolve length, their transitions never coincide → organic independent clocks.

**C) Composite:** one pass, step 4 → `living_painting_hour.mp4` (silent).

**D) Audio:** build the 3600s 4-bus bed per the audio plan; mux at final encode (`-shortest`).

`-stream_loop` fills use `-c copy` (frame-exact units → no re-encode until the xfade joins).

### 6. Final encode

```bash
ffmpeg -y -i living_painting_hour.mp4 -i ambient_bed.m4a \
  -c:v libx264 -preset slow -crf 20 -tune film \
  -g 48 -keyint_min 48 -sc_threshold 0 \
  -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -shortest living_painting_hour_final.mp4
```
crf 20 (slow gradient/dissolve content bands without bits; crf 18 for safety at ~1.7× size). `-tune film` preserves grain, avoids over-smoothing gentle motion (**not** `stillimage` — content is never truly static). `-g 48 -keyint_min 48 -sc_threshold 0` = fixed 2s GOP on a regular grid (no scene-cut keyframes — there are no hard cuts) → clean predictable seek points for a gallery player looping the hour. `+faststart` for instant loop-restart. **Est. size ~1.5–3.5 GB/hr** (low-motion floor ~0.6 GB; real grain + 11 dissolves + masked moving portal runs higher). Optional H.265 sibling (`-c:v libx265 -crf 24 -tag:v hvc1`) ~40% smaller for storage; keep H.264 as the playback master for device compatibility.

## Shot list (every Veo clip)

| ID | Zone | State/World | Veo s | Loop strategy | Motion-only prompt seed |
|---|---|---|---|---|---|
| **FG-dawn** | foreground | light 1: dawn | 6 | 2 distinct book-ends (face-safe), mci ×2, self-xfade | Quiet still interior at dawn, cool pale window light. Curtain stirs faintly; one slow shallow breath, the faint rise of a shoulder; head inclines a few degrees and settles; dust drifts in a band of dawn light. Camera locked, no cuts. Gentle room tone. |
| **FG-morning** | foreground | light 2: morning | 6 | 2 distinct book-ends, mci ×2, self-xfade | Same interior, warm even morning daylight across the wall. Curtain breathes in and out; a single slow blink and a barely-perceptible head-turn a few degrees toward the window, then back; faint shoulder shift with breath; dust floats in the beam. Locked camera, room tone. |
| **FG-midday** | foreground | light 3: midday | 6 | 2 distinct book-ends, mci ×2, self-xfade | Same interior at flat bright midday, near-shadowless. The faintest curtain stir; one slow breath and one slow blink, no head turn. The calm plateau. Locked camera, room tone. |
| **FG-dusk** | foreground | light 4: dusk | 6 | 2 distinct book-ends, mci ×2, self-xfade | Same interior, low golden dusk light raking across the room, shadows lengthening. Curtain stirs and settles in a warm draft; she slowly turns her head a few degrees toward the room interior, gaze lowers, then stills; dust glows in the low gold. Locked camera, room tone. |
| **FG-night** | foreground | light 5: night | 6 | 2 distinct book-ends, mci ×2, self-xfade | Same interior at night, a single small warm lamp-pool from off the left edge, deep blue-black beyond. The lamp flickers very faintly; slow breath, hands still on the table; one slow blink; dark curtain barely moves. Locked camera, low hum room tone. |
| **MW-beach** | mirror | world 1: beach | 8 | identical book-end (faceless), mci ×2 **directional**, no ping-pong, self-xfade | A calm beach, golden mid-morning: waves roll in and slide back along wet sand in a slow rhythm, foam advancing then retreating, a sheen of water receding; high thin clouds drift; a small pale-gold moth drifts low and unhurried over the foam line, wings fluttering. No cuts, camera perfectly still. Surf and wind. |
| **MW-forest** | mirror | world 2: forest | 8 | identical book-end, setpts ×2 **textural**, ping-pong ×2 | Deep quiet forest: high leaves and slender branches sway gently, dappled sunlight shifts slowly across a mossy floor, motes of dust and pollen drift and turn in warm shafts of light between the trunks; a small pale-gold moth threads slowly through one light beam. Camera completely still. Wind in leaves, sparse distant birdsong. |
| **MW-city** | mirror | world 3: lamplit city at dusk | 8 | identical book-end, mci ×2 **non-directional**, ping-pong ×2 | A quiet empty street at blue hour, wet cobblestones, a row of warm amber streetlamps just lit against a deep cooling-blue sky, soft mist, glowing windows. A faint mist drifts down the street, warm lamp reflections shimmer on the wet stone, the lamplight breathes with an almost-imperceptible flicker; a small pale-gold moth circles the nearest streetlamp. No people, no vehicles. Camera perfectly still. Faint distant city hum. |
| **MW-snow** | mirror | world 4: snowfield | 8 | identical book-end, mci ×3 (snow reads either way), ping-pong ×2 | A vast empty snowfield under a flat pale sky: snow falls steadily and drifts on a light wind, a thin veil of surface snow lifts and curls across the white ground, far bare trees stir imperceptibly; a single small pale-gold moth drifts slowly across the frame against the falling snow, the only warm color. Hushed. Camera completely still. Soft wind. |
| **MW-underwater** | mirror | world 5: underwater | 8 | identical book-end, setpts ×2 **particulate**, ping-pong ×2 | Underwater mid-column in a calm deep-blue sea: soft shafts of light waver and ripple down from a far surface, fine suspended particles drift and slowly rise, the whole column sways gently with a slow current, the deep below fading to dark; a small pale-gold moth glows faintly as it sinks and rises in the current, the only warm light. Submerged, camera perfectly still. Muffled water ambience. |
| **MW-desert** | mirror | world 6: ember desert at night | 8 | identical book-end, mci ×2 **directional**, no ping-pong, self-xfade | A still desert at night under a deep starry sky, cool blue dunes to the horizon, a single small dying ember glowing orange on the sand. The ember glows and breathes, a few faint sparks lift and fade, fine sand drifts off the dune crests in a soft night wind, stars shimmer; a small pale-gold moth hovers just above the ember, wings catching the orange light. Vast, unbroken, camera completely still. Soft wind. |
| **MW-return** | mirror | closing motif: the portal becomes HER ROOM (night) | (stills+ffmpeg, or 1 optional Veo 8s) | nano still of the room from the mirror's side, dim night-blue + moth drift via ffmpeg, OR 1 Veo @8s identical book-end | Dim night-blue interior seen from the mirror's side: a small pale-gold moth drifts slowly back across the room toward a dark window, the only warm point of light; everything else hushed and still. *(Prefer stills+programmatic moth-drift to save the Veo line; Veo only if the drift won't sell.)* |

**Optional (future-state primitive, NOT required for v1):** an isolated drifting-moth clip on a plain keyable background — a Veo @8s, mci ×2, ping-pong ×2 — composited as a faint overlay that the live engine can trigger into *any* zone. In v1 the moth is baked into each world clip instead, so this is a budget-line *spare*. Held in the reroll headroom.

## Budget

| Item | Unit | Qty | Subtotal |
|---|---|---|---|
| Veo Fast — foreground woman clips (dawn/morning/midday/dusk/night) @6s | $0.10/s × 6s = $0.60 | 5 | $3.00 |
| Veo Fast — mirror world clips (beach/forest/city/snow/underwater/desert) @8s | $0.10/s × 8s = $0.80 | 6 | $4.80 |
| Veo Fast — closing/motif clip (MW-return *or* isolated-moth primitive) @8s | $0.80 | 1 | $0.80 |
| **Veo subtotal (12 successful clips)** | | 12 | **$8.60** |
| Reroll margin ~30% (RAI / hung / clip-qa rejects — Veo bills every attempt) | 0.30 × $8.60 | | $2.58 |
| **Veo total incl. reroll** | | | **$11.18** |
| Nano-banana stills — FG 2 distinct ×5 (10) + MW 1 ×6 (6) + room master plate (1) + her-room return plate (1) + 1 spare | $0.15/image | 19 | $2.85 |
| ElevenLabs pads (5) + weather (6) + tick + bell, all in Creator quota | within quota | — | $0.00 |
| Anthropic QA (clip-qa / frame-qa, ~$0.14–0.24/call) | ~$0.20 × 14 | 14 | $2.80 |
| **GRAND TOTAL** | | | **$16.83** |

Headroom to the $20 cap: **$3.17** — covers ~3 extra Veo rerolls at $0.80, or the optional isolated-moth primitive if MW-return needs a real Veo clip. Stays ≤ $20 even at a worse-than-30% reroll rate. (Reroll margin for audio lives in the ElevenLabs quota, not the $20.)

## Proof-slice plan

A **2–3 min proof slice** validates compositing + loop + dissolve + audio **before** committing the full hour. Uses only **3 Veo clips** (1 FG + 2 MW), so a failed proof costs ~$2, not $17.

1. Generate the 3 lowest-risk anchors: nano stills for **FG-morning** (2 distinct), **MW-beach** (1), **MW-forest** (1). `python3 tools/frame-qa.py` each.
2. Submit 3 Veo Fast clips: FG-morning @6s (distinct book-ends), MW-beach @8s (identical book-end), MW-forest @8s (identical book-end). Download (`poll-veo-ops.cjs` → `dl.cjs`). `python3 tools/clip-qa.py` each.
3. Build looping units: FG-morning → mci ×2 → self-xfade (~22.5s). MW-beach → mci ×2 → self-xfade (~30.5s, directional, no ping-pong). MW-forest → setpts ×2 → ping-pong ×2 (~32s).
4. FOREGROUND mini-hour (180s): `-stream_loop` the FG unit to 180s (single light state — no FG dissolve in the slice).
5. MIRROR mini-hour (180s): fill ~85s with the MW-beach unit, `xfade=fade:duration=40` into the MW-forest unit for the remaining ~95s — validates the slow world dissolve.
6. Build `mirror_mask.png` + `mirror_glass.png` once (geometry-fixed).
7. COMPOSITE: run the mirror filtergraph (FG mini = room layer, MW mini = world layer). Extract a frame mid-dissolve and eyeball: portal reads as a **mirror** (bevel + faint abstract glass-reflection of empty wall), not a TV; the beach→forest dissolve is smooth inside the glass while the room stays put.
8. AUDIO: a ~3-min P2 pad loop + W1 surf SFX (ducked, with one entry bell) muxed with the final encode params (`-shortest`).
9. WATCH the full 3 min end-to-end. **Acceptance checklist:** (a) no visible loop seam in either zone; (b) world dissolve reads dreamy, not a cut; (c) portal reads as a mirror; (d) **the pale-gold moth is visible and drifting** in both worlds (it must read at portal scale ≈538px — if it's invisible inside the small mirror, enlarge it in the nano stills); (e) gentle motion everywhere, nothing dead-static; (f) audio bed loops without a click; (g) no Veo face-morph on the woman.

Only on **PASS**, scale to the full hour — the per-zone build is identical, just more states/worlds and longer `stream_loop` fills. If the mirror fails believability, retune only the reflection opacity / glass sheen (cheap, no new Veo). **The one proof-specific risk to front-load: moth legibility at portal scale** — confirm it in step 9 before generating the other 9 world/state clips.

## Future direction — indefinite generation with memory

The v1 architecture is the runtime, not a throwaway: a per-zone **state machine** over a reusable **clip library**, two cleanly-decoupled ideas the live version just keeps feeding.

1. **Clip library = the memory store.** The ~12 looping units *are* the system's memory. v1 plays them in fixed order; the live version keeps a growing library keyed by `(zone, state/world, motif-tags)` and a small JSON state: `{ fg_light_state, mirror_world, active_motifs, last_world_for_each, moth_state, run_clock }`. The player is a tiny loop: hold current unit → when the hold timer fires, pick the next state via the transition policy → xfade into it. Nothing about the compositing or looping changes — you swap "concat a fixed list" for "the state machine emits the next unit at runtime."
2. **Two clocks = two memories.** Foreground (slow forward-only light arc) and mirror (faster world cycle) are separate state machines on one clock — "the room remembers the day while the portal remembers which worlds it has shown." Add a per-zone transition-policy table (Markov weights so worlds don't repeat back-to-back; daylight that only advances) → coherent-but-evolving for free.
3. **The moth IS the memory cursor.** Persist a tiny record that rides with the moth between worlds: `{ last_world, screen_position, entry_edge, wing_wear, hue_drift }`. Each newly-generated world must honor "the moth enters from the edge it exited the previous world, at its accumulated wear-level." Over long runtimes the moth visibly ages (wings dulling, hue drifting gold→grey); the mirror "remembers" worlds by occasionally re-showing a previously-visited world tinted by the moth's current wear — literal memory: home state = the woman's room, the moth = the cursor carrying continuity across procedural worlds, and "recurrence" = the engine re-selecting a stored world-seed when the moth's wear crosses a threshold. The audio **L4 return/echo bus** is the sonic twin: it re-surfaces an earlier world's ambience faintly under a later one when the policy recalls it.
4. **Indefinite = library growth + lazy generation.** Every unit is a frame-exact seamless loop, so the engine runs forever on the existing library *and* generates fresh units (new worlds, light nuances, motif variations) in the background under a cost budget, dropping them into the library when ready. The **fixed mirror geometry + fixed composite filtergraph** mean any new world plugs in with zero new compositing work. v1's "render the hour" is literally the live engine run once with a fixed policy and a frozen library — flip the policy to live, let the library grow, and it generates forever with memory.

## Open risks

1. **Moth legibility at portal scale.** The portal is ≈538×562 px inside a 2560×1440 frame; a thumbprint-sized moth could vanish. *Mitigation:* size the moth generously in the nano world-stills; confirm in the proof slice (acceptance check d) before generating the other 9 clips. Fallback: isolated-moth overlay at controllable scale/opacity (held in headroom).
2. **Veo baking the moth into each world clip.** Veo may drop or mis-place the moth, or render it as a smudge. *Mitigation:* the moth is seeded in each world's nano book-end still (present at least at loop endpoints); clip-qa checks for it; the isolated-overlay fallback removes the dependency.
3. **Foreground face-morph on the woman.** Even at 6s with distinct book-ends, Fast can drift the jaw/hair. *Mitigation:* three-quarter-back (face not load-bearing), tiny motions, loop closes on xfade not a frame-wrap. Trust the human watch over clip-qa's over-flagging on held faces; reroll budget covers it.
4. **City world tripping RAI / baking signage.** *Mitigation:* prompt explicitly forbids text/signs/shop-names, no neon, no people/cars; lamplit-dusk is already the safe register; reroll once then fall back to a faceless near-empty street.
5. **mci smearing on grain/water/snow.** *Mitigation:* mci applied once per short clip (never the hour); cap 3×; drop to setpts ×2 + ping-pong if a world smears.
6. **Mirror reads as a TV, not glass.** *Mitigation:* proven composite; only knob to retune on failure is reflection opacity / sheen — cheap, no new Veo.
7. **Audible loop over an hour.** *Mitigation:* per-tile micro-detune, non-commensurate LFO periods, desynced clock lengths push the true repeat past the hour; sparse irregular bells are the only events.
8. **File size / gallery playback device.** ~1.5–3.5 GB/hr H.264 must loop cleanly on the target HDMI stick / media player. *Mitigation:* `+faststart` + fixed 2s GOP for clean loop-restart; H.265 sibling for storage; test the loop wrap on target hardware before install.
9. **Color-spill halo over-tinting the room.** *Mitigation:* keep it a soft low-opacity radial keyed off the world's mean hue; let it *linger* faintly rather than dominate, except deliberately at night.
