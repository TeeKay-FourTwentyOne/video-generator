# Scary Woods — Episode 01

**Published YouTube Short:** https://youtube.com/shorts/dsMDFQvEOew

Publication URL supplied with the release record on 2026-09-15.
Final delivery: **2160 × 3840, 9:16, 24 fps, 912 frames, 38 seconds**, H.264 with
48 kHz stereo AAC and eleven character-styled captions.

## Story and final edit

Wood, Clay and Paper are lost in a tangled forest. A snapped twig sends them
looking for safety at a warmly lit cabin. Spirit welcomes them and offers a
closer look into a crystal ball. The travelers' differing definitions of “close”
provide the final joke before the picture enters the glass and a story begins.

The opening walk lasts two seconds at its original speed. A wolf howl begins
almost immediately and fades beneath Paper's first question. Clay snaps a twig
at 6.75 seconds; the broken stick remains visible in the following wide views.
A half-second dissolve at 9.25–9.75 seconds softens the cabin reveal. The run
begins at 13.5 seconds, with another distant wolf and footsteps.

Luke is the final voice for Wood. All approved performances, music, effects and
caption timing are retained in the 4K delivery. Spirit's closing line is
“There was once a ship...” See the [final dialogue and shot guide](forest_spirit_episode_01_dialogue_shot_guide_v1.md).

## Finishing and verification

The local Real-ESRGAN `realesr-animevideov3-x2` model enlarged the approved
1080p edit by 2×. Encoding used H.264 CRF 16, slow preset, yuv420p, square pixels
and faststart. There was no frame interpolation or audio re-encoding during
upscaling. Every video timestamp and audio packet matched the approved source;
full decoding and representative visual checks passed. The approved mix
measures approximately −18.81 LUFS integrated and −1.85 dBTP.

The final 4K SHA-256 is
`3c41d9bfec115ecc6102ad935a961ae286904eebeb855d7f376870d1b1ad19f0`.

## Archive and reproduction

Local archive: `data/workspace-archive/forest-spirit/`.
Published master: `final/scary-woods-episode-01-4k.mp4`.

The compact archive retains the exact approved 1080p upscale input and an
editable finishing kit: clean picture, PCM stems, individual dialogue clips,
caption panels and cues, generated source imagery, reusable sprites/masks,
model weights, scripts and production notes. Repeated frame caches, review
exports, previous cuts and unused audition audio are removed. The archive
manifest records retained checksums and the removal inventory.

The [finishing tool](../tools/forest-spirit/README.md) verifies the archive,
reassembles an editable 1080p presentation, or runs the standard 4K upscale.
Reassembling from clean picture incurs another picture encode; the retained
approved input is the authoritative source for reproducing the 4K delivery.
The pilot contains no full 3D puppet rigs.

## Technical credits

- AI creative development, dialogue, editing and production engineering:
  OpenAI Codex — GPT-6 Astra.
- Generated imagery: OpenAI's built-in image-generation tool in Codex.
- Voices: ElevenLabs v3; Wood/Luke, Clay/Baxter, Paper/Elowen, Spirit/Iron Rose.
- Music and sound effects: ElevenLabs Music and Sound Effects.
- Dialogue timing checks: ElevenLabs Scribe v2.
- Animation, compositing and finishing: custom video-generator scripts, FFmpeg,
  Python, Node.js, Pillow, NumPy, SciPy, and Swift/AppKit for caption artwork.
- Local 4K upscale: Real-ESRGAN through ncnn.

https://github.com/TeeKay-FourTwentyOne/video-generator
