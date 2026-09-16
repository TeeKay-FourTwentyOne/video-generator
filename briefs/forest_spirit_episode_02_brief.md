# Scary Woods — Episode 02: Shorten Sail

**Published YouTube Short:** https://youtube.com/shorts/lykR2ZS4Hws

Publication URL supplied with the release record on 2026-09-15.
Final delivery: **2160 × 3840, 9:16, 24 fps, 840 frames, 35 seconds**, H.264,
48 kHz stereo AAC, six permanent character captions and four selectable ship
subtitle cues. The complete SRT sidecar contains ten cues.

## Story and final edit

Spirit's crystal ball opens onto a Nantucket whaler during an approaching
squall. The mate reports a falling barometer. Plain observational sea spray,
a short warning about an old repair and the captain's vow suggest a voyage
with a history we never see. A 1.75-second below-deck glimpse catches the crew
smoking and laughing before the captain watches men working the sails.
An original mournful Irish-style slow air underscores the passage.

Clay interrupts: “Hang on.” Back in the cabin, Spirit holds a vacant stare
while Clay asks how any of this gets them out of the woods. Wood and Paper
agree that it is odd. Spirit's glass eyes briefly turn in opposite directions.
It presents a spoon: “Look into the spoon.” A strong push into its reflection
ends with “There was once a king...” at 33 seconds, matching Episode 01's
storytelling voice and caption treatment. The final three frames are clean.

The ship story lasts 20 seconds; the stop-motion-style framing lasts 15.
All ship dialogue and location sound are native Veo audio. The framing uses
ElevenLabs voices and locally composited poses, masked facial changes and
camera moves. The final cut restores restrained reactions from the first
framing version and retains the spoon reveal from the zanier alternate.

## Finishing and verification

The released file uses a **Lanczos 2× upscale**, from 1080 × 1920 to
2160 × 3840, through FFmpeg. An animation-upscaler sample exaggerated skin,
hair and wet-wood contours and was excluded. Encoding used H.264 CRF 16,
slow preset, yuv420p, square pixels and faststart. There was no frame
interpolation or audio re-encoding during the upscale.

Every video timestamp and audio packet matched the approved source. Full
file decoding, all-frame proxy checks, subtitle preservation and representative
picture/caption review passed. The approved mix measures −19.75 LUFS
integrated and −2.03 dBTP. Spoken words were verified by mixed transcription;
direct audio audition was unavailable during production.

Final 4K SHA-256:
`bb4e1791b7bdb8a6db870b78020cd754c8e5056024b2fdd3286a506c80929fee`.

## Archive and reproduction

Local archive: `data/workspace-archive/scary-woods-episode-02/`.
Published master: `final/scary-woods-episode-02-4k.mp4`.

The compact archive retains the exact approved 1080p input, a caption-free
picture master, final PCM mix and editable stems, six individual framing
performances, all original generated ship clips and image assets, reusable
character imagery, selected captions, prompts, QA decisions and historical
recipes. Old full edits, previews, redundant mixes and QA image caches are
removed after verification; the archive records the original inventory and
retained source mappings. Duplicate byte content shares local disk storage.

The [finishing tool](../tools/forest-spirit/README.md) verifies the archive,
rebuilds an editable 1080p presentation, or reproduces the Lanczos 4K export.
The editable route re-encodes picture and is not promised byte-identical to
the approved cut. The exact approved 1080p input remains authoritative for
4K reproduction. Native ship speech and location sound remain combined;
the other stems separate framing dialogue from the music/effects bed.

Episode 01's archive remains unchanged. The Episode 03 handoff retains both
the clean spoon artwork and the exact final 4K frame. The king opening line
is approved; the proposed brief royal-dining-room scene has not been generated.

## Budget and provenance

The story-within-the-story authorization was $45. The retained ledger totals
$45 in allocations: $32 in Veo estimates and $13 reserved for other costs.
These are estimates and reserves, not reconciled invoices. Framing and outro
usage are recorded separately in the local production records. The release
upscale and archiving required no provider calls.

The ship is fictional, set around 1845. No whale hunting or rendering is
shown. Generated fittings and rigging are representative period scenery,
not a mechanically surveyed reconstruction. Historical references and
original research notes remain in the archive.

## Technical credits

- AI creative development, dialogue, editing and production engineering:
  OpenAI Codex.
- Character imagery and scene reference images: OpenAI's built-in
  image-generation tool in Codex.
- Ship video, native dialogue and location sound: Google Veo 3.1 Quality.
- Framing voices: ElevenLabs v3; Wood/Luke, Clay/Baxter, Paper/Elowen,
  Spirit/Iron Rose.
- Music and additional sound effects: ElevenLabs Music and Sound Effects.
- Dialogue transcription and timing checks: ElevenLabs Scribe v2.
- Animation, compositing, captions and audio finishing: custom video-generator
  scripts, FFmpeg, Python, Node.js, Pillow, NumPy, SciPy and Swift/AppKit.
- Local 4K upscale: FFmpeg Lanczos 2×, preserving the approved audio stream.

https://github.com/TeeKay-FourTwentyOne/video-generator
