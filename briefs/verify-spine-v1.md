# VERIFY — production spine v1

Standalone conceptual piece · original spine dated 2026-10-06.
The original treatment below proposed NBP → Veo → FFmpeg; production used Runway instead.

## Published revision — v4

The user-approved production direction uses Runway Gen-4.5 footage, with locally
rendered interface graphics and synthesized sound. V4 applies the requested
pacing trims, omits bicycles, and runs 22.75 seconds at 24 fps. The center tile,
then the upper-left and upper-right tiles, select silently during the black-grid
beat, after the helper changes to “Please remain a person.” Verifying is the last
beat. These revisions supersede the original beat durations, empty bus tail and
no-selection direction below.

The native review is 1080×1920; the explicitly authorized 4K finish is 2160×3840,
with the interface rendered at that resolution and original footage scaled
locally. The final user-edited publication text, including the concept credit and
related links, is preserved in [verify_description.md](verify_description.md).

Publication: [VERIFY on YouTube Shorts](https://youtube.com/shorts/lb9vcB07CRg).
Recorded 2026-10-12 from the user's supplied publication URL; user-confirmed,
not independently verified through the public page. This recording date is not
an assertion of the platform's publication date.

The released local master is `final/v4-4k/film.mp4`: 2160×3840, 24 fps,
546 frames / 22.75 seconds. SHA-256:
`a9efb8f799372976d070df3bda390874477de2915356a86c57678354b90da75a`.
Runway production spend, including auditions, was $6.72; Veo spend was $0.
Editing, sound and 4K finishing added no generation cost.

Verified local archive: `data/workspace-archive/verify-film-v1/` (2026-10-12).
The intact archive preserves sources, alternates, native exports, all revisions,
recipes, ledgers and QA: 2,062 inventoried files, plus the archive manifest.
Content hashes, sizes and permissions were verified after moving. Its local
publication record links the final description and release evidence. The
[post-publication workflow](../docs/post-publication.md) records the reusable
close-out procedure; the [production-record handoff](../docs/production-records-proposal.md)
describes the proposed documentation organization. The original treatment below is retained as history;
its proposed tools, durations and actions are superseded by this production record.

---

## 1. Concept

The entire piece is an image-selection verification challenge. A card sits on a black page: blue header, 3×3 grid, footer with a SKIP button. The only departure from the real thing is that the tiles are live footage instead of a still, and nobody ever clicks. Four road-category challenges make the test impossible on its own terms (the answer moves out of the square while you're deciding). Then the category changes to *a person* — first a crowd, then one synthetic face holding eye contact, then a black grid in which the viewer sees their own reflection in the phone. The card then verifies on its own, without any input, and the spinner never resolves: the video loops back to the first challenge.

Nothing is stated. No title card, no end card, no music. The viewer performs the argument on themselves.

---

## 2. Format

- Canvas 1080×1920 (9:16), 24 fps, H.264 (high, yuv420p) + AAC 48 kHz stereo.
- Runtime 39.0 s (936 frames). Built for platform auto-loop; the seam is designed, not incidental.
- No on-screen text other than the widget's own UI text. Credits live in the description.
- The page background is **#000000 for the entire runtime.** This is load-bearing (see §10).

---

## 3. Beat sheet

| # | Time (s) | Frames | Header line 2 | Grid | Source window | Audio |
|---|---|---|---|---|---|---|
| B1 | 0.0–4.5 | 0–107 | traffic lights | intersection; the light cycles | V1 0.0–4.5 | tick + V1 ambience |
| B2 | 4.5–9.0 | 108–215 | crosswalks | same intersection; pedestrians cover the stripes | V1 3.5–8.0 | tick + V1 ambience |
| B3 | 9.0–13.5 | 216–323 | bicycles | same intersection; one rider crosses four tiles | V2 (window chosen so rider enters ~0.5 s in, exits before end) | tick + V2 ambience |
| B4 | 13.5–18.0 | 324–431 | buses | same intersection; bus enters, fills ~5 tiles, exits; grid ends empty | V3 (window chosen so bus is gone by the last frame) | tick + V3 ambience |
| B5 | 18.0–23.0 | 432–551 | a person | sidewalk crowd, nobody looking at lens | V4 0.0–5.0 | tick + V4 ambience |
| B6 | 23.0–29.0 | 552–695 | a person | one face, close, eye contact, mouth closed | V5 1.0–7.0 | tick + V5 ambience (−6 dB) |
| B7 | 29.0–36.0 | 696–863 | a person | pure black tiles, faint gutters | none | tick, then digital silence |
| B8 | 36.0–39.0 | 864–935 | Verifying… | black tiles, spinner | none | digital silence |

Hard cuts between all beats, picture and sound, on the tick.

B4 tolerance: if the generated bus takes longer than 4.5 s to clear the frame, extend B4 to a maximum of 5.5 s and shift everything after it. The grid **must** be empty on B4's last frame; that is the beat.

B1→B2 reuses the same clip with a 1.0 s overlap (jumps back in time). This reads as "new image, same scene," which is what the real widget sometimes does. Acceptable.

---

## 4. The card — visual spec

All coordinates are canvas pixels (1080×1920), origin top-left. Build with Pillow (chrome) + ffmpeg (footage compositing). Claude Code may fine-tune text baselines by ±6 px for optical balance; everything else is fixed.

### Page
- Full canvas fill #000000, every frame.

### Card
- x 70–1010 (w 940), y 330–1590 (h 1260). Centered vertically (330 top, 330 bottom). Square corners. No drop shadow (invisible on black anyway).

### Header — y 330–550 (h 220), fill #1a73e8
- Line 1: `Select all squares containing` — Roboto Regular 36 px, #ffffff, left x 110, text top y 362.
- Line 2: category — Roboto Bold 72 px, #ffffff, left x 110, text top y 408. Lowercase, exactly as in the beat sheet.
- Line 3: `If there are none, click skip` — Roboto Regular 30 px, #ffffff, left x 110, text top y 500.
- B8 state: lines 1–3 removed; single line `Verifying…` (real ellipsis character) — Roboto Regular 48 px, #ffffff, left x 110, vertically centered in the header.

### Grid — y 550–1490 (940×940)
- Tiles 310×310, gutters 5 px.
  - Column x: 70, 385, 700. Row y: 550, 865, 1180.
  - Gutter strips: x 380–385 and 695–700 (full grid height); y 860–865 and 1175–1180 (full grid width).
- B1–B6: footage fills the full 940×940 area; gutters are drawn **over** it in #ffffff (occluding strips, no content shift).
- B7–B8: tiles #000000; gutters #0d0d0d. Faint, present, not decorative. The tiles must be true black — on an OLED those pixels turn off and the reflection is strongest.

### Footer — y 1490–1590 (h 100), fill #ffffff
- Left: three 40 px line-icon glyphs in #5f6368, drawn as simple vectors (circular arrow / headphones / circled i), centers at x 120, 180, 240, vertical center y 1540. Generic shapes; no brand glyphs.
- Right: button 190×64 at x 790–980, y 1508–1572, fill #1a73e8, label `SKIP` — Roboto Bold 30 px, #ffffff, +1 px letter-spacing, centered. **The button reads SKIP for the entire runtime** (see §10).
- B8 state: button fill #cfcfcf, label #ffffff (disabled look).
- No micro-text, no logos, no "Privacy · Terms". The card reads already; clutter at this scale is noise.

### Spinner (B8 only)
- Ring Ø 120 px, stroke 6 px, centered at (540, 1020) — the grid's center.
- Track: full circle #1f1f1f. Arc: #1a73e8, 270° sweep, rotating clockwise at 1 rev/s (24 frames per revolution; 72 frames = exactly 3 revolutions). Round caps.
- No easing, no fade-in. It is just there.

### Typography
- Roboto Regular / Bold (Apache 2.0). If unavailable in the container, Inter; if that fails, DejaVu Sans. Do not substitute a display face.

---

## 5. Footage plan

Five Veo generations, two Nano Banana Pro plates. All Veo clips: 8 s, 16:9, highest resolution available, audio ON, Veo 3-class model via Flow. Every clip gets center-cropped to square at assembly; frame the prompts knowing the left and right thirds are discarded.

Global prompt rules for this piece:
- Clean physical description, no poetic language.
- Every prompt ends with: `No on-screen text, no captions, no watermark.` (Veo likes to add subtitles.)
- Every prompt includes an audio line and `No music, no speech.`
- These are fixed shots, so "camera is fixed on a tripod, no camera movement" is correct here (the usual prohibition on that phrase is for shots that aren't locked).
- Do not put the words "verification," "test," "grid," "squares," or any UI language in a prompt. The widget is composited later; Veo should never know it exists.

### NBP plates

**P1 — intersection plate** (first frame for V1, V2, V3)
> Photograph, eye level, slightly wide angle, of a mid-sized city street intersection on an overcast day. A traffic light on a pole in the middle distance shows green. A white-striped zebra crosswalk runs left to right across the foreground. Parked cars line the far side of the street. Low commercial buildings behind. Nobody in frame, no moving vehicles. Flat, even daylight, muted colors, slightly soft, like a street-mapping camera capture. 16:9.

The look matters: flat, soft, slightly washed. The real challenge images come from street-mapping cameras, and matching that texture is what makes the first four beats read as documentary rather than "footage." If NBP returns something cinematic (golden hour, bokeh, contrast), regenerate.

**P2 — portrait plate** (first frame for V5)
> Photograph, eye level, head-and-shoulders close-up of an ordinary person in their forties standing on a city sidewalk on an overcast day, looking directly into the lens, neutral expression, mouth closed, no makeup, slightly tired, plain clothing, soft out-of-focus street behind them. Flat, even daylight, muted colors. 16:9.

Gender unspecified on purpose. Take the first plain, ordinary result. If NBP returns a stock-model face (glamorous, symmetrical, lit), regenerate once with "plainer, more ordinary" added. Then lock it.

### Veo clips

**V1 — lights and pedestrians** (first frame: P1) → B1, B2
> Eye-level view of a city street intersection on an overcast day. A traffic light on a pole in the middle distance shows green, then changes to yellow, then to red. After the light turns red, four pedestrians walk across the white-striped crosswalk from left to right, their feet covering the stripes as they pass. Parked cars on the far side of the street. Flat, even daylight, muted colors, slightly soft focus like a street-mapping camera. Camera is fixed on a tripod at eye level, no camera movement. Audio: distant traffic hum, footsteps on asphalt. No music, no speech. No on-screen text, no captions, no watermark.

If the light does not change, V1 is still usable; the color cycle is a bonus, not the beat. B1 is deliberately the almost-doable baseline. If pedestrians never reach the stripes, regenerate.

**V2 — bicycle** (first frame: P1) → B3
> Eye-level view of a city street intersection on an overcast day. A person on a bicycle rides through the intersection from the right edge of the frame to the left edge, passing in front of the camera at a steady pace, and exits the frame. Light traffic far in the background. Flat, even daylight, muted colors, slightly soft focus like a street-mapping camera. Camera is fixed on a tripod at eye level, no camera movement. Audio: bicycle tires on asphalt, distant traffic hum. No music, no speech. No on-screen text, no captions, no watermark.

Selection window: rider enters the square crop about 0.5 s into the window and exits before it ends. The point is the rider crossing tile boundaries, so a diagonal or mid-height path through the crop is better than hugging an edge.

**V3 — bus** (first frame: P1) → B4
> Eye-level view of a city street intersection on an overcast day. A large city bus enters from the left edge of the frame, drives slowly through the intersection filling most of the frame, and exits at the right edge, leaving the intersection empty. Flat, even daylight, muted colors, slightly soft focus like a street-mapping camera. Camera is fixed on a tripod at eye level, no camera movement. Audio: diesel engine approaching and passing, distant traffic. No music, no speech. No on-screen text, no captions, no watermark.

Exploit the literalness: "leaving the intersection empty" is the instruction that matters. Selection window must end on an empty grid.

**V4 — crowd** (no anchor) → B5
> Eye-level view of a busy city sidewalk on an overcast day. Twenty or more pedestrians of different ages walk toward and past the camera, some looking at phones, some talking to each other, none of them looking at the camera. Shop fronts behind them. Flat, even daylight, muted colors, slightly soft focus like a street-mapping camera. Camera is fixed on a tripod at eye level, no camera movement. Audio: crowd murmur, footsteps, distant traffic. No music, no distinct speech. No on-screen text, no captions, no watermark.

Hard requirement: nobody looks at the lens. B6 is the first eye contact in the piece. Check every frame of the selected window; if anyone glances at camera, choose a different window or regenerate.

**V5 — face** (first frame: P2) → B6
> Close-up of an ordinary person in their forties, head and shoulders, standing on a city sidewalk on an overcast day, looking directly into the camera lens with a neutral expression. They blink once, breathe, and shift their weight very slightly. Their mouth stays closed the whole time. Background is a soft, out-of-focus street. Flat, even daylight, no makeup, muted colors. Camera is fixed on a tripod at eye level, no camera movement. Audio: quiet street ambience, a faint breath. No music, no speech. No on-screen text, no captions, no watermark.

Selection window 1.0–7.0 (skip Veo's usual first-second settle). Veo wants people to talk; if the mouth moves as if speaking, regenerate.

**Take rule for V5:** the first *acceptable* take is the take. Acceptable means: ordinary person, eye contact held, mouth closed, no text. Do not regenerate to make the face more convincing, and do not regenerate to make it less convincing. Both directions editorialize. Whatever degree of uncanniness Veo produces on the first clean take is the honest answer to the question the header is asking.

---

## 6. Audio design

- **Ambience, B1–B6:** each clip's own Veo audio, trimmed to exactly the picture window. Normalize each clip's ambience to −23 LUFS integrated. B6 (face) sits 6 dB under that — it's a close-up, the street is behind them. Hard cuts at beat boundaries; the tick masks them. No crossfades anywhere.
- **Tick:** one dry UI click at frame 0 of B1 through B7 (seven ticks). None at B8. Synthesize in Claude Code: ~15 ms white-noise burst, band-passed 2.5–6 kHz, exponential decay, peak −14 dBFS, centered mono, no reverb, no tail. It should sound like a widget, not a sound effect.
- **B7:** after the tick decays (~30 ms), digital zero to the end of B8. About 10 s of true silence. Do not fill it with room tone. The silence is the loudest cut in the piece.
- **No music.** Suno is not used. ElevenLabs is not used.
- **Master:** do not run a loudness normalizer over the whole program — the 10 s of silence would make it misbehave and there is no dialogue to protect. Set levels per the above and cap at −1 dBTP.

---

## 7. Assembly (Claude Code)

Suggested stages; the exact script is Claude Code's call.

1. **Chrome plates (Pillow).** Render one 1080×1920 RGBA PNG per card state: B1–B6 (six, differing only in header line 2), B7, and the B8 base (header "Verifying…", disabled button, black grid). Grid area transparent for B1–B6 so footage shows through; gutters opaque white on top. For B7/B8 the grid area is opaque black with #0d0d0d gutters.
2. **Spinner frames (Pillow).** 24 RGBA PNGs of the ring at 15° steps, or draw the arc directly per frame. Composite onto the B8 base.
3. **Footage prep (ffmpeg).** For each of V1–V5: trim to window → center crop to square → scale 940×940 → pad onto 1080×1920 black at (70,550). Audio: trim to the same window, loudnorm to target, B6 −6 dB.
4. **Composite.** Overlay the chrome PNG on the padded footage for each beat (chrome on top; its transparent grid window reveals the footage; its white gutters occlude). B7 and B8 are chrome-only on black.
5. **Ticks.** Place the synthesized click at the first sample of B1–B7.
6. **Concat** all beats, picture and sound, with no transitions. Encode H.264 high / CRF 16 / yuv420p / 24 fps, AAC 48 kHz 192 kbps.
7. **Loop test:** concat the master to itself three times and watch the seam at 39.0 and 78.0 s on a phone. The seam should land as: silence → tick + street ambience, spinner → traffic-light grid, with nothing softening it.

Keep the beat durations as a single table in the script so the B4 tolerance shift propagates cleanly.

---

## 8. QA — on a real phone, not a monitor

- Watch on an OLED phone in a dim room and in a lit room. In the dim room the viewer's face must be visible in B7. In the lit room it will be fainter; that's acceptable, but it must not be *absent* on an OLED in ordinary indoor light.
- Confirm the header and the SKIP button sit clear of the Shorts/Reels UI. The card width (940, right edge at x 1010) was chosen so the right-rail icons overlap at most the outer ~40 px of the right tile column. That overlap is accepted — the platform's own buttons sitting over the grid is not a problem for this piece.
- B5: frame-step the window; nobody looks at the lens.
- B6: mouth closed throughout; eye contact never breaks.
- B4: last frame of the beat is an empty intersection.
- B7: measure the tile pixels. They must be 0,0,0, not 8,8,8.
- Every chrome plate: identical pixel geometry across beats. Only header line 2 changes until B8. Any 1 px drift between beats will read as a glitch on the hard cut.

---

## 9. Publishing

**Title:** VERIFY

**Description:** use [verify_description.md](verify_description.md), which records
the delivered film's actual tools, duration, fictional interface and verified
prior-art acknowledgments. The original draft description has been superseded.

Hashtags and the Reels cross-post are the director's call. No thumbnail work: Shorts picks a frame, and any frame of the card works.

---

## 10. Decisions and reasoning

- **Black page, whole runtime.** The viewer's reflection is in the margins from frame one; the piece just stops showing footage in B7 and the reflection is suddenly inside the grid. Nothing new is introduced at the hinge — something is withdrawn. That is the restraint rule applied literally.
- **The button reads SKIP throughout.** With nothing selected, the real widget's button offers only SKIP. Since nobody ever selects anything, that's accurate. It also means the one action the card ever offers is to skip — and then it verifies anyway. The word "verify" appears only in the title and in the B8 spinner text.
- **Auto-verify without a click.** No cursor, no tap, no selection highlight. The viewer is never represented inside the video. The test is administered, timed out, and verified by the machine alone.
- **Loop instead of result.** A checkmark or an X would both be a statement. The spinner at the seam means the question is asked again, of the same viewer, forever.
- **One intersection for three challenges.** Continuity from a single NBP plate makes B1–B4 feel like one test session reusing one image, and it costs three generations instead of four.
- **B1 is almost solvable on purpose.** The impossibility escalates: a traffic light is a traffic light whatever color it shows (B1), stripes get covered (B2), a bicycle crosses tile boundaries (B3), a bus fills the grid and leaves it empty (B4). The viewer is trained to hesitate before the category changes.
- **"a person," singular, lowercase.** Singular because one viewer is being asked. Lowercase because that's how the real header is set, and matching it is what keeps B5–B7 from reading as a reveal.
- **Face take rule.** The honest degree of synthetic-ness is whatever Veo produces on the first clean take. Polishing toward photoreal or leaning into uncanny would both be the author answering the question the viewer is supposed to answer.
- **Tick persists into B7.** The UI is still working; it's the image that's gone. Then silence.
- **No title, no credits on screen, no music.** All three would be the author's voice. The only voice in the piece is the widget's.
- **Street-mapping texture.** The real challenge images come from street-level mapping cameras. Flat overcast light, soft focus, muted color — if B1–B4 look like generated footage rather than scraped frames, the documentary ground is lost and the piece becomes an effect.
- **Prior art.** Acknowledge Tim Parchikov's *I'm not a robot* and Salzburger Kunstverein's 2026 programme *CAPTCHA Realism*, linked in the description. In this piece the tiles move, the people are synthetic, and the last grid is the viewer, via the device itself. Credit the lineage without claiming to exhaust the field.

---

## 11. Open items (resolve on what Veo returns)

1. B4 duration — 4.5 s if the bus clears in time, up to 5.5 s if it doesn't. Shift subsequent beats; update the total runtime and the loop test accordingly.
2. V1 — whether the pedestrians reach the stripes inside the 3.5–8.0 window. If they're late, slide the B2 window; if they never arrive, regenerate V1.
3. V2 — rider path through the square crop. Prefer a take where the rider crosses at least four tiles.
4. Font availability in the container (Roboto → Inter → DejaVu Sans, in that order).

Everything else is decided.
