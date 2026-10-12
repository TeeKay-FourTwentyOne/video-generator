# Clip catalog

Public metadata for local video assets. Start with the
[clip library guide](../docs/clip-library.md) for search, import, frame-range editing,
analytics and the historical import's evidence limits.

The [browsable index](index.json) lists labels, project collections, durations,
dimensions, prompt availability and use counts, with links to each full record.
Search a project name or character with `npm run clips -- search QUERY`.

- `clips/`: one JSON record per SHA-256 content ID.
- `uses/`: one JSON record per evidenced edit occurrence, linked by `clipId`.
- Schemas: [clip](../docs/schemas/clip.schema.json) and
  [use](../docs/schemas/clip-use.schema.json).

The corresponding bytes live in ignored `data/clips/`. Public hosting and media
licensing are pending. Metadata can be searched and validated without the media.
