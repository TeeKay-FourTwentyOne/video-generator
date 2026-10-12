# Runway video API

The production CLI and its MCP wrappers support direct Runway `gen4.5` and
`gen4_turbo` generation, with the same ledger and source preservation rules as
Veo and MiniMax. The contract and list prices were checked 2026-10-11 against
Runway's [OpenAPI specification](https://github.com/runwayml/openapi) and
[pricing](https://docs.dev.runwayml.com/guides/pricing/). Node's built-in fetch is
used; no new package is required and no request is automatically retried.

## Setup and account check

Set `RUNWAYML_API_SECRET`, or set `runwayApiKey` in the ignored `data/config.json`
with file mode `0600`. Environment configuration takes precedence. Never put a
key in a prompt, manifest, command-line argument or source file. The CLI does not
load `.env` files. Runway API credit is separate from web-app subscription credit.

```sh
npm run build
npm run film -- doctor
npm run film -- runway-account
```

`doctor` only checks local configuration presence. `runway-account` makes a
read-only `GET /v1/organization` request and reports credit balance and limits for
the two supported models. It omits account IDs and unrelated configuration.

## Film request

```json
{
  "id": "S01",
  "beat": "A bus crosses completely out of the fixed shot",
  "frames": 192,
  "requestId": "S01-runway-v1",
  "request": {
    "provider": "runway",
    "model": "gen4.5",
    "promptFile": "prompts/S01.txt",
    "durationSeconds": 8,
    "aspectRatio": "16:9",
    "resolution": "720p",
    "generateAudio": false,
    "seed": 421
  }
}
```

Use a film canvas with the same aspect ratio. Paths are workspace-relative.
Initialize one ledger after the user's provider/scope/spend authorization, then:

```sh
npm run film -- plan data/workspace/my-film-v1
npm run film -- submit data/workspace/my-film-v1 S01
npm run film -- poll data/workspace/my-film-v1 S01 --wait=300
npm run film -- reconcile-runway data/workspace/my-film-v1 S01
```

`plan` is local and free of API calls. Only `submit` creates a generation.
Text-only Gen-4.5 uses `POST /v1/text_to_video`; adding `firstFramePath` selects
`POST /v1/image_to_video`. Gen-4 Turbo requires that starting image. Polling uses
`GET /v1/tasks/{id}`. API calls use the fixed `api.dev.runwayml.com` origin,
Bearer authentication, and `X-Runway-Version: 2024-11-06`; redirects are refused.

## Qualified controls

- Both models: integer 2–10 seconds; prompt 1–1000 UTF-16 code units; optional
  unsigned 32-bit seed. A seed does not promise identical regenerated pixels.
- Native MP4 only: 16:9 at 1280x720, 9:16 at 720x1280, and image-to-video 1:1 at
  960x960. `resolution: "720p"` names the native tier, including square output.
  Runway offers other shapes and paid output formats; they are not exposed here.
- These models generate silent video. `generateAudio: true`, last frames,
  reference arrays, prompt expansion, third-party models and unknown controls
  fail locally rather than being ignored.
- Starting frames: local PNG/JPEG/WebP, 256–4096 pixels per dimension, with aspect
  matching the output exactly. This adapter refuses implicit provider cropping.
  It validates actual encoding with ffprobe and limits the entire encoded data
  URI to 5 MB. No public upload is created. Hashes bind the source to the attempt.

See [Runway inputs](https://docs.dev.runwayml.com/assets/inputs/) and the
[official model capability table](https://github.com/runwayml/runway-studio-skills/blob/main/SKILL.md#model-selection-guide).

## Costs and recovery

At USD 0.01 per credit, Gen-4.5 costs 12 credits/second and Turbo costs 5.
An eight-second Gen-4.5 take reserves USD 0.96 before POST. The quote excludes
tax, anchor generation, separate sound and later paid processing. Those require
their own reservations within the same authorized budget.

The operation journal saves the request fingerprint before POST, then saves the
task ID before updating the ledger. Repeating an identical known request returns
the existing task without spending again. Changed input under an existing ID is
refused. A lost response or ambiguous server error keeps the full reservation;
there is no claim of server-side idempotency. The public API does not expose a
task-list endpoint in this integration.

If submission outcome is uncertain, inspect the developer portal and local
journal. With evidence identifying the original task:

```sh
npm run film -- recover-runway data/workspace/my-film-v1 S01 TASK_ID "Evidence matching original prompt and submission time"
npm run film -- poll data/workspace/my-film-v1 S01
```

Recovery verifies the local fingerprint, existing reservation and reachable task
ID, and refuses a task already assigned to another entry. **Runway's task response
does not expose model or prompt parameters**: recovery depends on the supplied
external evidence for that match. It never submits another generation.

Polling treats PENDING/THROTTLED/RUNNING as active and
SUCCEEDED/FAILED/CANCELLED as terminal. Empty successful output is an error.
Every network call has a 120-second timeout; `--wait=N` bounds repeated polling
(a call already in flight may finish after that limit). Native files download
without the API key, through validated Runway/CloudFront HTTPS hosts, to atomic
no-overwrite files. Saved metadata includes ffprobe output and SHA-256.
Signed output URLs remain in ignored operation records and are downloaded promptly;
[Runway says they expire within 24–48 hours](https://docs.dev.runwayml.com/assets/outputs/).

`reconcile-runway` uses the matching saved terminal task's `cost.credits` at
USD 0.01/credit. It refuses missing, negative or mismatched evidence. Reported
API credit cost is not a tax invoice. Failures never imply an automatic refund:
retain the reservation until task cost or other billing evidence supports release.

## Validation

`npm test` builds the service and exercises offline price/input validation,
reservations, uncertain outcomes, duplicate/concurrent requests, crash recovery,
terminal states, account queries, authenticated API calls, credential-free
downloads, CLI routing and evidence-based cost reconciliation. Live qualification
must distinguish tested models and input modes from capabilities covered only
by the contract and offline fixtures.

On 2026-10-11, two eight-second Gen-4.5 text-to-video requests completed through
this integration. Each cost 96 credits, confirmed by terminal task costs and the
account balance change. Both native outputs were H.264, 1280x720, 24 fps, silent,
and **193 frames (8.041667 seconds)** despite the eight-second request. Full decode
and browser playback passed; originals were preserved. Use explicit frame ranges
for exact edits. Subsequent VERIFY production on the same date completed three
Gen-4.5 image-to-video requests using local first-frame anchors, through the same
submit, poll, download and reconciliation path. Each also cost 96 credits and
returned 193 silent native frames. Gen-4 Turbo remains covered by contract
validation and offline tests only; no paid qualification was performed.
