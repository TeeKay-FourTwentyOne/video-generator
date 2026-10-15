# Private clip analysis

`npm run clips -- analysis help` is the maintained, offline entry point for
`clip-analysis-plan.md`. It never downloads a model, calls a provider, uploads
media, deletes a master, or publishes extracted text. Cloud operations remain
explicit `clips cloud` commands.

The implemented baseline covers original-byte verification, historical evidence
capture, all-stream probing, full audio/video decode, compressed frame and packet
tables, signal measurements, scene candidates, decoded frame hashes, audio
measurements, and bounded previews. Native Apple Vision OCR is available through
explicit local compilation. Optional adapters support provisioned whisper.cpp with
VAD, MLX-VLM, OpenCLIP and CLAP. The core semantic candidate now has an
[explicit setup recipe](clip-analysis-setup.md), pinned dependency versions,
structured speech timing and matching image/text retrieval. Its usefulness must be established on the pilot;
an adapter being implemented is not evidence that its model was installed or
its output reviewed.

## Inventory, pilot and queue

```sh
npm run clips -- analysis inventory
npm run clips -- analysis inventory --verify
npm run clips -- analysis pilot-plan
npm run clips -- analysis run "$CLIP_ID"
npm run clips -- analysis enqueue all
npm run clips -- analysis work --limit=24
npm run clips -- analysis status
npm run clips -- analysis verify "$CLIP_ID" "$RUN_ID"
```

Inventory retains unknown kinds. Historical paths are reconciled against the
location index; `--verify` hashes masters and existing historical copies.
Path-based kind candidates remain hints. Missing copies and unresolved catalog
IDs are reported, never silently removed or treated as generation evidence.

`pilot-plan` nominates 24 distinct clips using measured technical properties and
attributed historical descriptions. These nominations are not ground-truth labels.
The private plan lists the remaining human labels and fixture cases. Run only
the selected IDs initially; enqueue the complete library after choosing a profile.
Source and unknown clips have queue priority. No derivative's analysis is reused
without a verified temporal mapping.

The worker processes one clip at a time with bounded FFmpeg threads. Semantic
passes share a separate model lock so only one large model runs at once. Progress
is persisted after each pass. A failed job requires `--retry`; `--recover` can
recover only a lock owned by a stopped process on this host. Extraction/worker
commands return a nonzero exit status when their result contains failures. Old
attempts and diagnostics remain private. If code, model files, catalog evidence or settings
change, enqueue a new run; the worker refuses to reinterpret an existing job.
When a verified successor completes at least the same configured/required passes,
the earlier failed job keeps its failure and gains a `supersededBy` reference.
It remains visible in history and is excluded from outstanding failures.
`analysis adopt CLIP_ID RUN_ID` registers an already completed, hash-verified
direct run in that queue without repeating extraction.

## Evidence contract

Runs live under `data/clips/<clip-id>/analysis/<run-id>/`:

```text
manifest.json                    immutable final completion manifest
state.json                       resumable coordinator state
steps/evidence/historical.json   attributed catalog evidence, separate from observations
steps/evidence/adjacent/          explicitly selected original evidence copies
steps/probe/technical.json       complete private FFprobe output
steps/decode/decode.json         complete decode result and retained diagnostics
steps/timing/frames.jsonl.gz     original stream PTS/DTS, time bases and frame indices
steps/timing/packets.jsonl.gz    original packet timing, flags and positions
steps/signal/scenes.json         scene candidates and signal aggregates
steps/signal/*.jsonl.gz          full-frame signals and decoded fingerprints
steps/audio/audio.json           audio presence and signal measurements
steps/audio/waveform-*.png      waveform previews, with measured envelopes in JSON
steps/preview/preview.mp4         seekable preview with source audio
steps/preview/preview.json        sampling, display conversion and timing mapping
steps/preview/contact-sheet.html timecoded local contact sheet
steps/preview/keyframes/          bounded sampled frames
steps/<adapter>/<adapter>.json   original model observations
steps/<pass>/receipt.json         immutable per-pass hashes, settings and measurements
attempts/                        interrupted/failed attempts; not completion evidence
```

The manifest schema is `docs/schemas/clip-analysis.schema.json`; runtime checks
also recompute run identity, reject traversal/symlinks/undeclared step artifacts,
and verify every hash and size. The run ID covers source identity, effective
configuration, tool versions and hashes, extractor source hashes, and the catalog
evidence captured at the start. Inputs are hashed again before sealing completion.
Completed step directories are installed atomically and are recoverable even if
the process stops before writing coordinator state.

New runs and queue entries use `storageVersion: 2`: their `configRef` identifies
one immutable configuration inventory under `data/clips/analysis/inventories/`.
The exact configuration still determines the run identity. Readers verify the
shared file before expanding it, and complete backups include it explicitly.
Historical inline manifests remain readable and are never rewritten. Changing
the extractor storage implementation creates new runs and requires qualification
before those runs can replace a frozen profile.

`complete` on a manifest means the immutable run was sealed. Each pass still has
its own status. Optional unprovisioned passes stay `pending`; model observations
start `needs-review`. A failed pass cannot be sealed as an empty successful
result. A verified absence of audio yields an explicit `not-applicable` result
for audio-only passes. Quiet audio and failed ASR are different states.

PTS and rational time bases are authoritative; float seconds are conveniences.
Preview frame counts and timestamp mappings are checked against the original
timing table. Audio measurements explicitly use a microsecond output time base.
The source-to-preview origin, autorotation, sample-aspect conversion and audio
shift are recorded. HDR conversion currently requires review and produces no
misleading SDR preview; image subtitles also require a qualified adapter.

Signal results include FFmpeg signalstats, scene, black, freeze and blur measures,
per-frame decoded SHA-256 fingerprints, silence detection, loudness and true-peak
metadata. They are measurements and candidates, not defect acceptance. Optical
flow, object tracks, anatomy judgments, calibrated event classifiers, full pixel
histograms and qualified HDR tone mapping remain extension work. The recorded
coverage does not claim those analyses ran.

Every command has a time limit and disk/free-space checks. Defaults reserve local
free space, cap retained output and keyframes, and record sampled child RSS,
elapsed time and output sizes. RSS sampling does not measure GPU allocations and
may be absent for commands that finish before the first sample. Inspect the pilot
measurements before selecting retention limits for the complete library.

## Local adapters and explicit provisioning

```sh
npm run clips -- analysis setup-ocr
npm run clips -- analysis run "$CLIP_ID" --config=data/clips/analysis/profiles/apple-vision-v1.json
npm run clips -- analysis pin data/clips/analysis/profiles/local-models-draft.json data/clips/analysis/profiles/local-models-pinned.json
```

`setup-ocr` compiles the checked-in Swift adapter with the installed Apple tools;
it downloads nothing. The profile pins the binary and source and records the OS
and Vision request revision. OCR preserves original spelling, normalized search
text, bounding boxes, confidence source and exact sampled-frame references.
Appearance between sampled frames is not inferred.

For other adapters, first provision the runtimes and weights through an explicit
setup action. A private draft profile can override `profile`, `required`, `limits`,
`signal`, `preview`, `evidence` and `adapters`. Unknown settings fail validation.
Keep an adapter entry for each desired pass:

| Pass / kind | Required settings |
| --- | --- |
| `transcript` / `whisper.cpp` | Qualified bridge executable, `modelFile`, `vadModelFile`, `bridgeSource`, `timestampContract` and explicit VAD settings |
| `observations` / `mlx-vlm` | `script`, `runtimeFiles`, local `modelPath`, `windowFrames`, `imageSide`, `maxTokens`, `seed` |
| `embeddings` / `openclip` | `script`, `runtimeFiles`, `architecture`, local `weights`, `modelConfig`, `tokenizerFile`, `vectorDimensions` |
| `audio-content` / `clap` | `script`, `runtimeFiles`, local `weights`, pinned `ffmpeg`; measured `durationSeconds` if absent from the stream |
| supported pass / `json-command` | `args`; executable reads request/output paths appended as separate arguments |

Each entry supplies `executable`, explicit `files` to pin (files or local
directories), `settings`, and an `identity` with nonempty `runtimeRevision`,
`model`, `license`, `quantization` and `preprocessing`. Python adapters use
`tools/production/clip-analysis-model.py`; include it, installed runtime package
files and all model/tokenizer files in `files`. `runtimeFiles` lists the selected
runtime files and must be covered by those pins. `pin` resolves local executables
and computes hashes; it never installs packages or downloads missing files.

Model execution currently requires macOS network denial through `sandbox-exec`.
The child environment omits provider credentials and enables offline flags.
Porting model execution requires a qualified OS network sandbox; baseline FFmpeg
analysis remains portable. FFmpeg input protocols are restricted to files/pipes.
Changing a pinned file fails before execution and again at final verification.

Visual meaning receives ordered timestamped windows with overlap and no creation
prompt. MLX uses deterministic sampling settings and retains sampled-frame references,
the exact formatted prompt and generation limits. Whisper receives local mono audio
with timestamp-preserving resampling. Structured VAD, segment, token and word-group
evidence retains both raw VAD-processed offsets and mapped original audio times.
See the [speech contract](schemas/clip-speech.schema.json) and
[timing limitations](clip-analysis-setup.md#evidence-and-limits). Language and
speech/vocal labels remain uncalibrated and require review. No speaker identities
are inferred. CLAP initially supplies candidate embeddings, not event probabilities.

## Search and review

```sh
npm run clips -- analysis index
npm run clips -- analysis search corridor
npm run clips -- analysis neighbors "$CLIP_ID" "$RUN_ID"
npm run clips -- analysis similar-text 'a forest at night' --config=data/clips/analysis/profiles/local-models-pinned.json
npm run clips -- analysis review-template "$CLIP_ID" "$RUN_ID"
npm run clips -- analysis record-review data/clips/analysis/review.json
npm run clips -- analysis project "$CLIP_ID" "$RUN_ID" data/clips/analysis/review.json
```

The private JSON search index and HTML coverage dashboard are disposable; rebuild
them from catalog records, verified runs and separate reviews. Results distinguish
measured signals, inferred observations, historical analysis, creation prompts,
human corrections and similarity candidates. They include clip identity, evidence
time range, matching preview times, sampled-frame paths and private local presence. Remote presence remains unknown
until an explicit cloud verification. Public `availability` keeps its existing
public-hosting meaning. No SQLite/vector service is required; vector comparisons
currently scan the private index and require identical model configuration hashes.
Wrong dimensions, nonfinite/zero values and nonunit vectors fail visibly. Coverage
retains each pass's sampling limits; a missing pass or unsampled action cannot be
interpreted as a negative finding.

Review templates deliberately have no approval timestamp. A human record binds
the exact manifest hash, step decisions with reasons, and optional corrections
to original observation hashes. Corrections remain separate; the original model
output is never rewritten. A public projection additionally requires explicit
privacy review and a selected description/tag summary. Only versioned hash
references, measured frame/decode fields and that reviewed text enter
`analysisRefs`. Raw OCR, transcripts, source tags, paths, logs, previews and vectors
are never automatically projected or committed.

## Analysis backups and absent masters

`cloud plan` includes only sealed, verified runs, their declared artifacts,
immutable reviews, creation snapshots, masters and a catalog snapshot. Adjacent
jobs, requests, prompt files, recipes and QA are included by adding hash-verified
entries to the extraction profile's `evidence` list:

```json
{
  "clipId": "clip_<full-sha256>",
  "path": "data/workspace/example/operations/saved-request.json",
  "sha256": "<file-sha256>",
  "join": "verified-hash",
  "reason": "Saved request explicitly identifies these original bytes"
}
```

`unambiguous-historical-mapping` is the other allowed join type. Copies remain
historical evidence and cannot become creation-time snapshots. The originals
are preserved. Files outside this explicit list are not implicitly backed up.

For dependency audits, frozen pilot reviews, access attestations and retention
plans, create `data/clips/analysis/support.json` with `schemaVersion: 1` and a
`files` array. Each entry has a private JSON `path`, its file `sha256`, `bytes`,
and `role` (`dependency-audit`, `pilot-review`, `access-attestation` or
`retention-plan`). Include an access-recovery attestation, never credentials.
Additional roles are `historical-locations`, `qualification-evidence`,
`source-recovery`, `relationship-evidence` and `recovery-policy`. Selected files
must be under the private workspace or analysis directories, or be the historical
`data/clips/locations.json` mapping. Supported evidence includes JSON, text/logs,
source snippets and explicitly selected preview artifacts. Credentials and cloud
configuration are excluded from these recovery paths.

These selected support files are backed up by content hash, with their original
relative paths in `restorePaths`. Nested private evidence references containing a
path and SHA-256 must also be explicitly included; a missing dependency fails the
plan. Recovery restores these mappings into the empty recovery root and checks
the transitive evidence again. Absolute model/runtime pins describe separately
provisioned software, not implicitly backed-up installations.

An isolated qualification fixture keeps its nested library namespace. Explicitly
include its catalog record, master, manifest, shared configuration inventory when
present, and every declared artifact. Planning and recovery validate that complete
run and reject a report whose referenced manifest or dependencies are absent.

After syncing the members, the cloud command seals a separate immutable complete
backup-set manifest. It joins catalog digests, canonical snapshot identities,
analysis run IDs, declared artifact paths, object checksums and remote generations.
An ordinary master-upload receipt is not a complete backup-set receipt.

```sh
npm run clips -- cloud plan
npm run clips -- cloud sync
npm run clips -- cloud backup-sets
npm run clips -- cloud verify-set "$BACKUP_SET_SHA256"
npm run clips -- cloud recover-set "$BACKUP_SET_SHA256" data/workspace/rehearsal "$CLIP_ID" --rehearse
npm run clips -- cloud plan --allow-absent
npm run clips -- cloud sync --allow-absent
```

The final two commands explicitly declare intentional local absence. They require
a previously complete backup set and verify that same remote generation, checksum
and size during sync. Missing or changed remote media fails before any attempted
replacement. Missing local creation snapshots or analysis artifacts still fail.
These commands do not evict files. The separate
[duplicate reclamation workflow](clip-cleanup.md) can remove an explicitly
approved canonical duplicate while preserving hash-verified historical originals.

`recover-set` works with independently provisioned cloud access and no local
catalog, media, analysis, receipts or snapshot mapping. It downloads a selected
clip set into a new private directory, validates all member hashes and references,
restores exact canonical snapshot mappings, and rebuilds search. `--rehearse`
also completely decodes the restored streams and records tested format/artifact
coverage. All cloud operations use the existing authorization and budget ledger.

## Freezing a profile and reporting cleanup readiness

`analysis freeze-profile PILOT_REVIEW.json` requires a human-reviewed 24-clip
pilot with all stated diversity labels, verified fixture evidence and retrieval
criteria derived from labeled results. The required profile includes the baseline,
OCR, speech, visual meaning and retrieval. Required model passes cannot silently
remain unrun. The samples must use identical extractor/runtime identities, and
cleanup candidates must match those frozen identities too. This is a reviewable
decision, not an automatic benchmark score.

Qualification version 2 additionally binds each sample to an immutable human
review, requires structured original-time speech evidence and per-sample retrieval
vectors, and verifies private fixture/query evidence files. The
[setup and qualification guide](clip-analysis-setup.md#qualifying-the-candidate)
describes those fields, including negative queries and recorded timing errors.

`analysis readiness PRIVATE_POLICY.json` provides an offline blocker report.
`cloud readiness PRIVATE_POLICY.json` additionally verifies every backup-set
member's current generation and checksums before reporting readiness. A private
policy contains `schemaVersion: 1`, `backupSetSha256`, `profileSha256`, selected
`clips` (`clipId`, `runId`, optional `reviewSha256`), `retention.maximumBytes`, and
hash/size/path references to `dependencyAudit` and `accessEvidence` JSON files.

The dependency audit binds current `catalogSha256`, `usesSha256` and
`locationsSha256` (canonical JSON digests). Each clip must record
`activeEditsReviewed`, `archivesReviewed`, `originalPathsReviewed`,
`alternatesReviewed` and `sharedSourcesReviewed` as explicit decisions. Planned
uses need a `pendingUses` decision with `useId`, a resolution
(`restores-by-clip-id`, `materialized-verified` or `confirmed-inactive`) and a
hash-verified, backed-up `evidence` record. The access evidence must affirm
`independentlyRecoverable` with `reviewedAt`. Audits and the frozen pilot must
themselves belong to the complete backup set.

Missing profiles, model passes, required human review, previews, searchable
records, remote members, matching recovery rehearsals, independent access,
dependency decisions or retained-storage allowance all block readiness. Output
is a concrete manifest of exact library master paths, hashes, backup sets and
potential space savings. Historical workspace/archive copies are outside that
manifest. Explicit cleanup authorization is still required; deletion is not
implemented by these analysis-readiness commands. The duplicate-only workflow
does not waive the requirements for removing a last local copy.

Use the [backup-readiness handoff](clip-backup-readiness-handoff.md) for the
remaining operational checks, including recovery dependencies and rehearsal
limitations that the automated gate does not yet enforce.
