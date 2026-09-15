# Scary Woods — character subtitles v1

Subtitles are a permanent part of the series presentation. Burn them into the
primary episode export, including phone review copies and future revisions.
Retain clean masters as production sources. Use **Wood, Clay, Paper, and Spirit**
until character names are chosen; never display voice-performer names or internal
asset IDs in captions.

## Character treatments

| Character | Material and lettering | Colors |
|---|---|---|
| Wood | Chamfered woodcut plaque, engraved serif, thin brass details | Espresso panel, warm cream lettering, muted amber border |
| Clay | Rounded terracotta tablet, sturdy rounded lettering | Brown clay panel, ivory lettering, warm terracotta edge |
| Paper | Folded parchment strip, hand lettering, small typewritten label | Pale parchment, dark brown lettering, red character label |
| Spirit | Moss felt panel, stitched inset border, italic lettering | Moss green panel, pale cream lettering, sage edge |

Use a small character label above the spoken words. Material styling must support
quick reading. Keep text stable while a line is spoken, with a restrained shadow
and sufficient panel opacity for both dark interiors and the bright blue ball.
The first pass uses single-line dialogue, without animated word highlighting.

## Placement and timing

Prefer the upper third of the vertical frame. Move the caption to the lower third
or raise it slightly when the default would cover a face, a speaking mouth, a
gesture, or a story object. Choose a placement for the entire cue; do not make it
chase the character. Keep the same character treatment when the position changes.
Check full resolution and phone size. Future longer lines may wrap; never shrink
dialogue until it becomes hard to read on a phone.

Align captions to the recorded words. A lead of roughly two frames at 24 fps is
used in Episode 01, with short reading holds after speech. Respect changes of
speaker and shot boundaries. Every spoken line must be captioned, including
off-camera narration. Keep an SRT companion for accessibility and later editing;
the artistic design is burned into the video itself.

## Episode 01 implementation

The published 38-second edit has eleven cues and thirty spoken words. Wood and the
final Clay close-up use the lower third. Paper's ball-side close-up uses the lower
left; the remaining captions use the upper third or a raised upper placement.
Existing audio and picture timing are retained.

Local panels and exact cue coordinates are retained at
`data/workspace-archive/forest-spirit/sources/captions/`.
The reusable artwork generator is `tools/forest-spirit/captions.swift`;
`tools/forest-spirit/finish.py` applies retained panels to the clean picture.
The published primary master is `final/scary-woods-episode-01-4k.mp4`
inside the local archive.
