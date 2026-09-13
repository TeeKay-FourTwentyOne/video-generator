# Session Closeout

Follow `AGENTS.md` and `docs/source-privacy.md`. PII/secrets review is mandatory
for every commit and push, including briefs, plans and Git metadata.

1. **Document the work** in a project brief or source-level session note: outcome,
   remaining limits, relevant tests, reproducible relative paths and next steps.
   Keep generated media and detailed runtime/provider records in ignored storage.

2. **Review scope and privacy before staging.** Separate unrelated changes. Inspect
   candidate code and prose for personal names, emails, phones, addresses, home
   directories, private project details, account/resource identifiers and secrets.
   Do not print sensitive values in findings. Inspect the proposed commit message
   and approved public GitHub/no-reply identity as well.

3. **Do not copy raw plans automatically.** If a local project plan contains useful
   source documentation, create a sanitized summary, then scan it. Never import
   global plans, private communications, credentials or unrelated project notes.

4. **Enable and run the local guard:** `npm run privacy:install`, then
   `npm run privacy:worktree`. Existing custom hooks must be integrated safely,
   never overwritten. Fix or exclude findings; pause for explicit approval if
   sensitive content is genuinely necessary. Never bypass a failed check.

5. **Stage explicit paths**, review `git diff --cached`, run
   `npm run privacy:check`, and run relevant tests/build. The tracked pre-commit
   and commit-msg hooks provide additional automatic checks.

6. **Commit only authorized work** with a descriptive, privacy-reviewed message.
   An explicit user request to commit and push is sufficient authorization for
   the clean, in-scope changes; it does not authorize unrelated files or uploads.

7. **Review everything going out:** fetch the intended remote, inspect divergence,
   list all outgoing commits and new files, and run `npm run privacy:outgoing`.
   The pre-push hook inspects all new outgoing snapshots and commit metadata,
   not just the final diff. No force-push or history rewrite without authorization.

8. **Push the authorized branch**, verify the remote ref, and confirm working-tree
   state. Summarize the commit, tests, privacy scope and any intentionally local
   or unrelated changes. A clean source commit does not back up generated media.
