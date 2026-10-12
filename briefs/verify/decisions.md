# VERIFY — production decisions

The [current summary](README.md) is generated from the production record. The dated snapshot below preserves the revision evidence; it does not replace that record.

## Delivered revision — v4 (recorded 2026-10-12)

The user-approved production direction uses Runway Gen-4.5 footage, with locally
rendered interface graphics and synthesized sound. V4 applies the requested
pacing trims, omits bicycles, and runs 22.75 seconds at 24 fps. The center tile,
then the upper-left and upper-right tiles, select silently during the black-grid
beat, after the helper changes to “Please remain a person.” Verifying is the last
beat. These revisions supersede the original beat durations, empty bus tail and
no-selection direction in the [original treatment](brief.md).

The native review is 1080×1920; the explicitly authorized 4K finish is 2160×3840,
with the interface rendered at that resolution and original footage scaled
locally. The final user-edited publication text, including the concept credit and
related links, is preserved in [publication text](description.md).

Publication: [VERIFY on YouTube Shorts](https://youtube.com/shorts/lb9vcB07CRg).
Recorded 2026-10-12 from the user's supplied publication URL; user-confirmed,
not independently verified through the public page. This recording date is not
an assertion of the platform's publication date.

The released local master is `final/v4-4k/film.mp4`: 2160×3840, 24 fps,
546 frames / 22.75 seconds. SHA-256:
`a9efb8f799372976d070df3bda390874477de2915356a86c57678354b90da75a`.

Verified local archive: `data/workspace-archive/verify-film-v1/` (2026-10-12).
The intact archive preserves sources, alternates, native exports, all revisions,
recipes, ledgers and QA: 2,062 inventoried files, plus the archive manifest.
Content hashes, sizes and permissions were verified after moving. Its local
publication record links the final description and release evidence. The
[post-publication workflow](../../docs/post-publication.md) records the reusable
close-out procedure; the [production-record handoff](../../docs/production-records-proposal.md)
records the implemented documentation migration. The [original treatment](brief.md) is retained as history;
its proposed tools, durations and actions are superseded by this production record.


## Restoring historical recipes

The sealed archive is evidence, not a working directory. Verify it with `node tools/production/archive.mjs verify verify-film-v1` before copying it into a new active workspace. Preserve the seal in the original archive. Adapt hardcoded `data/workspace/verify-film-v1` roots and choose new output versions only in the restored copy. The existing dependency note remains in the archive; a standalone rebuild has not been qualified.

`scripts/assemble-v4.mjs` historically reads `briefs/verify_description.md` as text. That path now forwards human readers. In a restored recipe, change the text source to `briefs/verify/description.md` for current wording, or to the restored `notes/publication-2026-10-12/published-description.md` for the exact historical wording. Do this before running assembly; copying the forwarding page would produce incorrect credits. The two description sources matched byte for byte at migration. No sealed recipe or delivery record was edited.
