# Angles

The latest study uses `accelerate.py`: one fixed vertical axis, one continuous
exponential speed ramp and no cuts. Speed rises from 1 rpm to 1,440 rpm in
30 seconds. The existing full-sphere source and all scene properties are fixed.

```sh
python3 tools/angles/accelerate.py \
  --source=data/workspace/angles/rotation-v1/source \
  --output=data/workspace/angles/acceleration-new/edit --size=1080
```

Output is native 1080p at 60 fps. Use `--size=270` for timing auditions.
`--end-rps` can lower the final speed; the default and upper bound are 24.
The initial yaw is -17 degrees with fixed zero pitch and -8 degrees of bank.
A cached yaw projection is checked against the general 3-D camera projector.
Every turn samples the same surrounding radiance, and only speed changes.
The finisher streams native frames into FFmpeg and retains their byte hashes,
all 1,800 reference proxies and selected native stills. QA decodes every frame,
checks neutral chroma, increasing speed/phase and sub-half-turn frame steps.
The final section intentionally flashes; fine repeated details can alias at
these speeds. The review page starts paused and does not loop.

The preceding study uses `spin.py`: six substantially faster fixed-center
rotations through the full sphere. It returns to the original solid-silver
scene, with unchanged materials and lighting. Render the source using
`physical-panorama.py --width=12288 --latitude=90 --samples=48`, then run:

```sh
python3 tools/angles/spin.py \
  --source=data/workspace/angles/rotation-new/source \
  --output=data/workspace/angles/rotation-new/edit --size=1080
```

Use `--size=270` with a separate output directory to audition timing first.
The film is 30 seconds, 24 fps with 12 held poses per second. Yaw, end-over-end,
diagonal, reverse, compound and accelerating rotations each occupy five seconds.
Quaternion-free axis rotation matrices preserve the camera basis through poles.
QA records camera bases, all-frame encoding comparisons, neutral chroma and
per-segment light/dark statistics. Longitude wraps; pole sampling is edge padded.

The scene direction is **solid silver**: sparse opaque machined forms, black
recesses and bright neutral reflections. `physical.py` builds the editable
Blender scene. `physical-panorama.py` renders the surrounding angular view with
Cycles. `finish-physical.py` samples the camera directions, holds each pose for
three frames, encodes the 30-second film and builds the review page.

```sh
BLENDER_BINARY=/path/to/blender
"$BLENDER_BINARY" --background --factory-startup --python-exit-code 1 \
  --python tools/angles/physical.py -- \
  --output=data/workspace/angles/physical-model-new --size=540 --samples=16
"$BLENDER_BINARY" --background data/workspace/angles/physical-model-new/angles-solid-silver.blend \
  --python-exit-code 1 --python tools/angles/physical-panorama.py -- \
  --output=data/workspace/angles/physical-panorama-new --width=16384 --samples=48
python3 tools/angles/finish-physical.py \
  --panorama=data/workspace/angles/physical-panorama-new \
  --scene-run=data/workspace/angles/physical-model-new \
  --output=data/workspace/angles/solid-silver-new
```

This route requires Blender with Cycles/Metal on Apple Silicon and Python with
NumPy, Pillow and OpenCV. It makes no generation-provider requests. The large
angular source is rendered at its original resolution to supply the whole
surrounding view; the film is 1920 by 1080, with no 4K upscale. Sampling the
angular render is valid because the scene is static, the camera does not
translate and depth of field is disabled. Changes to these conditions require
fresh per-pose rendering.

The saved `.blend`, render inputs, manifests and media remain in the ignored
workspace. QA checks closed meshes, opaque neutral materials, camera origin,
latitude coverage, exact return, grayscale source frames and all 720 decoded
frames. Encoding comparisons use 480 by 270 proxies.

## Earlier WebGL audition

A local 30-second study of chrome surfaces from the center of an irregular
spherical cavity. The camera rotates without translation. Geometry is fixed,
and eight poses per second are held in a 24 fps film. No generation providers
are called. The maximum render size is native 1920 by 1080; 4K is deferred.

The scene is an exact analytic sphere clipped by fourteen planes, plus three
annular cylinders. `scene.mjs` is the editable parametric model. The renderer
uses three specular bounces, approximate studio reflection fill and four
subpixel samples. Fine reflected edges can retain aliasing. There is no
captured metrology data or calibrated surface measurement.

```sh
mkdir -p data/workspace/angles
node --test tools/angles/scene.test.mjs
node tools/angles/capture.mjs --output=data/workspace/angles/materials-new --size=540 --stills=true
node tools/angles/capture.mjs --output=data/workspace/angles/audition-new --size=1080
python3 tools/angles/review.py data/workspace/angles/audition-new --materials=data/workspace/angles/materials-new
```

Requires installed Chrome, Node 22+, FFmpeg and a Python environment with
Pillow and NumPy. Capture reuses Scene Lab's isolated temporary browser and
allowlisted loopback server. Output directories must not already exist.
Source snapshots in each run are provenance records; rebuild through the
repository tools so the shared capture infrastructure is available.

Open the run's `review.html` for the film, finish comparison and sphere
control. `qa/validation.json` records full decoding, all-frame proxy comparisons,
PNG hashes, held-frame encoding checks and the exact return to the opening view.
Both source images and generated files remain under ignored `data/workspace/`.

## Matched metal and lighting auditions

`metal-audition.py` loads the saved Cycles scene and preserves every mesh and
transform while testing `polished` and `shaped` variants. The first tightens the
existing metal reflections. The second also adds a narrow physical white strip
light and reshapes the reverse softbox. Both keep opaque, neutral metal.

Render direct perspective stills first, then render the cropped angular plates
with `--panorama`. The current comparison uses the exact source camera angles
from seconds 11–14, including its settling hold. Cycles cropped longitude bounds
have the opposite sign to world azimuth for this camera orientation.

`finish-metal-audition.py --source=... --plates=... --reference-stills=...
--output=...` builds three matched 3-second clips and an interactive review.
The plate folder contains `polished-plate/` and `shaped-plate/`; the direct
reference folder contains `polished-still/` and `shaped-still-v2/`. The finisher
checks the projected frame against each direct render as well as decoding all
216 output frames, checking neutral chroma, held poses and source encoding.
The original 30-second film is hashed before and after, and remains intact.
