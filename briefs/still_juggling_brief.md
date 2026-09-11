# STILL JUGGLING — brief

**Format:** 9:16 social short, 17.2 s, 4K (2160×3840) upscaled from 720p. Built 2026-09-10, 20:10–21:20, speed run.
**Published:** https://youtube.com/shorts/xXGxzT1SSt8 (2026-09-10, description used virtually unchanged) · 4K delivered 2026-09-10 21:19 via share.cjs (7-day links, gs://vg-veo-0137184346/still-juggling/) · 4K verified 2160×3840 / 412 f / 17.17 s; audiowmark decode after upscale conf 1.20
**Workspace:** `data/workspace-archive/still-juggling/` · **Master:** `final/still_juggling_v12_wm_720.mp4` → `final/still_juggling_v12_4k.mp4`

## Concept
The Pierrot from Hellzapoppin' No. 5 (The Pepper's Ghost) juggles three yellow balls in a locked hips-up frame and never stops. Every cut lands on the same frame of the juggle — same pose, same three ball positions — while the world changes around her: a felt crocodile hand puppet pops in (stage), then the whole set swaps to a laundromat with a flat 2D cartoon bird on her shoulder, then back to the empty stage where she catches all three and winks. The crocodile heckles her ball count (Veo's juggling drops/merges balls; the heckler makes that the premise). Calliope under everything.

## Shape (final v12)
| t | beat |
|---|---|
| 0.00 | opens mid-juggle, stage |
| 2.33 | cut: crocodile pops in — "Three balls. I'm counting." (2.53) / "Hang on. Where'd that one go?" (4.15) |
| 6.00 | cut: laundromat + bird — "Oh, we're at the laundromat now. Great." (6.12) |
| 10.67 | cut: empty stage; "Two. Four. She's cheating!" (12.50) over the catch |
| 16.00 | "Show-off." on the wink; stinger; end 17.17 |

## How the continuity works
- One nano hero frame of the Pierrot at a canonical cascade snapshot (ball at apex, one in each palm) on flat magenta; keyed programmatically (magenta-difference key + despill) and composited onto nano plates (stage, laundromat) plus keyed puppet/bird sprites. Every anchor therefore has the juggler at identical pixels.
- Each clip is first-frame = last-frame book-ended at 720p (anchors bind at 720p). Veo returns to the anchor ~8 frames before the end (frame 136/144 at 6 s, 88/96 at 4 s); each clip is cut there, next clip starts at frame 0 → ball-on-ball joins. Opening clip uses its last 2.33 s so the head still ends on the match frame.
- Laundromat reroll froze her pose for the last ~1.2 s (ball floating); cut at frame 112, the first anchor match.

## Gens
s1 stage 6 s · s2 stage+puppet 6 s → rerolled s2b 4 s (jaw flapping) · s3 laundromat 6 s → rerolled s3b 6 s (jaw flapping) · s4 stage catch+wink 6 s (first-frame only). All Quality 720p. clone-check clean 6/6. clip-qa flagged ball-count/materialize on every clip; verified false at frame level on v1 (3 balls in every dense sample), then the user chose the joke path, so ball glitches are the premise.

## Sound
Veo native ambience per clip, level-matched to −23 LUFS; heckler = ElevenLabs Charlie (Australian) at −16.5 LUFS; calliope = ElevenLabs music (19 s, detected 120.2 BPM), aligned so a beat lands on the puppet pop and the stinger on the end hold, sidechain-ducked under lines; master −17.3 LUFS, −1.2 dBTP. audiowmark payload `STILLJUGGLING-26`, decode conf 1.33.

## Cost (≈ $9 of $25)
Veo 34 s ≈ $3.40 (+30% headroom ≈ $4.40) · nano 7 calls ≈ $1.05 · QA vision ≈ $2.50 · ElevenLabs TTS/music ≈ $0.50.

## Lessons
- Keyed-sprite composite anchors are the way to make a subject pixel-identical across environments; nano can't hold a pose across re-staged backgrounds.
- Veo's juggling is unreliable per-ball even when the cascade looks right in strips; a per-frame anchor-diff scan finds the true return frame and any tail freeze.
- Charlie's Australian read is naturally ~25% shorter than Callum's for the same lines.
