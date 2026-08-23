# THE LODGER — Series Home

A supernatural romance **vertical microdrama**: 9:16, 60–90 seconds per episode, every episode
ending on a swipe-point. Arc 1 is 20 episodes (see `arc-1-beats.md`, the canonical beat sheet,
pulled from Stephen's draft 2026-08-19). The series should ultimately run 20–40 episodes.

**Genre contract:** period Southern Gothic vampire romance, played sincere — the register is
*Dracula in a boarding house* by way of Bluebeard, wearing the full trope wardrobe of vertical
drama (broke heroine, beautiful rich stranger with a secret, forbidden room, love triangle
between the daylight man and the midnight man, rules that will be broken). And it photographs
**slick**: leads stay screen-pretty — the Depression is stakes and setting, never skin texture
(Stephen, 2026-08-20).

---

## Where things live

| Thing | Location |
|---|---|
| Beat sheet (arc 1, canonical) | `series/the-lodger/arc-1-beats.md` |
| Series bible (this file) | `series/the-lodger/README.md` |
| Episode shooting scripts | `series/the-lodger/episodes/epNN-<slug>.md` |
| Canonical refs (faces, plates, props) | `series/the-lodger/canon/` — these persist across ALL episodes; never archived with a workspace |
| Per-episode build workspace | `data/workspace/lodger-epNN/` (refs/frames/clips/final/scratch per workspace convention) |
| Exports | `data/exports/lodger-epNN-vN.mp4` |

**Slug rule:** always `lodger-epNN` / project_id `lodger_epNN`. Never bare `the-lodger` — that slug
belongs to the archived 2026-05 houseplant tone poem (`data/workspace-archive/the-lodger/`,
`briefs/the_lodger_brief.md`), an unrelated piece that happens to share the title.

**Shared universe — CONFIRMED (Stephen, 2026-08-19):** this is the same world as the camp short
*Outlaw Vampire Sommeliers — From Outer Space!* (`briefs/vascari_death_scene_edit_guide.md`).
The Lodger is a romantic interlude in that larger myth — Vascari falls in love **and is loved in
return** — set long before the story where Deputy Holloway, the same Holloway who courts Cora
here, kills Vascari with a corkscrew. Every Holloway scene carries that dramatic irony; never
wink at it on screen. **Register discipline:** the Sommeliers layer (aliens, camp) never
surfaces in Arc 1 — this series plays sincere Southern Gothic. Deep-canon texture available but
deploy only with Stephen's sign-off: Vascari is a *sommelier* (tasting-notes speech; might
accept a glass of wine while every supper tray goes untouched — pairs with Ep 4); Ira, a vampire
of his kind who opposes harvesting humans, exists and could seed later arcs. How Holloway
persists to his cryosleep era is OPEN canon — do not invent it.

## The vertical playbook (format contract, every episode)

1. **Hook ≤3.5s.** Open on the most charged image + a VO line that promises the genre. Never
   open on atmosphere alone.
2. **Episode skeleton: Hook → Friction → Spike → Button.** One emotional turn per episode. No
   subplots inside an episode.
3. **Swipe-point ending.** Final shot lands the beat-sheet swipe line/image, hard cut to black +
   sting. Next-episode title stamp ≤1.5s. Total runtime 60–90s (loop-friendly: the end card is
   brief so the loop re-hits the hook).
4. **Each episode pays the previous swipe inside its first 10 seconds.** Ep N opens in the
   shadow of Ep N−1's last image.
5. **VO narrator = her, retrospective, confiding.** Past tense, close-mic, like she's telling
   you what happened. VO carries exposition so on-camera dialogue stays sparse (also our best
   Veo hedge — fewer lip-sync-critical gens).
6. **Faces fill the frame.** CU/MCU dominate; two-shots stack in depth (foreground shoulder,
   background face), never side-by-side. Wides are ≤4s and earn their place. The house's
   verticals (stairwell, doorways, tall windows) are the establishing vocabulary.
7. **Caption everything spoken.** Dialogue regular, VO italic. Sentence case, white with soft
   black shadow, centered ~58–62% frame height (inside Shorts safe zone — nothing in bottom
   ~30% or right edge). One line ≤ ~30 chars, hard pop in/out.
8. **Title stamp** after the hook (~3.5–5.5s): Hoefler Text, ivory, soft shadow — "The Lodger"
   + "Episode N — Title", block centered in the **55–65% height band** over the establishing
   shot's dark foreground (LOCKED 2026-08-19; ref `canon/title_treatment_ref.png`). All text
   burned programmatically (PIL sprites — local ffmpeg has no drawtext); never ask Veo/nano to
   render text; every gen prompt carries the no-text suppressor.

## Setting & period canon

**ERA LOCK — summer 1934. Eastern North Carolina: coastal-plain tobacco country, deep in the
Great Depression.** (Locked with Stephen 2026-08-19, superseding an earlier 1898 draft that
misread the beats. Season = summer, per Stephen.) Why this era is what the beats were written for:

- **Foreclosure** (Eps 5, 15, 19, 20) is *the* Depression story — the banker, the papers her
  father signed, the auction.
- **Gold** (Eps 1, 12, 20): Executive Order 6102 recalled private gold in 1933. A year on, a
  stranger paying in uncirculated 1803 coins isn't just eerie — it's practically contraband,
  and it hands Deputy Holloway a genuine legal thread to pull in Ep 12. "Nobody pays in gold"
  lands three times harder in 1934.
- **"Wires to Raleigh, to Norfolk"** (Ep 12): Norfolk is eastern NC's metropolis — the
  geography was in the beats all along.
- **Boarding houses** are how the Depression housed itself; **oil lamps stay canon** (the REA
  doesn't reach these farms until the late '30s at the earliest).
- **Holloway continuity:** the Sommeliers short freezes him as "a 1950s lawman." A deputy in
  his late 20s in 1934 is a lawman in his late 40s in the 1950s — one mortal lifetime, no
  longevity mystery. The eras interlock; the 1898 draft would have made him ~90 at cryosleep.

**The town: Gilead, N.C.** (working name) — a county-seat rail town on the coastal plain. Flat
tobacco and cotton country, loblolly pine, sandy-clay roads that go to mud in the rain, mule
wagons and the occasional Ford, a depot with a telegraph. The boarding house is an 1890s-built
frame Victorian — exactly the aging housing stock a 1934 boarding house would be — weathered
whitewash, deep porch with a swing, picket fence, vegetable garden, a great leafed oak; poor
but proud, never derelict (canon plate `canon/env_house_ext_dusk_rain.png`, which survives the
era migration unchanged). Steep interior staircase = our best vertical composition; it recurs
constantly per the beats. Summer texture: cicadas and crickets after dark, fireflies, a far
train whistle, heat everyone feels but him — a man in a heavy black suit of another century,
and never a bead of sweat.

**Light canon:** interiors amber oil-lamp warmth; exteriors blue-hour and rain-grey. Him: the
lamp never quite warms his face (cool rim) — stylistic note, not a hard lock. **Ep 1's rain is
steady and dreary; the *violent* storm is reserved for Ep 10.**

## Cast & canon

| Character | Name | Notes |
|---|---|---|
| The heroine | **Cora May Albright** (goes by Cora) — CONFIRMED + CAST 2026-08-19 (`canon/char_cora_*.png`) | Full name is dramatically load-bearing (Ep 4: he knows it unprompted; Ep 13: he says it "the way other men say amen") — choose it for music before Ep 4. Runs the Albright boarding house alone. Reads a true early 20s — screen-pretty, capable; hardship shows in her eyes and circumstances, never as wear on her face (aged down per Stephen 2026-08-20). Signature prop: her oil lamp. Signature key ring (Ep 9). |
| The lodger | **Vascari** (freight crate: "Lord V—", Ep 8) — CAST 2026-08-19 (`canon/char_vascari_*.png`) | Appears late 20s. Pale; ink-black hair a touch too long; pale grey eyes that catch lamplight like an animal's (Ep 5 canon). Fine but old-fashioned clothes — a black frock-coat suit cut half a century out of date, a Victorian ghost walking through 1934, immaculate. **Always gloved in company until Ep 7** (first skin contact is Ep 7's beat; gloves protect it). Never marked by weather. Pays in old gold. |
| The deputy | **Deputy Holloway** — same-world CONFIRMED (first name open; working: Sam) | Sunny, broad-shouldered, easy. The daylight man. First appears Ep 3. He is *the* Holloway who will one day kill Vascari — play him warm and honest; the irony is ours, not his. |
| The father | (unnamed) | Absent until Ep 14; his empty chair is set dressing from Ep 1. Alive — VO must imply absence, never death. |
| Granny Holt | Granny Holt | Ep 17. |

**Continuity rules seeded by the beats (do not violate early):**
- **No skin contact between Cora and Vascari until Ep 7** (cold-touch beat). Gloves/staging enforce it.
- He is **never** seen in direct sunlight; he goes out only at night (stated Ep 9; visible pattern from Ep 2's sunrise-facing room request).
- **He makes no sound when he moves** — strip/never add footstep foley for him from Ep 1 onward (pays off Ep 9 "she never heard the stairs" and Ep 14's silent descent).
- Threshold/invitation lore stays **unvoiced and ambiguous** (Ep 1 stages it visually; commit to nothing).
- Coin close-ups: old gold, but **never show a legible date** before Ep 12's magnifying-glass reveal (mint 1803, uncirculated).
- The supper-tray ritual begins Ep 4; the room choice (facing away from sunrise) is Ep 2's beat — don't pre-empt either.
- Blood appears exactly once in Arc 1 (Ep 10, her cut palm). Plan it stills-first/implied per RAI doctrine when we get there.

**Character lock strategy:** nano-banana canonical refs (NOT lock_character's Imagen path) —
face-visible CU sheet + full-length in costume + profile for each lead, generated once, approved
by Stephen, filed in `canon/`, injected as refs into every downstream nano anchor and every
identity-bearing Veo gen. Locked 30–50 word descriptions live in `canon/locks.md` once extracted.
**The two lead faces are a piece-defining decision — explicit Stephen sign-off before any Veo
spend on Ep 1** (they commit 20+ episodes). *(DONE 2026-08-19: Vascari = candidate C, Cora =
candidate B, house = summer regen of A2; locks in `canon/locks.md`.)*

## Sound canon

- **Her VO (ElevenLabs):** warm, low, young Southern female; audition 2–3 voices at Ep 1 build;
  pin voice_id here afterward. Settings via `compute_audio_profile` (mood intimate/tension per scene).
- **On-camera dialogue: Veo native** (doctrine). His voice descriptor in every dialogue prompt:
  *"a low, unhurried voice, faintly accented, old-world courtesy."* Hers: *"soft North Carolina
  accent."* Native voices drift between gens — keep his lines short and distinctive; EL dub-over
  is the edit-rescue if a read breaks the spell.
- **Series theme ("Lamplight," EL music, ~75s instrumental):** slow gothic parlor waltz — solo
  slightly-detuned upright piano, low cello drone, sparse, rain-quiet. Generated once, reused
  every episode (branding + cost).
- **Sting kit (EL SFX, generated once):** dread hit (low cello sforzando + sub drop), soft
  romantic swell, "question" rise. Every swipe-point lands on one.
- Rain beds, knocks, coins, hoofbeats etc. via EL `generate_sound_effect`; Veo native ambience
  stays on under everything (audio default ON).

## Production doctrine (pipeline mapping)

- **The series builds through a manifest-driven production kit** — spec in
  `production-cycle.md`. Tooling first; Episode 1 is the shakedown run. Per-episode state lives
  in `data/workspace/lodger-epNN/episode.json`, never only in chat.

- Veo 3.1 **Quality direct**, 9:16, one gen per shot, native audio ON (skip-fast-draft;
  autonomous-build-doctrine). Book-end anchors on continuity-critical shots; `frame-qa` +
  `anchor-drift` before any Veo spend.
- Full **clip acceptance gate** per gen: normalize → clip-qa (with explicit "should NOT be
  present" context) → **clone-check on every motion shot** → transcribe on dialogue shots.
  Flag + recommend; never auto-reroll.
- Dialogue staging: **MCU, not ECU** — 9:16 close-ups magnify lip-sync error (vertical-drama
  dubbing literature agrees); keep mouths off macro.
- Review deliverable: native-res master + debug-overlay copy (`add-timestamp.py`) + 720p signed
  URL via `tools/gcp/share.cjs`. No 4K before review.
- **Budget: ≤ $22/episode** (~$16–18 typical + one protected retake on the episode's money
  shot). Cost-log per episode via `costlog.py`. At 20 eps ≈ $320–440/arc.
- **Stock library:** establishing/connective shots (house-in-rain ext, stairwell, hallway,
  dusk porch) are series assets — log them in `canon/stock-shots.md` as they're built and reuse
  shamelessly across episodes (vertical dramas do; it reads as brand, not cheapness).

## Episode index — Arc 1

| Ep | Title | Script | Status |
|---|---|---|---|
| 1 | The Stranger at Dusk | `episodes/ep01-the-stranger-at-dusk.md` | **RESTRUCTURE APPROVED — script v2.1 READY FOR BUILD (2026-08-22).** Lively common-room + boarders intro, extended books beat, episode ends on D1 "I'm told you let rooms." 5 new gens + 7 reused v1 clips (≈$8.60 incremental); creative decisions resolved (B1 keep / V3 keep / no end VO); boarder faces = build-day glance-approval gate; beat-sheet ripple DEFERRED until Stephen sees the cut (script §7 — do not touch arc-1-beats.md). v1 (63.5s) in `data/workspace/lodger-ep01/final/`; v1.4 script in git history. |
| 2 | House Rules | — | beats only — **inherits v1 S9–S13 (terms/boots/gold/condition, gated + word-perfect) pending Ep 1 v2 approval** |
| 3 | Daylight | — | beats only |
| 4 | The Untouched Tray | — | beats only |
| 5 | The Ledger | — | beats only |
| 6 | The Church Social | — | beats only |
| 7 | Midnight | — | beats only |
| 8 | The Crest | — | beats only |
| 9 | The Locked Door | — | beats only |
| 10 | The Storm *(paywall-slot cliffhanger)* | — | beats only |
| 11–20 | Morning After … Paid in Full *(arc finale)* | — | beats only |

Beats may be revised as we go (per Stephen, 2026-08-19); scripts are written one or two episodes
ahead, never the whole arc.
