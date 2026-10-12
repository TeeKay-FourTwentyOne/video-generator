# Production records: implementation handoff

Status: schema, tooling, workflow integration and two pilots implemented
2026-10-12. See [the working record workflow](production-records.md) and
[generated project index](../briefs/README.md). VERIFY and Scary Woods Episode 05
have canonical project folders and legacy forwarding links. The subsequent
2026-10-12 pass migrated all older project documents into 70 additional folders;
shared canon remains in place. Existing media and unrelated work are preserved.

This handoff records the rationale and acceptance criteria. Prices and financial
figures remain in ignored local accounting, outside the public record contract.

## Problems worth solving

| Observed issue | Production consequence | Proposed remedy |
| --- | --- | --- |
| Flat `briefs/` mixes treatments, descriptions, research and handoffs with inconsistent filenames | A new session must infer which files belong together and which is current | A small project directory with one index and stable project ID |
| VERIFY's original spine described 39 seconds, Veo and no selection; the delivered film is 22.75 seconds, Runway and three selections | An old plan can be mistaken for the current edit | Separate original intent from an explicit current production record and dated decisions |
| User description changes diverged from local delivery copies and recorded hashes | Review pages or future uploads can use stale credits | One canonical publication text, synchronized copies with hashes, preserved earlier snapshots |
| Cost summaries can mix a completion ledger, earlier auditions and account credit | Apparent budget remaining can be mistaken for authorization or film cost | Project-wide reconciled spend plus explicit unresolved reserves; account balances stay local |
| Historical assembly recipes embed the active workspace path | Moving files can break rebuilds even when all media survives | Workspace-relative recipes for new work and a dependency/restore note for archives |
| Inconsistent archive instructions can discard earlier versions | A later edit can lose its source or another harness can follow different rules | Shared intact archival with a manifest; cleanup requires separate scope |
| Review page linked `description.txt`, but the server did not allow it | Final copy was unavailable through the review link | Exact filename allowlist repair and HTTP regression test, now implemented |
| QA records contain `artisticApproval: false` from delivery time alongside later publication | Technical evidence and subsequent user actions appear contradictory | Dated events: technical checks, review/approval evidence, finishing authorization and publication |

## Proposed source layout

Use one directory per stable project ID, rather than renaming everything into one
large Markdown file. A series can keep its existing canon in `series/` and link
episode project records. Do not duplicate canon or move character assets.

```text
briefs/
  README.md                    # searchable project index; generated from records
  verify/
    README.md                  # short current status and links
    brief.md                   # creative intent; historical sections labelled
    description.md             # exact final user-facing publication text
    production.json            # small, allowlisted public production summary
    decisions.md               # only if the revision history warrants it
    handoff.md                 # only for unfinished work
```

Keep the directory stable across edits (`verify`), with versioned workspace and
delivery IDs (`verify-film-v1`, `v4-4k`) in the record. Native/4K pairs should be
explicit artifact roles, not a guess based on `film.mp4` or the newest directory.
Use optional files only when there is content for them. Do not create empty
research, decisions, lessons or handoff documents for every film.

## Public record contract to implement

Use schema version 1, strict unknown-field rejection and portable relative paths.
Define the schema and validator before migration. No database or paid service is
needed. Suggested fields:

| Field | Meaning and source of truth |
| --- | --- |
| `schemaVersion`, `projectId`, `title`, `kind`, optional `seriesId` | Stable public identity; no provider/account identifiers |
| `status` | `planned`, `producing`, `review`, `delivered`, `published`; status is not artistic approval |
| `briefPath`, `descriptionPath`, `descriptionSha256` | Repo-relative canonical documents; description hash is computed from exact bytes |
| `workspace` | Relative active/archive locator and `active`, `archive-planned` or `archived-verified`; never an absolute home path |
| `artifacts[]` | Role, version, workspace-relative path, SHA-256, dimensions, rational fps, integer frames, duration derived from frames/fps; explicit published master selection |
| `production.providers[]` | Public provider/model names actually used; distinguish images, motion and sound |
| `production.credits[]` | Role, model and harness separately; user-approved display text remains in the description |
| Financial data | Excluded from public JSON and prose; ignored `data/accounting/<project-id>/` retains itemized amounts, evidence and unresolved reservations |
| `publication` | Platform, supplied URL, evidence kind, recorded date, optional independently verified date and platform publication date only when known |
| `reviewEvents[]` | Event type, artifact hash/version, date when known, short sanitized evidence and outcome; never infer listening or approval from a decoder pass |
| `archive` | Manifest relative path, inventory hash and verification recording date; no claim of a remote backup |
| `relatedProjectIds`, `legacyPaths` | Public relationships and temporary migration aliases |

Do not put prices, financial figures, raw prompts, provider task IDs, signed media
URLs, authorization conversations, account balances, filesystem probes or operation
logs in this public JSON. Public video IDs inside supplied publication URLs and
artifact content hashes are intentional public identifiers. Build an explicit
allowlist exporter; never serialize the workspace object and delete a few known
private fields afterward. Apply the existing privacy guard to the resulting
record and prose, and inspect manually.

The workspace remains authoritative for frame edits, source hashes, usage and QA.
The public record summarizes those facts, not a second writable ledger. The
description is the one editable source for publication wording. Generate index
and current-summary views from records so the project status is not manually
maintained in three places. Keep original treatments intact with clear links to
the current summary. Do not refresh historical claims using a current provider
rate or reinterpret a past spending allowance.

## Implementation sequence and retained migration boundaries

1. **Read-only inventory.** Enumerate tracked `briefs/` files, inbound Markdown
   links, recipe references and series conventions with `rg`. Produce an ignored
   migration map: stable ID, existing documents, current workspace/archive,
   status, ambiguity and proposed destination. Do not open unrelated competing
   drafts or infer missing publication URLs. Separate indexable public metadata
   from local runtime evidence. Ask only about ambiguities that block a move.
2. **Schema and offline validator.** Add a small schema under
   `docs/schemas/production-record.schema.json` and validation/export code under
   `tools/production/`. Reuse existing path/hash and privacy primitives where
   their contracts fit. Validate source-only records without requiring ignored
   media on a fresh clone; offer an explicit local-evidence mode for hashes,
   artifact dimensions, frame counts and archive verification. Unknown fields,
   absolute/traversing paths and inconsistent durations fail clearly.
3. **One pilot.** Use VERIFY's brief and exact description, its published v4-4k
   master and the archive manifest. Map the original 39-second plan to intent,
   and the delivered 546 frames at 24 fps to the current record. Keep the
   publication evidence user-confirmed unless independently verified later.
   Preserve the original date text where present; do not fabricate missing dates.
4. **Compatibility.** Move only the pilot's documents with reviewed exact paths.
   Leave small forwarding Markdown pages at old public links, or update every
   caller and document any intentional break. Forwarders contain links, not a
   second editable copy. Historical archive recipes may rely on the old text
   path: keep local snapshots/restore instructions and test these references
   before removing an alias. Never edit a sealed archive to make migration easier.
5. **Current views.** Generate `briefs/README.md` and the project summary using
   status/title/series filters and links to description, decisions and record.
   Add dry-run/check modes that report drift without rewriting user text. Make
   output deterministic so a clean check creates no diff. Keep private runtime
   paths and logs out of generated source.
6. **Lifecycle integration.** Update the shared production/post-publication
   workflows to create/update the record from approved evidence. Synchronize
   description copies before archive sealing. Store post-seal Git receipts
   outside the archive. Reuse the existing archive helper rather than inventing
   a second archiving route. Source commit/push stays governed by existing
   authorization and privacy checks, not an automatic side effect of export.
7. **Second pilot and staged migration.** Exercise one active project or episode
   with native review pending, only within the owner's authorized scope. Confirm
   it cannot accidentally become published/approved. Migrate remaining projects
   in small reviewed groups; preserve uncertain states as unknown. Record
   unresolved links or dependencies for the next session.

## Acceptance checks

- On a fresh clone, validate all public records and internal document links
  without credentials, network calls, ignored media or new packages.
- Offline fixtures cover published and unfinished projects, multiple versions,
  a supplied-but-processing URL, local unresolved reserves, unknown fields and unsafe
  paths. An injected runtime secret/operation field cannot enter an export.
- The pilot description matches its pre-migration bytes and hash exactly; credit
  text and final repository URL remain. Repeated export/check has no diff.
- Local-evidence mode confirms the selected artifact hash, derived duration,
  explicit native/4K roles and archive manifest; technical success does not set
  artistic approval or imply real-time listening.
- Broken old brief links and recipe description references are resolved or
  explicitly documented. Restored copies, not sealed archives, receive new work.
- Run relevant tests/build and all source-publication privacy gates before an
  authorized commit/push. Report migration scope and unchanged/unresolved items.

## Harness distinctions

These are repository observations, not universal product capability claims.
Recheck the available tools in a fresh session; no model switch or installation
is part of this proposal.

| Scope | Current evidence and implementation consequence |
| --- | --- |
| Shared | `AGENTS.md`, production tools, project records and `.agents/skills/` carry durable decisions. Neither harness should depend on the other's personal memory. |
| Codex | `docs/harness/codex.md` records an earlier session without a usable browser and later VERIFY browser review. Browser availability is session-specific. Tool calls and frame inspection do not prove audio listening. |
| Claude Code | `docs/harness/claude-code.md` records Fable's 2026-10-03 zsh/cwd/background-job observations and its image-review limits. Preserve them as attributed observations; Codex has not independently qualified Claude's runtime. |
| Skill discovery | This repository uses canonical `.agents/skills/` instructions and relative Claude symlinks. Keep one body for the new workflow, avoiding separate harness policies for archival or publication. |
| Background work | Each agent uses its actual harness's process handles and timeouts, while saving progress/requests under the project. Do not copy a harness-specific timeout or cwd assumption into shared CLI behavior. |
| Attribution | The public record distinguishes model, harness and role. Commit trailers come from `.githooks/identity.json`; both author and committer remain TK-421. |

The initial milestone included VERIFY and the existing Episode 05 review draft.
The later full migration retains unknown status where evidence is incomplete,
and permits a historical publication URL without inventing an artifact hash.
Supporting scripts and edit recipes are indexed and validated alongside the
canonical documents. The ignored migration maps and snapshots preserve the old
paths and original contents. Archived text-file dependencies have restore notes.
Defer dashboards, databases, bulk archive cleanup and a new production UI until
the record has been exercised through another new film's complete lifecycle.
