# PERSONAL BEST — production brief

**Status:** v1 BUILT 2026-08-19, fully autonomous session — 51.75s silent picture cut awaiting
Stephen's review (720p signed URL in session log). All 6 joins gated: J1–J4 MARGINAL, J5–J6
PASS. Spend $24.80/$25.00 pre-logged (≈$23.20 expected after BQ reconcile of one RAI-filtered
attempt). Build log, boundary-verdict table, and the full decision queue:
`data/workspace/personal-best/build-plan.md`. Notable deviations queued for review: bench lost
off-screen at J3; seg5 ships take 1 (kneel at payoff, 3-fail rule); seg6 direction inversion
re-read as laps; seg7 ending is Veo's override (wall touch → climbs out → swims into the town).
**Authorized:** Stephen, 2026-08-18 — "30-60s, 9:16, $25 max budget… try for something
funnier rather than somber. And something that looks like a single take to really test
the joins."
**Runtime:** 52s finished — 7 segments, 6 joins.
**Budget:** `personal-best` pot, $25.00 cap, ledger `data/veo-budget-personal-best.tsv`.
**Technique:** `.claude/skills/extend-clip/SKILL.md` (doctrine revised 2026-08-18).

---

## Logline

A soft-bodied man in his fifties swims flawless freestyle on a wooden bench in a drained
municipal pool, and one unbroken retreating crane reveals — in stages — that the town is
underwater, that the flood arrives exactly when he pushes off a turn, and that the dry
sidewalk was eighteen inches from his shoulder the whole time.

## Why this concept and not another

Five concepts were written against distinct comic lenses and scored by three judges
(comedy, camera craft, Veo feasibility). Two of three picked this one; the third scored it
highest on the axis that decides whether a film exists at all.

**The joke is carried by a camera move, and camera moves are the most reliable thing Veo
generates.** The rejected concepts staked their engines on a half-inch weight shift, a
cruise ship reversing on cue, and a brim-full wine glass surviving six generations. Each
renders a film with the joke missing. This one renders the joke even when individual beats
fail, because the reveal is structural — a ladder that still climbs when a rung goes.

**And it is the only concept where the subject is the busiest object in frame at every
single boundary.** Freestyle stroke is high-frequency, high-amplitude, self-occluding limb
motion. The measured restage relocates and rescales *the subject*, not the background — so
background weather and crowds do not hide it and a cycling arm does. Every other concept
masked with environment while its anchor stood, sank, pivoted, or balanced.

The comedy judge's warning was "charming, not funny" — the original engine was a *state*
(he never revises), which produces recognition, not laughter. Four grafts fix it, each a
large legible physical action rather than a micro-performance:

1. **The turn.** Two-hand competition touch on the end grain, then a graceless 180° pivot
   on his belly — a man wriggling around on a plank — then immaculate freestyle the other
   way, unacknowledged. Elite technique either side of a humiliating land-animal shuffle.
   It is a *beat*, so the audience learns it the first time and anticipates it the second.
2. **Misattributed agency.** The second turn lands in segment 4, and on his push-off the
   water sheets over the far lip. He appears to have summoned the flood. Costs nothing —
   the flood was coming anyway — and converts an escalation into a joke with a turn.
3. **Authority applied where it cannot apply.** In the button he performs a regulation
   finish on a lamppost: two-hand touch, a glance at a pace clock that does not exist,
   flip turn, lap two.
4. **Non-correction, as a directing rule.** The joke is not that he's embarrassed — it's
   that he isn't. He never once looks at the town, the flood, the canoe, or the woman.

Register is dry and bright, not wistful. The score never agrees with him, the world never
applauds, and the last thing that happens is a small dog walking past faster than he can
swim.

---

## The subject (the only anchor the technique carries)

Mid-fifties. **Soft-bodied — round belly, pale untanned skin, sloped unathletic shoulders,
thin arms** — moving with the immaculate high-elbow catch and clean two-beat kick of
someone who was genuinely good thirty years ago. The comedy lives in that contradiction.
Re-specify the body in **identical words in every prompt**, never paraphrased.

**Wardrobe, unchanged throughout:** bright red silicone swim cap, mirrored silver goggles,
navy swim jammers to mid-thigh, bare feet. Nothing else, ever — no towel, no watch, no
stopwatch.

The wardrobe is engineering, not costume:

- Cap plus mirrored goggles **deletes hair and eyes from the identity budget** — the two
  variables that drift hardest across seven generations — and replaces them with two
  saturated high-contrast shapes that stay legible at fifty feet. They carry no *counted*
  features (no bolts, no portholes), so there is nothing to drift in number.
- The red cap is written into every prompt as **"the highest-saturation object in frame."**
  This is what keeps him findable in segments 4, 6 and 7, and what stops a background
  kayak or helicopter from being promoted to subject.
- **Jammers rather than briefs, deliberately.** This repo's ledger records two output-RAI
  trips in five generations (code 29310472), and a bare-torso male figure is exactly the
  subject class that trips people-focused output filters.

**Spec-budget rule:** spend the entire torso-specification budget on segments 1–2, where
the body fills frame and the joke depends on it. From segment 3 he is a small red dot;
concede body drift there and spend the tokens on environment.

**The second body** is deliberately *not* an anchor: a figure in a **yellow raincoat** with
a small dog, seen only from behind or strict profile, never a face. Segments 6–7 only,
planted at the extreme frame edge in the last second of 6 so segment 7 *inherits* her
rather than inventing her. One identifying feature and no others.

**Environmental through-line:** a painted black lane line runs down the basin floor under
the bench (1–4), stays visible as a dark stripe under the flood (5), and rhymes with the
painted centre line of the flooded street (6–7). It is a *shape, not a word*, so it cannot
render as garbled text.

---

## The camera — one rule, and it is load-bearing

**ONE unbroken move: backward and upward, monotonic, for all 52 seconds.** It never
descends, never reverses, never re-frames, never stops. Only the *rate* varies — slow and
intimate through 1–2, accelerating through the reveal, easing on the final wide.

This matters because **every segment carries the identical camera clause** — *"the camera
continues its slow backward crane, still rising"* — so the model is never asked to invent
a move, only to continue one, and no boundary negotiates a direction change on top of a
content change. The first draft of this concept declared "never reverses" and then blocked
an up-down-up; that contradiction was caught in review and is fixed here. **Do not
reintroduce a descent.**

The subject is pinned to the **lower third at roughly constant size**, with the upper two
thirds kept deliberately empty as the slot each reveal drops into. Because he holds the
bottom third, every reveal is staged by *widening* rather than repositioning.

- The town reveal happens **across, not from above** — the camera clears the fence at ~15
  feet and the flooded street is visible past it at that height.
- The adjacency punchline is bought by **continued rise**, not descent: from ~25 feet the
  dry raised sidewalk eighteen inches from his shoulder and the flooded street sit side by
  side in one legible graphic.

He becomes a dot through the first act — *that shrinking is the reveal* — and then he
closes the distance himself from segment 6, swimming toward the retreating camera.

---

## Segments

Every boundary lands mid-stroke. **No segment ends on a held beat.**

| # | sec | beat | what is moving at the boundary |
|---|-----|------|-------------------------------|
| 1 | 8 | **Master anchor.** Extreme close: blue caustics on a face in red cap and mirrored goggles, head rolling to breathe, arm scything, bubbles. Unambiguously elite pool swimming. Camera begins its retreat; over the last two seconds the caustics resolve into afternoon sun through dry leaves and his hand slaps **varnished wood**. There is no water. | Right arm at full recovery, elbow high, hand descending; feet fluttering; leaves crossing on the wind. Flat pale concrete behind — **no rigid line anywhere in frame**, the most forgiving substrate in the film. |
| 2 | 8 | Retreat completes the body reveal: a soft-bodied man face-down on a narrow bench doing textbook freestyle in open air, feet off the end, absorbed. Immaculate and ridiculous. Then **the first turn** installs the grammar. Around him: cracked pale-blue basin, drifts of dead leaves, a coiled lane rope. | Mid-stroke in the *new* direction, left arm entering, feet fluttering hard enough to lift dust. Boundary placed one beat **before** the wall's straight top edge dominates frame. |
| 3 | 8 | Camera crests the deck: empty lifeguard chair, closed umbrella, sun-bleached kickboards — bone dry, unpeopled. He breathes left and sees nothing. Then past the chain-link, the first wrongness: **the prow of a rowboat glides across at deck level**, oars dipping, and exits. | Rowboat exiting top of frame, oars still in water; chain-link already passing *out* of the bottom of frame rather than crossing it. |
| 4 | 8 | **The reveal.** The whole town under three feet of water: kayaks, a floating trash can, a dog on a car roof, someone poling a canoe past a submerged bus shelter. He is a red dot in his dry concrete hole, the only dry thing for a mile. Then **the second turn** — and on his push-off, water sheets over the far lip and starts pouring in. He does not notice. | A curtain of water pouring down the far basin wall with spray coming off it; kayaks and canoe moving in the upper socket; arms cycling. Peak information and peak motion in one frame. |
| 5 | 8 | The basin fills — churning brown surge, leaves and the lane rope rotating slowly around him, the black line wavering under a foot of moving water. The bench floats, tips, goes out from under him, and **for the first time his stroke catches actual water. He surges.** The film pays off its own setup: he was right, the facility was late. | Full whitewater — arm entering, a real bow wave off his shoulders, bench tumbling away, foam rotating. Busiest frame in the film, and the only one where nothing rigid, counted, or held is present anywhere. |
| 6 | 6 | He powers out of the drowned basin, over the submerged fence, into the street, and overtakes the canoe. Magnificent, and heading the wrong way — away from every boat making for high ground. He closes distance to hold his size in the socket. In the **last second**, at the extreme frame edge, a raised dry sidewalk enters with the yellow raincoat and the dog, from behind. | Full sprint with bow wave and spray; raincoat walking, dog trotting at frame edge; canoe receding; featureless brown water behind. |
| 7 | 6 | **The punchline.** The rise widens and the adjacency lands: the sidewalk is dry, raised, completely fine, eighteen inches from his shoulder. The raincoat keeps exact pace with his all-out sprint at a stroll — then pulls ahead. He reaches a lamppost, plants a two-hand competition touch, glances at a pace clock that is not there, flip-turns, and starts lap two. | Final frame — the only place the image may ease. Camera decelerates on the wide while the red cap tracks steadily up the middle of the brown ribbon. Nothing is generated downstream of it. |

**Total 8+8+8+8+8+6+6 = 52s.**

## What is knowingly given up

The money shot for this film is the lone red cap suspended in a vast empty concrete bowl,
**held**. It is forbidden in writing, because a near-static frame is where the technique
breaks. That is a real loss traded for invisible joins.

---

## Production rules

**Tier and resolution: `veo-3.1-prod` (quality), silent, 1080p, 9:16, $0.20/requested
second.** Quality is non-negotiable — measured, quality does *not* restart from rest
(VR 0.63–0.76, flat head series) while fast stalls (VR 0.33–0.45), and this entire film is
built on velocity surviving every boundary. 1080p because the quality tier is priced the
same at any resolution — it costs nothing over 720p and demonstrably trips the RAI filter
less. Fast tier is used for nothing, not even framing tests: the two things worth testing
here are joins, and fast cannot answer a join question.

**Silent generation, sound designed in post.** No dialogue anywhere. Audio continuity
across a generation boundary is unsolved in this repo, and generating silent both dodges
it and halves the rate. Post: water, breath, the slap of a hand on wood, a dry
municipal-swimming-pool reverb that never changes even after the flood, and a score that
never agrees with him.

**The chain, per `extend-clip`:**

1. `tools/last-frame.sh <A>.mp4 anchor.png` — from the RAW mp4, never after normalize-clip.
2. Generate B conditioned on that anchor as first frame. Every parameter explicit
   (`model`, `durationSeconds`, `generateAudio`, `resolution`, `aspectRatio`) — a bare call
   defaults to quality/8s and bills $1.60–$3.20.
3. Prompt describes **motion only**; never re-describe the frame.
4. **End A at anchor−1.** B[0] regenerates A's final moment; keeping both duplicates a frame.
5. Join with the **concat filter**, never the demuxer (`-c copy` corrupts r_frame_rate).
6. Gate with `tools/seam-check.py` in default perceptual mode. **MARGINAL is a shipping
   verdict, not a defect.** Then *watch it* — the central lesson of 2026-08-18 is that a
   rendered join must be looked at, not only scored.

**Every submission, through every door:**
```
python3 tools/veo-budget.py preflight --project personal-best \
    --model quality --seconds 8 --resolution 1080p --audio no --note "seg N ..."
```
Abort on non-zero. Never charge the `seamless-joins` pot — that is a different
authorization with $7.36 left and it is not fungible with this one.

---

## Spend plan, staged so the money can be stopped

**Stage 1 — anchor.** Segment 1 generated **three times** as competing candidates:
3 × 8s = **$4.80**. Segment 1 is simultaneously the master anchor and the clip fighting the
hardest prior in the film. **Hard rule: once extension begins, segment 1 is never
rerolled** — a late anchor reroll regenerates the entire film. If all three hallucinate
water, re-plan the prompt; do not buy a fourth.

**Stage 2 — the gate.** Generate segments 2 and 3 (16s = **$3.20**), then run seam-check on
B1/B2/B3 **and watch them**. This costs nothing extra because the two riskiest boundaries
(the basin rim, the chain-link) are simply the next two joins in the natural chain. Total
through the gate: **$8.00, 32% of budget** — and if rigid architecture defeats the masking,
the fence comes out of the design before the remaining $17 is committed.

**Stage 3 — remainder.** Segments 4, 5 (8s each) + 6, 7 (6s each) = 28s = **$5.60**.

**Clean pass: $13.60.** Reroll headroom **$11.40** (~seven more 8s clips): 2 for segment 3,
1–2 for segment 5, 1–2 reserved for RAI seed churn, 1 for segment 7 pacing, 1 floating.
**Zero reserved for segment 1 after Stage 1, by rule.**

**Expected total $18–21. Worst credible $24. Hard cap $25.**

**The discipline that keeps it solvent: three failures on the same design is a RE-PLAN, not
a fourth reroll.** A fourth attempt at an unchanged prompt is how the budget dies.

---

## Known risks

- **The swimming prior hallucinating water.** The whole first act is a negative image and
  Veo will fight it for three clips including the master anchor. Negation is the wrong
  instrument — this repo's own note is that Veo half-summons what you forbid. Use
  **substitution**: never write "no water", "swimmer", "swimming" or "pool" in act one;
  write the positive inventory the model must render in water's place — dry cracked
  pale-blue concrete, drifts of dead leaves, dust, varnished pine, a coiled lane rope, hard
  afternoon sun. Expect to burn rerolls here regardless. This is the hardest prompt in the film.
- **Output-RAI filtering on a bare-torso subject.** Measured in this repo: two of five
  generations filtered, and the filter is **(seed, resolution)-correlated, not
  prompt-correlated** — seed 1137 filtered at 720p on both models while passing at 1080p.
  On a filter hit, **burn a different seed, never rephrase**. A filtered generation may
  still bill; carry it as spend.
- **Body-type drift across seven generations.** The belly will slim toward an athlete and
  take the joke with it. Nothing protects the torso — re-specify verbatim every time.
- **Water level has no memory.** Segments 5–7 depend on a specific depth and Veo re-decides
  it per clip. State the depth in identical words every time. This is a continuity risk,
  not a seam risk, and the likeliest reason a shot gets rebuilt rather than rerolled.
- **The belly-pivot turn** is a compound body action and may mush, or render as a mid-air
  flip turn. **Fallback, specced before the first attempt so the reroll is a substitution
  rather than a redesign:** two-hand touch, a big shoulder-hauling shuffle, and he simply
  starts pulling the other way while staying face-down — no rotation requested at all.
- **The rowboat above the fence line** is a deliberately wrong-scale composition and Veo
  will normalise it to a boat in an ordinary pond, losing the gag. This is the shot most
  likely to come back technically fine and comedically dead. Ask for **motion, not
  tableau**: one clear thing enters frame, one clear thing leaves.
- **Relative-speed choreography in segment 7.** The woman must match a sprinting swimmer at
  a walk, then beat him, and the pacing *is* the punchline. Fallback: shoot her walking
  steadily and buy the overtake in post with a small speed ramp on the tail — free, because
  no join follows it.
- **Text and signage.** Pools and streets cue lane numbers, depth markings and street signs,
  all of which render as garbage. Suppress actively in every prompt.
- **Background spectacle stealing the subject.** Keep kayaks, canoe, helicopter and dog
  explicitly "far background, small, out of focus."
- **Chain-depth drift.** Six chained generations off one anchor is untested here — the
  deepest measured chain is two. Expect not a visible seam but slow monotonic drift in cap
  saturation, body type and framing. **Check segment 7 against segment 1 side by side
  before calling the film finished.**

## The other payload

This shoot is also the deepest test the extension technique has had, and the honest
scientific question is whether restage effects **accumulate** across six generations.
Record a seam-check verdict for every boundary, and record Stephen's perceptual verdict
too — `seam-check.py`'s perceptual ceiling currently rests on **two** human labels and its
header explicitly asks for more. This film can produce six, at known substrates with known
content deltas. Append each one to that header so the number keeps its provenance.

Boundary difficulty, ranked honestly: **B2** (basin rim) and **B3** (chain-link) are the
real technique tests — rigid straight architecture is the worst photometric substrate and
both are deliberately placed there. **B4** looks scary and is not; whitewater is the best
masking that exists, and its real risk is a *logic* break (Veo has no memory of water
depth), fixed by restating depth verbatim rather than rerolling. **B5** is a continuity
test wearing a join's clothes — but the bench is discarded *inside* segment 5, so segment 6
inherits "man swimming in churning water," a state with no prop in it. **B1** is low
photometric risk and carries the heaviest non-geometric burden: the first handoff of the
wardrobe and body spec. **B6** is the easiest join in the film, which is exactly why the
only new character is loaded onto it.
