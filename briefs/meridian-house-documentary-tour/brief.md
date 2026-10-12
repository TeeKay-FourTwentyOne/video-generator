# Meridian House — documentary Veo walkthrough

[Current production record](README.md).

This document preserves the retained creative and production history. Dated plans and technical observations describe their original sessions; the current record states only supported production facts.

Status: the user selected the 24-second full-turn version for review on
2026-09-14. Eight Veo attempts and two interior image generations remain recorded.
Authorization and unreconciled billing remain in the local ledger.

## Proposed finished cut

24 seconds, 16:9, 1080p, 24 fps. Three eight-second Veo 3.1 Quality clips follow
the existing atrium-to-library-and-return camera route. Finish locally with clean
handoffs and a 4K export. Preserve neutral daylight, unlit opal lamps, quiet room
ambience and the documentary materials. No score, narration, people, pulsing
lamps, moving orrery, magical effects or dramatic camera presentation.

| Time | Motion | Shared endpoint |
| --- | --- | --- |
| 0–8 s | Leave the front atrium and pass through the left library arch | Inside library, facing desk and shelves |
| 8–16 s | Approach the reading area and turn right to face the atrium | Library view back through its existing arch |
| 16–24 s | Walk back through the same arch and return to the front atrium mark | Original documentary atrium image |

The approved `documentary-v1/selected/anchor-00.png` is the canonical opening and
return image. Reuse its exact normalized pixels at both ends. Generate only two
new interior photographic anchors, using the original tour's camera marks 02 and
04 as spatial guides and the selected documentary look as the finish reference.
These anchors fill the interior coverage missing from the eight atrium rotations.
The existing rotation images are not a seamless texture projection and must not
be stretched onto the original mesh to supply translated viewpoints.

## Authorization and source limits

Additional production was authorized on 2026-09-13; the ceiling and all prior reservations remain in the local ledger. Interior anchors use the built-in image tool with the existing geometry and selected photographs, replacing the proposed Nano Banana submissions for this pass. The recipe permits at most four image calls and eight Veo calls. No automatic retries: pre-log every submission, and do not treat a failed request as released capacity.

## Preparation and acceptance

Workspace: `data/workspace/meridian-house/documentary-veo-v1/`.
The local plan retains the exact intended prompts, source hashes, endpoint
references and a labeled geometry-only camera guide. The guide tests translation
through the doorway; it is not documentary footage or a generated video result.

Before Veo submission, inspect the two new photographic anchors for room identity,
invented windows or props, lamp state, material continuity and registration of
large architectural boundaries. The canonical atrium master governs the orrery;
the slate-blue library has the existing shelves, desk, rose chair, rug, paper and
unlit green-shaded desk lamp. The fixed wall ring is a wall ornament, not a hanging
object, mirror, portal or additional orrery.

Review each returned clip for rigid architecture, unwanted object animation,
appearances/disappearances, black/frozen frames and audio anomalies. Inspect dense
samples during doorway crossings and the library turn. Locate the actual shared
anchor frames inside the files before trimming; the preceding tour's matching
bookends appeared before the file ends. Prefer local trims and timing adjustments
over another paid generation. First/last frames constrain the endpoints and do
not guarantee spatially correct motion in between.

Use the established local visual/technical review path; no new review provider,
publication, source commit or push is part of this request.

## Delivery and limitations

The user selected `edit/meridian-house-documentary-full-turn-review.mp4` as the
primary review version on 2026-09-14: "Preserve the full turn for review."
It is 24 seconds, 16:9, 1080p, 24 fps, and retains the complete middle turn.

**Review flag, 8-16 seconds:** the shelving changes and an extra ceiling fixture
appears during the library rotation. These defects remain visible for review.
This delivery choice does not approve the result as a geometrically exact tour.

The alternate clean edit remains `edit/meridian-house-documentary-24s-1080p.mp4`,
with the local Lanczos upscale `edit/meridian-house-documentary-24s-4k.mp4`.
Only that alternate makes a hard cut at 12.25 seconds and interpolates the two
calm library portions. The selected full-turn review uses the reverse-generated
middle take, restored to the intended direction locally, with matched joins at
8 and 16 seconds. The canonical atrium image is inserted at the opening and final
frame before encoding. Applying this preference changed no media and added no spend.

The selected entry and return are improved second takes. Brief background
shelving drift and small orrery-band changes remain; this is not a geometrically
exact continuous reconstruction. Native audio was largely silent with brief
transient bursts; quiet filtered indoor-air noise was synthesized locally for
continuous room tone. Audio levels were checked, but no listening review was possible.

Generation is stopped. Eight eight-second Quality requests and two interior
image generations are recorded; authorization, estimates and retained reserves
remain in the local ledger. All prompts, attempts, decisions, hashes and local
finishing recipes remain in the workspace. No publication, source commit or push
was performed.
