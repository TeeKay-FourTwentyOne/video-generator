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

## Finishing

### No 4K before review
Review at native resolution; upscale only after the director approves.
Source: claude-code · 2026-05 to 2026-10

### Real-ESRGAN waxes brushwork; photoreal is fine at exact 2x
Lanczos beats Real-ESRGAN below 2x on paintings; verify by a 100% crop, not a
thumbnail. Photoreal miniature footage at exact 2x (1080p to 4K vertical) upscales well.
Source: claude-code · 2026-06; Borrowed Light · 2026-10-03

### Check disk before upscaling, and chunk
The upscaler dumps every frame as PNG to the temp volume: roughly 20 GB for a
35-second 1080p vertical. Near-full disks fail silently, and the percentage shown
covers the AI phase only.
**Apply:** upscale the assembled segments one at a time and stream-concat them,
muxing the approved audio from the native master, when free space is under about
25 GB.
Source: claude-code · 2026-07; Borrowed Light · 2026-10-03

### The 2026 masters used the small x2 model, not x4plus
Until 2026-09-12 `tools/upscale.py` passed its public model ID straight to the ncnn
wrapper, where ID 0 is `realesr-animevideov3-x2`; so the August, September and
Can-Can 4K masters labelled "x4plus 2x" came from the fast x2 model (about 1.6 s
per 1080p frame). The mapping fix made "model 0" the true x4plus, which renders 4x
then resizes: about 30x slower (28-52 s per frame, six hours for 33 s) and a
heavier etch. The default is the fast model again, and the director ruled on
2026-10-03 that this MacBook must never spend that time: the tool refuses x4plus on
macOS (override only on another machine). Check power: on battery the GPU is
throttled and the run can outlive the charge.
Source: claude-code · Borrowed Light · 2026-10-03

### The local FFmpeg has no text filters
No `drawtext` or subtitles filter: burn text through PIL sprites and `overlay`
(`tools/add-timestamp.py`, `tools/caption-box.cjs`, the title recipes).
Source: claude-code · 2026-05

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
