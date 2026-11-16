# REPEAT release and restoration

The director supplied the publication URL on 2026-11-16 and requested the
post-publication workflow. The released local version is `4k-v2`, 670 frames at
24 fps in 2160 × 3840. This identifies the retained local delivery; it does not
claim that its hash identifies YouTube's transcode. The public description was
recovered from the page and preserved in [description.md](description.md).

## Edit and voice continuity

The three playbacks reuse the recorded source speech, with locally applied
distortion. The stinger repeats the clean third sample. The join revision keeps
the native spoken frames and uses six short, inspected motion blends in silent
gaps. It removes one redundant listening cut. The 4K finish preserves every video
timestamp and both compressed and decoded audio from that refined native cut.
Publication is a later event; it does not rewrite earlier review or listening
records.

## Retention and restoration

The final 4K review package, original references, prepared audio inputs, frame
recipes, edit decisions, provider evidence and QA remain local. Superseded full
edits and assembly segments were removed through the verified retention
transaction. Their delivery records, hashes and historical review events remain.
After private backup verification, the post-publication sync offloaded all 21
local clip masters and seven matching workspace copies, including composited
shot assets. Original and rejected takes remain in the verified private backup;
clip metadata and analysis remain local. The archive was resealed and its public
inventory hash updated. The workspace archive is a separate local artifact, not
a remote workspace backup. Recovery rehearsals and dependency audits were skipped
under the director's instruction; the backup and retained master were verified.

The archive depends on the repository tools, the clip library, FFmpeg, Node and
the provisioned Python environment with NumPy, Pillow and OpenCV. Interface
rendering also depends on an installed font. Backed-up composites preserve the
approved typography; a fresh render with a different font can differ.

Some historical recipes name the original active workspace. Future work must
verify the archive, copy it to a fresh workspace, then adapt those recipe roots
in the copy. Never edit or render into the sealed archive. Use
`npm run clips -- cloud fetch CLIP_ID` to restore a needed canonical clip, or
`npm run clips -- cloud restore CLIP_ID data/workspace/NEW_COPY/ORIGINAL_RELATIVE_PATH`
for a recipe's historical path in the new copy. Resolve every clip ID and verify
its hash before rebuilding. Private offload receipts map the removed paths to
clip IDs and verified backup objects. Earlier closeout notes describe the
pre-offload inventory; use the new receipt for current local availability.

To reconstruct removed drafts, first assemble the original native main sequence,
then append the restored stinger with its prepared audio. The refined native
export uses that draft's audio and restored composite assets. Finish from the
restored 4K counterparts only after the native base exists. Existing outputs and
QA receipts intentionally reject overwriting; use new output versions or an
explicitly prepared copy. No clean-room or byte-identical rebuild is claimed.

## Production improvement

REPEAT's recording-to-listening jumps led to a mandatory
[join-review workflow](../../docs/production.md#review-the-joins-before-delivery): inspect exact
source frames and moving context, rank nearby trim candidates, protect dialogue,
and inspect every intermediate frame in any local blend. Recheck affected joins
after finishing. The 4K pass also exposed rounded concat durations; the shared
editor now writes durations from cumulative integer frame boundaries, with a
regression check for every output timestamp. See the
[dated field note](../../docs/craft/field-notes/2026-11-15-repeat-joins.md).

Closeout now uses automatic local clip offload after verified private backup.
The shared [post-publication workflow](../../docs/post-publication.md#automatic-clip-offload-during-closeout)
retains the final delivery, records exact removals and resumes interrupted cleanup
without recovery downloads or a dependency audit.
