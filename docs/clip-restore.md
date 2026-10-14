# Restore clips from private storage

Use `cloud fetch` when an edit needs a clip whose master is no longer on the
machine. It restores the original bytes and retained creation evidence into the
shared library. Storage access stays authenticated; the commands never create
public links or signed URLs.

## Restore a clip for an edit

```sh
npm run clips -- search greenhouse
npm run clips -- cloud fetch "$CLIP_ID"
npm run clips -- resolve "$CLIP_ID"
```

The catalog supplies the expected identity. Fetch pins the remote object generation
and verifies SHA-256, server MD5 and byte length. It restores any private generation
snapshots and checks their canonical hashes against the catalog. Matching local
files are kept; conflicting files fail without replacement. Media masters become
read-only. A private receipt records exactly which remote generations were used.

To obtain a separate copy instead, retaining the original extension:

```sh
npm run clips -- cloud restore "$CLIP_ID" data/workspace/example/restore/source.mp4
```

This second command restores media only. `cloud fetch` is the complete library
recovery path, including generation snapshots. Neither command changes catalog
descriptions, prompts, use records or public availability.

## Set up another machine

Use a checkout containing the cloud commands, a supported Node.js runtime with
built-in `fetch`, and FFmpeg/FFprobe for subsequent media operations. Cloud recovery
itself uses Node built-ins and does not require generation providers, a model
download or the Google Cloud CLI. Local source changes must be transferred or
delivered before a checkout on another machine can use them.

Bring the private recovery configuration through a secure channel, separately from
source and media: the configured destination, authorization and current operating
limits, current `ledger.json` and `last-sync.json`, and access to an authorized
credential at the repository-relative path specified by `credentialFile`.
Do not copy a stale ledger back over a newer one or reset uncertain reservations.
Only one machine should write the accounting ledger at a time; it is a local lock,
not a distributed budget coordinator. Check pricing freshness before a download.

Store configuration and accounting under ignored `data/clips/cloud/`, restrict
private files to their owner, and keep credentials outside Git and recovery media
bundles. The current authentication helper expects a service-account credential
file; logging into the Google Cloud CLI alone does not configure this helper.
Use a separately administered credential with only the necessary bucket access
where possible. Provisioning or changing that account is an infrastructure action.

Access configuration must also be recoverable away from the original machine.
The bucket intentionally does not back up its own credentials. Keep the private
configuration in an independent secure store and retain an account recovery path.

## Recover a missing or newer catalog

The source catalog is normally enough to find a clip. If it is missing or older
than the backup, list the available snapshots and choose a specific digest:

```sh
npm run clips -- cloud catalogs
npm run clips -- cloud recover-catalog "$CATALOG_SHA256" data/workspace/recovery
```

The result contains `catalog.json.gz`, `recovery.json`, and a `catalog/` directory
with validated `clips/` and `uses/` records. Recovery does not overwrite the live
catalog or require any local media. Choose the snapshot deliberately: its creation
time is the upload time, not the time every annotation was written.

On a fresh checkout with no local catalog work, retain the checked-out catalog
before installing the recovered one:

```sh
mv catalog data/workspace/catalog-before-recovery
cp -R data/workspace/recovery/catalog catalog
npm run clips -- index
npm run clips:check
npm run clips -- cloud fetch "$CLIP_ID"
```

If `catalog/` was absent, omit the `mv`. If there are local edits, compare and merge
the staged records instead. Keep both versions until the differences are resolved.
Never replace a newer catalog with an older backup merely because its download
succeeded. `validate --media` expects all masters locally, so it is not the check
to use on a deliberately partial library; `resolve` verifies a requested master.

## Privacy and recovery checks

The storage client rejects a bucket without enforced public access prevention and
uniform bucket-level access, and rejects public bucket IAM grants. A broader audit
should also inspect project and ancestor IAM, any managed-folder policies and
serving backends, then try unsigned requests without credentials for both listing
and known objects. A denial must be an authentication/authorization failure;
an absent object or a network error proves nothing about privacy.

Authorized IAM principals can still read the bucket. Public access prevention also
does not block a signed URL created by an authorized signer. Keep credentials and
resumable upload session URLs private. See Google's documentation on
[public access prevention](https://docs.cloud.google.com/storage/docs/public-access-prevention)
and [inherited IAM permissions](https://docs.cloud.google.com/storage/docs/access-control/using-iam-permissions).

Periodically repeat a restore into an empty media library. Verify hashes, decode
every audio/video stream, and confirm creation evidence and edit resolution. A
successful sample is evidence that the recovery path works, not a full download
verification of every remote object. Inventory comparisons can separately check
all masters against server checksums.

Local cleanup remains separate work. A clip backup does not preserve project
scripts, timelines, audio assets, reference images or arbitrary workspace files.
The [analysis plan](clip-analysis-plan.md) defines the prerequisites for relying on
remote masters while retaining useful local search and preview information.

## Analysis and complete backup sets

The original media/catalog restore commands above remain available. For a backup
that also includes immutable analysis, declared previews, adjacent evidence and
reviews, use `cloud backup-sets`, `cloud verify-set`, and
`cloud recover-set SET_SHA data/workspace/recovery CLIP_ID --rehearse`.
See [private analysis recovery and cleanup readiness](clip-analysis.md).
