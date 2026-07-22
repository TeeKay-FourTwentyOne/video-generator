# THE CHURCH GRIM — brief (v1 build 2026-07-20, overnight autonomous)

**Logline:** The first soul buried in a churchyard must stand watch over all the rest, forever — so the old parishes buried a black dog first. One churchyard, one ink-black dog, six hundred years. The congregation dwindles to one old woman; she dies; the guardian of a thousand departed souls finally gets one that stays.

**Format:** 9:16 vertical · target ~75–80s · v1 at 1080×1920 (NO 4K upscale per user) · $50 cap, est. $20–25.

**Register (user-set):** Arthur Rackham pen-and-ink + muted watercolour wash, in video. First full illustration-register piece for the channel. The grim is literally a creature of ink — subject rhymes with medium.

**Audio rules:** single native-Veo dialogue line (S10b: "There you are. Good dog."). ElevenLabs for VO (aged English female storyteller, ≤80 words) + bell/wind SFX + sparse late-entering music. ElevenLabs only, no Suno.

## Style block (every nano prompt)
> Pen-and-ink illustration with muted watercolour wash in the manner of Arthur Rackham: sinuous fine ink linework, dense crosshatched shadows, aged ivory paper tone showing through, muted sepia-umber-moss palette with grey-blue night washes and one dull gold accent, gnarled organic forms, delicate silhouetted branch filigree. ABSOLUTELY NO text, no lettering, no caption, no title, no border, no frame, no signature, no watermark.

**Dog phrase (verbatim everywhere):** "a large rough-coated ink-black hound with pale grey eyes"
**Woman phrase:** "a small elderly woman in a long wool coat and headscarf, kind deeply-lined face" — face-visible ref REQUIRED (S10b shows her face).

## Master-plate accretion (living-painting technique → narrative time)
Vertical stack: lychgate (bottom) → stone path center → leaning slates + ancient hollow yew left → Norman church w/ squat tower (top) → sky. Dog's mound beside path, mid-frame.
Era plates chained ADD-ONLY: E1 1400s (sparse: fresh mound, 2–3 rough stones) → E2 1600s (+stones, lean) → E3 1800s (+iron rails, ivy, denser) → E4 1930s (+telegraph wires, more lean) → E5 now (+weeds high, boarded door, broken pane). Per-shot light/weather = redraw from era plate w/ explicit preserve language (layout/stones/yew/church/dog mound). frame-qa each vs its era plate.

## Shot list (durations 4/6/8 only; all book-ended unless noted)
| # | Era | Len | Content | Audio |
|---|-----|-----|---------|-------|
| S1 | 1400s night | 8 | Torch procession (≤4 figures, backs) recedes out lychgate; fresh mound; dog sits atop, still | VO1; torches, wind |
| S2 | 1600s rain | 6 | Funeral knot (≤4, ruffs) under yew below; DOG ON CHURCH ROOF RIDGE above; rain streaks | rain, passing-bell |
| S3 | 1700s night | 8 | TENSION PEAK. From outside gate: crooked-tall cloaked traveller under lychgate arch (face hidden), dog mid-path, hackles; one low growl; figure withdraws | growl native; near-silence |
| S4 | 1800s dusk | 6 | Victorian procession w/ umbrellas glides behind wall; crows lift from yew; dog unmoved | VO2; crows |
| S5 | 1930s grey | 6 | Motor hearse roof glimpsed past wall; telegraph wires sway; dog's ear flicks | distant motor |
| S6 | now, cold | 6 | Decay: boarded door, broken pane, high weeds; jackdaws burst from tower; dog on mound | jackdaws |
| S7 | autumn warm | 8 | Old woman tends a grave, fresh flowers in jar, wipes stone, rises, small nod toward mound; dog watches | rooks, jar clink |
| S8 | late autumn | 6 | Same framing EMPTY; dead flowers in jar; leaves blow; dog stands AT GATE looking down lane | VO3; wind. MUSIC IN |
| S9 | dusk | 6 | Fresh unmarked mound; dog walks to it, lies down beside it, head on paws | wind. clone-check |
| S10a | night moon | 6 | She stands mid-path near yew, hale; dog rises, RUNS up path away-from-camera toward her | patter of paws. clone-check! |
| S10b | night close | 8 | She kneels, takes dog's head in both hands: **"There you are. Good dog."** | NATIVE VEO DIALOGUE |
| S11 | night wide | 8 | Master wide: the two walk up path together into yew-dark mist; hold empty a beat | VO4; single warm bell |

Era turns punctuated by single bell tolls (EL SFX) at cuts.

## VO draft (trim at record; target ≤80 wds)
- VO1: "The first soul buried in a churchyard must stand watch over all the rest, forever. So the old parishes buried a dog first — black as ink — that no man or woman would ever bear the watch."
- VO2: "Six hundred years, it kept the gate."
- VO3: "It saw a thousand souls to elsewhere. None of them ever stayed. Staying was the dog's work."
- VO4: "She was the last. And the last may choose."

## Risks & mitigations
1. **Veo holds ink register?** THE unknown. Probe = real shot on Quality, book-ended both ends. Gentle line-boil acceptable (reads as hand-drawn animation). If drift → build `tools/style-hold.py` gate; if collapse → stills+parallax for still beats, Veo only for dog motion.
2. Vintage descriptors bake text into nano → NO-TEXT suppressor in every prompt.
3. Crowd RAI → cap mourners at 4, no children anywhere, stranger's face hidden.
4. Dialogue-in-ink uncanny → S10b near-static; fallback = play line small-in-frame on S11 wide.
5. Fast dog run (S10a) → clone-check mandatory; receding run reduces limb-splay.

## Gate (per clip-acceptance-gate)
frame-qa + anchor-drift pre-Veo on every pair · normalize/analyze + clip-qa (autonomous ⇒ mandatory, with explicit NOT-present context) + clone-check on all dog-motion shots post-gen · keep / edit-around / reroll ladder, decisions logged in workspace DECISIONS.md.

## Status — v1 BUILT overnight 2026-07-20→21, pending user review
Final: `data/workspace/church-grim/final/church_grim_v1.mp4` — 720×1280, 85.96s, -15.8 LUFS, ~34.5 MB. Debug-timestamp copy alongside. 7-day review link in DECISIONS.md / wrap message. NO upscale yet (per instruction).

### Final cut (13 segments)
| t | seg | beat |
|---|-----|------|
| 0.00 | S1 8.0 | 1400s night — last mourner tears himself away; dog stays (VO1 in) |
| 8.00 | S1b 6.0 | morning after — bare yard, dog turns to face us (VO1 tail) |
| 14.02 | S2 6.0 | 1600s rain funeral — grim watches from the roof ridge [bell] |
| 20.03 | S3 4.8 | night — crooked thing among the stones; growl; it withdraws (trimmed from 8) |
| 24.83 | S4 6.0 | 1800s dusk — umbrella procession passes the unchanged dog [bell], VO2 |
| 30.85 | S6 6.0 | now — boarded gold door, jackdaws burst [bell] |
| 36.86 | S7 8.0 | warm autumn — the one tended plot; she rises, nods toward the mound |
| 44.86 | S8 6.0 | the absence — dead flowers, empty mound, wind (VO3; MUSIC in) |
| 50.88 | S9 8.0 | dusk — fresh unmarked mound; dog lies down beside it |
| 58.88 | S10 8.0 | moonlit — she's on the path; dog rises and goes to her, head into hands |
| 66.88 | S10b 8.0 | kneel, face to face — **"There you are. Good dog."** (native Veo, verified) |
| 74.88 | S11 8.0 | the two settle on the dog's mound, head across her lap (VO4, warm bell) |
| 82.88 | endcard 3.1 | parchment: THE CHURCH GRIM · a folk tale |

### Build facts
- All Veo Quality (veo-3.1-prod) at **720p — anchors bind ONLY at 720p** (1080p demotes them to loose reference; discovered on the first probe, verified A/B). Rule + the interpolation-unreachable corollary (big A→B subject moves → first-frame-only + cut-covered end) recorded in memory.
- nano GA rename: `gemini-3-pro-image` (preview alias died); tool patched.
- 15 Veo submissions (incl. 1080p probe + S1 v1 + S10 rebind) = 108 Veo-sec ≈ **$10.80**; 35 nano ≈ **$5.25**; QA (Opus) ≈ **$4–5**; EL within quota. **Total ≈ $21 of $50.**
- Gate ran on every clip (frame-qa-equivalent anchor checks pre; clip-qa + clone-check post). Zero photoreal drift all night — the ink register is Veo-stable with book-ends. clip-qa over-fires on ink (boil/paint-pump read as morph); verify strips before trusting REGENERATE recs.
- Cuts: S5 (motor hearse) cut for pace; S10a run recast as slow approach (grim never hurries); S8 recast as S7-framing emptied.

### v2 / upscale-pass candidates (watch on review)
1. S7 t≈3.3–3.7: transient dark blob in her hand (trowel ghost) — frame-surgery if it pops at speed.
2. S4: iron-rail paint-pump mid-clip; S8: soft reframe in first ~1.5s; S2: slight framing breathe.
3. Her coat reads tan in moonlight shots vs dark wool in S7 (nano drift) — regrade or accept as lighting.
4. S10 breath-puff at ~6s — judged a feature (warm breath = she's really there); confirm at speed.
5. 4K upscale + loudness re-master on approval.

### v2 — silent-film intertitles (user-directed, 2026-07-21)
`final/church_grim_v2.mp4` — 720×1280, 99.92s, -15.9 LUFS. VO replaced by 5 nano-generated Rackham intertitle cards (indigo aged card, thorned yew/ivy border, ivory hand-lettering; text trimmed 66→54 words) + matching end title card; cards carry film grain + geq flicker (cards only). Her spoken line kept native — silence breaks once, at the climax. All cards letter-checked (one reroll: nano lettered the prompt word "EXACTLY:" onto card 3). Dialogue + timeline verified. v1 preserved alongside.

### v3 — final refinements (user notes, 2026-07-21)
`final/church_grim_v3.mp4` — 98.71s, -15.9 LUFS. (a) S1 trimmed to [0,5.4]: cut before the mourner's backward descent, ends on his held look. (b) S3 regenerated per note: dog erupts (rears, snaps, three ringing barks — native audio), the crooked figure whirls in a tatter-storm and is driven down the steps into the mist; first-frame-only submit (anchor-pair-unreachable lesson); clone-check caught a REAL second cloaked figure at t=6.35 in the mist tail (conf 0.95) — trimmed at 6.2. v3 assembled by measured-durations generator.

### v4 — PICTURE LOCK + 4K (user frame trims, 2026-07-21)
User cuts off v3 debug: S1→4.55s, S1b→4.08s, S2→2.94s, S3→2.22s (bark-lunge-CUT); S10 approach shot removed (S9 dusk → S10b night kneel ellipsis). 80.96s, -15.8 LUFS. **4K MASTER: `final/church_grim_v4_4k.mp4`** — 2160×3840, 80.93s, 230MB, realesr-animevideov3 3×. (Upscale task was killed mid-run; salvaged all 1943 AI frames from the orphaned tempdir, re-encoded + remuxed — no re-compute.) Total spend ≈ $25 of $50.

**Published:** https://youtube.com/shorts/rhsUdHSvHgE (2026-07-21)
