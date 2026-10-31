# Motion

The source brief and decisions live in `briefs/motion/`. The production uses stable ID `motion`; its public record locates the active or
archived workspace. Media, detailed receipts and accounting stay private.

Use the provisioned Python environment containing Pillow, NumPy, SciPy and OpenCV.
`audition.py` makes the still gallery. `finish.py` reads a private source selection
and the integer-frame beats, authors separate sound stems, and renders the four
camera files. It samples source timestamps at fifteen frames per second, applies
the monochrome camera treatment and clock, compresses the camera image, and repeats
each frame twice in the portrait master. Compose the odd vertical placement in RGB
**after scaling**; a YUV padding filter otherwise rounds it down by one pixel.
Five black pixels inside the horizontal edges contain codec ringing.

```sh
python tools/motion/finish.py data/workspace/motion-v1 \
  --selection data/workspace/motion-v1/edit/selection-v1.json --version NEW_RENDER
node tools/motion/assemble.mjs data/workspace/motion-v1 NEW_RENDER NEW_DRAFT
python tools/motion/verify.py data/workspace/motion-v1 NEW_DRAFT
```

Review the new local clips and create source-hash acceptance records before
assembly. The assembler imports the retained local sources, copies their encoded
picture into the frame-addressed cut, adds the authored soundtrack, and writes a
delivery receipt and timeline. Existing versions are never overwritten.

The verification script inspects decoded pixels, cadence and audio. It distinguishes
the exactly silent PCM gaps from AAC overlap at their edges. Source inspection,
technical checks, real-time listening and director approval remain separate.

After importing a batch, run the repository's project analysis checkpoint and
project-scoped private backup. Build the standard status page from
`briefs/motion/status.json`; its draft timeline comes from the delivery manifest.
Serve the native review directory with `tools/production/review-server.mjs` so
frame and scene seeking use HTTP byte ranges. The current workspace handoff records
the selected version and local URLs.

The director's approved trims and UHD finish are reproduced with `revise.py`:

```sh
python tools/motion/revise.py data/workspace/motion-v1 native
python tools/motion/verify.py data/workspace/motion-v1 draft-v4
python tools/motion/revise.py data/workspace/motion-v1 4k
python tools/motion/verify.py data/workspace/motion-v1 4k-v1
node tools/motion/register-finish.mjs data/workspace/motion-v1
```

These commands refuse to replace an existing delivery. The trim recipe removes
exact source frame ranges and the corresponding PCM samples. Explicit frame color
parameters and H.264 color metadata preserve BT.709 through encoding. AAC noise
synthesis is disabled to keep the mono sound identical in both channels. The UHD
pass enlarges with Lanczos, preserves the black matte and copies the native audio.

The 4K stage requires a matching successful native verification report before it
creates output. The delivered recipe is retained privately for historical recovery.
