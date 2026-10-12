# Post-publication workflow

Entry point: [shared post-publication skill](../.agents/skills/post-publication/SKILL.md).
The four required outcomes are updated documentation, reviewed source commit and
push, a verified local archive, and a process improvement. This does not upload
the film, edit a platform description, buy generations, or delete intermediates.

## Establish the release

Read the current brief, user-edited description, latest delivery record and
project notes. Identify the exact published version, its SHA-256, format,
integer frame count and duration. If the version is genuinely ambiguous, resolve
that before marking an artifact as published; continue independent documentation
work meanwhile. Retain earlier creative intent under an explicit historical label.

Use a supplied or independently verified publication URL. Record the evidence:
`user-confirmed`, `public-page-verified`, or `supplied-processing`, as appropriate.
The date the user supplied it is a **recording date**, not necessarily the platform
publication date. A failed web fetch does not invalidate a user's confirmation.
Do not claim the local master hash matches the platform transcode.

Use the user's final description as the source of truth. If only a URL was
supplied and the requested changes cannot be recovered locally or from the page,
ask for the missing text; do not silently publish an old draft. Keep credit order,
hashtags, related links and wording. Every publication description ends with:
https://github.com/TeeKay-FourTwentyOne/video-generator

## Prepare documentation and the workspace

1. Update the canonical `briefs/<project-id>/production.json` from approved
   evidence: status, URL, exact released version, description hash and archive
   state. Generate the current README and index using
   [production records](production-records.md); retain original intent in the
   brief. Keep the active locator with `archive-planned` until the move succeeds.
   Prices and monetary figures stay in ignored local accounting. Do not copy raw
   runtime JSON into Git; [source privacy](source-privacy.md) defines the boundary.
2. Preserve old local description/delivery records in a dated release folder,
   then synchronize the current description copies and SHA-256 values. Record
   publication as a later event; do not turn earlier technical checks into
   retrospective artistic approval. Keep version history and media unchanged.
   `npm run records -- sync-description PROJECT_ID --dry-run` previews exact
   copy/hash changes; apply without the flag while the workspace is active.
   The helper preserves prior copies. After sealing, use `--check` only.
3. Check ledger entries and operation records for unfinished work. Reconcile
   known costs, retaining unresolved reservations. Do not query a provider or
   resubmit a generation merely to archive. If work is still writing, defer that
   workspace move and record what remains. Account credit is not film spend.
   Keep all contributing ledger paths in ignored
   `data/accounting/<project-id>/sources.json`, including earlier auditions.
   `npm run accounting -- data/accounting/PROJECT_ID/sources.json` produces a
   granular local report without changing the ledgers or making provider calls.
4. Inventory dependencies before moving: source copies, edit/QA paths, scripts,
   font files, external source references and imports. Note what is self-contained
   and what requires the repository, tools or another local archive. A preserved
   folder is not automatically a qualified standalone rebuild. Prefer relative
   paths for new recipes. For historical hardcoded roots, document a restore-copy
   procedure rather than silently modifying the old evidence.
5. Stop only the named project's writers and preview servers. Choose final names
   for documentation snapshots and finish local metadata **before** hashing. A
   running generator, renderer or watcher can invalidate the snapshot.

## Archive one project intact

The helper requires Node 22+ on a POSIX filesystem and an existing
`data/workspace/<slug>/`. It has no network or package dependencies. Run from the
repository root, with one slug, never the entire workspace directory:

```sh
node tools/production/archive.mjs plan my-film-v1
node tools/production/archive.mjs apply my-film-v1
node tools/production/archive.mjs verify my-film-v1
```

`plan` is read-only and summarizes the inventory. `apply` takes a local archive
lock, writes `workspace-archive-manifest.json`, checks the source again, renames
the whole project to `data/workspace-archive/<slug>/`, and verifies the destination.
All hidden files, earlier exports, native masters, takes, sources, recipes,
ledgers and QA remain. The manifest inventories content hashes, byte sizes,
permissions and directories; it excludes only itself. It detects later additions,
deletions, same-size edits and permission changes. It is an integrity record,
not a signature, dependency resolver or remote backup.

Existing destinations, symlinked paths and special files are refused. Resolve
dependencies deliberately; do not delete links just to make the command pass.
There is no cross-device copy/delete fallback. No pruning tool runs. An existing
empty destination is also a collision, not permission to reuse it. For an already
completed archive, run `verify`; do not create a numbered duplicate.

If a move fails, the source and seal remain for inspection; fix the cause and retry
only if verification still passes. If the process was interrupted, inspect both
paths and active processes before removing a stale `data/.workspace-archive.lock`
or an empty reservation. Never discard a nonempty destination. A post-move
verification failure leaves the destination intact for investigation. Report the
failure and locate the changed content; do not regenerate or replace the manifest
just to erase a mismatch.

After archival, verify the master hash, full decode and current delivery links
from the new location. Restart the loopback review server at the archive path if
continued review is useful; it serves `description.txt` along with the known
review artifacts. Inspect the generated links, not just the server's exit code.
Mark the public record's archive locator verified only after these checks pass,
and regenerate its current views. `npm run records -- validate PROJECT_ID
--local-evidence` checks declared artifact hashes, dimensions, decoded frame
counts, description copies and the archive inventory. It records no new approval.

Keep any new Git/privacy logs or release receipts outside the sealed tree, for
example under ignored `data/release-receipts/<slug>/`. Do not run a QA script that
rewrites archived evidence. Future edits start from a verified copy in a new
workspace. Preserve the archive as it was closed out. Optional disk cleanup
requires a separate explicit scope and a dependency review; native masters and
rejected takes are never implicitly disposable.

## Commit and push source

Follow [the complete privacy procedure](source-privacy.md); these are checkpoints,
not replacements for that document:

1. Review the in-scope diff, description and metadata manually. Run the build and
   tests appropriate to any tooling changes. Preserve unrelated changes.
2. Enable the existing repository hooks. Run `privacy:worktree`, stage explicit
   reviewed paths, then run `privacy:check`. Review the actual staged diff.
3. Commit as the policy's TK-421 author **and** committer, with the active agent's
   permitted co-author trailer. Check the message as well as file content.
4. Fetch origin, inspect outgoing commits/files, run `privacy:outgoing`, and
   verify the pinned SSH command authenticates as TeeKay-FourTwentyOne.
5. Push the authorized ref, verify the remote SHA and final working tree, and
   record a receipt outside the archive. An accepted source push does not back up
   ignored media. If push fails, retain the archive and local commit, report the
   exact remaining action, and resume without repeating completed steps.

An explicit wrap-up request or an earlier commit/push instruction covers these
in-scope actions. Respect narrower directions. Do not add a redundant approval
gate, stage another project's work, bypass a failed privacy check, or upload media.

## Improve and report

Pick an observed friction point: stale descriptions, confusing version status,
hardcoded recipe roots, unreconciled costs, broken review links or unclear QA
claims. State the impact and a concrete change. For a larger change, leave a
handoff with target files, steps, compatibility/privacy boundaries and acceptance
checks. [Production-record organization](production-records-proposal.md) records
the completed pilot and remaining staged migration. Shared production behavior
belongs in shared docs;
harness-specific findings belong in dated `docs/harness/` notes and must identify
which harness was actually observed.

Report all four outcomes with links, commit/ref verification, archive counts and
hash verification, privacy scope and anything intentionally left local. Never
label the workflow complete while a requested step remains unresolved.
