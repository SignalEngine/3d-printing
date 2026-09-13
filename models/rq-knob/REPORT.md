# rq-knob — cylindrical glass-knob replacement (Reddit, 2026-08-24)

## Request (verbatim)
"Looking for someone to make an stl file for me to print of this cylindrical glass
knob. It's 15mm height, 7mm radius, an m5 hole in one end, and a slight dome on the
other end. The hole does not need to be threaded as I'll be using a tap drill to make
the threads."

## Images obtained: NO
All three preview.redd.it URLs returned HTTP 403 Forbidden (Reddit CDN blocks
unauthenticated curl fetches on preview links; needs a logged-in session/referer
Claude doesn't have). Proceeded from the text description only, per instructions.

## Questions I would have asked the customer (Step 0, skipped per task instructions)
1. Tap size/pitch — assumed M5 x 0.8 coarse (the common default); a fine-pitch M5x0.5
   needs a different tap-drill diameter.
2. How deep should the M5 hole go? Not stated.
3. "Slight dome" — how much rise? Purely subjective as worded.
4. Blind or through hole? "In one end" reads as blind but isn't explicit.
5. Filament/colour — glass is not FDM-printable; is an opaque PLA stand-in acceptable,
   or do they want to try clear/translucent PETG for a closer look?

## Assumptions made (stated since Step 0 couldn't run)
- Material: standard PLA. A printed part cannot replicate glass — this is a
  same-shape/same-fit functional replacement, not a transparent one. Flagged as a
  pipeline limitation below.
- Tap drill: M5 x 0.8 coarse, standard metric tap-drill diameter = 4.2mm.
- Print hole compensation: vertical printed holes shrink ~0.1-0.3mm (fdm-design-
  rules.md) -> designed the hole at 4.4mm (4.2 + 0.2) so the as-printed hole lands near
  true 4.2mm and is ready for the customer's own M5 tap.
- Hole depth: 10mm blind, not specified by customer — gives generous tap
  engagement while leaving >=3mm of solid material above it under the dome.
- Dome rise: 2mm spherical cap on a 13mm cylindrical body (15mm total height) —
  a literal reading of "slight dome" with no reference photo to calibrate against.
- Blind hole, opening in the flat (non-dome) end only, as literally stated.

## Print orientation
Flat (hole) face down on the bed, dome up. Gives full 14mm-diameter bed contact,
a vertical hole axis (best straightness for the customer's tap to follow true), and
the dome is a shallow, self-supporting cap (no overhangs beyond FDM limits).

## Gates — all first-attempt PASS, 0 fix rounds against the model geometry
| Gate | Result |
|---|---|
| verify_model.py knob.3mf | PASS — watertight, 1 body, bbox 14x14x15mm, 2.05cm3, overhang 1.5%, bed contact 122mm2 |
| render.sh + view PNGs (iso/front/top/section) | PASS on visual inspection — dome shape and hole position/axis match intent, no mirrored/misplaced features |
| features.py knob.step --expect holes.json | PASS — 1 hole, dia 4.4mm design, depth 10.0mm, axis Z, face -Z (bottom), centered |
| fit.py | N/A — single part, no mating assembly |
| slice_gate.py knob.3mf | PASS — real OrcaSlicer headless slice on Bambu A1 profile succeeded |

Fix rounds needed: 1, but it was a code bug, not a geometry/design iteration:
Sphere(RADIUS) created *inside* the BuildPart context auto-unions itself at the
origin before .scale()/Pos() transforms are applied — left a stray sphere fused
at z=0 on the first run. Fixed by constructing the dome standalone outside the
builder context, then explicitly add()-ing the transformed solid. Caught by
verify_model.py's bbox output (z ranged to -7mm, impossible for the design) before
any render was needed. After the fix, every gate passed clean on the next run —
zero design-level iterations.

## Final print time + filament (slice_gate.py, Bambu A1, 0.4mm nozzle, 0.20mm Standard, Bambu PLA Basic)
- Print time: 21m 38s
- Filament: 1.14 cm3

## Confidence this matches what the customer wants: MEDIUM
Geometry (cylinder dia 14 x 15mm, M5-tap-drill blind hole in one end, domed other end)
is a direct, literal translation of every dimension the customer gave — high
confidence on that axis. Confidence is capped at medium because:
- No reference image was available to calibrate "slight dome" (rise, or whether the
  dome is closer to a hemisphere/ellipsoid than a shallow spherical cap) or to check
  whether the real glass knob has a step/shoulder, flat land around the hole, or
  chamfer detail the text description omits.
- Hole depth (10mm) and material (opaque PLA vs. their glass original) are pure
  assumptions with no customer confirmation.

## What the pipeline could not do
- Could not fetch the Reddit reference images (403 from preview.redd.it under
  unauthenticated curl) — this is an access/auth limitation, not a modelling one.
- Cannot produce a glass or glass-look material — FDM PLA/PETG is opaque or at best
  translucent, not the reference material. Said plainly rather than delivered as if
  equivalent.
- features.py's hole check is axis-aligned only and blind-hole face labels ("+Z"/
  "-Z") are a known sharp edge in its --expect format (tripped once while writing
  the check — corrected, not a model defect).

## Deliverables (this directory)
- knob.3mf — primary, Bambu Studio native
- knob.step — editable master
- knob.py — parametric source (RADIUS, HEIGHT_TOTAL, DOME_RISE, HOLE_DIA_DESIGN,
  HOLE_DEPTH all at top — trivial to regenerate for "make it 20mm tall" etc.)
- knob.stl — included though not explicitly requested, since STL was the customer's
  literal ask ("an stl file for me to print")
- rq-knob-iso.png, -front.png, -top.png, -section.png — verification renders
