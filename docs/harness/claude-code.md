# Claude Code harness notes

What the Claude Code harness does on this workstation, observed 2026-10-03 during
the Borrowed Light draft (macOS, Fable 5.1). Shared rules are in `AGENTS.md`; craft
lessons are in `docs/craft/field-notes/`. Codex notes live in `codex.md`.

## Shell

- The Bash tool runs commands in `/bin/zsh` as a login shell, foreground and
  background alike. zsh does not word-split unquoted variables: `for s in $list`
  iterates once over the whole string. Use `for s in ${=list}`, an array, or put
  the loop in a bash script and run it with `bash path/to/script.sh`.
- The working directory persists between calls and the harness reports changes.
  A command that `cd`s into a workspace changes how later relative paths resolve.
  Background jobs honor a leading `cd` when they run alone. Reproduced twice on
  2026-10-03: when several Bash calls are issued in the same turn and one of them
  changes directory, another call's own leading `cd` can be lost and its relative
  paths resolve against the other call's directory. So parallel calls and
  long-running work use absolute paths throughout, and loops live in a script file
  with its own log (`data/workspace/<slug>/scratch/poll.sh` is the pattern).
- Foreground commands time out at ten minutes. Veo polling (`film poll --wait`),
  QA batches and upscales belong in background jobs that log into the workspace;
  the harness notifies when they finish and the output file lives in the session
  scratchpad.

## Tools and context

- `.mcp.json` registers the `video-generator` server; the default profile exposes
  the `production_*` tools plus `get_config`. The separate `veo-clips` catalog server
  may fail to connect and is not needed for production. The CLI
  (`npm run film -- ...`) does the same work without MCP.
- `.claude/rules/*.md` are auto-loaded routing notes; keep them tiny and point at
  `docs/` instead of pasting content. `CLAUDE.md` imports `AGENTS.md`.
- Claude Code keeps a personal memory directory outside the repository. It is not
  visible to Codex or to another checkout, so durable lessons go to
  `docs/craft/field-notes/` and project state goes to the workspace plan.
- The Read tool renders PNG and JPEG inline, so contact sheets
  (`ffmpeg ... select,scale,tile`) and full-resolution crops are the fastest honest
  way to inspect takes. `open` hands a file or `review.html` to the macOS viewer for
  the director; it is not a substitute for the director's own playback.
- The Python QA scripts resolve `data/config.json` relative to the repository since
  2026-10-03; they log token usage to `data/cost-ledger.jsonl`.

## Commits

- End commit messages with the Claude Code `Co-Authored-By` trailer; the
  commit-msg hook accepts the attribution addresses listed in
  `.githooks/identity.json` (Anthropic and OpenAI) on trailer lines only, and
  rejects any other email. Never bypass the hook. Author and committer are TK-421
  per the same policy; follow `docs/source-privacy.md` step by step.

## Things that look like bugs but are not

- "Budget is locked" from the ledger means another process holds the lock;
  retry after it finishes. Never delete a live lock.
- A `film poll` that returns `processing` is normal for several minutes on a
  Quality take; the operation is already paid for, and polling never submits.
- The ncnn upscaler prints a percentage per frame tile, not per clip; read the
  `[i/N] ... ETA` lines for progress. Its x4plus model is refused on macOS by design
  (about 30x the time of the default x2 model); do not work around the refusal here.

## Added during Washing Day (2026-10-03)

- Parallel Bash calls are the fast way to run paid QA: four to six `clip-qa`,
  `clone-check`, `frame-qa` or `anchor-drift` calls issued in one turn, each with
  absolute paths and its own `qa/<take>.<tool>.json` plus `.log`, finish together in
  about a minute. Never chain a dependent step (a submit after an extract, a poll
  after a submit) into the same turn as a parallel call; put it in the next turn.
- A background Bash call that launches `scratch/poll.sh S01 S02 ...` polls several
  Veo operations at once and notifies when the last one lands; one call per wave of
  submissions is enough. The poll script only ever calls `film poll --wait`.
- `npm run film -- image a.json b.json c.json --reconcile` is the right shape for a
  wave of anchors: it spaces the requests, reconciles each from its saved usage, and
  a background call returns when the batch is done. Inspect each image at half size
  (`PIL.Image.resize((540, 960))`) with the Read tool; zoom full-resolution crops for
  counts and pins.
- Spectrogram pictures (`showspectrumpic`, `showwavespic`) are the only "listening"
  the harness offers. They catch a throbbing drone, a missing bed, or music lines in
  a native take; they do not certify the mix. Say so in the delivery.
- Every edit version is immutable (`final/vN` refuses to re-render); a cut change or
  a mastering change means a new version, which is cheap because nothing is bought.

