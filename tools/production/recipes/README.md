# Film recipes

Film-specific local recipes kept with the code so a production can be rebuilt or
reused. Media, budgets and operation records stay in the ignored workspace.

| Recipe | Film | Purpose |
| --- | --- | --- |
| `borrowed-light-score.mjs` | Borrowed Light (Codex draft) | Original local score |
| `borrowed-light-finish.py` | Borrowed Light (Codex draft) | Local title and fades |
| `borrowed-light-fable-score.py` | Borrowed Light (Claude draft) | Original local score and foley, cues keyed to shot starts |
| `borrowed-light-fable-title.py` | Borrowed Light (Claude draft) | End title card (PIL + FFmpeg, installed font) |
| `borrowed-light-fable-socket-fix.py` | Borrowed Light (Claude draft) | Tracked, feathered repair of a re-lit prop in a locked-off shot |
| `washing-day-score.py` | Washing Day (Codex draft) | Original sparse plucks, wind and cloth; integer-frame edit cues and a pause at the pin release |
| `borrowed-light-compare-diptych.py` | Borrowed Light (comparison cut) | 16:9 diptych: two portrait films in panels, PIL text spine streamed raw to FFmpeg, timed cards and frame-exact freeze holds (prompt interludes) from `borrowed-light-compare-cards.json` |
| `borrowed-light-compare-mix.py` | Borrowed Light (comparison cut) | Alternating soundtrack: one draft's score to the transfer silence, the other's after, the first's second half under the outro; pauses across the freeze holds with a quiet air bed (`-mix.sh` is the v1 version without holds) |
