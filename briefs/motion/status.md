# Collaboration status

The source is [status.json](status.json). The published production’s frozen page is retained at `data/workspace-archive/motion-v1/status/index.html` and may be served read-only. Verify it with `python3 tools/production/status-page.py motion --check`; do not rebuild into the sealed archive.

For future revisions, restore a verified working copy and use the status builder’s `--workspace` override for that copy. The director comments in the production conversation using stable IDs P1, P2, P3, F2, F3, F4 or C1–C4. Preserve comments privately, apply them to the status source, and rebuild only in the new active workspace. Financial records and provider receipts stay private.

The adjacent `status/audition.html` preserves the historical still audition, including camera, phone-frame and original-source views. Its input manifest is `look-audition.json`; `tools/motion/audition.py` documents the recipe. Raw inputs, derivatives and hash receipts remain private. The final 4K cut is the retained playable delivery.
