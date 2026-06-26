# SECONDS — Brief (final)

**Title:** SECONDS (double meaning: seconds of time / "factory seconds" — duplicate, inferior goods)
**Format:** 9:16 vertical, ~46s, 2160×3840 (4K via Real-ESRGAN ×2)
**Built:** 2026-06-25 (dealer's-choice; $25 cap; ~$20–22 generation spend incl. heavy re-renders)
**Published:** https://youtube.com/shorts/ilQDgcNSgnE
**Workspace:** `data/workspace/seconds/` · approved master `final/seconds_v7.mp4` (+ `seconds_v7_4k.mp4`)

## Logline

A lone hand-sewn felt puppet stitches a small second puppet by hand. A cold machine arm begins
placing identical felt copies beside it — one, then more and more — until the maker is buried under
a heap of its own flawless duplicates. The machine stops. We hold on the mound, and a single red
thread runs out of it to a needle resting in bare wood, leading to no one. The maker was making one
*by hand*. It was never finished. There is no hand left to finish it.

## Theme (AI — felt, never stated)

Mimicry, obsolescence, the absent author. The handmade puppet = the human maker; the machine arm
producing perfect identical copies = generative AI. The handmade work is slow, flawed, singular,
unfinished; the machine's output is instant, perfect, infinite, indistinguishable — except the
original carries the trace of a maker. Made *by* AI, *about* machine-copying — the self-implication
is the point. Wordless. NOT an explainer.

## Visual style

Tactile felt-and-wood tabletop diorama, warm tungsten desk-lamp pool, heavy negative space. Palette:
oatmeal-cream wool felt, walnut wood, brass needle, one red thread. The machine arm is cold matte
charcoal-grey plastic — the only smooth, non-fuzzy object in frame. **Puppets are FACELESS** — blank
cream felt with a single vertical seam-stitch (no eyes/mouth). This (a) sidesteps Veo's schematic-face
RAI filter, (b) reads as uncanny/authored, (c) makes the copies genuinely indistinguishable from the
maker = the theme. The copies are **inert** — placed and still; their lifelessness is the contrast.

## Final cut (7 shots, ~46s)

| # | dur | beat |
|---|-----|------|
| 1 | 4s | Macro: the maker hand-sewing the half-finished puppet in its lap. (trimmed from 8s — Veo froze after 4s) |
| 2 | 4s | Extreme macro: the brass needle through felt, red thread drawn taut. |
| 3 | 6s | Wide: the cold gripper-arm places the FIRST identical copy on the bench beside the maker. |
| 4 | 8s | Wide: the gripper places **more and more** copies, fast — a group of duplicates accumulating, the maker working on, getting crowded. |
| 5 | 8s | Close: the maker engulfed, copies crowding in, its red-thread hand still reaching out. |
| 6 | 6s | Close: the mound complete — the maker buried, indistinguishable among the heap. |
| 7 | 8s | Aftermath: stillness. The unfinished puppet at the table edge, a red thread across the bare wood to a lone needle — leading to no one. Slow fade. |

## Audio (designed, wordless)

ElevenLabs. Tender music-box + felt-piano (0–8s, the maker's craft) → a cold pneumatic THUNK as the
machine intrudes (8s) → a mechanical thunk-hiss rhythm building and overrunning the warmth through the
accumulation + engulfment (8–36s) → the machine STOPS into a stark silence as the burial completes →
a single fragile music-box note over the final reveal, decaying into black. Veo native audio discarded;
mix built to the locked picture (`final/seconds_audio_final.m4a`).

## Production notes / hard-won lessons (these drove new tooling)

- **Faceless felt forms clear Veo RAI** where schematic dot-eye/line-mouth faces don't. Probe early.
- **Veo book-end interpolation slides/pops anything that differs between the two anchor frames.** A placed
  prop at position X in frame A and X′ in B is *slid* across the table with nothing moving it; a count
  mismatch at a cut makes a doll *pop in*. → Built the **`anchor-drift`** skill (`tools/anchor-drift.py`):
  a pre-generation, frame-only check (within-clip and across-cut) that flags these before any Veo spend.
  Rule learned the hard way: a mover's payload is OK *within* a clip (it carries it smoothly) but NEVER
  *across a cut* (a hard cut can't carry anything — the doll teleports, the rigid gripper morphs).
- **Reframe to mask a mover at a cut** — you cannot cleanly show a gripper deliver across a same-framing
  hard cut; cut wider→closer so the mover leaves frame.
- **Veo RAI trips on dense crowds of humanoid forms** (a wide pile of ~6+ felt bodies + the arm reads as
  a "body pile"), even with neutral prose. Cap visible count (~4–5 wide passed), defer the "many" to close
  chaotic shots, or fall back to nano stills + programmatic motion.
- **Book-end can hand-place only ONE object per clip cleanly** (mover in contact in both frames). Multiple
  per clip = materialization — acceptable only in a *fast* accumulation where it reads as machine output.
- **Rigid/mechanical objects morph in Veo Fast** (the gripper's geometry shifts frame-to-frame); Veo nails
  soft organic felt but not hard-surface geometry.

See `[[project-seconds]]` and the feedback memories for the reusable versions.
