# AUGUST — Shooting Script / Spine v1

**Series:** Monthly etymology series
**Format:** 9:16 vertical, target 70–75 s (hard ceiling 75)
**Version:** v1 — 2026-08-27
**Status:** Ready for production. Concept locked; shot durations are targets, trim in edit.

---

## 1. Concept (production-only, never on screen)

*Augustus* meant "consecrated by augury" before it meant "venerable." August is the month named for a man whose title means *bird-approved*. Everything downstream — author, authority, augment, inaugurate — is bird-reading.

The film: a Roman street where nobody will cross until a bird gives the sign. A kestrel hovers at the frame edge and never enters. The crowd waits, and strains. A goose walks across and the city exhales. Then more geese, and every crossing is read as permission for something bigger, until the city tears itself apart around birds that are doing nothing but walking and eating. Augustus, assembled from starlings, dissolves. A goose stands where he stood.

**Argument (never stated):** authority withheld is paralysis; authority handed out to everyone is collapse. Both run on birds.

**Sub-floor (never stated):** geese are the birds that saved Rome (Capitoline geese, 390 BCE). The savior-bird, multiplied, is what the city can't survive.

**Restraint rules:**
- No text on screen except the end card. No VO. No dialogue.
- The geese never do anything. No goose attacks, chases, or reacts to people. They walk, eat, honk. The riot is entirely human-authored.
- Nobody explains the rule. The viewer learns it from where people look.

---

## 2. The Rule (what the viewer must infer)

1. Permission comes from the sky. Everyone keeps glancing up and to the right, where the kestrel is.
2. Nobody is stopping anyone from crossing except each other. When someone steps off the kerb, neighbours haul him back — automatically, without anger.
3. A bird crossing the street from screen-left to screen-right is "yes."
4. Once the geese arrive, nobody looks at the sky again. They look at the ground.

**Direction note:** Roman augural convention treated the left (*sinistra*) as the favourable side. A goose entering from screen-left is favourable in Roman terms *and* reads as forward motion in Western reading direction. Keep every "yes" crossing left → right. The kestrel is upper-right, i.e. not on the favourable side, and never enters.

---

## 3. Visual Register

- **Light:** high-summer noon. Overexposed sky, hard black shadows, dust in the air. Sections A–C are noon. Section E is dusk.
- **Texture:** cheap. Undyed and ochre tunics, sweat, flour, dirt. No gleaming marble, no Hollywood Rome. Reference the crowd texture of Fellini's *Satyricon*, not *Gladiator*.
- **Street:** a narrow street between insula facades, a raised kerb on each side, and **stepping stones across the roadway** (Pompeii-style). The crossing is physically provided and refused. The stepping stones stay empty until B2.
- **Camera:** mostly static or very slow push. Handheld only in Section C, and only slightly.
- **Colour grade (Claude Code):** lift blacks slightly, push the sky toward white, warm midtones. Section E cools.

---

## 4. Audio Design

No music until Section E. No VO. No dialogue. Every Veo prompt carries an audio note; final sound is built in Claude Code from Veo audio, library, and Suno.

**Layers:**
- **Kestrel bed:** rapid wingbeats close-miked, thin high wind. Present under all of Section A, dropped after B1, returns only for D1.
- **Crowd bed:** starts as breath and shuffling, becomes murmur, becomes shove-and-grunt. Never words. Rises across A.
- **The honk:** August's audio signature (as the howl was February's). First honk at B1, dry and single. Layered honking builds across C. Final honk over black at E4 — same sound, transformed meaning (Rose mechanism).
- **Riot:** wood cracking, ceramic breaking, fire, running. Keep it dry and close, not epic.
- **Starlings:** the sound of a murmuration is a soft roar of wings. Enters at E1, peaks at the scatter (E2), fades to silence under E3.
- **Tone (Suno):** one sustained held chord, no rhythm, no melody. Enters under E1, holds through E3, **cuts dead on the black** before the honk.

**Goose honk source:** Veo audio is a candidate but unreliable. Plan on a library or field-recorded domestic goose honk for B1 and E4; these two must be the same recording.

---

## 5. Recurring Elements — Reference Sheets (Nano Banana Pro)

Generate a character sheet (front / three-quarter / profile, neutral background, noon light) for each before any Veo generation. Anchor every Veo shot with a shot-specific frame derived from these.

| ID | Description |
|---|---|
| **KERB MAN** | 40s, heavy build, cropped grey hair, undyed tunic, leather sandals, sweat at temples. The one who breaks and is hauled back. First to cross. |
| **FIG WOMAN** | 30s, dark braided hair, ochre palla over a plain tunic, basket on hip. |
| **BAKER** | Bald, 50s, floured apron over a tunic, forearms burned. |
| **SENATOR** | 60s, white toga with purple stripe, thin, hand that's half raised. |
| **CHILD** | About 7, close-cropped hair, short tunic, barefoot. |
| **HERO GOOSE** | White domestic goose, orange bill and feet, clean. Consistency matters most for B1, C9, E2, E3. |
| **KESTREL** | Eurasian kestrel, male: grey head, rufous back, barred tail fanned in hover. |
| **STREET PLATE** | Narrow street, insula facades three storeys, raised kerbs, stepping stones across the roadway, a fig stall on the near kerb, a bakery doorway on the far side. This is the NBP anchor plate for all Section A–C geography. |
| **FORUM PLATE** | Open forum at dusk, an empty stone plinth centre-frame, colonnade behind, thin smoke. Anchor for Section E. |

---

## 6. Composited Elements (Claude Code)

### 6.1 The Kestrel Overlay
Generate one hero hover plate (A1) against a clean bright sky. In Claude Code, key or matte the bird and overlay it into the **upper-right corner** of every Section A shot that shows sky (A2, A6, A7, A10), partially cropped by the frame edge. The bird should never be fully inside the frame — it sits on the border. This keeps it consistent across shots without regenerating it. Loop the hover plate as needed; hover is naturally loopable.

### 6.2 Starling-Augustus
**Primary approach: particle sim, not Veo.**

1. Generate the **goose-on-plinth plate** in Veo (E2/E3 base): forum at dusk, one white goose standing on the empty plinth, still. This is the plate the figure is composited *onto*.
2. NBP: generate a **silhouette mask** — solid black silhouette of a classical statue in the Augustus of Prima Porta pose (contrapposto, right arm raised and extended, cuirass, cloak over left arm) on white. The raised arm is the read; everything else is secondary.
3. Claude Code: boids/particle simulation (numpy) of ~8–12k small dark points with slight motion blur. Timeline:
   - **E1 (4 s):** points already in the mask shape, jittering, breathing at the edges like a murmuration under tension. The shape holds but is never still.
   - **E2 (3 s):** on cue, all points accelerate upward and outward, clearing frame in ~1.5 s, revealing the goose on the plinth beneath.
4. Composite the sim over the goose-plate with the plinth as the figure's base. The goose is hidden inside the figure's footprint until the scatter.

**Fallback:** Veo prompt for "a dense flock of starlings holding the shape of a standing classical statue" — expect literalness problems (statue with birds on it). Try at most 3 generations before committing to the sim.

---

## 7. Shot List

Durations are usable-clip targets. Each Veo prompt is 9:16. Audio notes are part of the prompt. Do **not** add "static camera angle unchanged" unless marked FIXED.

### SECTION A — THE WAIT (target 0:00–0:28)

**A1 — Kestrel hero plate** · 3 s · FIXED · composite source
> A kestrel hovering in place against a bright hazy midday sky, wings beating rapidly, tail fanned, head perfectly still. The bird is in the upper right of frame, partly cut off by the frame edge. Hard sunlight, sky slightly overexposed. Static camera, fixed shot. Audio: rapid wingbeats close, thin high wind, nothing else.

*Also: generate a second clean take with the bird fully in frame for keying.*

**A2 — Street, wide** · 4 s · NBP anchor: STREET PLATE
> A narrow ancient Roman street at noon, stepping stones across the roadway. A crowd of thirty people in plain tunics is bunched on the near kerb; the far kerb and the stepping stones are empty. Everyone is looking up and to the right at the sky, shifting their weight. Hard overhead light, dust in the air. Slow push in. Audio: shuffling feet, breathing, a distant cart, no voices.

**A3 — Kerb Man** · 3 s
> Medium shot, a heavy man in his forties in an undyed tunic stands at the edge of a raised stone kerb. His right foot lifts over the edge, hovers, and comes back. He glances up and to the right, wipes sweat from his temple. People pressed behind him. Noon light, hard shadows. Audio: his breathing, a shuffle of sandals, no voices.

**A4 — Fig Woman** · 3 s
> Close on a woman's hand hovering between two ripe figs on a wooden stall. The hand moves toward one, stops, moves toward the other, stops. She glances up and to the right; the vendor behind the stall does the same. Noon light. Audio: flies, a basket creaking, no voices.

**A5 — Baker** · 2 s
> A bald baker in a floured apron stands in a bakery doorway holding a long wooden peel with a loaf half out of a brick oven. He is sweating and looking up past the doorframe at the sky. Heat shimmer at the oven mouth. Audio: fire crackle inside the oven, no voices.

**A6 — Senator** · 3 s · kestrel overlay upper-right
> A thin elderly man in a white toga with a purple stripe stands on stone steps above a crowd, his right hand half raised. The crowd below is not looking at him; they are all looking up and to the right at the sky. His hand trembles slightly. Noon light. Audio: murmur of a crowd, no words, wind.

**A7 — Kerb, thickening** · 3 s · kestrel overlay upper-right
> The crowd on the raised kerb has grown denser. People shift from foot to foot, bounce on their heels, glance up at the sky. More people arrive from behind and push in. Nobody leaves. Slight handheld drift. Audio: murmur rising, sandals scraping stone, a grunt, no words.

**A8 — Child** · 3 s
> A small barefoot child in a short tunic darts off the kerb onto the street. An adult arm catches the child by the shoulder and pulls them back into the crowd, calmly, without anger. The adult goes back to looking up at the sky. Audio: a small scuffle, no words.

**A9 — Bribe** · 2 s
> A man in the crowd holds a round loaf of bread up toward the sky with both hands, waits, lowers it, then holds up a single coin. Others around him glance at him and look back up. Noon light. Audio: crowd murmur, wind.

**A10 — Kerb Man breaks** · 3 s · kestrel overlay upper-right
> The heavy man in the undyed tunic steps down off the kerb onto the street with his whole weight. Immediately two people beside him grab his arms and haul him back up onto the kerb. It is automatic, not angry. All three resume looking up and to the right. Audio: a scuffle, a grunt, the crowd murmur continuing, no words.

**A11 — Kestrel, unchanged** · 2 s · reuse A1

*Edit note: Section A must feel slightly too long. If the room isn't restless by A10, the exhale in B doesn't land. Do not cut A short to save time; cut C instead.*

---

### SECTION B — THE GOOSE (target 0:28–0:36)

**B1 — The crossing** · 3 s · FIXED · hero goose
> Ground-level shot of an empty ancient Roman street with stepping stones. A single white domestic goose walks into frame from the left and crosses to the right, unhurried, and honks once. Static camera at street level. Noon light. Audio: one goose honk, clear and dry; otherwise complete silence.

**B2 — The foot** · 2 s
> Close on a heavy sandalled foot coming down from a stone kerb onto a stepping stone in the street, firmly. Dust puffs. Audio: the slap of the sandal, then a crowd exhaling all at once.

**B3 — Release** · 3 s
> A crowd pours off a kerb and across a narrow Roman street, laughing, some running. A woman bites into a fig. A baker pulls a loaf from an oven with steam rising. Bright noon light. Slight handheld. Audio: laughter, cheering, feet on stone, no words.

---

### SECTION C — MORE GEESE (target 0:36–0:58)

*Escalation order is deliberate: ordinary → transactional → political → destructive. Nobody looks at the sky after C3.*

**C1 — Two geese, the amphora** · 2 s
> Two white geese walk across a Roman street from left to right. At a market stall, a vendor hands a clay amphora to a man who had been reaching for it. Both glance down at the geese, not up. Noon light. Audio: two honks, crowd chatter without words.

**C2 — The vote** · 3 s
> A thin elderly man in a white toga on stone steps drops his raised hand. The crowd below roars and throws caps in the air. Three white geese walk past the base of the steps. Noon light. Audio: a crowd roar, honking.

**C3 — The flood** · 3 s
> A dozen white geese come around a corner into a narrow Roman street, honking, walking unhurried. People's feet move faster among them, running in every direction. Street level, slight handheld. Audio: a wall of goose honking, running feet.

**C4 — The stall** · 3 s
> A wooden market stall is tipped over and sacks of grain burst across the stones. People grab jars and cloth and run. Four white geese calmly eat the spilled grain in the middle of it. Noon light. Audio: wood cracking, ceramic breaking, honking, geese pecking.

**C5 — The door** · 3 s
> A heavy wooden door is kicked open and people push through into a building. A single white goose sits on the doorstep, unbothered, as they step over it. Audio: the door cracking, shouting without words, one honk.

**C6 — The Senator falls** · 3 s
> A thin elderly man in a white toga is lifted onto the shoulders of a crowd, then dropped. People step over him. Geese walk around him. Handheld. Audio: crowd roar, a thud, honking.

**C7 — Fire** · 2 s
> An iron brazier is knocked over in a narrow street and coals spill; flames catch the edge of a cloth awning. A white goose walks past the flames without reacting. Audio: fire catching, honking.

**C8 — Wide, smoke** · 3 s
> A narrow Roman street full of smoke. Figures run through it in every direction. Twenty white geese walk slowly through the smoke, some eating from the ground. Nobody is looking at the sky. Audio: fire, running, honking, no words.

**C9 — Goose, close** · 2 s · hero goose
> Close on a white goose's head as it eats grain from a burst sack. Firelight flickers on its feathers. It is completely calm. Audio: the goose pecking grain, fire crackling nearby, distant honking.

*Moderation note: if any C prompt is refused, reframe rather than push — "people push through," "flames catch the awning," "the stall is tipped." Avoid: riot, mob, attack, violence, blood, weapon.*

---

### SECTION D — INSERT (target 0:58–1:01)

**D1 — Kestrel over smoke** · 3 s · composite
> Hover plate from A1, composited upper-right over a sky plate with smoke drifting below and behind it. The bird is unchanged. Still hasn't entered.

> *Sky plate prompt:* A bright hazy sky with grey smoke drifting up from below the frame, slow. No ground visible. Static camera. Audio: distant fire and honking, muffled.

*Audio: kestrel wingbeat bed returns here, alone, for the full 3 s. This is the only place it comes back.*

---

### SECTION E — THE FIGURE (target 1:01–1:13)

**E-base — Goose on plinth plate** · 8 s source · FIXED · NBP anchor: FORUM PLATE · hero goose
> An open Roman forum at dusk, empty of people. A single white domestic goose stands still on top of an empty stone plinth in the centre of frame. Thin smoke drifts. A few white geese on the ground in the distance. Cool dusk light, static camera. Audio: distant wind, faint honking far away.

**E1 — Augustus of starlings** · 4 s · composite (see 6.2)
> Particle sim of starlings holding the Prima Porta pose on the plinth, over the goose plate. The shape breathes at the edges. The goose is hidden inside the figure.

*Audio: starling murmuration roar enters soft. Suno tone enters under it.*

**E2 — Scatter** · 3 s · composite
> All starlings release upward and outward at once, clearing frame in ~1.5 s. The goose stands on the plinth where the figure stood.

*Audio: wing roar peaks, then fades.*

**E3 — The goose** · 3 s · hero goose
> Slow push in to a close-up of a white goose standing on a stone plinth at dusk, head turned to camera, one eye. The goose is still. Cool dusk light. Audio: near silence, faint wind.

*Audio: wings gone. Suno tone holds. Cut to black — tone cuts dead on the cut.*

**E4 — Black** · 1.5 s
Black. Silence for a beat. **One honk**, dry, same recording as B1. Then end card.

---

## 8. Assembly Notes (Claude Code)

- **Running order:** A1–A11 → B1–B3 → C1–C9 → D1 → E1–E4 → end card. Total target 70–75 s before end card.
- **Trim priority if over:** cut C first (drop C6 or C7), then B3, never A.
- **Pacing:** A is held shots, cuts every 2–4 s, getting slightly faster from A7. B slows down: B1 is the longest-feeling 3 s in the piece. C cuts fastest. D and E slow all the way down.
- **The gaze shift:** confirm in edit that every A shot has someone looking up-right, and no shot after C3 does. If a C generation has people looking up, don't use it.
- **Kestrel overlay:** see 6.1. Same position every time, same partial crop.
- **Left → right discipline:** every goose crossing in B and C enters from screen-left. If Veo mirrors it, flip the clip.
- **The two honks:** B1 and E4 must be the same recording. Everything between them is layered and different.
- **Grade:** A–C warm and overexposed; D neutral; E cool. The black at E4 is true black.

---

## 9. End Card

Match the series end card treatment from prior months. Minimal:

```
AUGUST

a][ productions

Video generation: Google Veo via Flow
Reference imagery: Nano Banana Pro
Compositing, simulation, assembly: Claude Code + ffmpeg
Sound: [library / field recording]; tone: Suno
Concept developed with Claude
```

Transparent AI attribution stays. No Premiere. Adjust the sound line to what's actually used.

---

## 10. Risks and Fallbacks

- **Goose consistency across C:** the flood shots don't need the hero goose; any white domestic geese are fine. Only B1, C9, E-base, E3 need the hero.
- **Veo crowds:** crowd shots drift. Generate A2 and C8 first as geography anchors; if Veo won't hold 30 people, halve the count in the prompt and let the framing do the work.
- **"Looking up" drift:** Veo may have people look at the camera instead. If it persists, add "looking up past the top of the frame at the sky" and drop "to the right."
- **Kestrel hover:** if Veo won't hold a clean stationary hover, a short library clip is acceptable for the overlay plate — it's the one element where stock is invisible.
- **Starling figure:** particle sim is primary. Do not spend more than 3 Veo generations on the fallback.
- **Moderation:** see C section note. Plan reframes before generating.

---

## 11. Open Decisions (owner: Stephen)

1. Series end card treatment — reuse or evolve.
2. Whether the Suno tone is worth it or whether E plays better in pure sound design. Recommendation: try it, cut it if it softens the black.
3. Goose honk source.
