# Video production with Claude Code

@AGENTS.md

Use the shared `produce-video` skill for making or revising films. It is available
at `.claude/skills/produce-video/SKILL.md` and `.agents/skills/produce-video/SKILL.md`.
`docs/production.md` describes the maintained CLI/MCP workflow; load detailed craft
notes only when the shot or edit needs them.

Claude Code specifics (zsh Bash tool, background jobs, timeouts, memory, MCP
profile) are in `docs/harness/claude-code.md`.

Build the existing MCP service with `npm run build`. `.mcp.json` configures the
local servers for Claude Code. Do not install packages as a routine startup step.
The CLI works without an MCP connection and has the same production behavior.

For publication descriptions, retain the project's credit conventions and include
`#gpt6` or `#gpt6astra` when appropriate to the models used. Every description or
credit block ends with the repository URL specified in `AGENTS.md`. Record a
published URL only when supplied or verified.
