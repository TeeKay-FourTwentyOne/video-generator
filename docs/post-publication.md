# Post-publication workflow

Entry point: [shared post-publication skill](../.agents/skills/post-publication/SKILL.md).
The four required outcomes are updated documentation, reviewed source commit and
push, a verified local archive, and a process improvement. Standard archive
retention keeps the final 4K edit and original sources, and removes superseded
edit renders and mixes after verification. This does not upload the film, edit a
platform description or buy generations.

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
   brief. Keep the workspace state `active` while synchronizing description
   copies in the next step; the synchronization helper requires that state.
   Once synchronization and local metadata are complete, use `archive-planned`
   with the active locator until the move succeeds.
   Prices and monetary figures stay in ignored local accounting. Do not copy raw
   runtime JSON into Git; [source privacy](source-privacy.md) defines the boundary.
2. Preserve old local description/delivery records in a dated release folder,
   then synchronize the current description copies and SHA-256 values. Record
   publication as a later event; do not turn earlier technical checks into
   retrospective artistic approval. Keep version history and media unchanged
   until the separate checked retention step below.
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
   Run `npm run clips -- analysis process-project PROJECT_ID`, followed by
   `npm run clips -- analysis process-project PROJECT_ID --check`, for all project
   clips, including unused takes and local renders. This uses the explicitly
   provisioned local profile and verifies immutable private library evidence;
   film-specific QA alone does not satisfy it. Resolve missing/failed required
   passes before marking closeout complete. Preserve model review states and
   optional pending passes. Run authorized private cloud sync after this step
   with `npm run clips -- cloud sync --project PROJECT_ID`, so unrelated missing
   media cannot block the named film. Confirm its own scoped receipt with
   `npm run clips -- cloud status --project PROJECT_ID`. This mirrors the clip
   library inputs and analysis; the sealed workspace archive is a separate local
   artifact, including the finished film and standalone audio.
5. Stop only the named project's writers and preview servers. Choose final names
   for documentation snapshots and finish local metadata **before** hashing. A
   running generator, renderer or watcher can invalidate the snapshot.

## Move and verify one project

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
There is no cross-device copy/delete fallback. The move itself removes no files. An existing
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
then apply the standard retention step below and record its new inventory hash.
Regenerate current views. `npm run records -- validate PROJECT_ID
--local-evidence` checks declared artifact hashes, dimensions, decoded frame
counts, description copies and the archive inventory; explicitly removed
intermediates must be absent and are not counted as newly decoded. It records no
new approval.

Keep any new Git/privacy logs or release receipts outside the sealed tree, for
example under ignored `data/release-receipts/<slug>/`. Do not run a QA script that
rewrites archived evidence. Future edits start from a verified copy in a new
workspace. Outside the checked retention transaction, preserve the archive as it
was closed out. Original source takes, including rejected takes, are retained.

## Standard retention: final 4K plus sources and records

The director's standing policy is to delete intermediate edits at archival and
keep the final 4K version. Apply this to the named project without asking again.
Respect a narrower retention instruction. If the exact final 4K is missing or
ambiguous, preserve the media and resolve that issue before deletion. Do not use
a filename alone to decide which master to retain, and do not clean older or
unrelated archives as part of another film's closeout.

Keep the final 4K file byte-for-byte, its delivery/description/review package,
original generated shots and rejected source takes, original music and effects
stems, reference images, recipes, edit decisions, provenance, ledgers and QA.
Remove superseded full edits (including native review exports), debug copies,
assembly segments, unused finishing candidates and derived complete soundtrack
mixes. Keep reusable title/shot assets and original or processed source stems.
The cleanup command accepts video derivatives under `final/` and `finish/`, and
`soundtrack*.wav|flac|mp3|m4a` under `edit/`; it never recursively deletes a version
folder. Custom editor derivatives require an exact reviewed path, its SHA-256,
and a `derivativeClass` on that removal item. Supported classes are `render-cache`
for videos under `renders/`, `qa-render` for videos under `qa/`, and `complete-mix`
for `master*`, `soundtrack*` or `mono-test-*` audio files directly under `audio/`.
Original/source paths, per-shot stems, metadata and other locations remain
protected. These classes are review assertions, not permission to select every
file in a directory: retain reusable shot/title assets and inspect dependencies.

Inspect transitive dependencies before selecting files. A deleted render may be
an input to a later recipe: retain the source inputs and recipes, and document
the order in which missing derivatives must be rebuilt in a new working copy.
Do not promise a qualified or byte-identical rebuild without testing one. If a
derivative is the only surviving source for the final edit, retain it and explain
the dependency. Keep historical hashes, delivery records and review events even
when their media is removed; past checks remain historical facts.

For an extended location, a removal item takes this form:
`{ "path": "renders/cache/pass.mp4", "sha256": "<reviewed SHA-256>", "derivativeClass": "render-cache", "reason": "Regenerable intermediate; source and recipe retained" }`.
The helper carries the class and verified hash through planning, quarantine,
resealing and purge. A missing or mismatched reviewed hash stops the operation.

Use the maintained helper with an explicit selection in ignored storage:

```json
{
  "schemaVersion": 1,
  "slug": "my-film-v1",
  "master": { "path": "final/v5-4k/film.mp4", "sha256": "<verified SHA-256>" },
  "dependencyReview": "Original inputs and recipes retained; regenerate native derivatives before finishing in a restored copy.",
  "remove": [
    { "path": "final/v4/film.mp4", "reason": "superseded edit" },
    { "path": "final/v4/segment-01.mp4", "reason": "assembly render" },
    { "path": "edit/soundtrack-v1.wav", "reason": "derived mix" }
  ]
}
```

```sh
node tools/production/archive-retention.mjs plan data/release-receipts/my-film/selection.json > data/release-receipts/my-film/retention-plan.json
node tools/production/archive-retention.mjs apply data/release-receipts/my-film/retention-plan.json data/release-receipts/my-film/retention
node tools/production/archive-retention.mjs purge data/release-receipts/my-film/retention
node tools/production/archive.mjs verify my-film-v1
```

Stop the project's writers/servers before planning. Inspect the exact paths and
hashes in the plan. The helper requires a verified existing seal and a matching
4K master. Apply fully decodes that master, rechecks the plan, moves only listed
files to a private quarantine outside the archive, verifies every retained byte
and permission, and writes a new seal. The original manifest and removal journal
remain in the receipt. Purge rechecks the new archive and quarantined hashes,
then deletes only the listed files; it is resumable. This transaction is an
intentional archive revision, not permission to reseal an unexplained mismatch.

An apply failure rolls back completed moves when possible. If interrupted,
inspect `transaction.json`, both manifests and exact file locations. Never delete
the receipt or blindly retry apply over it. Resolve a partial move by restoring
the listed quarantined files without overwriting conflicts and verifying the old
seal, or complete the verified transaction deliberately. Purge refuses an archive
that has changed. Keep the lock until an interrupted writer is confirmed stopped.
The old `.claude/skills/archive-workspace/prune.py` remains historical and must
not be used; it does not enforce this preservation and receipt contract.

After success, update `production.json` with the new archive inventory hash and
`retention: "removed-intermediate"` on removed video artifacts. Omitted retention
means retained, so a missing file can never silently pass local verification.
Keep their version, path, hash, frame data and review events. Historical preview
pages are evidence of the old versions; only retained deliveries remain playable.
Check the final master and its current links, run record validation, and report
the number of removed files and logical bytes reclaimed. Keep later receipts
outside the newly sealed archive. Source-clip deletion is a separate workflow.

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
