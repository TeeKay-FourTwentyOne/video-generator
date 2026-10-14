# Clip analysis handoff: qualify the first semantic profile

Status: next implementation task, following the baseline delivered on 2026-10-14.
Read [the plan](clip-analysis-plan.md) for the full target and
[the command guide](clip-analysis.md) for the implemented interfaces.

## The next critical deliverable

Make a provisioned local semantic profile produce trustworthy, timecoded speech
and visual observations, then demonstrate useful retrieval on a reviewed pilot.
Technical measurements and OCR alone cannot answer what happens in most footage
or what is said. This is the largest remaining first-pass gap before relying on
small local previews to select a remotely stored master.

Keep the next increment focused on Whisper/VAD, prompt-blind visual descriptions
and OpenCLIP image/text retrieval. The current adapters are starting implementations;
they have not been qualified with installed models. CLAP, tracking, anatomy checks
and other advanced detectors can follow after this core profile is useful.

## What is already available

- Immutable, hash-verified runs; bounded subprocesses; a resumable queue; original
  frame/packet timing; complete decoding; signal measurements; private previews.
- Native Apple Vision OCR, separate human reviews, private search/coverage views
  and an explicitly reviewed public-summary projection.
- Pinned local-model contracts, network-denied execution, complete backup-set
  membership/recovery, and cleanup-readiness checks that report missing evidence.
- A baseline/OCR run on 24 library clips, including a recovered long-clip failure.
  Those runs span development revisions and have no semantic or human acceptance.
  They must not be presented as one qualified, frozen extraction profile.

Private continuation evidence lives in
`data/workspace/clip-analysis-implementation-v1/`:

| File | Use |
| --- | --- |
| `implementation.json` | Scope, completed checks and remaining work |
| `pilot-evidence-v2.json` | Final baseline/OCR pilot report and limitations |
| `pilot-plan.json` | Candidate clips; diversity hints still need inspection |
| `inventory-verified.json` | Original-byte and historical-copy verification |
| `qa/npm-test-commit.log` | Final pre-commit build and offline production regressions |
| `qa/final-targeted-tests.log` | Earlier targeted extraction/recovery regressions |

The queue, search, coverage and pinned OCR configuration live under
`data/clips/analysis/`. Older reports and failed attempts remain evidence. Inspect
current manifests and source revisions before resuming; a completed queue item
does not imply that its model observations have been reviewed.

## Implementation sequence

1. **Qualify setup and the real adapter contracts.** Inspect the installed tools
   and the current upstream interfaces before selecting revisions. Use the local
   model candidates in the plan as candidates, not already validated dependencies.
   Provide an explicit setup recipe and an example configuration with placeholders;
   keep downloaded weights, environments and resolved machine paths in ignored
   storage. Pin executables, runtime packages, tokenizers, weights, licenses,
   quantization and preprocessing. Missing files or attempted network access must
   fail visibly. Analysis must never install a package or fetch a model implicitly.
2. **Finish auditable speech timing first.** The Whisper adapter currently retains
   raw JSON/tokens and segment offsets but records VAD only as a diagnostic label.
   Add structured VAD spans and normalized word/segment evidence with stream IDs,
   source presentation times, raw offsets and the mapping from resampled audio.
   Verify whether the selected Whisper/VAD revision reports original or shortened
   audio offsets; never assume silence removal preserves the timeline. Preserve
   original output, language uncertainty and detector failures. Silence, no audio,
   music, sung vocals and an empty transcript need distinct evidence and review.
3. **Exercise visual descriptions and image/text retrieval together.** Keep first
   observations blind to creation prompts and historical descriptions. Qualify
   ordered, overlapping frame windows and links to the actual sampled frames.
   Pin matching image/text preprocessing and model identities; reject incompatible
   or malformed vectors. Test a query through `similar-text` to a result's original
   time range and preview. Show limited sampling and missing passes in coverage;
   an unobserved brief action must not become a confident negative finding.
4. **Run one bounded, labeled pilot.** Review candidate diversity before use. Cover
   speech, silence, music/vocals, absent audio, brief text/actions, static/moving
   scenes, cuts and longer material. Keep the required rotation, HDR, variable-rate
   and corrupt-input fixtures. Run one large model at a time and retain elapsed
   time, peak memory and artifact footprint privately. After implementation settles,
   run all 24 accepted samples with the same pinned code, tools and configuration.
5. **Record review and freeze only the evidence that passes.** Inspect visual claims
   against frames and listen to speech at source times. Record expected matches,
   false matches, missed events and timing errors; derive acceptance criteria from
   labeled cases. Human review remains distinct from automated test results. Retain
   corrections as separate records. Freeze only after required passes and reviews
   satisfy the gate; otherwise leave the blockers explicit.

## Files to work in

| File | Likely change |
| --- | --- |
| `tools/production/clip-analysis-adapters.mjs` | Whisper/VAD timing normalization, adapter validation and coverage |
| `tools/production/clip-analysis-model.py` | Real MLX/OpenCLIP API qualification and output validation |
| `tools/production/clip-analysis-store.mjs` and `docs/schemas/clip-analysis.schema.json` | Versioned contracts if structured speech evidence needs them |
| `tools/production/clip-analysis-views.mjs` | Search timing, model compatibility and pilot/freeze evidence |
| `tools/production/clip-analysis.test.mjs` | Offline failure and timestamp regressions |
| `docs/clip-analysis.md` | Reproducible setup and qualified limits |

Keep schema changes backward readable and derive a new run identity when behavior
or configuration changes. Never rewrite a sealed earlier run to satisfy a new gate.

## Acceptance and resume commands

Completion requires a documented local setup, meaningful offline failure tests,
and a reviewed pilot showing source-aligned speech and useful visual retrieval.
Include delayed/nonzero-start audio, silence gaps, failed ASR, changed pins,
incompatible vectors and interrupted runs in regression coverage. Keep OCR/raw
transcripts/model output private and prove they cannot bypass the reviewed public
projection. Run `npm test` and the applicable privacy checks before committing.

Start by inspecting the current state:

```sh
npm run clips -- analysis help
npm run clips -- analysis status
npm run clips -- analysis inventory
npm run clips -- analysis index
```

After explicit local provisioning, pin a private configuration and test one clip
before enqueueing the selected pilot:

```sh
npm run clips -- analysis pin data/clips/analysis/profiles/semantic-local.json data/clips/analysis/profiles/semantic-pinned.json
npm run clips -- analysis run "$CLIP_ID" --config=data/clips/analysis/profiles/semantic-pinned.json
npm run clips -- analysis verify "$CLIP_ID" "$RUN_ID"
npm run clips -- analysis index
npm run clips -- analysis similar-text 'a person opening a door' --config=data/clips/analysis/profiles/semantic-pinned.json
npm run clips -- analysis review-template "$CLIP_ID" "$RUN_ID"
```

This handoff does not establish production cloud recovery or cleanup readiness.
Those still require current backup verification, an actual recovery rehearsal,
independent access evidence and a dependency audit after the semantic profile is
qualified. Preserve masters, archives and unrelated work throughout.
