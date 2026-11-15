# POLISH local screen production

The exact interface, photographed-screen composites and synchronized phone cues
for the [POLISH brief](../../briefs/polish/brief.md). All commands are local;
provider requests and their creation snapshots belong in the ignored workspace.

Use the repository's provisioned media Python with Pillow, NumPy, OpenCV and
SciPy. Set `POLISH_FONT` to a local Helvetica-compatible font when the default
macOS font is unavailable.

```sh
python tools/polish/render.py data/workspace/polish-v1 --stills
python tools/polish/render.py data/workspace/polish-v1 --render renders/interface-v1.mp4
python tools/polish/hand.py data/workspace/polish-v1 SOURCE.mp4 --version=v2 --source-start-frame=18
python tools/polish/sound.py data/workspace/polish-v1 --version=v2
python tools/polish/held.py data/workspace/polish-v1 --stills
python tools/polish/held.py data/workspace/polish-v1 --render renders/held-v2.mp4
```

The interface is 912 frames at 24 fps. The hand composite replaces frames
720–755 with 36 consecutive source frames at normal speed. Exact source hashes,
voice trims, edit decisions, cue times and recipe copies are retained in the
workspace. The physical-screen corners are measured for the selected reference
plates; different plates require a new calibration and reviewed output version.

The held-phone revision uses `held.py` and retains the original renderer as its
exact conversation/timing source. It isolates the existing handset from the
tabletop, adds an oblique camera and grip movement, compacts the suggestion row,
and checks the projected keyboard bounds on every frame. It replaces the hand
insert with continuous held-phone coverage and keeps an angled pixel macro.
The prepared soundtrack and all original renders remain unchanged.

Import new local interface renders and 4K counterparts with the explicit derived
classification before their first analysis:

```sh
npm run clips -- import data/workspace/polish-v1/renders/held-v2.mp4 tools/polish/local-derived-metadata.json
```

Use a new workspace/version when revising a sealed film. The example names the
historical production path; do not import or rewrite an archived original.
Classifying the first import prevents finishing from changing the clip's
classification and invalidating its analysis identity. Existing analysis records
remain immutable. See the [closeout and recovery notes](../../briefs/polish/closeout.md).

Movie and mix output versions refuse replacement. Stills are working look
previews; retain reviewed versions before changing them. Generate final delivery
through the maintained `film assemble` and `film review` commands, including the
project clip-analysis checkpoint. Still inspection, technical verification,
listening and director approval remain separate.
