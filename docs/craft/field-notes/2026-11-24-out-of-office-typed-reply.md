# OUT OF OFFICE: a typed reply instead of title cards

Source: claude-code · OUT OF OFFICE · 2026-11-24

### Text that is being written plays lighter than text that is shown
The first cut set every line as a card over its shot, with one score throughout.
The director asked for a lighter, fun feel and moved most lines into a mail
client where the reply is typed, edited and at one point deleted and replaced.
The same words became a performance with timing of its own, and the shots between
them could run shorter and without type.
**Apply:** when a film's voice is a document (a reply, a form, a list), consider
showing it being written. Keep printed type for the lines that belong to a
picture, and let one line be changed on screen if the joke is a change of mind.

### Draw the interface in code and put each keystroke on its character's frame
The mail client is a generic panel drawn with Pillow: no product name, logo or
layout from a real client. A seeded script expands "type", "enter" and "erase"
actions into one state per frame, and the same event list places a keystroke
sound on the frame each character appears. Keystrokes were sliced by onset from
one generated keyboard recording, with wide keys pitched slightly lower and a
held delete as a fast run. Sync cannot drift because picture and sound come from
one list. The director approved pace and sound on the first watch.
**Apply:** generate typing as events first, then render picture and sound from
them. Type at one or two frames per character with a longer beat after
punctuation. Nobody needs to be shown typing.

### Draw synthetic segments again at the finishing size
For the 4K master the interface and the type over the shots were drawn again at
twice the size through a small coordinate-scaling wrapper, with line breaks still
decided at the base size so the layout cannot change; only the generated takes
went through the upscaler. Text edges stay exact.
**Apply:** keep layout units separate from pixels in any drawn segment, and give
`film finish` a native counterpart for it. Do not upscale type.

### Score under one shot only, and trim a take to where its sound has a cause
The cello now plays only under the cellist, from its false start, and every
other shot runs on its own sound. One take was silent for its first three
seconds and then had distinct sounds; measuring loudness per frame against a
dense frame sheet showed which motions the sounds belonged to, and the window
was moved to where each sound had one. (The shot was later cut for pace.)
**Apply:** when a take's own sound is used, print per-frame loudness next to a
numbered frame sheet before choosing the trim. An agent that cannot listen can
still check that a sound has a visible cause.

### A recipe must not share a name with a standard-library module
A recipe saved as `email.py` broke every script in its folder that imported
NumPy or SciPy, because Python resolved the standard `email` package to it.
**Apply:** name recipes for the film's own objects (`autoreply.py`), never for a
generic noun that may be a module.
