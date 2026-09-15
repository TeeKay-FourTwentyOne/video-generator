# Scary Woods — series brief

Episode 01 is published: https://youtube.com/shorts/dsMDFQvEOew

Scary Woods follows three mismatched travelers through a miniature forest with
more personality than reliable signposts. Dry exchanges, physical reactions and
warmly eerie discoveries carry the comedy. The established format is vertical
9:16 with a stop-motion appearance, expressive close-ups and brisk editing.

## Accepted characters and world

| ID | Character / environment | Visual and performance direction | Voice |
|---|---|---|---|
| T2 | Wood | Tall carved-wood planner; officious posture and fragile dignity | Luke |
| C3 | Clay | Squat clay skeptic; grounded movement and economical reactions | Baxter |
| P2 | Paper | Folded accordion-paper explorer; bright curiosity and quick questions | Elowen |
| F1 | Spirit | Small felt woodland host with unruly hair and mischievous warmth | Iron Rose |
| E1 | Forest | Tangled miniature woodland, winding path and a warmly lit hilltop cabin | — |

The blue crystal ball and the cabin interior establish the pilot's transition
into storytelling. Episode 01 ends inside the ball with Spirit saying,
“There was once a ship...” Episode 02's plot and shot guide remain to be discussed.

## Production conventions

- Preserve the contrasting wood, clay, paper and felt construction styles.
- Use the built-in OpenAI image-generation tool for new imagery and keep a local
  generation-call ledger. Its exact image-model identity is not exposed.
- The pilot uses generated 2D imagery, masks, sprite compositing, discrete poses
  and local camera moves. No complete 3D character rigs or UV-textured models
  were produced; new coverage must be judged against the retained references.
- Use close-ups to support dialogue and comic reactions. Keep geography readable
  when cutting between similar wide views, and preserve visible prop continuity.
- Always include material-styled captions with the character labels Wood, Clay,
  Paper and Spirit. Placement normally favors the upper third, with adjustments
  to protect faces and story objects. See the [subtitle guide](forest_spirit_subtitle_style_v1.md).
- Finish picture and audio at 1080 × 1920 and 24 fps, then use the standard local
  2× Real-ESRGAN process for the vertical 2160 × 3840 master.

## Published pilot and reusable archive

The [Episode 01 brief](forest_spirit_episode_01_brief.md) and
[final shot guide](forest_spirit_episode_01_dialogue_shot_guide_v1.md) describe the
released 38-second, 912-frame film.

Its local archive is `data/workspace-archive/forest-spirit/`. It retains the final
4K master, exact approved upscale input, clean picture, audio stems, selected
dialogue, caption artwork, source images, reusable sprites/masks, model weights
and production history. Intermediate edits, held-frame caches, old audition
clips and superseded mixes were removed to reduce storage.

The archive's `README.md`, `project.json` and `notes/next-episode.md` are the active
handoff. Historical notes record earlier decisions and may reference removed
intermediates. Use [the finishing entry point](../tools/forest-spirit/README.md)
to verify retained files or rebuild the final presentation.
