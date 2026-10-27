# Coming Attractions

[Current production record](README.md).

A vertical short, 9:16, about fifty-five seconds. One movie theater, one seat, four
decades, and the previews that played before the feature every time.

## The film

A movie palace, 1943. The house is filling: hats, coats, a sailor standing to let a
young woman edge along the row to her seat. The crowd is bright and loud. The lights
go down and the screen shows the old swirl card: *Coming Attractions*. A newsreel:
troops on a boulevard, bombers in formation, a city under searchlights. The crowd
goes silent.

Cut back to the same seat. The same woman, but the year is 1973: long hair, a suede
jacket, orange seats, a popcorn bucket, laughing with a man with a moustache. The
screen: a trailer-voice over a gas line a mile long. "By 1980 the pumps may run dry
for good." The row goes still.

Cut back. 1999: a highlighted bob, a track jacket, blue seats, a giant soda. The
screen: a control room of monitors and a city grid going dark. "At midnight the
computers that run our world may simply stop." Still again.

Cut back. 2026: her phone glowing in her lap, a bearded man leaning in to show her
something. The screen's light changes. The preview arrives in her own format this
time, full frame, vertical: an empty office at night, a man at a kitchen table lit by
a laptop. "This year the machines learned to do your job. By 2030, half the jobs in
the country are gone." Then we are no longer watching her. We are in her seat. We
look left: the bearded man, jaw set. We look right: an older woman with her hand at
her mouth. Back to the screen. "What will you do, when there's nothing left to do?"
The screen goes white.

The white is daylight. The theater doors open and the audience walks out into a
bright afternoon a few years from now. The same woman shades her eyes and smiles.
Nobody is in a hurry. It is a weekday, two in the afternoon, and everyone has the
afternoon off. Trees along the boulevard, people on benches, a slow tram, a clear
sky. The film fades up to white.

## What the piece is

Every generation has sat in the dark and watched the coming attractions of its own
fear: war, scarcity, the millennium bug, the machines. Each preview was true enough
to silence a room. The feature was always life, and it kept playing. The ending does
not argue that the fears were silly. It answers the last question literally: when
there is nothing left to do, people go to the matinee and walk out into the sun.

The AI fear shown is specific and present: work and its disappearance. The film does
not visualise extinction. That is a decision of the brief, not a budget limit.

## Form

- 1080 x 1920, 24 fps, photoreal, locked-off camera in every shot, human-scale frames.
- The audience is seen from the screen's side, low, looking up a raked house. One
  woman in the same centre seat in every era, her face lit only by the screen. The
  eras change on the cut back from the screen: hair, wardrobe, the seat-mate, the
  upholstery, the snack, the colour of the light on her face.
- The screen content is letterboxed inside the vertical frame and widens with the
  decade: 1.37:1 black-and-white newsreel (1943), 1.85:1 faded colour (1973),
  2.39:1 scope trailer with broadcast-video texture (1999), then the 2026 preview
  breaks the band and fills the whole vertical frame. The coda is also full frame,
  in daylight: the world is wider than any screen.
- Period title and preview cards are rendered locally in each era's typography:
  the 1943 swirl card carries the film's title; 1973 and 1999 get one date card
  each; 2026 gets the trailer's intertitles and the white-out.
- Native Veo sound on every audience shot (the murmur, the hush, the seats). Four
  short narration lines from ElevenLabs, one per era, each in that era's announcer
  register, band-limited to the era's playback. Era music cues and effects from
  ElevenLabs. A warm, simple cue carries the coda.

## Shot plan (intent)

| Shot | Era | Beat | Source |
| --- | --- | --- | --- |
| S01 | 1943 | The house fills; she edges along the row past the sailor; both sit; the lights dim | Veo, 8 s, native audio |
| T00 | 1943 | *Coming Attractions* swirl card, projector clatter, brass fanfare | local |
| N1 | 1943 | Newsreel: troops on a boulevard, bombers, searchlights | Veo 16:9, treated to 1.37 B&W |
| S02 | 1943 | She and the sailor, silenced by the screen | Veo, 8 s, native audio |
| S03 | 1973 | Laughing with the moustache man, popcorn; the light changes; they go still | Veo, 8 s, native audio |
| C2 + N2 | 1973 | Date card, then the gas line; "by 1980 the pumps may run dry" | local + Veo 16:9, treated to 1.85 |
| S04 | 1999 | The track jacket, the giant soda; the light changes; still | Veo, 8 s, native audio |
| C3 + N3 | 1999 | Date card, then the control room and the grid going dark; "at midnight the computers may stop" | local + Veo 16:9, treated to 2.39 |
| S05 | 2026 | Phone glow, the bearded man leans in; the light changes; she lowers the phone | Veo, 8 s, native audio |
| N4a, N4b + cards | 2026 | Empty office at night; a man at a kitchen table; trailer intertitles | Veo 9:16 full frame + local |
| S06, S07 | 2026 | Her point of view: left to the bearded man, right to the older woman, keeping the wide shot's left and right | Veo, 6 s each, native audio |
| C4 | 2026 | "What will you do, when there's nothing left to do?" then white | local |
| S08 | near future | The doors open; the audience walks out into a bright afternoon; she shades her eyes | Veo, 8 s, native audio |
| S09 | near future | The boulevard at two in the afternoon; benches, trees, a slow tram, the sky | Veo, 8 s, native audio |

Generated takes are raw material; the edit uses the clean ranges. Every audience take
is planned to give two beats, the chatter before the preview and the stillness after
it, with the screen content cut between them.

## Ideas offered by the agent

- One face across four decades, rather than four strangers. The audience is always
  us. It also makes the era changes land on the cut as a single joke repeated.
- The widening letterbox, and the 2026 preview arriving full-frame, in the viewer's
  own vertical format.
- Reading post-scarcity as a weekday matinee: the answer to "what will you do" is
  the afternoon off. No flying cars.
- The piece starts in the dark and ends on white, not black.

## Status

Planned 2026-10-25. Shot plan, prompts, image requests and local card recipes are
prepared; generation waits on the director's budget authorization.
