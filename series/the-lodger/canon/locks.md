# THE LODGER — Canonical locks

Locked 2026-08-19 after Stephen's casting call (Vascari = candidate C, Cora = candidate B,
house = A2 regenerated to summer). Inject the lock blocks **verbatim** wherever
`{{VASCARI_LOCK}}` / `{{CORA_LOCK}}` appears in a prompt. Pass the listed canon images as refs
on every identity-bearing generation (face-visible rule: if the face appears in shot, a ref
that clearly shows the face must be among the refs).

## {{VASCARI_LOCK}}

> A pale man who appears in his late twenties, ink-black hair worn slightly too long, pale grey
> eyes, sharp high cheekbones and fox-like features, a listening-animal stillness. Charcoal wool
> frock coat of an old-fashioned cut, black waistcoat, high white collar, dark cravat, black
> leather gloves on both hands. Immaculate, unhurried, courteous.

Refs: `char_vascari_face.png` (cast 3/4, porch dusk) · `char_vascari_front.png` (frontal bust,
lamplight) · `char_vascari_full.png` (full-length, hall, case + both gloves + boots).
Persistent details: small brown leather traveling case; silver watch chain; pristine black
boots that are never muddy; **gloves stay on in company until Ep 7**. In 1934 his suit is half
a century out of fashion — that wrongness is the point; never modernize him. His refs survive
the era migration unchanged.
Voice descriptor (native Veo dialogue) — **RELOCKED 2026-08-22**: *a young man's low, unhurried
voice with a soft North Carolina drawl, courteous in an old-fashioned way.* The earlier
"faintly accented, old-world courtesy" wording drifted European aristocrat in the voice harvest;
never leave the accent implicit, always name the region. Source of truth:
`characters/vascari/character.json` and `series-config.voice_descriptors`.

## {{CORA_LOCK}}

> A young woman of twenty-three, light auburn hair pinned back with soft loose strands escaping
> at the temples, hazel eyes, fine delicate features, smooth clear skin, a quiet loveliness —
> wariness in her eyes, never in her skin. Faded cotton print house dress with a small floral
> pattern, elbow-length sleeves, a lightly worn canvas apron, worn low-heeled shoes.

*(Era migration 2026-08-19: wardrobe moved from the 1898 draft to 1934. Aged down 2026-08-20
per Stephen — slick-romance register: hardship is stakes and setting; it never ages her face
or dirties her past "lightly worn." Her clothes must always read current-for-1934 — she dates
the film for the audience.)*

Refs: `char_cora_face.png` (cast 3/4, lamp + staircase) · `char_cora_front.png` (frontal bust)
· `char_cora_full.png` (full-length with lamp).
Persistent details: signature brass oil lamp; ring of house keys at her waist (introduce by
Ep 9). Voice descriptor (native Veo dialogue): *soft North Carolina accent, guarded.*

## House — establishing plate

`env_house_ext_dusk_rain.png` — gable-fronted two-story frame Victorian, weathered whitewash,
deep covered porch with a porch swing, lace curtains, a single warm amber-lit downstairs window,
low picket fence, vegetable garden bed (tomatoes, cabbages), great oak in full summer leaf;
damp rutted dirt lane in the foreground, puddles reflecting the lit window. Summer 1934, last
light, steady warm rain. An 1890s-built house — exactly the aging stock a Depression boarding
house would be. Poor but proud — cared-for, never derelict.

## Title treatment — LOCKED

Hoefler Text, ivory (#F1E9DA), soft blurred black shadow. "The Lodger" (large) over
"Episode N — Title" (small), block centered in the **55–65% frame-height band** over the dark
foreground of the establishing shot (true bottom-third is covered by Shorts UI; upper third
fails against bright sky). Reference: `title_treatment_ref.png`. Same treatment every episode.

## Interior plates (filed 2026-08-19)

- `env_entry_hall.png` — front door with rain-streaked oval glass + transom, side table with
  brass lamp, staircase rising frame-right into dark. Governs interior geography for S5–S13
  and the S7 book-end anchors.
- `env_parlor.png` — writing desk with open ledger (script indistinct — keep it that way) and
  brass lamp, cold stone hearth, worn leather armchair, pipe in a small bowl on its side table,
  lace curtains, rain on dark glass.
- `still_fathers_chair.png` — the same chair/table/pipe as the parlor, centered for the S4
  push-in; **cobwebs on the chair arm** — the one thing in a proudly-kept house she won't
  touch. Deliberate shrine detail; carries forward to Ep 14 (the father's return).

## The boarders — light canon (filed 2026-08-22, Ep 1 v2)

Six rooms; **three occupied**. The house is half-full: alive in the evenings and still failing.
Glance-approved by Stephen before the Ep 1 v2 Veo spend. They recur at least at Eps 14 and 20.
Boarders are asleep upstairs or absent for every Vascari night-beat unless a beat says otherwise.
**Cap any single frame at 4–5 people** (body-pile RAI).

| Boarder | Ref | Lock |
|---|---|---|
| **Mr. Pruitt** | `char_boarder_pruitt.png` | Late sixties, lean and straight-backed, weathered kind face, full white mustache, thin white hair. Retired railroad man; the checkers shark. Collarless white shirt, sleeves rolled, dark trousers, dark suspenders. |
| **Mr. Odom** | `char_boarder_odom.png` | Early sixties, heavyset and broad, round good-humoured face, bald with a close-cropped grey fringe, clean-shaven. Loses at checkers nightly and comes back nightly. Grey work shirt, braces. |
| **Miss Vann** | `char_boarder_vann.png` | Mid-forties country schoolteacher, composed and handsome, dark hair in a low neat roll with grey at the temples, fine wire-rimmed spectacles. Plain navy shirtwaist, small white collar, cameo at the throat. Marks papers by lamplight — **the papers are always blank; no legible text, ever.** |

Only Pruitt has spoken so far (Ep 1: *"King me."*). Native-dialogue voice descriptor for him:
*a warm gravelly old man's voice with a soft North Carolina drawl.*

## The common room — plate

`env_common_room.png` — **the parlor, widened**, not a separate set. Same dark walnut panelling,
same cold swept stone hearth, same brass chimney lamps, same lace curtains on rain-dark glass,
plus a long boarding-house supper table under worn oilcloth, cleared after supper to white enamel
coffee cups and a pot, and **one** checkerboard. Her writing desk with the ledger sits at the back
under the window. **Father's leather armchair stands alone and empty beside the hearth** — so the
chair still (`still_fathers_chair.png`) reads as the one empty seat in a full room. Hearth is
**cold in every shot** (high summer). This single set carries the common room, the ledger, the tin
box and the knock.
