# EVERY WAY HOME — dependency inventory (closeout 2026-11-04)

Self-contained in this workspace: the twelve Veo takes (`clips/S1a-e-v1.mp4`, `T-v1.mp4`, `H-v1.mp4` (rejected), `S2a-e-v1.mp4`,
copies of the library masters), the Nano Banana plate and anchors (`refs/P0.png`, `A-raw.png`, `B-raw.png`, `B2-raw.png`) and their
plate-pinned 1080x1920 versions (`refs/P0-1080.png`, `A.png`, `B.png`, `B2.png`, with `.json` provenance), the prompts, the composites
(`clips/M1-ghost-a50.mp4` simultaneous reference, `clips/M1-v1.mp4` movement one, `clips/FILM-v2.mp4` the whole film, `clips/FILM-v2-4k.mp4`
its 2x counterpart, each with a `.json` recipe/source-hash sidecar and `M1-v1.mp4.plate.png` the median plate), the layer and mix specs
(`edit/layers-v2.json`, `edit/mix-v*.json`, `edit/v1-3.json`, `edit/finish-v3.json`), the QA decisions (`qa/`), the recipes and the 4K
master with its delivery and description copies (`final/v3-4k/`).

Requires the repository: `tools/production/mix.mjs`, `film assemble`/`review`/`finish`, `tools/upscale.py`, the status-page and records
tooling. Requires the machine: FFmpeg 8 with libx264, Python 3 with NumPy, SciPy and Pillow; `realesrgan_ncnn_py` only to regenerate the
retained 4K counterpart.

All recipe paths are workspace-relative. Run them from a restored copy, never inside the sealed archive.

Rebuild order after the standard retention (native edits v1-v3 and the complete mixes are removed; the master and both composites stay):
1. `python3 recipes/layers.py edit/layers-v2.json clips/FILM-v2.mp4` (about 20 min; or keep the retained one)
2. `node tools/production/mix.mjs <ws> edit/mix-v3.json edit/soundtrack-v3.wav --report=...` then update `edit/v3.json` audio sha256
3. `npm run film -- assemble <ws> v3` (new version name in a new workspace) and `finish <ws> v3 v3-4k --sources=edit/finish-v3.json`
A byte-identical rebuild of the master has not been tested; the retained master is the reference.
