# REPEAT: recording-to-playback joins

Observed 2026-11-15, Codex. The director requested frame-level refinement after
the first full draft, then requested this method for future video production.

The fixed portrait exposed small pose and expression differences. Several
speech takes continued with unwanted words, so leaving their tails longer was
not a free fix. One reaction switched head tilt in the opposite direction.
Trimming improved the candidates but could not remove every expression change.

Bounded searches used 270 × 480 grayscale proxies, a small Gaussian blur, and
weights on face, eyes, mouth and shoulders. We inspected candidate strips and
native neighbors, removed one unnecessary second-reaction cut, then used six
short bidirectional optical-flow bridges in silent gaps, before the UI overlay.
The third-line bridge retained an extra native closing-blink frame and shortened
to three intermediate frames. Its pixel score was worse than the longer version,
but the blink no longer lingered: score ranking is not performance selection.

All indices below are decoded, zero-based at 24 fps. Endpoint columns are the
actual adjacent native frames; bridge frames exclude those endpoints.

| Join | Outgoing endpoint | Incoming endpoint | Intermediate frames | Edit start |
|---|---|---|---:|---:|
| J01 | S01 43 | L01 0 | 4 | 44 |
| J02 | L01 87 | S01B 0 | 6 | 136 |
| J03 | S01B 42 | L01 45 | 6 | 185 |
| J04 | L01 132 | S01C 0 | 6 | 279 |
| J05 | S01C 44 | L01 56 | 3 | 330 |
| J06 | L01 117 | S03 0 | 6 | 395 |

The 31 intermediate frames are separate local media, not native generated motion.
Native speaking frames and edit positions remain `[4,44)`, `[154,185)` and
`[297,329)`. The 611-frame main plus unchanged 59-frame tail is 670 frames,
27.9167 seconds. The renderer recipe is:

```json
{
  "fps": 24,
  "bridges": [{
    "id": "J01",
    "from": {"clipId": "clip_FROM_SHA256", "sha256": "FROM_SHA256", "frame": 43},
    "to": {"clipId": "clip_TO_SHA256", "sha256": "TO_SHA256", "frame": 0},
    "frames": 4
  }]
}
```

## Retained evidence

Paths below are relative to private `data/workspace/repeat-v1/`. Follow the
production record if that workspace is subsequently archived.

- `recipes/inspect-joins-v3.py`, `qa/joins-v3/ranked.json`: project-specific
  search, candidates and alternatives.
- `recipes/joins-v3b.json`, `render/joins-v3b.recipe-receipt.json`: selected
  bridge endpoints, hashes and packed intermediate-frame ranges.
- `recipes/draft-v3b-picture.json`: exact native/derived frame mapping.
- `qa/joins-v3/endpoint-continuity.json`: all bridge endpoints match adjacent
  native frames, avoiding off-by-one duplication/skips.
- `qa/joins-v3/J01-bridge-strip.png` through J04, plus
  `J05-bridge-v3b-strip.png` and `J06-bridge-v3b-strip.png`: inspected frames.
- `qa/joins-v3/final-join-comparison.json`: old boundary differences and maximum
  adjacent differences across replacements, with identical weighting. Those
  numbers describe positional discontinuity, not an artistic-quality percentage.
- `qa/joins-v3/joins-before-after.mp4`: twelve-second silent comparison; six
  equal-speed windows aligned to each old cut/new bridge start.
- `final/draft-v3/preservation.json`: all tail decoded frames match draft-v2;
  complete AAC packet and decoded PCM hashes match; speaking-frame selection
  and timing match. The re-encoded main does not claim pixel identity to v2.
- `qa/joins-v3/analysis-check.json`, `cloud-sync.json`, `use-records.json`:
  seventeen project clips processed/backed up, including unused bridge versions;
  underlying source uses retained.

Every bridge frame was inspected. Real-time listening was not claimed. A later
4K request authorizes finishing; it does not manufacture a listening result.
