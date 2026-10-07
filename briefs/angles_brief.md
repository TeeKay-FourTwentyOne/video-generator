# ANGLES — inside the sphere

Revised visual audition rendered. 30 seconds, 16:9 landscape, native 1080p
maximum, 60 fps for the current acceleration study. 4K is deferred until the
edit is approved.

## Current direction: one accelerating axis

The user requested a slow start followed by acceleration as far as flashes of
light, within 30 seconds. Every revolution must follow the same path; only its
speed changes. The camera now rotates continuously around the fixed vertical
axis, with unchanged pitch, bank, lens, center, geometry and lighting. There
are no cuts, changes of direction, phase resets or exposure changes.

Speed increases exponentially from 6 degrees per second (1 rpm) to 24 full
turns per second (1,440 rpm). The first revolution takes 11.318 seconds; the
complete film traverses 98.936 revolutions. The same camera orientation always
produces the same image. The initial orientation faces the turned shoulder so
the slow beginning has a clear physical reference.

The film uses 60 distinct frames per second throughout. This supports the
faster movement without changing cadence partway through. At the maximum,
adjacent frames advance less than half a revolution. Fine repeated details can
still alias, and the final section deliberately resolves into rapid flashing
light. The review page identifies that content, starts paused and does not loop.

Recipe: `tools/angles/accelerate.py`. Existing source:
`data/workspace/angles/rotation-v1/source/`. New run:
`data/workspace/angles/acceleration-v1/`. Output:
`edit/angles-acceleration-30s.mp4` and `edit/review.html` within the new run.
Native frame byte hashes, all-frame 480 by 270 references, selected native
stills, the speed curve and source hash are retained. Reusing the existing
source keeps the same world throughout and makes no generation-provider calls.

The completed 1080p/60 fps film passed all 1,800 decoded-frame checks, with a
minimum 48.56 dB encoding comparison at 480 by 270 and exactly neutral chroma.
The cached projection matches the general 3-D camera calculation, identical
phases repeat exactly, and speed/phase increase continuously. The largest
sampled angular step is 143.13 degrees. The last five seconds contain 124
substantial dark/bright transitions. Review playback, seeking and the speed
readout passed browser checks. Both earlier 30-second films retain their hashes.

## Earlier direction: six fast rotations

The user redirected the study toward its original spatial idea: an observer
fixed at the center of a sphere, rotating through different axes. The metal
enhancement auditions did not establish the desired direction. The next cut
prioritizes substantially faster motion, strong differences between segments,
and rapid encounters with bright and dark parts of the same surrounding scene.

The original solid-silver geometry, materials and fixed white lights are reused.
The surrounding angular render now covers the entire sphere, including both
poles. There are six five-second passages, separated by hard cuts:

| Time | Motion | Pace |
| --- | --- | --- |
| 0–5 | Horizontal sweep | One full turn every 3 seconds |
| 5–10 | End-over-end flips | One full turn every 2.5 seconds |
| 10–15 | Orbit on a diagonal axis | One full turn every 2 seconds |
| 15–20 | Reverse horizontal sweep | One full turn every 1.5 seconds |
| 20–25 | Corkscrew | Fast yaw, large pitch oscillation and continuous roll |
| 25–30 | Accelerating oblique tumble | One turn every 2.5 seconds, accelerating to 1.25 seconds |

Twelve poses per second, held for two output frames, retain the stop-motion
cadence while making the much larger angular steps more readable. The camera
never translates or zooms. Light levels change only because different parts of
the fixed world enter the view; there are no animated lights or exposure ramps.

Run: `data/workspace/angles/rotation-v1/`. The new source panorama is a native
12288 by 6144 rendering input, not an upscaled film. The review film remains
1920 by 1080 and 30 seconds. The existing cuts and lighting auditions remain
intact. Reusable camera/finishing recipe: `tools/angles/spin.py`.

Delivered film: `data/workspace/angles/rotation-v1/edit/angles-rotation-30s.mp4`.
Review with segment buttons: `data/workspace/angles/rotation-v1/edit/review.html`.
All 720 frames decoded and passed encoding comparisons (minimum 48.72 dB at
480 by 270). Chroma is exactly neutral. Every camera basis is orthonormal and
every camera position is the origin. Full-turn and pole traversal checks passed;
the new spherical source agrees with the prior scene in five matched views.
Each segment contains 4–12 substantial dark/light transitions; no near-black
interval exceeds two-thirds of a second. The original 30-second film's hash is
unchanged. No generation-provider calls, 4K upscale, commit or push were made.

## Earlier solid-silver direction

The user requested a more photorealistic, physically real, simpler result,
with much brighter metal. Black and neutral silver are the only image colors.
Every surface must be opaque solid metal; no transparency or translucency.

The revised scene replaces the mirrored faceted chamber with a turned shoulder,
a thick ground jaw and two opposed metal faces inside a black spherical
enclosure. True bevel geometry and restrained machining marks establish weight.
White rectangular lights produce broad bright highlights and black reflections.
All metal materials have metallic weight one, transmission zero and alpha one.

Production now uses local Blender Cycles. A single high-resolution angular
render from the center supplies every view in the film. Because the scene is
static and the camera only rotates with depth of field disabled, this preserves
the same outgoing light directions through all shots. The camera remains at
the origin. The new cut retains eight held poses per second and 24 fps output.
Cuts occur at 6, 11, 17, 22 and 26 seconds, with an exact return to the opening.

The angular source is rendered at native 16384 by 4096; it covers the full
horizontal surround and the latitude band used by the film. This is a rendering
input, not an upscaled video. Delivery remains 1920 by 1080. No 4K export or
generation-provider call is part of this revision.

Revised film: `data/workspace/angles/solid-silver-v2/angles-solid-silver-30s.mp4`.
Review page: `data/workspace/angles/solid-silver-v2/review.html`.
The complete editable Blender scene and native angular source are retained
under this run's `source/` directory. The first audition remains intact.

All 720 output frames decoded and passed source comparisons at 480 by 270
(minimum per-frame PSNR 52.73 dB). Every encoded frame has exactly neutral
chroma, U = V = 128. Every source frame is grayscale without alpha. Mesh checks
confirm all five surfaces are closed, positive-volume solids. Camera positions
remain at the origin and the opening and closing source frames match exactly.
An independent direct perspective render and the angular projection agree at
43.53 dB at 1920 by 1080; separate stochastic sampling prevents pixel identity.

The stronger artistic passage is the opposed pair around 13.5 seconds: a bright
face and a darker face meet at a narrow beveled diagonal. Broad highlights are
deliberate; the result remains rendered CG and has not been represented as a
photograph or actual instrument capture. Sound remains deferred.

## Light and metal refinement

The user selected seconds 11–14 as the strongest passage and asked for more
light and metallic character. The next audition keeps that exact geometry,
camera orientation sequence and timing, and compares two material/light changes:

- **A / Clean polish:** smoother silver, more restrained surface texture and
  sharper existing reflections.
- **B / Shaped chrome:** the same polished face, a tighter finish on the dark
  opposing surface, a narrower reverse softbox and one thin white strip light.
  The added reflection gives the dark plane a clearer metallic response.

The artistic preference is B: its bright strip emphasizes the same diagonal
that makes the original passage effective. A remains the quieter alternative.
Neither variant adds geometry, transparency, colored light or bloom. The
original 30-second cut remains intact while the three-second passage is reviewed.

Review: `data/workspace/angles/metal-enhancement-v2/review/review.html`.
Clips: `current.mp4`, `polished.mp4` and `shaped.mp4` in the same folder.
Each is native 1920 by 1080, silent, 3 seconds, 24 fps with eight held poses per
second. Material/light recipes, direct-reference stills, source angular plates
and verification records remain local. No generation-provider calls or 4K
upscale are part of this audition.

All 216 encoded frames passed decoding, neutral-chroma and source comparisons.
The two projected 13-second frames agree with independent direct perspective
renders at 39.64 and 37.17 dB respectively. The review controls preserve the
playhead when switching versions. The original film's SHA-256 is unchanged.

## Earlier concept and first audition

The observer remains at the center of an imperfect sphere. Only orientation
changes. The sphere is a cavity cut by planar tools: near chrome faces,
distant spherical patches, and three annular bearing forms. The world remains
fixed through every cut. No scale is asserted and no measurement data is used.

The point of view is that sharpness is a relationship between surfaces:
the face that catches light from one angle becomes a dark edge from another.
Broad polished faces oppose fine lathe marks; curvature opposes flat cuts;
the open circular bearing opposes the enclosing faceted cavity.

Scary Woods contributes eight held poses per second, brief settling holds and
hard edits. Meridian House contributes persistent geometry and repeatable
camera orientations. The camera never translates or zooms. Six passages cover
edge, reverse, flank, undercut, crown and return. Cuts occur at 6, 10.5, 16.5,
21 and 25.5 seconds. The closing orientation recovers the exact opening view.

The first audition is silent so surface and timing can be reviewed together.
Sound direction remains open: sparse metallic detents and close contact
resonance are preferred to a continuous cinematic score.

The local WebGL renderer uses analytic intersections, three specular bounces,
an analytic studio reflection fill, fixed light panels and procedural
object-local machining marks. It is an artistic approximation, not an optical
simulation of a KEYENCE instrument. KEYENCE surface profilometry is a reference
for treating microscopic relief as landscape, not a source of captured imagery.
Reference: https://www.keyence.com/products/3d-measure/roughness-measure/

No paid provider requests are allocated for the local audition. A provider,
model and spending ceiling must be discussed before any paid generation.
Existing Scary Woods and Meridian House assets remain independent of this study.

First review question: should the enclosing world feel like a precision-made
machine cavity, or should its surfaces be pushed toward damaged metallic terrain?
The initial artistic choice is the precision-made cavity.

Local runs: `data/workspace/angles/`. Reusable recipe: `tools/angles/`.

## Audition 01

Review page: `data/workspace/angles/audition-v1/review.html`.
Film: `data/workspace/angles/audition-v1/angles-audition.mp4`.
The review page includes precision chrome, denser mirror and warm-metal finish
comparisons, plus a perfect-sphere control and a plain geometry view.

The initial high-amplitude surface marks obscured the major forms and were
reduced before the film render. Precision chrome is the selected first look.
This is a stylized local geometry/material audition; fine reflected edges retain
some aliasing. The user's subsequent feedback requested the simpler, brighter,
physically grounded revision described above.

All 720 frames decoded and passed comparisons to the held source sequence at
480 by 270. Minimum per-frame PSNR is 43.16 dB. All 240 source PNG hashes passed;
the source opening and closing views match exactly. Camera-origin and basis
checks passed for every pose. No paid generation calls, upscale, commit or push
were made for this audition.
