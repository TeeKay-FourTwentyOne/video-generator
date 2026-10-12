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

After publication, use the shared
[post-publication skill](.agents/skills/post-publication/SKILL.md) and
[close-out workflow](docs/post-publication.md). They cover final documentation,
reviewed source commit/push, intact workspace archival and a process improvement.
The [production index](briefs/README.md) links validated current records. The
[record workflow](docs/production-records.md) separates creative intent, exact
publication text and dated production evidence. All project briefs now have
canonical folders; old Markdown paths forward to them. Shared series canon stays
in place, and incomplete historical metadata remains explicitly unknown or absent.

The [shared clip library](docs/clip-library.md) catalogs existing footage by content
hash, with public prompts, descriptions, characters and evidenced edit uses.
Start with `npm run clips -- search QUERY`; originals stay in ignored `data/clips/`.

MCP now defaults to eleven focused tools. Existing specialist callers can set
`VIDEO_MCP_PROFILE=legacy` in their server environment and reconnect. The CLI
works directly for Codex, Claude Code and other agents with local file access.

## Where things live

| Path | Purpose |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` | Short shared operating rules and Claude import |
| `.agents/skills/produce-video/` | Canonical production skill; Claude links to it |
| `.agents/skills/post-publication/` | Shared release wrap-up; Claude links to it |
| `tools/production/` | Agent CLI, local editing, review and offline tests |
| `briefs/<project-id>/` | Canonical brief, public record and generated current summary |
| `catalog/clips/`, `catalog/uses/` | Public clip metadata and evidenced usage records |
| `data/clips/` | Ignored shared originals, addressed by SHA-256 clip ID |
| `data/accounting/<project-id>/` | Ignored itemized accounting and reconciliation evidence |
| `mcp/video-generator/src/production/` | Budget and qualified provider specifications |
| `mcp/video-generator/src/clients/` | Google, MiniMax, Runway, Anthropic and ElevenLabs clients |
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
path from historical bulk executors, SDK agents and experiments. Production tools
leave prior media in place; the explicit archive command moves only its named
workspace intact after inventory and verifies it at the destination.

[Pricing](PRICING.md) records Google, MiniMax and Runway rates and accounting limits.
[MiniMax H3/H3 Max](docs/minimax.md) supports the same plan/submit/poll workflow;
its API contract is covered by offline tests, with live generation qualification pending.
[Runway Gen-4.5 / Gen-4 Turbo](docs/runway.md) uses the same ledger and workflow,
with native silent MP4 output and explicit reported-credit reconciliation.
Other providers remain research options. Source publication
is a separate checkpoint with [mandatory privacy checks](docs/source-privacy.md).

## Tests

`npm test` covers paid-request refusal/recovery and local production contracts.
`npm run test:local` also runs the existing scene-lab and privacy suites. Tests do
not submit provider jobs. Full creative review still requires inspecting the film.

MIT license.
