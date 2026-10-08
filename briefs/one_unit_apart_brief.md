# ONE UNIT APART

**Subtitle:** Six or seven colors for an infinite plane

**Format:** 56 seconds, 16:9, 1920 × 1080, 30 fps; native 1080p

**Current delivery:** v3, with ElevenLabs narration

**Status:** Native v3 delivered; YouTube link recorded.

**YouTube:** https://youtu.be/nnR-HPxd6WI

**Workspace:** `data/workspace/one-unit-apart-v1/`

YouTube URL supplied by the user on October 7, 2026. Public availability has
not been independently verified.

## Premise and intent

How many colors does infinity need? Color every point on a plane so that points
exactly one unit apart have different colors. A triangle demands three colors;
a seven-point pattern demands four. Seven colors can cover the entire plane.
The film then introduces the result presented in OpenAI's mathematics
collection: five colors cannot suffice, leaving six or seven.

The aim is a visually compelling, factual introduction to the Hadwiger–Nelson
problem within the requested 45–60 seconds. Family 158 was selected because its
rule is immediately understandable, its classical constructions can be drawn
exactly, and the remaining uncertainty gives the film a strong ending. The new
result is stated and attributed; the film does not attempt to animate its proof.

## Visual and sound direction

Luminous points and precise geometric lines sit against a dark ink-blue field.
Warm ivory typography and seven jewel colors give the mathematics clarity and
texture. A rotating unit ruler, traced graph edges and an expanding hexagonal
field carry the movement. The final pullback turns a small distance rule into
an apparently endless landscape.

George, ElevenLabs' warm British storyteller voice, supplies the narration using
Eleven Multilingual v2. A restrained original electronic score uses synthesized
pads, bells, air and small rhythmic ticks. The mix keeps the voice prominent.
Fourteen sentence-level caption cues accompany the finished film.

## Edit

| Time | Beat | Mathematical purpose |
| --- | --- | --- |
| 0–6 s | An infinite canvas | Establish the colored plane and title. |
| 6–14 s | One rule | A fixed-length ruler turns: endpoints exactly one unit apart must differ in color. |
| 14–24 s | Three, then four | An equilateral triangle develops into the seven-vertex, eleven-edge Moser spindle. |
| 24–36 s | Seven works | Reveal the repeating seven-color hexagonal construction; matching points are either too close or too far apart to violate the rule. |
| 36–47 s | Five is impossible | Attribute OpenAI's unrestricted no-five-coloring result and identify the supplied Lean formalization. |
| 47–56 s | Six or seven | Pull back across the plane, retaining both possibilities and closing on “A simple rule. An infinite puzzle.” |

## Mathematical sources and accuracy

- **Collection:** [OpenAI math repository](https://github.com/openai/math).
- **Featured paper:** OpenAI, [The Euclidean plane is not five-colorable](https://github.com/openai/math/blob/main/preprints/The-Euclidean-plane-is-not-five-colorable-September-23-2026/paper.pdf), September 23, 2026.
- **Formalization scope:** [Family 158](https://github.com/openai/math/blob/main/lean/docs/158.md). The supplied lower bound applies to arbitrary colorings, without measurability or continuity assumptions.
- **Source snapshot:** `adc7f1241b42e322a6451854ab7e4b4c146bf78a`; selected source copies and hashes are retained in the workspace.

The rule concerns distance **exactly one**, not all distances below one. The
Moser spindle demonstrates a four-color lower bound; it is not evidence for the
new six-color lower bound. The spindle and seven-color construction are
classical mathematics, not inventions credited to OpenAI.

The depicted hexagons have diameter 0.90. Points in different hexagons of the
same color are separated by more than 1.16, giving strict margins on either
side of the forbidden distance. A finite crop represents the repeating plane.
The featured result narrows the answer to six or seven; it does not determine
the exact minimum.

The paper source, formalization scope and actual solution theorem were read.
The production did not compile Lean or independently audit the full new proof.
Local geometry checks verified unit-edge lengths, exhaustively rejected all
three-color assignments to the spindle, and checked a valid four-color witness.

## Production and delivery

All pictures are deterministic local mathematical animation, rendered with
Python, NumPy, OpenCV and Pillow and finished with FFmpeg. The original score
was synthesized locally. No generated image or video footage was used.

The narration used one continuous ElevenLabs take, split into seven edit cues
using provider alignment timestamps. All cues fit without changing speech
speed. The provider reported **535 included subscription credits**; no
additional cash charge was expected within the checked quota. Detailed usage
records and the project ledger remain in the ignored workspace.

Paths below are relative to `data/workspace/one-unit-apart-v1/`:

- Film: `final/v3/film.mp4`
- Review page: `final/v3/review.html`
- Transcript: `final/v3/transcript.txt`
- Source inventory and claims: `sources/manifest.json`, `sources/claims.json`
- Geometry verification: `qa/geometry.json`
- Delivery verification: `qa/completion-v3.json`
- Editable production: `film.json`, `recipes/`, `edit/`, `audio/`

The final file contains 1,680 frames and passes a full decode. Its compressed
picture stream is identical to v2; the original score source and earlier
versions are preserved. Final audio measures −16.0 LUFS and −2.0 dBTP. Script
alignment, cue timing, caption loading and browser seeking were checked.
Technical checks do not constitute a full human listening review. No upscale
was performed. The YouTube link above was supplied by the user.

The prepared YouTube copy is in [one_unit_apart_description.md](one_unit_apart_description.md).

## Credits

Concept, script, mathematical animation, editing and original synthesized
score: OpenAI Codex. Synthetic narration: George, ElevenLabs, Eleven
Multilingual v2. Featured mathematical result: OpenAI, family 158 of the
OpenAI math collection. Classical constructions: the Moser spindle and the
seven-color hexagonal coloring of the plane.

#MathAnimation #HadwigerNelson #OpenAI #gpt6

https://github.com/TeeKay-FourTwentyOne/video-generator
