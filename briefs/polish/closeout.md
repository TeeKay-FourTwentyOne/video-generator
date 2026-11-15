# POLISH — publication and recovery

The director confirmed publication of the held-phone **v2-4k** revision and
supplied [the YouTube Shorts URL](https://youtube.com/shorts/arM1eQzBi7k).
The recording date is 2026-11-15; the platform publication date is not asserted.
The [production record](production.json) identifies the delivered local master;
its hash does not identify the platform transcode. The exact current
[publication text](description.md) includes the director's edits.

The published film is 38 seconds, 912 frames at 24 fps, 2160 × 3840. It replaces
the tabletop phone and hand insert with a close oblique handset, subtly moving
as though held and typed on just offscreen. The input and recommendations stay
visible. All keyboard bounds remain outside the camera throughout, including
the pixel macro. The original exchange, timing and soundtrack are unchanged.

## Preservation and recovery

The archive retains the final 4K review package, all three original provider
video takes and their creation records, reference images, original voice files,
source stems, recipes, frame edits, metadata and QA. The clip library separately
retains the imported sources and private analysis, including unused material.
Verified project backup is distinct from the sealed local workspace archive.
Technical checks, sampled visual review, listening and publication remain
separate facts; publication does not create a retrospective listening record.

Standard retention removes exact reviewed superseded full edits, assembly
segments, regenerable composite caches and complete soundtrack mixes. It keeps
their historical hashes, delivery metadata and review records. Private receipts
identify every removed path and the verified archive inventory. No source take
or other project's media is part of this cleanup.

For another edit, restore a verified copy into a new active workspace. Restore
needed immutable clips by ID, then regenerate the local interface with
`tools/polish/render.py` or the current framing with `tools/polish/held.py`.
The archived recipe copies identify the exact recipe versions used for each
render. `tools/polish/sound.py` rebuilds the current mix from retained voice files
and deterministic cues; stems and the final master's encoded soundtrack are
also retained. Prepare the native edit before its 4K counterparts and finish.
Do not write into the sealed archive. This is a documented reconstruction order,
not a claim of a qualified standalone or byte-identical rebuild. The repository,
FFmpeg, the provisioned Python dependencies and a compatible local font are
external requirements.
Some historical verification recipes name the original active workspace path.
Use that path in a restored working copy or adapt the copied verification recipe;
the sealed historical recipe remains unchanged.

## Process improvement

The first 4K counterpart import lacked its derived classification. Maintained
finishing subsequently supplied that classification, changing catalog evidence
and requiring another analysis pass for identical media. The new
`tools/polish/local-derived-metadata.json` and documented import command establish
the classification before the first pass.

A shared follow-up belongs in `tools/production/edit.mjs` and
`tools/production/clip-analysis-workflow.test.mjs`: register the final counterpart
metadata before analysis and verify that finishing leaves the catalog evidence
and analysis identity unchanged. Acceptance should cover a fresh counterpart,
an existing correctly classified counterpart, and conflicting metadata. Retain
old runs, keep all required extraction and verification, and never reinterpret
an obsolete run as current. This broader repair is proposed, not implemented.

The local analysis process also exhausted its default JavaScript heap while
checking a large pinned tool profile. Recovery retained the failure evidence
and reused completed extraction with a larger process-local heap. The separate
global search refresh remained explicitly deferred; no project pass was waived.
