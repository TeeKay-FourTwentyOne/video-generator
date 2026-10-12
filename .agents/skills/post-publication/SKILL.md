---
name: post-publication
description: Close out a published film in this repository. Use for a post-publication wrap-up, recording a supplied publication URL and final description, updating production documentation, committing and pushing reviewed source, archiving the project workspace, and suggesting a process improvement.
---

# Close out a published film

Follow `docs/post-publication.md` from the repository root. Read `AGENTS.md` and
`docs/source-privacy.md` before source publication. This is the shared workflow
for Codex and Claude Code; `.claude/skills/post-publication/SKILL.md` links here.

Complete and report all four outcomes: **documentation, source commit/push,
workspace archive, and a concrete process improvement**. Order them to keep
records accurate. A request to perform this complete workflow authorizes these
four actions for the named film; do not ask again for authorization already given.
Honor any narrower instruction, such as “do not push.” A bare URL outside an
established wrap-up request is not authorization for unrelated source changes.

Identify the film, exact released version, publication evidence and user-edited
description. A user-supplied URL can be recorded as user-confirmed without waiting
for crawler access. Distinguish that from an independently verified public page
or a URL still processing. Preserve the user's wording and credits; do not
replace them with the agent's earlier draft. Never invent a URL, publication date,
artistic approval or listening claim. Publication copy ends with the repository
URL required by `AGENTS.md`.

Update the current status and artifact pointers, retaining the original creative
intent and revision history. Keep credentials, account/task IDs, raw provider
records, logs, media and machine-specific paths in ignored storage. Reconcile
project cost separately from provider account balance. Synchronize current local
description copies and their hashes before sealing the archive.

Follow `docs/production-records.md`: update the allowlisted public record and
generate its current summary/index. Keep prices, monetary amounts and detailed
accounting in ignored `data/`. Use `sync-description` on the active workspace
before sealing; use check mode afterward. Public status, publication evidence,
technical checks and artistic approval remain separate facts.

Archive exactly one inactive project with `tools/production/archive.mjs`:
inspect `plan`, run `apply`, then `verify`. Preserve sources, rejected takes,
native exports, earlier versions, recipes, ledgers and QA. Stop only that
project's writers/servers first. Check external dependencies and current review
links. Do not prune, move other workspaces, overwrite a destination, or rerun paid
generation to reconstruct missing records. Cleanup is a separate, explicitly
scoped request. Treat a completed archive as sealed; keep later release receipts
outside it.

Manually review exact source changes, run relevant checks and the repository
privacy gates, commit as TK-421 with the current agent's allowed attribution, and
verify the pinned SSH account, outgoing commits and pushed ref. Preserve unrelated
working-tree changes. If source publication fails, retain the verified archive
and report the remaining step; do not claim all four outcomes complete.

Leave one useful improvement tied to an observed production issue. Implement a
small authorized repair when appropriate; write a fresh-session handoff for larger
changes. Label shared production issues separately from dated harness observations.
Finish with the publication/brief links, source commit, archive verification,
privacy scope, improvement and any real remaining limitation.
