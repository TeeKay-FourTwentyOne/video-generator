# Calculation and reproduction

The [implementation notes](../../tools/wavefield/README.md) describe the three
complex source amplitudes, padded Fresnel propagation, coherent cross terms,
independent numerical checks, procedural detector pulses and local sound synthesis.

The six selected material images are M01-A, M02-A, M03-B, M04-B, M05-A and M06-A.
Each pair was generated from the preceding selection and the original anatomy
reference. All twelve original images, exact prompts and selection reasons remain
in the private workspace.

The native film computes fields at 1080 by 1920 in a padded 1620 by 2880 grid.
Six complete numerical snapshots retain the individual complex branches,
coherent intensity, incoherent intensity, cross terms and phase. The calculation
notebook displays comparable intensity maps before the film's color and bloom.

The continuous picture is stream-copied into each delivery. The first draft's
prepared soundtrack was encoded once. Its metadata-only correction supplied
explicit BT.709 tags without changing decoded picture. The revised renderer
writes those tags directly and the second draft copies the first draft's audio
stream. Encoded packet and decoded PCM hashes verify soundtrack identity.

The second pass tracks the bright junction above the central opening through all
six source masks. The camera reaches scale 3.3 at four seconds and 42 immediately
before the final click. Curved strand masks resolve the close-up; 24 secondary
strands gather and disappear, and 84 Gaussian packets travel toward the junction
and are absorbed there. These amplitude changes are authored. Each resulting
complex field is still propagated numerically before evaluating interference.
Cyan, violet and amber separate overlapping branches, while colored pulse fronts
follow the click-driven phase disturbances. Both versions' numerical snapshots
and calculation notebooks remain available.

Frame-by-frame decode, audio correlation, loudness and true-peak evidence are
recorded privately. Reusing a verified soundtrack does not establish new listening.

Version 3 changes only the early camera growth: its initial increase in scale is
two thirds of v2, followed by a quintic ease back to the v2 path at frame 250.
Frames 0 through 249 are recalculated from the same wave-field model. Frames 250
through 719 are copied from v2 at a keyframe boundary. Per-frame decoded hashes
verify all 470 retained frames and all 250 new opening frames after joining.

Version 4 preserves the complete v3 picture and replaces the detector sound.
Short damped mechanical contacts supply the ticks, with no low resonator.
Brief spatial reflections diminish through the approach; the final tick is dry.
The existing quiet field-air stem stays at its original level. The six onset
samples are unchanged. The new mix is encoded once, with source correlation,
true peak, final silence and full picture identity checked separately.

The authorized 4K master resamples the finished picture to 2160 by 3840 using
Lanczos interpolation. A lossless counterpart retains the resized samples for
comparison, and the maintained finisher cuts the original integer-frame ranges
at the larger size. The wave simulation remains the original native calculation.
The full v4 soundtrack is copied without re-encoding. Frame timestamps, encoded
audio packets, decoded audio and compression fidelity are verified separately.

This is an artistic optical construction. It does not implement GRW, CSL or
Diosi-Penrose collapse dynamics. Technical verification, full listening and
director approval remain separate facts.
