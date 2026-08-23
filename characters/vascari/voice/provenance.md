# Vascari voice — clone provenance

**Current voice:** `sDEuoCGIPass1GN7PF1I` — "Vascari (Lodger native S2 - southern)".
**Status: APPROVED + LOCKED (Stephen, 2026-08-22: "S2 is good. Let's lock it.")** This is
Vascari's voice for dub-rescue and any off-camera use; changes need Stephen's sign-off
(casting tier). On-camera dialogue stays Veo native with the locked drawl descriptor.

Samples: S8 retake read + X1/X4/X6 from the **round-3 hard-southern harvest** (~18s voiced):
descriptor "warm North Carolina drawl, soft country vowels, gentle Southern cadence" AND
southern-idiom lines (contractions, "much obliged" — round-2's formal diction was itself
pulling reads aristocrat). Tightest harvest cluster of any round (X mutual 0.81–0.86;
X1 0.783 / X4 0.763 / X6 0.736 vs S8), all word-perfect. Auditions embedded 0.74–0.79 vs S8
— a deliberate trade of a little identity-closeness for drawl and body, confirmed by ear.

Final-round loser **S (pure S8 seed)** `GaYp1F2yp0nf3JlN7dRw`: closest identity embeds
(0.83–0.86) but less southern; deleted (recreatable from `samples/01_s8_good_evening.wav`).
**Round-2 candidate C** `h7bodkuTlJNvppahDqA2` (S8+W1/W5/W6): Stephen picked S over it; deleted.

## The accent lesson (why there were two harvest rounds)

Round 1 reused S8's original descriptor — "*a low, faintly accented voice, old-world
courtesy*" — and Veo read "faintly accented" as **European aristocrat**. The S8 gen itself
had just happened to land a young Southern read. Stephen rejected round-1 candidates A
(`isxGTIm1uVv3XsRtfKZv`) and B (`TTXSb9lX7C9vVLDc7pSn`); both deleted from EL.
**Descriptor now locked in `character.json`:** "a young man's low, unhurried voice with a
soft North Carolina drawl, courteous in an old-fashioned way" — use it for ALL future native
dialogue gens too, or they'll drift the same way. (Same lesson as Cora: name the region;
never leave accent implicit.)

Round 2: same recipe (S8 anchor `refs/S8_first.png`, VASCARI_LOCK verbatim, rain-stopped
quiet staging, 6 × 8s Quality, ≈$6.2) with the Southern steer. All six word-perfect, no RAI.

## Sample files (`samples/`)

| file | origin | used by |
|---|---|---|
| `01_s8_good_evening.wav` | Ep1 S8 retake (the reference) | S + S2 |
| `09_x1_come_long_way_southern2.wav` | round-3 X1 (0.783 vs S8) | S2 |
| `10_x4_pay_month_ahead_southern2.wav` | round-3 X4 (0.763) | S2 |
| `11_x6_much_obliged_southern2.wav` | round-3 X6 (0.736) | S2 |
| `02–05_*` (V1/V2/V3/V5) | round-1 harvest — REJECTED (European drift) | none (kept for record) |
| `06–08_*` (W1/W5/W6) | round-2 harvest — superseded with C | none (kept for record) |

Unused spares (W2/W3/W4, X2/X3/X5) + all raw takes:
`data/workspace/lodger-ep01/scratch/voice-harvest-vascari{,-v2,-v3}/`. S8 gen-1 also
excluded (0.770 vs retake, borderline; Stephen scoped to the retake read only).

## Auditions

`data/workspace/lodger-ep01/audio/clone-vascari/` — per candidate (S, C): D1 self-check
(plain), D3 swipe-line dub-preview ("One condition…", ominous profile), long read
("I have seen Vienna…"). Raw W-take wavs are the accent ground truth for the harvest.
