# Architecture and compatibility

The repository has three useful layers: provider primitives, local production
tools, and film-specific recipes. The October review adds a small maintained path
through those layers, without moving media or rewriting old projects.

```text
Codex / Claude Code / another local agent
      |                         |
      | shell CLI               | MCP production_* wrappers
      +------------+------------+
                   v
         tools/production/film.mjs
           | plan / quote / submit / poll
           | edit / delivery / review
           v
  MCP package production/ledger.ts + production/veo-spec.ts
           |
           v
  existing clients/veo.ts and Google authentication
```

The ledger owns the all-in spend limit and attempt identity. The provider adapter
owns request validation, transport, and terminal-state decoding. The film manifest
owns narrative intent and constraints. The edit owns exact frame ranges and source
hashes. The acceptance record owns the decision to use those frames. None of these
records substitutes for the others.

## Maintained production path

- `tools/production/film.mjs`: JSON commands, project-local paths, explicit network
  operations, source acquisition and metadata. It loads compiled MCP modules, so
  build after editing TypeScript.
- `production/ledger.ts`: exclusive writer lock, atomic file replacement, integer
  money, no implicit reset/retry/refund. Ambiguous submissions are retained.
- `production/veo-spec.ts`: qualified GA capabilities and dated rates. This is the
  common quote used by the client and plan command.
- `tools/production/google-image.mjs`: bounded version of the already-used Google
  image route, preserving references, usage and output hash.
- `tools/production/edit.mjs`: hard-cut, frame-addressed local edits and a prepared
  soundtrack. Refuses changed sources, missing acceptance, out-of-range trims and
  existing output versions. Full decode and actual frame counts are checked.
- `src/tools/production.ts`: MCP wrappers invoke the same CLI; no duplicate
  state machine or separate interpretation of the budget.
- Default MCP profile: nine production tools and read-only configuration presence.
  `VIDEO_MCP_PROFILE=legacy` restores the full specialist catalog on restart.
  This reduces tool selection ambiguity and keeps unqualified paths out of new films.

## Existing useful specialists

`tools/scene-lab/` is the persistent geometry/camera sandbox. Frame/anchor QA,
`clip-qa`, `clone-check`, seam tools, captions, audio analysis and the finishing
recipes remain useful when a shot needs them. Their dependencies and billing
behavior differ: inspect the relevant tool before use. Paid legacy helpers require
an allowance; the shared ledger cannot intercept arbitrary shell/network code.

Film-specific tools such as Forest Spirit, Carnival Dream, Hall of Memories and
Angles retain their original paths because archived recipes depend on them. Do
not flatten or rename them merely for visual tidiness. Promote a mechanism into
the shared path when a second real production demonstrates the need.

## Legacy paths and deliberate compatibility changes

- `execute_project` used to buy prompt generation and submit whole projects without
  a common budget. It now fails before paid work. Its original implementation is
  retained in the module for migration reference. Convert projects to an explicit
  `film.json` plan; do not bypass the client guard.
- Existing `create_job` and `submit_veo_generation` callers must now pass a budget
  and stable request ID. Bare model aliases resolve to GA rather than dead previews.
  These tools are in the explicit legacy profile; `production_submit` is the default.
- Old jobs remain in their original ignored store. Writes are atomic, polling is
  bounded, and `resume_job` can continue an existing operation after interruption.
  The old global job store is not a multi-process queue; use per-film operations
  for new productions.
- `src/agents/`, `public/`, `realtime-narrative/` and `stegasus/` are preserved
  experiments/legacy applications, not a required modern agent harness. Some SDK
  agents expect HTTP application endpoints not served by this MCP process.
- `mcp/veo-clips-mcp/` is a separate catalog/search server; it is not the submission
  authority. Its existing configuration is preserved.
- Detailed Claude rules moved to `docs/craft/`; their former locations contain
  short routing notes. The canonical production skill lives under `.agents/skills`
  with a Claude-compatible link. Historical bulk-workflow documents live in
  `docs/legacy/` and are not production instructions.

The root agent instructions contain operating boundaries, not a model-specific
persona or an exhaustive tool catalog. This follows current official guidance on
[small, task-relevant Codex instructions](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra),
[repo skill discovery](https://learn.chatgpt.com/docs/build-skills), and
[concise Claude Code context](https://code.claude.com/docs/en/best-practices).

## Boundaries still worth improving

Several legacy services build shell command strings, use global mutable state,
or make unbudgeted non-Veo calls. The new editor uses argument arrays and immutable
versions; it does not certify those old services as hardened. Future work should
migrate one exercised service at a time, with an offline failure test and a film
that demonstrates the benefit. No new provider client is justified by research
alone. Storage cleanup requires a dependency/hash audit and separate authorization.
