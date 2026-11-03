# RETAKE — brief v1

[Current production record](README.md).

a][ productions · 2026-11-03 · Claude Code, from the director's brief: a piece along the
themes of VERIFY (9:16, 25 s maximum, a fixed all-in ceiling). Concept approved
2026-11-03 with three director's notes folded in: reproduce the look of the
identity apps that ask you to turn your head inside a ring, build a smile ladder
(smile, fails; bigger, fails; a frown, passes), and end on a robot's face being
verified instantly.

## 1. Concept

An identity-verification app of the kind that puts your face in a circle of tick
marks and asks you to turn your head. One ordinary person, at arm's length in
their own hallway, does what it says. They turn too fast: "Move your head more
slowly." Slow to the left, slow to the right: the ring fills. "Smile." They
smile. "Try again." They smile bigger, teeth. "Try again." The smile collapses
into a frown, the ring turns green: "Verified." The frown is captured as their
photo. Then a robot's head in the same hallway. "Smile." Verified, instantly.

Nothing is stated. No title card, no music, no voice but the app's. The viewer has
stood in that circle. VERIFY asked whether you were a person and verified you
anyway; RETAKE accepts you the moment you stop performing for it, and accepts the
machine without asking.

## 2. Format

- 1080×1920 (9:16), 24 fps, H.264 high + AAC 48 kHz stereo.
- Runtime about 22.5 s (540 frames); the ceiling is 25 s. Built to loop: the
  robot's Verified cuts to black and the loop lands on "Position your face in
  the frame."
- A fictional reconstruction of a generic liveness pattern: no logos, product
  names or brand glyphs. All interface text and the ring sit in the top two
  thirds of the frame, clear of the Shorts interface.
- Page black for the whole runtime. The only picture is the camera feed inside
  the circle.

## 3. Beat sheet

Frames at 24 fps. Source windows are set from the takes; the beats are the plan.

| # | Beat | Edit (s) | Instruction | Result | Source |
|---|---|---|---|---|---|
| B0 | Face settles into the circle; the ring appears | 0.0–2.0 | Position your face in the frame | ring ready | C1 head |
| B1 | A quick turn and back | 2.0–5.5 | Slowly turn your head to the left | fail: Move your head more slowly | C1 |
| B2 | A slow turn left, a slow turn right; the ring fills | 5.5–9.5 | Slowly turn your head to the left / Now to the right | ring complete | C2 |
| B3 | A polite closed-lip smile | 9.5–12.5 | Smile | fail: Try again | C3 |
| B4 | A bigger smile, teeth | 12.5–15.5 | Smile | fail: Try again | C3 |
| B5 | The smile collapses into a frown; green ring; the feed freezes as the captured photo | 15.5–19.5 | Smile | Verified | C3, then a freeze |
| B6 | The robot in the same hallway; the ring completes in one frame | 19.5–22.0 | Smile | Verified | R (still) |
| B7 | Black | 22.0–22.5 | | | local |

Hard cuts on the app's own events: B1→B2 on the reset after the fail, B2→B3 on the
ring completing, B5→B6 after the capture. Every take starts from the same anchor,
so each cut returns to the same centered, neutral face.

## 4. The chrome

Built locally with Pillow and FFmpeg; the feed is composited through a circular
mask. Canvas coordinates, origin top-left.

- Page #000000 every frame.
- Caption, top: `Identity check` in a plain sans (Helvetica Neue), 34 px, grey
  #8e8e93, centered, y ≈ 150. No step counter, no logo.
- Instruction: 56 px white, centered, baseline band y 260–380, up to two lines.
- Viewfinder: circle centered at (540, 820), radius 370. The feed is a square crop
  around the head, scaled so the face fills most of the circle.
- Ring: 60 rounded ticks (6° apart) between radii 400 and 436, 8 px wide. Idle
  #2c2c2e. During a turn the ticks on the side the head faces fill green
  #30d158 as the head covers them; on a fail they turn dim red for twelve frames
  and drain back to idle. During Smile, a thin white arc sweeps the ring (the
  app analyzing); on a fail it stops. On Verified every tick is green.
- Status line: 44 px, centered, y ≈ 1300: fail text in white, `Verified` in green.
  Nothing below y 1340.
- Capture: on Verified the feed freezes on that frame; a 2-frame 25 % white flash
  and a shutter mark the photo being taken.
- Robot beat: identical chrome; `Smile` for ten frames, then all green and
  `Verified`. The still carries fine moving grain so it reads as a live feed, and
  the robot does not move at all.

## 5. Footage plan

Two Nano Banana Pro images, three Veo 3.1 Quality takes (8 s, 9:16, 1080p, native
audio). All Veo takes use A as the first frame. Exact prompts are in the
workspace and frozen in each request's creation snapshot.

- **A — the anchor.** Front-facing phone camera at arm's length, vertical: an
  ordinary person of about forty, head and shoulders centered, looking into the
  lens, neutral, mouth closed, plain dark crew-neck, a plain hallway with a closed
  door behind them, flat daylight from one side, slightly soft. Gender
  unspecified; the first plain, ordinary result is the person (VERIFY's rule:
  no polishing toward or away from convincing).
- **R — the robot.** Same hallway, framing and light, with A as the environment
  reference: a humanoid robot's head and neck, matte white hard-shell faceplate,
  two round glass lens eyes, a thin seam for a mouth, exposed grey mechanical
  neck with cables and actuators, brushed-metal shoulders; industrial, not cute,
  no markings. It looks into the lens and does not move.
- **C1 — settle and the fast turn.** Looks into the lens, breathes, blinks once;
  then turns the head quickly to the left and back to center; holds.
- **C2 — the slow turns.** Turns the head slowly to the left, holds, returns;
  slowly to the right, holds, returns. Mouth closed throughout.
- **C3 — the smile ladder.** A polite closed-lip smile, held; it widens into a
  big open smile with teeth, held; then the smile fades and the face falls into
  a frown, held. No words. If the take does not carry the frown, a fourth take
  (C4) asks for the fall from neutral into the frown alone.

The anchor is a selfie-framed face, which is the near-portrait case that has
tripped Veo's input filter before; the hallway, door and shoulders keep it
scene-embedded. C1 is the probe. If Veo refuses the face, the fallback is Runway
Gen-4.5 image-to-video (VERIFY's route) with the sound built locally.

## 6. Sound

No music, no speech. Native room tone and breath from the takes where clean.
The app's sounds are synthesized locally and dry: a soft tick as ticks fill, a
low double tap on a fail, a two-note bell on Verified, a shutter at the capture.
The robot beat has the bell and nothing else; the hallway tone drops out with the
person. Master to about −21 LUFS, true peak −1.5 dBTP.

## 7. Assembly

Chrome plates per beat state (Pillow), ring frames driven by a per-beat fill
table keyframed from the takes, feed crops through the circular mask (FFmpeg),
local renders registered as edit sources, hash-bound decisions under `qa/`,
`edit/v1.json`, `film assemble`, `film review --overlay`. Loop test: the master
concatenated to itself, watched across the seam.

## 8. QA

- Dense strips on every turn and on the smile ladder; the frown must be a frown,
  not a neutral.
- The mouth stays closed in C1 and C2; no speech-shaped motion anywhere.
- Eye contact holds in every used frame except mid-turn.
- Tick geometry identical across all plates; any 1 px drift reads as a glitch on
  the hard cuts.
- Status text and ring clear of the Shorts interface zone.

## 9. Decisions and reasoning

- **The head-turn pattern, not the passport oval** (director's note): it makes
  the test choreography, and the ring is a wordless instrument that reads on mute.
- **The smile ladder** (director's note): every line stays plausible app copy; the
  machine never asks for a frown. By the third try the frown is sincere, and that
  is what passes.
- **The robot, two seconds, deadpan** (director's note, my conditions): same
  chrome, same bell, no music; the ring completes before the robot could have
  moved. The speed is the joke. A still, with grain, because stillness is in
  character and robot heads with faces have tripped Veo's third-party filter.
- **Black page, feed only in the circle.** Withdrawal rather than decoration,
  and the viewer's own reflection sits in the margins on a phone.
- **One anchor for every take.** Each cut returns to the same face at rest, so
  the generator's 8-second limit disappears into the app's own resets.
- **The instruction stays `Smile` when the frown passes.** The app does not
  change its mind; it just verifies.

## 10. Open items

1. Whether Veo accepts the selfie anchor (C1 is the probe).
2. Whether C3 carries all three expressions in one take, or C4 is needed for the frown.
3. The exact source windows and the ring keyframes, set from the takes.

## 11. Status

- 2026-11-03: planned, built and cut the same morning. The first anchor rendered a phone
  in a hand showing the camera app; its screen content was cropped and regenerated as the
  direct camera view, which Veo accepted on the first probe. Three Quality takes with
  native audio, all first attempts, all kept: a whip-turn, two slow turns, and the whole
  smile ladder in one take. The takes' own sound is muted (unasked speech in the first,
  a loud burst under the grin in the third) in favour of a synthesized hallway tone and
  local app cues. v1 is 528 frames (22.0 s), assembled and verified; the loop seam was
  checked on a doubled copy. Technical checks only; the director has not yet watched it.
  Decisions and the dated log are on the status page (`status.json`).
- 2026-11-03, later: the director watched v1 and gave three notes: open on the card half a
  second before the first instruction, add a quarter second of black before the robot, and
  the second turn went to his left again (the take had turned the same way twice, and the
  sheet was misread). One retake was bought for the right turn; it too turned left first,
  then swung into a proper right profile, so the usable turn-in is its return to center
  played backward with the hold as a palindrome, no jump cut. v2 is 498 frames (20.75 s),
  assembled and verified; awaiting the director's watch.
- 2026-11-03, afternoon: the director approved v2 and authorized the 4K finish. The master
  (`final/v2-4k/film.mp4`, 2160×3840, 498 frames) redraws the interface natively at 4K, scales
  the camera feed locally (Lanczos; a 100 % comparison showed the neural x2 drawing ink lines
  into the skin, so it was used only on the robot still, where it cleaned edges), and carries
  v2's AAC stream across unchanged. Frame count, dimensions and audio identity verified; the
  director's upload and the publication wrap-up follow.
