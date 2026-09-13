# RQ-Trophy — "CONGRATULATION" word trophy

Reddit request, 2026-09-11: reprint a word-trophy design with the word changed
to "Congratulation" (no s), optional personalized line along the base,
~150x150x25-50mm, must keep the overhanging-last-letter look, must stand
stably, review-before-print requested.

## Reference image
**Obtained: NO.** `curl` to the `preview.redd.it` URL returned HTTP 403
(hotlink/geo-blocked from this VPS) both plain and with a browser
User-Agent + Referer. Built an original design from the text description
instead, per the task's fallback instruction.

## Questions I would have asked (not asked -- task requires proceeding on
stated assumptions)
1. What should the personalized base line actually say? (name, date, event?)
2. Any preferred print color / two-color split between word and base?
3. Is a flat wall-plaque mount needed, or free-standing only (assumed
   free-standing, matches "print it out ... as is")?
4. Do they want the exact reference font/style, or is a bold sans (used here)
   acceptable?

## Assumptions made (stated explicitly)
- **Personalization text**: no content given -- used the literal placeholder
  `PERSONALISED TEXT HERE`, debossed on the base front. Swap by editing
  `PERSONAL_TEXT` in `trophy.py` and re-running.
- **Word "CONGRATULATION" (14 letters) cannot fit on one or two lines at a
  readable height within a 150mm-wide envelope** -- the math: legible bold-sans
  characters are roughly as wide as they are tall, so N characters at width W
  cap out around H~W/N tall. Two lines (worst line 8 chars) forces ~19mm cap
  height and a total design ~63mm tall -- far short of the 150mm target. Split
  the word across **4 lines** (`CONG`/`RATU`/`LAT`/`ION`) instead, giving
  ~29.5mm cap height per line and a total height/width that actually hits the
  150mm target in both axes. Documented and justified in `trophy.py`'s header
  comment too.
- **The literal reference photo's single-line "overhanging T" motif doesn't
  map 1:1** onto a word that doesn't end in T and needs 4 lines. Recreated the
  *structural feature* instead: the final letter of the word ("N", end of
  "ION") is cantilevered ~10mm past the visible edge of the base foot -- the
  same "last letter hangs off the edge" look -- rather than forcing a literal T.
- **Engineering addition not visible in the reference**: stacking 4 lines with
  gaps between them means each line needs its own support down to the base, or
  it's a floating unprintable shell. Added a thin (6mm) backing panel behind
  all four lines, with a shallow (~6 deg from vertical, self-supporting)
  diagonal gusset on its right edge that carries the overhanging "N" without
  needing print supports. This panel is set back behind the raised letters and
  reads as a plain slab from the front/3-quarter view; visible as a flat back
  on a straight rear view. This is the one place the design diverges
  structurally from "as is" -- flagged because a true free-floating
  cantilevered letter (nothing behind it) would either need print supports or
  would snap along a layer line per the FDM design rules (layer lines are the
  weak direction).
- Material: PLA (default per design rules -- this is a visual/display piece,
  indoors, no load).
- Font: Liberation Sans Bold (bold sans on file; the reference's exact
  typeface is unknown since the image never loaded).

## Gates -- final status
All run against `trophy.3mf` / `trophy.stl` in this directory.

| Gate | Result | Notes |
|---|---|---|
| `verify_model.py --bodies 1` | **PASS** | watertight=True, winding=True, bodies=1 (letters, panel, gusset and foot all fused into one connected solid -- no floating shells), euler=2, bbox 145x46x151mm, volume 217.7cm3, overhang>45deg=6.2%, bed contact 3773mm2. No thin-wall warning (font strokes at this scale are well above the 0.8mm min wall). |
| `render.sh --section` (iso/front/top/section/iso-rear viewed) | **PASS** | Confirmed: word reads "CONGRATULATION" top-to-bottom correctly across 4 lines, final "N" visibly overhangs the base foot's right edge, base front carries the personalization line, section shows a solid interior with no voids/overlap artifacts. |
| `slice_gate.py` (real OrcaSlicer A1 slice) | **PASS** | See print stats below. |
| `features.py` | N/A | No holes in this part (no fasteners/mating features). |
| `fit.py` | N/A | Single body, nothing mates to it. |

### Fix rounds during build (3 iterations before all gates passed)
1. First build: bounding box came out with negative X/Z (letters and panel
   mis-transformed via a bad `Pos`/`Rot` composition) -- rewrote to sketch
   letters and panel directly on `Plane.XZ` instead of rotating an XY sketch.
2. Second build: `Text()` default alignment is centered, not left-anchored --
   my width-based positioning math assumed a left-anchored origin, producing
   a huge negative X offset. Fixed by passing `align=(Align.MIN, Align.MIN)`.
   Also found the panel/letters/deboss extrude directions were inverted (sign
   convention on `Plane.XZ` extrusion is opposite to what I assumed) --
   letters were extruding backward into the foot instead of forward, and the
   deboss text was extruding into open air instead of into the base. Fixed
   both signs; verify_model then passed with bodies=1.
3. Third build: line-height math used `bounding_box().size.Y` (near-zero,
   the sketch's own thickness) instead of `.size.Z` (the actual glyph height
   on this plane) -- all 4 lines landed on top of each other near the base.
   Fixed to `.size.Z`; render then showed the four lines correctly stacked,
   but in the wrong reading order (last word at top). Reversed the stacking
   loop so "CONG" is on top and "ION" (with the overhang) is at the bottom,
   near the base -- matching normal reading order and putting the overhang
   near its support.

Each fix was caught by actually looking at the rendered PNGs, not by the
mesh-only checks -- verify_model.py PASSED even on the broken second attempt's
underlying geometry (it was watertight) -- consistent with the skill's warning
that geometric validity is not correctness.

## Final print time + filament (Bambu A1, 0.4mm nozzle, 0.20mm Standard,
Bambu PLA Basic -- from `slice_gate.py`, a real headless OrcaSlicer slice)
- **Estimated print time: 15h 14m 45s**
- **Filament: 97.42 cm3** (~122g at PLA density -- the 270g figure in
  verify_model's own estimate is a 100%-infill upper bound, not the sliced
  estimate)
- Not checked: whether OrcaSlicer's default profile auto-added supports
  under the cantilevered "N" -- the gusset is well within the self-supporting
  angle (~6 deg from vertical, vs. the ~45 deg FDM limit) so it shouldn't need
  any, but I did not open the sliced preview to confirm zero support material
  was generated. Flagging this as unverified rather than claiming it.

## Confidence it matches what the customer wants: **MEDIUM**
Reasons:
- Correctly carries over the two things they explicitly called out: the word
  swap ("Congratulation") and the overhanging final letter, plus adds the
  requested personalization line, at close to their stated 150x150x~30mm
  envelope (145x151x46mm bounding box -- the 46mm Y figure includes the
  10mm raised letters + 6mm panel projecting off a 30mm-deep foot, i.e. the
  footprint that sits on the table is 130x30mm, well inside their 25-50mm
  depth range).
- Lowered from HIGH because: (a) the reference photo was never actually seen,
  so the base proportions, letter style, and overall "shape" are inferred
  from the text description only, not matched pixel-for-pixel; (b) the word's
  length forced 4 stacked lines instead of the reference's implied single
  line, which is a real deviation from "print this as is with a different
  word" -- this is the biggest gap between what was asked and what was built;
  (c) the personalization text content is a placeholder, not their actual
  wording.

## What the pipeline could not do
- Could not fetch the reference image (403 from `preview.redd.it` off this
  VPS) -- no way to compare the built shape against the actual reference
  contours, font, or base style. Everything about matching the original
  design's specific look is inference from the text description, not
  verification against the source.
- Could not get the customer's actual personalization text (task disallows
  asking) -- placeholder used, needs a one-line edit + re-run before printing.
- Did not verify whether the slicer's auto-support setting would place any
  support material under the cantilever in practice (see above) -- the
  geometry is self-supporting by design, but that specific check wasn't run.
