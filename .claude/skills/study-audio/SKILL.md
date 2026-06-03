---
name: study-audio
description: Turn an AI-generated transcript into a single study-audio MP3 via ElevenLabs and push it to the GCS bucket for phone listening. Use when the user wants to "make a study recording", "turn this into audio I can listen to", or narrate notes/transcripts of a Claude conversation. Estimates credit/dollar cost and gates real spend on a cost cap before generating.
allowed-tools: Read, Bash
---

# Study Audio

Convert a transcript (typically AI-generated notes covering a topic the user discussed with Claude) into one continuous MP3, narrated by the "AI Explains" voice, and upload it to the user's GCS bucket so it's reachable on a phone.

The pipeline is `tools/study-audio.cjs`: stage transcript → estimate cost → gate on cap → chunk → TTS each chunk (ElevenLabs) → concat → upload + signed URL.

## When to use

- User asks to make a study recording / listenable audio from notes or a transcript.
- User points at a file (or describes where it is) and wants it narrated.

**Don't use for:** video VO (use the MCP `generate_tts` tool inside a project), music (`generate_music`), or SFX (`generate_sound_effect`).

## Cost model (read this before estimating)

ElevenLabs is a **flat monthly subscription** billed in **credits = characters of input text**. Work that fits inside the remaining monthly quota is **FREE**. Only characters past the quota are a real dollar charge (usage-based billing). So:

- **Within quota → free → always proceed** (the cost cap does not apply).
- **Past quota → real overage dollars → gate on the cap** (default **$10**). If estimated overage exceeds the cap, **stop and confirm with the user** before generating.

Default model is `eleven_turbo_v2_5` = **0.5 credits/char** (~$0.033/min, ~$2/hr of audio). Standard models are 1 credit/char.

## Workflow

1. **Resolve the transcript location.** The user may give a path or just describe it ("the file I downloaded", "the notes from our last chat"). Resolve to a concrete file path. If the transcript doesn't exist yet because it's meant to be AI-generated from the conversation, draft it first (save to a file), then proceed.

2. **Sanity-check the transcript before estimating.** Skim it. If anything looks off — it's a raw chat dump with UI cruft, contains code blocks that would be read aloud as noise, is much longer/shorter than expected, or isn't actually prose meant to be heard — raise it with the user before spending. (The tool strips markdown by default, but it won't fix a transcript that's structurally wrong for narration.)

3. **Estimate (never spends):**
   ```bash
   node tools/study-audio.cjs <path> --estimate
   ```
   Report back: char/word count, credits, estimated duration, remaining quota, and whether it's free or carries overage.

4. **Decide on the gate:**
   - Free (within quota) → go straight to generation.
   - Overage ≤ cap → go ahead.
   - Overage > cap → **ask the user to confirm** (show the dollar figure). On approval, add `--confirm`.

5. **Generate + upload:**
   ```bash
   node tools/study-audio.cjs <path> [--confirm] [--slug=name] [options]
   ```
   Output lands at `data/study/<slug>/<slug>.mp3`; upload is on by default and prints a 7-day signed URL. Give the user that URL.

## Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--estimate` | — | Print estimate and exit. No generation, no spend. |
| `--slug=NAME` | from filename | Folder name under `data/study/`. |
| `--voice=ID` | `hpp4J3VqNfWAUOO0d1Us` (Bella, "AI Explains") | ElevenLabs voice. |
| `--model=ID` | `eleven_turbo_v2_5` | TTS model (turbo/flash = 0.5 credit/char). |
| `--speed=N` | `1.0` | Voice speed 0.7–1.2 (explainers used ~1.1). |
| `--max-cost=N` | `10` | Real-overage USD cap. |
| `--confirm` | — | Authorize generation past the cap. |
| `--no-upload` | (upload on) | Skip the GCS upload. |
| `--raw` | (strip markdown) | Narrate the file verbatim, including markdown. |
| `--move` | (copy) | Delete the source after staging it in. |
| `--chunk=N` | `2500` | Max characters per TTS request. |
| `--json` | — | Machine-readable output. |

## Defaults & conventions

- **Voice:** Bella (`hpp4J3VqNfWAUOO0d1Us`) — the voice from the AI-explainer series. Override only if the user asks.
- **Staging is a copy, not a move.** The original transcript is left in place; pass `--move` to delete it. (Surface this if the user explicitly said "move".)
- **Markdown is stripped by default** so headings/bullets/links aren't read literally. Use `--raw` to keep it.
- **Bucket path:** `gs://vg-veo-0137184346/study/<slug>/<slug>.mp3`. The signed URL expires after 7 days; re-mint anytime with `tools/gcp/share.cjs` (the file persists in the bucket).
- **Verify spend afterward** (optional): `node tools/elevenlabs-usage.cjs` shows credits consumed this cycle.

## Notes

- Long transcripts are chunked on paragraph → sentence → hard boundaries; chunks carry `previous_text`/`next_text` for prosody continuity, then concatenate seamlessly.
- The cost gate runs **before** any TTS call, so a blocked job (exit code 10) spends nothing.
