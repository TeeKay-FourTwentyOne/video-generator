# Scene Lab

A local prototype for videos grounded in one persistent 3D scene. The first set,
**The Meridian House**, has an atrium with an orrery, a library, and a conservatory.
Doorways connect actual rooms in one coordinate system. Furniture, books, plants,
and planets are individually named mesh objects.

The initial deliverable is a **geometry and camera study**, with local materials.
The completed style experiment projects eight reviewed Nano Banana images onto
the same static model. Those two rotation versions contain no people or Veo output.
The subsequent living-tour experiment uses Veo 3.1. Its locally repaired edit was
approved by the user and delivered as a **4K full video**; known generated interior
mutations remain, so it is not a geometry-locked final. The
[production brief](../../briefs/meridian_house_brief.md) records the complete result.
The first artistic video is saved at
`data/workspace/meridian-house/artistic-rotation-v3/16x9/sweep.mp4`: 1920 × 1080,
24 seconds, two full revolutions. All 144 corresponding raw-frame hashes match.
The labeled source sheet is `data/workspace/meridian-house/styles-v1/style-board.png`.

## Run

Node 22+ and an installed Chrome/Chromium are required for capture. The interactive
studio works in a browser with WebGL 2. ffmpeg is required only for MP4 encoding.
No npm install is needed.

```bash
npm run scene:studio
# http://127.0.0.1:4317

npm run scene:capture -- --output=data/workspace/meridian-house/take-01

npm run scene:capture -- --shot=tour --aspect=16:9 \
  --output=data/workspace/meridian-house/tour-01

npm run scene:test
```

`SCENE_LAB_CHROME` can point to an installed browser if automatic discovery fails.
The preview server serves only its own allowlisted assets on loopback. It does not
serve the repository, credentials, or workspace outputs. Capture launches an
isolated temporary browser profile, blocks page requests outside the local
studio, and removes that temporary profile on completion. Your normal browser
profile is not used. This is request isolation, not an operating-system firewall.

Existing capture output directories are refused. Each run belongs under the
repository's gitignored `data/workspace/` directory. Code stays in `tools/scene-lab/`
so it can move into another package later without changing the current MCP server.

## What is implemented

- Procedural triangle meshes in metres, Y up, with stable object names and IDs.
- Wavefront OBJ + MTL export for editing in Blender or another 3D tool.
- Two complete 360° sweeps from the same camera position.
- A continuous camera route through the library doorway and back to its starting
  position and orientation. The route centerline is tested for wall intersections.
- 16:9 and 9:16 renders with a fixed 64° **vertical** field of view. Portrait uses
  its own projection matrix; it is not a crop of the landscape render.
- Beauty, clay, depth, world-normal, object-ID, and image-coverage previews.
- Source-camera metadata with a geometry checksum, dimensions, and view-projection
  matrix. Imports reject mismatched scene geometry, aspect ratio, or invalid poses.
- Up to eight perspective image projectors with source depth checks, surface-angle
  weighting, and feathered blending. Hidden surfaces are not painted through.
  Source image centers receive more weight to keep different styles distinct.
  Coverage is independent of angle weighting so visible distant floors keep paint.
- Local PNG sequences and silent H.264 MP4s. Defaults: 6 distinct images/second,
  24-second shot, 24 fps output with held frames. No optical flow or video model.
- A manifest with every frame's camera, scene revision, sample time, pixel hash,
  continuity checks, and generation-call count.

The two revolutions are independently rendered; their matching frames are compared
before video compression. Pixel identity checks determinism of a static scene,
not the consistency of independently generated images. The tour separately checks
returning to the exact initial view after changing camera position.

## Outputs

```text
take-01/
  model/
    meridian-house.obj     # geometry, named objects, vertex normals
    meridian-house.mtl     # base materials
    scene.json            # scene revision, rooms, object catalog
  16x9/                   # also 9x16/ when --aspect=both
    frames/               # numbered PNG samples
    refs/                 # anchor beauty/depth/normals/objects + camera JSON
    qa/                   # self-projection coverage
    poster.png
    sweep.mp4             # or tour.mp4
  image-prompt.txt         # proposed image restyling prompt; never submitted
  manifest.json
```

Depth preview is **radial camera distance / 30 metres**, clamped to [0,1], quantized
to an 8-bit PNG. It is a visual guide, not calibrated linear-Z or metric EXR input
for a depth-conditioned model. Normals are world-space RGB = (normal + 1) / 2.
Object colors are diagnostic pseudo-colors, not an exact ID interchange encoding;
the model catalog is the authoritative ID map. A future depth-conditioned adapter
must convert the depth convention expected by that model.

## Image generation and projection

The interactive studio and capture command do not invoke a generator. The repository provides
`tools/nano-banana.cjs` for Gemini reference-image generation through its configured
Vertex AI account. It is the existing integration to evaluate once a specific
request is discussed; no alternative service has been contacted or recommended
based on unverified capability claims.

For a new experiment, start with one
`16x9/refs/anchor-00.beauty.png` using `image-prompt.txt`, with the same 16:9 framing.
Discuss the image, prompt, provider, and spend before invoking a generator beyond
the user's approved scope. The eight-style experiment below was user-authorized.
Depth/normals are exported for inspection and future conditioning; the existing
Nano Banana tool accepts image references and does not expose a strict geometry
constraint. A prompt to preserve silhouettes is not a guarantee.

In the studio:

1. Save a frame and its matching camera JSON. “Save camera” uses the last saved
   frame, even if the camera has moved since that save.
2. After a generated or manually edited image has been approved, load that camera
   JSON and select the matching image. Keep its exact aspect and framing.
3. Inspect **Projection coverage**, rotate, and take the library tour. Missing
   areas remain on the local base materials; they are not hallucinated.
4. Repeat from a new source camera to fill missing surfaces. Use the current
   textured render as context for the next image when generation is authorized.

The “Test projection with this render” button uses the local render itself as
the texture. It is a calibration test, not AI image generation.

To encode approved projections, create a local JSON file containing paths relative
to that JSON file:

```json
[
  {
    "image": "painted-anchor-00.png",
    "camera": "../take-01/16x9/refs/anchor-00.camera.json"
  }
]
```

```bash
npm run scene:capture -- --projections=data/workspace/meridian-house/paint/projections.json \
  --output=data/workspace/meridian-house/painted-01
```

It is useful to paint from landscape sources even when delivering portrait:
landscape covers more horizontal surface per source image. Eight portrait sources
at this field of view do not cover an entire 360° horizon. Projection count and
coverage are explicit prototype limits; source views also need vertical and
occlusion coverage, not merely evenly spaced yaw angles.

Capture copies imported images and their camera JSON into the output's
`projections/` directory, with a reusable `projections.json` beside the manifest.
The saved run therefore retains its projection inputs even if the original files
are moved later.

## Eight-style rotation experiment

`style-frames.mjs` prepares eight source prompts at 45-degree intervals: oil,
watercolor, cut paper, woodcut, glazed ceramic, pastel, ink wash, and cinematic
realism. Generation is opt-in and uses the existing Nano Banana CLI after user
authorization. The command records submissions and successes, preserves completed
outputs, and stops on an API failure without automatically retrying.

```bash
# Prepare only: no external calls.
node tools/scene-lab/style-frames.mjs --output=data/workspace/meridian-house/styles-v1

# Once authorized, submit selected source frames. Existing completed images are kept.
node tools/scene-lab/style-frames.mjs --generate --only=0,1

# Locally normalize selected results to exact 16:9; no crop or content synthesis.
node tools/scene-lab/style-frames.mjs --normalize --only=0,1
```

The tested provider returned 2752 × 1536 for a requested 2K 16:9 image. The local
normalization step resizes the entire canvas to 2048 × 1152, records the source
checksum and dimensions, and rejects aspect differences greater than 2%.
Normalization preserves the full frame but cannot repair generation-induced drift.

Review each image against its source before making the final projection list.
In the first experiment, the initial ceramic image invented a doorway in an empty
wall, and the cinematic image added two wall sconces. Both were excluded and
corrected with targeted prompts saved beside the original prompts. The reviewed
list is `data/workspace/meridian-house/styles-v1/projections-reviewed.json`, with
selection decisions in `review.json`.

```bash
node tools/scene-lab/capture.mjs \
  --projections=data/workspace/meridian-house/styles-v1/projections-reviewed.json \
  --output=data/workspace/meridian-house/artistic-rotation-v3 \
  --aspect=16:9 --size=1080 --fps=12 --duration=24
```

The same eight images stay fixed during both revolutions; no new generation occurs
as the camera moves. Different styles blend across their shared surfaces. Capture
serves only the explicit input image bytes over loopback, avoiding large image
data URLs in browser-control messages. Rendered PNG results are transferred in
bounded chunks so high-resolution frames do not overflow the browser-control
connection. The scene's clay pass always ignores paint.

Generate a labeled, local contact sheet of the reviewed source images with:

```bash
node tools/scene-lab/style-board.mjs \
  data/workspace/meridian-house/styles-v1/review.json \
  data/workspace/meridian-house/styles-v1/style-board.png
```

The capture manifest's zero generation cost applies only to the local render.
Image-generation billing is separate and is not reported by the existing CLI.

## Living-tour Veo experiment

The first Veo test uses seven clean 1080p renders at the original tour's movement
boundaries (0, 3.84, 7.68, 12, 15.84, 19.68, 24 seconds). Six four-second shots
use adjacent images as their first/last frames. No new image generations were
needed. The existing Google Vertex integration is used; no additional provider
receives the scene or footage.

Rotation paint was **excluded** from these anchors after a local translation test
revealed stretched book contours and a duplicate-looking orrery ring on the wall.
The original clean tour materials are used throughout. Rejected trial anchors are
retained as evidence, not submitted to Veo.

```bash
# Local preparation only. Choose a NEW run directory.
node tools/scene-lab/tour-veo.mjs prepare --output=data/workspace/meridian-house/veo-next

# Inspect every anchor; record anchor-review.json and include prior costs in the ledger.
# PAID: only after authorization and review. Submit individually; never auto-retry.
node tools/scene-lab/tour-veo.mjs submit --output=data/workspace/meridian-house/veo-next --shot=1
node tools/scene-lab/tour-veo.mjs poll --output=data/workspace/meridian-house/veo-next

# Local contact sheets, endpoint metrics, black/freeze and audio-level checks.
node tools/scene-lab/tour-qa.mjs data/workspace/meridian-house/veo-next 1
node tools/scene-lab/tour-veo.mjs status
```

Submission checks reviewed anchor/prompt hashes, pre-logs the requested cost,
and refuses a second submission with the same take record. Polling records both
successful downloads and terminal failures. This recipe is limited to Quality
Veo 3.1, 1080p, 16:9, native audio, four/eight-second requests and at most two
recorded takes. The Meridian budget has a $49 operational ceiling for the user's
strictly-under-$50 **all-in** authorization, including prior images and overhead.
Reserve entries are not actual billed charges; do not release them without
reconciliation. The run's `budget.json` contains the current accounting caveats.

`tour-veo.mjs assemble` requires six approved, hash-matched selected takes.
For failed experiments, `tour-review.mjs RUN_DIRECTORY [NEW_OUTPUT_DIRECTORY]`
instead requires explicit `includedForReview` decisions under a `needs-review`
verdict. It creates a visibly labeled diagnostic cut and a beat-aligned comparison
against the original 3D tour. It does **not** approve clips or create a final edit.

The September 12 experiment produced six original clips, one opening correction,
and one eight-second duration comparison. Both alternates were rejected. The
longer clip improved the final-image SSIM but introduced a worse camera path and
new ornaments: endpoint similarity alone cannot establish scene consistency.
All original takes are included in the diagnostic edit to expose the full route.

Outputs are under `data/workspace/meridian-house/veo-tour-v1/`:

- `edit/review-v1/tour-review.mp4`: 24 seconds, 1920 × 1080, 24 fps, native audio.
- `edit/review-v1/tour-comparison.mp4`: synchronized six-beat 3D/Veo comparison.
- `clip-review.json`: time-stamped defects and explicit keep/reject decisions.
- `anchors/`, `prompts/`, `operations/`, `clips/`, `qa/`: reproducible inputs and evidence.
- `budget.json`, `README.md`: cost allocation and experiment handoff.

Visual review used direct assistant vision on local contact sheets, not the repo's
separately billed Claude QA API. No people were present. Audio was technically
checked but could not be auditioned in this session; it remains pending human
listening review. All paid generation has stopped for this version.

## Limits and next experiments

### Local tour finish v2: the bookends were inside the files

The first review edit's endpoint diagnosis was incomplete: it compared physical
file ends and missed the matching views earlier in each clip. A full frame-exact
search found **frame 88 at 3.666667 seconds** as the match to the next clip's frame
0 in all five original joins. The eight-second alternate matches at frame 184.
The final original take also matches the initial view at frame 88. These findings
apply to these recorded outputs, not every Veo request. Do not hardcode a universal
eight-frame tail trim; search and inspect the actual footage.

The earlier 4-vs-8-second end-SSIM comparison measured file ends, not the nearest
bookends. It therefore does **not** establish better anchor fidelity at eight
seconds. The observed interior prop/geometry and path defects remain valid.

The local pass uses the original six takes, with no new generation requests:

1. Decode each source once to small luma proxies and search interior frame pairs.
2. Inspect the candidate pair sheet. Keep the shared anchor once, not twice.
3. Preserve a 22.04-second trim-only cut as the control.
4. Apply monotonic per-shot timing ramps to match incoming/outgoing motion, using
   FFmpeg motion interpolation **within** each shot. Never interpolate across a cut.
5. Verify frame deltas and motion speeds separately, plus dense cut samples.
6. Mix an original locally synthesized bell/pad score over quiet native Veo room tone.

The 24-second, 1080p deliverable is
`data/workspace/meridian-house/veo-tour-v1/edit/local-v2/final/meridian-house-tour-v2.mp4`.
`before-after.mp4` compares the original edit and the local finish. `qa/` contains
the measurements, dense join strips, interior samples and technical scan.
`final/description.md` provides publication text and credits; nothing was published.

The new tools are all local-only:

```bash
# Each command preserves existing runs and refuses to overwrite outputs.
node tools/scene-lab/seam-search.mjs RUN_DIR NEW_SEARCH_DIR
node tools/scene-lab/tour-finish.mjs RUN_DIR EDIT_PLAN_JSON NEW_TRIM_DIR
node tools/scene-lab/tour-retime.mjs RUN_DIR NEW_RETIME_DIR 1080
# With retained clips and the sanitized source recipe, no runtime plan copy is needed:
node tools/scene-lab/tour-retime.mjs RUN_DIR NEW_RETIME_DIR 1080 briefs/meridian_house_edit.json
node tools/scene-lab/tour-score.mjs RUN_DIR PICTURE_MP4 NEW_FINAL_DIR
node tools/scene-lab/tour-finish-qa.mjs RUN_DIR
```

The finishing recipe intentionally targets this six-shot experiment. The retimer
reads its reviewed `edit/local-v2/edit-plan.json`, uses the discovered frame 88 and
shot-specific speed ramps, and checks source hashes. It is not a general-purpose
automatic film editor. Candidate data and direct visual review remain essential.

All five final joins pass the configured local frame-delta and motion-ratio bands,
including an eleven-pair motion cross-check. These are diagnostic indicators, not
a guarantee of imperceptibility. The source's interior invented globe, hanging
ornament and room changes remain. The music was technically checked, not auditioned.
New generation spend is $0; the conservative all-in allocation remains $25.40,
including the prior-image/cloud reserves, with actual billing still unreconciled.

### Approved 4K delivery

After the user approved the 1080p local finish, it was upscaled locally to
3840 × 2160 using Real-ESRGAN `realesr-animevideov3-x2`. The corrected
`tools/upscale.py --model 1 --scale 2` maps to wrapper model ID 0 in
`realesrgan-ncnn-py==2.0.0`. The general model is wrapper ID 4, not 0; native
model scale must not be assumed from the public CLI ID. General 4x/reduced 2x
and native animation 2x were compared on three source views before selection.

The upload copy is
`data/workspace/meridian-house/veo-tour-v1/edit/local-v2/upscale-4k/meridian-house-tour-v2-4k.mp4`:
24 seconds, 24 fps, 576 frames, 80.5 MB, H.264 CRF 16 / slow, yuv420p, faststart.
Every presentation timestamp and all AAC packets/decoded audio match the approved
source. No interpolation, retiming, additional sharpening or audio re-encoding
was added by upscaling. Local sample review and full technical QA passed.

Use Python 3.12 with `realesrgan-ncnn-py==2.0.0`, Pillow, NumPy and OpenCV installed
in an isolated, ignored environment. The weights run locally; no footage upload
or paid generation is required. The native macOS wheel used in this production
was available for Python 3.12, not the default Python 3.14 interpreter.

```sh
data/tools/upscale-venv/bin/python tools/upscale.py INPUT_1080.mp4 NEW_4K.mp4 \
  --scale 2 --model 1 --tile 256 --crf 16
data/tools/upscale-venv/bin/python -m unittest discover -s tools -p test_upscale.py -v
```

`upscale-sample.py` compares candidate models; `upscale-qa.py` checks the exact
Meridian approved source, timestamps, audio and pixels and emits local reports.
Those reports contain runtime paths and are not source-publication artifacts.
The [source recipe](../../briefs/meridian_house_edit.json) preserves sanitized
source clip hashes, trim ranges and timing settings; exact reproduction still
requires the retained local footage. A fresh clone can rebuild the 3D set but
cannot recover generated clips from their hashes. The accepted video has not
been published by the agent. Add the published URL to the brief when supplied.

### Rendering and scene limitations

The scene is deliberately static. Frame time moves the camera; it does not advance
characters or props. Conversing diners require rigged characters, persistent
identity, and a shared scene clock so off-screen actions progress deterministically.
Those are separate work from architectural continuity.

Image projection is implemented as camera-calibrated texture sampling during
rendering. It is **not yet a UV atlas bake**. The OBJ exports geometry and base
materials, not projected textures or the shader's procedural tile pattern. Keep
the projection images and camera JSON with the set. The renderer recomputes source
depth from this exact static geometry; moving an object would require a new
visibility pass and an object-local texture strategy.

Independent generated images can disagree on patterns, lighting, or silhouettes.
Weighted blends can ghost conflicting details and bake view-dependent highlights
into surfaces. The depth mask prevents projection through geometry but cannot
repair inconsistent source images. The completed rotation deliberately mixes
styles, and some overlapping contours remain doubled. The next consistency study
should use one chosen style and test a small sideways move, then an overlapping
second source view. The first Veo test instead used clean original renders;
first/last conditioning still did not preserve all furniture or the return view.
An untested next direction is retaining 3D as the full-frame camera/geometry source
and constraining generated motion to registered lighting or foliage regions.
That requires alignment and occlusion work; it is not an automatic compositing fix.

The current renderer is a simple material study with approximate local lighting;
it has no physically based shadows, reflections, ray tracing, or photorealism.
Source geometry is editable in `scene.mjs`; OBJ is a one-way export in this version.
Importing artist-edited meshes, UV baking, geometry-conditioned image adapters,
dynamic 3D objects, and a continuity-preserving Veo composite remain future work.
