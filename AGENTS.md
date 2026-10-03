# Repository working rules

These rules apply to all agents in this repository. For film production, use
`docs/production.md` and the shared `produce-video` skill. For code changes, read
only the relevant module and tests; detailed craft references are in `docs/craft/`.
Read `docs/source-privacy.md` before preparing any commit or push.

## Working surface

- Build: `npm run build`. Offline production regressions: `npm test`.
  Broader local suite: `npm run test:local`. Tests use disposable local fixtures;
  they do not require generation credits or new packages.
- Production CLI: `npm run film -- help`. MCP `production_*` tools use that same
  implementation. Inspect `docs/architecture.md` for maintained and legacy paths.
- Start new media in a versioned `data/workspace/<slug>/`. Keep plans, budget,
  provider records, sources, edits and QA together. Preserve existing media and
  unrelated working-tree changes.
- Paid work requires the user's active provider/scope/budget authorization.
  Reserve all costs in one project ledger before submitting. A timeout is not a
  reason to generate again: recover the existing operation first.
- Prefer local work for exact timing, sound mixing, typography and compositing.
  Model choice serves the shot; do not impose a paid draft pass or a global style.
- Deliver native review artifacts and distinguish technical checks from artistic
  approval and real-time listening. Do not infer permission to upscale or publish.
- For long work, retain the current plan, decisions, request IDs and verification
  evidence under the ignored workspace so another agent can resume accurately.

## Source publication is a separate checkpoint

- Commit and push only when authorized. An explicit user request to commit and
  push authorizes the reviewed, in-scope changes; it does not authorize publishing
  the video, uploading assets, or signing up for providers.
- Preserve unrelated work and generated media. Store reusable code, tests,
  sanitized briefs and recipes in source; leave media, credentials, provider
  operation records, local logs and machine-specific manifests under ignored paths.
- A PII/secrets check is mandatory before every commit and push, including
  documentation, tests, commit messages, and author/committer metadata.
- All commits and pushes in this repository use TK-421 (GitHub login
  `TeeKay-FourTwentyOne`). Set both author and committer to the public no-reply
  identity in `.githooks/identity.json`; verify SSH authenticates as that account.
  Do not infer identity from the active `gh` account or change global Git settings.
  Follow the repository-local setup in `docs/source-privacy.md`.
- Enable the repository hooks with `npm run privacy:install`. Do not replace
  existing custom hooks without review. Never bypass a failing privacy check.
- Review candidate content manually; run `npm run privacy:worktree`, stage exact
  paths, then run `npm run privacy:check`. After committing, run
  `npm run privacy:outgoing` and review the outgoing commit/file list before push.
- Redact or omit personal names/contact details, home paths, account/resource IDs,
  unrelated private project information and credentials. Use portable relative
  paths, environment variables, and an approved public GitHub/no-reply identity.
- Report findings by relative file, line and category; never echo secret or PII
  values. If sensitive content is genuinely required, pause for explicit approval
  and design a narrowly scoped exception. Do not silently include or bypass it.
- If an actual secret was already published, stop and report the exposure. Do not
  claim a later deletion purges Git history; coordinate rotation/remediation.
- Run relevant tests/build, verify the pushed ref and final working-tree state,
  and report the commit, privacy-check scope, and anything intentionally left local.

The automated guard is a pattern-based backstop, not proof that prose or images
contain no identifying information. Manual review remains required. It checks new
outgoing snapshots, not a retrospective audit or rewrite of already-public history.

## Video credits

Every publication description or credit block must end with the repository URL:
https://github.com/TeeKay-FourTwentyOne/video-generator

Record a published video URL in its brief only when supplied or verified. Do not
invent one or publish on the user's behalf without authorization.
