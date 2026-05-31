# June — "The Contested Month"
### Monthly etymology series · a][ productions
### Spine + production brief · v1

---

## 1. Premise

June is the one month whose name the Romans themselves never agreed on — and the disagreement *is* the subject. Three powers each claimed it; no authority could settle the matter; Ovid, asked to choose, refused on the grounds that the last man to judge between three claimants (Paris) got his city burned to the ground.

This piece dramatizes the dispute as a **turf war between three factions**, each marching from a different version of Rome toward a central prize: the unwritten name of the month. They converge, the standoff reaches the edge of violence, and one figure breaks ranks to seize the chisel — but we cut to black before the first letter lands. **The month is never named.** That refusal is the whole point and the whole ending.

Faction names below are for our clarity only. **They are never stated on screen.** The factions are legible entirely through banner symbol, color, register, and which Rome they come from.

---

## 2. Etymological grounding

Three serious ancient derivations of *Iunius*, mapped to the three factions:

| Faction (internal) | Derivation | Source | Claim basis |
|---|---|---|---|
| **Sovereigns** | *Iuno* — month of the queen of the gods | Common ancient derivation; Ovid *Fasti* 6 (Juno's speech) | By right / dynasty |
| **Younger** | *iuniores* — the young men, paired against the *maiores* (May) | Macrobius, crediting Fulvius Nobilior; Ovid *Fasti* 6 (Juventas's speech) | By force / arms |
| **Joined** | *iungere* — the joining of Roman and Sabine peoples into one state | Ovid *Fasti* 6 (Concordia's speech) | By union |

The framing device is **Ovid's refusal** (*Fasti* Book 6 opens with all three goddesses descending and demanding the month; he declines to crown a winner, citing Paris). Our narrator inherits that posture: he stages the seizure and withholds the verdict.

> ⚠ **Latin verification gate.** Do not place any carved or spoken Latin on screen (e.g. an *IVNIVS* inscription, a *Fasti* line) until the exact passage is pulled from the Latin source text and confirmed. No reconstructed-from-memory Latin. This blocks the prize-stone lettering and any VO that quotes Ovid directly.

---

## 3. The three factions (reference-sheet specs)

Each gets a **locked reference sheet** (Nano Banana Pro) before any Veo work: one representative figure + banner design + palette. Continuity is carried by **graphic identity, not figurative likeness** — color, symbol, costume silhouette.

### Sovereigns — Juno — *ancient Rome*
- **Symbol:** peacock standard (Juno's bird).
- **Palette:** imperial gold + Tyrian purple.
- **Register:** stately, slow, processional. The establishment that assumes it already won. Condescending calm.
- **World:** pristine intact imperial Rome — clean marble, columns whole, statuary unweathered.

### Joined — Concordia — *layered Rome*
- **Symbol:** *dextrarum iunctio* — two clasped right hands (Concordia's actual coin iconography; historically anchored, not invented).
- **Palette:** verdigris / aged-bronze green — the patina of old statuary. Reads as "layered time," and stays distinct from the bleached neutral arena.
- **Register:** diplomatic, reasonable, "can't we all share." The joke: the peace faction is also a combatant, in the street fighting for the month like everyone else.
- **World:** stratified Rome — the palimpsest city where eras are mortared together. A column holding up a later church; a temple swallowed by an apartment block; spolia walls; ruins with traffic running past. All times at once. This is union made architectural.

### Younger — Juventas / the *iuniores* — *modern Rome*
- **Symbol:** the raised arm (the *iuniores* "served by arms"). Read as defiance/salute, **not** a closed-fist political gesture — keep it open-handed and ambiguous to avoid both moderation flags and unintended real-world coding.
- **Palette:** red + black agitprop.
- **Register:** kinetic, loud, young. The rebel faction. Defined explicitly *against* the elders who already seized May.
- **World:** living contemporary Rome — scooters, concrete, graffiti, night.

---

## 4. The neutral center & the prize

**The arena is drained of color; the faction members are not.** The convergence space is bleached — fog / white-out, no era markers, no century. But each faction's people and banners **retain their full saturation** as they enter. The result: vivid color-coded figures isolated against a colorless ground, so the only color in frame is the conflict itself. This focuses all attention on the factions and the prize, and makes the final red/black break the dominant element on screen.

**The prize is the unwritten name.** A blank altar / plinth in the center, with a chisel resting on it (or a stylus over wax). Whoever takes the tool gets to carve the month. **Option to push it:** the stone already carries the first few strokes of a letter — so the open question isn't "will it be named" but "who finishes it," which never resolves.

Deliberately abstract: **no throne, no crown.** A throne implies someone *should* sit on it and pre-loads a winner. The empty slot does the opposite — it stays empty.

---

## 5. Beat sheet (target ~50–60s, Shorts / Reels vertical)

Keaton logic: subtraction establishes the rule (one faction, calm), escalation follows (add, add, overrun).

| # | Beat | Sec | Content |
|---|---|---|---|
| 1 | **Cold open — the empty prize** | 0–8 | The bleached center. Blank stone, chisel resting, name unwritten. Establish the prize *empty* before anyone arrives. VO states the refusal frame. |
| 2 | **Sovereigns claim** | 8–18 | Ancient Rome. Gold-and-purple, peacock standard, slow processional march. VO: the claim by right. |
| 3 | **Joined claim** | 18–28 | Layered Rome. Verdigris, clasped-hands banner, diplomatic procession. VO: the claim by union. |
| 4 | **Younger claim** | 28–38 | Modern Rome. Red-and-black, raised arm, kinetic surge. VO: the claim by force. (Highest energy — sets up the break.) |
| 5 | **Convergence** | 38–50 | All three cross into the drained center. Color-coded members vivid against fog. Banners crowd in, poles cross overhead. Tension peaks. **No VO — music carries.** Edge of violence; no blows. |
| 6 | **The break** | 50–57 | One Younger figure breaks ranks and reaches for the chisel. This *is* the violence, sublimated — a unilateral grab that ends the standoff by audacity, not force. |
| 7 | **Cut to black** | 57 | On the reach, before contact. The name is never carved. Optional final card: the month, or nothing — black and a held sound. |

**Narration:** sparse. One claim-line per faction as it appears (states the etymology, lands the educational hook fast); silent through convergence and break. ElevenLabs voice — single narrator, arbiter register, detached. Decision left open: whether VO survives at all into the final mix or the piece goes fully wordless after beat 4.

---

## 6. Production notes (Veo / pipeline)

**Pipeline order:** Nano Banana Pro reference sheets → shot-specific first/last-frame anchors → Veo motion prompts → ElevenLabs VO + Suno score → Claude Code / ffmpeg assembly.

- **Convergence is the hard shot.** Three crowds merging is exactly what Veo fumbles. Build the center as a **controlled low-detail fog environment** and **composite banners/figures in** rather than asking Veo to choreograph a three-way crowd merge in one generation. Do not hand Veo the whole convergence as one prompt.
- **The chisel grab is a hand/physics state-change.** Veo is weak on precise hands and physics. **Anchor it with Nano Banana Pro first/last frames** (hand-away → hand-on-chisel) and let Veo interpolate the reach. Cut on the reach, so we never need contact physics.
- **Audio notes in every Veo prompt.** Veo's generated dialogue audio is unusable — plan ElevenLabs from the start for any VO. Ambient/footfall/crowd-murmur from Veo is fine as a scratch layer.
- **No "static camera angle unchanged from before"** unless a fixed lock is explicitly wanted. For static-scene transitions use reverse clips for seamless joins.
- **Literalism / trigger words.** Veo is extremely literal. Describe banners, marches, and the reach in **clean physical terms** — "a crowd in red and black walks forward holding tall banners," not poetic abstraction. Watch for misfires.
- **Moderation.** "Faction," "fist," "edge of violence," "seize," "lunge" risk refusals. Frame prompts as **ceremony, procession, march, reach** — not aggression. If refused, **reframe rather than push**: strip the triggering element, approach from another angle.
- **Credit budget.** Where a beat is mostly a held image (the empty prize; a banner standing), collapse to a still + ffmpeg motion rather than a full Veo generation.

---

## 7. Open questions carried forward

1. **VO survival** — does narration continue past beat 4, or does the piece go wordless into convergence + break? (Leaning wordless after the three claims.)
2. **Prize stone** — fully blank, or first strokes already cut? (First-strokes sharpens "who finishes it" but needs the Latin gate cleared.)
3. **Latin on screen** — blocked until source-verified (see §2 gate).
4. **Final card** — month name / etymology tag at the cut, or pure black?

---

## 8. Credits (transparent AI attribution)

- **Creative direction:** a][ productions
- **Video generation:** Google Veo (via Flow)
- **Reference images / frame anchors:** Nano Banana Pro
- **Voice:** ElevenLabs
- **Music:** Suno
- **Post / compositing / assembly:** Claude Code + ffmpeg
- **Source grounding:** Ovid, *Fasti* Book 6; Macrobius (Fulvius Nobilior derivation)
