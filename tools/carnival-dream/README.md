# Carnival Dream: Borrowed Light

A deterministic local paper-miniature music-video recipe. Blender builds one
performer, a flat projected partner, theatre scenery, a rotating lantern, and
three monochrome rides. The characters and props retain their geometry across
shots. Eight poses per second are held on a 24 fps delivery timeline.

The song and all media remain local under ignored `data/`. The original music
file must not be moved or modified. Copy it to the run's `assets/song.mp3`,
record its SHA-256, and copy `film.json` to the run as `timeline.json` before
rendering. The timeline uses the full decoded song duration; cuts round to
24 fps. Its final picture hold extends about 11 ms beyond the last song sample.
There is no music retiming, normalization, added sound, or generated audio.

## Build

Use Blender 4.5 LTS, FFmpeg, and Python with Pillow and NumPy. The renderer,
finisher, assembly and review scripts are local. The explicitly named generation
and QA runners use the repository's existing providers with spend preflight. Set
`BLENDER_BIN` to the installed Blender executable and `CARNIVAL_RUN` to a fresh
ignored run directory. The validated first draft uses EEVEE, 32 samples, native
1920x1080, with no upscale.

```sh
"$BLENDER_BIN" --background --factory-startup \
  --python tools/carnival-dream/render.py -- \
  --run "$CARNIVAL_RUN" --output "$CARNIVAL_RUN/stills" \
  --engine eevee --samples 32 --height 720 --stills

python tools/carnival-dream/finish.py \
  --run "$CARNIVAL_RUN" --stills "$CARNIVAL_RUN/stills" --blockout

"$BLENDER_BIN" --background --factory-startup \
  --python tools/carnival-dream/render.py -- \
  --run "$CARNIVAL_RUN" --output "$CARNIVAL_RUN/frames" \
  --engine eevee --samples 32 --height 1080

python tools/carnival-dream/finish.py \
  --run "$CARNIVAL_RUN" --stills "$CARNIVAL_RUN/stills" \
  --frames "$CARNIVAL_RUN/frames"
```

`--revision 1`, `2`, or `3` selects the successive whole-film recipes.
`--frame N` renders one frame; `--frame-list N ...` renders anchors;
`--start N --end N` renders a bounded range.
Frame directories resume without replacing existing frames. A recipe change
requires a new frame directory. Held frames use hard links to limit storage.
Rendering stops before exhausting a 5 GiB free-space reserve. The `.blend` file
contains the constructed assets at the opening pose; the Python recipe and
timeline are the authoritative animation, rather than baked keyframes.
Each full render captures those source files under its own `recipe/`. Use that
captured renderer and sibling refinements when reproducing an older draft:
the current source may have advanced to the next revision.
Disjoint render ranges may share a frame directory: start the capturing process
first, then pass `--worker` to subsequent ranges. Workers verify their source
matches the captured recipe and do not rewrite it. Split at a shot boundary and
wait for every expected frame, rather than only the final numbered frame.

The finisher refuses a non-native frame size or a missing frame. It checks the
stream count, raster, frame count, duration, complete decode, unchanged source
copy, and full-song plus windowed AAC correlation at zero offset. The original
decoded song is also preserved as a PCM WAV. `--verify-only` rechecks an existing
export without re-encoding it.

Local review uses the existing range-capable server:

```sh
python tools/hall-of-memories/serve_review.py \
  --root "$CARNIVAL_RUN/review" --port 8876
```

Open `http://127.0.0.1:8876/`. The server's legacy console message may mention
an extra `edit-v1` segment; this run is served at the root URL above.

## Creative review

Each draft's $30 production allowance is a ceiling, not a spending target. This first
draft uses local animation throughout and makes no production API calls. The
separate Whisper analysis predates this production run.

Review the duet's emotional clarity, the contrast between color and monochrome,
the legibility of the three defects, and the meaning of the final deliberate
return. Numerical QA does not establish artistic approval. Preserve the first
draft and make revisions in a new directory. Publication, source push, and 4K
finishing are separate actions and are not performed by this recipe.

## Generated accents and comparison

Drafts 2 and 3 each reserve two four-second performance accents. The existing
Vertex client generates directly on Veo Quality at native 1080p, using reviewed
first/last local anchors. `qa_runner.py` wraps the repository's frame, drift,
clip and clone checks with draft-specific budget reservations and token receipts.
`generate_accents.mjs` refuses a changed anchor or prompt, an unreviewed anchor
pair, or a duplicate submission. Failed or questionable clips require a recorded
decision; the scripts never retry paid generation automatically.

`assemble_accents.py` builds a fresh sequence from local hard links and explicitly
accepted clips. It checks native dimensions, discards all provider audio, samples
eight poses per second and holds them at 24 fps. Original renders and provider
files remain intact. `reconcile_budget.py` sums usage estimates, retaining full
reservations for uncertain calls. The $30 limits are separate per draft.
The assembly also supports reviewed local shot corrections through
`qa/local-patches.json`; each correction has its own captured recipe and native
frames. Draft 3 uses this for the backstage turn and continuous final reaches,
discovered during native motion review. Apply it before generated accents; never overwrite the
base render to hide the correction's provenance.

Once all three native exports and technical reports exist, run:

```sh
python tools/carnival-dream/build_comparison.py
python tools/hall-of-memories/serve_review.py \
  --root data/workspace/carnival-dream --port 8877
```

The comparison is at `http://127.0.0.1:8877/review/`. Switching drafts retains the
song playhead; each complete file also has a download link. The page defaults
to Draft 3. This is local review, not publication.
