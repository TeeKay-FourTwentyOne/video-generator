# REPEAT collaboration status

[status.json](status.json) tracks the planned scenes and the director's ending
revision. The [brief](brief.md) carries the creative treatment; the
[production record](production.json) carries current production facts.

The film is published. The sealed collaboration page is retained at
`data/workspace-archive/repeat-v1/status/index.html`; its current player uses a
relative link to the retained 4K master. Earlier draft timelines remain history,
while superseded full edits are removed under the archive retention policy.

For a future revision, restore a working copy and build the standard page from
the repository root, passing that copy explicitly:

```sh
python3 tools/production/status-page.py repeat --workspace data/workspace/repeat-revision
python3 tools/production/status-page.py repeat --workspace data/workspace/repeat-revision --check
```

Do not rebuild inside the sealed archive. The retained page includes frame
stepping and the source timeline for the published edit. The focused join
comparison remains private QA evidence. The [published film](https://youtube.com/shorts/M7O0Jh9JFLc)
and [production record](production.json) are the current public references.
