# Scary Woods archive finishing

The compact Episode 01 archive lives locally at
`data/workspace-archive/forest-spirit/`. Generated assets and runtime records are
excluded from source control. The public [episode brief](../../briefs/forest_spirit_episode_01_brief.md)
records the released film and its production method.

```sh
python3 tools/forest-spirit/finish.py data/workspace-archive/forest-spirit
python3 tools/forest-spirit/finish.py data/workspace-archive/forest-spirit \
  --mode rebuild-1080 --output data/exports/scary-woods-rebuilt-1080.mp4
data/tools/upscale-venv/bin/python tools/forest-spirit/finish.py \
  data/workspace-archive/forest-spirit --mode upscale-4k \
  --output data/exports/scary-woods-rebuilt-4k.mp4
```

Verification hashes every retained file. Rendering refuses existing destinations
and outputs inside the archive. The 4K route uses the exact approved captioned
1080p input and checks the installed model against the retained weights before
calling the archived version of `tools/upscale.py`. Use the documented local
Python environment with `realesrgan-ncnn-py==2.0.0` and its dependencies.

The editable 1080p route combines the clean picture, retained transparent caption
panels and approved AAC audio. It preserves the edit, captions and audio timing,
but re-encodes the picture and is not promised to be byte-identical to the approved
master. The archive also contains PCM stems and individual dialogue clips for
future changes. Original generated images, masks, sprites and historical recipes
support further visual work; old frame caches and intermediate edits are absent.

`captions.swift` regenerates the material-styled transparent panels on macOS using
AppKit and the fonts named in the archive cue configuration. Saved panel PNGs
remove that font dependency when rebuilding the existing cut.

```sh
mkdir -p data/exports/scary-woods-caption-panels
swift tools/forest-spirit/captions.swift \
  data/workspace-archive/forest-spirit/sources/captions/cues.json \
  data/exports/scary-woods-caption-panels
```

The pilot uses composited 2D imagery and discrete poses. It does not include a
complete 3D puppet rig. Future episodes should preserve the accepted silhouettes,
materials, voices, caption treatments and camera geography described in the brief.
