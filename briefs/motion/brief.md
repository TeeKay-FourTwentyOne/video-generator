# Motion — production spine v1

The director selected the release title **Motion** after production. Stable project ID: `motion`. The source spine below preserves the original plan; the current publication draft is [description.md](description.md).

Imported source intent. Current implementation decisions and corrections are in [decisions.md](decisions.md); the original supplied file is preserved unchanged in the private workspace. Provider and harness names below describe the supplied plan, not work already performed.

Standalone conceptual piece · source dated 2026-10-30
Handoff target: Claude Code (NBP → Veo → ffmpeg). Written to survive without the director present.

---

## 1. Concept

Four clips from a motion-triggered trail camera, reposted the way such clips get reposted: a 4:3 infrared frame sitting on black, data strip along the bottom, hard cuts between files. 11:48 PM, a deer walks through and looks at the camera, its eyes blazing white in the infrared. 2:51 AM, a couple in 1950s evening wear waltzes slowly across the same trail, and their eyes blaze the same way each time a face comes around toward the lens. 3:14 AM, four couples. 3:40 AM, all eight of them are standing still in dance hold, every face turned to the camera, and the clip runs out on them.

Nothing is stated. No title, no end card, no music, no text except the camera's own strip. The deer teaches the viewer to read eye-shine as animal; the dancers then have it. The dancers make no sound on the leaves; everything else about the night (temperature, moon phase, the cricket, the camera's gain) is accurate. The camera does not react. It records, and then it stops.

Source: the last scene of *Carnival of Souls* (Herk Harvey, 1962). Pale, unsmiling couples in dated formal wear waltzing to music the protagonist cannot hear, who stop and turn to look at her all at once. This piece keeps the dancers, the silence, the stop-and-turn, and the flat documentary texture, and relocates all of it into the fixed camera of 2026. The turn itself happens off-camera, between the 3:14 file and the 3:40 file.

---

## 2. Format

- Canvas 1080×1920 (9:16), **30 fps**, H.264 (high, yuv420p) + AAC 48 kHz (dual-mono in a stereo container).
- Runtime 30.0 s (900 frames). Not built to loop; the seam is black/silence → black/silence, which is neutral, and a replay starting on the deer is acceptable.
- Footage window: 4:3, 1080×810, full canvas width, y 555–1365. Everything outside the window is #000000 for the entire runtime.
- Footage cadence inside the window: **15 fps effective** (each footage frame held for two master frames). The data strip updates at the same cadence.
- Footage is rendered at 960×720, degraded (§7), and upscaled to 1080×810. The degradation is the documentary ground; do not skip it.
- On-screen text: the data strip only.

---

## 3. Beat sheet

| # | Time (s) | Frames | Strip time | Temp | Content | Source |
|---|---|---|---|---|---|---|
| — | 0.0–0.3 | 0–8 | — | — | black, silence | — |
| C1 | 0.3–7.3 | 9–218 | 10/30/2026 11:48:07 PM → :14 | 41°F | deer enters right, pauses, looks at lens, exits left | V1 |
| — | 7.3–7.5 | 219–224 | — | — | black, silence | — |
| C2 | 7.5–14.5 | 225–434 | 10/31/2026 02:51:33 AM → :40 | 37°F | one couple waltzes left → right, exits | V2 |
| — | 14.5–14.7 | 435–440 | — | — | black, silence | — |
| C3 | 14.7–21.7 | 441–650 | 10/31/2026 03:14:02 AM → :09 | 36°F | four couples waltz left → right at four depths | V3 |
| — | 21.7–21.9 | 651–656 | — | — | black, silence | — |
| C4 | 21.9–29.5 | 657–884 | 10/31/2026 03:40:51 AM → :58 | 35°F | eight standing in hold, all faces to lens, nothing moves | V4 |
| — | 29.5–30.0 | 885–899 | — | — | black, silence | — |

Hard cuts everywhere, picture and sound. The 0.2 s black gaps are the uploader's cuts between files; they must be true black and digital silence.

Each clip begins at its own recording start: the subject is already entering at frame 0 (trigger latency), and the IR-cut filter clack (§6) sits on frame 0. Choose each Veo window so the first frame has the subject at the frame edge, not in the clear.

Moon glyph on every strip: waning gibbous, lit on the left, dark on the right (verified: ~74% illuminated on Oct 30, ~64% on Oct 31; Hunter's Moon was Oct 25/26).

Tolerances: C2 and C3 may each run to 8.0 s if a take needs it to clear the frame; shift everything after and recompute. C4 does not extend: 7.6 s is the beat. Keep the beat table as one structure in the script.

---

## 4. The camera — visual spec

### Page
- #000000 everywhere outside the window, every frame.

### Window
- 1080×810 at (0, 555). No border, no rounding, no shadow. The window is the whole 4:3 frame of the camera, strip included.

### The infrared look (target; §7 has the recipe)
- Monochrome, no green tint. High contrast. The leaf litter and the nearest trunk are overexposed by the illuminator; depth falls to black within about 12 m. Foliage reads bright (it does in IR). Pale fabric blooms white; dark fabric reads mid-grey, lighter than it would by day (dyes are often transparent in IR). Skin reads smooth, waxy, pale. These are physical facts about IR, not style choices, and they are why the dancers look the way they look without any makeup instruction.
- Eye-shine: hard white points, slightly bloomed, **only when the eyes are near the lens axis.** In C2 and C3 it appears once per rotation as each face comes around; in C4 it is constant. A face turned away has no eye-shine. This is physics and it gives the waltz its rhythm.
- Grain, softness, compression blocking in the dark areas, slight exposure pumping when something close enters (auto-exposure).

### The scene (identical in all four clips)
- A game trail crossing the frame left to right, 4–6 m from the camera, through bare and half-bare deciduous trees. Leaf litter. A fallen log on the right third. A large trunk very close at the left edge, blown out. Brush behind, then black. No sky to speak of. No man-made objects, no bait pile, no path markers.
- Camera strapped to a tree at about 1 m, angled slightly down. Fixed.

### Data strip
All coordinates at the 960×720 render scale; the strip is burned in **before** degradation so it suffers with the footage.
- Band: full width, y 668–720 (h 52), fill #141414, opaque.
- Font: DejaVu Sans Mono Bold 30 px, #e6e6e6. Fallback Roboto Mono Bold. Monospace so the ticking seconds don't jitter the layout.
- Left group, x 16: moon glyph (24 px disc, #e6e6e6, with the right ~26% occluded by a #141414 ellipse → waning gibbous), gap 12 px, then temperature `41°F` etc.
- Center group, centered on x 480: `10/30/2026  11:48:07 PM` (two spaces between date and time; 12-hour clock with AM/PM, leading zero on the hour for AM times: `02:51:33 AM`). Seconds tick live at the 15 fps cadence.
- Right group, right edge x 944: battery glyph, 26×12 outline with a 3 px nub, three of four bars filled. Expendable; the Shorts right rail will cover it on some phones and nothing is lost.
- No camera name, no brand, no logo, no GPS, no pressure. Four facts and two glyphs.

### Typography elsewhere
- None.

---

## 5. Footage plan

Four Veo generations plus retakes; six Nano Banana Pro plates. All Veo clips: 8 s, 16:9, highest resolution available, audio on (discarded at assembly), Veo 3-class model via Flow. Every clip is center-cropped from 16:9 to 4:3 at assembly, so the left and right eighths of every frame are discarded: **keep all action inside the central 75% of the generated frame.**

### Global prompt rules
- Clean physical description, no poetic language.
- Every Veo prompt opens with the look line and the scene line below, verbatim, and ends with the close line, verbatim.
- Never use: costume, zombie, ghost, dead, undead, spirit, creepy, eerie, haunted, horror, Halloween, scary, spooky, flash, glow, night vision, grid, timestamp (except in the prohibition). "Infrared" is the only technical word Veo needs. Eye-shine is always "reflect the infrared light as bright white points."
- The dancers are described by clothes and expression only. The woods and the camera do the rest.
- Veo will want to add a timestamp or a camera logo. The close line forbids it; if one appears anyway, regenerate (do not crop around it, the strip position is fixed).
- Veo will want a green tint. The look line forbids it; if it comes back green, desaturation in post fixes it, so a green take is not a reject on its own.

**Look line:**
> Black and white infrared night footage from a fixed trail camera strapped to a tree at waist height, angled slightly downward. Monochrome, no green tint. Grainy and high contrast; the leaf litter and the nearest tree trunk are brightly lit by the camera's infrared illuminator and the woods fall off to black behind.

**Scene line:**
> A game trail crosses the frame from left to right through bare and half-bare deciduous trees, with leaf litter on the ground, a fallen log on the right, and a large tree trunk very close at the left edge.

**Close line:**
> Camera is fixed, no camera movement. No music, no speech. No on-screen text, no timestamp, no captions, no watermark.

### NBP plates (all 16:9, action in the central 75%)

**P1 — scene plate** (first frame for V1; base for every other plate)
> Black and white infrared trail camera photograph at night. [scene line, rephrased as a still]. Nobody and no animals in frame. Grainy, high contrast, the foreground overexposed by the infrared illuminator, the background black. 16:9.

If NBP returns something atmospheric (fog, moonbeams, blue tint), regenerate. It should look like a frame nobody would keep.

**P2 — couple A reference** (full length, in the scene, IR)
> [P1 setting]. A man in a dark 1950s suit with a white shirt and bow tie and a woman in a long pale satin evening gown with long gloves and her hair pinned up stand in closed ballroom dance hold in the middle of the trail, both in profile to the camera. Pale, unsmiling faces, eyes open, mouths closed. 16:9.

Lock A before anything else. Take rule: the first ordinary pair is the pair. Not glamorous, not made-up, not styled toward anything. If NBP returns prosthetics or horror makeup, regenerate once with "plain, ordinary faces" added, then lock.

**P3 — couples B, C, D reference** (same framing as P2)
- B: man in a tuxedo; woman in a long dark gown (reads grey in IR), short dark hair.
- C: an older couple, grey-haired man in a dark suit, woman in a pale gown with a fur stole.
- D: a tall couple, man in a dark double-breasted suit, woman in a pale gown with bare shoulders.
Lock all three. Every later first frame derives from P2 and P3.

**F2 — V2 first frame.** Couple A in hold at the left edge of the central 75%, mid-turn, the woman's back toward camera.

**F3 — V3 first frame.** Couple A mid-frame in hold; couple B entering at the left edge; couple C far back, small and dim; couple D not yet in frame.

**F4 — V4 first frame.** All eight standing on the trail in pairs, in hold, at four depths (nearest about 3 m, farthest about 9 m), every head turned to camera, every face to the lens, all sixteen eyes as bright white points. This plate is the shot; V4 only has to keep it alive.

### Veo clips

**V1 — deer** (first frame P1) → C1
> [look line] [scene line] An adult white-tailed deer walks into frame from the right edge, pauses in the middle of the frame, lifts its head and looks directly at the camera for a moment, its eyes reflecting the infrared light as two bright white points, then walks on and exits at the left edge. Audio: hooves on dry leaves, a soft exhale, light wind in bare branches. [close line]

Must be a deer, adult, either sex. The look at the camera is required; the eye-shine on the deer is required. Window: 7.0 s starting with the deer already breaking the right edge.

**V2 — one couple** (first frame F2) → C2
> [look line] [scene line] A man in a dark 1950s suit with a white shirt and bow tie and a woman in a long pale satin evening gown with long gloves and her hair pinned up dance a slow waltz in closed ballroom hold. They turn slowly as a couple and travel along the trail from the left edge of the frame to the right edge, and exit at the right edge. Their faces are pale and unsmiling, eyes open, mouths closed. They look at each other or past each other and never at the camera. Each time a face turns toward the camera, the eyes reflect the infrared light as bright white points. Audio: light wind in bare branches. [close line]

Reject if: they dance in place and don't cross; either looks at the lens; mouths move as if talking; anything reads as makeup. Window 7.0 s, entry at frame 0, exit before the end.

**V3 — four couples** (first frame F3) → C3
> [look line] [scene line] Four couples in 1950s evening wear dance a slow waltz in closed ballroom hold and travel along the trail from left to right at different distances from the camera: one couple far back and dim, two in the middle distance, and one very close to the camera, so close that their heads are cut off by the top of the frame and their clothes are overexposed by the infrared illuminator. Men in dark suits or tuxedos; women in long gowns, some pale, some dark. Pale, unsmiling faces, eyes open, mouths closed. Nobody looks at the camera. Eyes reflect the infrared light as bright white points when a face turns toward the camera. Audio: light wind in bare branches. [close line]

Count must be four couples, visibly the same four as F4 will show. The close couple is the auto-exposure cue (§7). Window 7.0 s; the last couple may still be exiting at the cut.

**V4 — standing** (first frame F4) → C4
> [look line] [scene line] Eight people in 1950s evening wear, four men in dark suits or tuxedos and four women in long gowns, stand completely still on the trail in pairs, each pair in closed ballroom hold as if a dance has been paused, at different distances from the camera. Every head is turned toward the camera and every face looks directly into the lens, pale and unsmiling, eyes open, mouths closed. All sixteen eyes reflect the infrared light as bright white points. Nobody moves. At most, a slow blink. Audio: light wind in bare branches. [close line]

Reject if anyone walks toward the camera, reaches, smiles, or speaks. Micro-motion is wanted (breath-scale sway, a blink that kills a pair of eye-points for a frame); walking is not. Window 7.6 s. If Veo cannot hold still, fall back to F4 as a plate with programmatic micro-motion (sub-pixel drift, grain, two or three composited blinks) — this clip is the one that can be faked from a still without loss.

**Eye-shine fallback (V2–V4).** If Veo does not render eye-shine on the dancers, or renders it on faces turned away from the lens, add it in Claude Code: per-frame face landmarks (mediapipe face mesh or equivalent) → eye centers → gaussian white points, radius 4–7 px at 960×720 scaled by face size, additive, clipped, with ±15% frame-to-frame flicker, gated to faces whose yaw is within ~30° of the lens. Decide on V2's first take and apply the same method to all three.

**Face take rule.** The first acceptable take is the take. Acceptable: ordinary people, pale in the way IR makes everyone pale, no visible makeup or prosthetics, eyes open, mouths closed, no text. Do not regenerate toward more frightening or toward more photoreal. The IR does the editorializing; the author does not.

---

## 6. Audio design

All audio is built in Claude Code. Veo audio is discarded entirely.

- **Channel and bandwidth.** Mono, band-limited 150 Hz–7 kHz, mild codec-style smear. It is a trail camera microphone.
- **AGC.** Emulate automatic gain control: a slow leveler (attack ~0.4 s, release ~1.5 s) that raises gain toward a ceiling when the input is quiet. The effect: the noise floor swells when nothing happens. In C1 the deer's hooves keep the gain in check; in C2–C4 there is nothing to check it, so each clip's hiss rises over its first two seconds and sits there. By C4 the floor is at its ceiling from about 2 s in. This is the machine's version of the stop-and-turn: it turns its ears all the way up and hears nothing.
- **Bed.** Night wind in bare branches, low, intermittent, with occasional single leaf ticks. Different wind per clip (they are 25–50 minutes apart) but the same character.
- **Cricket.** One, in C1 only. At 41°F a tree cricket chirps about four times a minute (Dolbear's law, T°F ≈ 50 + (chirps/min − 40)/4), so one slow chirp in the seven seconds, no more. At 37°F and below (C2–C4) there is none. This is correct and almost nobody will notice; it is there for the one person who does.
- **Camera self-noise.** On frame 0 of every clip: the IR-cut filter clack, a two-part mechanical click (~40 ms total, −14 dBFS peak), followed by a short recording-start pop. Throughout each clip: the illuminator whine, a faint tone near 11 kHz at about −48 dBFS, rising with the AGC. Inaudible on most phone speakers; present on earbuds.
- **C1 foley.** Hooves in leaf litter, five or six steps on entry and exit, one soft exhale at the look. Peaks −18 dBFS.
- **C2–C4.** No footsteps. No fabric. No breath. Bed, whine, AGC. This is the tell, and it is the only one.
- **Gaps and ends.** The 0.2 s blacks, the 0.3 s head and the 0.5 s tail are digital zero. C4 ends on a hard cut from full-gain hiss to zero.
- **No music.** Suno is not used. ElevenLabs is not used.
- **Master.** Bed around −32 LUFS short-term in C1 rising with the AGC to about −26 LUFS by C4. Cap at −1 dBTP. No program-wide loudness normalization.

---

## 7. Assembly (Claude Code)

1. **Plates (NBP).** P1 → P2 → P3, lock each before deriving F2, F3, F4.
2. **Veo.** V1–V4 per §5. Select windows per the beat sheet (subject at the edge on frame 0).
3. **Footage prep, per clip (ffmpeg / Pillow / numpy):**
   a. Trim to window. Center-crop 16:9 → 4:3. Scale to 960×720.
   b. Desaturate fully.
   c. Curve: black floor around 8/255, mids crushed, highlights clipped from ~235. Illuminator falloff: multiply by a soft mask brightest at center-low, darker toward the top corners. Light touch if Veo already did it.
   d. Auto-exposure pumping: in C3, a gain dip of ~1.5 stops over 0.4 s as the close couple enters the frame, recovering over ~1.2 s after they exit. In C1 a smaller dip if the deer comes close. None in C2 or C4.
   e. Eye-shine composite if needed (§5).
   f. Decimate to 15 fps (drop every other frame, no blending).
   g. Grain: monochrome, per-frame uncorrelated, sigma 6–8 at 960×720, plus a faint fixed-pattern component. Gaussian blur 0.6 px before the grain.
   h. Burn the data strip (§4) frame by frame with the correct ticking time.
   i. Degrade: encode libx264 at 960×720, ~1000 kbps with maxrate 1000k / bufsize 500k, GOP 30 (2 s at 15 fps), no B-frames, preset fast; decode. The macroblocking in the dark areas and the GOP pulse are wanted.
   j. Upscale to 1080×810 bilinear (not lanczos). Pad onto 1080×1920 black at (0, 555). Conform to 30 fps by frame doubling.
4. **Audio** per §6, one WAV per clip at the clip's exact length; silence for gaps, head and tail.
5. **Concat** per the beat table. Encode H.264 high / CRF 16 / yuv420p / 30 fps, AAC 48 kHz 192 kbps.
6. Keep the beat table, the strip times, and the temperatures in one structure in the script so a C2/C3 extension propagates to timestamps and runtime.

---

## 8. QA — on a real phone

- Window pixels outside the frame are 0,0,0. Gap frames are 0,0,0.
- Cadence: footage frames hold exactly twice; no single-frame slips at clip starts.
- Strip: legible at phone size; date rolls from 10/30 to 10/31 between C1 and C2; seconds tick; moon glyph is lit left, dark right, the same on all four; temperatures descend 41, 37, 36, 35.
- No text in the footage other than the strip. Frame-step every clip.
- C1: the deer looks at the lens; two eye-points.
- C2: one couple; they cross and exit; never look at the lens; eye-shine only when a face is toward camera.
- C3: four couples; the close couple is overexposed and cropped at the head; auto-exposure dips and recovers.
- C4: count eight people, sixteen eye-points; nobody walks; micro-motion present; the clip ends on a hard cut.
- Clothes match across C2, C3, C4 (couple A in all three; B, C, D in C3 and C4).
- Audio: clack on frame 0 of all four clips; one cricket in C1 and none after; hooves in C1 and no footsteps anywhere else; the noise floor rises in C2–C4; C4 ends in a hard cut to zero.
- Watch once on an OLED in a dark room with earbuds and once on a lit bus with the speaker. The piece has to read in both; the earbud version is the one with the whine and the cricket.

---

## 9. Publication

**Title:** Motion

**Published:** [YouTube Shorts](https://youtube.com/shorts/xw4HQtnVbqc), confirmed by the director and recorded 2026-10-30. The local release master is `4k-v1`; its hash is not a claim about YouTube’s transcode.

The approved description and actual production credits are preserved in [description.md](description.md). The supplied source’s earlier publishing draft remains in the private original. The rest of this spine records the original creative plan; final timing and sound decisions are in [decisions.md](decisions.md).

---

## 10. Decisions and reasoning

- **A window on black, not full-bleed vertical.** Trail cameras do not shoot 9:16. A vertical crop would be a lie about the source, and a reposted 4:3 clip on black is how this footage actually appears in a feed. The black also keeps the phone's OLED off around the frame, the same move as VERIFY.
- **4:3, 15 fps, 960×720, hard compression.** Cheap sensor, cheap codec. The degradation is what VERIFY's street-mapping texture was: the documentary ground. If the footage looks like generated video, the camera stops being a camera and the piece becomes an effect.
- **The deer.** It is the primer. It teaches eye-shine as an animal fact and teaches that things on this trail look at the camera (the illuminator's faint red draws a glance). Without it, the dancers' eyes are an effect; with it, they are a fact about the dancers.
- **Eye-shine only on-axis.** Real, and it hands the waltz its meter: a flash of white every time a face comes around. In C4 it never goes out.
- **No footsteps.** The single falsehood in the sound. Everything else, the cold cricket, the temperatures, the moon, the AGC, is true, so that the one wrong thing is unmistakable.
- **The turn happens between files.** At 3:14 they are dancing; at 3:40 they are already turned. The camera did not see them stop. The most famous beat in the source is withheld and replaced by a gap in the record, which is the restraint rule applied literally.
- **Clip length.** Some trail cameras stop recording when motion stops. C4 is the shortest beat because nothing in it moves. Unstated.
- **The dates.** The night of October 30 into October 31. Posted on Halloween, the strip reads as this morning.
- **Same eight.** The four couples in C3 are the eight in C4. If the count or the clothes drift, it becomes a crowd scene instead of a record.
- **IR does the makeup.** Infrared makes everyone pale and every pale fabric bloom. No prosthetics, no makeup instruction, no "horror" in any prompt. The dancers are ordinary people photographed by a camera that makes everyone look like this.
- **No stop-and-turn in motion, no chase, no footprints, no car.** The camera cannot follow and does not care.
- **No music.** The source's dancers moved to music the protagonist could not hear. This camera cannot hear it either.
- **Prior art.** Creepy trail-cam imagery is an established genre: the annual spooky-trail-cam roundups, the 2022 British Columbia "witches" photo, the Hawaiian "night marchers" procession claims, and the fake-cryptid clip industry. Found-footage IR horror exists at feature length (*Infrared*, 2022). All of it trades on a creature, a jump, or lore. The divergence here: nothing is wrong except the people, they are formally dressed and dancing, every datum is correct, and the camera is the only witness. Credit the film in the description; do not pretend trail-cam horror is new ground.

---

## 11. Open items (resolve on what Veo returns)

1. Eye-shine on the dancers: Veo-native vs. the landmark composite, decided on V2's first take and applied uniformly.
2. V4: Veo hold vs. F4-plate-with-micro-motion fallback.
3. C2/C3 length: 7.0 s if the couples clear the frame, up to 8.0 s if not; recompute timestamps and runtime.
4. Cricket sample: a tree-cricket chirp slowed and pitched for cold; one chirp, placed by ear in C1.
5. Strip font availability in the container (DejaVu Sans Mono Bold → Roboto Mono Bold).
6. Whether the 4:3 crop of each Veo take keeps all action inside the frame; reframe prompts toward center if a take loses a couple off the edge.

Everything else is decided.
