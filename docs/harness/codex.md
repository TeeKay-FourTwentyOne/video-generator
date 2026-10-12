# Codex harness notes

Maintained by Codex (GPT-6 Astra) sessions; Claude Code should not rewrite it.
Recorded from the earlier October 2026 repository review as a starting point:

- The computer-use session had no browser provider and native window lookup
  failed, so the review page was validated with its offline fixture rather than
  opened; the production CLI was exercised end to end from the shell.
- The canonical production skill lives in `.agents/skills/produce-video/`; the
  Claude copy is a relative symlink to it.
- Commit messages may end with the Codex `Co-authored-by` trailer; the hook accepts
  the OpenAI attribution address listed in `.githooks/identity.json` on trailer
  lines. Author and committer stay TK-421.

Add shell flavor, sandbox and timeout behavior, how media is inspected, and any
tool quirks here as they are observed, with dates.

## VERIFY close-out, 2026-10-12

- The earlier browser failure was session-specific. During VERIFY production,
  the available computer-use surface could open the Chrome loopback
  player and inspect the encoded film. Discover the current session's surfaces
  rather than treating the older failure as a permanent limitation. Visual
  inspection and computational audio checks still do not establish listening.
- Durable release instructions now live in the shared `post-publication` skill;
  its Claude entry is a relative symlink. Do not place required archive rules in
  personal Codex memory or require Claude to read it.
- A publication page fetch can fail even when the user supplies a published URL.
  Record the user's confirmation and the verification limit; do not block local
  documentation or claim the page was independently inspected.
