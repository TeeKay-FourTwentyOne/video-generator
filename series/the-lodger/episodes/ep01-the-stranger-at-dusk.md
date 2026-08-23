# THE LODGER — Episode 1: "The Stranger at Dusk"
### Shooting script v2.1 (RESTRUCTURE) — status: **v2 BUILT 2026-08-22 — AWAITING STEPHEN'S WATCH (GATE 2).**
Draft at `data/workspace/lodger-ep01/final/ep01_v2_review.mp4` — **60.75s**, 1080×1920, −14.5 LUFS,
captions + title + end card + full mix. Decisions queued: `data/workspace/lodger-ep01/flag-queue-v2.md`.
v2 increment **$8.66** (Veo $4.68 / 6 gens, nano 13, QA $2.03) vs the $8–9 estimate; ep cumulative ≈$28.96.

**Built as written, with these build-time calls:** boarder faces glance-approved before any Veo
spend (step-1 STOP cleared); the **common room is the parlor widened**, not a new set, so father's
empty armchair sits in the same room as the laughing table and S6/S7/S9 share one geography;
**S13 used the budgeted contingency gen** (both reuse candidates failed inspection — see
flag queue §3), which also retires v1's puff-sleeve and hurricane-lantern flags; S2 and S4 are
trimmed shorter than planned to dodge a frame-exit and a true background break. **1080p probe:
works** — S2 returned true 1080×1920; `gen-runner` now takes a per-shot `resolution` override.
Two decisions need Stephen: Veo wrote *legible dialogue* where the script wanted walla (kept
uncaptioned as background), and S5's scripted hand-pat did not land.

**Why v2:** Stephen's GATE 2 notes on draft v1 (built 2026-08-20, 63.5s, in
`data/workspace/lodger-ep01/final/`): too much tell, too little show. Directives:
1. Extend the introduction of Cora and the boarding house — with **liveliness**: a common room
   with people talking.
2. Show Cora **doing the books** more.
3. Vascari arrives at the **very end** — the episode now closes on "Good evening, ma'am.
   I'm told you let rooms."

That moves the entire transaction — her terms, the no-mud boots, the gold, "One condition…
Especially you." — into **Ep 2 "House Rules"**, whose spike/button is therefore **already shot**
(v1's S9–S13, dialogue word-perfect). See §7 for the beat-sheet ripple, which needs Stephen's
sign-off.

v1.4 (the built draft's script) lives in git history; draft-v1 clips remain in
`data/workspace/lodger-ep01/clips/` under their OLD shot names — the reuse map in §3 translates.

| Spec | Value |
|---|---|
| Format | 9:16, 1080×1920, 24fps, Veo 3.1 Quality, native audio ON |
| Target runtime | **~62–68s** (contract 60–90; extended Friction is the point of v2) |
| Veo gens | **5 new** (S2, S3, S4, S5, S7) + 7 reused v1 clips + 1 reused still + contingency S13 |
| Incremental budget | est. **$8–9** Veo/nano/QA (see §6) + VO regen on EL credits |
| Workspace | `data/workspace/lodger-ep01/` (continue; new clips use NEW shot names) |
| Emotional turn (one only) | *The last ordinary evening of her life — ended by a knock.* |

**Episode skeleton (Hook → Friction → Spike → Button):**

| Unit | Time (approx) | Content |
|---|---|---|
| HOOK | 0–3.5 | Door opens on his face in the rain (excerpt of S11) + V1 |
| — title | 3.5–8.0 | Series stamp over house exterior |
| FRICTION A — the living house | 8.0–22.5 | Common room warm and full: checkers, chatter, Cora pouring coffee; the one chair nobody sits in |
| FRICTION B — the books | 22.5–38.5 | A boarder pays what he can; ledger; tin box that counts short; father's chair |
| SPIKE | 38.5–51 | The knock → the lamp down the hall → the reveal |
| BUTTON / SWIPE | 51–59 | **D1: "Good evening, ma'am. I'm told you let rooms."** Her held look. Black + sting. |
| End stamp | 59–61 | "Episode Two — House Rules" |

---

## 1. The script

**VO = Cora, retrospective, close-mic, confiding — now recorded with her LOCKED cloned voice
(`qgVHCjozdBwKCEAWjZCa`, EL clone of her Veo-native read, approved 2026-08-22). VO is recorded
AFTER picture lock, per the standing deferral. All spoken text gets burned captions (dialogue
regular, VO italic). Background walla is NOT captioned.**

v2 deliberately slims VO from seven lines to three — the pictures carry what v1 narrated.

| # | Speaker | Line | Where |
|---|---|---|---|
| V1 | CORA (VO) | "Papa always said nothing good knocks after dark." | Hook (S0) |
| B1 | MR. PRUITT (bg) | "King me." *(Odom groans; the table laughs)* | S3 |
| V2 | CORA (VO) | "Folks paid me what they could. The bank didn't take eggs." | S5→S6 |
| V3 | CORA (VO) | "Papa's chair. Right where he left it." | S8 |
| D1 | VASCARI | "Good evening, ma'am. I'm told you let rooms." | S12 (v1's S8 clip) |

Notes on the writing:
- V1 keeps the series' narrator frame and re-arms every loop. Unchanged from v1.
- **Cut from v1:** "Six rooms. Five of them empty." (contradicts the lively house — see canon
  change, §2), "However I worked the figures…" (the tin box shows it), and V5–V7 (they belong
  to Ep 2's material now).
- V2 is the one interpretive line Friction gets — it rides the payment insert into the ledger,
  wry not bitter. The eggs are ON SCREEN in S5 before the line lands.
- V3 keeps the father plant (*left it*, never *lost him* — alive, returns Ep 14). **CONFIRMED
  KEEP (Stephen, 2026-08-22).**
- B1 is one two-word background line so the room genuinely *talks* (Stephen's note). Two words,
  soft-focus old man, minimal lip-sync exposure. **CONFIRMED KEEP (Stephen, 2026-08-22).**
  Fallback if the read garbles: keep the laugh, drop to indistinct walla.
- D1 is now the SWIPE. The clip is already shot and word-perfect (v1 S8 retake). **No
  end-of-episode VO — CONFIRMED (Stephen, 2026-08-22):** his line and her face are the button.

---

## 2. Canon changes & new canon assets

### Canon change: the house has boarders (supersedes v1's empty-house read)
The Albright house lets **six rooms; three are occupied** — the house is half-full: alive in the
evenings, and still failing. This is the stronger Depression truth (a full table and an empty
cashbox: boarders pay short, in scrip, in kind, and she can't turn them out), it makes her warmth
*visible* instead of narrated, and it's more consistent with the later beats (Ep 14 "in front of
the boarders", Ep 20 "boarders whispering"). Three rooms vacant also preserves Ep 2's beat — he
must be able to *choose* the room facing away from the sunrise.

**The boarders (new light canon — nano refs + Stephen glance-approval before the Veo spend, since
they recur at least Eps 14 & 20):**

| Boarder | Working sketch |
|---|---|
| **Mr. Pruitt** | late 60s, retired railroad man, white mustache, suspenders, checkers shark |
| **Mr. Odom** | 60s, heavyset, bald, good-humored, loses at checkers nightly |
| **Miss Vann** | 40s, schoolteacher, wire spectacles, grades papers by lamplight |

Cap any single frame at 4–5 people total (body-pile RAI caution). Nobody else in Arc 1's Ep 1.

### New nano assets (all before any Veo spend)
All to `series/the-lodger/canon/` (boarder sheets) or workspace `refs/` (anchors). Space calls
~10s; no text in any image; no "photograph" wording; face-visible rule applies to anyone whose
face shows.

| Asset | File | Notes |
|---|---|---|
| Boarder trio sheet(s) | `char_boarders_{pruitt,odom,vann}.png` | one seated-in-costume ref each; common-room dressing behind them |
| Common room plate (evening, lamplit) | `env_common_room.png` | long table cleared to coffee cups, checkerboard at one end, hearth COLD (summer), **father's leather armchair empty beside it**, brass chimney lamps (canon lamp — no hurricane lanterns) |
| S2/S3/S4/S5/S7 first-frame anchors | workspace `refs/` | composed per shot below; **Cora in canon collared shirt-dress + apron** (guard against v1's S2/S13 puff-sleeve drift); frame-qa all vs canon |

**Existing canon reused as-is:** both lead sheets, `env_house_ext_dusk_rain`, `env_entry_hall`,
`env_parlor`, `still_fathers_chair`, title treatment.

**Standard prompt suffix (every Veo gen):** unchanged from series-config (`era_suffix`).

---

## 3. Shot list

**Reuse map (v1 clip name → v2 slot):**

| v1 clip | v2 slot | Disposition |
|---|---|---|
| S1_RAW | **S1** | reuse — house ext + title bed |
| S2_NORM (alone at table) | — | **dropped** (contradicts lively house; had wardrobe drift) |
| S3_RAW (ledger CU) | **S6** | reuse — tail ledger-shift trim per flag queue |
| S4 chair still | **S8** | reuse — zero-cost programmatic push |
| S5_RAW (knock) | **S9** | reuse — trims/knock-SFX plan per flag queue |
| S6_RAW retake (hall walk) | **S10** | reuse — use [0.6, 4.6] |
| S7_NORM (reveal) | **S11** + S0 hook excerpt | reuse |
| S8_NORM retake (his ask) | **S12** — THE BUTTON | reuse — word-perfect D1; case-hand cosmetic stands |
| S9_NORM (her terms D2) | → **Ep 2** | held (possible S13 look source, see S13) |
| S10 (boots), S11 (coins), S12 (condition), S13 (her eyes) | → **Ep 2** | held — Ep 2's spike/button, already gated |

Per clip-acceptance-gate on all NEW gens: `normalize-clip` → `clip-qa` with explicit
should-NOT-be-present context → `clone-check` on every motion shot (all five new shots are
multi-person or subject-motion) → `transcribe` on S3 (B1 line). Flags → keep / edit-around /
reroll queue for Stephen; no auto-reroll.

---

### S0 — HOOK (no gen — excerpt of S11/v1-S7)
- **Edit:** ~2.5–3.5s of the door-swing/reveal, cut on his eyes. VO V1 over it. Smash to S1 + title.

### S1 — EXT: The house in the rain *(REUSE v1 S1)*
- Use ~4.5s under the title stamp. Amber window now earns its warmth — the common room is lit.

### S2 — INT: The common room, alive ★ new
- **Gen:** 8s → use ~6s. First-frame anchor composed from `env_common_room` + boarder refs +
  `{{CORA_LOCK}}`.
- **Frame:** From the hall doorway, depth-stacked tall: supper cleared to coffee, Pruitt and Odom
  over the checkerboard mid-game, Miss Vann with her papers, Cora crossing through with the
  coffee pot refilling cups. Warm overlapping talk, a small laugh. **The leather armchair by the
  cold hearth sits empty — nobody so much as drapes a coat on it.**
- **Axes:** energy 0.45 / tension 0.1 / mood: intimate-warm. The series' one truly warm interior
  — everything after erodes it.
- **Prompt draft:** From a doorway, a warm lamplit boarding house common room in the evening. An
  elderly mustached man and a heavyset bald man play checkers at the end of a long cleared table;
  a middle-aged woman in wire spectacles marks papers by lamplight. {{CORA_LOCK}} moves through
  pouring coffee from an enamel pot into their cups, easy and practiced. A worn leather armchair
  beside the cold hearth sits empty. Cheerful indistinct conversation, a soft laugh, rain on the
  windows. Sound: quiet talk, cups, checkers clicking, rain. *(+ suffix)*
- **QA context (not-present):** exactly four people (one young woman standing, three seated
  boarders); no one sits in or touches the leather armchair; no fire in the hearth; brass chimney
  lamps only — no hurricane lanterns; no food on the table; nothing legible on the papers.
- **Series stock:** file best take — the living common room recurs (Eps 4, 6, 14, 20).

### S3 — INSERT: Checkers — "King me." new
- **Gen:** 6s → use ~4s.
- **Frame:** CU across the checkerboard: Pruitt's weathered hand double-jumps and lands, taps the
  board. **B1: "King me."** Odom's groan off-mic; the table laughs softly; Cora's laugh joins
  from off-frame.
- **Axes:** 0.4 / 0.1 / whimsical-warm.
- **QA:** transcribe vs B1 (fallback: mute line, keep laugh, drop caption); clip-qa context:
  two elderly men's hands/faces at a checkerboard; checkers move legally-ish but board detail
  soft; no extra hands; no text.

### S4 — INT: Cora pouring, close new
- **Gen:** 6s → use ~4s. Anchor: `{{CORA_LOCK}}` (canon wardrobe enforced) + common room bokeh.
- **Frame:** MCU Cora mid-pour, catching the joke and smiling down at the table — the series
  banks its first real warmth on her face here. Boarders soft-focus beyond.
- **Axes:** 0.35 / 0.1 / intimate. No VO — let her smile do it.
- **QA:** clone-check (pour + turn). Context: one woman sharp in frame; background figures stay
  seated and stay THREE; coffee pot in her hands the whole shot; canon dress + apron.

### S5 — INSERT: Paying what they can new
- **Gen:** 6s → use ~4.5s.
- **Frame:** CU on the table by the door or desk: Pruitt counts out a few small coins — short —
  then sets a folded slip of paper and a small basket of brown eggs beside them. Cora's hands
  take the coins; a beat; her hand pats his. No shame in it, on either side. **VO V2 begins over
  her hands and rides into S6.**
- **Axes:** 0.3 / 0.3 / bittersweet.
- **QA context:** two people's hands only (one elderly man, one young woman); coins few and
  small, NOT gold, faces indistinct; the folded slip stays folded — **no legible writing
  anywhere**; eggs stay eggs (count stable).
- **Note:** skin contact fine — the no-touch rule is Cora×Vascari only.

### S6 — INT: The ledger *(REUSE v1 S3)*
- Use ~3.5s (tail trimmed per flag queue). Her finger down the column, pencil taps. **VO V2
  finishes here.** The house has gone quiet around her — boarders retiring upstairs (floorboards,
  a muffled goodnight, in the mix). Aloneness *shown* by subtraction, not narrated.

### S7 — INT: The tin box new
- **Gen:** 6s → use ~4s. Anchor: parlor desk plate + `{{CORA_LOCK}}`.
- **Frame:** MCU at the desk, lamplight: she counts the evening's take into a dented tin cash
  box — coins, the folded IOU slip dropped in on top with the faintest exhale — glances at the
  open ledger, and closes the box gently. The click of the latch is the beat.
- **Axes:** 0.2 / 0.45 / tense-quiet. No VO — the arithmetic is visible.
- **QA context:** one woman; one tin box; coin count small and non-gold; no legible figures in
  the ledger; lamp is the brass chimney lamp and does not move.

### S8 — INT: Father's chair *(REUSE v1 S4 still + push — zero Veo)*
- 3.0s push-in on `still_fathers_chair`. **VO V3** (or silent — Stephen's call, §8). Now it
  reads as the answer to S2: the one empty seat in a full room.

### S9 — INT: The knock *(REUSE v1 S5)*
- ~3.5s: she's writing at the desk; **three deliberate knocks**; pencil stops; only her eyes
  lift. EL knock triple synced to her flinch (src ≈2.5s) per flag queue; native knock ducked.
- Theme OUT after the knock. From here v1's spike runs unchanged.

### S10 — INT: The hall, lamp in hand *(REUSE v1 S6 retake)*
- Use [0.6, 4.6]: she carries the lamp toward the closed front door, staircase dark beside her.

### S11 — INT→EXT: THE REVEAL ★ *(REUSE v1 S7)*
- ~5.5s: over her shoulder the door swings open — Vascari motionless on the rain-lashed porch,
  case in gloved hand, lamplight finding his face. Beat of rain before S12.

### S12 — EXT porch: THE BUTTON ★★ *(REUSE v1 S8 retake)*
- ~5.5s: courteous stillness, the small bow. **D1: "Good evening, ma'am. I'm told you let
  rooms."** Word-perfect in the can. This is now the swipe line — let it land in near-silence
  (rain only; no music).

### S13 — CU: Her held look / smash out
- ~2.5s: her face taking him in — wary, and not only wary. Cut to black mid-breath. Sting.
- **Source, in order of preference (decide at reshoot phase, not now):**
  1. Head of v1 S9 (her pre-line appraisal, before D2 audio) — trim to the silent look;
  2. v1 S13 eyes-CU (carries the puff-sleeve/lantern cosmetic flags);
  3. New 4s gen (contingency in budget).

---

## 4. Assembly plan

**Timeline (target ~61–64s; shape only — re-anchor by SRC after gates/trims, audio recomputed
from shot+src anchors):**

| Clip | In–Out | Audio on top |
|---|---|---|
| S0 hook (S11 excerpt) | 0.0–3.5 | V1; rain; cold open |
| S1 + title | 3.5–8.0 | title 4.0–7.5 (locked treatment); theme enters low |
| S2 common room | 8.0–14.0 | walla + cups + checkers; theme warm |
| S3 "King me." | 14.0–18.0 | B1 + laughter |
| S4 Cora pouring | 18.0–22.5 | walla continues under |
| S5 paying what they can | 22.5–27.0 | V2 begins; walla thins |
| S6 ledger | 27.0–30.5 | V2 ends; goodnights/floorboards above; theme thins |
| S7 tin box | 30.5–34.5 | latch click; near-quiet |
| S8 chair still | 34.5–37.5 | V3; theme barely there |
| S9 knock | 37.5–41.0 | EL knock triple synced to flinch; **theme OUT** |
| S10 hall | 41.0–44.5 | rain + her footsteps only |
| S11 reveal | 44.5–50.0 | hinge; rain swell |
| S12 D1 — the button | 50.0–55.5 | D1; rain only, no music |
| S13 her look | 55.5–58.0 | lamp/rain; breath |
| BLACK + sting | 58.0–59.5 | dread sting |
| End stamp | 59.5–61.0 | "Episode Two — House Rules"; quiet rain |

- **Transitions:** hard cuts throughout; only black is the swipe-out. Concat filter, 24fps, stereo.
- **Emotional shape:** Friction A is the warmest the series ever gets; the sound design cools in
  stages (walla → floorboards → latch → rain alone) so the knock arrives in true quiet.
- **Text passes:** title stamp per locked treatment; captions V1/B1/V2/V3/D1 only (walla never
  captioned); end stamp on black. Safe zone rules stand.
- **Sound pass (after picture lock):** rain bed continuous; common-room bed (EL: low period
  walla, cups, checker clicks, laughter — replaces/ducks native chatter if Veo's walla reads
  wrong); theme per map; sting at black. **VO recorded fresh with Cora's locked clone
  (`qgVHCjozdBwKCEAWjZCa`) — the sarah takes are dead.** His-silence rule untouched (he doesn't
  move this episode; rule resumes with Ep 2's boots shot).
- **Review deliverable:** native-res master + debug copy + 720p signed URL. No 4K before approval.

## 5. QA plan

- Pre-Veo: `frame-qa` every new anchor vs canon (Cora wardrobe explicitly checked — this is
  where v1 drifted); boarder refs glance-approved by Stephen before spend.
- Post-gen per new clip: normalize → clip-qa (contexts above) → clone-check (all five new shots)
  → transcribe S3.
- Multi-person frames (S2–S5) are our first for this series: expect clone-check noise around
  the seated trio; **full-res frames are the arbiter**, never tool confidence.
- Resolution probe: submit ONE new gen with `resolution: "1080p"` (S2, the most detail-hungry);
  if returned at cost parity, set in series-config for all future gens (flag-queue action item).

## 6. Budget (incremental, v2 work only)

| Item | Est. |
|---|---|
| Veo: 32 gen-s (8+6+6+6+6) @ $0.10 × 1.3 overhead | $4.16 |
| S13 contingency gen (4s) | $0.52 |
| nano: boarder sheet ×3 + common-room plate + anchors ×5 @ ~$0.15 | $1.35 |
| QA API: frame-qa ×6 + clip-qa ×5 + clone-check ×5 + transcribe | ~$2.60 |
| ElevenLabs (VO ×3 regen, walla/laugh SFX) | plan credits |
| **Total incremental** | **≈ $8.60** |

Ep 1 cumulative ≈ $20.3 (v1) + $8.6 ≈ **$29** — over the $22/ep norm, BUT Ep 2 inherits five
gated, word-perfect clips (S9–S13 v1 ≈ $6–7 of paid Veo) and both voice locks. Amortized across
Eps 1–2 we're on budget. Voice-harvest sessions tracked separately.

## 7. Beat-sheet ripple — **DEFERRED (Stephen, 2026-08-22)**

**Decision: build Ep 1 v2 now; `arc-1-beats.md` stays UNTOUCHED until Stephen has seen the new
cut.** Do not edit the beat sheet or renumber episodes in any doc during the build session. The
proposal below is preserved for that later decision (renumber-to-21 vs compress-to-hold-20):

- **Ep 2 "House Rules" (revised):** opens paying the swipe inside 10s — her terms ("Three
  dollars a week, with board. Supper's at six."), she steps back (never says "come in"), the
  no-mud boots, gold on the table, and the condition. *Swipe:* "One condition. No one enters my
  room. Not even you. — Especially you." **Spike + button already shot and gated** (v1 S9–S13,
  incl. the S12 protected retake). New material needed is connective tissue only — Ep 2 gets
  cheap. The title fits better than ever (her house rules; then his).
- **Ep 3 (new) "The Trunk":** old Ep 2 wholesale — she shows him up, the sunrise-facing refusal,
  the trunk and four straining men. *Swipe:* one hand, silent, through the banister rails.
- **Eps 4+ shift by one** (old Ep 3 "Daylight" → new Ep 4, etc.); arc becomes 21 episodes —
  inside the 20–40 intent, and the paywall cliffhanger (old Ep 10 storm) lands at new Ep 11.
  **Alternative** if Stephen wants to hold 20: compress old Eps 3–4 (deputy's peaches + the
  untouched tray both feed the triangle) into one episode downstream.

**Ep 1→2 handoff obligations (v2):** he is OUTSIDE, on the porch, never crossed the threshold;
no terms spoken, no gold yet, no condition yet; case in gloved hand; her lamp lit; rain ongoing;
boarders upstairs asleep (they must NOT witness the arrival); tin box closed on the desk;
coins/IOU/eggs from S5 are Ep 2 set-dressing continuity if the desk reappears.

## 8. Decisions — RESOLVED 2026-08-22 (Stephen)

| Decision | Call |
|---|---|
| Beat-sheet ripple | **Deferred** — build now, beats untouched until he sees the cut (§7) |
| B1 "King me." | **Keep** (fallback: mute line, keep laugh, no caption) |
| V3 chair VO | **Keep** the line |
| End of episode | **No closing VO** — his line, her look, black + sting |

**Remaining build-day gates (not pre-resolved):**
1. **Boarder faces** — nano sheets → Stephen glance-approves BEFORE any Veo spend (runbook step
   1 STOP). Names Pruitt / Odom / Miss Vann are working names; boarders are asleep/absent for
   every Vascari night-beat until the beats say otherwise.
2. **S13 her-look source** — preference order in §3 S13, decided when cutting the button.
3. **Budget:** ≈$8.60 incremental (Ep 1 cumulative ≈$29, recouped by Ep 2's inherited shots);
   confirm session ceiling at build kickoff.
4. **Runtime:** ~61–64s target; S2/S3/S4 carry ~5s headroom if the common room deserves more
   air — stretching toward ~70s needs no new spend.

## 9. Build-day runbook (CLEARED TO RUN — fresh session starts here)

1. nano: boarder sheets + common-room plate → **STOP: Stephen glance-approves boarders.**
2. Compose + frame-qa anchors for S2/S3/S4/S5/S7 (wardrobe check explicit).
3. Veo: submit the 5 new gens (S2 with the 1080p probe), one gen per shot → full gate per §5.
4. Flag queue → Stephen's keep/edit/reroll pass.
5. Re-cut picture per §4 (reused clips keep their v1 trims where noted).
6. EL: record V1/V2/V3 with Cora's locked clone; walla/laugh bed; knock kit reused.
7. audio-anchor pipeline: --anchors → --stems → --mute-base → --mix; text passes.
8. Master + debug + 720p link; costlog per spend; update README index + this doc's status.
