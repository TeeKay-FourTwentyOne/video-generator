---
name: archive-workspace
description: Archive one inactive project workspace, keep the final 4K and original sources, and remove verified intermediate edits under the standard retention policy. For full release closeout, use the shared post-publication skill.
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

After the intact move, apply the standard retention policy in
`docs/post-publication.md` using `tools/production/archive-retention.mjs`: keep the
verified final 4K, original sources, stems, references, recipes and QA; remove
reviewed superseded edit renders and mixes. Keep historical metadata and a receipt
linking the old and new seals. If no final 4K exists, defer cleanup. Do not move a
flat workspace wholesale, touch another project or use the adjacent historical
`prune.py`; it is not part of this workflow. Future edits use a verified copy.
