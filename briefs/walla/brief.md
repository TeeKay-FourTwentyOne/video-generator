# Walla

[Current production record](README.md) · [Publication text](description.md).

This document preserves the retained creative and production history. Dated plans and technical observations describe their original sessions; the current record states only supported production facts.

An open-invitation film, October 2026: the director handed the agent any topic, either
aspect and start-to-finish creative control within the local spending authorization. Delivered: 31.2 seconds,
1920 x 1080 (16:9), 24 fps, native 1080p review export. Existing providers only.

## Release status

**Status:** Published (2026-10-08, confirmed by the director).

**YouTube:** https://youtu.be/lcT11ZH_awM

URL supplied by the director on October 8, 2026, about 21:30; public availability not independently
verified. Source commit and workspace clean-up are the director's, planned for October 9.

**Build history:** Native v4 delivered for the director's review (2026-10-08, evening). v1 (48 s) was
withdrawn after the director saw the lead's lips move under the background's lines; v3 (33.8 s)
cut each room before her mouth opens and still missed one in the laundromat, which the director
caught; v4 (31.2 s) cuts that room in at its third line. The director approved v4 and asked for the 4K master, made
the same evening. 4K master made at the director's request and published (`final/v4/film_4k.mp4`, 3840 x 2160, 749 frames, SHA256
0f3006689781209956c1c0d5662f3f5a50a9169203635112ed658dba38583ac9). Source commit pending (the director's, 2026-10-09); media stays under the ignored workspace.

## The film

**walla** (noun, film sound): the murmur of a crowd talking, made so that no single word
can be picked out.

A woman of about sixty-five spends a day in a city drawing people in a small sketchbook:
a café at breakfast, a tram, a park bench at noon, a laundromat, a bar at dusk. She never
speaks. The camera stays on her. The subtitles do not: they carry, word for word, what the
people behind her are saying. At night, at a bus stop, a stranger sits at the other end of
her bench. She closes the sketchbook, turns, and says something to him. The subtitle reads
*[indistinct]*. Black. The word, and its definition.

The rule of the build: the agent wrote none of the background's lines. Veo's native audio
made them, Whisper transcribed them, the agent selected and ordered. The film is made of
what the model volunteered. If a take had given no usable speech, that scene would have
played uncaptioned; none did. The only authored caption is the last one.

## Visual and sonic direction

Photoreal, 35 mm feel, locked-off camera in every shot, human-scale frames. One woman:
short silver hair, a mustard-yellow raincoat open over a dark green jumper, a small black
sketchbook. At most three other people in any frame, close enough to the camera for native
audio to carry. The light walks through the day: grey rain, mid-morning, noon gold,
afternoon fluorescent, blue dusk, wet night. No legible text in the world; subtitles in
Avenir Next, white, bottom centre; the end card in Baskerville.

No score. The six native tracks are the whole soundtrack: room, street, and the talk,
levelled from measurement, crossfaded over the cuts, the night street ringing on under the
black.

## Coverage

| Shot | Take | Edit s | Beat |
| --- | --- | ---: | --- |
| S01 | 8 s Quality, native audio | 2.75 | Café, morning: she looks out at the rain, turns to the two women at the next table |
| S02 | 8 s Quality, native audio | 5.4 | Tram: two passengers across the aisle talk |
| S03 | 8 s Quality, native audio | 2.9 | Park bench, noon: she closes her eyes in the sun; two old men on the next bench talk |
| S04 | 8 s Quality, native audio | 3.9 | Laundromat: two people folding a sheet talk |
| S05 | 8 s Quality silent retake, v1's native audio | 2.75 | Bar, dusk: the couple in the booth talk; the bartender comes over |
| S06 | 8 s Quality, native audio | 7.5 | Bus stop, night: a stranger sits; she speaks: [indistinct] |
| T01 | local | 6.0 | Black; the word and the definition |

Anchors: one café image that doubles as the character reference, five location images
generated fresh from it. Nine Veo attempts: six first takes with audio, then three silent
retakes of the café, park and bar after the lead's lips were found moving under the
background's lines; only the bar retake reached the cut. Veo gave the foreground woman lines
in five of six audio takes despite "she does not speak", and animated her mouth in two of
three silent takes despite "lips closed and still"; the remedy was cutting each room before
her mouth opens.

## Delivery and provenance

Primary film: `data/workspace/walla-v1/final/v4/film.mp4` (749 frames, H.264 + AAC 48 kHz
stereo) and its 4K master `film_4k.mp4` beside it (a 50/50 blend of the fast 2x model and a Lanczos 2x,
chosen on 100% crops after the model alone waxed the faces; the end card rendered natively at 4K;
audio untouched); v1, v2 and v3 are preserved. Review player, delivery manifest and a frame/timecode overlay copy are adjacent;
the workspace plan holds the blocking, the per-shot table, the transcripts, the gate record
and the decision queue. Recipes for the subtitles, the end card and the transcription live
under the workspace's `recipes/`.

Nine Veo 3.1 Quality takes (six with audio, three silent), six Google reference
images, 23 Claude QA calls and six Whisper transcriptions are recorded. Usage
estimates and retained reserves remain in local accounting. No new provider or
library was used.

## Review contract

The v4 export passed full decode, frame count, dimensions and source-hash checks.
Measured audio: -16.1 LUFS integrated, -1.9 dBTP. Every take passed clip-qa and clone-check; two LOW flags (a folding
sheet, a wandering wine glass) were cut around. Real-time playback and listening were not
certified by the agent: the subtitles are Whisper's reading of the native audio and should be
checked against what is heard. Known residuals: she glances at the lens at the head of each
scene (the anchors' eye contact, kept as a motif); the park bin carries the word LITTER; the
café, park and bar run under three seconds each because the cut stops where her mouth starts.

## Claude Code build (Fable 5.1), 2026-10-08

Workspace `data/workspace/walla-v1/`. Built in one evening session from the invitation to the
native export: plan, anchors, six takes, transcripts, gate, captions, mix, assembly, review.
What the background says in v4, in order: it's nice in here despite the rain; the tram when
it's not crowded, and the market later; a beautiful day; a corner, ten minutes; the rush being
over; and then hers, which nobody could make out. The director's note that her mouth moved
in v1 was right in five rooms, and he found the fifth after my strips had passed it; the dense strips are under `scratch/`
and the gate record in `qa/README.md`.
