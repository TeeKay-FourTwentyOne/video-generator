# Production records

Use `briefs/<stable-project-id>/` for new public production documentation.
The ID survives different edits and workspace versions. A project's `brief.md`
holds creative intent; `production.json` holds current public facts; the
`README.md` and [project index](../briefs/README.md) are generated views.
The schema is [production-record.schema.json](schemas/production-record.schema.json).

Add `description.md` only when publication wording exists. It is the one editable
source for exact wording and credits. Add `decisions.md` or `handoff.md` only when
there is useful content. List additional scripts, research, scene notes and edit
recipes in `supportingDocuments`, with a label and a repository-relative path to
a Markdown or JSON source inside the project folder. These documents receive
the same privacy and link checks and appear in the generated project summary.
Series canon and character assets keep their existing
locations; link them with `seriesId` and `seriesPath` rather than copying them.

## Public facts and private evidence

Public records allow only stable identity, status, document paths, explicit
artifact roles/versions/hashes, actual provider/model names, role/model/harness
credits, publication evidence, review events, archive integrity and legacy links.
Unknown schema fields fail at every nesting level. Missing knowledge stays absent
or explicitly unknown; do not select a status by guessing from a filename.
Use `statusNote` for a concise explanation of incomplete or conflicting history.

Prices, budget amounts, spending totals and itemized accounting **never enter
Git-bound documentation or public records**. Keep those in ignored `data/`, along
with provider/account identifiers, raw prompts and operation records. The exporter
projects a reviewed object through an allowlist; it does not redact a raw runtime
object after serialization. A pattern check catches common monetary text and
PII/secrets; manual review remains necessary.

The workspace remains authoritative for edits, usage, source hashes and QA. The
public record summarizes evidence and is not a writable budget or an approval
mechanism. A technical pass cannot change status or create listening/approval
events. `supplied-processing` does not permit `published`; publication requires
its own matching dated event. When a retained release record identifies the local
master, bind both the publication and event to that artifact's version and hash.
Older publication evidence may identify only a supplied URL: omit the artifact
association in both places and leave every `publishedMaster` flag false. The
generated summary makes the missing association explicit. Do not infer it from
the latest or largest local file. All other review events require an artifact
version and hash. The local hash never identifies a platform transcode. Recording dates and event or
platform publication dates are separate; omit unknown event dates.

Artifact paths are relative to the recorded workspace. Documents and the archive
manifest use repository-relative paths. Keep the active path while the workspace
is `archive-planned`; change to `archived-verified` only after the existing archive
helper succeeds. Every video artifact has integer frames, rational fps and a
duration derived from them, plus a role such as `native-review`, `phone-review`
or `finishing-master`. `publishedMaster` is explicit, never chosen by recency.
Use `archived` for a known legacy archive locator without claiming a fresh
inventory verification. It remains read-only and carries no `archive` verification
object; `archived-verified` still requires the existing helper's complete evidence.

## Create, export and check

Review a small schema-shaped JSON candidate under ignored storage. Record only
evidence you have checked; copy no whole delivery, ledger or provider objects.
Use the two migrated pilots as examples: [published VERIFY](../briefs/verify/production.json)
and [unfinished Episode 05](../briefs/scary-woods-episode-05/production.json).
The latter has no description or publication placeholder.

```sh
npm run records -- export data/workspace/my-film-v1/public-record.json --dry-run
npm run records -- export data/workspace/my-film-v1/public-record.json
npm run records -- build
npm run records:check
npm run records -- list --status=review
npm run records -- list --title=verify
npm run records -- list --series=scary-woods
```

Create the canonical brief and any description before export. Source validation
checks their links and exact description hash without credentials, network calls,
compiled provider modules or ignored media. Paths reject traversal, absolute
paths and symlinks. Canonical descriptions must end with the repository URL.
Publication URL validation currently supports HTTPS YouTube and Vimeo links.

`build --dry-run` reports view changes without writing. `build --check` fails on
drift. `export --check` checks the canonical serialization without writing.
Export does not rewrite prose, synchronize media, commit, push or set approval.
Repeated export/build is deterministic. Review financial/privacy boundaries in
prose as well as JSON before source publication.

When media is available, opt into the heavier, read-only check:

```sh
npm run records -- validate verify --local-evidence
```

It checks each declared video hash, decoded frame count, dimensions and rational
fps using ffprobe, then description copies/delivery hashes and the complete
archive inventory through `archive.mjs`. It does not rewrite a seal or QA record,
perform listening, replace artistic review or make provider calls.

## Synchronize publication text before sealing

For each delivery with publication text, record its workspace-relative
`descriptionCopyPath` and `deliveryRecordPath`. They identify the `description.txt`
and `delivery.json` beside that artifact. When the canonical text changes:

```sh
npm run records -- sync-description PROJECT_ID --dry-run
npm run records -- sync-description PROJECT_ID
npm run records -- build
npm run records -- sync-description PROJECT_ID --check
```

The command preserves previous copies, delivery metadata and the previous public
record under the active workspace's `notes/description-sync/`, writes the exact
canonical bytes to declared copies, and updates their hashes. Other delivery
fields are preserved. Stop project writers first. If interrupted, inspect the
snapshot and rerun the dry run; no media regeneration is involved.

Archived and sealed workspaces are read-only. Later source wording changes can
be published as a new documentation revision, but must not overwrite the archived
historical wording. A mismatch remains visible; restore a working copy for a new
delivery. Human forwarding pages do not replace text inputs to old recipes; see
[VERIFY's restore note](../briefs/verify/decisions.md#restoring-historical-recipes).

## Itemized local accounting

Keep one explicit source map at `data/accounting/<project-id>/sources.json`:

```json
{
  "schemaVersion": 1,
  "projectId": "my-film",
  "asOf": "2026-10-12",
  "sources": [
    {
      "path": "data/workspace/my-film-v1/budget.json",
      "kind": "budget-v1",
      "basisByEntry": { "S01-v1": "reported-usage", "anchor-v1": "estimate" }
    }
  ]
}
```

Include all project ledgers, including related auditions, once each. For each
reconciled entry, review its saved evidence and supply a `basisByEntry` value of
`reported-usage`, `invoiced` or `estimate`. Unclassified reconciliation stays
explicitly unresolved; the helper never infers invoice confirmation from a
status flag or converts a token estimate into a confirmed charge. The helper
also recognizes legacy allocation records as
`episode-allowances-v1`; other formats need an explicit adapter, not guessed
conversions. Keep existing ledgers in place, including sealed archives.

```sh
npm run accounting -- data/accounting/my-film/sources.json --dry-run
npm run accounting -- data/accounting/my-film/sources.json
npm run accounting -- data/accounting/my-film/sources.json --check
```

The derived, ignored `summary.json` retains each source hash, ledger entry ID,
category/model, purpose, available usage units and billing evidence. It separates
confirmed amounts, estimates, pending reservations, allocations and unknown billing; failed
or uncertain attempts retain their reservations. Partial confirmed totals are
explicitly incomplete. A reconciled provider-usage amount is not necessarily an
invoice. Unknown billing never becomes a zero charge. Account balances are not
included. Source duplication and repeated provider operations fail instead of
being double-counted. Changed summaries retain earlier copies under `history/`.
The helper does not change ledgers, limits, permissions or financial authority.

## Migration and lifecycle

The 2026-10-12 migration covers 106 older documents in 70 additional project
folders, alongside the original VERIFY and Scary Woods Episode 05 pilots. Flat
Markdown paths are forwarding pages, not independently editable copies. Shared
Scary Woods canon and subtitle conventions keep their original locations.
The Meridian House JSON recipe moved to `briefs/meridian-house/edit.json`; its
documented CLI caller now uses that path.

The complete original documents, initial worktree state, document map, financial
sections and verification receipts are retained under ignored
`data/release-receipts/briefs-migration-2026-10-12/`. Existing standalone
description bytes are preserved. Embedded descriptions were separated from
their briefs, with personal credits omitted from draft publication text;
drafts remain identified as drafts, missing credits were not
invented, and the repository URL terminates each canonical description.
The two pilot records retain their existing review/publication facts.

Archived scripts that copy or rewrite old brief paths have explicit restore notes
in their project's `decisions.md`. Human forwarding pages are not text inputs to
assembly scripts. For historical wording, use the archived document copies or
the exact pre-migration snapshot; change dependencies only in a restored working
copy. No media, workspace ledger or sealed archive was changed by this migration.

For future migrations, inspect inbound links and recipe text reads, preserve a
local snapshot, and update callers or leave explicit restore instructions before
moving a document. Keep unsupported fields absent and uncertain statuses explicit.

The shared [production workflow](production.md) creates and updates records;
[post-publication](post-publication.md) synchronizes text before archive sealing,
adds the publication event, verifies the archive and leaves later Git receipts
outside it. Source commit/push still follows [source privacy](source-privacy.md)
and requires its own authorization. No command here publishes source or video.
