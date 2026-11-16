# REPEAT: a close-up exposes the joins

Source: Codex · REPEAT · 2026-11-15

The director liked the full draft but identified jumps between separately
generated recording and listening takes. A source-clip review had not resolved
those assembled boundaries. Fixed frontal close-ups make small changes in head
tilt, eyes, mouth and shoulders unusually conspicuous.

The repair used bounded source-frame searches, weighted grayscale comparisons
on the face and shoulders, dense candidate strips and native movement context.
We removed an unnecessary reaction cut and selected closer source poses. Six
small residual differences used 3–6-frame bidirectional optical-flow bridges at
24 fps, before the interface overlay. Every intermediate frame was inspected.
All native speaking-frame ranges and their edit positions remained unchanged.

The third-line blink looked better with one additional native closing frame
and a shorter bridge, even though the pixel-discontinuity score increased.
Use metrics to locate options, then judge the performance. A good endpoint match
can still stall or reverse movement; inspect the neighboring frames as well.

The full exported AAC stream and decoded PCM matched the prior draft, as did
every decoded frame of the accepted stinger and final black. The re-encoded main
was not claimed pixel-identical. The comparison reel was silent; full real-time
listening was not claimed.

**Apply:** the director requested this method in the standard process for future
videos. The [review-video-joins skill](../../../.agents/skills/review-video-joins/SKILL.md)
contains the workflow, reusable bounded ranking helper, optional bridge guidance
and exact private evidence pointers. Review every assembled boundary, while
reserving smoothing for cuts intended to feel continuous. Preserve existing
sources and alternatives, and record any remaining defect for the director.

## Finishing exposed a smaller timing error

The subsequent 4K check compared every video timestamp against draft-v3 and
found the 59-frame tail started roughly 0.326 ms early, despite correct total
frame count and identical audio. FFmpeg concat had inferred the first segment's
duration from rounded MP4 metadata. The initial candidate and discrepancy report
remain private evidence. The shared assembler/finisher now writes durations
from cumulative integer-frame boundaries, rounding the boundary to microseconds
before taking differences so many cuts cannot accumulate rounding drift.
The offline finishing regression uses an eleven-frame segment at 24 fps and
checks every base timestamp plus exact timestamp equality after finishing.
