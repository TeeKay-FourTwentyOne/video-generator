# REPEAT local edit

These tools prepare the picture and soundtrack for the maintained production
assembler. They perform no generation or network calls. The private workspace
holds the frame recipes, original references, provider snapshots and receipts.

- `render_ui.py` draws the approved white voice-setup panel. The preview uses an
  illustrative waveform; `compose.py` replaces it with measured soundtrack RMS.
- `sound.py WORKSPACE RECIPE OUTPUT.wav` selects native voice samples by integer
  frame, processes the first two playbacks and leaves the third playback clean.
  Its receipt records both input and prepared PCM hashes for every occurrence.
  Use `tools/production/mix.mjs` afterward for measured loudness and peak control.
- `compose.py WORKSPACE RECIPE OUTPUT.mp4` cuts the native-speed source ranges
  and adds the sound-driven interface. Recipe and output paths are relative to
  the workspace. Sources may be library clip IDs or workspace-relative paths,
  with explicit hashes. Black segments omit the source. No frames are held,
  repeated or retimed. The source ranges and hashes are retained in a receipt.
  An optional integer-pixel crop keeps the portrait aspect ratio and removes
  temporary framing cues before the final scale.
- `append_stinger.py sound|join WORKSPACE RECIPE` copies the existing mastered
  voice sample into a new tail and places local contact sounds at the inspected
  impact frames. It preserves the main mix without remastering and joins the
  picture by copying compressed video. Verification compares every decoded main
  frame and every prepared main audio sample with the base.
- `smooth_join.py WORKSPACE RECIPE OUTPUT.mp4` creates short optical-flow
  bridges between explicitly chosen source frames. Each intermediate frame is
  a bidirectional warp and blend, recorded separately from the native takes.
  Place these only in reviewed silent gaps, inspect every bridge frame, and
  preserve the native picture frames where dialogue is spoken. The join pass
  copies the existing soundtrack and stinger rather than regenerating them.

Use the repository's provisioned analysis Python for NumPy and Pillow. All
outputs refuse overwriting. Import the local composite through `clips import`,
record the underlying picture and audio uses, process the project clips, then
use the maintained edit validation and `film review` with source-specific
acceptance decisions. Fresh cuts can use `film assemble`; an append uses
`append_stinger.py join` to preserve the existing picture without re-encoding it.

The first native draft ends at the initial cut to black. The stinger extends it
in a separate version; the main sequence's later smoothing pass is independent.
Source-word checks, PCM identity and loudness measurements do not establish
listening or artistic approval.
