# Repository review — October 2026

The repository now has one maintained path from film intent to a native review
export, shared by Codex, Claude Code, the shell and MCP. **Borrowed Light** exercised
that path: a 32.5-second, 1080 × 1920 film with six generated takes, an original
local soundtrack, explicit editorial decisions, and a $11.20 estimated total
including reserve against a $20 authorization.

The useful production knowledge was preserved. The restructuring concentrates
new work around a budget, request identity, source hashes, reviewed frame ranges
and an inspectable edit. It does not rename old film directories or replace their
recipes with a speculative universal framework.

## Scope and evidence

Reviewed root instructions, agent skills/rules, package manifests, MCP registration,
configuration, Google/Claude clients, job execution/recovery, editing/assembly,
analysis/metadata services, representative Python generation/QA helpers, local
scene tools, privacy guards, and workspace/archive storage. A prior review's
budget and terminal-poll findings were reproduced against current code before
being addressed. The existing build and 30 scene/privacy tests passed at baseline.

The installed stack was retained: Node 22.22.2, MCP SDK 1.25.2, Zod 3.25.76,
TypeScript 5.9.3, FFmpeg/ffprobe 8.1.1, and an existing Python environment with
Pillow/NumPy. No install, dependency update, model-weight download, new account,
new generation provider, origin push, repository commit, or old-media deletion
was performed. Research visits to official documentation did not submit assets.

This is an exercised production review, not a security certification of every
historical application. Unrelated work present at the start remains local and
untouched; the initial status is retained in the ignored review workspace.

## Findings and changes

| Priority | Finding and consequence | Result |
| --- | --- | --- |
| High | Configuration responses redacted only a subset of credential aliases; historical keys could be returned to an agent | All configuration values now become presence booleans, including unknown/nested fields; regression covers aliases and nested markers |
| High | The common Veo client could submit outside project budget helpers | Required ledger and stable attempt ID; exclusive lock and atomic microdollar reservation before authentication, uploads or POST |
| High | Bulk execution bought prompt calls and submitted a project without a common all-in quote | `execute_project` refuses before paid work; original code remains for migration reference |
| High | A completed filtered/empty result could remain pending indefinitely | Pure terminal decoder treats filtered, empty and malformed completed output as failure; polling is bounded and resumable |
| High | Retrying after a timeout could buy another take | Separate submit/poll; identical known attempt returns its saved operation; changed input or unknown outcome refuses; uncertain spend stays reserved |
| Medium | Duration snapping and preview aliases made the request differ from the agent's plan | Exact qualified 4/6/8 seconds, GA Quality/Fast aliases, explicit aspect/resolution/audio/seed checks and current rate table |
| Medium | Interrupted job writes could destroy JSON, and corrupt reads silently reset state | Atomic job writes; corrupt reads fail; `resume_job` continues a known operation without another generation |
| Medium | Unrestricted downloaded URLs could receive the Google bearer credential | GCS download restricts HTTPS host and refuses redirects |
| Medium | Legacy handlers returned error strings as successful MCP results | Current SDK registration plus `isError` for refusal/exception paths; real stdio client tests |
| Medium | Default Claude text calls pinned a retired model and older sampling assumptions | Configurable Sonnet 5.5 default, bounded request timeout, supported sampling body; Python QA shortcuts and exact-model cost rate updated |
| Medium | About 35 KB of craft rules loaded automatically, with conflicting production doctrines | 1.25 KB of routing notes; detailed craft moved to `docs/craft/`; one shared production skill under `.agents/skills` with a Claude link |
| Medium | A large MCP catalog mixed paid legacy shortcuts with current production | Ten-tool default profile; historical specialists require `VIDEO_MCP_PROFILE=legacy` |
| Medium | Editing could proceed without proving which source frames had been accepted | Hash-bound acceptance records and integer-frame edit contract; changed source, unreviewed range and output overwrite refuse |

The budget is deliberately conservative. It does not assume all failures are
billed; it retains exposure until saved usage or billing evidence permits a
reconciliation. An accepted request lost before its operation is persisted remains
ambiguous. Local request IDs cannot manufacture provider-side exactly-once
guarantees. The tool refuses to resolve that ambiguity by silently resubmitting.

## What the film changed about the tools

The story is a maintenance machine giving its chest lamp to a dead tree. Its chest
stays empty while the tree lights the greenhouse. The coverage approaches the
choice through progressively closer shots, then returns wide. Read the
[film brief](../briefs/borrowed_light_brief.md) for the treatment and final timing.

Two reference images failed the prop-transfer brief. They were preserved and
excluded before buying motion. The eventual macro anchor came from a local crop
of the tree-growth take's first frame. That creates a stronger spatial match than
another independently generated reference would have guaranteed.

The opening take invented an unwanted lamp lift after about four seconds. The
extraction take changed the arm layout and bulb shape. General contextual QA
flagged both, while the dense duplicate-subject checker passed the extraction.
Those results demonstrate why a single automated pass is insufficient. The edit
uses the clean approach and hesitation, then cuts to the bulb already seated in
the roots. No rerolls were needed. The resulting 32.5 seconds use 67.7% of the
48 generated seconds; paying for a clip does not make its full duration useful.

The final tools follow those observed needs:

- `film.mjs`: local prerequisites, project initialization, dry-run quote, budget
  status, one-shot submission and recovery, source hashes, local delivery.
- `google-image.mjs`: bounded existing Google route with reference hashes and
  usage evidence; no automatic retries or overwritten anchors.
- `edit.mjs`: small frame-addressed editor and review package. Derived typography
  and fades are explicit sources with recipes; they do not expand the core into
  an untested nonlinear editor.
- `score.mjs`: deterministic event-based sound synthesis, using an existing WAV
  writer. The film recipe includes bell, pad, air, mechanical tick and servo cues.
- `production/ledger.ts` and `veo-spec.ts`: common money and capability contracts
  used by the CLI, MCP and shared provider client.

## Agent workflow and compatibility

`AGENTS.md` carries repository boundaries, executable entry points and preservation
rules. `CLAUDE.md` imports it. `.agents/skills/produce-video/SKILL.md` is canonical;
the Claude skill is a relative symlink. Detailed material is loaded for the shot
or technical problem at hand. This follows current official guidance on
[focused Codex instructions](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra),
[repository skills](https://learn.chatgpt.com/docs/build-skills), and
[Claude Code context management](https://code.claude.com/docs/en/best-practices).

Default MCP exposes nine `production_*` tools plus read-only `get_config`.
Existing clients needing `create_job`, `resume_job`, cataloging, voice or assembly
specialists must set `VIDEO_MCP_PROFILE=legacy` and reconnect. Existing direct
Veo callers must supply a ledger and request ID. These are deliberate compatibility
changes. The catalog/search MCP server and old media paths remain unchanged.

The modern host agent performs planning and judgment directly; the old
`src/agents/` HTTP-oriented SDK applications remain experiments. A new orchestration
framework would add another interpretation of state without solving the film's
actual continuity problems. The shell and MCP instead call the same implementation.

Current Sonnet behavior and pricing were checked in the
[official model documentation](https://platform.claude.com/docs/en/models/sonnet-5-5/overview);
the [deprecation list](https://platform.claude.com/docs/en/about-claude/model-deprecations)
supports removing the retired Opus 4 default. Model selection remains configurable.

## Validation and delivery

Primary export: `data/workspace/borrowed-light-v1/final/v2/film.mp4`.
Adjacent `review.html` has a player, shot navigation and delivery evidence.
`final/v1/` preserves the picture edit before local opening/closing polish.

| Check | Evidence/result |
| --- | --- |
| TypeScript and production regressions | Build passed; 16 tests, including actual FFmpeg fixture edit, source protection, deterministic score, protocol error handling, both MCP profiles and cross-process budget contention |
| Existing local suites | 15 scene-lab and 15 privacy tests passed |
| Python changes | Five changed/new modules parsed; exact Sonnet cost fixture passed |
| Shared skill | Skill validator passed; relative Claude link resolves |
| Generated sources | Six eight-second 1080 × 1920, 24 fps takes downloaded and hashed |
| Visual checks | Six contextual clip scans and five dense character-motion scans, 16 paid QA calls in total; flagged frames inspected and excluded |
| Native delivery | Full decode, 780 decoded frames, 32.5 seconds, 1080 × 1920, 24 fps; source hashes retained |
| Sound | Original local stereo score/foley; -19.00 LUFS, -5.89 dBTP, 5.2 LU loudness range; 0.99993 zero-offset correlation after AAC encoding |
| Final inspection | Contact sheets for all shots, final overview, full-size closing title and fade endpoints inspected |

The source and final images are fictional generated material. Automated visual QA
and computational audio checks are not human playback/listening. Browser review
could not be exercised in this session: no browser provider was available, and
the native window lookup failed. The HTML package was generated and its offline
fixture tested. Real-time listening and artistic approval remain open review
items, not claims made by the delivery manifest.

There is still small generated microgeometry variation between scales. The film
does not establish a mechanically continuous bulb transfer. Its ellipsis is an
editorial response to that limitation, preserved in the acceptance records.

## All-in budget

| Category | USD | Basis |
| --- | ---: | --- |
| Six Veo Quality takes, silent 1080p, 8 seconds each | 9.600000 | Qualified $0.20/second list rate |
| Seven Google image attempts, including rejected references | 0.982746 | Saved modality/token usage at dated rates |
| Sixteen Claude Sonnet 5.5 QA calls | 0.217076 | Saved usage, $2/M input and $10/M output |
| Retained storage/network allowance | 0.400000 | Reserve, not a measured invoice charge |
| **Total estimated plus reserve** | **11.199822** | **$8.800178 below the $20 ceiling** |

The maximum reservation before reconciliation was $19.10. No automatic paid
retries or video retakes occurred. All usage evidence and calculations remain in
the ignored film workspace. These numbers are usage/list-price estimates, not
invoice verification; any later invoice difference should be reconciled honestly.
At this edit length, video alone cost about $0.295 per accepted second; the all-in
estimate including reserve is about $0.345 per delivered second.

## Remaining engineering risks

1. **Legacy shell construction.** `services/assembly.ts`, `editing.ts`, `analysis.ts`
   and `clip-metadata.ts` still interpolate local paths/options into shell command
   strings. They are outside the default profile and should be migrated to
   argument-array execution when next exercised, with hostile-filename fixtures.
   Existing successful files do not establish that those paths are safe for
   arbitrary untrusted manifests.
2. **Legacy money accounting.** `tools/vertical/gen-runner.py` still has a flat
   $0.10/second estimate. Do not use that figure for current Quality/audio work.
   Old QA/audio/image helpers do not themselves enforce the new all-in ledger;
   reserve a bounded allowance first. A common library cannot intercept arbitrary
   shell scripts or a separate provider client. Historical budget pots were
   preserved, including unrelated user edits in the existing budget helper.
3. **Global legacy job state.** Atomic writes prevent partial JSON, but the old
   job file is not a transactional multi-process queue. New work uses per-film
   attempt records. Crash recovery may still require private provider evidence.
4. **Capability coverage.** Live qualification covered Quality, portrait, 1080p,
   silent eight-second first-frame generation. Other advertised GA combinations
   have request/rate tests and documentation support, not a paid smoke test in
   this review. New Google Lite/extension/4K controls remain research only.
5. **Boundaries of local file safety.** The new CLI rejects traversal, absolute
   artifact paths and symlink ancestors. This is accidental-escape protection,
   not isolation from another hostile process concurrently rewriting the workspace.
6. **Dependencies.** No upgrades or external package-audit requests were performed.
   Build/test success does not establish the absence of dependency vulnerabilities.

## Storage candidates — suggestions only

At inspection, `data/workspace` occupied roughly 42 GiB and
`data/workspace-archive` roughly 24 GiB in allocated blocks. The largest immediately
interesting items are reproducible intermediate frames and assemblies, not
approved finals. Measurements are approximate and APFS clones can make summed
sizes differ from eventual reclaimed space.

| Candidate for a later cleanup review | Approx. GiB | Required evidence before deletion |
| --- | ---: | --- |
| `data/workspace/carnival-dream/draft-v1/frames-v1` | 3.17 | Preserve source assets, exact audio, recipe, reviewed export and sampled rebuild hashes |
| `data/workspace/carnival-dream/draft-v2/assembly-v1` | 3.14 | Identify frame/assembly intermediates and prove later recipes do not reference them |
| `data/workspace/carnival-dream/draft-v3/assembly-v1` | 2.84 | Same dependency and rebuild check; retain patches and accepted alternatives |
| `data/workspace/carnival-dream/draft-v4-shadow/frames` | 4.67 | Preserve draft/recipe/QA and verify regeneration before releasing frame cache |
| `data/workspace/surveyors-table/scratch` | 1.64 | Mixed recipes, graphics and videos: classify individual intermediates; never delete this whole folder blindly |

The first four directories total about 13.8 GiB of **review candidates**, not
certified disposable bytes. Draft 5's larger current frame tree was left out of
this shortlist. Archive finals, accepted alternatives, original soundtracks,
canonical characters and Hall of Memories source/core material are not cleanup
candidates merely because they are large. Nothing was deleted or moved.

## Privacy and next decisions

The whole-worktree pattern scan retains four findings in pre-existing unrelated
scripts: `tools/angles/accelerate.py:74` and `tools/angles/spin.py:53`
(`personal-email`), `tools/carnival-dream/refinements.py:326` (`personal-email`),
and `tools/hall-of-memories/deep_time_finish.py:105` (`phone-like`). Values were
not echoed and those files were not edited. These are candidate pattern findings,
not a determination that actual credentials were exposed. No staged/outgoing
publication scan is claimed because no repository commit or push was prepared.

The 56 source candidates from this review passed a separate scoped pattern scan
with zero findings and received manual review. The whole-worktree scan covered
156 snapshots and retained the four unrelated findings above. Media, provider
operations, usage records and logs stay ignored. A future
source commit still needs exact staging, identity checks and the full repository
privacy procedure. Do not infer approval to publish the film from this review.

For new models, read the [official-source comparison](video-model-options-2026-10.md).
Runway is the first proposed direct-provider audition for cheap anchored motion
and an independent editing path; MiniMax, Luma, Kling and local LTX cover different
needs. None was integrated or called. Reuse this film's failed transfer and
successful growth shots as the benchmark before authorizing a provider expansion.
