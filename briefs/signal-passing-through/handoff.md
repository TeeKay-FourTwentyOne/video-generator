# Next workflow improvement: explicit project identity

This production exposed an order-dependent identity bug: assembly before creation
of the public production record used the versioned workspace name as the project
ID. Later assembly found the stable ID. Provider polling independently assigned
the workspace name as the new clip's collection. The local repair and the
original twelve use records are preserved with the production evidence.

This is shared production behavior observed through Codex, not a harness-specific
failure. No production tooling changed during the film or its finishing pass.

## Proposed implementation

1. Add an explicit stable project ID to initialization in
   `tools/production/film.mjs` and the corresponding production MCP interface.
   Persist it in a versioned workspace metadata object separate from the budget.
2. Have `projectIdFor` in `tools/production/clip-import.mjs` prefer that explicit
   identity. Keep the existing public-record lookup and basename fallback for
   older workspaces; reject a conflict rather than silently choosing an identity.
3. Carry the same identity into assembly in `tools/production/edit.mjs` and into
   generation collections during polling in `tools/production/film.mjs`.
   Retain existing collection labels and stable use IDs. Do not rewrite historical
   catalogs, creation snapshots, sealed archives or old financial ledgers.
4. Document the setup order and compatibility behavior in `docs/production.md`.
   Keep machine paths and provider identifiers out of public source.

## Acceptance checks

- Two differently versioned workspaces initialized for the same project produce
  use records and new clip collections with the same stable project identity.
- Assembly before a public record exists has the intended project identity.
- Existing workspaces without explicit metadata retain their current behavior.
- Conflicting identities fail before catalog mutation; malformed IDs fail early.
- Completed polling remains idempotent and preserves creation snapshots exactly.
- Offline production tests and catalog/record checks pass without paid requests.

Until this is implemented, create the canonical production record before the
first real assembly and explicitly verify each new generation's collections.
