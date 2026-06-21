# HEAD FAKE — Production Brief v1

**a][ productions**
Standalone conceptual piece. Short-form (YouTube Shorts / Instagram vertical).

---

## Concept

A literalized pun in the Videodrome register (cf. "handgun"). The compound **head fake** is split into its two live meanings — the basketball *feint* and *a head that is fake* — and the piece collapses one into the other, twice, with opposite payloads.

The spine is a stated rule and a broken rule:

- **Beat 1 (player):** a fake conceals a *real* head. Deception hides a truth.
- **Beat 2 (ref):** a fake conceals *nothing*. Deception hides absence.

Same grammar both times (a face/head is shed, something is revealed), opposite content. The piece sets its own rule on the player, then breaks it on the authority figure. The arbiter of the fake turns out to be the fakest thing on the floor.

Register: Beat 1 is kinetic (the juke). Beat 2 is dread (slow peel to camera).

---

## Setting

Basketball, legible and ordinary. Top of the key. A defender, a court, hardwood, a crowd in the stands, a ball in play. The sport context pre-loads "head fake" so the betrayal reads clean. Real-time, naturalistic lighting — no stylization until the break. The horror works because the world is mundane right up to the seam.

---

## Sequence

### BEAT 1 — THE JUKE (kinetic)

1. **Setup.** Player squares up on the defender at the top of the key, ball in hand. Crowd behind. Ordinary. Establishes the rule: a guy about to make a move.
2. **Feint.** Head snaps hard left to sell the drive. Defender bites.
3. **Betrayal.** The head keeps going — tears loose at the collar and sails off left. No wound, no blood: it is a hollow molded shell, slack like a shed mascot/costume head. Nothing organic.
4. **The real head rises** up out of the collar where it had been tucked the whole time, settling exactly where a head should be — calm, *already looking the other way*, toward the lane the player actually drives. The discarded head was the bait; the real one was always crouched and watching. **The unbothered calm of step 4 is what makes it land — do not play it as shock.**
5. **Button.** The shell hits the floor and peels — another identical fake underneath. Punch plus rot.

### TRANSITION

Fade to black.

### BEAT 2 — THE FOUL & THE DREAD (dread)

6. **The whistle.** Up from black: the referee blows the play dead. He points at the fallen shell and throws the "illegal" / foul signal — **he is penalizing the deception itself.** Make this beat clearly legible: the foul is *on the head fake*. This sets up the irony.
7. **The peel.** The ref's face peels forward off the front of the skull, toward camera (mirroring the dread register — the player's shell went sideways, the ref's decoy comes at us). Thin, latex-like, a decoy mask coming away.
8. **The reveal — nothing.** Behind the face is not a skull and not another face. It is **the court.** We see straight through the ref-shaped gap to the hardwood and the crowd behind him. He is a ref-shaped hole in the world. No flesh, no gore — see-through compositing.
9. **The payload — function without a source.** The ref *keeps reffing.* Arm still locked in the foul signal. Whistle still shrieking from the empty collar. Crowd visible straight through the gap. The authority functions anyway. The arbiter who adjudicates what is real on this court does not need a head — was never behind the face at all. **This persistence is the entire point of the piece.** Hold on it.

---

## Production approach

Precise state-changes (head detaching, face peeling, see-through gap) are exactly what Veo fumbles if asked to improvise. Anchor hard with **Nano Banana Pro** first/last frames, then run short Veo motion passes between locked anchors. Character/uniform continuity across all anchors via a locked player reference and a locked ref reference.

### Nano Banana Pro anchors

**Beat 1:**
- **A1 (first frame):** Player squared up, head centered and normal, ball in hand, defender opposite, court + crowd.
- **A2:** Peak of feint — head whipped fully left, clean hollow seam just opening at the collar.
- **A3:** Shell airborne left, hollow interior clearly visible, real head cresting up out of the collar into the gap.
- **A4 (last frame):** Real head fully seated, looking right toward the lane; shell falling away.
- **A5 (button):** Shell on the floor, partway peeled, identical fake visible underneath.

**Beat 2:**
- **B1 (first frame):** Ref mid-court, whistle at mouth, arm up in foul signal, pointing at the fallen shell.
- **B2:** Face peeling forward off the skull toward camera, decoy mask coming away, gap beginning to open.
- **B3 (last frame):** Face fully shed; ref-shaped gap shows hardwood + crowd straight through; arm still locked in foul signal; collar empty.

### Veo motion passes

- **P1:** A1 → A2 (the feint, head snap, defender bites)
- **P2:** A2 → A3 → A4 (the tear and the rise; real head settles looking the other way)
- **P3:** A4 → A5 (button: shell lands and peels)
- Fade to black (post)
- **P4:** B1 (hold) — whistle, point, foul signal
- **P5:** B2 → B3 (the peel and the reveal)
- Hold on B3 — whistle continuing from the empty collar

Collapse any pass to a still + ffmpeg motion where it saves credits without losing the state-change (e.g. the hold beats P4 / final B3 hold are candidates for still + audio over ffmpeg rather than full generation).

---

## Moderation discipline

"Head tears off" + "neck" will trip Veo as decapitation. The reframe is also the *truer* description — write every prompt around a **hollow plastic/latex shell separating like a costume or mascot head**, explicitly **no blood, no flesh, no wound, no gore.** The ref reveal is a **see-through gap / hole**, nothing organic to flag. If a pass refuses, remove the triggering element and re-approach from a different angle rather than pushing the same prompt.

---

## Audio

Veo's generated audio is not usable here — plan all of it as ElevenLabs / Suno / library SFX in post from the start.

- **Setup:** crowd bed + sneaker squeak under the squaring-up.
- **Detach (Beat 1):** a dry hollow *pock* — empty gourd, not wet. Sells "it was always fake."
- **Button:** soft peel/tear of the shell on hardwood.
- **Transition:** crowd ducks under the fade to black.
- **Whistle:** sharp ref whistle on the foul call.
- **Reveal (Beat 2):** **the whistle keeps shrieking from the empty collar — do not drop to silence.** Function persisting through absence is the idea. Crowd bed continues, indifferent, behind the gap.

---

## Output & assembly

- Vertical short-form aspect (9:16). Confirm target length on assembly — this wants to be tight; the whole thing lives or dies on pacing.
- Assemble passes + fade + audio in ffmpeg.
- Commit script/brief and pipeline files to GitHub under the appropriate standalone-pieces directory.

## Credits

Transparent AI-tool attribution per standing practice. Distinguish creative direction / human oversight / production. Tools: Google Veo (Flow), Nano Banana Pro, ElevenLabs, Suno, Claude Code + ffmpeg.
