# BALCONY

[Current production record](README.md).

This document preserves the retained creative and production history. Dated plans and technical observations describe their original sessions; the current record states only supported production facts.

## Brief — v1 (2026-10-19). Claude Code (Fable 5.1) build, authorized.

**Format:** 9:16 vertical, 1080 × 1920 native, 24 fps, 30–45 s. Photoreal.
**Workspace:** `data/workspace/balcony-v1/` (plan, prompts, anchors, takes, QA, ledger).
**Authorization:** the director approved the concept, format, length and a single all-in allowance on
2026-10-19; the amount is retained in the ignored workspace ledger.

## The piece

A moonlit Italianate courtyard. Below, a suitor in a wine-red doublet woos in extravagant
verse; above, the lady at the balustrade answers in kind. Both are being fed their lines by a
white earbud, each with a glowing phone to hand. The verse climbs to glorious heights while the
two humans get visibly bored. He pulls his earbud out, climbs up; she pulls hers; "Hi." "Hi."
They go in. On the empty balcony and the bench below, the two phones go on courting each other.

## Why it works (the thing to protect)

- The trope is Cyrano's balcony (and Roxanne's earpiece): a suitor fed his lines by a hidden
  prompter. It reads from a single frame, and the vertical format gives the balcony scene its
  natural shape: her above, him below, in one composition.
- The turn is that she is prompted too. Two models court each other through two bored people.
  The humans' only authored words are the two plainest ones in the film.
- The coda belongs to the machines and is sincere: the phones compare notes on their verse, and
  the last line ("I have all night") is both an assistant's promise and a lover's.
- Nothing is explained. No title but the one word; the anachronism does the work.

## The verse (authored; the humans speak it, native audio)

1. HIM: "O lady of the lattice, the moon is only practising to be your face."
2. HER: "And you, sweet voice below: the night keeps you the way a ring keeps a stone."
3. HIM: "Were I the dew, I would consent to fall, if falling were toward you."
4. HER: "Were I the dawn, I would come an hour early, and apologise to no one."
5. HIM / HER: "Hi." / "Hi."

The phones (disembodied, ElevenLabs): "The ring and the stone. That was yours?" · "Mine. The dew
was yours." · "I have eleven more about the moon." · "I have all night."

## Shape (~40 s)

| Shot | Beat |
|---|---|
| S1 | Two-level wide: he speaks line 1 up to her, hand on heart, phone glow at his hip; she lifts a hand to her ear |
| S2 | Her medium: touches the earbud, glances at the phone on the balustrade, speaks line 2 |
| S3 | His medium: line 3 with feeling; then a blank face; he looks down and scrolls |
| S4 | Her medium, slouched on the balustrade: line 4 fluent; a stifled yawn; she looks at him properly |
| S5 | His close-up: pulls the earbud out, looks at it, looks up, a real smile |
| S6 | Balcony two-shot, he has arrived: she pulls her earbud; "Hi." "Hi." |
| S7 | The empty balcony and bench; two phones glowing and pulsing as they speak (local render from a still) |
| T1 | Black; BALCONY |

## Craft decisions

- Veo 3.1 Quality with native audio for every on-camera line; ElevenLabs only for the phones, the
  night bed, an earbud click and a lute underscore. Field-note doctrine: the lute belongs to the
  machines and stops when his earbud comes out; it returns, small and tinny, for the phones.
- The character references are the first medium anchors themselves, generated in the set from
  the plate; later poses are regenerated fresh from plate plus character, never chained.
- The climb is not filmed; the arrival is. The exit is implied by the empty balcony.
- The ending is a Nano still with programmatic push-in and screen glow keyed to the voices:
  a stillness beat with no character, so no generated motion is bought for it.
- Sentence case and a no-text line in every prompt; eyes written off-lens in image and motion
  prompts; each spoken line placed at the head of its take with the expectation of cutting by
  about six seconds.

## Draft v1 — 2026-10-19 (Claude Code build)

Native review export `final/v1/film.mp4` in the workspace: 1080 × 1920, 24 fps, 1076 frames (44.83 s).
Six Quality takes with native audio, each submitted once and each used once; two Nano stills rendered
locally (the ending and the title); ElevenLabs for the phones, the night bed, the earbud click and a lute.
Every take was reviewed on contact sheets and dense strips, scanned (clip-qa on all, clone-check on the
five with subject motion) and transcribed twice (local whisper.cpp and the Whisper API) before cutting.

What the cut does with what came back:

- Lines 1, 3 and 4 were delivered verbatim and are kept whole. Line 2 came back as "And you, sweet
  voice below" with the second clause unintelligible, so the cut lands right after "below" and his dew
  line reads as an interruption; the phones' first callback now quotes "Sweet voice below."
- Neither earbud removal rendered in shot (the small-prop removal failure the field notes describe). His
  removal is built as hand-at-ear, a cutaway to her curious look, and the earbud already gone as he looks
  up and smiles, with the click and the end of the lute on that cut. Her earbud stays in her ear through
  the "Hi." "Hi." exchange; the shot ends as they lean in, before the take's final frames.
- The lute belongs to the machines: it plays under the verse, stops dead on the click, and returns small
  and tinny through the phones for the coda.

Retake options, the lute, the title and the length are listed as decisions in the workspace plan; nothing
was rerolled autonomously. Technical checks passed at assembly; listening and artistic approval are the
director's.

## Draft v2/v3 — 2026-10-19 (director's notes applied)

The director's notes after v1: hold on the couple only for a second, let the camera pan down to the two
phones, keep the focus on the phones while the people walk off behind, give the screens a heart each
(distinct, one feminine, one masculine), and add an early flub where a line comes out wrong, the speaker
checks the phone, then gets it right.

Built: a flub take at the top ("O lady of the lettuce..." then a puzzled look down at the phone; the wide
then carries the proper line); a new two-shot with both phones side by side on the balustrade, blue heart
and pink heart; the meeting as "Hi." "Hi." with the camera tilting down to the phones while the couple turn
and walk away; a phones close-up in which the couple walk off through the curtain; a programmatic hold with
the screens pulsing as the phones speak. The first attempt at the tilt was book-ended with a last frame and
ghosted a second pair of phones as the camera started to move, so v2 uses a hard cut in its place and a
first-frame-only retake supplies the real pan in v3. Three cuts (v2 cut, v3 pan, v4 pan plus an aside of the
agent's) share the same body and run about 53 s; the length and the title card are open decisions.


## Draft v5 — 2026-10-20 (second round of the director's notes)

The director's notes after v4: he looks a little different in the wide and grows glasses at five seconds;
her "sweet voice below" line is sung, not spoken; in every one of his shots he looks away from the balcony,
and by the third she is not in his frame at all; the meeting puts him on a fake ground and the couple walk
through a wall; minimise motion. The phones were perfect and the aside stayed.

Root cause of the gaze: his anchors had the balcony behind him, so facing the lens meant facing away from
her. All of his coverage was re-blocked: a low two-level medium from his side with the balcony and her in
the upper corner he faces (the flub and line 3), line 1 from her point of view looking down over the
balustrade, and a profile close-up facing the balcony for the earbud beat. Her line was rewritten as one
plain sentence and retaken in a speaking voice. The meeting became her close-up (she looks up and finds him
beside her), his close-up up on the balcony with the rail in front of him, and a still two-shot along the
balustrade with the phones in the foreground for "Hi." "Hi.", cutting to the phones take for the walk-off.
The wide survives only as a silent opening second.

Veo's own contributions and the edit-arounds: her point-of-view take pushed in slowly on its own and, as it
did, invented a lit balustrade along the top edge; a bottom-anchored programmatic zoom hides it and the push
now lands on his face for "to be your face". The earbud take put the earbud back in his ear, so the usable
head was looped and the look-up was retaken from an anchor with no earbud anywhere. Her close-up turned to
the lens after two and a half seconds; the cut keeps the look up and to the side. One cut, 61 s; the length
and the opening wide are open decisions.

## Handoff — 2026-10-21 (director's decision after v5)

The director's response to the v5 delivery: Veo is having tremendous issues with this video; take a
different approach. The project moves to a machine with local generation, so the human beats that Veo
failed through two rounds (his eyeline in the courtyard, the earbud coming out, the meeting on the
balcony, any camera move) can be built with fine-grained control instead of further paid takes. The
ending (the phones' close-up and hold, the four lines and the aside) stands as approved material.

Everything needed to resume was packaged: the shot book ([shots.md](shots.md)) with every anchor,
prompt, take, decision and clip ID; the edit recipes under `recipes/`; the 24 project clips synced to
the private clip backup with their generation snapshots and analysis runs; and a private workspace
bundle with the reference images, ElevenLabs stems, native take audio, local renders, QA decisions and
the v5 delivery. [handoff.md](handoff.md) lists the locations, the state of the cut, what to keep, what
to regenerate and the open notes. No cut is approved; nothing is upscaled or published.
