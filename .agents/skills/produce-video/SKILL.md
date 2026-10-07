---
name: produce-video
description: Produce or revise a film in this repository, from shot planning through budgeted generation and a native review export.
---

# Produce a film

Use `docs/production.md` for the executable workflow and manifest examples.
The same implementation is exposed by `npm run film -- ...` and MCP
`production_*` tools. Work from the repository root. No harness-specific agent
or provider SDK is required.

Make the film's intent and continuity concrete before buying motion: stable shot
IDs, what changes in each shot, what must stay fixed, and the sound that makes the
change legible. Choose shot scale, duration and local/generated technique for the
beat. A generated clip is raw material; the edit is the film.

Use the user's active authorization for scope, aspect, duration, budget and
providers. Initialize one all-in budget per authorization. Include images, QA,
audio and storage in that pot. Never reinterpret leftover money from another film
as permission. An existing authorization is not a reason to ask again.

Check `docs/craft/field-notes/` for known behavior of the models you are about to
pay for. Inspect anchors before generating. Submit one planned attempt per shot, preserve
the request ID, and poll the existing operation. An uncertain submission retains
its reservation; recover from its record before considering another attempt.
Choose retakes deliberately based on reviewed defects and remaining budget.

For acceptance, use `docs/craft/clip-acceptance-gate.md`: technical decode,
contextual visual review, dense inspection of motion/transfer windows, then a
keep/edit-around/reject decision tied to the source hash and clean frame range.
Existing paid QA scripts need a prior allowance and usage reconciliation. Tool
confidence cannot replace inspecting its flagged frames.

Build an integer-frame edit with explicit source/audio hashes into a new version.
Deliver the native review film, local review player, remaining defects, budget
estimate/reserves, and verification evidence. Distinguish frame inspection and
computational audio checks from full playback/listening. Preserve sources and
alternates. Publication, source commits, and requested finishing are separate
actions governed by the user's authorization and `AGENTS.md`.
