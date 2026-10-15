# Handoff: verify recovery before reclaiming clip storage

Status: 2026-10-14. The semantic implementation and a 24-clip technical pilot are
complete. Human acceptance, a frozen profile, full-library coverage, current
complete-backup verification and a production recovery rehearsal are still open.
No master is cleared for removal by this handoff.

The requested delivery is a local source commit, without a push. A source commit
does not back up ignored media, analysis, model installations or private recovery
configuration. Preserve the original clips and historical workspace/archive copies.
Cloud operations must stay within active storage and download authorization;
deletion requires a later approval of exact paths and hashes.

Read [the analysis handoff](clip-analysis-handoff.md),
[analysis commands](clip-analysis.md), [local setup](clip-analysis-setup.md),
[private backup](clip-library.md#private-cloud-backup) and
[restoring on another machine](clip-restore.md). Recheck the implementation when
resuming; historical upload receipts and earlier backup checks are not current
evidence for the expanded analysis backup.

## Resume evidence

Private continuation files are under `data/workspace/clip-analysis-semantic-v1/`.
They are local evidence, not a verified off-machine backup.

| File | What it establishes |
| --- | --- |
| `implementation.json` | Technical status, final identities and known limits; its original authorization notes predate this commit request |
| `pilot-evidence-final.json`, `pilot-results.json` | The final 24 runs and measured resource/storage footprint |
| `retrieval-results.json`, `agent-review-notes.json` | Bounded retrieval results and proposed labels, without human acceptance |
| `review.html`, `review-templates.json`, `reviews/` | Review package and pending human records for exact manifests |
| `pilot-review-draft.json` | Proposed qualification record; approval fields remain unset |
| `real-fixtures.json`, `fixture-evidence.json`, `qa/` | Timing/silence fixtures, regression and review-link checks |
| `source-snapshot/manifest.json` | Pre-commit source hashes; documentation may have changed since this snapshot |

The candidate configuration is
`data/clips/analysis/profiles/semantic-pinned-v1.json`. Find its exact hashes in
the private reports; do not substitute a similarly named configuration. There is
no frozen profile from this pilot. The final implementation passed 136 offline
regressions. Review-page links and byte-range serving were checked; native playback,
real-time listening and human acceptance were not completed.

## 1. Settle extraction and retained storage before scaling

- Address duplicated runtime inventories before a full-library batch. The current
  profile inventory is copied into both resumable state and sealed manifests.
  Prefer shared immutable inventories addressed by hash, with verified backup
  membership and recovery. Preserve existing sealed runs and backward readability.
  A storage/schema/extractor change needs new run identities and qualification;
  never edit earlier manifests to make them pass.
- Measure the full retained footprint: successful and failed attempts, manifests,
  state, previews, search, review evidence, model installations and workspace copies.
  The readiness report measures catalog and retained analysis/review/snapshot data;
  it excludes model installations, masters and workspace/archive copies. Its byte
  total alone is not a disk-space plan. Keep reviewed limits and free-space reserves
  in private evidence, and measure actual allocated space before promising savings.
- Decide which additional parsing is required for discovery before removal. The
  most useful next auditions are timecoded audio-content labels (speech, music,
  sung vocals, ambience and silence), denser sampling around cuts/motion/brief text,
  and reviewed usable ranges with continuity or defect notes. These are proposals,
  not implemented or qualified detectors. Audition anything made mandatory before
  freezing a profile; record explicitly deferred coverage gaps.
- Capture relationships that pixels cannot recover: source, alternate, derivative
  and delivery roles; source-to-cut ranges; generation requests and references;
  existing QA, source/rights evidence and unresolved historical mappings. Join by
  verified hashes or unambiguous records. Preserve unknowns and original records.

## 2. Qualify the profile and every proposed cleanup clip

Review the exact 24 final manifests, including source-time speech listening,
visual claims, OCR, VAD gaps and padded endpoints. Confirm the diversity labels;
agent labels do not establish music/vocals/silence or known-defect coverage.
Keep corrections separate from raw model output.

Ten scene queries placed the agent-nominated clip first within this pilot. That is
not a library-wide accuracy score. The door-opening query remains an unconfirmed
action match; nearby people and a partly open door do not establish the action or
its direction. Label expected matches, false candidates, missed events and timing
errors, then approve concrete acceptance criteria. Do not turn an unconfirmed
action into a verified negative or accept unsupported static-scene claims.

Record immutable human reviews and a qualification-version-2 pilot bound to the
exact configuration, extractor, manifests and fixture/query evidence. Freeze only
when the existing gate passes. If behavior or pins change, rerun the candidate
set under the new identities and review that evidence.

```sh
npm run clips -- analysis verify "$CLIP_ID" "$RUN_ID"
npm run clips -- analysis review-template "$CLIP_ID" "$RUN_ID"
npm run clips -- analysis freeze-profile "$PILOT_REVIEW_JSON"
```

Then run the frozen required profile for **every clip proposed for cleanup**.
Resolve required `needs-review` states with exact human reviews. Failed decoding,
overlapping audio timestamps, unqualified formats or pending reviews leave that
clip local. Completing a representative pilot does not qualify the remaining
library. Keep seekable previews with audio where present, searchable metadata,
reviews, source timing and sampling limitations locally available.

## 3. Prove the backup includes every dependency

Inspect the current private configuration, active authorization, accounting and
download allowance. Check the current bucket access controls and unsigned listing
and known-object denial. A missing object or network error is not a privacy test.
Also inspect intended overwrite/deletion protections, lifecycle expiration and
their recovery procedures; a successful upload does not establish those policies.
Keep configuration, identities, receipts and detailed measurements ignored.

Prepare an explicit inventory of the originals, current catalog and uses,
historical location mappings, creation snapshots, required analysis manifests and
all declared artifacts, previews, human reviews, frozen pilot, qualification
evidence and dependency/access/retention records. Include selected surrounding
production evidence needed to understand or rebuild edits. Arbitrary workspace
files and archives are not covered by an ordinary clip mirror.

Use profile `evidence` entries and `data/clips/analysis/support.json` as documented
in [analysis backups](clip-analysis.md#analysis-backups-and-absent-masters).
Audit the **transitive** references too: backing up a JSON file containing another
path does not back up that target. In particular, inspect the frozen pilot's
fixture/query evidence, nested dependency decisions and any shared inventories
introduced by the storage improvement. Add supported, explicit backup membership
or another verified recoverable bundle for missing dependencies before proceeding.

Current recovery restores selected support JSON into content-addressed support
paths. It does not automatically reinstall every original workspace path, frozen
profile path or `data/clips/locations.json`. Preserve those bytes and a recovery
mapping, and test their restoration. A hash of the locations file in an audit is
not a backup of the locations file itself. Retain a tested copy of the recovery
source revision away from this disk through an authorized channel; this local
commit has deliberately not been pushed.

The following are later operational steps, not evidence that they ran for this
handoff. `plan` is offline; the other commands access private storage.

```sh
npm run clips -- cloud plan
npm run clips -- cloud sync
npm run clips -- cloud backup-sets
npm run clips -- cloud verify-set "$BACKUP_SET_SHA256"
```

Require one immutable complete backup-set manifest with the intended membership,
exact bytes, SHA-256 identities, server checksums and pinned object generations.
Verify every member against current remote metadata and confirm a repeat sync
skips unchanged payloads. `cloud status` reads local receipts; it is not a live
verification. Server checksum/metadata checks cover the inventory; actual downloads
and local hashing in the next step establish recovery behavior.

## 4. Rehearse recovery without the original local state

Use a new empty recovery directory and independently recoverable access. Prefer a
separate checkout or machine without the original catalog, manifests, media,
receipts, workspace evidence or cached backup-set manifest. Do not remove the live
copies to simulate loss. The recovery tools still need their supported runtime and
private access configuration; provision those independently and document how.

```sh
npm run clips -- cloud recover-set "$BACKUP_SET_SHA256" data/workspace/clip-recovery-rehearsal-v1 "$CLIP_ID" --rehearse
```

Choose explicit representative clips for every format signature and artifact type
in the proposed removal batch, including differing codecs, audio layouts, rotation,
HDR/VFR handling and creation-snapshot cases. Each selected clip restores all its
backed runs; size the rehearsal and download allowance accordingly. Use a new
output directory for each attempt and preserve failed evidence.

The maintained rehearsal verifies downloaded hashes and references, creation
snapshots, declared run artifacts, full audio/video decode and search rebuilding.
Also verify the following manually or with focused additional checks:

- Recover the backup-set manifest and selected catalog/uses/support records from
  remote storage, restore the historical-location and qualification mappings, and
  validate their nested evidence without consulting the original disk.
- Search restored observations, open the returned preview at its mapped source
  time, listen, and materialize an edit range from the restored master. Verify
  both inspection of saved results and the separately provisioned model runtime
  needed for new text embeddings or rerunning analysis; weights are not implicitly
  included in an analysis backup.
- Exercise normal restore-by-clip-ID into an empty test library, including creation
  snapshots and existing edit resolution. Confirm exact source hashes and frame
  ranges, without overwriting the live catalog or local masters.
- Establish recovery access from a secure off-machine store/account recovery path.
  Record a dated attestation containing no credentials. The current helper expects
  its configured credential file; a CLI login alone does not prove access works.
- Retain evidence identifying the source/tool revision, backup set, selected runs,
  tested formats/artifacts and results. Review it against the **current** intended
  backup set. The current readiness gate matches rehearsal format signatures and
  artifact extensions; it does not bind that rehearsal to the policy's backup-set
  hash or prove native playback, independent access or transitive evidence recovery.
  Close those checks explicitly, and strengthen the gate before automating cleanup.

## 5. Audit dependencies and produce a fresh readiness report

Bind the dependency audit to the current catalog, uses and historical-location
digests. For every proposed clip, explicitly review active edits, archives,
original paths, alternates and shared sources. For each planned use, document
`restores-by-clip-id`, `materialized-verified` or `confirmed-inactive`, with
hash-verified evidence included in the backup. Check scripts and timelines that
still refer to filesystem paths, not just catalog use records.

Prepare a private policy with the exact backup-set and frozen-profile hashes,
clip/run/review identities, dependency audit, access attestation and reviewed
retention limit. Include the supporting records in the complete set before its
final sync. Rebuild search after the final required runs and reviews.

```sh
npm run clips -- analysis index
npm run clips -- analysis readiness "$PRIVATE_POLICY_JSON"
npm run clips -- cloud readiness "$PRIVATE_POLICY_JSON"
```

The offline command reports blockers; it cannot establish fresh remote evidence.
The cloud command verifies all backup-set members before evaluating readiness.
The current gate accepts verification no older than one hour and rejects future
timestamps. Rerun immediately before a removal proposal if membership, metadata,
reviews, dependencies or remote objects change. Require `ready: true`, zero global
blockers and every selected row ready; a nonempty `proposedCleanup` list alone is
not enough. Also satisfy the recovery checks above that the automated gate does
not enforce.

## 6. Make removal a separate, reviewable action

Present a concrete manifest containing only the proposed canonical master paths,
hashes, byte sizes, clip/run IDs and verified backup-set identity, plus measured
expected reclaimed space and the local data to retain. Historical workspace and
archive copies are outside the current readiness manifest and need their own
audit and approval. Shared bytes or filesystem clones can make logical byte totals
differ from actual reclaimed space.

Wait for explicit approval of that manifest before removing anything. The current
commands perform no eviction; do not invent an existing delete command. Any later
cleanup implementation must recheck path containment, original hashes, dependencies
and fresh recovery evidence, stop on change, and keep a private action receipt.
Start with a bounded approved batch, then search, preview, restore and resolve a
removed clip before expanding. Preserve all metadata, reviews, local previews and
unapproved copies. Never treat cloud reliance as permission to delete the cloud
objects or to expire their recovery protection.

Completion means the chosen clips are qualified and useful without local masters,
their complete dependency set is verifiably backed up, recovery works without this
disk, the current dependency audit and readiness report pass, and the user has
approved exact removals. Until then, report the remaining blockers and keep the
originals.
