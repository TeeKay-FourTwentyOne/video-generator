# Steamboat Wilhelm III — Lessons

Shipped 2026-05-28 — https://www.youtube.com/watch?v=kAsnmkXTOTU

## Iris-out via geq at 4K is viable and fast enough

`geq=lum='if(gt(hypot(X-CX,Y-CY),RMAX*(1-T)),0,lum(X,Y))'` (with matching cb/cr) renders a clean 1.0s iris-out closing at 4K in well under 5 minutes. Hard-edged circle matches the 1928 register; no soft falloff needed. Slight motion-prediction ghosting can appear on h264 CRF 18 at the iris boundary as rapidly disappearing content — visible in stills, mostly imperceptible during playback. Bump to higher bitrate or force more keyframes if it bothers.

## Off-center iris targets look "wrong" while still being mathematically right

When the iris center is in the upper half of the frame (closing on a face up there), the early-large iris circle extends past the top edge of the frame. The viewer's eye reads the visible (truncated) iris as offset downward from the actual center. This is **correct period behavior** — 1928 cartoons did this constantly — and corrects itself once the iris shrinks fully inside the frame. Don't compensate by moving the target back toward frame-center; the close-up reveal at the end is what justifies the off-center target.

## Find iris center with a crosshair-marked still, not by eye on the source

Before launching a slow 4K geq render, extract a representative frame from the source clip, draw a crosshair + dot at candidate (X,Y) via ffmpeg `drawbox`, look. Scale by 2× to 4K coords for the actual filter. Cost is one ffmpeg pass per candidate; saves a full re-render.

## ElevenLabs Music will refuse named IP, but offers a usable rewrite

A Cue B prompt referencing "Pink Panther" and "Looney Tunes" returned a `bad_prompt` 400 with a `prompt_suggestion` field containing the same instructions stripped of trademark names. Accepting the suggestion verbatim worked and produced the right musical direction. **Pattern:** when ElevenLabs refuses with a prompt_suggestion, take it — the music content was identical, only the show-name references were dropped.

## Don't trim a cue's dead air if it leaves insufficient coverage — regenerate

Cue B v1 had ~9s of quiet intro before the action got going. Trimming to skip the intro left only 14–15s of usable audio for a ~22s music bed. **The right move was to regenerate** with an explicit "no quiet intro, start with the action at the first second, build from there" instruction (and prepending "CRITICAL:" to the prompt to make it stick). Cue B v2 came back with active pizzicato from t=0 and covered the full timeline without trimming.

## For title-card edits that swap one figure but preserve layout: chain off prior frame + "paint over"

Generating a 1928-style title card via nano-banana, then asking it to "replace the LEFT figure" while keeping text/border/right figure intact: chaining off the prior generation locks pose pathologically (per [[feedback_nano_banana_chain_vs_regen]]) — but only if the prompt asks to *modify* the figure. Switching the verb to **"PAINT OVER the left-side figure with an entirely new and different mouse drawing in the same blank space"** broke the pose lock and produced the requested change while preserving everything else. Stronger language = stronger override.

## Whistle-as-character-action belongs as SFX, not in the music bed

The original brief had Wilhelm whistling "Steamboat Bill" as part of the music bed (single continuous calliope cue). When the music swap moved to a 3-cue ragtime-piano structure, the whistle had to be **extracted as its own ElevenLabs SFX layer** so it could persist as Wilhelm's character action under the new music. Vol 0.55 under the music bed at vol 0.75 reads clearly without competing. Generated via `generate_sound_effect` with `prompt_influence=0.6`; ElevenLabs handles tune-based whistling cleanly when given a named PD melody.

## Continuous music bed → 3-cue arc was the right call for a descent narrative

The brief's original conceit was a single jaunty cue running unchanged through the descent — the music's *refusal* to acknowledge the visuals as the joke. The shipped version swapped this for a 3-cue jaunty → spooky → jaunty arc because (a) the descent went to 4 separate visual registers, not 3, and (b) the new "comedic-scary" middle landed the descent more directly without being po-faced about it. The continuous-bed conceit is still musically interesting and worth trying in a future piece where the descent is simpler / the music's indifference can be the point.

## Title-card-with-music-under works better than title-card-silent

Original v11 prepended a 3.5s silent title card before music started at S1. Cue A starting under the card (fading in over 1.5s) gave the piece a more polished "1928 cartoon main-theme entrance" register. Cost is zero (Cue A's audio extends 3.5s longer anyway via atrim); benefit is significant. Default to music-under-card unless the brief specifically calls for silence.

## Cue C duck-then-recover beats cut-dead for closing VO under music

Tried both: (v12) Cue C cuts dead at 39.6s, silence, then VO at 40.0s — felt abrupt and deflated. (v13) Cue C ducks to 0.25 at VO start, holds through VO, recovers to 0.75 after, fades with iris — felt earned, kept the emotional through-line. The "music refuses to acknowledge the horror" conceit is stronger when the music **persists** under the VO, not when it cuts.

## Volume eval expression for inline VO ducking

Single-pass duck/hold/recover inside an ffmpeg filter chain:
```
volume='if(lt(t,T1),BASE,if(lt(t,T2),BASE-(BASE-DUCK)*(t-T1)/(T2-T1),if(lt(t,T3),DUCK,if(lt(t,T4),DUCK+(BASE-DUCK)*(t-T3)/(T4-T3),BASE))))':eval=frame
```
Where T1→T2 is the duck-down ramp, T2→T3 is the hold, T3→T4 is the recover ramp. Apply `volume` **after** `adelay` so `t` corresponds to video time, not cue-internal time. Combine with a final `afade=t=out:st=...:d=...` for the video-end fade.

## Workflow note: stream-copy video + remix audio = fast iteration

v12 → v13 → v14 each rebuilt only the audio mix (or, for v14, only the last 1s of video). The bulk of the 4K video was `-c:v copy`'d through. This made each mix revision a 30-second rebuild instead of a 5-minute one. **Pattern:** when the video edit is locked but the audio is in iteration, keep the video stream as a stream-copy input and rebuild audio only. For v14 the iris segment required a re-encode of just the final 1s (since the iris is a frame-by-frame filter), and the pre-iris portion was concat'd via filter_complex — slightly slower than pure stream-copy but still much faster than a full rebuild.
