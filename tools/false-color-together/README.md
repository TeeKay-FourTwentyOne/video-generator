# Together

Deterministic companion to *False Color — Green*. Read the
[creative brief](../../briefs/false-color-together/brief.md).

The renderer uses Pillow and NumPy from the existing local media environment.
It draws antialiased circles, exact straight-line Tusi trajectories, captions and
the reveal guides. It writes an immutable local source, mathematical checks,
source frames and a creation receipt with recipe and font hashes.

```sh
data/tools/clip-analysis/semantic-v1/python/bin/python tools/false-color-together/render.py data/workspace/false-color-together-v1 --stills
data/tools/clip-analysis/semantic-v1/python/bin/python tools/false-color-together/render.py data/workspace/false-color-together-v1 --render
```

`--preview` writes a 540 × 960 motion proof. `--render` writes the 1080 × 1920,
60 fps source. Neither flag overwrites an existing file. The score uses the
maintained local synthesizer and the project cue sheet. All intermediates and
media stay in ignored storage. Rendering a new edit requires a new source name
or workspace; preserve earlier renders.

```sh
python3 tools/false-color-together/score.py data/workspace/false-color-together-v1
node tools/production/score.mjs data/workspace/false-color-together-v1/audio/cues-v1.json data/workspace/false-color-together-v1/audio/score-v1.wav
node tools/production/mix.mjs data/workspace/false-color-together-v1 audio/mix-v1.json audio/mix-master-v1.wav --report=qa/mix-v1.json
npm run clips -- import data/workspace/false-color-together-v1/render/picture-v1.mp4 data/workspace/false-color-together-v1/edit/import-metadata.json
npm run clips -- analysis process-project false-color-together
npm run clips -- analysis process-project false-color-together --check
node tools/false-color-together/assemble.mjs data/workspace/false-color-together-v1 v1
```

The shared editor presently accepts 24, 25 and 30 fps. This production uses its
own small assembler to preserve the original 60 fps motion. It still requires the
maintained clip-analysis checkpoint, records catalog uses, verifies all decoded
picture bytes are unchanged by muxing, and produces a native frame-stepping
review package. The sound mixer uses a 30 fps timing grid for one precomposed
38-second WAV; this leaves the picture's 60 fps clock unchanged.

The delivery explicitly sets H.264 colour metadata because the local encoder
does not retain all requested transfer/primaries tags. The source is kept intact.
No change to the shared production editor is needed for this film.

## Authorized 4K finish

The 4K adapter loads the preserved native recipe by its creation-time hash and
scales only its raster canvas, drawing primitives and fonts. It compares the
new frames with the native images and repeats target equality checks at 4K.

```sh
data/tools/clip-analysis/semantic-v1/python/bin/python tools/false-color-together/render4k.py data/workspace/false-color-together-v1 --render
npm run clips -- import data/workspace/false-color-together-v1/render/picture-4k-v1.mp4 data/workspace/false-color-together-v1/edit/4k-import-metadata.json
npm run clips -- analysis process-project false-color-together
npm run clips -- analysis process-project false-color-together --check
node tools/false-color-together/finish4k.mjs data/workspace/false-color-together-v1
npm run clips -- analysis process-project false-color-together
npm run clips -- analysis process-project false-color-together --check
```

The film-specific 60 fps finisher verifies the authorized base hash, contiguous
frame ranges, decoded picture identity, and both AAC packet and decoded PCM
audio identity. It records counterpart uses and imports the finished master.
All native files remain unchanged. Publication text accompanies the master.

## Archived production

The production is closed out. The paths above describe the original working
copy; future work starts from a restored copy of the verified archive. The archive
retains both picture sources, the original score, cue/mix recipes and provenance.
Standard retention removes the native review MP4 and derived complete WAV mixes
from the archive, while keeping their metadata.

The 4K finisher checks the exact native base hash. Restore that base from its
recorded clip ID before reusing the historical finisher. Reconstruct complete
WAV mixes from the retained score and mix recipe if needed. Keep existing final
outputs and QA separate in the restored copy; these recipes refuse overwrites.
Repository tools, FFmpeg, Pillow/NumPy and the creation-hash-matched system font
remain dependencies. A byte-identical rebuild has not been qualified.
