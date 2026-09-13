# Source privacy and publication checklist

PII and secret review is a standard part of **every commit and push**, not just
video publication. This applies equally to source, briefs, copied plans, tests,
commit messages and Git identities. Nothing is uploaded to a scanning provider.

## One-time repository setup

```sh
npm run privacy:install
```

This enables the tracked `.githooks/` using repository-local `core.hooksPath`.
The installer refuses to replace existing custom hooks. New clones must run it;
Git does not activate hooks merely because they are tracked. Node 22+ is required.
Global Git settings are not modified. Use an approved public GitHub handle and
GitHub no-reply email for the repository-local author and committer identity.
No-reply addresses are public identifiers, not a claim of anonymous authorship.

## Each commit and push

1. Review the working tree and separate the requested work from unrelated edits.
2. Put human-readable briefs in `briefs/`; retain reusable source and tests. Use
   relative artifact paths and public model names. Do not copy whole runtime
   manifests or plans into source: they can contain home paths, account IDs,
   storage locations, provider operation names and private request logs.
3. Manually inspect proposed files for names, email/phone/address details, customer
   or private project information, identifiable screenshots, personal narrative,
   credentials and non-public URLs. Review Git identity and the commit message.
4. Run `npm run privacy:worktree`; fix or exclude findings. Stage **explicit paths**.
5. Run `npm run privacy:check`, review `git diff --cached`, and run relevant tests.
6. Commit only when authorized. The pre-commit hook checks the actual index and
   current author/committer emails; the commit-msg hook checks the message.
7. Fetch the intended remote, inspect divergence and all outgoing commits. Run
   `npm run privacy:outgoing` (or pass the intended base ref after `--`).
8. Push only the authorized branch. The pre-push hook checks every new outgoing
   commit snapshot, message and email using the ref updates supplied by Git. It
   catches sensitive content committed and then removed in a later local commit.
9. Verify the remote ref and working tree. Report privacy scope and exclusions.

An explicit request to commit and push is sufficient authorization for the clean,
reviewed task changes. It does not authorize unrelated changes or video publication.
If sensitive content is necessary rather than safely removable, pause for a choice;
never bypass the check or add a blanket exclusion. Existing custom hooks require
careful integration, not replacement.

## Guard scope and limits

`tools/privacy-check.mjs` has no external dependencies or network calls. It reports
only the repository-relative path, line, rule and redaction marker. It checks:

- Personal emails (except reserved examples and public GitHub no-reply identities),
  personal home directories, common phone/SSN/address formats and private IPs.
- Provider-token patterns, private keys, JWTs, literal credential assignments,
  credential-bearing URLs, service-account payloads and concrete cloud buckets.
- Private/runtime file paths, opaque binary/media files and files over 2 MiB that
  require deliberate review rather than being silently skipped.
- Outgoing author/committer emails and commit messages, as well as file contents.

This is a conservative pattern guard, **not exhaustive PII detection**. Names,
unusual phone/address formats, private business context, custom secret formats,
encoded payloads, model outputs and embedded image metadata still need manual
judgment. Variable names such as `apiKey` are not themselves credentials. Real
findings are never printed verbatim. No broad content or path allowlist is used.

The scan is scoped to candidate/index files and new outgoing commit snapshots.
It does not certify old public history as clean. If a previously published secret
is found, report it and arrange rotation and history remediation separately; do
not force-push or rewrite history without explicit authorization.

Generated video/audio/images, virtual environments, local QA manifests and logs,
cloud operation records, API keys and `data/config.json` stay local. A clean source
commit is not an archival backup of those production assets.

Tests: `npm run privacy:test`. The regression suite uses synthetic data in isolated
temporary repositories; no real credentials or identifiers are used as fixtures.
