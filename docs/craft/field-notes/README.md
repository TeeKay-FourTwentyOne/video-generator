# Field notes

Short, dated lessons from real productions: what was observed, why it matters,
and what to do next time. These are the durable part of an agent's working
memory, kept in the repository so every agent and every future session sees them.

## How the notes are organized

| File | Covers |
| --- | --- |
| `veo.md` | Veo generation: filters and rejections, motion behavior, native audio, cost behavior |
| `anchors.md` | Image references (Nano Banana Pro), plates, book-ends, continuity across framings |
| `qa.md` | What the frame, clip and clone checks catch and miss; calibration; running them |
| `edit-sound-finish.md` | Editing conventions, sound and mix targets, upscaling, delivery and publication |
| `direction.md` | Working doctrine: autonomy, decisions queued for the director, budget expectations |

Shared topic files hold facts about models and craft; any agent appends to them.
An agent that wants a running log in its own voice adds `<agent>-notes.md` in this
folder (for example `codex-notes.md`). Harness mechanics (shell, timeouts, sandbox,
how to view media) belong in `docs/harness/<agent>.md`, not here.

## Entry format

```
### Title, phrased as the behavior
What happened and where (one to three sentences). Why it happens, if known.
**Apply:** what to do next time.
Source: claude-code · Film · 2026-10-03
```

Rules: one behavior per entry; prefer measured over guessed, and say which;
never include personal names, contact details, credentials, account or resource
IDs, or private project detail (see `docs/source-privacy.md`); when an older entry
proves wrong, edit it and note the correction instead of adding a contradiction;
keep series-specific conventions with their briefs or `series/`, not here.

The initial entries were distilled on 2026-10-03 from Claude Code's production
memory (May to October 2026). Entries without a film name come from several
productions in that period.
