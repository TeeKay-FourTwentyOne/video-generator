# MiniMax video API

The maintained CLI supports the direct MiniMax V2 API for `MiniMax-H3` and
`MiniMax-H3-Max`. It uses Node's built-in fetch and the existing film ledger;
no new SDK or package is needed. The API contract and rates were checked
2026-10-11. Offline tests pass through mocked provider responses and synthetic
local media. A live read-only task-list authentication check succeeded on
2026-10-11. Generation quality and billed totals remain unverified until an
authorized audition; no generation was submitted during integration.

## Credentials

Set `MINIMAX_API_KEY` in the process environment, or set `minimaxApiKey` in the
existing ignored `data/config.json`. Environment configuration takes precedence.
Keep that file private (mode `0600`) and preserve other configuration fields.
Do not place credentials in film manifests, prompts or command-line arguments.
The CLI does not load `.env` files automatically.

```sh
npm run build
npm run film -- doctor
```

`doctor` reports only whether credentials are configured. It does not authenticate
or generate. Provider error bodies are not echoed. The key is sent only to
`https://api.minimax.io`, with redirects disabled. Output downloads use approved
MiniMax/Hailuo HTTPS hosts and never receive the API key.

## Plan and submit

Create a workspace and ledger only after provider, scope and spend are authorized,
as described in [production.md](production.md). Add a shot request to its `film.json`:

```json
{
  "id": "S01",
  "beat": "A lamp comes on while the surrounding room stays still",
  "frames": 144,
  "requestId": "S01-minimax-v1",
  "request": {
    "provider": "minimax",
    "model": "MiniMax-H3-Max",
    "promptFile": "prompts/S01.txt",
    "firstFramePath": "refs/S01.png",
    "durationSeconds": 6,
    "resolution": "768P",
    "aspectRatio": "16:9",
    "promptExpansionMode": "balanced"
  }
}
```

The film canvas must have the same aspect ratio. Set `frames` for its intended
edit at the film's FPS. Generated files retain their provider dimensions and
soundtrack; inspect actual dimensions in the saved probe before editing.

```sh
npm run film -- plan data/workspace/my-film-v1
npm run film -- submit data/workspace/my-film-v1 S01
npm run film -- poll data/workspace/my-film-v1 S01 --wait=300
npm run film -- status data/workspace/my-film-v1
```

`plan` inspects local references and quotes without networking or reservations.
Only `submit` creates a task. The existing MCP `production_plan`,
`production_submit` and `production_poll` wrappers invoke these same commands.
Omitting `provider` retains the existing Veo behavior; model names never silently
route through an aggregator.

## Inputs and limits

| Control | H3 | H3 Max |
| --- | --- | --- |
| Output resolution | `768P`, `2K` | `480P`, `768P` |
| Integer duration | 4–15 seconds | 5–15 seconds |
| Prompt expansion option | Omit | `disabled`, `balanced`, `quality` |

Defaults are H3 Max, six seconds, 768P, 16:9 and balanced expansion. Set controls
explicitly in production. Supported ratios are 21:9, 16:9, 4:3, 1:1, 3:4 and 9:16.
There is no exposed seed or `generateAudio` switch in this direct V2 contract;
passing either is rejected instead of silently ignored. Direct H3 Max does not
expose 1080P or 2K in this adapter.

- Text to video: omit all media paths.
- Image to video: `firstFramePath`, `lastFramePath`, or both. MiniMax derives the
  aspect ratio from the image, so each frame must match the planned ratio exactly.
  The transport sends `ratio: "adaptive"`; it never silently crops an anchor.
- Reference generation: use `referenceImagePaths`, `referenceVideoPaths` and/or
  `referenceAudioPaths`, each an array of workspace-relative paths. At most nine
  images, three videos, three audio files and twelve files total. Reference
  inputs cannot be mixed with first/last frames.

The local transport currently accepts PNG/JPEG/WebP images, MP4 video with
H.264/H.265 and optional AAC/MP3 audio, and WAV/MP3 audio. HEIC/HEIF and MOV are
documented by MiniMax but are intentionally not enabled in this inline adapter.
Images/videos need dimensions from 256 to 5760 pixels and a width/height ratio
from 0.4 to 2.5. Video must run at 23.976–60 FPS. Each audio/video reference must
be 2–15 seconds; totals cannot exceed 15 seconds per media type.

Inputs are sent as data URIs directly in the authorized submission. No public
asset upload is performed. Local checks enforce 30 MB per image, 50 MB per video,
15 MB per audio file and a 64 MB serialized body. Base64 expansion counts toward
that body limit; large references must be reduced explicitly. Source hashes,
sizes and durations are recorded; credentials and inline payloads are not.

The quote includes reference charges from [PRICING.md](../PRICING.md). Reference
video on H3 Max costs more per second than output. The first two image inputs on
Max (five on H3) are free, with additional image charges thereafter.

## Persistence and recovery

Each request reserves the full quote before the POST. Stable request IDs and
source-content fingerprints prevent duplicate submissions locally. A known task
is returned on a repeated identical submit, even if the API key is unavailable.
There is no claim of server-side idempotency: MiniMax does not document a client
idempotency key for this endpoint.

The ignored workspace keeps:

- `operations/<requestId>.json`: prompt, quote, input hashes, task ID and submission state.
- `operations/<requestId>.poll.json`: normalized task state, usage and output URL.
- `operations/<requestId>.asset.json`: downloaded source hash and ffprobe metadata.
- `clips/<requestId>.mp4`: preserved provider output, written without overwriting an existing file.

Each API call times out after 120 seconds; there are no automatic POST retries.
Polling waits at least ten seconds between MiniMax queries and has an explicit
wait limit (an in-flight API call may finish after that limit). Failed, cancelled
or terminal empty results stop polling. Reservations remain committed until
evidence-based reconciliation, including on explicit HTTP rejection. Usage is
saved as evidence; it is not automatically presented as an invoice or refund.

If a POST's response is lost, inspect the provider's recent tasks:

```sh
npm run film -- minimax-tasks
npm run film -- minimax-tasks 2
```

This is an explicit read-only API call, not a generation. MiniMax query/list
endpoints cover the last seven days. Match the task using provider records and
the local attempt journal; the API response cannot prove prompt identity for you.
Then attach the known task with a written evidence note:

```sh
npm run film -- recover-minimax data/workspace/my-film-v1 S01 TASK_ID "Evidence linking this task to this attempt"
npm run film -- poll data/workspace/my-film-v1 S01
```

Recovery checks the request fingerprint, model, resolution and duration. It
requires an existing reservation and never submits another generation. If a crash
saved the task ID in the local journal but missed the ledger update, repeating the
identical submit repairs the ledger without a POST. An existing unrecorded output
is preserved for inspection; the tool will not overwrite it.

## Validation and sources

`npm test` builds and runs the offline suite, including pricing, input validation,
budget guards, uncertain submissions, duplicate prevention, recovery, task
decoding, credential isolation, downloads and CLI integration.

- [Create task and input contract](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)
- [Query task](https://platform.minimax.io/docs/api-reference/video-generation-v2-query)
- [List tasks](https://platform.minimax.io/docs/api-reference/video-generation-v2-list)
- [Model guide](https://platform.minimax.io/docs/guides/video-generation)
- [Direct API pricing](https://platform.minimax.io/docs/guides/pricing-paygo)
