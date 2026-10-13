# Decisions and workflow findings

## The film

The native review is 45 seconds, 720 × 1280, 24 fps: 1,080 frames. Eight existing
clips contribute 984 frames, or 91.11 percent of the runtime. One new 96-frame
candle ending completes the return. The first complete edit, `v1`, uses existing
footage throughout; `v2` changes the closing picture and aligns its breath cue
to the action that actually came back.

The sequence is candle ignition, falling drop, clockwork, corridor, indigo ink,
an amber lamp, an underwater projector, a projected meadow, and the candle going
out. The sound is an original deterministic local composition. Source audio is
omitted; several historical annotations identified stray speech. No explanatory
text appears on screen.

The older clips carry differing provenance. Several exact historical model
versions are unknown, while other metadata comes from saved jobs or later film
plans. Those evidence labels remain intact. Nothing in this production upgrades
an old prompt to creation-time evidence.

## Selection and acceptance

Ten catalog queries returned 73 distinct eligible portrait source candidates.
Twenty-nine received a thumbnail scouting pass; eight were selected for motion
review. The selected set spans five named catalog collections and two sources
without collection labels. Collection membership is not proof of use in a
previous published cut. No old production folder was needed to retrieve media.

The water take had an early splash before the main drop landed. General and
duplication QA identified it; the edit uses only source frames 42–95. The lamp
take dims while an ember-like glow moves up its stem. QA correctly flagged that
as a deviation from the older prompt. After inspecting the actual frames, it was
retained deliberately as the signal leaving the lamp. This is a creative
adaptation with a known flag, not a claim that the old request was fulfilled.

The new ending returned 97 frames for a four-second request. Exactly the first
96 are used. The flame expires around source 2.1 seconds; sound follows that
observed action rather than the prompt's requested timing. The last twelve
picture frames fade to black.

## What the production exercised

- The existing offline suite passed before production.
- A ten-second real-media assembly checked clip-ID resolution, reviewed frame
  ranges, encoding and usage recording before the complete edit.
- Both complete edits used library IDs directly. Source hashes, decoded frame
  counts and dimensions were checked by the maintained editor.
- A single Runway Gen-4.5 image-to-video request used an extracted, hash-bound
  frame from the original candle clip. The immutable request retained exact
  prompt bytes, model, seed, controls and the reference hash.
- Polling resumed in a fresh process while the editable prompt was temporarily
  different. The saved original snapshot survived and followed the downloaded
  master. The original prompt file was restored afterward.
- Polling the completed request again returned the same clip ID, retained one
  generation record and created no additional use records. Library and private
  snapshot hashes were verified.
- The public production record distinguishes technical checks, frame inspection,
  listening claims and the director's subsequent artistic approval. No publication
  is claimed without its own evidence.

## Friction worth addressing

1. **Project identity depends on setup order.** Before a production record existed,
   the smoke and first edits acquired the versioned workspace name as their
   project ID. After creating the canonical record, those twelve new use records
   were corrected through the existing use-record API; their original rows and
   an exact mapping are preserved in the ignored workspace. Create the production
   record before first assembly. An explicit project ID during initialization
   would make this less fragile. New-generation collections also currently use
   the workspace name; the stable project collection was added explicitly.
2. **Search finds literal text, not visible concepts.** “Signal” returned no eligible
   source. Concrete nouns worked, but “clock” also found “clockwise” in an apple
   prompt, and “lightning” matched a water metaphor. Positive visual tags and
   direct kind/aspect filtering would help more than adding more prose. This
   scout intentionally used the source records with useful metadata; it does not
   establish discovery quality across the much larger unknown/derived inventory.
3. **One QA invocation may make several requests.** The duplication checker splits
   its selected frames into groups of fifteen. Accounting should predict and
   reconcile those individual calls, rather than count command invocations.
4. **The Python environment is an unstated dependency.** The default interpreter
   lacked Pillow. The existing repository-local production environment worked.
   A read-only doctor check could make this visible before image QA starts.

The next small tooling change to prioritize is explicit project identity at
initialization, carried consistently into uses and generation collections.
No shared tooling was changed as part of this production test.

## Approved finish

The director approved native v2 and requested a 4K upscale and the standard
publication workflow. Finishing uses the approved master directly, retaining
all 1,080 frames and copying its audio packets. The earlier native exports remain
unchanged. The 4K delivery is 2160 × 3840 at 24 fps, still exactly 45 seconds.

Six representative frames were compared using Lanczos, the maintained fast
Real-ESRGAN model and a half-strength blend. The model smoothed the metal and
projection-screen textures; the selected Lanczos finish retains those surfaces.
No new generation was needed. The finishing recipe and comparison frames remain
with the local production evidence.

The publication description is prepared, but no platform URL has been supplied.
The delivered status records readiness without inventing a publication event.
The project-identity improvement has a [fresh-session handoff](handoff.md).

## Archive dependencies and restoration

The archive preserves the approved native master, the 4K master, earlier edits,
materialized segments, sound stems, generation records, QA and local recipes.
Rebuilding an edit from clip IDs also requires the nine hash-addressed masters
in `data/clips/` and the repository's catalog and production tools. The ignored
dependency manifest records their exact paths and hashes. This is an intact
production archive, not a standalone copy of the entire clip library.

Verify the archive before restoring a copy to a new active workspace. Keep the
original sealed. Existing scout and QA recipes may reference the historical
workspace location or system fonts; review those paths in the working copy before
running them. Rebuilding only the approved 4K finish needs the preserved native
v2 master, FFmpeg and Python. Do not run writing QA or description synchronization
inside the sealed archive. Later release receipts belong outside it.
