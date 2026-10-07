# Hall of Memories — With one person

Complete first continuation draft delivered 2026-09-26; accepted as working
material with no notes on 2026-09-27. The user will rework the polis scenes as a
whole once the core is complete. Continue forward from this baseline.
Selected review: `data/workspace/hall-of-memories/polis-invitation-v1/edit-v1/index.html`.
It includes the new segment and both polis scenes together, in native 1080p and
smaller 720p copies, with optional captions. Technical export checks passed.
This acceptance does not lock the final look, dialogue, voices or animation.

The user accepted the preceding polis
conversation as a useful baseline, with targeted future revisions intended to
affect all stop-motion polis portions together. This does not lock a final look.
The user then requested the elder's invitation through a natural segment ending.

## Dramatic boundary

Continue immediately after “I used to ask that, too.” The elder acknowledges
that nobody knows when the last human died. The children test his certainty;
he offers something people left behind and invites them to come with him.
They rise, cross the same neighborhood and arrive at the Hall of Memories.

The closing exchange is “Where do we start?” / “With one person.” Hold all four
figures at the open threshold, ready to listen. No individual record is selected
or played, no human voice or scream is heard, and no extinction mechanism or
biological past for the elder is established. This boundary completes the
invitation while giving the next segment room for its first human experience.

## Draft dialogue

**Quiet child:** Did you find out?

**Elder:** No one knows when the last human died.

**Storyteller:** Then you don't know either.

**Elder:** Not that.

**Challenger:** What do you know?

**Elder:** They left us more than stories.

**Quiet child:** Can we see?

**Elder:** Come with me.

The children stand. Follow their walk, then reveal the Hall. No music.

**Quiet child:** The Hall of Memories.

**Storyteller:** Whose memories?

**Elder:** Billions of people. Each with a whole life.

**Quiet child:** Where do we start?

**Elder:** With one person.

The elder turns toward the open Hall. Hold on the group, then end the segment.

## Production choices

- Retain the baseline's rounded graphite puppets, glowing amber eyes, mouthless
  performances, temporary local voices and eight pose samples per second.
- Extend the persistent set east of the existing courtyard. A muted violet
  facade, pale open doorway and exact local inscription name the Hall. Rows of
  unplayed panels hint at records inside; no visual record content is invented.
- Seated dialogue, a shared rise, a lateral walking shot, the Hall reveal,
  arrival coverage and a wider final tableau. New camera positions keep active
  speakers visible; footsteps accompany the held walking poses.
- Native 1920 x 1080 at 24 fps. New segment: 46.250 seconds, 370 source poses,
  1,110 output frames. With the complete retained conversation: 86.125 seconds.
- All new dialogue, Hall architecture and movement remain first-draft choices.
  Future polis-wide revisions should address both scenes together.

Workspace: `data/workspace/hall-of-memories/polis-invitation-v1/`.
Reusable source: `tools/hall-of-memories/polis_invitation.json`,
`polis_invitation_audio.py`, `polis_invitation_render.py`, and
`polis_invitation_finish.py`. The renderer shares baseline set and puppet
construction through `polis_render.py --setup-only`.

Generated media, local ledgers, recipe snapshots and verification remain under
the ignored workspace. No new image, video or voice provider calls; $0 new
provider charges. The earlier fifteen built-in image calls retain unknown exact
cost. Preserve earlier factory work and the original conversation exports.

All 370 source PNGs and all five exported movies passed technical checks. The
context movie's decoded picture exactly equals the complete baseline followed
by the new segment. The baked animation has constant pose keys and a valid
relative audio link; active-speaker visibility passed at every speaking pose.
Visual review used contact sheets and key native frames. Dialogue was checked
for duration, non-silence and headroom; no listening or real-time playback review
is claimed. The editable animation is `animation-v1/polis-invitation-animation.blend`
under the new workspace. The last two seconds of source picture are identical.
