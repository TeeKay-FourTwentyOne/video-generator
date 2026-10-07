# Meridian House — documentary photographic study

The user requested a stronger photographic treatment after reviewing the first
photoreal study: documentary style, with no cinematic presentation. This run
interprets the existing mansion as an actual building photographed in ordinary
overcast daylight. The same eight original 3D camera views provide the layout.

## Visual direction

- Neutral available daylight; existing opal-glass lamps and orrery globe unlit.
  Existing windows show pale overcast sky in place of the stylized giant moon.
- Muted gray-green plaster, off-white limestone, tarnished brass, walnut,
  dusty-rose upholstery and slate-blue library walls. Restrained wear and actual
  construction details, without staged decay or decorative additions.
- Natural rubber-plant leaves and plausible upholstery/joinery may depart from
  the blockout's simplified microgeometry. Preserve architecture, viewpoints,
  broad object placement and inventory. This is a photographic interpretation;
  exact projection registration is not an acceptance requirement.
- No theatrical lighting, cinematic grading, bloom, fog, HDR polish or added props.

## Scope and budget

Eight 16:9 still images, Nano Banana Pro through the existing Google integration,
2K request size. No video duration or new Veo generation in this pass. Preserve
the original tour and `photoreal-v1` unchanged. No publication or source commit.

Reserve $11 for at most 20 image requests, including deliberate corrections.
The initial $8 / 10-request plan was revised after inspecting provider
rate-limit failures and side views with invented windows or inconsistent details.
Photograph-only references are used for the final local corrections to avoid
copying crude blockout materials back into the photographs.
Previous conservative project allocation: $37.40. New allocation: $48.40 of the
existing $49 operational ceiling, leaving $0.60. Reserves are not actual billed
charges. Do not release prior reserves or retry automatically.

## Reproduction and review

```sh
node tools/scene-lab/photoreal-frames.mjs prepare \
  --output=data/workspace/meridian-house/NEW_DOCUMENTARY_RUN --look=documentary
# Record a matching RESERVE tag in the project ledger before any submission.
node tools/scene-lab/photoreal-frames.mjs generate \
  --output=data/workspace/meridian-house/NEW_DOCUMENTARY_RUN --index=0 --take=1
```

The run directory must be a new lowercase slug directly inside the Meridian
House workspace. Inspect the first output against its original layout and the
previous study, then use isolated material crops to guide subsequent angles
without copying a complete competing composition. Inspect all returned images
and retain attempts, prompts, failures and selection decisions locally.

Workspace: `data/workspace/meridian-house/documentary-v1/`. Generation and review
status, selected images, comparisons and limitations are recorded there.

Completed with eight selected 2048 x 1152 images. There were 20 recorded requests:
16 returned images and four rate-limit failures with no image. The gallery includes
the earlier study and original model comparisons. Image loading, comparison
controls, source hashes, duplicate-take protection and the 20-request stop were
checked locally. Generation is stopped; no video was generated for this pass.

The resulting stills establish a more natural photographic treatment. They retain
differences in framing, plants, furniture details, glazing, trim and tile treatment;
one library-side view retains a narrow bright edge remnant after a rate-limit
failure. They require continuity reconciliation before use in a moving-camera tour.
