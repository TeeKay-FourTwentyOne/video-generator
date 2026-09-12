# Character Registry

Reusable characters that persist **across projects and series**. A character here is an
identity contract: face canon + a verbatim Veo lock description + a voice. Any project that
uses the character injects these instead of re-inventing them.

Started 2026-08-22 (Stephen: "let's start building re-usable characters somewhere in the
broader repository") — seeded with The Lodger's two leads.

## Layout

```
characters/<character-id>/
  character.json    # machine-readable identity record (see schema below)
  profile.md        # human notes: who they are, casting history, usage rules
  voice/            # voice assets: clone source samples, provenance notes
```

## Conventions

- **id** is kebab-case (`cora-albright`); stable once created.
- **Image canon:** existing series keep their canon files where they live (e.g.
  `series/the-lodger/canon/`) and `character.json` *points* at them — those directories are
  never archived with a workspace. Characters created *outside* a series home their refs
  here in the character dir.
- **Veo lock text is verbatim** — it is injected word-for-word into generation prompts.
  Change it only with the owner's sign-off; it commits every future shot.
- **Voice:** `voice.voice_id` is the *current* ElevenLabs voice. Prior voices go in
  `voice.history` (superseded clones, auditioned-and-rejected casts) so old renders remain
  reproducible. Clone source audio lives in `voice/samples/` with a provenance note —
  where each sample came from, how it was cleaned.
- **Native-voice characters:** for Veo-native dialogue, `voice_descriptor_veo` is the
  descriptor phrase used in prompts. The EL voice (if any) is for VO/narration and
  dub-rescue when a native read breaks.
- A character used in a shipped piece is **locked**: face and voice changes need explicit
  owner sign-off (same tier as casting).

## Index

| id | name | origin | voice |
|---|---|---|---|
| `cora-albright` | Cora May Albright | The Lodger (2026-08) | EL clone of her Veo-native voice |
| `vascari` | Vascari | Outlaw Vampire Sommeliers / The Lodger | Veo native on-camera + EL clone of his native voice (locked) |
| `floss` | Floss | FLOSS (2026-09) | Veo native (descriptor); EL clone pending |
