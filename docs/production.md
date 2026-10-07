# Production workflow for agents

The maintained path is a small, local-first production CLI and its MCP wrappers.
It was exercised by **Borrowed Light**, a 32.5-second portrait film. Film craft is
in [craft/](craft/core-workflow.md); executable behavior lives in
`tools/production/` and `mcp/video-generator/src/production/`.

## Start and plan

Use installed dependencies. `npm run build` compiles the MCP service; `npm test`
builds and runs offline production regressions. `npm run film -- doctor` checks
local tools and configured credential presence without sending a provider request.
No command installs packages. Node 22+, FFmpeg and ffprobe are required. Existing
Python QA tools additionally need their existing Pillow/NumPy environment.
The default MCP profile exposes nine `production_*` commands and read-only
`get_config`. Set `VIDEO_MCP_PROFILE=legacy` in the server environment and restart
the connection to expose the historical specialist tools. This is an intentional
compatibility change; film recipes and media remain in place.

```sh
npm run film -- init data/workspace/my-film-v1 20 "User-approved total allocation and scope"
npm run film -- plan data/workspace/my-film-v1
```

Skim `docs/craft/field-notes/` for known provider behavior before writing anchors
and prompts. Write `film.json` in that workspace. Paths inside the plan are workspace-relative;
provider operation records and media stay ignored. The minimal shape is:

```json
{
  "schemaVersion": 1,
  "title": "A small film",
  "width": 1080,
  "height": 1920,
  "fps": 24,
  "shots": [{
    "id": "S01",
    "beat": "The character notices an empty socket",
    "frames": 168,
    "requestId": "S01-v1",
    "request": {
      "promptFile": "prompts/S01.txt",
      "firstFramePath": "refs/S01.png",
      "model": "veo-3.1-prod",
      "durationSeconds": 8,
      "aspectRatio": "9:16",
      "generateAudio": false,
      "resolution": "1080p"
    }
  }]
}
```

`frames` is the intended edit length, not the generated take duration. Local
animation can be another shot without a `request`; the edit references its source
file in the same way. The plan command is a dry run and does not reserve money.

## Spend and recovery

```sh
npm run film -- reserve data/workspace/my-film-v1 qa-budget 2 qa "Bounded QA allowance"
npm run film -- submit data/workspace/my-film-v1 S01
npm run film -- poll data/workspace/my-film-v1 S01 --wait   # keeps polling the same operation, never submits
npm run film -- status data/workspace/my-film-v1
```

The shared Veo client requires `budgetFile` and `requestId`, including when invoked
through `submit_veo_generation` or `create_job`. It reserves integer microdollars
under an exclusive filesystem lock before network access. Same ID + same request
recovers the existing operation; changed input refuses. Different attempts need
different IDs. A concurrent writer can receive a lock error; inspect status and
retry the local command after the writer finishes. Never remove a live lock.

Unknown transport outcomes retain the full reservation. A crash after provider
acceptance but before the operation is saved is inherently ambiguous: inspect the
private provider logs, recover the operation if possible, and do not automatically
POST again. Polling is separate and can continue across process restarts.
Finished filtered/empty outputs are terminal failures. Seeds record intent but do
not guarantee identical regenerated pixels.

The current adapter qualifies GA Veo 3.1 Quality/Fast, 9:16 or 16:9, 720p/1080p,
and exact 4/6/8-second durations. Old bare aliases resolve to GA. Unsupported
variants fail locally; changing capabilities needs current official documentation
and an explicit qualification test, not just a new model string.

`image WORKSPACE request.json [more.json ...] [--reconcile] [--spacing=N]` exercises
the existing Google image provider with up to three references, bounded output
tokens, and a conservative $0.80 reservation per request. The JSON has `id`,
`aspectRatio`, `output`, `promptFile`, and `refs` (relative paths). It saves usage
metadata and never retries or replaces an image automatically. Several request
files run in order, spaced ten seconds apart by default, because the endpoint
answers HTTP 429 to rapid batches; the batch stops at the first failure and names
what completed. `--reconcile` reduces each reservation to the list-price estimate
from the usage record it just saved (`tools/production/image-rates.mjs`, rates
dated in the file); `reconcile-image WORKSPACE IMAGE_ID` does the same later for one
request. A rejected request with no usage record is reconciled by hand with the
response as evidence.

Reserve allowances **before** invoking legacy paid QA/audio/image helpers. Those
scripts do not yet enforce this ledger themselves. Reconcile only from saved
usage or billing evidence, and distinguish a token-price estimate from an invoice:

```sh
npm run film -- reconcile data/workspace/my-film-v1 qa-budget 0.42 "Saved usage totals and dated provider rates"
```

`tools/veo-budget.py` and its historical pots remain intact for older productions;
they are not the budget authority for this new path. Do not count two ledgers as
two allocations. The unbudgeted `execute_project` bulk executor now refuses before
paid prompt generation; migrate its shot descriptions into an explicit film plan.

## Review and edit

For a generated continuation, extract the chosen moving frame by decoded index:

```sh
npm run film -- join-anchor data/workspace/my-film-v1 clips/S04-v1.mp4 156 refs/S05.png
```

This local command writes the PNG and a hash-bound `.png.json` provenance record.
The preceding edit ends at frame 155 (`endFrameExclusive: 156`); the continuation
normally starts at frame zero. It refuses overwrites and out-of-range frames.
Review the actual generated boundary with `tools/seam-check.py`; an exact anchor
does not guarantee either visual or motion continuity.

When revisiting a location after intervening action, use anchor-drift's
`--mode=return-shot --elapsed-action="Describe what happened between these shots"`.
This checks persistent identity, wardrobe and set details without demanding the
same pose. The elapsed action must be explicit; unexplained changes still count
as violations. Keep `across-cut` for adjacent frames and `within-clip` for anchors
that the generator must interpolate. Neither adjacent mode accepts that allowance.

Review source clips with intent context (including what must remain absent).
Use the [clip acceptance guide](craft/clip-acceptance-gate.md), inspect flagged
frames yourself, and preserve decisions under `qa/`. Run the Python QA scripts
from the repository root (their default config path is relative); they log token
usage to `data/cost-ledger.jsonl`, which is the evidence for reconciling a QA
allowance. Their model replies are parsed leniently (`tools/qa_json.py`) so a
stray quote in a note no longer discards a paid call. A decision has:

```json
{
  "sha256": "SOURCE_SHA256",
  "decision": "edit-around",
  "startFrame": 12,
  "endFrameExclusive": 180,
  "notes": "Trim the unmotivated initial gesture; transfer is coherent in this range."
}
```

Write `edit/v1.json` with the final frame ranges:

```json
{
  "schemaVersion": 1,
  "segments": [{
    "shotId": "S01", "source": "clips/S01-v1.mp4",
    "sha256": "SOURCE_SHA256", "inFrame": 12, "frames": 168,
    "decisionFile": "qa/S01.json"
  }],
  "audio": { "path": "edit/score.wav", "sha256": "AUDIO_SHA256" }
}
```

```sh
npm run film -- assemble data/workspace/my-film-v1 v1
npm run film -- review data/workspace/my-film-v1 v1 --overlay
```

Assembly checks input hashes and accepted frame ranges, refuses an existing
version, preserves source media, encodes local segments, and verifies full decode,
dimensions and actual decoded frame count. `final/v1/film.mp4`, `delivery.json`,
and `review.html` form a native review package; `--overlay` adds `film_debug.mp4`,
a frame and timecode burn for review notes in source time. Failed/incomplete versions remain
inspectable; choose a new version after fixing the cause. The review page can be
opened locally or served on loopback with byte-range support for native seeking:

```sh
node tools/production/review-server.mjs data/workspace/my-film-v1/final/v1
```

The server prints its loopback URL and serves only the review package's known
filenames. Stop it with Ctrl+C. A generic server without HTTP byte ranges may play
the opening but leave shot buttons and the scrubber unable to seek.

The present editor supports hard cuts, optional per-segment black fades
(`fadeInFrames` / `fadeOutFrames`, frame counts inside the segment, length
preserving) and a single prepared soundtrack. Make composites, typography,
crossfades or elaborate sound mixes as explicit local source assets first, using
existing craft tools. Keep their recipes alongside the
production. This keeps the core edit contract small and makes each transform
reviewable. Final audio needs loudness/peak checks and listening; the CLI does not
claim artistic approval or automatically upscale/publish.

`tools/production/mix.mjs WORKSPACE MIX_JSON NEW_WAV [--report=JSON]` prepares the
single soundtrack from frame-addressed tracks: native Veo audio trimmed to the same
frames as the picture segments and placed at their edit frames, local score and
foley files, per-track gain, fades and high/low-pass, summed without normalization,
then a static gain to a target integrated loudness and a true-peak limiter. The
report records EBU R128 measurements before and after mastering; listening stays a
separate human step. `tools/production/score.mjs CUES_JSON NEW_WAV` renders
deterministic local pad, bell, air, tick and servo cues. `recipes/borrowed-light-score.mjs` is the original
film score; `recipes/borrowed-light-finish.py` makes the optional local title and
fades with existing Pillow/FFmpeg. Both preserve earlier versions. The finishing
recipe accepts an existing font and never downloads one.

## Interfaces and compatibility

MCP: `production_doctor`, `production_init`, `production_plan`, `production_status`,
`production_image`, `production_submit`, `production_poll`, `production_assemble`,
`production_review` call the same CLI implementation. Author film/cue/edit JSON
through the host's local file tools; use the CLI for allowance reconciliation.
In the legacy profile, `resume_job` resumes a known operation without generating
a new one. The existing creative primitives remain available there. Their schemas
are not a promise that every historical production route is currently qualified.
See [architecture.md](architecture.md) and [repository-review-2026-10.md](repository-review-2026-10.md).

The shared Claude client defaults to `claude-sonnet-5-5`; override using
`VIDEO_CLAUDE_MODEL`, local `claudeModel` configuration, or an explicit call model.
It omits unsupported sampling parameters for Sonnet 5.5. The Python vision helpers
default to their Sonnet 5.5 shortcut and retain `--model-id` overrides. Qualify a
replacement on a saved, representative film defect before changing the default.
