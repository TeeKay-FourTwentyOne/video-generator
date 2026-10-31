# Editing, sound and finishing field notes

Editor contract: `docs/production.md` (integer frames, hash-bound decisions,
per-segment fades, one prepared soundtrack). Precise FFmpeg: `../ffmpeg-knowledge.md`.

## Editing

### Review notes use source time
The director reads "src X, edit Y" off a debug overlay; source time is canonical
because trims move edit time. Burn `tools/add-timestamp.py --frame` on the
delivery for review, and re-anchor audio by shot plus source time after any trim.
Source: claude-code · 2026-06 to 2026-08

### Integer frames, not planned offsets
Rearranging chunks by planned seconds drifts; use start and end frames (the
maintained editor is integer-frame). Stream-copy trims snap to keyframes.
Source: claude-code · 2026-07

### Fades end on true black
FFmpeg's fade ramps from the frame after its start, so a fade-out starting at
`frames − N` never reaches black; the editor starts it one frame earlier.
Source: claude-code · Borrowed Light · 2026-10-03

### Splices that stagger want a finer scan
Rescan with `--trim-a-step=0.05` (`tools/splice.cjs`).
Source: claude-code · 2026-08

### Long-form music: pre-trim per segment
Pre-trim the music with per-segment fades and layer it in the assembler.
Source: claude-code · Da Derga's Hostel · 2026-05

## Sound

### Mix by absolute RMS targets
ElevenLabs and Veo source levels vary wildly; normalize each source to a target
RMS and verify the grammar windows. `alimiter` needs `level=false`.
Source: claude-code · 2026-07

### Mask an imperfect vocal beat with ambient sound
Louder ambient effects over an imperfect line beat a regeneration chase.
Source: claude-code · 2026-07

### ElevenLabs covers effects and music
`generate_sound_effect` does snickers, screams and muffled voices, not only
ambience. ElevenLabs is the only music provider in use. TTS `speed: 1.2` offsets a
slow mood speed factor.
Source: claude-code · 2026-06 to 2026-08

### Concat audio wants matching layouts
Normalize to stereo before concatenation or a mono/stereo mismatch drops audio;
regenerate parts rather than splitting and inserting silence.
Source: claude-code · 2026-05

### A deterministic cue timeline re-times for free
Composing cues relative to shot starts (`T['S04'] + 1.1`) means a trimmed edit
is one re-render; measure with `loudnorm` after each render. For a short vertical
with a quiet first half, about −16 LUFS integrated with true peak under −1.5 dBTP
worked, lifting the quiet half rather than squashing the climax.
Source: claude-code · Borrowed Light · 2026-10-03

### Native beds and a local score mix from one frame-addressed manifest
`tools/production/mix.mjs` takes the same frame ranges as the picture segments, places
each native take at its edit frame, applies gain, fades and a high-pass, sums without
normalization, then a static gain to the target integrated loudness and a true-peak
limiter; the report holds the measurements before and after. Native Veo levels
differed by 23 LU between two takes of the same film, so per-track gains are a
measurement, not a default. A detuned drone pair at 0.2% beat at about 0.9 Hz and
read as a throb on the waveform; 0.05% breathes instead.
Source: claude-code · Washing Day · 2026-10-03

### Disembodied voices read as a device when they are band-limited and keyed to a glow
Four ElevenLabs lines for two phones were run through a 380–5200 Hz band, a +4 dB presence bump at 2.4 kHz,
a short single echo and a limiter, and the ending still's screen glow was driven by each line's RMS envelope
(fast attack, slow release) so the phone "speaking" brightens. A lute underscore passed through the same
chain returned "from the phones" after stopping dead on the earbud click.
Source: claude-code · Balcony · 2026-10-19

## Finishing

### No 4K before review
Review at native resolution; upscale only after the director approves.
Source: claude-code · 2026-05 to 2026-10

### Verify encoded colour tags, including after a stream-copy remux
The Perpetual Check 4K encode retained the BT.709 matrix and limited range but
omitted primaries and transfer tags despite explicit encoder arguments. The
picture and timing checks passed; a separate probe caught the missing tags.
A metadata-only H.264 remux completed the tags without re-encoding. All decoded
frame hashes and timestamps matched the inspected candidate, and audio packets
and decoded audio matched the approved native cut.
**Apply:** probe range, matrix, primaries and transfer on the final muxed file.
When the intended colour interpretation is known, complete missing H.264 tags
with `h264_metadata` and write the container colour information. Recheck the tags,
decoded picture hashes, timestamps and audio identity before replacing the
delivery pointer. Preserve a failed candidate's QA rather than overwriting it.
Source: Codex · Perpetual Check · 2026-10-22

### Real-ESRGAN waxes brushwork; photoreal is fine at exact 2x
Lanczos beats Real-ESRGAN below 2x on paintings; verify by a 100% crop, not a
thumbnail. Photoreal miniature footage at exact 2x (1080p to 4K vertical) upscales well.
Source: claude-code · 2026-06; Borrowed Light · 2026-10-03

### The fast x2 model waxes photoreal faces; blend it with Lanczos and judge at 100%
On 16:9 1080p Veo footage of people (not a miniature), realesr-animevideov3-x2 at exact 2x turned
hair into drawn strokes, smoothed skin to plastic, grew a woven texture on a grey overcoat and
cut bokeh into discs, all visible in 100% crops and invisible in a thumbnail. A plain Lanczos 2x
kept the photograph but was soft; a 50/50 `blend` of the two 4K streams kept the texture and
most of the definition and was delivered. Burned subtitles survived all three.
**Apply:** for photoreal people, render the model pass and a Lanczos pass, cut 100% crops of a
face, a textured garment and an out-of-focus area side by side, and deliver the blend (or the
Lanczos) unless the crops say otherwise; a synthetic card is re-rendered natively, never upscaled.
Source: claude-code · Walla · 2026-10-08

### Check disk before upscaling, and chunk
The upscaler dumps every frame as PNG to the temp volume: roughly 20 GB for a
35-second 1080p vertical. Near-full disks fail silently, and the percentage shown
covers the AI phase only.
**Apply:** upscale the assembled segments one at a time and stream-concat them,
muxing the approved audio from the native master, when free space is under about
25 GB.
Source: claude-code · 2026-07; Borrowed Light · 2026-10-03

### Resolve the wrapper's model ID before upscaling
Numeric model IDs can differ between `tools/upscale.py` and the ncnn wrapper;
resolve the actual upstream model name before selecting a pass. The fast
`realesr-animevideov3-x2` model enlarges directly to 2x, while x4plus renders 4x
before resizing and can be much slower with a heavier etch. The fast model is
the default, and the tool refuses x4plus on macOS. Compare representative 100%
crops before approving a model. Check power: battery operation throttles the
GPU and can greatly extend the render.
Source: claude-code · Borrowed Light · 2026-10-03

### The local FFmpeg has no text filters
No `drawtext` or subtitles filter: burn text through PIL sprites and `overlay`
(`tools/add-timestamp.py`, `tools/caption-box.cjs`, the title recipes).
Source: claude-code · 2026-05

### Subtitles: burn PIL sprites into per-take copies and cut from the copies
With no drawtext filter, film-style subtitles were PIL sprites (soft Gaussian shadow under
off-white text) composited with `overlay=enable='between(t,a,b)'` into a re-encoded copy of
each take (CRF 16, audio stream-copied, frame count verified unchanged). The copies were
registered as local shots in the plan and became the edit's sources, so the native takes and
their hashes stayed untouched and the cue files are the only thing a caption fix changes.
Source: claude-code · Walla · 2026-10-08

### Six native tracks can be the whole soundtrack
Rooms measured -22.7 to -28.8 LUFS in; per-track gains to about -23 LUFS, a 60 Hz high-pass,
eight-frame crossfades across the picture cuts and the last track ringing on under the black
mastered to -16.1 LUFS at -1.9 dBTP with 4.5 LU range and no score. The audio crossfade is
just a track whose `frames` run eight past its picture segment with a fade-out.
Source: claude-code · Walla · 2026-10-08

### Synthetic flat-field video
Full-range sRGB with bitstream tags, static dither to de-band, native 4K rather
than ESRGAN for synthetic frames, raw-piped frames.
Source: claude-code · False Color · 2026-05

### Shorts safe zone
The bottom quarter to third and the right edge are covered by platform UI; text
goes top or middle.
Source: claude-code · 2026-08

### Audio watermark
The `audiowmark` Docker profile with 16-byte payloads survives platform
transcodes and ESRGAN; skip it when the piece needs true silence or a
representation-identity claim.
Source: claude-code · 2026-07

## Delivery and publication

### Descriptions stay short
Hook, viewing notes, credits, thesis and tags only; the director trims before
sharing. Every description ends with the repository URL; the brief gets a
`**Published:** URL` line at wrap-up, only when supplied or verified.
Source: claude-code · 2026-08 to 2026-09

### Name the model family on screen in explainers
Concrete examples in explainers carry on-screen attribution of the model family.
Source: claude-code · 2026-05

### Workspace layout and archiving
`data/workspace/<slug>/` with refs, clips, edit, qa, final and scratch; archiving
preserves the structure but drops intermediate edits, keeping the shipped version
and its 720p master.
Source: claude-code · 2026-06 to 2026-09

### The editor wants every segment's shot id in the plan; mix tracks with fades want explicit lengths
`assemble` refused "Edit references an unknown shot" for graded copies of a take and for a take split into three
segments; adding local shot entries (no request) with those ids fixed it. `mix.mjs` refuses a `fadeOutFrames`
without `frames`; probe each file's duration and clip the track length to the picture.
Source: claude-code · October · 2026-10-08

### Set track gains from measurement, cap premaster peaks
Seventeen ElevenLabs effects spanned −60 to −16 LUFS. Per-track gains set from measured integrated loudness
(sustained sources) or sample peak (one-shots), with a −12 dBFS premaster peak cap and the beds lightly compressed,
gave a master that needed +10 dB static gain to −21 LUFS with a true peak under −1.5 dBTP and sections within 6 LU.
Source: claude-code · October · 2026-10-08

### A synthesised air bed can be inaudible rumble that still eats the ending
A one-pole 23 Hz noise "air" measured −39 LUFS but sat at −21.7 dBFS RMS below 150 Hz in the film's closing black,
flattening the fade to black; K-weighting hides sub-bass. Band-limiting the air to 150 Hz–3 kHz (two one-pole stages
each way, slow ±1.5 dB breathing) made the ending step down with the picture (−24 → −28 → −29 dBFS) at the same LUFS.
**Apply:** measure beds by band (high-pass 150 Hz) as well as LUFS; keep sustained synthetic beds out of the sub-bass.
Source: claude-code · October · 2026-10-08

### Keep late native vocal moments aligned with their source picture
An empty speech-detector result does not establish that an applause bed contains no vocal sound. In House Special, the director identified a short late vocal moment after the bow that automated transcription missed. When the picture is trimmed, copying later native sound to the beginning of the shot can move that moment onto the title. For an intentionally retained utterance, preserve the source-frame offset in both picture and audio; use separate crowd beds where sound must be moved.
Source: Codex · House Special · 2026-10-18

### Period narration plays through the house, so treat it as the house's playback
Five ElevenLabs lines in five announcer registers only read as "the trailer's voice" once each was passed
through its era's playback (1943 mono, 300–3400 Hz, soft compression; 1973 warm 80–8 kHz with a low shelf;
1999 clean 100–10 kHz; 2026 full) plus one short hall shared by narration and era music, with the coda cue left
clean. Band limits alone were not enough; the hall is what puts the voice on the screen instead of in the mix.
Veo's own native dialogue needed nothing: it already sat in the room.
**Apply:** render treated copies with a deterministic recipe (hashes in an index) and place them in the mix
manifest; keep the era music under the same chain and let the coda break it.
Source: claude-code · Coming Attractions · 2026-10-26

### Preserve dual mono through AAC noise coding
A source with identical PCM channels can decode with different left/right noise
when AAC perceptual-noise synthesis is enabled. On the trail-camera finish, forcing
mid/side alone increased the difference; `-aac_ms 1 -aac_is 0 -aac_pns 0` retained
identical decoded channels at the intended rate. For deliberately mono noise beds
in stereo containers, check decoded channel difference as well as source PCM.
Copy that accepted AAC stream into the upscale and verify packet timing and hashes.
Source: Codex · Untitled trail-camera film · 2026-10-30

### Put fine playback noise after low-rate dub encodes
For GENERATION, increasing pre-encode grain through the literal 1200 kbps dub
chain produced large digital blocks before the fifth copy became sufficiently
obscured. Keeping the original per-pass grain growth, then adding increasing
fine noise and a small contrast reduction at playback, preserved the intended
tape decay. Burn the deck's PLAY display after that noise so it stays clean.
**Apply:** compare the entire progression at delivery scale; do not calibrate
only a clean source or a single grainy frame.
Source: Codex · GENERATION · 2026-10-30

### Test black surrounds after the final lossy encode
A portrait film with a 4:3 window starting on an odd luma row shares a chroma cell
with its black surround. Neutralizing that shared cell and supplying black
footroom solved blue-edge leakage, but noise frames still produced isolated
values above zero after quantization. Protecting the two boundary macroblock
rows with FFmpeg ROI metadata eliminated those residual pixels in the native
master. The check decoded every frame rather than sampling only blue cards.
Source: Codex · GENERATION · 2026-10-30
