# Video Generator

An agent-operated film workshop: plan a scene, generate only the motion it needs,
edit locally, and deliver an inspectable native-resolution film. Codex and Claude
Code share the same production contract and tools.

The October 2026 baseline is **Borrowed Light**, a portrait mechanical fable made
while reviewing the repository. See its [brief](briefs/borrowed_light_brief.md),
[review findings](docs/repository-review-2026-10.md), and
[provider research](docs/video-model-options-2026-10.md).

## Start here

Use existing dependencies (Node 22+, FFmpeg/ffprobe). These commands do not install
libraries or call generation providers:

```sh
npm run build
npm test
npm run film -- doctor
npm run film -- help
```

For an authorized film, follow [the production workflow](docs/production.md).
It provides one all-in budget, stable shot/request IDs, bounded provider calls,
recoverable polling, source hashes, reviewed frame ranges, versioned edits and a
local review player. `npm run film -- plan WORKSPACE` is a dry run. Only explicit
submission/image commands buy new media.

MCP now defaults to ten focused tools. Existing specialist callers can set
`VIDEO_MCP_PROFILE=legacy` in their server environment and reconnect. The CLI
works directly for Codex, Claude Code and other agents with local file access.

## Where things live

| Path | Purpose |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` | Short shared operating rules and Claude import |
| `.agents/skills/produce-video/` | Canonical production skill; Claude links to it |
| `tools/production/` | Agent CLI, local editing, review and offline tests |
| `mcp/video-generator/src/production/` | Budget and qualified provider specifications |
| `mcp/video-generator/src/clients/` | Existing Google, Anthropic and ElevenLabs clients |
| `mcp/video-generator/src/tools/` | MCP tools, including wrappers around the same CLI |
| `docs/craft/` | On-demand continuity, dialogue, FFmpeg, editing and QA guidance |
| `docs/craft/field-notes/` | Dated, attributed production lessons; any agent appends |
| `docs/harness/` | Per-agent harness notes (Claude Code, Codex) |
| `tools/scene-lab/` | Persistent local 3D scenes and camera experiments |
| `tools/` | Specialized local/QA helpers and preserved production recipes |
| `briefs/`, `characters/`, `series/` | Sanitized intent, character canon and series craft |
| `data/workspace/<slug>/` | Ignored film assets, budget, operation records, edits and QA |
| `data/workspace-archive/<slug>/` | Preserved older productions |

[Architecture and compatibility](docs/architecture.md) distinguishes the maintained
path from historical bulk executors, SDK agents and experiments. Existing media
and prior production directories are not moved by the new tools.

[Pricing](PRICING.md) records the qualified Google rates and accounting limits.
Other providers are research options, not enabled integrations. Source publication
is a separate checkpoint with [mandatory privacy checks](docs/source-privacy.md).

## Tests

`npm test` covers paid-request refusal/recovery and local production contracts.
`npm run test:local` also runs the existing scene-lab and privacy suites. Tests do
not submit provider jobs. Full creative review still requires inspecting the film.

MIT license.
