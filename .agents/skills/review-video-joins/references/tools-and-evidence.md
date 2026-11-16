# Local tools and evidence

Run from the repository root. Use
`data/tools/clip-analysis/semantic-v1/python/bin/python` for NumPy, Pillow and
OpenCV; system Python may lack them. Keep media and receipts in ignored data.

## Exact boundary extraction

Enumerate cuts from edit recipes, including composite internals. For a cut at
edit frame 142, extract the actual adjacent frames 141 and 142:

```sh
ffmpeg -v error -n -i data/workspace/my-film-v1/final/v1/film.mp4 \
  -vf 'select=between(n\,141\,142)' -fps_mode passthrough \
  data/workspace/my-film-v1/qa/joins-v1/pair-%02d.png
```

Create a new evidence directory first. Expand the interval for dense strips and
normal-speed windows; preserve the actual frame rate, including rational rates.
`tools/cut-pair-inspector.cjs` locates possible cuts, but its default ±0.05-second
offsets are not adjacent frames and it can overwrite outputs. Use exact indices
for decisions. Scene detection can miss subtle joins or flag lighting changes.

For stream-copy concatenation, do not infer timing from rounded MP4 durations.
The maintained assembler/finisher writes explicit durations from cumulative
frame boundaries. Custom muxes need the same care: compare every output video
timestamp with the intended timeline, not just the total frame count. Rounding
each segment separately can itself accumulate error across many cuts.

## Rank bounded source handles

`../scripts/rank_pairs.py` verifies source hashes, decodes integer-frame ranges,
preserves aspect ratio and ranks weighted grayscale differences. It saves a
labeled shortlist without editing the movie or declaring a match acceptable.
It does not infer speech, movement direction, identity or optical flow.

Inputs are workspace-relative. Prefer native sources. If using `clips extract`
to materialize a range, retain the original clip ID and source offset as well
as the derivative's hash. A byte-for-byte copy of a resolved library source into
the QA directory is another option. Ranges are end-exclusive:

```json
{
  "from": {"path": "clips/A.mp4", "sha256": "FULL_SHA256", "startFrame": 80, "endFrameExclusive": 96},
  "to": {"path": "clips/B.mp4", "sha256": "FULL_SHA256", "startFrame": 0, "endFrameExclusive": 18},
  "proxyWidth": 270, "top": 6, "separation": 7,
  "regions": [
    {"box": [0.15, 0.15, 0.85, 0.65], "weight": 1},
    {"box": [0.28, 0.30, 0.72, 0.38], "weight": 3}
  ]
}
```

Boxes are normalized `[left, top, right, bottom]`; overlapping weights add.
Omit regions for equal frame weighting. Author boxes for the current framing;
these are illustrative. On REPEAT, weighting eyes/mouth/shoulders prevented the
large static wall from overwhelming subject changes. Keep exposure differences
visible rather than normalizing away an actual lighting jump.

```sh
data/tools/clip-analysis/semantic-v1/python/bin/python \
  .agents/skills/review-video-joins/scripts/rank_pairs.py \
  data/workspace/my-film-v1 recipes/join-search.json qa/joins-v1/search-01
```

Search narrow clean handles. Each window is capped at 240 frames. The helper
requires matching source raster; prepare explicit aligned derivatives if needed.
It makes no automatic crop, alignment or retiming choice.

## Movement checks

For a continuation intended to read as one shot:

```sh
data/tools/clip-analysis/semantic-v1/python/bin/python tools/seam-check.py \
  --pair data/workspace/my-film-v1/clips/A.mp4:95 \
  data/workspace/my-film-v1/clips/B.mp4:4 --json
```

Indices are last included A and first included B. Photometric change and motion
energy are separate channels. Thresholds are empirical, not universal perceptual
truth; near-static footage and prominent faces need direct scrutiny. Do not
apply continuous-motion expectations to intentional editorial cuts.
`tools/scene-lab/seam-search.mjs` has fixed landscape proxy geometry and 24-fps
labels: its project-specific main is not a general command for other films.

## Optional optical-flow bridge

The exercised renderer is `tools/repeat/smooth_join.py`. It packs intermediate
frames into a separate silent source and records recipe, tool and endpoint
hashes. It currently assumes **1080 × 1920**, with flow computed at **540 × 960**.
Use it unchanged only for that raster. For other dimensions, adapt a versioned
local tool/recipe and independently scale flow X/Y back to output resolution.
Verify the adaptation; do not stretch landscape footage into the portrait tool
or replace the historical implementation underneath its receipts.

It calculates forward/backward dense flow, warps both endpoints toward each
intermediate time, then blends. Times are `(j+1)/(N+1)` so endpoints are not
repeated. The outgoing segment ends on `from.frame`, the incoming begins on
`to.frame`, and N bridge frames sit between them. Account for N explicitly in
the timeline. Inspect every bridge frame plus surrounding motion; a smaller
pixel-difference peak can conceal distorted anatomy or wrong acceleration.

## Private decision record

Retain these facts in `qa/joins-VERSION/` (editorial evidence, not a new core
edit schema): join ID and intent; base edit hash; source hashes; old/new edit
and source indices; chosen treatment and reason; protected dialogue/action;
dense strip and normal-speed clip; metrics with method and proxy dimensions;
remaining defects; actual playback/listening and director-review state.
Use `pending` when a review has not occurred. Extracted frames or a successful
HTTP response do not establish that the movie was watched.
