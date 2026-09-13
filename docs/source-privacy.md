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
Global Git settings are not modified. This repository uses **TK-421**, whose
GitHub login is **TeeKay-FourTwentyOne**, for both commits and pushes. Configure
the repository-local author and committer identity:

```sh
git config --local user.name TK-421
git config --local user.email 237485569+TeeKay-FourTwentyOne@users.noreply.github.com
git config --local user.useConfigOnly true
```

The tracked `.githooks/identity.json` policy makes the privacy guard reject a
different author or committer name/email, even another public no-reply identity.
Environment overrides and an amend's retained author can differ from `user.*`;
review the actual commit metadata, not just configuration.
No-reply addresses are public identifiers, not a claim of anonymous authorship.

Push authentication is separate from commit attribution. Use the SSH remote for
`TeeKay-FourTwentyOne/video-generator` on GitHub and pin this checkout's
`core.sshCommand` to the existing TK-421 key with `IdentitiesOnly=yes` and
`-F /dev/null` so unrelated SSH identities are not offered. Key paths are
machine-specific and stay in local Git configuration, never source. Before
pushing, run an SSH authentication test with that same command and confirm the
greeting names `TeeKay-FourTwentyOne` (GitHub's no-shell test normally exits 1).
The privacy guard is network-free and does **not** verify the SSH account itself.
Do not choose an identity from the active `gh` account, which may belong to a
different project; do not switch global accounts or add new credentials silently.

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
   current author/committer identity; the commit-msg hook checks the message.
7. Fetch the intended remote, inspect divergence and all outgoing commits. Run
   `npm run privacy:outgoing` (or pass the intended base ref after `--`).
8. Verify the pinned SSH account is TK-421, then push only the authorized branch.
   The pre-push hook checks every new outgoing commit snapshot, message and
   identity using the ref updates supplied by Git. It
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
- Outgoing author/committer identities against `.githooks/identity.json`, public
  no-reply emails, and commit messages, as well as file contents. The guard remains
  reusable in repositories without this optional account policy.

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
