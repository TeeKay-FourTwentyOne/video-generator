# Audition the voice before finishing the stinger

2026-10-24 · Codex · RED TEARS · Shared production workflow observation

RED TEARS needed a frightened voice behind a rigid mask in a three-quarter-second
flash. Several individually generated cues sounded cartoonish to the director.
A broader numbered set exposed useful differences in voice texture. The final
choice was a local refinement of take five: slower, lower and more muffled.
The exact approved audition sample then entered the film without further changes.

For short nonverbal voices, audition a small authorized set early. Preserve raw
takes and offer numbered, matched-level previews in the intended time slot.
Include a longer source preview when it reveals a usable opening that the full
performance obscures. Choose voice character before adjusting pitch, speed,
filtering and placement. Keep the director's selected sample and checksum as
the insertion reference; verify its timing and PCM after mixing. Signal checks
do not substitute for listening or artistic approval.

## Fresh-session implementation handoff

Add a local audition packager under `tools/production/` that accepts existing
audio files, cue duration and processing settings. It should produce numbered
full-source and cue-length previews, a loopback review page, level measurements
and a manifest mapping each output to its source hash and exact processing.
Begin with local inputs; provider submission remains in the maintained clients
and project ledger workflow. A timeout must resume the existing operation.

The ElevenLabs client should preflight its current prompt-length contract before
submission; one overlong prompt in this production was rejected by validation.
Inspect `mcp/video-generator/src/clients/elevenlabs.ts` before choosing the repair.
Preserve creation snapshots and usage evidence in private storage.

Acceptance checks should cover source preservation, exact cue sample counts,
stable numbering, clipping detection and selection-to-mix identity. Keep provider
generation tests offline. Test different sample rates and cues shorter than their
source, and distinguish deliberate rate/pitch coupling from independent pitch
shifts. The tool should package a choice for the director, not infer approval.
