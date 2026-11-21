# No Enemy production page

The page is built from [status.json](status.json), using the shared production-status workflow. Its current workspace is recorded in [production.json](production.json).

```sh
data/tools/clip-analysis/semantic-v1/python/bin/python tools/production/status-page.py no-enemy
data/tools/clip-analysis/semantic-v1/python/bin/python tools/production/status-page.py no-enemy --check
```

The generated page is `data/workspace/no-enemy-v2/status/index.html`. Images and generation receipts remain in the ignored workspace. Review notes in this conversation are applied to the stable scene IDs and decisions in the status source. Generated images await director review; technical inspection does not establish approval.

The current set is **9:16 portrait**, as selected by the director. A full-size review
gallery is at `data/workspace/no-enemy-v2/status/anchors.html`; all original images
and their prompts are retained under `refs/` and `prompts/images/` in the workspace.
The first widescreen design pass remains preserved as reference.
