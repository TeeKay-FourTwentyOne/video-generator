# CLAUDE.md

## Overview

AI video production system: concept → structured shots → video generation → assembly. Uses Claude (Opus 4), Veo 3.1, ElevenLabs TTS, Gemini.

All functionality is exposed via MCP (Model Context Protocol) tools. The `video-generator` MCP server provides ~45 tools covering the complete pipeline.

```bash
# Build the MCP server
cd mcp/video-generator && npm install && npm run build

# The server is configured in .mcp.json and runs automatically
```

## Documentation

| Topic | File |
|-------|------|
| MCP tools & workflow | `.claude/rules/core-workflow.md` |
| Narrative model (energy/tension/mood) | `.claude/rules/narrative-model.md` |
| Veo techniques & limitations | `.claude/rules/veo-techniques.md` |
| FFmpeg encoding knowledge | `.claude/rules/ffmpeg-knowledge.md` |
| Multi-character dialogue | `.claude/rules/dialogue-system.md` |
| Clip editing & variations | `.claude/rules/editing-system.md` |
| Agent reference & QA | `.claude/rules/agents.md` |
| Per-generation clip QA gate | `.claude/rules/clip-acceptance-gate.md` |
| Mandatory source PII/secrets review | `docs/source-privacy.md` and `AGENTS.md` |
| Advanced hybrid techniques | `TECHNIQUES.md` |
| **Skills** (auto-triggered) | `.claude/skills/` |

## File Locations

- Videos: `data/video/`
- Audio: `data/audio/`
- Images: `generated-images/`
- Exports: `data/exports/`
- Edits: `data/edits/`
- Projects: `data/projects/`
- Config: `data/config.json`

## MCP Server

The MCP server is located at `mcp/video-generator/` and provides tools for:
- Project generation and execution
- Video generation via Veo 3.1
- Image generation via Imagen 3.0
- Audio (TTS, music) via ElevenLabs
- Video analysis (transcription, scene detection, quality checks)
- Clip editing (trim, speed variations)
- Assembly with tension-aware transitions
- Project validation

## Publication descriptions

End every video description / credit block with this repository URL as its final line (user instruction, 2026-09-12):
https://github.com/TeeKay-FourTwentyOne/video-generator

Record published video URLs in the corresponding brief when supplied, so finished work can be revisited as model capabilities progress. Credit the models and tools actually used, respecting any project-specific credit exclusions.

## Mandatory commit and push privacy gate

Follow `docs/source-privacy.md` for every commit and push. Enable the tracked
hooks with `npm run privacy:install`; manually review PII/private context and run
`privacy:worktree`, `privacy:check` on the staged snapshot, and `privacy:outgoing`
before pushing. Include documentation, copied plans, commit messages and Git
identity in the review. Keep generated media, credentials, home paths, runtime
manifests and provider resource identifiers out of source. Never bypass a finding.
