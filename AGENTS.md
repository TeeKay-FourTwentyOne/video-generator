# Repository working rules

Read `CLAUDE.md` for the production workflow and `docs/source-privacy.md` before
preparing any commit or push. These rules apply to all agents in this repository.

## Source publication is a separate checkpoint

- Commit and push only when authorized. An explicit user request to commit and
  push authorizes the reviewed, in-scope changes; it does not authorize publishing
  the video, uploading assets, or signing up for providers.
- Preserve unrelated work and generated media. Store reusable code, tests,
  sanitized briefs and recipes in source; leave media, credentials, provider
  operation records, local logs and machine-specific manifests under ignored paths.
- A PII/secrets check is mandatory before every commit and push, including
  documentation, tests, commit messages, and author/committer metadata.
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
