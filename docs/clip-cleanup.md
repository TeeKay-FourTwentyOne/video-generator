# Reclaim verified canonical duplicates

This workflow removes only a canonical library master that also has a
hash-verified historical original on the same machine. It keeps that original,
all workspace/archive files, metadata, previews, reviews, creation evidence and
remote objects. Removing a last local copy still requires the complete semantic
qualification and readiness procedure in the
[backup handoff](clip-backup-readiness-handoff.md).

Use duplicate reclamation only after the user explicitly chooses this narrower
scope and approves the exact removal manifest. A general backup request does not
authorize it. The semantic qualification requirement is deferred for this scope
because the full local original remains available, not because model output has
been accepted.

Prepare a private `schemaVersion: 1` policy with:

- `scope: "canonical-duplicates-with-retained-local-originals"`;
- the immutable `backupSetSha256` and explicit `clipIds`;
- hash/size/path references to `dependencyAudit`, `accessEvidence` and
  `recoveryEvidence`.

The audit binds current catalog, uses and location digests. Every selected clip
needs the five source/edit/archive review decisions documented in the analysis
guide, an empty reviewed `canonicalPathReferences` list, and any planned uses
resolved as `verified-local-copy`. Review path-based scripts and timelines as
well as catalog use records. Include the audit and dated independent-access
attestation in the backup support mapping.

Recovery evidence must identify the exact set and establish empty-root recovery,
downloaded hashes, full decoding, search rebuilding, transitive support recovery,
recovered source tools, normal fetch and edit-range materialization. The additional
fields are `sourceRecovered`, `normalFetchVerified` and `editRangeVerified`.
Human access attestation must not contain credentials. Evidence is recorded after
the rehearsal and referenced by the local cleanup policy, avoiding a circular
requirement to include a set's own hash in that set.

```sh
npm run clips -- cloud cleanup-plan "$PRIVATE_POLICY" "$PRIVATE_MANIFEST"
```

Planning verifies every current remote member, all candidate bytes and the
retained local copies. It writes a new immutable manifest containing exact paths,
hashes, sizes, filesystem identities, backup generations and retained-copy paths.
On macOS, Python's standard library calls `getattrlist` to measure the
`ATTR_CMNEXT_PRIVATESIZE` value: bytes currently exclusive to each file. Apple's
[attribute documentation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/man/man2/getattrlist.2)
distinguishes these from blocks trapped in clones or snapshots. If this metric is
unavailable, the proposal reports it as unknown. Logical and allocated sizes alone
are not guaranteed reclaimed space; filesystem clones and snapshots can share
blocks, and concurrent disk activity can affect the final free-space measurement.

Present this manifest to the user. After approval, record a private JSON object
with `schemaVersion: 1`, the same `scope`, `approvedBy: "user"`, the actual
`approvedAt`, and the exact file-byte `manifestSha256` returned by planning.
Never infer or manufacture this approval.

```sh
npm run clips -- cloud cleanup-apply "$PRIVATE_MANIFEST" "$PRIVATE_APPROVAL"
```

Apply repeats live remote verification and checks approval, catalog digests,
dependencies, source identity and retained copies before removal. It acquires
cloud, analysis and catalog-writer locks, records a durable private journal,
stages each exact canonical file by rename, verifies local resolution through a
retained original, and then unlinks the staged duplicate. A changed dependency or
identity stops the operation. Failed post-rename checks restore the canonical
name when possible; an interruption can leave the staged file identified by the
journal. Preserve that evidence and inspect it before any retry.

Start with a bounded batch. Search and preview retained material, materialize an
exact range through the clip ID, and fetch a removed master before expanding.
Report measured free-space change and any test masters retained locally.
