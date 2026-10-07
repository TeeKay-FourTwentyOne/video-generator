---
name: archive-workspace
description: Archive the current workspace by moving all files from data/workspace/ into a named subfolder under data/workspace-archive/. Use when finished with a project, cleaning up workspace, or archiving current work.
allowed-tools: Bash, Read, Glob
context: fork
---

# Archive Workspace

Archive one project folder from `data/workspace/<slug>/` to `data/workspace-archive/<slug>/`, preserving its internal sub-layout (`refs/`, `frames/`, `clips/`, `final/`, `scratch/`) but keeping only the **published 4K version** of the film: intermediate versions and renders are deleted first (step 4). The per-project workspace convention lives in memory: `feedback_workspace_convention.md`.

## Steps

1. **Inspect workspace** - List `data/workspace/` to see which project folders exist and, if needed, peek inside to confirm which one to archive.

2. **Pick the archive name** - Default to the project folder's own name (e.g., `hellzapoppin4-loading-dock`). Only override if the user wants a different name.

3. **Check for conflicts** - Verify `data/workspace-archive/<name>/` doesn't already exist. If it does, append a number (e.g., `hellzapoppin4-loading-dock-2`).

4. **Prune to the published 4K version** (standing instruction, 2026-10-06). Find which
   `final/<version>/` was published (the brief's `**Published:**` line or `delivery.json`
   `publication`). Dry-run, read the list, then apply:
   ```bash
   python3 .claude/skills/archive-workspace/prune.py data/workspace/<slug> --published <version>
   python3 .claude/skills/archive-workspace/prune.py data/workspace/<slug> --published <version> --apply
   ```
   The script deletes every other `final/<version>/` folder; inside the published one it deletes
   per-segment renders, the native export, lower-resolution (1080/720) and debug copies, and
   `upscale*/` segment files, keeping the 4K master and its small records (delivery, review page,
   contact sheets, logs, scripts). It also deletes media in `scratch/` and derived `.mp4` renders
   under `edit/` (polished segments). Pass `--also <path>` for extras that belonged only to a
   deleted version (for example an old mix). It refuses to run if the published folder has no
   `*4k*.mp4`, and it writes `archive-prune.log` (every deleted path and size) in the workspace.
   Never delete `clips/`, `refs/`, `frames/`, `qa/`, `operations/`, `prompts/`, `recipes/`, scores
   or mixes still used by the published version, plans, budgets or briefs. If no version is
   recorded as published, do not prune versions: ask which one to keep.

5. **Move the project folder intact**:
   ```bash
   mkdir -p data/workspace-archive
   mv data/workspace/<slug> data/workspace-archive/<name>
   ```
   Preserves the full sub-layout in one move — no per-file walk needed.

6. **Legacy flat workspace** - If the workspace is still flat (files directly under `data/workspace/`, no project sub-folder), fall back to the original pattern:
   ```bash
   mkdir -p data/workspace-archive/<name>
   find data/workspace/ -maxdepth 1 -not -name '.DS_Store' -not -name '.claude' -not -name 'workspace' -exec mv {} data/workspace-archive/<name>/ \;
   ```

7. **Confirm** - List the archive folder contents, confirm `data/workspace/` no longer contains the project, and report what the prune removed (count and MB from `archive-prune.log`).

## Rules

- Delete only what the prune step lists (other film versions, segment and upscale renders, native/1080/720/debug copies, scratch media, derived edit renders); never delete source clips, references, QA, operation records, prompts, recipes, scores, plans or budgets
- Skip `.DS_Store` and `.claude/` directory (leave in workspace)
- If the archive name already exists, append a number (e.g., `patterns-wiener-2`)
- Tell the user the archive path when done
