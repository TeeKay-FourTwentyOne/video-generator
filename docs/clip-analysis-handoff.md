# Clip analysis handoff: qualify the first semantic profile

Status: core implementation and local provisioning completed on 2026-10-14;
semantic pilot acceptance and profile freezing remain separate review steps.
Read [the plan](clip-analysis-plan.md) for the full target and
[the command guide](clip-analysis.md) for the implemented interfaces.
For the remaining checks before relying on remote masters or reclaiming disk
space, continue with [the backup-readiness handoff](clip-backup-readiness-handoff.md).

## Implementation continuation

The [reproducible setup](clip-analysis-setup.md) and placeholder configuration now
cover the pinned Whisper/VAD bridge, MLX-VLM and OpenCLIP runtimes. Speech evidence
retains structured VAD, source-aligned segment/token/word-group times, raw shortened
offsets and resampling maps. Word intervals crossing VAD gaps are flagged rather
than repaired silently. Padded VAD endpoints retain raw estimates and explicit
boundary adjustments to the decoded sample range. Visual windows retain exact
prompts and sampled-frame links. Image/text retrieval uses matching pinned preprocessing and rejects invalid
vectors. Private search exposes original and preview times plus sampling limits.

The follow-through evidence is under
`data/workspace/clip-analysis-semantic-v1/`: `implementation.json`,
`pilot-candidates-reviewed.json`, `real-fixtures.json`, `pilot-results.json`,
`retrieval-results.json`, `review.html`, `reviews/` and `qa/`. Check the current
status of those files; a running or incomplete report is not acceptance evidence.
The candidate configuration is `data/clips/analysis/profiles/semantic-pinned-v1.json`.
All raw model output, weights, environments and measurements remain ignored.

The final technical pilot completed on 24 clips with identical configuration and
extractor hashes. Ten scene queries returned the agent-nominated clip first within
that pilot; an additional door-opening probe remains an unconfirmed action match.
These are audition results, not human-ground-truth accuracy. Final delayed-audio
and silent-audio fixtures passed, along with 136 offline regressions. The complete
report is `pilot-evidence-final.json`; `agent-review-notes.json` and
`pilot-review-draft.json` retain proposed acceptance criteria without approval.

One original long candidate failed on overlapping decoded audio timestamps and
was replaced; its evidence remains private. The endpoint-padding case found in
another clip is now covered by an explicit regression and ambiguity flag. Runtime
inventory duplication also needs attention before a full-library rollout: measure
the complete retained footprint, not only declared media artifacts.

The freeze gate now requires qualification version 2, immutable human reviews of
the exact sample manifests, source-bound retrieval labels and retained query and
fixture evidence. Agent inspection and passing regressions do not satisfy it.
Subtle actions, inferred static claims, music/vocals and estimated word boundaries
remain review concerns. No profile has been frozen by this implementation.

The original scope below remains the acceptance checklist, not a claim that the
human review or cloud recovery work has been completed.

## The next critical deliverable

Make a provisioned local semantic profile produce trustworthy, timecoded speech
and visual observations, then demonstrate useful retrieval on a reviewed pilot.
Technical measurements and OCR alone cannot answer what happens in most footage
or what is said. This is the largest remaining first-pass gap before relying on
small local previews to select a remotely stored master.

Keep the next increment focused on Whisper/VAD, prompt-blind visual descriptions
and OpenCLIP image/text retrieval. The baseline adapters were starting implementations;
the core paths now have real local execution evidence. CLAP, tracking, anatomy checks
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
2. **Finish auditable speech timing first.** The baseline Whisper adapter retained
   raw JSON/tokens and segment offsets but recorded VAD only as a diagnostic label.
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
npm run clips -- analysis pin data/clips/analysis/profiles/semantic-local-v1.json data/clips/analysis/profiles/semantic-pinned-v1.json
npm run clips -- analysis run "$CLIP_ID" --config=data/clips/analysis/profiles/semantic-pinned-v1.json
npm run clips -- analysis verify "$CLIP_ID" "$RUN_ID"
npm run clips -- analysis index
npm run clips -- analysis similar-text 'a person opening a door' --config=data/clips/analysis/profiles/semantic-pinned-v1.json
npm run clips -- analysis review-template "$CLIP_ID" "$RUN_ID"
```

This handoff does not establish production cloud recovery or cleanup readiness.
Those still require current backup verification, an actual recovery rehearsal,
independent access evidence and a dependency audit after the semantic profile is
qualified. Preserve masters, archives and unrelated work throughout.
