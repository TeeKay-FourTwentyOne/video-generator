# Hall of Memories local blocking

## Deep time and the visitors

`deep_time.json` sets the 121-second passage from the retained jewel hold to the
ship's departure. The selected painted relief supplies the surface, with fired
ceramic and mineral texture in the interior. Local animation deforms strata,
translates through the interior, advances and withdraws ice, reveals vegetation,
and articulates the ship and two visitors. The English subtitle is exact local
text. Human recurrence is outside this segment.

Use a new ignored run with `assets/{jewel,ice,interior,dry,green,clearing,ship,explorer}.png`.
The first image is the exact prior Hall endpoint; the ship and explorer require
alpha transparency. Preserve original artwork, image-generation prompts and the
run ledger. This recipe uses Pillow, NumPy, OpenCV, FFmpeg and ffprobe. Commands
below perform no provider calls:

```sh
python tools/hall-of-memories/deep_time_render.py \
  --run data/workspace/hall-of-memories/deep-time-next --stills --width 960
python tools/hall-of-memories/deep_time_audio.py \
  --run data/workspace/hall-of-memories/deep-time-next
python tools/hall-of-memories/deep_time_render.py \
  --run data/workspace/hall-of-memories/deep-time-next --render
python tools/hall-of-memories/deep_time_finish.py \
  --run data/workspace/hall-of-memories/deep-time-next --export --review --verify
```

The renderer streams 968 source poses into 2,904 output frames at 24 fps; it does
not retain a full PNG sequence. Source-pose hashes, selected frames, artwork and
a frozen recipe retain inspectability. Audio is separate original procedural
stems, including fictional-language scratch speech, with no music or animal
calls. Listening remains a creative review requirement.

The finisher expects the selected Hall run as a sibling, plus a local baseline
preservation manifest. It appends this segment to the 185-second core and checks
that every decoded prior picture frame and concatenated PCM sample is preserved.
The review is 306 seconds. The first draft's landing/boarding, puppet articulation,
and changes of scale remain review points. This is 2.5D relief animation, with an
abstract interior passage and no established geological/polis clock ratio.

Open the review HTML directly, or serve the run with working media seeks:

```sh
python tools/hall-of-memories/serve_review.py \
  --root data/workspace/hall-of-memories/deep-time-next --port 8779
```

This binds only to loopback and implements byte ranges for chapter jumps. It does
not publish or upload the review.

## Hall demonstration and first jewel reveal

`polis_hall.json` authors the next complete draft: enter the Hall, hear four
fragments from one fictional person's record, then one derived whole-life voice,
a growing accumulation, and withdrawal to the first exterior jewel reveal.
The preceding two scenes remain preserved working baselines. Stop before deep time.

```sh
python tools/hall-of-memories/polis_hall_audio.py \
  --output data/workspace/hall-of-memories/polis-hall-next

data/tools/blender-local/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup \
  --python tools/hall-of-memories/polis_hall_render.py -- \
  --run data/workspace/hall-of-memories/polis-hall-next \
  --output data/workspace/hall-of-memories/polis-hall-next/render-v1/frames \
  --height 1080 --samples 16

python tools/hall-of-memories/polis_hall_finish.py \
  --run data/workspace/hall-of-memories/polis-hall-next \
  --frames data/workspace/hall-of-memories/polis-hall-next/render-v1/frames \
  --output data/workspace/hall-of-memories/polis-hall-next/edit-v1
```

Before the full render, create `assets/hall-facet.png` from the last withdrawal
pose at native resolution. Find its index from `timeline.json`, render that
single pose with `--start N --end N+1` in a separate study directory, and retain
it as the facet texture. The first run's index is 682. Missing texture is useful
only for an early geometry study; it is not a complete transition. Retain the
source image and its hash alongside the recipe. Use `--stills` for a framing pass.

`polis_hall_verify.py` uses the same render arguments to audit speaking-pose
framing and entry separation without rendering. `polis_hall_bake.py -- --run RUN
--output RUN/animation-v1` runs inside Blender and keys the exact retained
`render-v1/recipe/` source. The bake selects only changing objects, packs the
facet image and keeps a relative audio link. `polis_hall_animation_verify.py
-- --run RUN` compares the saved animation to that recipe at every source pose.
Run these scripts with Blender's `--background --factory-startup --python` form.

The finisher explicitly combines all three selected PCM masters. It verifies
every decoded context frame against those sources and exact concatenated PCM,
without retiming or independently normalizing earlier scenes. `master-timeline.json`
in the run records the available three-scene context and join offsets; it does
not claim a complete factory or deep-time timeline. All media and runtime records
stay under ignored paths. The review has optional external dialogue captions.

Identical held PNG poses share storage through hard links. The renderer refuses
existing output ranges and changed recipes on resume, and stops before a storage
reserve is exhausted. The facet asset must also stay unchanged on resume.
Existing output files, earlier media and unrelated work are preserved.
Voices remain installed local speech plus original procedural scratch vowels;
no provider calls are made. Real-time listening remains a separate review need.

## Elder invitation and Hall threshold

The existing conversation is an accepted revision baseline. Its continuation
is configured in `polis_invitation.json`, with the same temporary voice cast,
puppets and cadence. It ends before a human record is played.

```sh
python tools/hall-of-memories/polis_invitation_audio.py \
  --output data/workspace/hall-of-memories/polis-invitation-next

data/tools/blender-local/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup \
  --python tools/hall-of-memories/polis_invitation_render.py -- \
  --run data/workspace/hall-of-memories/polis-invitation-next \
  --output data/workspace/hall-of-memories/polis-invitation-next/render/frames \
  --height 1080 --samples 16

python tools/hall-of-memories/polis_invitation_finish.py \
  --run data/workspace/hall-of-memories/polis-invitation-next \
  --frames data/workspace/hall-of-memories/polis-invitation-next/render/frames \
  --output data/workspace/hall-of-memories/polis-invitation-next/edit-v1 \
  --baseline data/workspace/hall-of-memories/polis-draft-v1
```

The audio preparation records hashes of the retained baseline's native movie,
PCM master, editable animation and timeline. Use `--baseline` if it is not in
the sibling `polis-draft-v1` directory. The renderer saves its source and timing
under `render/recipe/`; the finisher retains that exact snapshot. A resumed
render refuses a changed recipe or timeline, so use the retained recipe to
resume or a new render directory for a revision. These records permit a context
edit without modifying the accepted baseline.

The renderer supports `--stills`, `--start`, `--end` and `--bake-only`. The bake
writes `polis-invitation-animation.blend` with constant interpolation and a
relative sound link. New version directories are required for rerenders.
`polis_render.py --setup-only` exposes the existing set/puppets to this scene;
ordinary baseline render commands retain their previous behavior.
Use a Python environment with NumPy and Pillow. No provider calls are made.
Load the saved animation in background Blender with
`--python tools/hall-of-memories/polis_invitation_verify.py -- --run RUN --output REPORT`
to check its pose keys, sound link, speaker visibility and character separation.

## Complete polis scene draft

`polis_scene.json` contains the complete children-conversation draft requested
on 2026-09-26. `polis_audio.py` prepares local temporary voices, separate sound
stems, optional captions and the authoritative performance timing.
`polis_render.py` builds one Blender set and articulated rounded avatars, then
renders held poses and camera marks. `polis_finish.py` assembles native and
smaller review copies, a PCM master and a review page, and verifies the encodes.

```sh
python tools/hall-of-memories/polis_audio.py \
  --output data/workspace/hall-of-memories/polis-next

data/tools/blender-local/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup \
  --python tools/hall-of-memories/polis_render.py -- \
  --run data/workspace/hall-of-memories/polis-next \
  --output data/workspace/hall-of-memories/polis-next/render/frames \
  --height 1080 --samples 16

python tools/hall-of-memories/polis_finish.py \
  --run data/workspace/hall-of-memories/polis-next \
  --frames data/workspace/hall-of-memories/polis-next/render/frames \
  --output data/workspace/hall-of-memories/polis-next/edit-v1
```

Use a Python environment with NumPy. The audio recipe requires macOS `say` and
FFmpeg. The Blender recipe targets the installed Blender 4.5 API and Metal
Cycles renderer; `--engine eevee` is an optional faster look-study mode.
`--stills` renders six key views, while `--start` and `--end` allow frame-range
renders. Existing audio, rendered frames and edits are refused. All outputs
remain under ignored paths. These recipes make no image, video or voice
provider calls. Voices, dialogue additions, architecture, proportions and the
eight-pose cadence are draft choices, not new whole-film approvals.

Use `polis_render.py --bake-only` with a separate output directory to save an
editable `.blend` animation. It contains constant-interpolation pose keys,
editorial camera marks and a relative link to the retained draft sound mix.
The first draft's animation covers 957 frames at 24 fps.

## Factory photographic motion study

The subsequent factory test uses approved rounded dark-grey robots and
photographic plates. Its 18-second work-routine excerpt contains no robots;
a separate six-second frontal robot test supplies later-coverage performance.
Robots are absent at the chapter beginning, sparse until the last two thirds,
and increasingly present toward its end. Exact reveal time is still open.

```sh
python tools/hall-of-memories/factory_motion.py \
  --assets data/workspace/hall-of-memories/factory-motion-v1/assets \
  --output data/workspace/hall-of-memories/factory-motion-v1/edit-next
```

This recipe uses FFmpeg and NumPy, with generated stills and transparent layers
prepared separately through imagegen. It makes no provider calls. Its exact
16:9 native crop is 1664 × 936, with 720p review proxies, PCM audio masters,
separate locally synthesized sound stems and eight held poses per second within
24 fps. Existing output directories are refused. `factory_motion_plan.json`
records shot timing, pivots and performance limits. The wide is held; the lever
tests a rigid hand/forearm layer, and the robot tests a small planar head tilt.

The historical rough blocking recipe below remains separate and unchanged.

## First rough blocking package

The first review package is at
`data/workspace/hall-of-memories/auditions-v2/index.html`.
`auditions-v1` and `still-study-v1` are retained internal studies. None is approved.

Subsequent user direction requires photorealistic factory and Exchange passages,
in depressed-workplace and cinematic registers respectively. This recipe's paper
figures are blocking placeholders for those scenes, not their final style target.
See `briefs/hall_of_memories_auditions.md` for the clarification.

This small, film-specific recipe builds a twelve-panel whole-film board and three
transition auditions, including two ending placements with the same audio.
It uses locally drawn geometry, six held poses per second, twelve camera samples
per second, 24 fps output, installed macOS speech and original scratch synthesis.
The board deliberately omits detailed coverage and treats its 5:14 timing as a
hypothesis. It does not constitute a complete rough animatic.

```sh
# Use a Python environment with Pillow and NumPy installed.
python tools/hall-of-memories/build.py \
  --output data/workspace/hall-of-memories/auditions-next

# Fast local picture study without speech, synthesis or video encoding:
python tools/hall-of-memories/build.py \
  --output data/workspace/hall-of-memories/stills-next --stills-only
```

FFmpeg, ffprobe and macOS `say` must be installed. Default fonts are macOS Arial;
set `HALL_FONT` and `HALL_FONT_BOLD` for alternative installed font files. There
are no provider calls, uploads, downloads or paid QA steps. Existing output
directories are refused. A run retains a copy of the exact recipe, editable
dialogue and effects, cue times, board images, local ledger and file hashes.

- `plan.json`: broad beats, asset identities and scratch dialogue.
- `picture.py`: paper puppets, one persistent Hall, emerald and strata geometry.
- `sound.py`: local speech, separate wordless voices and shared mix gain.
- `build.py`: stills, native/proxy movies, review page and technical verification.

The Hall/facet cut is a conceptual coordinate change. It deliberately does not
model a physical tunnel from the simulation. The far cutaway is a legibility
study, not a scientifically scaled Earth model. Outside perception is unselected.
Geological time, the simulation clock and screen duration remain independent.

The source crowd is pixel-identical throughout its hold. Only the final fade
changes the image. A canonical PCM audio master retains exactly 12,000 silent
samples after the ending cutoff; the matching six video frames are black.
AAC review copies can ring around that boundary. Synthetic infant and scream
recognition, performance and emotional effect still need listening review.

Source review notes are in `briefs/hall_of_memories_auditions.md`. Paid chapter
scopes, ceilings, final assets, duration and finishing remain undecided.
