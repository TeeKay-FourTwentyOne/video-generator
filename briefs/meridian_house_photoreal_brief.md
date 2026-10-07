# Meridian House — cohesive photorealistic reference study

Date: 2026-09-13. Status: **eight selected stills complete; local rotation preview
complete.** Projection remains a diagnostic study, not a finished new tour.

The user requested repeating the Nano Banana image exercise with a cohesive,
photorealistic mansion. The existing completed tour and its source assets are
preserved. This pass covers images and local projection previews; it does not
request Veo footage or publish anything.

## Visual direction

Photograph the same full-scale house during one midnight session: mineral-jade
plaster, ivory limestone, satin aged brass, walnut, dusty-rose velvet, restrained
green/ivory stone flooring and deep blue library walls. Warm existing practical
lamps balance cool light through the existing glazing. Preserve the model's
architecture, camera, object inventory and occlusions; add real surface texture
and plausible shading. No people or new furnishings.

The first selected image establishes the material and lighting reference.
The early full-scene style references caused later requests to borrow the wrong
camera composition. The selected workflow instead supplies each view's geometry
and object-boundary images with a board of cropped plaster, stone, brass, floor,
velvet and walnut samples from the selected photographs. This preserves the
shared finish without supplying a competing room composition. Explicit per-view
inventory and placement instructions reinforce the target camera.

## Recipe and retained inputs

Source tool: `tools/scene-lab/photoreal-frames.mjs`.
Local workspace: `data/workspace/meridian-house/photoreal-v1/`.

Eight original rotation cameras, spaced 45 degrees apart, retain scene
`meridian-house-v1` and geometry hash `27e11313`. Their local source images and
camera metadata are copied into the new workspace. This samples the atrium and
the room views available through its arches; it is not full interior coverage
of the library and conservatory.

Generation uses the existing Google Vertex AI Nano Banana Pro integration,
`gemini-3-pro-image`, 2K, 16:9, temperature 0.35. Each request is recorded before
submission. Selected reference hashes are verified; existing takes are never
overwritten or automatically resubmitted. The run allows up to 16 requests
within a $12 image reserve, including targeted corrections and rejected trials.
Generated images are locally normalized to
2048 × 1152 without cropping; original outputs are retained.

There were 16 recorded requests: 15 returned images and one provider call failed
without an image. The final selected takes for angles 0 through 315 degrees are
1, 3, 3, 2, 1, 1, 3, 2. All source and rejected images are retained. Cropped
material references corrected major camera borrowing; localized edits corrected
an invented library window and material drift. Small lighting, lamp finish and
contour differences remain between independently generated views.

```sh
# Local preparation; choose a new workspace for a new experiment.
node tools/scene-lab/photoreal-frames.mjs prepare --output=data/workspace/meridian-house/photoreal-next

# Paid request; only within the authorized, pre-reserved project budget.
node tools/scene-lab/photoreal-frames.mjs generate --output=data/workspace/meridian-house/photoreal-next --index=0
```

The initial full-image reference mode requires local `reviews/anchor-NN.json`
records with `verdict: selected`, a relative image path and its SHA-256. In the
selected material-sample mode, the plan instead records `styleReferenceMode:
material-swatches` and a hash of `material-swatches.png`. Final selections still
require direct visual comparison with the original camera image. Selection is
not a claim of exact geometry preservation. Correction takes require a saved
targeted correction prompt. An optional `prompts/anchor-NN-take-T.edit-source.txt`
selects a retained normalized photograph for a localized edit, helping preserve
otherwise successful appearance. Runtime prompts, decisions and request metadata stay
in the ignored workspace. A new run requires its own matching `RESERVE run-name:`
ledger entry; a later run cannot reuse this run's reserved allowance.

## Budget

The previous conservative project allocation was $25.40. An initial $8 image
reserve plus a $4 correction allowance brings it to $37.40 under the existing
$49 operational ceiling. Retain
the prior image and infrastructure reserves until billing is reconciled. These
figures are allocations, not actual Google charges.

On the checked [Google pricing page](https://cloud.google.com/vertex-ai/generative-ai/pricing),
standard global 2K image output is 1,120 tokens at $120 per million: $0.1344 per
image, excluding input and reasoning/text tokens. Actual billing is not reported by the existing
Nano Banana helper, so the broader reserve remains in place.
The 15 returned images have a $2.016 image-output-only subtotal. This is not a
total charge; inputs, reasoning/text and the failed call remain unreconciled.

## Deliverables and verification

All outputs are under `data/workspace/meridian-house/photoreal-v1/`:

- `index.html`: local gallery with a toggle between photographs and 3D references.
- `contact-sheet.png`: the eight selected photographs, labeled by camera angle.
- `selected/`: eight 2048 × 1152 PNGs; original 2752 × 1536 outputs stay in `raw/`.
- `projections-reviewed.json`: selected image/camera pairs for the scene renderer.
- `rotation-preview/16x9/sweep.mp4`: silent 1080p, 24 seconds, two revolutions,
  24 fps with six distinct locally rendered views per second.
- `material-bible.txt`, `prompts/`, `prompts-selected.json`: exact prompt records.
- `material-swatches.png` and its recipe: the shared cropped material reference.
- `review.json`, `reviews/`, `requests/` and `qa-*`: local review and provenance.

All 72 matching frame pairs across the two local revolutions are identical.
The renderer's self-projection test passes with WebGL error zero. These checks
establish deterministic rendering, not consistency of generated image content.
The gallery loads all eight images and toggles to and from the source model
correctly. All 13 scene-lab tests passed. The new runner's refusal of duplicate
takes, existing output directories and invalid view indices was checked locally.

Visual inspection covered the selected stills against their geometry inputs,
the contact sheet, and eight intermediate projected rotation views. The rotation
shows some doubled thin edges, light/material transitions and uncovered strips
at image borders. Keep these visible as diagnostics. No new Veo requests were
made and no source commits or publication were requested.

Tests with all eight selected projectors include a 0.3 m sideways camera move
and entry into the library. The sideways view retains the main photographic
appearance with thin-edge/visibility artifacts. Library entry reveals substantial
uncovered original materials and stretched desk/ceiling detail. Additional
interior references are needed before producing a new tour; this completes the
eight-angle rotation image exercise rather than full interior texture coverage.

The existing 4K tour's SHA-256 was rechecked and is unchanged. The new local
preview passes a full FFmpeg decode. Media, request records and the gallery stay
in the ignored workspace; the reusable runner and this brief are uncommitted.

## Review limitations

Photorealistic still-image quality and calibrated projection accuracy are
different checks. A realistic image can move fine edges, cast highlights onto
the wrong modeled surfaces, or reveal uncovered areas after camera translation.
Inspect overlapping views and a short translated camera test before using these
projections as anchors for a new tour. No geometry repair or UV texture bake is
claimed by this image study.
