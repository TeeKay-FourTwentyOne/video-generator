# RED TEARS — archive and future work

The released master is `final/v5-4k/film.mp4`: 2160 × 3840, 24 fps,
302 frames. The [production record](production.json) holds its checksum and
verified archive locator. The [description](description.md) preserves the
published text. Local playback uses the retained master and review page.

The archive retains all nine project clip masters under `sources/clips/`,
including the rejected first motion take and reusable local composites. It also
retains reference images, all original and processed audio stems and auditions,
generation snapshots, edit decisions, recipes, delivery records and QA.
Detailed accounting and provider evidence remain private.

Only the final v5 4K complete film is retained. Earlier complete exports,
assembly/debug renders, finishing candidates and derived full soundtrack mixes
are removed through the checked retention transaction. Their historical hashes
and reports remain; old review pages are historical evidence rather than current
playable deliveries. The final review page links the retained master,
description and publication.

## Rebuild boundaries

Verify the archive before copying it to a new active workspace. Work in that
copy; never rerun production or QA writers inside the sealed archive. The final
master is independently playable, but a complete source rebuild has not been
qualified as a single command or as byte-identical output.

Rebuilding requires this repository, Node, FFmpeg/ffprobe and the provisioned
Python environment with NumPy, Pillow and OpenCV. Restore missing library clips
from `sources/clips/` only after checking the immutable clip hashes; preserve
existing conflicts. Historical recipes can refer to the shared clip library or
the original workspace root. Adjust paths in the new working copy, retaining
the original evidence.

Reconstruct the original twelve-second mix from `edit/mix-v2.json` and its
retained stems before adding the approved voice. `recipes/mix-selected-05-v5.py`
documents the 604,000-sample stereo timeline: the exact selected mono cue is
duplicated into both channels at sample 564,000 for 36,000 samples. The final
4,000 samples are silent. Its checks also refer to the superseded v4 mix, so
rebuild that from its retained stem or adapt the comparison in the restored
copy. Do not discard historical checks or overwrite their reports.

`edit/v5.json` identifies the five picture segments. Rebuild native assembly
before 4K finishing; historical remux scripts expect previous native and 4K
exports that standard retention removes. The coda required an explicit timing
repair: verify all 302 presentation timestamps, the eighteen-frame flash and
two-frame terminal blackout. Source frames, compositing recipes, upscale recipes
and the original verification evidence are retained to support this work.

## Next useful workflow change

The [vocal-stinger field note](../../docs/craft/field-notes/vocal-stinger-auditions.md)
describes an early audition workflow and acceptance checks for a reusable local
tool. Implementation is future work; this release requires no further generation.
