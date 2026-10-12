# PASSENGER — Production Lessons

[Project overview](README.md).

**Built:** 2026-05-22. 6 beats, ~37.6s, 9:16. Wordless tone poem.
**Final:** `data/workspace-archive/passenger/final/passenger_v1_4k.mp4`
**Brief:** `briefs/passenger/brief.md`

## What worked

- **A single locked vantage carries a quiet piece.** Once every shot was unambiguously
  the child's view from the back seat (after a v1 → v2 re-render), the piece read
  effortlessly as a continuous ride. The same back-seat vantage also made the
  rear-view-mirror glance its natural gesture — exactly how a driver checks on a kid
  in the back. Form serving content.
- **Soft crossfades for a drowsy piece.** All beats joined with 0.5s xfades + a fade
  to black at the end. Hard cuts would have wrecked the mood. Tension-aware
  assembly says low/sustained tension → crossfades; this confirms it.
- **All Fast + one Standard on the emotional beat.** Gentle low-motion shots are
  Fast's strength; the single Standard went to the mirror glance (the one beat
  where eye-detail had to read warm). Right allocation.
- **Lean into nano's gifts.** nano added a small teddy bear in the foreground of
  the mirror beat — unprompted, perfect for the child's-back-seat world. Rather than
  fight it, I locked it in by regenerating the B5 last-frame to keep the teddy in the
  same spot, so Veo didn't morph it away. Serendipitous detail → make it canon.

## What to watch

- **The POV-vs-portrait decision is structural; surface it BEFORE generating.**
  v1 had a real continuity error: the camera waffled between *being* the child
  (POV: window, windshield, mirror) and *watching* the child (portrait: a sleeping
  child in the seat). The user caught it immediately. Direct application of
  [[feedback_surface_structural_decisions]]: "are we the child or watching the
  child" is the kind of fork that must be an explicit check-in, not a tacit
  decision spread across shot prompts.
- **"Child" + "asleep" trips Veo RAI.** B4's first prompt mentioned "the small
  blanketed child asleep in the seat" — submitted, came back with the RAI 58061214
  error. Same family as [[feedback_veo_child_prompt_words]]. Fix that worked:
  rewrite the prompt as **pure motion** — "soft golden light slides across the
  warm cabin and the soft blanket; the image drifts gently and softly." The frame
  carries the child; the prompt describes only the camera/light motion.
- **Even POV pieces benefit from the rear-view-mirror gesture.** Worth banking:
  for any back-seat-of-a-car piece, the rear-view mirror is the *one* place a
  driver's face naturally appears without breaking POV. Use it for the emotional
  beat — the mirror's reflection of the driver's eyes finding the camera is one
  of the most loaded micro-shots available in this format.

## Production footprint

The notes retain about twelve nano frames per version and revisions to the back-seat view. Their Veo-attempt count is internally inconsistent, so no exact total is asserted here. One score and five sound effects are recorded; the original accounting text is preserved locally.
