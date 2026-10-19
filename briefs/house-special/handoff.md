# Preserve approved picture during sound revisions

House Special needed one extra copy of an existing vocal sound over its end title
after the picture had been approved. A private finishing recipe validated the
existing frame edit, copied its video stream unchanged, and replaced only the
soundtrack. The final upscale then copied the revised audio stream. This avoided
changing an approved cut to make a small sound edit, but duplicated delivery and
catalog bookkeeping outside the maintained editor.

Add an audio-only revision command to the maintained production CLI in a fresh
implementation session. Start with `tools/production/edit.mjs`,
`tools/production/mix.mjs` and their offline tests. The command should accept a
verified base delivery, a new soundtrack and a new version, reuse the approved
picture and frame edit, and create normal delivery evidence and clip-use records.

Acceptance checks:

- Refuse a changed base hash, invalid soundtrack, existing output version or
  mismatched duration before writing the new delivery.
- Preserve the video packet payloads, frame timestamps, frame rate and frame
  count. Keep the earlier delivery intact.
- When the soundtrack is derived from an approved mix, record the intended
  change intervals and verify identical PCM outside them. Check the encoded
  result for clipping and the presence of the added cue.
- Retain source-aligned picture and sound offsets for native vocal moments.
  Intentional repeats should be explicit cues rather than displaced shot audio.
- Keep visual inspection, numerical sound checks and real-time listening as
  separate facts. An empty speech transcript cannot establish an empty vocal bed.
- Use existing local media only. Add offline success and refusal cases, and do
  not submit generation jobs or infer a new finishing authorization.

The film's private recipes and verification evidence provide the reference case;
they remain in its verified archive. This is a shared production improvement, not
an implemented CLI feature.
