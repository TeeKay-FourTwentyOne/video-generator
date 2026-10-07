# Carnival Dream — music-video preparation

Status: analysis complete; ready for a creative walkthrough. No treatment,
section labels, aspect ratio, or production budget has been approved.

## Scope and source

Analyze the supplied song before planning a music video made primarily with
local stop-motion-style animation and similar effects, with selected generated
video at key moments. Analysis ceiling: **$10**. The initial local signal analysis
cost **$0**. At the user's subsequent request, the existing repository Whisper
service transcribed the full song and three short checks. Total estimated
analysis spend is **about $0.024**, using the published
[Whisper rate](https://developers.openai.com/api/docs/models/whisper-1) of
$0.006/minute; the invoice was not queried. No model downloads or production
generations were made.

Original: `../music-distribution/audio/01 - Carnival Dream.mp3`. It remains in
place, unchanged. A checksum-matched copy and all measurements are in ignored
`data/workspace/carnival-dream/analysis-v1/`. Artist and account metadata are not
needed in this source brief. Hall of Memories work is separate and untouched.

- [Local listening map](../data/workspace/carnival-dream/analysis-v1/index.html)
- [Timestamped Whisper lyric draft](../data/workspace/carnival-dream/analysis-v1/whisper/lyrics.draft.md)
- [Draft subtitle timing](../data/workspace/carnival-dream/analysis-v1/whisper/lyrics.draft.srt)
- [Signal plots](../data/workspace/carnival-dream/analysis-v1/signal-map.png)
- [Measurements](../data/workspace/carnival-dream/analysis-v1/analysis.json)
- [Source-preservation checks](../data/workspace/carnival-dream/analysis-v1/verification.json)
- [Offline tool documentation](../scripts/song-analysis/README.md)

## What was established

- Decoded duration **170.155828 seconds (2:50.156)**; stereo, **44.1 kHz** MP3.
- Strong regular pulse: refined global estimate **176.010 BPM**, with a supported
  half-rate reading of approximately **88.005 BPM**. Use **88 BPM provisionally**
  for planning. Tempo feel, time signature, and downbeat are not verified.
- The first ten seconds are about **8 dB lower in RMS** than the next ten,
  with markedly less energy below 180 Hz. A substantial entrance occurs around
  **0:10**.
- Spectral patterns recur across passages near **0:43, 1:38, and 2:22**.
  The approximately **54.5-second** separation between the first two returns
  fits 20 four-beat bars at 88 BPM, *if* the meter is 4/4. This is a structural
  hypothesis, not proof of chorus placement or meter.
- The post-opening arrangement maintains substantial level and bass through
  the track; there is no similarly large sustained RMS collapse. A middle
  contrast near **2:00** should not automatically be staged as a silent or
  beatless breakdown.
- The ending remains strong until roughly **2:48.3**, followed by a short
  decay; the final approximately **0.15 seconds** are near silent.
- Technical reference: integrated loudness **−10.92 LUFS**, loudness range
  **5.0 LU**, estimated true peak **+0.14 dBTP**. These are measurements of the
  supplied MP3, not a remaster request; the audio was not processed for output.

The interface did not provide direct listening. The repository does have a
configured Whisper API function at
`mcp/video-generator/src/services/analysis.ts:transcribe`; this was missed in the
initial capability search and then used at the user's request. The full-song
pass plus independent checks of all three hooks now support a draft lyric map.
The short checks corrected a repeated misrecognition in the hook and an
overextended first-chorus ending. Raw responses and all revisions are retained
under ignored `whisper/` artifacts. The count-in near 1:36 differs between the
full and short passes and still needs listening confirmation. Do not treat raw
word timings as final lip-sync or karaoke alignment.

My text-based reading is attraction and temporary euphoria giving way to loss
and circular motion. Verse 2 supplies carnival, lights, riding, and spinning
imagery directly; those ideas no longer depend only on the title. This is an
interpretation of the draft, not the artist's confirmed intent. Instrumentation,
key, chords, and the sung delivery still need listening review.

## Provisional map for the walkthrough

Updated with Whisper onsets and checked refrain endings. Labels remain a draft;
times are listening cues, not frame-accurate edit points. Gaps without recognized
words may still contain backing vocals or missed words.

| Approximate passage | Working role | Useful visual question |
| --- | --- | --- |
| 0:00–0:21.2 | Intro; fuller entrance near 0:10 | What single image establishes the world, then begins moving? |
| 0:21.2–0:42.3 | Verse 1 | What relationship or desire are we following? |
| 0:42.3–1:04.8 | Chorus 1 | What central image expresses euphoria becoming unstable? |
| 1:04.8–1:16.1 | Instrumental link, provisional | What changes before the next verse? |
| 1:16.1–1:38.1 | Verse 2 and count-in | How do riding and spinning develop the situation? |
| 1:38.1–1:59.3 | Chorus 2 | How has the meaning of the central image changed? |
| 1:59.3–2:20.6 | Instrumental contrast, provisional | Is there a reversal, transformation, or new viewpoint? |
| 2:20.6–2:42.8 | Final chorus | What is the visual payoff? |
| 2:42.8–2:48.3 | Outro | What does the final invitation and circular answer mean? |
| 2:48.3–2:50.156 | Ending decay | Which image can hold after the last large accent? |

The earlier signal-only A/B/C map is preserved in `review.signal-only.json`.
Its development regions included lead-ins before the verses; transcription
now separates those. Repeated lyrics support the working chorus labels.
Additional texture-change candidates occur near 0:22, 0:36, 0:49, 0:56,
1:16, 1:50, 2:11, 2:27, and 2:34; most may only need gesture or framing changes.

## Production implications to discuss

My working recommendation is a small set of tactile images that evolve across
the returns. Repetition can support the song while saving animation work; each
return should change an action, setting, relationship, or visual scale.

At 88 BPM, a beat lasts about **0.682 seconds**; a half beat **0.341 seconds**;
two and four four-beat bars last about **5.45 and 10.91 seconds**, respectively,
if 4/4 is confirmed. These are useful provisional loop lengths. Keep motion
accents aligned to the music while allowing the camera and story to breathe
across several beats. Avoid turning every transient into a cut.

For a prospective 24 fps timeline, one 88 BPM beat is **16.36 frames**. Derive
each cue from its absolute time and round to the delivery frame; repeating a
fixed 16-frame beat would drift. The exported pulse grid follows the stronger
176 BPM subdivision and is explicitly not a downbeat grid. Animation pose
cadence and delivery frame rate should be chosen separately.

Mostly local held poses, cutouts, replacement animation, parallax, and reusable
loops are plausible. Two or three generated-motion events are a useful initial
allocation to discuss: an entrance, a middle transformation, or a final payoff.
Choose them for the agreed action and performance needs rather than simply
because a section is loud. No production cost estimate or spending authority
is implied by the $10 analysis ceiling.

## Information needed next

1. **Lyric confirmation and intended meaning.** Check the Whisper draft,
   particularly the count-in, then discuss the artist's reading, desired
   emotional destination, and any ambiguity to preserve.
2. **The video's relationship to the song.** Literal carnival imagery, a
   metaphorical world, a character narrative, performance, abstraction, or a
   blend. The title alone is not grounds for choosing horror or whimsy.
3. **Visual taste and subjects.** A few references, tactile materials, recurring
   figures/objects, artist appearance or likeness, and imagery to avoid.
4. **Delivery.** Full track versus an edit, aspect ratio, viewing context, and
   desired finish. Do not carry Hall of Memories' format into this automatically.
5. **Production budget and priorities.** Separate from analysis; identify the
   moments worth generated motion after a treatment and simple animatic exist.
6. **Optional source assets.** Lossless master and stems if available; supplied
   artwork if it should influence the visual identity. The MP3 suffices to plan.

Walkthrough order: confirm lyrics/meaning and the map; choose one visual premise;
assign story states to the repeated passages; select the exceptional motion
events; set format and production budget; make a rough timed animatic before
production generation. Do not begin asset generation merely because analysis
is complete.

## Reproduction and checks

The reusable analyzer is `scripts/song-analysis/map_song.py`; the local player
builder is `scripts/song-analysis/build_player.py`. FFmpeg performs decoding
and read-only loudness measurement. NumPy/SciPy supply spectral analysis; a
compatible already-cached NumPy was used to run the installed Matplotlib.
No shared environment was modified.

The copied audio matches the original SHA-256. Original modification time and
content hash remain unchanged. Measurements and cues are relative to the first
decoded sample, not MP3 packet timestamps. Local runtime commands and validation
details stay with the ignored analysis artifacts.
