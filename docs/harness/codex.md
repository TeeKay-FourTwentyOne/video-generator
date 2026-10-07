# Codex harness notes

Maintained by Codex (GPT-6 Astra) sessions; Claude Code should not rewrite it.
Recorded from the October 2026 repository review as a starting point:

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
