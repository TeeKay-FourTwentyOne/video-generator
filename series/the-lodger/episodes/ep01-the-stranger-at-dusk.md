# THE LODGER — Episode 1: "The Stranger at Dusk"
### Shooting script v1.4 — 2026-08-20 — status: **PREP COMPLETE.** Cast, era (summer 1934 eastern NC), title, anchors (QA'd), manifest, kit, and VO audition all ready. **Production session starts at `ep01-build-runbook.md`** — the manifest (`data/workspace/lodger-ep01/episode.json`) supersedes this doc's shot table as the machine source of truth; this doc remains the creative reference.

**Beat source:** `../arc-1-beats.md` Ep 1 — *Rain. Establish her fast: running the boarding house
alone, ledger that doesn't balance, father's empty chair. A knock at last light. A young man,
beautiful, travel-worn but wrong for it — no mud on him. He asks for a room and pays a month in
advance in old gold coins. Swipe: "One condition," he says. "No one enters my room. Not even
you." Beat. "Especially you."*

**Logline:** A broke boarding-house keeper answers a knock at last light and rents a room to a
beautiful stranger who pays in gold — and sets one impossible rule.

| Spec | Value |
|---|---|
| Format | 9:16, 1080×1920, 24fps, Veo 3.1 Quality, native audio ON |
| Target runtime | **~67s** (contract: 60–90s) |
| Veo gens | 12 shots (S1–S3, S5–S13) + 1 nano still (S4) + hook reuses S7 |
| Budget | est. **$17–19**, cap **$22** (incl. one protected S12 retake) |
| Workspace | `data/workspace/lodger-ep01/` |
| Emotional turn (one only) | *Salvation arrives — wearing a warning.* |

**Episode skeleton (Hook → Friction → Spike → Button):**

| Unit | Time | Content |
|---|---|---|
| HOOK | 0–3.5 | Door opens on his face in the rain (excerpt of S7) + VO hook line |
| — title | 3.5–5.5 | Series stamp over house exterior |
| FRICTION | 5.5–24 | Her poverty, alone: empty table, failing ledger, father's chair |
| SPIKE | 24–52 | The knock → the reveal → no mud → gold on the table |
| BUTTON / SWIPE | 52–65.5 | "One condition… Especially you." Her eyes. Black + sting. |
| End stamp | 65.5–67 | "Episode Two — House Rules" |

---

## 1. The script

**Working names** (flagged, see §8): CORA (heroine), VASCARI (the lodger). No name is spoken
on-screen in Ep 1 — the full-name reveal is Ep 4's beat; nothing here forecloses renaming.

**VO = Cora, retrospective, close-mic, confiding. All spoken text gets burned captions
(dialogue regular, VO italic).**

| # | Speaker | Line | Where |
|---|---|---|---|
| V1 | CORA (VO) | "Papa always said nothing good knocks after dark." | Hook (S0) |
| V2 | CORA (VO) | "Six rooms. Five of them empty." | S2 |
| V3 | CORA (VO) | "However I worked the figures, they came up short." | S3 |
| V4 | CORA (VO) | "Papa's chair. Right where he left it." | S4 |
| D1 | VASCARI | "Good evening, ma'am. I'm told you let rooms." | S8 |
| D2 | CORA | "Three dollars a week, with board. Supper's at six." | S9 |
| V5 | CORA (VO) | "Ten miles of mud in every direction. There wasn't a speck on him." | S10 |
| V6 | CORA (VO) | "He paid the month entire. In gold. *Nobody* pays in gold." | S11 |
| D3 | VASCARI | "One condition. No one enters my room. Not even you." *(beat, almost gently)* "Especially you." | S12 |
| V7 | CORA (VO) | "I should have told him no." | S13, into black |

Notes on the writing:
- V1 + V7 establish the series' narrator frame (she's telling this *afterward*) — pure vertical
  convention, and V1 is re-armed every loop.
- V4 says *left it*, not *lost him* — the father is alive (returns Ep 14). Keep absence ambiguous.
- V6's "Nobody pays in gold." is the caption-pop line of the Friction→Spike turn. No coin dates
  visible or mentioned (Ep 12's beat).
- D3 is the swipe. Delivery: unhurried, courteous, and the last two words *softer*, not harder.

---

## 2. Pre-build: canon assets (nano-banana, all before any Veo spend)

All refs → `series/the-lodger/canon/`. Space nano calls ~10s (429 backoff). No text in any image;
avoid the word "photograph" (film-stock edge-text trip); face-visible rule applies to both leads.

| Asset | File | Prompt sketch |
|---|---|---|
| Cora face sheet (CU + 3/4 + full) | `char_cora_*` | Young woman of 23, light auburn hair pinned back with loose strands, hazel eyes, screen-pretty capable warmth; faded 1930s cotton print house dress, lightly worn canvas apron; rural eastern North Carolina, 1934; warm oil-lamp interior light |
| Vascari face sheet (CU + 3/4 + full-with-case) | `char_vascari_*` | Man who appears late 20s, pale, ink-black hair slightly too long, pale grey eyes catching the light; charcoal frock coat of an old-fashioned cut, black waistcoat, white high collar, dark cravat, **black leather gloves**, small leather traveling case; immaculate; blue dusk rim light |
| House exterior plate (dusk rain) | `env_house_ext_dusk` | Tall two-story frame Victorian boarding house, peeling white paint, deep porch, one amber lit window, steady rain, blue last light, muddy lane in foreground — tall composition |
| Entry hall plate (lamplight) | `env_entry_hall` | Narrow entry hall, oil lamp on a small side table, steep staircase rising frame-right into dark, wallpaper, front door with oval glass |
| Parlor plate (desk + hearth + chair) | `env_parlor` | Small parlor: writing desk with ledger and lamp; cold hearth; worn leather armchair with a pipe on its side table |
| Father's chair still (S4 source) | `still_fathers_chair` | The armchair alone, lamp-edge glow, cold hearth behind, a thin layer of neglect — composed for slow push-in |
| Book-end anchors for S7 (A/B) | workspace `refs/` | See S7 |

**CHECKPOINT — PASSED 2026-08-19.** Stephen cast Vascari (candidate C, elegant predator), Cora
(candidate B, fine guarded), and the house (A2 regenerated to high summer, less mud). **Era
relocked the same day: summer 1934, eastern NC, Great Depression** — Cora's canon refs
re-dressed to 1930s wardrobe (face unchanged); Vascari, house, and interior plates survive
unchanged (his suit is deliberately antique; the house is 1890s-built aging stock). Locked
descriptions + canon ref paths live in `../canon/locks.md`. Remaining pre-Veo assets: S7
book-end anchors (all plates now done).

**Standard prompt suffix (every Veo gen):**
> Rural eastern North Carolina, summer 1934, Great Depression era, period-correct detail.
> Cinematic photoreal, shallow depth of field, tall 9:16 composition, subject centered. Warm
> oil-lamp interior palette / blue-hour rain exterior. No on-screen text, no titles, no
> captions, no watermarks.

---

## 3. Shot list

Per clip-acceptance-gate: `normalize-clip` always; `clip-qa` with explicit should-NOT-be-present
context; **`clone-check` on every motion shot**; `transcribe` on D1/D2/D3 shots. Flags go to the
keep / edit-around / reroll ladder — decisions queued for Stephen, no auto-reroll.

---

### S0 — HOOK (no gen — excerpt of S7)
- **Edit:** ~2.5–3.5s excerpt of S7's door-swing/reveal, cut on his eyes. VO V1 over it. Smash
  to S1 + title stamp.

### S1 — EXT: The house in the rain (establishing)
- **Gen:** 6s → use ~4.5s (title stamp rides over it from ~3.5s). First-frame anchor: `env_house_ext_dusk`.
- **Frame:** Static or near-static tall wide; house fills the vertical; one lit window.
- **Axes:** energy 0.15 / tension 0.35 / mood: desolate.
- **Prompt draft:** Static wide shot, slow almost-imperceptible push. A gable-fronted two-story
  frame Victorian boarding house at last light, weathered whitewash, deep porch with a porch
  swing, picket fence and garden bed, a great oak in full summer leaf, a single amber-lit
  window downstairs. Steady warm rain, damp rutted lane with puddles reflecting the lit window,
  dripping eaves. Sound: steady rain on a tin roof, cicadas dulled by the rain, distant low
  thunder. *(+ suffix)*
- **QA context (not-present):** no people, no animals, no vehicles, no signage or lettering, no lightning.
- **Series stock:** file the best take in `canon/stock-shots.md` — this exterior recurs all arc.

### S2 — INT: Alone at the long table
- **Gen:** 6s → use ~3.5s. Refs: `env_parlor`/dining + `{{CORA_LOCK}}`.
- **Frame:** MCU-to-medium; she stacks unused plates at a long table set for no one, lamp burning.
- **Axes:** 0.25 / 0.3 / melancholic. **VO V2.**
- **Prompt draft:** Medium shot. {{CORA_LOCK}} gathers untouched place settings from a long
  empty dining table by the light of a single oil lamp, stacking plates with practiced, tired
  economy. Quiet evening interior, rain on the windows behind her. Sound: rain, the soft clink
  of china, floorboards. *(+ suffix)*
- **QA:** clone-check (subject motion). Context: exactly one woman; no other person; no food on
  the table; table settings clean and unused.

### S3 — INT: The ledger
- **Gen:** 6s → use ~3.5s. Refs: `env_parlor` desk + `{{CORA_LOCK}}`.
- **Frame:** CU over her shoulder / insert: finger tracking down a ledger column, pencil taps,
  she closes the book softly. Figures soft-focus and oblique — **never legible** (Veo text
  gibberish; keep the page low in frame, shallow DOF).
- **Axes:** 0.2 / 0.45 / tense-quiet. **VO V3.**
- **QA context:** one woman's hands only; ledger writing indistinct; no legible characters; no
  second lamp appearing.

### S4 — INT: Father's chair (nano still + programmatic push — zero Veo)
- **Source:** `still_fathers_chair` → 3.0s push-in (~4%/s scale ramp), light grain to match.
- **Axes:** 0.1 / 0.4 / desolate. **VO V4.** Stills-for-stillness doctrine; also our safest shot.

### S5 — INT: The knock
- **Gen:** 6s → use ~3.5s. Refs: parlor desk + `{{CORA_LOCK}}`.
- **Frame:** MCU at the desk, lamp foreground; she writes; **three deliberate knocks**; her hand
  stops; she lifts her eyes toward the hall. No VO — the knock owns the beat.
- **Axes:** 0.3 / 0.7 / ominous.
- **Prompt draft:** Medium close-up. {{CORA_LOCK}} writes in a ledger by lamplight, rain heavy
  on the windows. Three slow, deliberate knocks sound from the front door. Her pencil stops
  mid-stroke. She lifts only her eyes. Sound: rain; three unhurried knocks on a heavy wooden
  door; the scratch of a pencil that stops. *(+ suffix)*
- **Edit note:** Veo's knock timing is uncontrollable — sync a clean EL knock SFX to her flinch
  in post regardless of what native audio delivers (mask-with-SFX doctrine).
- **QA:** clone-check. Context: one woman; no one else visible; nothing at the window.

### S6 — INT: The hall, lamp in hand
- **Gen:** 6s → use ~3.5s. Refs: `env_entry_hall` + `{{CORA_LOCK}}`.
- **Frame:** Tall shot down the entry hall; she carries the lamp toward the front door, staircase
  rising dark beside her (plants the stairwell for Ep 2+). Camera static or gentle drift.
- **Axes:** 0.3 / 0.75 / ominous.
- **QA:** clone-check (walking). Context: one woman; front door stays CLOSED this shot; no
  figure or silhouette behind the door glass yet.

### S7 — INT→EXT: THE REVEAL ★ (book-ended)
- **Gen:** 8s → use ~5.5s here + ~3s excerpt as S0. Two-figure shot — full anchor treatment.
- **Frame:** From inside the entry, past Cora's shoulder/back-of-head (her face NOT visible —
  drift-safe): the door swings open. VASCARI on the porch, still, travel case in gloved hand,
  rain sheeting off the eaves behind him, her lamplight finding his face. He does not move to
  enter. Depth-stacked vertical two-shot: her shoulder bottom-foreground, him centered.
- **Axes:** 0.35 / 0.9 / ominous-beautiful. Beat of nothing but rain before S8.
- **Anchors (book-end):** A = door closed, her silhouette + lamp at frame bottom. B = door open,
  him framed in the doorway exactly per `char_vascari_full`. `frame-qa` both vs canon;
  `anchor-drift` on the pair (door is the ONLY thing that may move; porch/props pixel-static).
- **Prompt draft:** From inside a dim entry hall, over a woman's shoulder in the near foreground,
  the front door swings slowly open. {{VASCARI_LOCK}} stands motionless on the rain-lashed
  porch, a small leather traveling case in one gloved hand, lamplight from inside catching his
  pale face. He inclines his head slightly. He does not step forward. Sound: rain loud then
  shielded by the porch; the door's hinge; a settling quiet. *(+ suffix)*
- **QA:** clip-qa + clone-check (door motion + two figures). Context: exactly two people — one
  woman seen from behind, one man in the doorway; no third figure; no reflections in the door
  glass; the man does not duplicate as the door passes him; door opens once.
- **This is the series' lead-reveal shot — comment bait. If it's merely okay, flag for Stephen
  rather than settling.**

### S8 — EXT porch: His ask (dialogue)
- **Gen:** 8s → use ~5s. First-frame from S7-B geometry (his doorway MCU).
- **Frame:** MCU Vascari (mouth NOT macro — lip-sync hedge), rain behind the eaves, courteous
  stillness. **D1:** "Good evening, ma'am. I'm told you let rooms." Small bow of the head.
- **Voice descriptor in prompt:** a low, unhurried voice, faintly accented, old-world courtesy.
- **Axes:** 0.3 / 0.7 / mysterious.
- **QA:** transcribe vs D1; clip-qa context: one man; gloves stay on; case stays in hand; no
  entering the doorway this shot.

### S9 — INT: Her answer (dialogue)
- **Gen:** 6s → use ~4s. Refs: entry hall + `{{CORA_LOCK}}` (face visible now — lamplight).
- **Frame:** MCU Cora, lamp under-light, wary appraisal → resolve. **D2:** "Three dollars a
  week, with board. Supper's at six." Then, after a held beat, she steps back/aside to admit
  him — **she never says "come in"** (threshold lore stays unvoiced, see bible).
- **Voice descriptor:** soft North Carolina accent, guarded.
- **Axes:** 0.3 / 0.6 / wary-hopeful.
- **QA:** transcribe vs D2; clone-check (her step-back). Context: one woman; the man is NOT in
  this frame.

### S10 — INSERT: The boots / no mud
- **Gen:** 4s → use ~2.5s.
- **Frame:** CU threshold: rain-spattered porch boards, mud-flecked doorsill — and his black
  boots step across, **immaculate**. **VO V5.**
- **Axes:** 0.25 / 0.65 / unsettling.
- **Prompt draft:** Close-up at floor level on a boarding house threshold at night. Weathered
  porch boards wet with rain, mud-flecked at the sill. A pair of pristine black leather boots,
  entirely unmarked, steps unhurried across the threshold into warm lamplight. Sound: rain
  behind; two soft unhurried footfalls; a floorboard that does not creak. *(+ suffix)*
- **Edit note:** his silence canon starts here — in the mix his footfalls get NO foley (kill any
  native footsteps); the room tone continues undisturbed.
- **QA context:** exactly two boots/one person crossing; boots stay clean the entire shot; no
  mud appears on them; nothing else enters frame.

### S11 — INSERT: Gold on the table
- **Gen:** 6s → use ~3.5s. First-frame anchor: `env_entry_hall` side table + lamp.
- **Frame:** CU entry side table: his **gloved** hand places a neat stack of old gold coins
  beside her lamp; coins throw warm glints. (Gloved = no skin contact; coins on TABLE, never
  palm-to-palm — Ep 7 owns first touch.) **VO V6** + caption pop "Nobody pays in gold."
- **Axes:** 0.3 / 0.6 / mysterious.
- **QA context:** one gloved hand only; no bare skin; coin faces indistinct — **no legible
  dates or lettering**; the lamp does not move; no second hand.

### S12 — MCU: THE CONDITION ★★ (the swipe — protected shot)
- **Gen:** 8s → use ~7s. First-frame anchor: him in the entry hall, lamplit, hat-less, case set
  down; slow push-in.
- **Frame:** MCU Vascari, the warm hall light not quite warming him. **D3:** "One condition.
  No one enters my room. Not even you." *(beat — and softer, almost kind:)* "Especially you."
- **Axes:** 0.25 / 0.95 / ominous-intimate. The whole episode hangs on this read.
- **Voice descriptor:** as S8; the last two words quieter than the rest, not harder.
- **Prompt draft:** Slow push-in to a medium close-up. {{VASCARI_LOCK}} stands in a warm
  lamplit entry hall and speaks quietly, with unhurried old-world courtesy, to someone just off
  frame: "One condition. No one enters my room. Not even you." A pause. Softer: "Especially
  you." His expression is courteous and unreadable. Sound: rain muffled outside; a clock
  somewhere; his low, faintly accented voice. *(+ suffix)*
- **Protected retake:** budget carries ONE planned re-gen if the read/lip-sync misses — this is
  the exception written into the plan, not an autonomous reroll.
- **QA:** transcribe vs D3 (word-exact matters here); clip-qa context: one man; no one else in
  frame; background static; his face does not morph across the push (over-flag caution:
  held-shot face-morph flags get the human-watch benefit of the doubt).

### S13 — CU: Her eyes / smash out
- **Gen:** 6s → use ~3s. Refs: `{{CORA_LOCK}}` + entry hall.
- **Frame:** CU Cora; the lamp flame **shivers in a draft**; her eyes on him; she doesn't
  answer. Cut to black mid-breath. **VO V7 rides the cut into black.** Sting.
- **Axes:** 0.2 / 0.95 / unsettling.
- **QA context:** one woman; lamp flickers but does not go out; no one behind her.

---

## 4. Assembly plan

**Timeline (target ~67.0s):**

| Clip | In–Out (edit) | Audio on top |
|---|---|---|
| S0 (S7 excerpt) | 0.0–3.5 | V1; rain; theme tail-less (cold) |
| S1 + title stamp | 3.5–8.0 | title at 4.0–7.5 in the 55–65% band (locked treatment); theme enters low |
| S2 | 8.0–11.5 | V2 |
| S3 | 11.5–15.0 | V3 |
| S4 (still push) | 15.0–18.0 | V4; theme thins |
| S5 | 18.0–21.5 | knock SFX synced to flinch; theme OUT after knock |
| S6 | 21.5–25.0 | rain + footsteps (hers only) |
| S7 | 25.0–30.5 | hinge; rain swell; theme re-enters as lamplight finds him |
| S8 | 30.5–35.5 | D1 |
| S9 | 35.5–39.5 | D2 |
| S10 | 39.5–42.0 | V5; **no footfall foley for him** |
| S11 | 42.0–45.5 | V6 + coin-set SFX; caption pop |
| S12 | 45.5–62.5 → **use 7s → lands 45.5–52.5**; extend hold as cut | D3; **music fully out — rain + clock only** |
| S13 | 52.5–55.5 | lamp gutter SFX; V7 begins on her eyes |
| BLACK + sting | 55.5–57.0 | dread-hit sting; V7 finishes in black |
| End stamp | 57.0–58.5 | "Episode Two — House Rules"; quiet rain |

*(Table shows the shape; exact times re-anchored by SRC timestamps after gates + trims — audio
recomputed from shot+src anchors, not prior edit times. If total lands 60–70s anywhere, we're
on contract; do NOT pad.)*

- **Transitions:** hard cuts throughout (sustained-tension doctrine); the only black is the
  swipe-out. Concat via filter (never demuxer+copy), 24fps normalized, stereo everywhere.
- **Text passes (PIL sprites + overlay; no drawtext):**
  - Title stamp: "The Lodger" serif wordmark + "Episode One — The Stranger at Dusk", ivory,
    upper third, 4.0–7.5s.
  - Captions: every V/D line, ~58–62% height band, sentence case, ≤ ~30 chars/line, hard
    pop-in/out on speech timing; VO italic, dialogue regular. Safe zone: nothing in bottom 30%
    or hard right.
  - End stamp on black: "Episode Two — House Rules" + small wordmark.
- **Sound pass (after picture lock):** rain bed continuous (EL, ~80s loop); theme "Lamplight"
  per map above; stings; his-silence rule in the mix (S10, and forever); duck music −6 dB under
  speech; loudness target consistent with prior shorts.
- **Review deliverable:** master (native res) + `add-timestamp.py` debug copy + 720p share.cjs
  signed URL. No 4K until approved.

## 5. QA plan (gate summary)

- Pre-Veo: `frame-qa` every anchor vs canon refs; `anchor-drift` on S7's A/B pair.
- Post-gen, per clip: `normalize-clip` → `clip-qa --context="<per-shot QA context above>"` →
  `clone-check` on S2, S5, S6, S7, S9, S10 (motion) → `transcribe` on S8, S9, S12.
- All flags → keep / edit-around / reroll queue for Stephen (except S12's pre-authorized single
  retake). Full-res frames are the arbiter on any clone flag, never tool confidence.

## 6. Budget estimate

| Item | Est. |
|---|---|
| Veo: 76 gen-seconds (6+6+6+6+6+8+8+6+4+6+8+6) @ $0.10 × 1.3 overhead | $9.90 |
| S12 protected retake headroom (8s) | $1.04 |
| nano: ~22 images (casting 12 incl. regens + canon 7 + S7 anchors ~3) @ ~$0.15 | $3.30 |
| QA API: frame-qa ×6 ($0.24) + clip-qa ×12 ($0.14) + clone-check ×6 ($0.14) | ~$4.00 |
| ElevenLabs (VO ×7, SFX kit, 75s theme) | plan credits |
| **Total** | **≈ $18–19** (cap $22) |

## 7. Ep 2 handoff obligations (end-state this episode must leave true)

- Coins on the entry table; his case in the entry; **trunk has NOT arrived** (Ep 2 beat).
- No room chosen yet — the sunrise-facing refusal is Ep 2's beat.
- Her lamp lit; rain ongoing; door closed behind him is fine.
- Ep 2 opens paying this swipe within 10s (e.g., her only possible answer: "…This way." — and
  up the stairs we go). Stairwell plate gets built in THIS episode's canon batch for that reason.
- No skin contact occurred (gloves stayed on). His footsteps made no sound.

## 8. Decisions to confirm with Stephen (pre-build)

1. **Lead faces** — **RESOLVED 2026-08-19**: Vascari = C (elegant predator), Cora = B (fine
   guarded), house = A2-summer. Canon filed in `../canon/`; locks in `../canon/locks.md`.
2. **Names & era** — **RESOLVED 2026-08-19**: Cora May confirmed; Deputy Holloway confirmed as
   the *same* Holloway (shared universe, see series README); town Gilead, NC (working); **era
   relocked to summer 1934, eastern NC** at Stephen's correction (1898 was my misread).
3. **Her VO voice** — I'll audition 2–3 EL voices at build and bring picks.
4. **Caption scope** — recommended: caption ALL spoken lines (genre standard, sound-off
   viewing); alternative: key lines only.
5. **Title treatment** — **RESOLVED 2026-08-19**: Hoefler Text, ivory, soft shadow, 55–65%
   height band over dark foreground (Shorts-UI-safe). Ref `../canon/title_treatment_ref.png`.
6. **Budget cap** $22/ep and the S12 protected-retake exception.
7. **Runtime** ~67s (short end of 60–90) — verticals reward tight; confirm you're happy landing
   Ep 1 under 70s.

## 9. Build-day runbook (once §8 clears)

1. Scaffold `data/workspace/lodger-ep01/{refs,frames,clips,final,scratch}`.
2. nano canon batch (spaced ~10s) → **STOP: Stephen approves faces/plate/title mock.**
3. Extract + file locked descriptions (`canon/locks.md`).
4. Build S7 book-end anchors + S4 chair still → `frame-qa` all, `anchor-drift` S7 pair.
5. EL: audition + record V1–V7; generate knock/coin/lamp/rain SFX + sting; generate theme.
6. Veo: submit S1–S13 (quality, 9:16, audio ON), one gen per shot, via MCP submit → poll.
7. Gate every clip (§5); build the keep/edit/reroll queue.
8. Assemble picture (concat filter, 24fps); caption + title passes; review cut v1.
9. Sound pass; mix; master + debug copy + 720p share link.
10. `costlog.py` entries per spend; update this doc's status + episode index in series README.
