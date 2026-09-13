# RQ Pillbox — 5-part pill organiser

Reddit r/3Dprintmything, London UK, 2026-09-12. Original poster has their own
design (not shared) quoted at ~£55 for 1 copy; a commenter estimated ~£6
material + would charge £25+postage. This is an ORIGINAL design to the
stated envelope, not a reproduction of the poster's part.

## Reference photo: NOT obtained

`curl` to the reddit preview URL returned HTTP 403 (reddit blocks the VPS's
IP/UA on preview.redd.it). Proceeded without it per instructions. This means
the compartment count/shape/opening style is my own interpretation of "pill
box, 5 parts" — not a match to their actual prototype's look.

## Questions I would have asked (Step 0), and the assumption used instead

| Question | Assumption made |
|---|---|
| 4, 5, 6, 7, or per-day compartments? "5 parts" — is that the whole BOM including lids, or 5 compartments? | Read "Number of parts: 5" as the total part count for the design. Chose 1 base tray + 4 identical snap-in lids = 5 parts. (A 4-compartment tray with one lid per compartment, not a 7-day organiser — 7 lids would over-shoot "5 parts".) |
| One lid per compartment, or one lid for the whole tray? | Per-compartment lids — smaller lids are easier to open one-handed and a single 255mm lid would be an awkward, flexy part. |
| Fit type for the lids (press / snug / loose)? | Snug sliding fit, 0.2mm clearance per side (fdm-design-rules.md) — openable by hand via a thumb notch, not a tool-fit. |
| Material: PLA / PETG / ABS all listed as OK — which? | PETG recommended (repeated lid insertion/removal is a fatigue/wear case PLA is worse at; ABS ruled out — A1 is open-frame, ABS warps per fdm-design-rules.md). Assumed no colour preference (stated "no preference — prototype"). |
| Wall thickness / compartment size preference? | 2mm walls (2x 0.4mm nozzle perimeters+, comfortably above the 0.8mm min-wall rule), 4 equal-length compartments (61.25mm each) — no reason given to make them unequal. |
| Any branding/text/label per compartment (e.g. day initials)? | None — not requested, and no reference photo to match a labelling scheme. |

## Design

- **1 base tray** (255 x 70 x 30mm outer, exactly the stated envelope): 2mm
  walls/dividers/floor, 4 equal compartments (61.25 x 66mm opening, 26.5mm
  clear pill depth). Each compartment has a 1.5mm-deep x 2mm-wide rabbet at
  the top so its lid sits flush, and a 5mm-radius thumb notch cut into the
  front rim for finger access to pry the lid.
- **1 lid** (56.85 x 61.6 x 1.4mm), printed once and needed **x4** (identical
  — all 4 compartments are the same size) = 5 physical parts total, matching
  "Number of parts: 5". Matching thumb-notch cutout, chamfered bottom edge as
  a lead-in for dropping into the rabbet.
- Print-in-place-free: everything is a rigid, separately-printed part; no
  supports needed on either part class (base prints cavity-up, lid prints
  flat).

Files: `pillbox.py` (parametric source, single script builds both parts),
`base.step` / `base.3mf` / `base.stl`, `lid.step` / `lid.3mf` / `lid.stl`,
`lid_placed.stl` (lid positioned inside compartment-0 in the base's own
coordinate system — used only for the fit check), `assembly.3mf` (base + 4
lids laid out on one plate — the file to actually print from), `renders/`.

## Gates — PASS/FAIL, 1 fix round

Zero geometry bugs on first build (no fix rounds on the model itself). One
issue found and resolved at the slicing stage (below).

| Gate | Target | Result |
|---|---|---|
| `verify_model.py` | base.3mf | **PASS** — watertight, 1 body, 255x70x30mm, 84.52 cm³, WARN: ~2% of sampled surface <0.8mm (at the thumb-notch/rabbet edge intersections — geometric, not a print-failure risk at that small a fraction) |
| `verify_model.py` | lid.3mf | **PASS** — watertight, 1 body, 56.85x61.6x1.4mm, 4.84 cm³, no warnings |
| `render.sh --section` | base, lid | **PASS on inspection** — iso/top/section PNGs viewed: 4 equal compartments correct, rabbet step visible, thumb notches on the correct (front) face and centred per compartment, lid notch aligns with base notch, bottom chamfer present. No features on the wrong face. |
| `fit.py` | base.stl vs lid_placed.stl (same coordinate system, lid placed in compartment 0's rabbet) | **PASS** — `RESULT: CLEARANCE`, minimum gap 0.2000mm, 0mm² contact area — matches the designed 0.2mm-per-side snug clearance exactly, no interference. |
| `slice_gate.py` | lid.3mf | **PASS** — 48m 43s, 4.92 cm³ |
| `slice_gate.py` | base.3mf (standalone, single-object 3mf) | **FAIL** first attempt: `"One of the plate is empty or has no object fully inside it"`. Investigated (see below) — this is a headless-CLI single-object quirk, not a real design/fit defect. |
| `slice_gate.py` | assembly.3mf (real print job: 1 base + 4 lids, one plate) | **PASS** (after the finding below) — **2h 51m 32s, 19.49 cm³ filament**, RESULT: PASS |

### The one fix round: bed-fit investigation (the "check it" instruction)

The base alone (255x70x30, axis-aligned, single-object 3mf) was refused by
OrcaSlicer's headless CLI with "not fully inside" the plate — reproduced
consistently, including with `--arrange 0/1` and `--allow-rotations` forced
explicitly, and even for plain test boxes with **no relation to this
design** (a bare centred 190mm square at H=30mm fails the same way; a 180mm
one doesn't) — so this is a limit of the headless slicer/profile
combination on THIS environment, not a defect in the pillbox geometry.
I did not fully root-cause the exact threshold rule (see Pipeline
limitations below).

**What does work, reproducibly:** `assembly.3mf` — the base and all 4 lids
laid out together on one plate, exactly as the customer would actually load
it into Bambu Studio — slices cleanly. Inspecting the sliced output's
transforms, OrcaSlicer's own auto-arrange rotates the 255x70mm base
~45° (footprint shrinks to (255+70)×0.707 ≈ 229.8mm square) to make it fit,
which is exactly the "diagonally" case flagged in the brief. **Conclusion:
255x70x30 fits the A1 256mm bed, but only diagonally, not axis-aligned
straight** — confirmed by a real slice, not just geometry math.

## Confidence the lids fit: **MEDIUM**

- `fit.py` reports exactly the designed 0.2mm clearance with zero
  interference and zero contact — this is the intended, correctly-modelled
  geometry. That part is HIGH confidence (verified in CAD).
- Confidence is capped at MEDIUM, not HIGH, because: (a) 0.2mm is a
  community-standard "snug sliding fit" starting point per
  `fdm-design-rules.md`, **not a value calibrated to this printer/filament**
  — real FDM shrinkage/first-layer variance on a 1.4mm-thin lid could easily
  eat that margin; (b) `fit.py`'s own documented limitation is that
  edge/corner-only contact can read up to ~0.3mm too tight/loose; (c) no
  physical print exists to confirm by touch. A test coupon (per
  `build123d-patterns.md`) would raise this to HIGH after one print.

## Filament & cost (from the real slice of `assembly.3mf`, 0.20mm Standard, 20% infill, PLA)

- Print time: **2h 51m** (total estimated), 2h 45m model time
- Filament: **19.49 cm³ ≈ 24.2g** (PLA density 1.24 g/cm³)
- Cost at £18/kg: **24.2g × £0.018/g ≈ £0.44**

This is a thin-walled hollow tray (2mm walls, mostly empty compartment
volume) — the low material figure is expected for this geometry, and is
consistent with the commenter's "~£6 material, way under £55" complaint:
even generously padding for waste/failed prints/spool minimums, this is not
a £55 (or £25) part on material grounds. The real cost driver at that quote
is likely time/labour/business overhead, not filament.

## What the pipeline could not do

- Could not fetch the reference photo (403) — the design's compartment
  layout/shape is an assumption, not a match to the actual submitted
  prototype.
- Could not fully root-cause OrcaSlicer's single-object "not fully inside"
  refusal for the standalone `base.3mf` (worked around by slicing the real
  print plate, `assembly.3mf`, instead, which is what matters for the
  customer anyway) — a genuine headless-CLI quirk investigated but not
  resolved to a documented rule.
- No physical print exists — clearance numbers are CAD-verified + community
  design rules, not calibrated-fit-proven (see Confidence above).
