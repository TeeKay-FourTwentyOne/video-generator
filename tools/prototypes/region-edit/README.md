# region-edit — working prototypes

Bespoke scripts that produced `B_darkhair_manual.png` (Beckmann deck painting: blonde ->
brunette, **0 pixels changed outside her head**). Kept verbatim as the seed for a general
`tools/region-edit.py`. Paths inside are relative to
`data/workspace/beckmann-cruise-desert/` (may now be under `data/workspace-archive/`).

- `01_build_mask.py` — region-grow a mask bounded by the artwork's own dark contour lines
- `02_recolor.py` — HSV recolour of the masked pixels + pixel-diff containment proof

Run order: 01 writes `scratch/hair_mask2.npy` + a magenta overlay to eyeball; 02 consumes it.

See memory `project_region_edit_tool` for the build-out plan and the failure modes.
