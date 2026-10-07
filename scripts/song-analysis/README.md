# Offline song planning

`map_song.py` reads a local audio file with FFmpeg, copies it into a separate
analysis directory, and measures duration, RMS level, spectral flux, candidate
pulses, spectral changes, timbre similarity, and integrated loudness. It makes
no network calls and never normalizes or alters the input. Output belongs under
ignored `data/`, including the audio copy, fingerprints, plots, and local notes.

Requirements: FFmpeg/ffprobe on PATH and a Python environment containing
`offline-requirements.txt`. Use an existing compatible local environment where
possible. NumPy 2 with an older compiled Matplotlib is incompatible; do not
change a shared Python environment merely to run this tool.

```sh
python scripts/song-analysis/map_song.py path/to/song.mp3 \
  data/workspace/song/analysis-v1 --title 'Song title'
python scripts/song-analysis/build_player.py data/workspace/song/analysis-v1
```

The player works from `index.html` without a server or external assets. Optional
`review.json` in the analysis directory supplies `working_tempo_label`,
`sections` (start, end, label, note), `observations`, `questions`, and `approach`.
These are editorial annotations; the analyzer does not invent semantic labels.
Optional `lyrics` (start, end, text) add clickable transcript lines. Use
`lyrics_note`, `scope_note`, `footer_note`, and `analysis_spend_label` to distinguish
local measurements from any separately authorized transcription service calls.

All times begin at the first decoded audio sample. The strongest detected pulse
may be a subdivision or multiple of the perceived beat. `pulse-grid.json` is
not a verified downbeat map. The autocorrelation estimates are coarsely
quantized; the fitted global pulse refines their frequency using phase coherence.
Validate phase at several points and confirm meter through listening before
syncing cuts or exporting frame-accurate markers. Texture-change peaks use
four-second windows and are approximate. Similar timbre does not prove repeated
melody or lyrics; RMS does not establish emotional intensity. The analyzer does
not transcribe lyrics, identify instruments, or perform listening review.

`onset_detection.py` is the older, separate librosa-based tool, with its own
`requirements.txt`; this offline map does not depend on it.
