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
GitHub login is **TeeKay-FourTwentyOne**, for both commits and pushes. The
account's mailbox is recorded in the tracked `.githooks/identity.json` policy;
configure the repository-local author and committer identity from that file:

```sh
git config --local user.name "$(node -p 'require("./.githooks/identity.json").name')"
git config --local user.email "$(node -p 'require("./.githooks/identity.json").email')"
git config --local user.useConfigOnly true
```

The policy makes the privacy guard reject any other author or committer
name/email, including GitHub no-reply addresses. Environment overrides and an
amend's retained author can differ from `user.*`; review the actual commit
metadata, not just configuration. The policy mailbox is a published identifier
for the account, not a claim of anonymous authorship.

Agent attribution is welcome and should not be hidden: the policy's
`attributionTrailers` list names the vendor addresses that may appear on a
`Co-Authored-By: Name <address>` line of a commit message (currently the Anthropic
and OpenAI attribution addresses used by Claude Code and Codex). The allowance is
limited to well-formed trailer lines in commit messages; the same address in file
contents or body text is still a finding, and an address that is not listed, or is
a personal mailbox, is rejected. Author and committer remain TK-421.

The policy's `publishedContacts` list names addresses the repository deliberately
publishes, such as a product contact link; they pass the personal-email rule
anywhere. Any other address remains a finding.

`.githooks/reviewed-assets.json` maps exact blob ids to a short note for media
and oversized files a human has already inspected, including embedded metadata.
The guard releases only the two review prompts, and only for that exact content:
new or changed media is flagged again. Look at the asset yourself before adding
its id (`git ls-files -s <path>` prints it).

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

- Personal emails (except reserved examples, public GitHub no-reply identities and
  listed published contacts),
  personal home directories, common phone/SSN/address formats and private IPs.
- Provider-token patterns, private keys, JWTs, literal credential assignments,
  credential-bearing URLs, service-account payloads and concrete cloud buckets.
- Private/runtime file paths, opaque binary/media files and files over 2 MiB that
  require deliberate review rather than being silently skipped. Blob ids listed in
  `.githooks/reviewed-assets.json` do not prompt again.
- Outgoing author/committer identities against `.githooks/identity.json` (without
  a policy, only public no-reply addresses pass), commit messages, and file
  contents. Listed agent attribution addresses pass only on `Co-Authored-By`
  trailer lines. The guard remains reusable in repositories without this
  optional account policy.

This is a conservative pattern guard, **not exhaustive PII detection**. Names,
unusual phone/address formats, private business context, custom secret formats,
encoded payloads, model outputs and embedded image metadata still need manual
judgment. Variable names such as `apiKey` are not themselves credentials. Real
findings are never printed verbatim. No broad content or path allowlist is used.

Public instructions should describe privacy categories, without naming the
people or private entities to omit. Keep project-specific exclusion lists and
identifying review notes in ignored local storage. An instruction to withhold
information must not itself publish that information.

The scan is scoped to candidate/index files and new outgoing commit snapshots.
It does not certify old public history as clean. If a previously published secret
is found, report it and arrange rotation and history remediation separately; do
not force-push or rewrite history without explicit authorization.

Generated video/audio/images, virtual environments, local QA manifests and logs,
cloud operation records, API keys and `data/config.json` stay local. A clean source
commit is not an archival backup of those production assets.

Tests: `npm run privacy:test`. The regression suite uses synthetic data in isolated
temporary repositories; no real credentials or identifiers are used as fixtures.
