---
name: archive-workspace
description: Archive one inactive project workspace intact, preserving sources, native exports, earlier versions, recipes and QA. For the full post-publication wrap-up, use the shared post-publication skill.
---

# Archive one workspace

Read `AGENTS.md` and the archive procedure in `docs/post-publication.md`.
Use `node tools/production/archive.mjs plan SLUG`, then `apply SLUG` and
`verify SLUG`, from the repository root. Inspect dependencies and stop only
that project's writers before moving. The helper preserves the whole folder,
refuses existing destinations and symlinks, and verifies a content manifest.

An archive-only request does not authorize a source commit/push or video upload.
For the full four-step release wrap-up, use the canonical shared skill at
`.agents/skills/post-publication/SKILL.md` (also linked from the Claude skill tree).

Do not prune by default, move a flat workspace wholesale, or depend on personal
harness memory. The adjacent historical `prune.py` is not part of this workflow;
any cleanup needs a separate explicit scope and dependency review. Preserve the
sealed archive; future edits use a verified copy in a new workspace.
