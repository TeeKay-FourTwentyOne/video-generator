# PARKING LOT GOSPEL — Shooting Brief

**Logline:** A four-voice gospel choir + lead stand in a laundromat parking lot in full Sunday rapture, mourning one empty parking space in glorious four-part harmony — because someone's beloved Corolla just got towed. Played with total sincerity. The grief is real; it's just *hilarious* that it's about an economy sedan.

- **Format:** 9:16 vertical, ~47s, 8 beats.
- **Model budget:** Veo 3.1 Fast for most; **exactly 2 Veo Quality** (Beat 1 a-cappella hook, Beat 6 tutti climax).
- **Workspace:** `data/workspace/parking-lot-gospel/` (refs / frames / clips / final / scratch)
- **Title (working):** "Where My Corolla Used To Be"

## The Load-Bearing Decision (why the risky idea is actually safe)

**Voice is decoupled from picture.** The full song (lead + 4-part choir + organ + rhythm) is authored ONCE in ElevenLabs as the single canonical track. Every Veo clip is generated with `generateAudio: false`; the performers MIME to the track and the ElevenLabs vocal is post-synced underneath. Veo never sings, never produces harmony. Gospel performance = held open vowels, closed eyes, sway, raised hands → loose lip-sync is invisible. Book-end every singing clip on an open-mouthed belt pose.

Other locked decisions:
- The tow is a **HARD CUT**, never a Veo tow-physics shot. Receding-taillights aftermath = nano still + programmatic Ken Burns.
- ALL on-screen text (end card, marquee, signage) is baked into nano stills / ffmpeg — **never Veo** (it garbles text).
- Each choir member hard-anchored with a 30–50 word locked description in every prompt + both book-end frames.
- Keep group physics loose (sway + raised hands); **no precise unison clapping**.
- Shorts safe zone: all end-card text top/middle, never a bottom band.

## The Song — "Where My Corolla Used To Be"

Traditional Black church Sunday-service gospel, **call-and-response** (warm weathered contralto LEAD + close churchy SATB choir w/ soprano descant). Hammond B3 (Leslie slow→fast), gospel piano triplets (12/8), tambourine, brushes→sticks, claps on 2&4, walking bass at the shout. **Key Ab major → up a half-step to A on the tutti.** Rubato a-cappella open → ~72 BPM → ~84 at climax. ppp solo → ff tutti shout → hard silence → lone Hammond note.

**Hook line:** *"There's a SPAAACE... where my Corolla used to be."*

| Section | (draft) t | Lyric core | Notes |
|---|---|---|---|
| a-cappella intro | 0–7 | "There's a space / where my Corolla used to be… Lord, she was right HERE this mornin'." | **Quality peak #1.** Solo lead, no instruments. |
| organ-drop / soft answer | 7–15 | LEAD "where'd she GO?" / CHOIR (hushed) "Mm — towed." / "Check-engine light stayed on for a year… she loved it still." | Organ swells in under last word. |
| verse / call-response build | 15–24 | "Did I FEED that meter? (She fed it!) / Did I read that SIGN? (…she did not.) / never left me on the side of ninety-five — Tow-ed a-WAY!" | Full 4-part; lone comic deadpan "…she did not". |
| stack the harmonies | 24–31 | "Somebody PRAY for my deposit — (Where my Corolla used to BE!) / paid OFF, paid OFFF / the GRIEF, it don't depreciate" | Lead + choir overlap; voice added each repeat. |
| tutti climax | 31–41 | "WHERE MY CO-ROL-LA USED TO BE! / Ride ON to the impound in the SKY! / eighty-seven thousand miles — and not ONE of them a LIE!" | **Quality peak #2.** Key up ½. Tow exits behind on held "LIE". Do NOT resolve. |
| the cut | 41–45 | (hard cut to empty lot) lone Hammond note / "…that was the wrong space, sir?" / "Towed." | Spoken beats = **separate dry TTS**, not music model. |
| tag / end card | 45–47 | CHOIR faint a-cappella "used to be… used to be." | Form comes full circle. |

**ElevenLabs generation:** put full arrangement in the style prompt; paste section lyrics with bracketed structure tags + (LEAD)/(CHOIR) cues and open vowels spelled out. Mark a-cappella intro + tag as instrument-free. Generate 2–3 takes, pick clearest harmony bloom (or stack two). Render the tutti chord **sustaining past the cut**; clip frame-accurate in the assembler. The two spoken-deadpan lines → separate TTS (dry contralto aside + flat tow-company voice). **ElevenLabs only — no Suno.**

## Choir (locked descriptions — inject verbatim)

Unifying wardrobe: **matching plum-purple satin choir robes + gold-trimmed stole** over each member's Sunday best; gold accents echo across the group. Della Mae's stole fuller/longer to mark the lead.

- **Sister Della Mae** (lead, contralto) — Heavyset Black woman, late 50s, deep umber skin, full round face, high cheekbones, broad warm smile, expressive brows. Short silver-grey natural curls. Reading glasses on a beaded chain. Plum-purple satin robe, gold stole, large gold hoops.
- **Yolanda** (alto) — Slender Black woman, early 30s, warm brown skin, oval face, large almond eyes, sharp jaw. Long box braids in a high bun. Small gold nose stud. Plum robe over high-neck cream blouse, thin gold cross.
- **Brother Cornell** (tenor) — Tall broad-shouldered Black man, 40s, rich dark-brown skin, square face, neat full beard flecked grey, close fade. Black-framed glasses. Plum robe, gold stole over white shirt + dark tie, lapel pin.
- **Deacon Otis** (bass) — Wiry older Black man, late 60s, light-brown weathered skin, lean lined face, thin grey moustache, balding w/ white sides. Gold-capped front tooth. Plum robe, gold stole, gold-rimmed bifocals low on nose.
- **Keisha** (soprano) — Young Black woman, early 20s, deep brown skin, round full-cheeked face, dimples, bright wide eyes. Short tapered natural afro. Silver studs up one ear. Plum robe over mustard turtleneck, silver hoops.

Staging: Della Mae front-center; Cornell + Otis (tall) flank, Yolanda + Keisha inside — heights stagger, no face occluded. For the two Quality peaks, tighten to lead + 1–2 members to cut multi-face morph risk.

## Environment — "Suds & Sun" laundromat lot

Single-story strip-mall plaza, **golden magic hour ~20 min before sunset** — warm amber key + cool sky fill ("stained-glass" trick turns a parking lot into a sanctuary). Dead center, framed like an altar: ONE parking stall holding a **faded champagne-gold 1990s Corolla** (oxidized hood, one mismatched door, rear-bumper dent, faded decal). Blank marquee + blank pole sign (lettering added later, never rendered). Empty trash can, drifted shopping cart, carriage lamp on the verge of buzzing on. Palette: golden-amber/honey + peach-to-teal dusk; accent pops reserved for the turn = tow truck's hazard amber + receding taillight red.

**Master plate nano prompt** (no text in image; lighting/lens language, never "photograph"): *Vertical 9:16 wide of a 1980s strip-mall laundromat parking lot at golden magic hour, slightly low locked tripod, wide 24mm-feel lens, deep focus, photorealistic. Back third: flat-roofed cinderblock laundromat, long plate-glass windows glowing warm amber from dryers; completely BLANK marquee fascia + BLANK pole sign — no letters/numbers/words/logos anywhere. Foreground sun-warmed asphalt, faded white stall lines, two wheel-stops, dented shopping cart, unlit carriage lamp, overflowing trash can. Dead center framed like an altar: ONE empty stall, asphalt cleaner + oil-darkened, white lines bracketing a car-shaped emptiness. No people. Top third wide-open dusk sky, peach-to-teal gradient, scrubby palms + telephone wires in silhouette. Low raking golden sun camera-left, long soft shadows, warm amber key + cool blue fill, gentle lens bloom on the glass, faint haze, fine grain. Sacred holy-hour stillness but unmistakably a strip-mall lot. No text anywhere.*

The tow reads three ways: (1) setup — tow truck idling at lot edge w/ amber strobe in an early/mid wide; (2) the turn — Veo lateral background drift of truck+Corolla exiting frame during the tutti, then HARD CUT; (3) aftermath — nano still of empty stall + receding taillights, Ken Burns only.

## Shot list (durations to be CONFORMED to the rendered track)

> **Blocking fixes baked in:** all Veo beats use legal **4/6/8s** durations; the **hard cut lands on the climax peak ("LIE")**, not 3s early. Final boundaries get re-anchored to the actual ElevenLabs track once rendered.

1. **Cold-open hook** (Veo **Quality**) — CU/medium-CU lead alone, eyes closed, head back, single sustained held vowel; bokeh lot behind, empty space faint over her shoulder. No choir, no organ.
2. **Organ drop + wide reveal** (Veo Fast) — hard cut wide: full choir flanks lead, all in rapture over the one empty stall. Magnitude/smallness gap revealed.
3. **Verse 1 — the lament** (Veo Fast) — medium two-shot lead + alto, grieving open-palm reach toward the empty space. Loss specified in lyric.
4. **Harmonies stacking** (Veo Fast) — tighter four-choir group shot, call-and-response layering, hands rising, staggered poses.
5. **Build to the brink** (Veo Fast) — medium on lead, eyes skyward, cresting; short rising bridge (the inhale).
6. **Tutti climax + the tow behind** (Veo **Quality**) — wide hero, all five at full rapture; tow truck w/ Corolla already winched drifts laterally OUT of frame behind their unaware backs. Hard cut on the peak.
7. **Hard cut — empty lot + receding taillights** (stills) — locked wide of the now-empty stall at dusk, two red taillights receding; music clips to a lone decaying organ note + ~1.5s silence.
8. **End card** (stills) — "PARKING LOT GOSPEL" upper-middle over the empty-lot still; epitaph line fades up ~1s later ("In Loving Memory — '09 Corolla, Towed"). Gentle dip-to-black.

## CONFORMED EDIT TIMELINE — from Take 1 transcription (canonical)

Take 1 = `song_master.mp3` (47.05s). All cuts pinned to transcribed word times. **6 Veo clips (2 Quality V1/V6, 4 Fast), 2 nano-still inserts, 2 stills beats.** Hard cut lands on the tutti peak "lie" @ 38.5s.

> **STRUCTURAL CHANGE (car already gone):** The Corolla is GONE from frame one — the choir mourns an empty altar stall (oil stain + lone hubcap) the entire song, matching the lyric "where my Corolla *used to be*." This **retires the climax tow-truck lateral-physics shot** (was the riskiest Veo beat). V6 is now pure tutti rapture over the empty space (magnitude-vs-nothing gap at its strongest). The only vehicle anywhere is faint receding red taillights far down the boulevard in the S7 aftermath — the truck that already took her, never watched. Cast/world anchor = `refs/choir_group_plate_empty.png`.

| On-screen | Source | Tier | Gen len | Content | Lyric under it |
|---|---|---|---|---|---|
| 0.00–4.00 | **V1** | **Quality** | 4s | Lead CU, a cappella, eyes closed, head back, hand rising | "There's a space… used to be, Lord / she was right here this mornin'" |
| 4.00–12.00 | **V2** | Fast | 8s | Organ drop → hard cut WIDE, full choir reveal over the empty stall | "Tell me where'd she go / (towed) / silver in the mornin' / she got towed / check-engine light… she loved it still" |
| 12.00–12.80 | **V3** | Fast | 8s (12–20) | Choir/lead: "Did I feed that meter—" | "did I feed that meter" |
| 12.80–13.55 | **INSERT-A** | still | — | **Expired parking meter**, red EXPIRED flag, quick punch-in | (on "meter") |
| 13.55–14.90 | **V3** | Fast | (cont.) | "(she fed it) / Did I read that—" | "she fed it / did I read that" |
| 14.90–15.70 | **INSERT-B** | still | — | **No Parking / Tow-Away Zone sign**, quick punch-in | (on "sign") |
| 15.70–20.00 | **V3** | Fast | (cont.) | Choir deadpan "…she did not" → "left me on the side" → "towed away, towed away" | "she did not / …side of ninety-five / towed away towed away" |
| 20.00–28.00 | **V4** | Fast | 8s | Harmonies stacking, hands rising, call-and-response | "somebody pray for my deposit / where my Corolla used to be / the grief don't depreciate / used to be" |
| 28.00–31.00 | **V5** | Fast | 4s | The brink — medium on lead, eyes skyward, cresting into the lift | (instrumental lift → "oh, my Corolla") |
| 31.00–38.90 | **V6** | **Quality** | 8s | TUTTI climax — all five at full rapture over the EMPTY stall; peak on "lie" @ 38.5; no tow physics | "ride on to the impound in the sky / 87,000 miles and not one of them a lie" |
| 38.90–43.80 | **S7** | stills | — | HARD CUT → empty lot + receding red taillights, dusk; Ken Burns push-in | "all right, all right, used to be, used to be" (over empty lot) |
| 43.80–47.05 | **S8** | stills | — | End card "PARKING LOT GOSPEL" upper-middle + epitaph fade-up; dip-to-black | instrumental decay |

**Insert build:** INSERT-A (meter) + INSERT-B (sign) are nano stills (text baked legibly, kept out of Veo). They hard-cut OVER V3's continuous choir performance, then cut back — V3 is one 8s gen representing the 12–20 window, chopped around the two inserts. Per user note: literal diegetic cutaways on the itemized grievances make the call-and-response a visual gag too.

**Spoken button (optional, decide in edit):** a single flat dry "Towed." TTS could land ~44.5s over the decay as a final deflation — generate it, audition both with/without; don't let it step on the sung "used to be" ache if it dampens the landing.

## Risk register (from line-producer go/no-go, risk 0.42)

- **BLOCKING — climax sync:** conform picture to the rendered song; the hard cut must land on the tutti peak.
- **BLOCKING — legal Veo durations:** 4/6/8s only.
- **Pre-flight the song before Veo spend** (~$2 of music vs ~$30 of Veo).
- Render tutti sustaining past the cut; clip in assembler.
- Spoken-deadpan beats = separate dry TTS, not generate_music.
- Re-anchor all audio cues by SRC after the re-block.
- Beat 6 is the riskiest (5 small faces + lateral truck + 8s held belt) — correctly Quality; if it morphs, trust the human watch / fall back to lead + 2 members. Don't burn five re-rolls (clip-qa over-flags morph the eye never catches).
- Keep the blank-marquee plate textless (vintage descriptors can bake in phantom signage — strong NO-TEXT suppressors already in the prompt).
- Keep ALL-CAPS lyric words OUT of Veo prompts (Veo renders caps as signage); Veo prompts describe mime/pose/sway only, never lyric content.

## Production order

1. **Song first** (canonical ElevenLabs track) → analyze → confirm good (2–3 takes if needed).
2. Conform shot durations + cut point to the real track; generate the two deadpan TTS lines.
3. Nano: master plate → choir character refs → per-beat book-end poster frames (frame-qa each).
4. Veo: 6 Fast + 2 Quality, `generateAudio: false`, mime.
5. Assemble: post-sync vocal under picture, frame-accurate cut, end card, SFX, dip-to-black.
6. Upscale to 4K (Real-ESRGAN), final.
