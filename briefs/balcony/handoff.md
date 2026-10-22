# BALCONY handoff (2026-10-21)

After the fifth native cut the director judged that Veo was having tremendous issues with this
film and chose a different approach: continue on a machine that can generate locally, with the
fine-grained control the tricky shots need, instead of buying more Veo takes. This page says where
everything is, what state the film is in, and what the next builder should know. The creative
intent is in [brief.md](brief.md); every anchor, prompt, take, decision and clip ID is in
[shots.md](shots.md); the current public facts are in [production.json](production.json).

## Where everything is

- **Source (this folder).** Brief, production record, draft description, the shot book, and
  `recipes/`: the v5 edit table and its builder, the phones-hold renderer and the title renderer.
  The catalog records for the project's 24 clips and their edit uses are under `catalog/`.
- **Clip library.** Collection `balcony`: 19 Veo takes and 5 local renders, each with its private
  generation snapshot and local analysis run, synced to the private clip backup on 2026-10-21.
  On another machine, `npm run clips -- cloud fetch CLIP_ID` restores a master into
  `data/clips/` with its snapshots; the IDs are in the shot book's inventory table. Setting up
  the recovery configuration on a new machine is described in `docs/clip-restore.md`.
- **Workspace bundle.** A tar of `data/workspace/balcony-v1/` without scratch files, QA strips,
  superseded renders and old mixes was uploaded to the project's private infrastructure bucket
  (the one `data/config.json` names as `veoGcsBucket`) as `handoff/balcony-v1-2026-10-21.tar`.
  Its SHA-256 and the full locator are recorded in the workspace plan. It holds `refs/` (the
  plate, both character references and every anchor), `audio/` (the ElevenLabs stems: four phone
  lines, the aside, the night bed, the lute, the earbud click, their small-speaker versions and
  the receipts), `clips/` (each take's native audio as WAV, and the local renders), `prompts/`,
  `images/` (the anchor requests), `recipes/`, `transcripts/`, `qa/` (hash-bound decisions and
  scan reports), `operations/` (provider records, so that no request is ever resubmitted), the
  ledger (closed; accounting only), `film.json`, `plan.md`, the v1 to v5 edit lists, the v5 mix and
  `final/v5/` (film, debug overlay, review page, delivery record). Unpack it to
  `data/workspace/balcony-v1/`, fetch the clip IDs, and `python3 data/workspace/balcony-v1/recipes/build-edit-v5.py v6 recipes/v5-table.json`
  followed by `npm run film -- assemble data/workspace/balcony-v1 v6` reproduces the v5 cut as a
  new version (v5 itself is immutable).

## State of the film

v5 is the latest cut: 1470 frames, 61.25 s, five segments longer than the brief's 30 to 45 s.
Its timeline is at the end of the shot book. The director's responses so far:

- v1: liked ("Interesting. Funny. I like it."), then three notes: hold on the couple only for a
  second and pan down to the two phones; the people walk off behind while the phones keep
  speaking, a distinct heart on each screen; an early flub.
- v3/v4: the phones are perfect and the aside stays; five notes: he looks different in the wide and
  grows glasses; her line is sung; he looks away from the balcony in every one of his shots; the
  meeting puts him on a fake ground and they walk through a wall; minimise motion.
- v5 (all of his coverage re-blocked, her line retaken spoken, meeting as close-up, close-up,
  still two-shot): Veo is having tremendous issues with this video; take a different approach.

### What holds up and is worth keeping

- **S07B** (the phones in close-up while the couple walk off through the curtain) and **S08** (the
  programmatic hold with the screens pulsing to the phones' lines), with the four phone lines and the
  aside. The director called the phones perfect.
- **FL1B**, the flub ("O lady of the lettuce..."), with her at the rail in the corner he faces.
- **S02B**, her line 2 spoken plainly and complete.
- **S04**, her bored line 4 with the stifled yawn, and its cutaway (frames 152 to 177).
- **T01**, the title card, if a title is wanted at all.

### What Veo could not do in two rounds (candidates for local generation)

1. **His courtyard coverage with his eyes on her.** The first anchors put the balcony behind him,
   so facing the lens meant facing away from her; the re-blocked C1 angle fixed the eyeline but
   the wide still paints spectacle glints on his small face, and the point-of-view take (S01B)
   pushed in on its own and invented a second lit balustrade at the top of frame (hidden in v5 by
   a bottom-anchored zoom, with his legs showing between the balusters).
2. **The earbud coming out.** Three takes (S05, S05C, and the two-shot S06) either left it in or put
   it back. v5 fakes the beat with a 44-frame palindrome loop of the one clean half second and a
   retake (S05D) from an anchor with no earbud anywhere.
3. **The meeting.** The tilt-down takes (S06B, S06C) ghosted the phones or made a fake ground and a
   walk through the wall; the v5 close-ups work only in their first two seconds (M1 turns to the
   lens, M3 adds a third "Hi" and lets her drift out of frame).
4. **Any camera move.** Book-ended tilts ghost props; "locked off" still drifts or pushes in.
5. **Long spoken lines.** A two-clause line lost its second clause and came back sung; the fix was
   one plain sentence of about a dozen words.

### Open director's notes still standing

Length (brief 30 to 45 s; v5 is 61 s); whether the silent opening wide stays; the push-in and
the legs in the point-of-view shot; line 3 finishing while he reads the phone; the cut third
"Hi" (available if a stammer is wanted).

## Suggestions for the local approach

These are the builder's suggestions, not instructions.

- Keep the ending (S07B into S08, the phone lines and the aside) exactly as it is. It is the best
  material in the film and the one part the director has approved.
- Keep the Veo takes that carry spoken lines where the picture is acceptable (FL1B, S02B, S04,
  M3's two words), since their native voices are already matched to the faces; the per-take native
  audio is in the bundle as WAV if a locally generated picture needs to be cut to it.
- Generate locally the beats that are silent or reactive and that Veo kept failing: the earbud
  coming out of his ear, his looks up at her, the two close-ups of the meeting, any camera move
  (the pan from the couple down to the phones that the director asked for). The anchors in
  `refs/` carry the wardrobe and set continuity and were accepted through two rounds; the C1, C3,
  C2b/C2c, M1, M2b and M3 frames are the right starting images, and the first frame of any kept
  take can be extracted for a match.
- The lessons from this film are in `docs/craft/field-notes/veo.md` and `anchors.md` (Balcony
  entries dated 2026-10-19): block eyelines in the anchor's geometry, keep a wide's use short when
  the face is small, land prop removals on a cut, give the model nothing to restore after the cut,
  keep spoken lines to one clause, and expect the lens-look.

## Rules carried over

- Every clip here was paid for once and is immutable in the library; never resubmit a request ID
  from `operations/`. Edit decisions are bound to clip hashes.
- The spending authorization for this title was used to its ceiling on the original machine; any
  new paid generation, finishing or upscale needs a fresh authorization from the director. The
  amounts live in the ignored ledger, not in these documents.
- No cut is approved, nothing is upscaled and nothing is published. `description.md` is a draft.
