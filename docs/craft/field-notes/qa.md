# QA tooling field notes

Gate: `../clip-acceptance-gate.md`. Tools: `tools/frame-qa.py`, `tools/anchor-drift.py`,
`tools/clip-qa.py`, `tools/clone-check.py`, `tools/seam-check.py`.

### The scripts bill the Anthropic API and log it
Each call logs token usage to `data/cost-ledger.jsonl` through `tools/costlog.py`;
that file is the evidence for reconciling a QA allowance in the production ledger.
At Sonnet 5.5 prices a clip scan costs about one to two cents, a three-image
frame-qa about four. They resolve `data/config.json` relative to the repository
(since 2026-10-03; before that they had to run from the repository root).
Source: claude-code · 2026-06; Borrowed Light · 2026-10-03

### Tell clip-qa what must be absent
It assumes an occluded or early object was always there unless told the surface
is empty; naming "no second lamp, no gripper may enter" flips a silent pass into a
flag. `clone-check --expected` is an integer subject count.
Source: claude-code · Mine Too · 2026-06; Borrowed Light · 2026-10-03

### The strips are the arbiter, never the confidence
clip-qa over-flags face morphs in held two-shots and motion blur; clone-check gave
three of three false high-confidence claims in heavy-splash windows and its
rule-out prose fabricated detail. Its true positives are dry-land cross-frame
moves, which eyes and clip-qa miss.
**Apply:** inspect the saved strip and full-resolution crops of the flagged window;
never auto-reroll and never auto-dismiss.
Source: claude-code · Personal Best, Mine Too · 2026-06 to 2026-08

### frame-qa reports hidden features as failures
A slit on the far side of a turned head, a scratch on the hidden panel and a
second arm behind the body were "fail" and "partial"; read the notes before a reroll.
Source: claude-code · Borrowed Light · 2026-10-03

### Model replies can be malformed JSON
Three paid frame-qa calls were lost to a stray quote inside a note before the
shared lenient parser (`tools/qa_json.py`).
Source: claude-code · Borrowed Light · 2026-10-03

### Skip the general scan for director-reviewed clips; keep clone-check for motion
When the director watches every clip, clip-qa's general scan can be skipped;
clone-check still runs on any shot with subject motion.
Source: claude-code · 2026-08

### Contact sheets are the fastest honest look
`select='not(mod(n,8))',scale=270:480,tile=4xN` gives a readable eight-second take
in one image; dense strips of the flagged window at full resolution settle the call.
Source: claude-code · Borrowed Light · 2026-10-03

### Older background manifest writers clobber edits
Legacy tools that rewrite a manifest from the background silently revert
concurrent edits; merge on save and re-verify trims afterward.
Source: claude-code · 2026-09

### The dense strip settles what clip-qa names
clip-qa called a second sheet emerging at a roof ridge "a fragment of the first" and
a sheet's tail leaving frame "a detached blob"; it called a real hand a hand. Each
flag was resolved by a strip of every fourth to sixth frame across the window at
300 px width: two were story, one was a defect confined to fifteen frames and cut.
**Apply:** keep the tool's timestamps, look at the window, and decide from the frames.
Source: claude-code · Washing Day · 2026-10-03

### A per-frame motion-energy table is a free join planner
Mean absolute frame difference on a 270 px grey proxy (numpy over an FFmpeg raw
pipe) over the first clip shows where motion is still busy; the continuation anchor
chosen from the table passed seam-check at the first try.
Source: claude-code · Washing Day · 2026-10-03

