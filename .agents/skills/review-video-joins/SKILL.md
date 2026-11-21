---
name: review-video-joins
description: Inspect and refine the joins in an assembled video before delivery, after editorial changes, or when a cut jumps. Uses exact source frames, movement context, trim matching and optional local blends while protecting dialogue and intentional cuts.
---

# Review video joins

Use this pass for every film before its first native delivery. Repeat it on
affected joins after editorial or finishing changes. For a single continuous
source, record that there are no internal joins and review the opening/ending.
Scale the investigation to the problem: most deliberate cuts need a contextual
check, not a search or optical flow. Preserve intentional hard cuts, ellipses,
changes of shot scale, stingers and cuts to black. A good individual take does
not establish that two takes join well.

## Inspect the assembled edit

- Derive the boundary list from the actual integer-frame edit, including cuts
  inside local composites. Classify each as continuous action, recording/reaction,
  intentional editorial cut, or transition. Do not treat a composite's single
  outer source entry as proof that it has no internal joins.
- For a cut at edit frame N, inspect decoded frames N−1 and N. A source range
  `[start, endExclusive)` ends at `endExclusive−1`. Retain source clip IDs,
  hashes, source indices and edit indices separately.
- Inspect both sides together, then every frame in a context window (roughly
  half a second each side to start). Check pose, eye line, mouth/blink phase,
  shoulders, hands, props, camera movement, lighting and background edges.
  Inspect full resolution when proxies hide defects.
- For a cut inside one scene that keeps the same person on both sides, measure
  as well as look: `python tools/join-appearance.py FILM N --crop L,T,R,B`
  compares mean luma, chroma and fine-texture energy of the same region (a
  jacket, hair) in frames N−1 and N at full resolution. A regenerated or
  restaged take can match in a 720p player and differ plainly at 4K. A flag is
  a prompt to inspect the saved crops, not a verdict; a scene change will flag
  and means nothing.
- Review normal-speed context as well as stills. Matching poses can hide a
  pause, velocity reversal, repeated frame or restarted movement. If playback
  or listening is unavailable, retain a review clip and report that limitation.
  A metric does not establish that the movie has been watched or heard.

## Refine an unintended jump

1. Mark protected speech, lip-sync, impacts, essential action and director-locked
   material. Search usable handles. In a dialogue-preserving pass, retain native
   speaking frames and their timing; remove unwanted extra mouthing in silent
   tails where possible. Do not hold/repeat frames to fake sync. A deliberate
   offscreen edit can be a separate craft choice.
2. Trim either side for closer pose and motion phase. Remove an unnecessary cut
   if one continuous reaction works. Recompute affected timeline and audio cues
   explicitly if duration changes.
3. For fixed-camera footage, optionally rank bounded candidates using weighted
   grayscale differences around the subject. Read [tools and evidence](references/tools-and-evidence.md)
   for the ranking helper, motion checks and evidence fields. Inspect the
   shortlist; the lowest pixel difference is not automatically the best take.
4. For small residual pose changes, audition a short local motion blend in a
   suitable gap. REPEAT used 3–6 intermediate frames at 24 fps; that is an
   example, not a universal preset. Protect active lip-sync and fast contact
   action. Inspect every intermediate frame plus both native motion windows.
   Reject doubled eyes/teeth, rubbery faces, drifting backgrounds and lingering
   blinks. Composite UI, captions and typography afterward to keep them crisp.
5. If blending harms the shot, use a clean cut, another range, a motivated
   cutaway or a documented remaining defect. Paid regeneration is a deliberate
   choice within authorization, never an automatic response to a score.

## Verify and retain the decision

Render a new version. Verify each bridge's endpoints are the exact adjacent
native source frames; check entry and exit for duplicate/dropped frames. Preserve
sources, alternatives, recipes and prior drafts. For a nontrivial refinement,
retain a short before/after reel at the same playback speed with labels and
source/edit frame references. Explain when windows align to different cut times;
a silent diagnostic reel does not establish sound QA.

Verify the actual export: decode, dimensions, fps, frame counts/timestamps,
source hashes and protected speech-frame mapping. For unchanged audio, copy it
and compare both compressed packets and decoded PCM. Compare unchanged picture
ranges by decoded frame hashes when the encoding path permits exact identity.
Do not claim pixel identity across re-encoding or upscaling; inspect those
changes with appropriate visual checks.

Retain a private per-join decision: intent, old/new source and edit ranges,
reason, treatment, inspected frames, metric definition, remaining defect, and
playback/listening actually performed. Keep technical checks, agent inspection
and director approval separate. A reduced discontinuity score is not a percentage
improvement in artistic quality.

Import reusable derivatives, record underlying source uses, and run project
analysis and authorized scoped backup as in `docs/production.md`. Update the
production page and review notes. This is an editorial pass; the assembly CLI
does not automatically judge continuity or grant spending/publication authority.

For the worked dialogue example and retained evidence, read
[REPEAT's join pass](references/repeat-join-pass.md).
