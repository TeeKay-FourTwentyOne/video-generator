# Runway

### Eight-second requests can return one extra frame
Two Gen-4.5 text-to-video auditions requested eight seconds and both returned
193 frames at 24 fps (8.041667 seconds), with no audio stream. Each terminal task
reported 96 credits, matching the account balance change. This is an observation
from two clips, not a promise about every Runway output.
**Apply:** preserve the native source and measure decoded frames; select an
explicit integer-frame range when exact edit duration matters.
Source: Codex · Runway API auditions · 2026-10-11

### A starting frame helped hold a crowd shot still
In VERIFY production, a side-on crowd take tracked the walkers despite a fixed
camera prompt. A new image-to-video take using that clip's opening frame, with
explicit instructions to keep the architecture in place, held the wall steady.
Local background tracking measured roughly 1.5 pixels of net movement over the
selected five seconds, compared with over 1,000 pixels in the rejected take.
This is one comparison and does not isolate the anchor from the prompt change.
**Apply:** when a fixed camera is essential, inspect the background independently
of the people; a coherent crowd can hide substantial camera movement.
Source: Codex · VERIFY production · 2026-10-11

### No eye contact requires checking the background too
The first crowd take had a background face directed toward the lens early in the
selected window. It was rejected to preserve the portrait as the first deliberate
eye contact. Every frame of the replacement's selected window was inspected in
native-resolution face crops, alongside wider context.
**Apply:** test the selected interval, including partially occluded background
faces; a contact sheet with large time gaps cannot establish the absence of gaze.
Source: Codex · VERIFY production · 2026-10-11

### Quiet realism still needs literal detail checks
A bus completed its crossing with a coherent body and an empty tail, but the
background traffic signal had implausible stacked lamps. A restrained portrait
held a closed mouth and steady gaze, but supplied two blinks when asked for one.
These were retained as raw model auditions, not approved as final film shots.
**Apply:** inspect persistent background geometry as well as the moving subject;
check exact action counts through dense frame review before selecting a window.
Source: Codex · Runway API auditions · 2026-10-11
