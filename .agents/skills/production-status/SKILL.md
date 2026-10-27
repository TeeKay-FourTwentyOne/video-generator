---
name: production-status
description: Build and publish a film's collaboration status page from briefs/<project-id>/status.json. Use at planning time for every new production, after each generation or review batch, and whenever the director's comments change a scene's state. One page per project, scenes with bulleted beats and authored statuses, open decisions and a dated log; no prices.
---

# Production status page

A production gets one status page from the day it is planned. It is the high-level
summary the director and the agent collaborate on: the film in one paragraph, each
scene with its beats as bullets, an authored status on every line, the decisions
waiting on the director, and a dated log. It is not a player, a ledger or a QA
report; those stay in the workspace.

This is the shared workflow for Codex and Claude Code;
`.claude/skills/production-status/SKILL.md` links here.

## Source of truth

`briefs/<project-id>/status.json` (Git-bound, public). Schema version 1:

- `projectId`, `title`, `updated` (ISO date), `format` (one line), `phase` (a word
  such as `planning`, `anchors`, `motion`, `edit`, `review`, `delivered`, `published`),
  `logline` (the film in two sentences), `overall` (where things stand), `next`
  (the next concrete action).
- `statuses`: the vocabulary, `{ key: { label, tone, description } }`, tone from
  `muted`, `active`, `attention`, `good`, `bad`. The default vocabulary is
  `planned`, `anchored`, `generating`, `review`, `revision`, `accepted`, `hold`,
  `dropped`, `approved`; copy it from `briefs/coming-attractions/status.json`
  and adapt only when the project needs another state.
- `scenes[]`: `{ id, number, title, status, summary, image?, segments[], next? }`.
  `number` is whatever the film counts by (an era, a chapter, an act). Each
  segment is a beat or a major section inside the scene:
  `{ id, title, status, detail?, image? }`. Start a segment title with its shot
  code (`S01`, `N2`, `C4b`) when one exists; the page uses it as the caption.
  Scene and segment IDs are stable lowercase slugs; never renumber them, because
  comments and links point at them.
- `decisions[]`: `{ id, title, status: open | decided, detail }`, the queue for the
  director. Record a decision by flipping its status and quoting the director in
  `detail`; do not delete it.
- `log[]`: `{ date, text }`, one line per session or milestone, newest last.
- `drafts[]` (optional): the cuts the director can watch, oldest first; the last
  one is the current draft and gets the page's player. Each is
  `{ version, date, title?, film, poster?, posterFrame?, fps, frames, width?, height?, note?, segments[] }`:
  `film` is the workspace-relative native review film, `poster` an image or
  video for the player's still (default: the film, at `posterFrame`), and
  `segments[]` is the integer-frame timeline of the cut, in order and
  contiguous: `{ label, shot, frame, frames, sourceFrame?, source? }` where
  `label` is the edit segment (`S02b`), `shot` the shot code the beats use
  (`S02`), `frame` the first edit frame, `frames` the length, `sourceFrame` the
  first frame used from the source, and `source` the workspace-relative local
  render when the segment is not cut from the shot's generated take. Build it
  from the edit manifest and timeline, never by hand.
- `image` values are workspace-relative paths to an anchor PNG/JPEG or a local
  render MP4 (the middle frame is used). They are inlined as small thumbnails.

Rules the generator enforces: known statuses only, unique IDs, ISO dates, portable
image paths, and no money text anywhere (prices, budgets and spend stay in the
ignored workspace and `data/accounting/`). Rules it cannot enforce: a status is
authored from a decision or a reviewed result, never inferred from a file
appearing on disk; a technical check does not make anything `accepted` or
`approved`; `approved` is the director's word only.

## Build

```sh
python3 tools/production/status-page.py PROJECT_ID            # writes <workspace>/status/index.html
python3 tools/production/status-page.py PROJECT_ID --check    # verifies the page is present and fresh
```

The workspace comes from `briefs/<id>/production.json` (`workspace.path`), else
`data/workspace/<id>-v1`, else `--workspace`. The generated HTML stays under the
ignored workspace. The template is `tools/production/status-page.html`; the page
is self-contained apart from Google Fonts and works in light and dark themes.

## Publish and collaborate

Publish the generated page where the director can comment on it, and republish
to the same URL after every rebuild so links and comments keep their meaning.

- Claude Code: the `Artifact` tool, `file_path` set to the generated
  `status/index.html`, same path on every republish (pass `url` when resuming
  from another session). Record the returned URL in the ignored
  `<workspace>/status/artifact.json` as `{ "url": ..., "published": "<date>" }`
  and in the agent's project memory. Read the director's comments with
  `ArtifactComments` at the start of a session and fold them into
  `status.json` (statuses, decisions, log), then rebuild and republish.
- The draft player (Claude Code): the page cannot inline a film, so the current
  draft's video is an artifact asset. Encode a review copy under the asset
  limit (720 by 1280 H.264 with faststart, same frame count and frame rate as
  the film, about 1.5 Mbit/s for a minute) into `<workspace>/status/`, publish
  the page once with `capabilities: {assets: {}}`, upload the copy with the
  `Artifact` tool (`url`, `asset: true`, `file_path`), then record the result in
  the ignored `<workspace>/status/assets.json` keyed by the draft's `film` path:
  `{ "<film>": { "url", "id", "review", "sha256", "width", "height", "uploaded" } }`.
  Rebuild and republish; the generator reads that file and renders the player,
  a readout of edit time to the millisecond with the frame number and the
  segment's source frame, one-frame stepping, a copy-timestamp button, the shot
  timeline and a time link beside every beat. Without an entry the page says the
  draft is not on it yet. Replace the asset when the draft changes; the review
  copy is a convenience, the native film in `final/` remains the deliverable.
- Other harnesses: serve or share the same HTML file by the harness's own means;
  keep the comment channel's notes in the workspace and fold them in the same way.

The artifact URL is private by default and is not written into Git-bound files.

## When to run

1. **Planning**, before any generation: create `status.json` with every scene and
   beat as `planned`, the decisions queue, and the first log line. Build and
   publish. This is part of the initial production steps in `docs/production.md`.
2. **After each anchor, generation or review batch**: update the lines that changed
   (and only those), add a log line, bump `updated`, rebuild, republish.
3. **After the director comments**: apply each comment to the exact scene, beat or
   decision it points at, quote the decision in `detail`, rebuild, republish.
4. **Delivery and wrap-up**: set the phase and the scene statuses from the
   director's words; the page stays as the project's readable history.

Keep `production.json` the authority for public status (`planned`, `producing`,
`review`, `delivered`, `published`); `status.json` carries the finer scene-level
state and must not contradict it.
