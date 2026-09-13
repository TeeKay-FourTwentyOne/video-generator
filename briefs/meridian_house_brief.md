# Meridian House: The Living Library — production brief

Date: 2026-09-12. Status: **finished 4K deliverable; user approved the 1080p edit
and requested the 4K export.** Publication URL: not yet supplied. Nothing was
published by the production agent.

## Concept and constraints

A continuous-feeling midnight tour of an imagined fantastical mansion: leave
the celestial orrery in the atrium, pass through the library arch, approach the
reading desk, turn around, and return to the same camera mark. The long-term
experiment is spatially grounded generative video, with a real 3D set as the
source of camera geometry and repeatable views.

The first scene has no people. The requested inventory is limited to the modeled
architecture and objects; generated footage occasionally violates that constraint,
as documented below. Keep experiments in this repository, support 16:9 and 9:16,
and use local timelapse before spending on video generation. No account signup or
new provider uploads without discussion and authorization.

The selected final is **16:9, 3840 × 2160, 24 fps, 24 seconds, 576 frames**, with
48 kHz stereo AAC. The 4K file is 80,504,641 bytes. It is an AI-upscaled 1080p
production, not native 4K scene/video generation.

## The persistent set

Source: [`tools/scene-lab/`](../tools/scene-lab/README.md). A procedural WebGL 2
miniature mansion with jade/ivory architecture, warm brass, dusty rose furnishings,
a cobalt library and a moonlit conservatory. Three connected rooms share one
coordinate system. The source contains 810 named objects and 55,116 triangles;
geometry checksum `27e11313`.

The local renderer exports OBJ/MTL, camera metadata, beauty, clay, radial-depth,
world-normal and object-ID guidance. Projection is camera-calibrated sampling
with visibility tests, not a baked UV texture atlas. The scene is static; camera
time does not yet advance props or characters.

## Production sequence

1. **Geometry rotation:** render two full 360-degree sweeps from one fixed camera.
   Test corresponding views for deterministic return consistency.
2. **Artistic rotation v3:** project eight reviewed Nano Banana Pro images onto
   that scene: oil, watercolor, cut paper, woodcut, glazed ceramic, pastel, ink
   wash and cinematic realism. Two full rotations at 1080p; all 144 corresponding
   raw-frame pairs match. This validates static repeated rendering, not independent
   image-generation consistency or camera translation.
3. **Tour v1:** test a moving camera through the library and back. Rotation paint
   produced stretched contours during translation, so the Veo anchors use clean
   geometry/material renders rather than the artistic projectors.
4. **Veo tour:** six bookended four-second Veo 3.1 Quality shots at 1080p, 16:9,
   native audio. Existing lamps/orrery light and visible leaves may move gently;
   prompts forbid people and additional objects. One opening correction and one
   eight-second desk comparison were tested and rejected. Original takes were kept.
5. **Local finish v2:** search actual source frames for matches, trim the overshoot,
   gently retime each shot, and add original local music. No replacement footage
   was needed. The user approved the result, including the contextually acceptable
   remaining stop/start feel of the camera.
6. **4K:** local Real-ESRGAN animation 2x upscale of that exact approved cut. No new
   timing interpolation, edit changes, soundtrack remix or paid generation.

## Camera beats

The original 3D marks occur at 0, 3.84, 7.68, 12, 15.84, 19.68 and 24 seconds.
Veo/editorial beats are evenly timed to four seconds each:

| Final interval | Camera action |
|---|---|
| 0–4 s | Leave the orrery and turn toward the library arch |
| 4–8 s | Cross the existing library doorway |
| 8–12 s | Approach the reading desk |
| 12–16 s | Turn right toward the atrium |
| 16–20 s | Leave through the same arch |
| 20–24 s | Return to the original orrery view |

## Editorial finding and local repair

The matching bookends were **inside** the files. In these six original takes,
source frame 88 (3.666667 seconds) matches the next clip's frame 0 at all five
joins. The original edit cut at physical file-end frame 95, seven frames past
the useful anchor, causing a jump back. The last take also returns at frame 88;
the eight-second alternate's relevant match was frame 184.

This is a measured property of these outputs, not a universal tail-trim rule.
Find and inspect the nearest actual anchors in each new generation. File-end
SSIM alone initially misdiagnosed the handoffs and did not establish that longer
generations have better bookend fidelity.

The trim-only control includes frames 0–87 of shots 1–5 and frames 0–88 of shot 6:
529 frames, 22.041667 seconds. The chosen edit uses monotonic per-shot timing
ramps to restore 24 seconds and smooth the motion handoffs. FFmpeg interpolation
is confined **within each shot**, never across cuts. There are no crossfades or
geometric alignment warps at the handoffs. The exact source identities and trim
recipe are in [`meridian_house_edit.json`](meridian_house_edit.json); shot-specific
ramps remain in [`tour-retime.mjs`](../tools/scene-lab/tour-retime.mjs).

Five cut frame-delta ratios measured 0.877, 0.940, 0.680, 0.923 and 1.078. The
eight-pair motion ratios measured 0.889, 1.046, 0.779, 0.776 and 1.323, with a
separate eleven-pair cross-check. These are local diagnostic measures, not proof
of invisible cuts or persistent generated geometry.

## Sound and upscale

Original score: **“After Hours at Meridian House”**, an 80 BPM, eight-bar local
oscillator composition with bell-like arpeggios and warm sustained chords. No
sample library, downloaded music or paid music generator was used. Quiet native
Veo ambience remains underneath. The finished mix measured about -18.84 LUFS and
-7.68 dBTP before AAC. The user listened to and approved the 1080p version.

Three sample views compared plain Lanczos, general Real-ESRGAN 4x reduced to 2x,
and native animation 2x. The animation model was selected for cleaner book spines,
curves and architectural edges. Actual model: `realesr-animevideov3-x2`, wrapper
ID 0 in `realesrgan-ncnn-py==2.0.0`, exposed as `--model 1` by the corrected repo
helper. Tile size 256; no extra sharpening. Final encoding: H.264 High, yuv420p,
CRF 16, slow preset, MP4 faststart, stream-copied audio.

The verified 4K export preserves every video presentation timestamp, all 1,126
AAC packets and their timing, and identical decoded audio. Full decoding and
black/freeze checks passed. Sixteen tour views, native-pixel comparisons and dense
moving-detail strips were inspected. Review was local, with no external QA upload.

## Cost record

User authorization: strictly below **$50 all-in**, including artistic-rotation-v3
image work. Operational cap: $49. There were ten successful image calls and one
quota failure; image billing was not reconciled. Eight Veo requests totaled 36
requested seconds: estimated $14.40 at the recorded rate. With a $10 prior-image
reserve and $1 infrastructure reserve, the conservative allocation is **$25.40**.
Reserves are not actual billed charges or an invoice. Local editing, music, QA
and 4K upscaling added **$0 in generation charges**. Do not release reserves or
claim final actual spend without billing reconciliation.

## Local deliverables and source boundary

Production root: `data/workspace/meridian-house/` (ignored, not included in Git).

- Artistic rotation: `artistic-rotation-v3/16x9/sweep.mp4`.
- Finished 1080p: `veo-tour-v1/edit/local-v2/final/meridian-house-tour-v2.mp4`.
- Full 4K video: `veo-tour-v1/edit/local-v2/upscale-4k/meridian-house-tour-v2-4k.mp4`.
- 4K poster, description and technical evidence: adjacent to that 4K video.
- Runtime source hashes, clip decisions and cost ledger remain local; the compact
  source recipe contains only relative clip names, technical settings and hashes.

Approved 1080p SHA-256:
`bd325ccef807f0b50a6d1d4fae1d9e6d6e2f6f63df6cdc781ef213384734e356`.
Delivered 4K SHA-256:
`7633acfe8cff9c2a6886136af0c67f96661edcd92e946ef21d83328a2f0d1504`.

Git contains the procedural model, cameras, shader, bounded generation wrappers,
local editing/music/upscale tools, tests, this sanitized brief and recipe. It does
not contain generated footage/images/audio, model weights, a Python environment,
credentials, home-directory paths, account IDs or provider operation records.
Rebuilding the local scene is possible from source alone. Reproducing the exact
finished video additionally requires the retained local Veo clips; new model
generations are not promised to be identical.

## Limits and next work

The generated library briefly invents a globe/side table, a wall ring turns into
a hanging ornament, and bookshelves appear in the conservatory. These accepted
Veo artifacts remain. Camera easing is perceptible. The upscale cleans detail;
it does not repair source geometry or guarantee perfectly seamless motion.

Next: choose one visual style, test overlapping translation views, keep persistent
3D geometry/camera output as the reference, and investigate registered local
lighting/foliage animation with occlusion. Characters, rigging, a shared scene clock,
UV baking and generalized editing are separate future work, not implemented claims.

## Publication description and credits

A midnight tour through an imagined mansion: past the glowing orrery, into the
library, and back again. Built from one procedural 3D set and six bookended Veo
shots, locally edited at the matching frames and gently retimed. This is a motion
experiment, not a claim of perfectly preserved generated geometry.

Scene, cameras, editing tools and original music by Astra / Codex. Video motion
and native ambience by Google Veo 3.1 Quality via Vertex AI. Local 3D rendering
with WebGL 2; timing, audio mixing and encoding with FFmpeg. Locally AI-upscaled
from 1080p to 4K with Real-ESRGAN (`realesr-animevideov3-x2`) via
`realesrgan-ncnn-py`. Original score: “After Hours at Meridian House,” synthesized
locally without external samples.

https://github.com/TeeKay-FourTwentyOne/video-generator
