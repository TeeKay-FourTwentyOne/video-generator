# Wavefield

A 24-second, six-pulse abstract film. The picture is built from generated
boundary images and numerical complex-wave propagation. Motion, interference,
detector response, sound and the final expansion are computed locally.

## What is calculated

The six selected images form a continuous boundary source. Dense bidirectional
optical flow carries the folds between anchors. This is image registration, not
an optical propagation law. Linear-light luminance supplies the squared amplitude
of three displaced source fields. Each has its own carrier tilt and curvature:

```text
psi_j(x, y) = sqrt(L_j(x, y) / 3) exp(i phi_j(x, y))
H(kx, ky; z) = exp(-i z (kx^2 + ky^2) / (2 k0))
psi_j(z) = IFFT(FFT(psi_j(0)) H)
I_coherent = |psi_1 + psi_2 + psi_3|^2
I_incoherent = |psi_1|^2 + |psi_2|^2 + |psi_3|^2
I_cross = 2 Re(psi_1 conj(psi_2) + psi_1 conj(psi_3) + psi_2 conj(psi_3))
```

The intensity used in the picture includes the cross terms. Dark seams can
therefore come from actual destructive interference, even where the independent
fields are bright. For every rendered frame, the recipe records propagation
energy error, the cross-term identity error, and constructive/destructive regions.
Six full complex-field snapshots retain all three propagated branches, coherent
and incoherent intensity, cross terms and phase.

The Fresnel operator is the paraxial scalar propagator with its common carrier
phase removed. The arrays are zero padded before propagation and cropped after
it; the operator itself has periodic FFT boundaries. Coordinates and propagation
distance are dimensionless. This is a changing boundary-value construction,
not the evolution of a closed state: the source images and camera change with
time. Energy conservation is checked across each propagation operation.

The optical basis follows [MIT's Fourier optics formulas](https://www.mit.edu/~birge/formulas/fourieroptics.pdf)
and the [angular-spectrum construction in MIT's diffraction notes](https://people.csail.mit.edu/dgreensp/may/diffraction.html).

## What is authored

Six phase disturbances begin at exactly 2, 6, 10, 14, 18 and 22 seconds. Their
traveling ring functions drive phase and displacement. Their regular timing,
increasing strength, visual camera travel, bloom and color are artistic controls.
The final disappearance, surviving point and white expansion are precisely timed
compositing. None of these is a measurement prediction.

This film does not implement GRW, CSL or Diosi-Penrose collapse dynamics. It is
an abstract work inspired by the question of how overlapping possibilities
become one outcome.

## Numerical verification

`field.verify()` checks power conservation, forward/backward recovery, an
independent analytic Gaussian solution, a plane-wave eigenmode, constructive and
destructive interference identities, doubled spatial sampling, and agreement
with a band-limited Helmholtz comparator on a smooth Gaussian. Film frame
measurements are separate from those controlled analytic tests. They do not
certify a collapse theory or the accuracy of an unbounded physical experiment.

## Files and reproduction

- `generation.py` prepares immutable request snapshots and records a selection
  from each pair. It does not submit provider calls. Both candidates survive.
- `field.py` implements the numerical propagation and independent checks.
- `render.py` registers the six masks, computes the fields, and renders motion.
- `render_v2.py` tracks one source junction, moves the camera in sooner, resolves
  curved macro strands, and computes inward packet envelopes and colored ripples.
- `sound.py` synthesizes one click and six progressively nearer versions, plus
  body, resonance and a quiet field-air stem. No stock recording is used.
- `report.py` creates six comparable field plates and a local calculation page.
- `validate.py` decodes every frame and measures continuity, white, the surviving
  point, encoded sound correlation, true peak and final silence.
- `deliver.mjs` uses maintained acceptance and project-analysis checks, copies
  the continuous picture stream, adds sound, records clip uses and builds the
  native review player.

Use the repository's provisioned Python environment with NumPy, SciPy, Pillow
and OpenCV. FFmpeg is required. Commands run from the repository root:

```sh
PYTHON=data/tools/clip-analysis/semantic-v1/python/bin/python
"$PYTHON" tools/wavefield/render.py verify
"$PYTHON" tools/wavefield/render.py preview --width 540 --field-width 360
"$PYTHON" tools/wavefield/render.py render --width 1080 --field-width 1080 --output edit/picture-v1.mp4
"$PYTHON" tools/wavefield/sound.py
```

The versioned private workspace is `data/workspace/wavefield-v1`. Retain its
original images, exact prompts, snapshots, both candidates, selection lineage,
numerical arrays, audio stems and QA. Render and audio commands refuse to replace
an existing output. Native delivery is 1080 by 1920 at 30 fps; this is not a 4K
finish. Human listening and director approval are separate review steps.

The native delivery retains explicit BT.709 H.264 VUI and container tags. A
metadata-only correction was retained separately from the original render;
decoded YUV hashes match. With the existing local analysis corpus, its default
Node heap was insufficient during indexing. The maintained recovery/check calls
completed with `node --max-old-space-size=16384`; existing extraction runs and
their `needs-review` states were retained.

## Second draft

The v2 camera follows measured source coordinates of the same bright intersection
through the six anchors, reaching the final material image at 9.5 seconds.
Apparent scale increases from 1.12 to 42. The last part of the approach reveals
curved analytic strand masks within the source luminance. Secondary strands
converge and disappear, while Gaussian packets travel along each curve and are
absorbed at its junction. Three complex fields are propagated and interfered on
every frame. Absorption, camera travel and display color are authored controls;
per-frame propagation remains unitary before cropping.

```sh
"$PYTHON" tools/wavefield/render_v2.py preview --width 540 --field-width 540 --preview-prefix v2-study
"$PYTHON" tools/wavefield/render_v2.py render --width 1080 --field-width 1080 --output edit/picture-v2.mp4
"$PYTHON" tools/wavefield/report.py --version picture-v2 --name v2
node tools/wavefield/deliver.mjs data/workspace/wavefield-v1 v2 --copy-audio-from=v1
```

The final assembly command requires the imported source, accepted clean range,
`edit/v2.json`, and completed project analysis. It preserves the first draft's
AAC stream and verifies both encoded packet and decoded PCM hashes. Earlier
films, image studies, numerical snapshots and notebooks remain intact.

## Gentler opening

`render_v3.py` scales the opening zoom increase by two thirds through three
seconds, then uses a quintic ease to meet v2 at frame 250. Ripple and material
timelines stay fixed. Render only the changed opening:

```sh
"$PYTHON" tools/wavefield/render_v3.py render --width 1080 --field-width 1080 --frames 250 --output edit/picture-v3-opening.mp4
```

`join_v3.py` joins that opening to a retained v2 tail beginning at frame 250.
The tail is extracted at the v2 keyframe with stream copying. Its extraction
recipe and frame hashes are retained in the revision workspace. Joining verifies
the full 720-frame timeline, exact timestamps and every decoded source frame;
the last 470 frames must match v2 exactly. Delivery copies the complete v2
soundtrack through `deliver.mjs ... v3 --copy-audio-from=v2`.

## Sharper detector sound

`sound_v4.py` synthesizes short damped contacts with a small secondary mechanical
contact. It removes the low resonator, replaces the long echoes with faint short
reflections, and makes the final detector tick fully dry. The original quiet
field-air stem is retained sample for sample. Six source events remain at the
same samples, and their level and clarity increase through the approach.

```sh
"$PYTHON" tools/wavefield/sound_v4.py
node tools/wavefield/deliver.mjs data/workspace/wavefield-v1 v4
"$PYTHON" tools/wavefield/validate.py data/workspace/wavefield-v1/final/v4/film.mp4 --name native-v4 --audio-reference audio/mix-v4.wav
```

The edit uses the complete v3 source picture. The revision preserves prior
sound stems and films, records the new sound recipe before synthesis, and checks
detector duration and low-frequency energy against the original separate stems.
Source measurements describe the signal; they do not establish human listening.

## Authorized 4K finish

`upscale.py` prepares a 2160 by 3840 counterpart of the existing v3 picture used
in v4. It uses a local 2x Lanczos resize with accurate rounding and retains the
resized samples in a lossless H.264 intermediate. The numerical wave fields were
computed at the original native resolution; this finishing pass resamples that
picture and does not introduce new motion or rerun the field simulation.

```sh
"$PYTHON" tools/wavefield/upscale.py
node --max-old-space-size=16384 tools/production/film.mjs finish data/workspace/wavefield-v1 v4 v4-4k --sources=edit/finish-v4-4k.json
```

The source map and inspected counterpart must exist before finishing. The
maintained editor cuts the same six integer-frame ranges at 4K, copies the
complete v4 audio stream, verifies coded and decoded sound identity, records the
counterpart uses and imports the master. Private evidence retains the resize
recipe, exact source hashes, full-frame reference comparison, timing checks,
compression comparison, frame inspection and project analysis. All prior versions
remain intact during active production.

The project-specific `finish.mjs` also invokes that maintained editor after a
fresh required-analysis check, under the maintained project lock. It can finish
from existing verified analysis while the shared catalog search refresh is
deferred. Its explicit `--recover-project-lock` option only recovers a lock whose
owner has stopped, using the maintained ownership checks. It does not suppress
missing or failed analysis.

## Published archive

The final release and restoration order are documented in
[the closeout notes](../../briefs/wavefield/closeout.md). The active workspace
commands above describe production history. Use a restored working copy for
future revisions; the sealed archive is read-only. Superseded edits and complete
mixes are removed only through the verified retention transaction, with their
source inputs and historical delivery evidence retained.
