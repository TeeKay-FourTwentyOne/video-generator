# Provision the local semantic candidate

This is an explicit setup recipe exercised with macOS 26 on Apple Silicon and
Python 3.12. Other runtime combinations need new pins and qualification. It installs an
isolated Python environment, downloads public weights and builds a small speech
bridge. Extraction never invokes these setup steps. Keep the entire installation,
profiles and download receipts under ignored `data/`; retain the free-space reserve
enforced by analysis. No provider account is needed.

The candidate uses whisper.cpp v1.9.5, Whisper small multilingual, Silero VAD
v6.2.0, MLX-VLM 0.7.8 with Qwen3-VL-4B-Instruct in 4-bit form, and OpenCLIP 3.3.0
with ViT-B-32 LAION-2B weights. The complete Python dependency versions are in
[`clip-analysis-requirements.txt`](../tools/production/clip-analysis-requirements.txt).
The profile builder checks installed distribution versions against that file.

## Explicit setup

Use an installed Python 3.12, CMake, C++ compiler, FFmpeg and FFprobe. Choose a new
installation path when changing dependencies; preserve earlier pinned environments.
The download helper uses `curl` and fixed upstream revisions, retains partial
downloads on failure, and checks existing files against its local receipts.

```sh
analysis_install="$PWD/data/tools/clip-analysis/semantic-v1"
python3.12 -m venv --copies "$analysis_install/python"
"$analysis_install/python/bin/python3.12" -m pip install --no-cache-dir -r tools/production/clip-analysis-requirements.txt
git clone --depth 1 --branch v1.9.5 https://github.com/ggml-org/whisper.cpp.git "$analysis_install/whisper.cpp"
git -C "$analysis_install/whisper.cpp" rev-parse HEAD
python3 tools/production/clip-analysis-download.py "$analysis_install/models"
cmake -S tools/production/clip-analysis-whisper -B "$analysis_install/bridge" -DWHISPER_SOURCE="$analysis_install/whisper.cpp"
cmake --build "$analysis_install/bridge" --target clip-analysis-whisper -j 4
npm run clips -- analysis setup-ocr
node tools/production/clip-analysis-profile.mjs "$analysis_install" data/clips/analysis/profiles/apple-vision-v1.json data/clips/analysis/profiles/semantic-local-v1.json
npm run clips -- analysis pin data/clips/analysis/profiles/semantic-local-v1.json data/clips/analysis/profiles/semantic-pinned-v1.json
```

The Whisper checkout must resolve to
`d1be6fde11ac6e0407606b4e42fe72d34add8037`. The bridge uses its original-time token
getters and VAD-span API. Its static CPU build is intentional. The plain upstream
CLI is not interchangeable with this executable: its full JSON exports raw token
times on the VAD-shortened timeline, whereas segment getters report original audio
times. See the pinned [Whisper API contract](https://github.com/ggml-org/whisper.cpp/blob/v1.9.5/include/whisper.h).

The [example configuration](examples/clip-analysis-semantic.example.json) contains
placeholders rather than machine paths. The builder fills those paths locally;
`pin` hashes the interpreter, every selected installed package file, model files,
tokenizer, implementation, model cards and licenses. Runtime directory inventories
are checked as well as file hashes. Python bytecode writes are disabled during
execution. Use `--copies` for the virtual environment so resolving the interpreter
does not escape to the base interpreter and lose its installed packages.

The model revisions are fixed in the download helper. Licensing evidence remains
with the downloads: [Whisper](https://huggingface.co/ggerganov/whisper.cpp),
[Silero](https://huggingface.co/ggml-org/whisper-vad),
[Qwen MLX conversion](https://huggingface.co/mlx-community/Qwen3-VL-4B-Instruct-4bit)
and [OpenCLIP weights](https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K).
The candidate uses MIT-licensed speech/retrieval components and Apache-2.0 Qwen
weights. Re-check model cards when selecting a different revision.

## Evidence and limits

Speech artifacts use [`clip-speech.schema.json`](schemas/clip-speech.schema.json).
They retain raw output, language uncertainty, source stream identity, VAD spans,
segment times, original token bytes and both token timelines. Word evidence groups
whitespace-separated tokens; it is model-estimated timing, not forced alignment,
and does not claim language-independent word segmentation. Missing token times
remain unavailable. A word interval crossing outside VAD speech is flagged
`ambiguous-vad-gap`; its original interval and VAD intersections remain visible
without silently trimming or repairing the estimate. At the end of audio, the
pinned Silero model pads its last 512-sample probability window; token timestamps
also have 10 ms resolution. An estimate within that documented overhang keeps its
raw offsets while its displayed source range is intersected with available audio.
`boundaryAdjustment` records the change and affected words are marked
`ambiguous-source-boundary`. Larger out-of-range estimates fail. Silent audio, no
audio, VAD without text, empty ASR and failed ASR have separate evidence. Music and
sung vocals remain unclassified until review or a qualified content detector.

The resampling map starts at the first decoded audio PTS, not the container's
advertised start. It records the exact rational origin, source sample rate,
resampled sample count, timestamp quantization tolerance and inserted silence
gaps. Overlapping timestamps beyond that tolerance fail for review. ASR original
offsets map through that unshortened audio; they are never added directly from a
shortened VAD timeline. Raw offsets and source times remain separately auditable.

Visual descriptions use ordered four-frame windows with one-frame overlap, a
336-pixel resize bound, deterministic decoding and a bounded response. Each result
retains the exact formatted prompt, generation limits, possible truncation,
sampled frame indices and source times. The prompt contains no historical or
creation descriptions. Limited sampling can miss a brief action or word; lack of
an observation is not evidence of absence. MLX reports its own peak allocation in
addition to the coordinator's sampled child RSS.

Image and text retrieval share one model loader, explicit local model configuration,
tokenizer and preprocessing. The adapter rejects mismatched architecture/config,
missing files, overlong text queries, nonfinite/zero vectors, nonunit vectors and
wrong dimensions. Retrieval compares only identical pinned model configurations.
Results include source times, corresponding preview times and actual sampled-frame
paths. A bounded pilot supplies its exact run IDs to `similarText` so earlier
development runs cannot crowd out its results. Similarity is a ranking score,
not a probability.

## Qualifying the candidate

First run one clip, inspect its frames and speech, then rerun the selected 24 clips
after implementation and configuration have settled. Older baseline/OCR runs stay
intact and do not become semantic acceptance evidence. Extraction is serialized
through the model-worker lock; retain elapsed times, sampled RSS, MLX peak memory
and artifact footprints privately. The current format repeats runtime inventories
in run manifests and resumable state; measure retained metadata separately from
media artifacts before scaling the batch. Sharing immutable inventories by hash
is a follow-up storage improvement, not yet implemented.

```sh
npm run clips -- analysis run "$CLIP_ID" --config=data/clips/analysis/profiles/semantic-pinned-v1.json
npm run clips -- analysis verify "$CLIP_ID" "$RUN_ID"
npm run clips -- analysis index
npm run clips -- analysis similar-text 'a person beside a campfire' --config=data/clips/analysis/profiles/semantic-pinned-v1.json
npm run clips -- analysis review-template "$CLIP_ID" "$RUN_ID"
```

A freeze record requires `qualificationVersion: 2`, 24 samples using the same
configuration and extractor hashes, separate immutable human reviews referenced
by `reviewSha256`, and acceptance of each required review pass. Each fixture has
`case`, `passed` and an `evidence` object containing its private JSON `path`,
`sha256` and `bytes`; that file must identify the same case and pass result.
Required cases include rotation, HDR, VFR, corruption, silent/no audio, delayed
audio, silence gaps, failed ASR, changed pins, incompatible vectors and interruption.

Each reviewed retrieval query records `query`, `accepted`, `expectedMatches`,
`falseMatches`, `missedEvents`, `timingErrors`, `notes` and a hash-bound `evidence`
file. Expected matches identify a pilot clip, run and original start/end seconds.
For a deliberately negative query, set `expectedNoMatch: true` and leave
`expectedMatches` empty; record returned false candidates explicitly. The evidence
stores that query, `configSha256` and its actual result list. Derive
`retrieval.acceptanceCriteria` from those labeled cases. Agent inspection and
automated regressions do not substitute for the required human review or listening.
Unresolved claims, misses and timing errors remain blockers to freezing.

Raw output and review packages stay private. Public projection still requires an
explicit privacy-reviewed summary. This setup does not establish cloud recovery,
cleanup readiness or permission to remove any master.
