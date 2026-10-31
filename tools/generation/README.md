# GENERATION local finish

The production spine and decisions are in [the brief](../../briefs/generation/brief.md)
and [decisions](../../briefs/generation/decisions.md). The writer is Claude Fable 5.1.

`render.py` reads `edit/render.json` in a named workspace. The recipe contains the
single integer-frame timeline, selected source paths, source windows and dub
constants. It uses the provisioned Pillow, NumPy, SciPy and OpenCV environment,
and local FFmpeg. It makes no provider calls.

Run `video`, `graphics`, then `audio`, then `assemble --version v1`. Existing
intermediate stages are reused; a final version cannot be overwritten. Move a
superseded calibration into a distinct retained directory before changing its
recipe. Keep the matching recipe and hashes with each candidate.

The picture pipeline registers the background, crops to 4:3, applies the camera
base once and performs the requested number of literal lossy dub passes. Fine
playback noise follows those passes, and clean PLAY lettering follows the noise.
The empty-yard copy bypasses both dubbing and playback noise. Portrait encoding
protects the black margins at the odd chroma boundary.

`verify.py WORKSPACE --version v1` decodes every frame and checks the dimensions,
frame count, black margins, PLAY timing, blue color tolerance, PCM silence and
dual-mono channels. FFmpeg true-peak measurement is retained separately. These
are technical checks; phone viewing and real-time listening remain separate.

Local inputs must be imported into the clip library with the project collection.
Retain generation snapshots for provider sources and input hashes for derived
sources. Run the maintained project analysis checkpoint and project-scoped private
backup before native delivery. The review manifest records clip IDs, source
ranges, hashes and editorial decisions; the maintained review server supports
byte-range seeking.

After director approval, `finish.py WORKSPACE` creates `final/4k-v1/film.mp4`
at 2160 by 3840 using a bilinear 2x enlargement. It copies the approved AAC
stream and verifies every audio packet and timestamp. Run
`verify.py WORKSPACE --version 4k-v1 --scale 2` for the final raster, margin,
color-tag and timing checks. The enlargement deliberately retains the tape noise.

https://github.com/TeeKay-FourTwentyOne/video-generator
