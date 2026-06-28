# Burger Djinn — Hold the Onions (brief + lessons)

**Published:** https://youtube.com/shorts/QmJ6X3qcvQU
**Built:** 2026-06-26/27 · **Spec:** 9:16, 43.3s, 2160×3840 (Real-ESRGAN ×2) · **Cost:** ~$16–17 (under $20 cap)
**Workspace (archived):** `data/workspace-archive/burger-djinn/` · final `final/burger_djinn_v3_4k.mp4`

## Concept
Upbeat AI-comedy short for the "make me laugh, something about AI" brief. A literal-minded AI drive-thru hands back everything you ask it to *remove* as its own labeled product: "hold the onions" → an onion in a paper boat; "no ice" → your ice returned; compounding (pickles/tomato/sauce). Exhausted driver says "surprise me" → the AI: *"I have been holding these… for you"* → every onion it's been holding avalanches in and buries the car. Button: serene *"Would you like me to remove the onions?"* → smash to black + deadpan legal fine print. On-theme = LLM over-literalism / misaligned instruction-following as slapstick.

Concept chosen via a fan-out Workflow (10 comedic engines → 3-lens judge panel [funny/fresh/feasible] → showrunner synthesis); literal-genie won, then overridden-on-taste confirmed it. Treatment JSON in workspace `scratch/concept-workflow-result.json`.

## Build
- **8 shots:** 4 live Veo 3.1 (S1 establish, S2 onion-in-boat, S3 ice-boat, S6 onion avalanche) + 4 programmatic (S4 boat-accumulation montage, S5 lamp-menace push-in, S7 buried-car, S8 legal card).
- **Faceless by design** (the key RAI dodge): lamp-speaker = the AI, back-of-head driver, single gloved hand, onions have no faces. The avalanche is rigid round produce (NOT a body-pile) → dodges crowd-RAI. Zero Veo rerolls (avalanche landed first try).
- **Veo audio OFF everywhere** (every speaker disembodied/faceless → no lip-sync); full mix built in ElevenLabs + ffmpeg for frame-exact comedy timing. AI voice = Sarah (serene corporate-assistant), Driver = Chris (tired everyman). 3-note brand jingle + escalating dings as the running gag.
- Visual: night drive-thru, brass genie-lamp speaker = the AI (warm *practical* indicator ring — never glow/neon/hologram). Nano plates: menu-board + service-window.

## Lessons / reusable wins
1. **anchor-drift "hand-contact-at-endpoint" rule** — on any place-an-object book-end, keep the mover touching its payload in the LAST frame (and pre-place the receiving container in the first), or Veo pops/slides the object. Where un-generatable, use a firstFrame-only Veo shot (no lastFrame = no endpoint to pop toward).
2. **Veo pricing was stale in memory** ($0.10/s) — actual Quality $0.40/s, Fast $0.15/s. Drove the live-vs-programmatic shot split.
3. **Faceless framing** reliably dodges Veo's face/crowd RAI and reads as more authored.
4. **Review-round failure classes & tooling** (v1 had 3 contextual bugs the user caught):
   - *Contextually-odd action* (a car window rolled UP at the drive-thru) — invisible to clip-qa (glitch-only) and to intent-anchored checks (author blind spot). Built **`tools/motion-direction.py`** (dense optical flow) to catch the "right action, wrong direction" class — localizes motion, measures direction, separates camera vs object. CV localization is reliable; VLM judgment is advisory (attention-direction is the win). Fix = reverse the clip.
   - *VO/action desync* — "Holding the onions!" fired ~1.3s after the onion was placed; root cause = authored VO against an idealized beat, never measured the rendered clip's action timing. Fix = re-time onto the action (verified via transcribe / vo-alignment).
   - *Long hold/freeze* (S7 7s frozen push-in) — caught by detect-long-holds / evaluate-edit. **Run `evaluate-edit` as a standing gate before any review delivery** (it wasn't run on v1). Fix = regenerate as a live settling clip.
5. **v3 edit:** lifted a redundant onion re-hold (8.6→10.5s) directly from the 4K master (frame-accurate re-encode, NOT re-upscaled) + audio re-synced (`scratch/build_mix_v3.py`).
