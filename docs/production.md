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

Write `film.json` in that workspace. Paths inside the plan are workspace-relative;
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
npm run film -- poll data/workspace/my-film-v1 S01
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

`image WORKSPACE request.json` exercises the existing Google image provider with
up to three references, bounded output tokens, and a conservative $0.80 reservation.
The JSON has `id`, `aspectRatio`, `output`, `promptFile`, and `refs` (relative paths).
It saves usage metadata and never retries or replaces an image automatically.

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

Review source clips with intent context (including what must remain absent).
Use the [clip acceptance guide](craft/clip-acceptance-gate.md), inspect flagged
frames yourself, and preserve decisions under `qa/`. A decision has:

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
npm run film -- review data/workspace/my-film-v1 v1
```

Assembly checks input hashes and accepted frame ranges, refuses an existing
version, preserves source media, encodes local segments, and verifies full decode,
dimensions and actual decoded frame count. `final/v1/film.mp4`, `delivery.json`,
and `review.html` form a native review package. Failed/incomplete versions remain
inspectable; choose a new version after fixing the cause. The review page can be
opened locally or served from the workspace on loopback.

The present editor supports hard cuts and a single prepared soundtrack. Make
composites, typography, crossfades or elaborate sound mixes as explicit local
source assets first, using existing craft tools. Keep their recipes alongside the
production. This keeps the core edit contract small and makes each transform
reviewable. Final audio needs loudness/peak checks and listening; the CLI does not
claim artistic approval or automatically upscale/publish.

`tools/production/score.mjs CUES_JSON NEW_WAV` renders deterministic local pad,
bell, air, tick and servo cues. `recipes/borrowed-light-score.mjs` is the original
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
