# Production decisions

## 2026-10-30 — import and image audition

The director supplied the production spine and asked: “Stop and audition images for key shots and looks. Use the standard HTML production status page process.” The stable ID is `motion`; the release title waits until after production. The original file is preserved unchanged in the private workspace.

Keep the specified four files, the 30-second baseline, the 4:3 image on a black portrait canvas, the silent dancers, the off-camera turn, and the 7.6-second final hold. The first ordinary acceptable faces remain the cast. The image round is a candidate look for director review; no motion is submitted before that review.

Use the repository’s metered Nano Banana Pro route for the image audition. The supplied Flow and Claude Code labels describe the handoff's intended tools. This run uses Codex and the maintained Google image adapter; final credits will reflect actual tools. Motion delivery through Flow versus the maintained Veo adapter remains to resolve before motion, with provider capability and rates checked then.

Audition P1 (empty trail), P2 (couple A), P3 (couples B/C/D), F2 (entry), F3 (layered dancing), and F4 (the final tableau). Inspect each dependency before deriving the next. Carry the same scene and cast forward; reject only a concrete defect. No music, titles, or decorative lighting.

## Technical interpretations

The 7 kHz microphone filter applies to the environmental bed and foley. Add the very quiet 11 kHz electronic whine after that filter so both directions can coexist. This is an implementation interpretation, not a claim about a particular real camera.

The director decided: “Omit the cricket (recommended).” No cricket in any clip. The calculation extrapolates the chirp formula below its usual useful range; [University of Nebraska entomology guidance](https://entomology.unl.edu/sites/unl.edu.ianr.casnr.entomology/files/media/file/Crickets%20and%20Temperature.pdf) says crickets generally do not sing below 55°F. Preserve all strip temperatures. No sound has been rendered.

The moon glyph remains the requested waning gibbous with the left side illuminated. Exact percentages in the supplied brief are not yet validated at the fictional camera's location and timezone. Do not present them as measured environmental evidence. The temperatures are authored fictional telemetry.

Timestamp updates use elapsed clip time, not an inclusive endpoint label: the final sampled second of a seven-second clip is its start time plus six seconds. The final hold reaches its start time plus seven seconds. The image cadence resets at each clip's first frame and holds every image for exactly two master frames, including clips beginning on an odd master frame.

A 24 fps generated source must be sampled to 15 fps by timestamp before doubling to 30 fps; dropping every other 24 fps source frame would incorrectly produce 12 fps. Preserve the original take and source-frame map.

C4 is the longest baseline shot (7.6 seconds), despite the source reasoning calling it the shortest. The explicit beat table takes precedence.

## First image round

The first scene plate put the path into depth and lost the bright trunk in the crop; it was replaced with a sideways trail. The corrected plate keeps the foreground trunk farther inward than the sketch. The first acceptable couple A and the first B/C/D cast plate are retained. The entry study shows how much the trunk obscures the left-side arrival and remains a staging question for review.

The first F3 put the older pair outside the camera crop, and the first F4 flattened all four pairs into a row. Targeted corrections preserve faces and clothes while changing placement and depth. Earlier candidates and exact request snapshots remain in the private workspace.

Roboto Mono Bold, the brief's named fallback, supplies the data strip. The font and its license are retained privately. The static audition shows the actual camera crop and black portrait layout, with modest softness and grain. The final moving codec, exposure changes and timed eye reflections await production; no motion is generated for this audition.

The corrected F3 retains all six opening figures inside the crop and places the older couple deeper. F4 now retains all eight visible faces and sixteen eye-points with more separation into depth. Its farthest pair is still too large for the intended distance. The agent recommends keeping the cast and look, then refining the near trunk's placement and the older pair's distance after the director's audition notes. No motion anchor is marked approved.

## Motion and draft authorization

The director approved the image audition: “All looks good. Proceed with video generation. Add audio as appropriate as well. Use your own discretion and complete an entire finished draft.” The cast and infrared look are approved. Entrance staging and local finishing are delegated production decisions. The title remains deferred.

## Selected draft treatment

The native draft keeps the four-file, thirty-second structure. The agent selected the first deer and tableau takes and the second takes for both dancing scenes. The deer gives a continuous crossing glance rather than a planted stop. The first pair follows a waltz arc; the crowd includes one counter-crossing background pair and a near pair receding slightly as it crosses. These are deliberate adaptations to the returned material, preserving the ordinary-camera premise.

Tracked infrared eye returns are brief during verified near-frontal turns. The final tableau keeps all eight people and sixteen eye-points. The partly occluded woman during the first turn is left untreated because a reliable eye track could not be established. Local sound consists of distinct camera-noise and wind beds, trigger clicks, and deer hoof/leaf and exhale sounds. There is no music, speech, cricket, title or end card.

## Director trims and 4K authorization

The director reviewed draft-v3: “Excellent work.” The exact notes were “Trim C3 to start at src 1.000s (frame 30)” and “Trim C4 to end at src 4.467s (frame 134),” followed by “Then 4k upscale.” C3 uses source frames 30–209; C4 uses 0–133, with frame 134 as the exclusive out boundary. Earlier versions remain retained.

The revised cut is 776 frames at 30 fps. Audio uses the same uncompressed source ranges as the picture, without moving cues or changing gain. The first second of C3, including its original trigger click, is removed; its burned camera clock starts one second later. All recording gaps and the half-second black tail retain their original lengths.

The agent chose a local Lanczos enlargement to 2160 × 3840 to retain the authored infrared noise, compression and data strip. The 4K finish preserves all 776 frames and copies the revised native audio without another encode. The release title remains deferred.

## Release title and description

The director selected **Motion** while uploading and requested a description. The draft in `description.md` keeps the final tableau unspoiled, credits the dancers in *Carnival of Souls* (Herk Harvey, 1962), identifies the actual generation and finishing tools, and discloses the generated footage. Publication is not yet recorded.

## Publication confirmation

The director confirmed that **Motion** is published and supplied [the release URL](https://youtube.com/shorts/xw4HQtnVbqc). The final 4K cut is the release master. Preserve the approved description verbatim; the platform wording was not independently recovered. Record 2026-10-30 as the confirmation date, without inventing a platform publication date.
