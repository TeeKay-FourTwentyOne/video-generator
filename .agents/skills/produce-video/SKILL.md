---
name: produce-video
description: Produce or revise a film in this repository, from shot planning through budgeted generation and a native review export.
---

# Produce a film

Use `docs/production.md` for the executable workflow and manifest examples.
The same implementation is exposed by `npm run film -- ...` and MCP
`production_*` tools. Work from the repository root. No harness-specific agent
or provider SDK is required.

This is an artistic project. Treat the brief as a vision to push, not a
specification to satisfy: make the craft choices with a point of view, let the
material that comes back change the plan where it is better than the plan, and
bring ideas the brief did not ask for, marked as yours. The ledger, the gates and
the check-ins exist so that boldness is affordable, not to replace it.

Make the film's intent and continuity concrete before buying motion: stable shot
IDs, what changes in each shot, what must stay fixed, and the sound that makes the
change legible. Choose shot scale, duration and local/generated technique for the
beat. A generated clip is raw material; the edit is the film.

Use the user's active authorization for scope, aspect, duration, budget and
providers. Initialize one all-in budget per authorization. Include images, QA,
audio and storage in that pot. Never reinterpret leftover money from another film
as permission. An existing authorization is not a reason to ask again.

Use `docs/production-records.md` for `briefs/<project-id>/`: one canonical brief,
an allowlisted public record and generated current views. Keep prices, budget
amounts and itemized charges in ignored local accounting. Preserve unknowns;
delivery checks do not establish listening, artistic approval or publication.

Check `docs/craft/field-notes/` for known behavior of the models you are about to
pay for. Inspect anchors before generating. Submit one planned attempt per shot, preserve
the request ID, and poll the existing operation. An uncertain submission retains
its reservation; recover from its record before considering another attempt.
Choose retakes deliberately based on reviewed defects and remaining budget.

Preserve creation-time metadata for every generated source. Maintained clients
freeze the exact prompt, requested/resolved model, effective settings and seed,
reference hashes and API identity before submission; polling retains the private
snapshot with the clip master and adds a privacy-filtered catalog entry. Verify
that receipt when reviewing a take. For any outside generation route, capture
the same evidence at creation and import it with `clips import --snapshot=...`
(see `docs/clip-library.md`). Never infer a hidden model or label a later film
plan as the submitted request. Local renders have no model prompt unless one was
actually used; preserve their recipe and source hashes instead.

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

When the user requests the post-publication wrap-up, use the shared
`post-publication` skill and `docs/post-publication.md` to update documentation,
commit/push reviewed source, archive the final 4K and original sources, remove
verified superseded edit renders under the standard retention policy, and record
a process improvement. Preserve every version during active production.
