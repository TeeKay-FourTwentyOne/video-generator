# Futility production notes

The director selected a continuous, measured poem performance after hearing four
auditions. Keeping the generated pauses and pace intact helped the poem read as
one thought. Later revisions changed the laughter level and ending without
rearranging that performance.

The final image reaches black at frame 363 and holds for the first brief laughter
burst. Finishing preserved all 408 frame timestamps and copied the approved
soundtrack. Full-resolution face, hair and fabric comparisons favored Lanczos
for this footage. The final master was inspected separately from those samples.

## Repairs completed during closeout

The finishing mux now completes and verifies BT.709 range, matrix, primaries and
transfer tags. Previously the concat could omit two tags despite explicit
segment settings, requiring a separate correction. The regression checks the
actual encoded file and unchanged soundtrack.

The retention helper now accepts explicitly reviewed, hash-bound versioned
complete mixes in `edit/`, where the maintained mixer stores them. Stem names
remain protected. The tests exercise quarantine, purge and source preservation.

## Shared analysis follow-up

The project analysis wrapper could complete extraction, then fail while adopting
the completed run because it attempted to reacquire its own analysis lock. A fresh
read-only project check verified the required passes; the failed attempts were
retained. This is a shared workflow issue, not an artistic-review failure.

A separate repair should inspect lock ownership across
`tools/production/clip-analysis-workflow.mjs` and
`tools/production/clip-analysis.mjs`. Keep one lock owner or supply an explicitly
internal adoption path; preserve exclusion of competing workers. Acceptance
checks should cover a new run, reused run, a genuinely competing worker, failed
extraction and project membership changing during a run. No generation provider
is needed for that regression. This larger repair is deferred.
