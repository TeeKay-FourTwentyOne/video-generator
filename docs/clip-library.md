# Shared clip library

Every clip has a content ID: `clip_` followed by the full SHA-256 of its original
bytes. Identical files share an ID even if their names or project folders differ.
A trim, transcode or composite has different bytes and gets its own ID when
imported. This ID will also identify the clip when public hosting is added.

| Location | Contents | Git |
| --- | --- | --- |
| `data/clips/<clip-id>/source.<ext>` | Verified, read-only original bytes | Ignored |
| `data/clips/<clip-id>/generations/<snapshot-sha256>.json` | Exact private creation-time request snapshots | Ignored |
| `catalog/clips/<clip-id>.json` | Technical properties, prompts, analysis, characters, collections | Tracked |
| `catalog/uses/<use-id>.json` | One occurrence in an edit, its source range and output hash | Tracked |
| `data/clips/locations.json` | Historical local paths mapped to IDs | Ignored |
| `data/clips/migration-report.json` | Import coverage, unresolved references and failures | Ignored |

The JSON records are the portable source of truth. They work in a clone without
media, providers or a database. A future SQLite index can be rebuilt from them;
stable IDs and separate usage records provide the join keys. An opaque database
file should not replace the reviewable public records.

## Find and inspect existing clips

```sh
npm run clips -- search greenhouse
npm run clips -- search char_001
npm run clips -- show "$CLIP_ID"
npm run clips -- resolve "$CLIP_ID"
npm run clips -- analytics
npm run clips -- index
npm run clips:check
npm run clips -- validate --media
```

Search includes prompts, descriptions, tags, character names, collections and
legacy identifiers. `resolve` verifies local bytes against the catalog hash.
`validate` needs metadata only; `--media` additionally hashes every master and
verifies retained creation snapshots against their hashes and catalog projections.
`index` rebuilds the compact Git-tracked browse index; `clips:check` also verifies
that index is current. Regenerate it after adding sources or uses, before committing.
MCP `production_clips` exposes `search`, `show`, `resolve` and `analytics` through
the same CLI. No command here calls a generation or analysis provider.

## New sources and edits

Maintained Veo, MiniMax and Runway polling stores originals in the library and
returns `clipId`, `sha256` and a **repository-relative** media path. Veo legacy jobs
also use this store. Provider transport helpers accepting an explicit destination
remain low-level download primitives; production polling performs ingestion.
Import local animation, composites and externally acquired clips explicitly:

```sh
npm run clips -- import data/workspace/example/render/source.mp4
```

An optional second argument supplies public metadata (`labels`, `collections`,
`tags`, `generations`, `analysis`, `characters`, `kind`). Request metadata is
projected onto the schema allowlist; provider operations, credentials, paths and
accounting are never copied into public records. A prompt rejected by the privacy
filter is marked `withheld`, with its text and prompt ID absent. The filter is a
backstop; manually review metadata before committing it.

### Generation snapshots

New maintained Veo, MiniMax and Runway attempts save a private, immutable request
snapshot before any generation request. This also covers Veo legacy jobs using
the shared client. Polling attaches the saved snapshot to the clip, without
re-reading prompt files or using changed plan settings. The public generation
entry has `source: "creation-snapshot"` and `snapshotSha256`, plus the safe prompt,
resolved model, requested alias, known seed, effective controls, capture timestamp
and ordered reference hashes/roles/sizes. API details and exact untrimmed prompt
remain in the private copy. Missing model versions and provider-selected seeds
stay unknown. Repeated polling is idempotent; different attempts yielding the
same video bytes retain separate snapshots under the shared clip ID.

For another generation route, capture its request at creation using
`saveGenerationSnapshot` in `tools/production/generation-snapshot.mjs`, then attach
that record when importing its video:

```sh
npm run clips -- import data/workspace/example/source.mp4 --snapshot=data/workspace/example/operations/S01-v1.request.json
```

The helper takes the budget-file location and an object containing `provider`,
`requestId`, `fingerprint` (SHA-256 of the request), `prompt`, `requestedModel`,
`model`, `seed`, `parameters`, `sources` and `api`. A source has `role`, `sha256`
and `bytes`, with available `mimeType`, `width`, `height` and `durationSeconds`.
Use `null` for an unknown model/seed; never infer them from a tool's branding.
The helper adds the timestamp and schema/evidence labels. Capture normalized
defaults and the exact bytes sent, exclude credentials and media payloads, and
keep later outcomes in a separate operation/asset receipt. This helper records
provenance; it does not authorize or reserve spending for an external route.

Keep both the workspace record and library copy when archiving. A snapshot
conflict or hash mismatch stops ingestion; restore original evidence rather than
overwriting it. Historical imports remain distinguished by their original
evidence source. A later reconstruction must not be labelled `creation-snapshot`.
Local animation and derived edits retain their recipes and source hashes; a
generative model and prompt are applicable only when actually used.

New `edit/v1.json` segments refer directly to the master:

```json
{
  "shotId": "S01",
  "clipId": "clip_<full-sha256>",
  "inFrame": 12,
  "frames": 168,
  "decisionFile": "qa/S01.json"
}
```

The acceptance decision still records the full source SHA-256 and reviewed frame
range. Assembly checks those boundaries, verifies the master, and renders only
the requested portion into the edit's output folder. It records one use for each
segment after the delivery passes technical checks. Repeating a clip twice in one
edit counts twice. Re-running ingestion does not add uses.

Legacy `source` plus `sha256` edits remain supported; assembly imports their source
and saves a clip-ID-based delivery record. Existing source paths and archives are
preserved. `join-anchor` accepts either a clip ID or a legacy workspace path.
For a custom editor, materialize a frame range with:

```sh
npm run clips -- extract "$CLIP_ID" 12 168 data/workspace/example/edit/portion.mp4
```

Extraction writes a picture-only MP4 and a local `.clip.json` receipt. It performs
frame-count and decode checks and refuses existing outputs. Extraction alone is
not a use in a film. A custom editor can submit a schema-conforming use via
`npm run clips -- record-use PUBLIC_USE.json` after building its output. Provider
audio is not implicitly mixed; retain the project's explicit soundtrack workflow.

## Historical import and analytics limits

`npm run clips -- migrate` inventories videos in existing `data/` folders, hashes
them, and installs independent verified masters (copy-on-write when supported).
It never moves, replaces, hard-links to, or deletes originals. Original paths
remain in a private location index. The importer skips symlinks and the library
itself. Synthetic test fixtures outside `data/` are not production clips.

The initial catalog deliberately includes derivatives and finished exports so
potential source footage is not silently omitted. `kind` distinguishes known
generation sources, conventional `edit`/`scratch` derivatives, conventional
`final`/`review` deliveries and `unknown` files. Path-based classifications are
organizational hints; generation evidence is stronger. Collections describe
association with a project, not proven inclusion in its final cut.

The importer joins the older clip metadata and search manifest, saved jobs,
explicit prompt/media records, film plans and asset hashes. It retains recorded
descriptions, transcripts, frame descriptions and character-cluster labels with
their provenance. These are historical automated analyses, not freshly verified
annotations. Character clusters are not verified identities; face embeddings and
runtime analysis paths are not copied into the catalog.

Prompt IDs hash the stored text with leading and trailing whitespace trimmed.
Prompt evidence distinguishes an actual saved request from a `film-plan` or older
catalog entry. A saved plan may have changed after generation. Unknown prompts,
models, seeds and dates stay unknown. Matching by filename is allowed only when
all matches have the same content hash; a supplied hash must match exactly.

Frame edits become `planned` uses. A matching saved delivery with a locally
identified output upgrades the exact edit to `rendered`; this does not establish
artistic approval or publication. Revisions count as separate edits. Copied media,
repeated imports and folder membership never increase use counts. Procedural
Python recipes and unsupported historical timelines need separate evidence before
their usage can be counted. The private migration report records unresolved
references; analytics are a lower bound on historical use.

Analytics include prompt IDs/text/model evidence, rendered and planned occurrence
counts, distinct rendered projects, and source seconds used. Seconds count repeated
occurrences; they are not unique coverage or audience views. This supports prompt
reuse research without conflating selection with quality or inferring causation.

## Public hosting and integrity

`availability` starts with `status: local-only`, empty `urls`, and unknown `license`.
No media was uploaded and no media-license grant is inferred from the code license.
After a hosting and rights decision, attach unsigned public HTTPS URLs to the same
ID and preserve its hash. Media paths, embedded tags, prompts and annotations still
need publication review. Changing the bytes creates a new ID.

Writes use per-clip locks and atomic replacement. An interrupted import is safe to
rerun; the master hash is checked before reuse. If a writer lock remains after a
crash, confirm that writer has stopped before removing its directory under
`data/clips/.locks/`. A master hash mismatch stops the operation; restore verified
bytes from an original, never bless changed bytes under the old ID.
