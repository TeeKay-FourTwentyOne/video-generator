# A maintained finishing-master command

RETAKE's 4K finish was made by a private recipe: the interface composites were
rendered again at 2160 by 3840, concatenated frame-exactly by the approved
edit's ranges, and the approved native edit's AAC stream was copied across
unchanged. The result is right, but the recipe repeats bookkeeping the
maintained editor already does: it wrote its own delivery record, which the
record exporter then refused twice (the record must be named `delivery.json`
beside the video; the publication text and its hash must be set as a pair),
and it registered no clip uses for the master. House Special's audio-only
revision needed the same private route. Both are finishing steps that start
from an approved edit and must not change its picture or its sound.

Add a finishing command to the maintained production CLI in a fresh session.
Start from `tools/production/edit.mjs` (assembly and delivery records),
`tools/production/mix.mjs` (soundtrack contract) and their offline tests.

- `film finish WORKSPACE BASE_VERSION NEW_VERSION --sources=MAP.json` takes a
  verified base delivery and a map from each base segment's source to a
  higher-resolution counterpart (a native re-render, or an upscaled copy), cuts
  the same integer frame ranges from the counterparts, and copies the base
  delivery's audio stream unchanged.
- Refuse a changed base hash, a counterpart with a different frame count or
  frame rate, a mismatched aspect ratio, an existing output version, or a
  missing counterpart for any segment.
- Write the normal delivery record beside the video, with the base version,
  base hash, per-segment counterparts and hashes, the full-decode frame count,
  and an audio identity check (packet digest and decoded PCM digest against the
  base). Register the master and the counterparts as uses in the catalog.
- Carry the publication-text copy when the base has one, so `sync-description`
  sees the new master without a hand-written path.
- Offline tests: a two-segment fixture at 2x, success; refusals for each rule
  above; no provider calls; no neural upscaling inside the command (a counterpart
  is whatever the agent prepared and reviewed).

Dated harness observation (Claude Code, 2026-11-03): two Bash calls issued in
the same turn can share a working directory, so a `cd` in one was overridden by
the other and a relative-path step failed silently. Use absolute paths in every
parallel call; noted in `docs/harness/claude-code.md`.

Implemented 2026-11-03: `film finish WORKSPACE BASE_VERSION NEW_VERSION
--sources=MAP.json` in `tools/production/edit.mjs` (`validateFinish`,
`registerFinishClips`, `finish`), wired into the CLI and the `production_finish`
MCP tool, with the two-segment 2x offline fixture and every refusal above in
`tools/production/edit.test.mjs`. The counterpart map is keyed by base clip ID;
the delivery record carries a `finishing` block with the audio packet and PCM
digests; counterpart uses are recorded under `finish/<version>` and the master is
imported as a `delivery` clip. Usage is documented in `docs/production.md`.
