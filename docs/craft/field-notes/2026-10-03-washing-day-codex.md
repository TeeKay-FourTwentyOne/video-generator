# Washing Day: independent Codex production notes

Attribution: Codex, 2026-10-03. Native portrait draft, existing providers, $20
authorization including QA. These observations concern this build only. No other
agent's Washing Day footage or project assets were inspected.

## A clean image can still encode the wrong physical constraint

The initial floating-sheet anchor looked attractive but attached corners to the
shaft. Describing blue sky around every edge produced a usable free cloth anchor.
Counting rope strands remained less reliable than counting laundry levels: extra
pulley return strands survived several plate attempts. The delivered opening has
four laundry levels, with a disclosed exact-strand-count caveat. A crop can exclude
a contradictory balcony but does not prove the unseen architecture is correct.

## Bookends do not establish the cause of a release

A pinned first frame and an empty last peg prompted an extra peg and an assisting
hand. A first-frame-only retake with explicit exclusions still invented a hand.
Both full releases were rejected. The final insert holds the clean pinned state,
then cuts to a clean empty-peg tail with a local clack and a dip in the sound bed.
That is an editorial ellipsis, not a claim that continuous mechanics succeeded.

The woman's two release takes also lifted the cloth by hand and returned it to the
line. One was technically clean enough to pass generic QA. Intent review rejected
the complete action. The final cut keeps her look and unpinning gesture, then moves
to three already airborne sheets; sequential releases remain implied. Preserve
the rejected ranges and document the exact accepted range instead of relabeling
the whole take as good.

## Local direction repair and a measured continuation

The silent cloth-only S04 moved toward the lens. Reversing it locally created an
upward entrance and recession without reversing a human action, speech or sound.
The original remains intact. Review time reversal for causal contradictions before
using it; this observation is specific to a freely billowing cloth and a static set.

The new `film join-anchor` command extracts a decoded frame, binds it to the
source hash, and records the preceding edit's exclusive end. S04 frame 156 became
the S05 first-frame anchor; the cut uses S04 frame 155 followed by S05 frame zero.
The actual pair measured a photometric ratio of 2.189 and velocity ratio of 1.149:
the seam gate classified it MARGINAL, with no motion-stall failure. Dense inspection
supported keeping the close match cut; do not describe it as mathematically seamless.

## Returning to a scene is a different QA question

Comparing S02 and S06 as adjacent frames treated the woman's changed gaze and arm
position as unexplained drift despite three intervening shots. The added
`anchor-drift --mode=return-shot` requires a stated `--elapsed-action` and keeps
persistent identity, wardrobe and set checks. It must not silently weaken adjacent
cut or interpolation checks. Offline tests guard those mode boundaries.

## Friction and remaining limits

- The exact-frame join helper and its offline extraction, bounds, overwrite and
  path-containment tests passed with the production build/regressions.
- Reference-image reconciliation and sequential spacing worked for this run.
  Generation polling recovered the submitted operations without duplicate calls.
- `clone-check --expected=0` can reinterpret a cloth as the subject even when the
  intended count means no people. Its no-doubling result is not a reliable laundry
  census. Combine contextual clip QA with manual frame counts.
- Default Python lacked Pillow and NumPy. The already installed media virtual
  environment handled QA, score and title work; selecting its `bin` directory on
  the review command's PATH also lets the overlay helper resolve Pillow. No package
  installation was needed.
- Browser review found that the generic Python HTTP server advertised no usable
  seek range: the first few seconds buffered, but shot navigation returned to zero.
  Added a loopback-only review server with single-byte-range responses, HEAD support
  and a filename allowlist. Its integration test covers ranges, invalid ranges,
  methods and path/symlink exclusions. The production suite now passes 24 tests.
- Native audio from the first two shots was mixed under an original deterministic
  score and local foley. Loudness, peaks and waveform inspection are computational
  checks. Real-time listening and artistic approval remain user review steps.
