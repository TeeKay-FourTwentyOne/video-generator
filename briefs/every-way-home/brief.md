# EVERY WAY HOME — brief v1

[Current production record](README.md).

**Published:** https://youtube.com/shorts/MR1BPNIdsDM (YouTube Shorts, 2026-11-04, user-confirmed)

a][ productions · 2026-11-04
Claude Code, from a workshop brief: something visually distinct that is only possible, or only easy, with generated video and an agent that can make programmatic changes. The director chose this idea as the first of two (the second, a many-character room in the manner of Rybczyński's *Tango*, follows in its own project).

## 1. Concept

A woman sits in a chair at the near end of a long, bare room. She stands and walks to the window at the far end. That is the whole action, and it is filmed five times from the same first frame to the same last frame. Because both ends are locked, the five takes can only differ in the middle: how soon she rises, which side of the table she passes, whether she stops to touch the cup, how fast she goes. The five takes are composited as translucent selves over one plate. She is one solid woman in the chair; at the first step she thins into five; the five take their own ways down the room; and at the sill they gather back into one solid woman, looking out.

Generated video supplies five different performances from identical boundary conditions, which no camera can do. Local code supplies the rest: the plate, the mattes, the stacking, the sound of five sets of footsteps collapsing into one.

The second half is the return. At the window she turns to face the room; the selves leave the window one at a time, each by its own way, reach the chair, turn and sit, and she becomes solid again. The last self never leaves: the film ends with her home, back to us, and one translucent self still at the window, facing her.

## 2. Format

- 1080×1920 (9:16), 24 fps, H.264 high + AAC 48 kHz stereo.
- About 25.7 s (616 frames): out, the turn, back, and the one that stays, then a fade to black.
- One fixed high camera. No cuts inside a movement. Photoreal, muted, a bottle-green dress against lime-washed walls so the ghosts read. Wordless; no music; native room sound from all five takes summed.

## 3. Shots

| # | Beat | Take |
|---|---|---|
| S1a–S1e | Chair to window, five routes: straight down the middle; slow along the left wall; along the right wall past the stool; a stop at the table to touch the cup; fast and early, then waiting. | 8 s each, same first and last frame, native audio |
| M1 | The composite of the five: solid, then five translucent selves, then solid at the window. | local |
| T | At the window she turns to face the room. | 4 s, same technique, solid |
| S2a–S2e | Window to chair, five routes, each ending seated with her back to the camera. | 8 s each, same first and last frame |
| H | A held self at the window (rejected: an invented second woman); replaced by a loop of a return take's still head. | 4 s |
| M2 | The whole film as one layered composite: five leave, one stays. | local |

## 4. Agent's choices

- Five routes written explicitly rather than five samples of one prompt: the divergence is the subject, so it is authored.
- Ghosts by difference matte over a plate derived from the takes themselves (the temporal median), so the room keeps Veo's own light; stacked at partial opacity so that agreement reads as solidity and disagreement as thinness.
- Both anchors pinned to the plate programmatically so the only pixels that differ between the first and last frame are the woman; nothing else can slide.
- No title on screen (director's call). The ending, the self that stays, is mine; the page lists it as a decision the director can reverse at no cost.

## 5. Status

- 2026-11-04: planned, built and cut the same day. Three images (one attempt each), five Quality takes with native audio, all first attempts, all kept. Veo gave the five nearly the same timing, so the composite staggers them by about a second each; v1 is 240 frames (10 s) with the five native tracks mixed at the same offsets. Technical checks passed; the director has not yet watched it. Decisions and the dated log are on the status page (`status.json`).
- 2026-11-04 (later): the director approved the return and asked for an ending that makes it a complete film. Seven more takes (the turn, five returns, a held self); the held self rejected for an invented second woman and replaced by a loop. v2 is the whole film, 616 frames (25.7 s), rendered as one layered composite with a twelve-track native mix. Technical checks passed; the director has not yet watched v2.
- 2026-11-04 (evening): the director approved v3 ('absolutely perfect. Seamless.'), authorized the 4K, and published it the same day. Closed out under the standard retention.
