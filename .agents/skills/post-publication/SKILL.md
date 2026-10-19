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

Before closeout, run `npm run clips -- analysis process-project PROJECT_ID`, then
repeat with `--check`, covering unused takes and local renders too. Resolve
missing/failed required passes; film-specific QA does not replace library analysis.
Use the provisioned local default profile and preserve raw evidence privately.
Extraction completion does not establish human semantic review; see
`docs/clip-analysis.md` for completion states and recovery.

Follow `docs/production-records.md`: update the allowlisted public record and
generate its current summary/index. Keep prices, monetary amounts and detailed
accounting in ignored `data/`. Use `sync-description` on the active workspace
before sealing; use check mode afterward. Public status, publication evidence,
technical checks and artistic approval remain separate facts.

Archive exactly one inactive project with `tools/production/archive.mjs`:
inspect `plan`, run `apply`, then `verify`. Standard retention keeps the final 4K
master and removes superseded edits, debug/segment renders, earlier finishing
candidates and derived soundtrack mixes. Use `archive-retention.mjs` with an exact
reviewed list and the dependency checks in `docs/post-publication.md`. The user's
standing archive policy authorizes this cleanup for the named project; do not
ask again unless scope or the final master is genuinely ambiguous. Preserve
original shots, rejected source takes, audio stems, references, recipes, edit
decisions, historical delivery metadata, ledgers and QA. Stop only that project's
writers/servers first. Verify the master, retain the original seal and removal
receipt outside the archive, verify the retained inventory before purging, then
update the public archive hash and mark removed renders explicitly. Do not clean
other workspaces, overwrite a destination, or rerun paid generation. If no final
4K exists, preserve the media and record that retention cleanup is deferred.
Future edits use a restored copy; unrelated archive writes remain prohibited.

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
