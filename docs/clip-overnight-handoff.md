# Resume clip processing

Operational continuation details live under ignored
`data/workspace/clip-overnight-v1/`. Read `handoff-20261015.md`, `authorization.json`,
`plan.json`, `state.json` and the newest entry in `resumes/` before starting another
process. These records retain the current queue, source and configuration pins,
resource limits, attempt history and checkpoint receipts. Live state takes
precedence over an earlier handoff snapshot.

## Inspect the existing worker

From the repository root:

```sh
node data/workspace/clip-overnight-v1/status.mjs
tail -30 data/workspace/clip-overnight-v1/events.jsonl
```

Check whether the recorded worker and any analysis child are alive, then inspect
the current step and its command log. A live PID alone does not establish progress.
Keep one model worker active at a time. Preserve interrupted attempts and retained
upload sessions so continuation can recover their existing work.

## Continue the saved queue

After establishing that the previous worker has stopped:

```sh
node data/workspace/clip-overnight-v1/worker.mjs --hours=10
```

The worker first completes any outstanding backup checkpoint, then processes
pending clips serially. Matching completed runs are reused. Backups follow batches
of successful clips and a normal stop. Resource limits and existing cloud
allowances remain enforced; a failed checkpoint stops further processing.

Use `--recover` only after confirming that the prior worker and child are dead
and inspecting the lock owner. Remove a private `STOP` file only when intentionally
resuming. A changed source, model pin or catalog record requires a new explicit
plan. Do not rerun preparation over the existing immutable plan.

The private runner uses small job records and one shared configuration reference.
Do not replace it with `analysis enqueue all`: the generic queue currently expands
and hashes the full pinned configuration separately for each job, and has not been
qualified for a library of this size.

To stop after the current clip and checkpoint:

```sh
touch data/workspace/clip-overnight-v1/STOP
```

A detached launch should retain its process and log references under a new
`resumes/` directory. Use process-scoped sleep prevention so it ends with the
worker. A reboot or process termination still requires inspecting persisted state.

## Preserve evidence and recovery

Keep successful and failed runs, model output, timing, previews, pending review
records and checkpoint receipts in ignored storage. Extraction completion does
not establish human acceptance or permission to remove an original. Failed or
unavailable passes retain their explicit status.

Reclamation follows a separate path and dependency audit with current backup and
restoration evidence. Read the applicable private completion record before further
cleanup; never rerun a completed removal manifest. Historical scripts may need
exact original paths restored before use. Preserve active project dependencies and
all source files whose processing or backup remains unresolved.

See the [analysis guide](clip-analysis.md),
[backup-readiness handoff](clip-backup-readiness-handoff.md),
[duplicate-cleanup guide](clip-cleanup.md) and [restore guide](clip-restore.md).
