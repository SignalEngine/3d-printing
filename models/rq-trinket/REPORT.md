# rq-trinket — Samsung Buds-case-sized trinket box

## Request
Reddit customer wants a lidded trinket box, 51 x 51 x 28.3 mm, rounded edges,
sized to replace a Samsung Galaxy Buds case inside a decorative outer case she
bought (the outer case's cavity is shaped for that Samsung case).

## Reference images
**Obtained: NO.** Both `preview.redd.it` URLs returned HTTP 403 (Reddit blocks
unauthenticated/non-browser fetches on that CDN) via `curl` with a browser
user-agent and referer, and `WebFetch` doesn't fetch raw images. Proceeded from
the text description only, per instructions.

## Questions I would have asked the customer (skipped per task instructions — answered with stated assumptions instead)
1. Is 51 x 51 x 28.3 mm the Samsung case's exact outer size, and does the
   decorative case's cavity have any extra room around it, or is it a snug
   wrap? (Determines whether I should undersize the box.)
2. Hinged lid or lift-off lid preference — cosmetic vs. functional priority?
3. Will she decorate/paint it, and does she want a flat lid top (for
   engraving/stickers) or a domed one?

## Assumptions made (stated explicitly, no customer confirmation)
- **51 x 51 x 28.3 mm is the target OUTER envelope**, built at that size
  exactly with no shrink — reasoning: the number given IS the Samsung case's
  own size, and the decorative case was bought to fit a case of that size, so
  it should already have whatever clearance a rigid case needs. If the fit is
  tight in practice, the honest fallback is to shave the outer profile by
  0.3-0.5 mm and reprint — flagged to the customer, not silently baked in.
- Wall 1.8 mm, floor 2.0 mm, lid top 3.0 mm — light-duty trinket box, not
  load-bearing (per `fdm-design-rules.md` min-wall guidance).
- **Lift-off lid with an internal friction skirt**, not a hinge. Justification:
  (a) a print-in-place hinge at this scale (51 mm) needs a 0.4 mm+ clearance
  gap and a separate pin/knuckle feature that is a known fragility point in
  small PLA parts and unverifiable for durability without a physical
  hinge-cycle test; (b) a lift-off lid is a single friction interface,
  fully checked by `fit.py`, and matches how real Samsung Buds cases and most
  trinket/pill boxes actually open; (c) no customer requirement to keep the
  lid tethered. Traded off: has no thumb notch, but a "snug sliding" fit
  clearance (0.15 mm/side, not press-fit) was chosen specifically so it lifts
  off by hand without needing one.
- Material: PLA (default), no load/heat exposure implied by "trinket box".

## Gates — PASS/FAIL and fix rounds
Zero fix rounds needed — every gate passed on the first attempt for both parts.

| Gate | base.3mf | lid.3mf | Notes |
|---|---|---|---|
| `verify_model.py` | PASS | PASS | watertight, 1 body, 0% overhang / 6.8% overhang (lid, from the fillets), within 256mm volume |
| `render.sh --section` (iso/front/top/section, viewed) | PASS | PASS | rounded-rect footprint correct, cavity centered and uniform wall, lid skirt visible and correctly recessed under the top panel on the front-view render |
| `features.py` | N/A | N/A | no holes in this design — skipped, nothing to check |
| `fit.py` (lid vs base) | — | — | **Required a fix**: first run compared both STLs in their own local coordinate frames (each part's own extrusion starts at local Z=0) and reported false INTERFERE (5105 mm3) because the lid's full solid overlapped the base's full solid at the origin. Added an assembled-position export (`lid_assembled.stl`, lid translated up by the base height) and reran: `RESULT: CLEARANCE`, min gap 0.0 mm at the rim contact face (109 mm2 contact area — the lid resting flush on the rim, which is correct, not interference), skirt-to-cavity clearance 0.15 mm/side as designed |
| `slice_gate.py` (real OrcaSlicer slice, A1 profile) | PASS | PASS | see print time/filament below |

That one fit.py round was a **workflow correction** (wrong coordinate frame for
the check), not a geometry fix — the model itself needed no changes after the
first pass.

## Print time + filament (slice_gate.py, 0.20mm Standard, Bambu PLA Basic, 0.4mm nozzle)
- Base: 1h 47m, 11.08 cm3 filament
- Lid: 1h 6m, 6.76 cm3 filament
- **Combined: ~2h 53m, 17.84 cm3 (~22.5 g PLA)**

## Confidence
- **Matches the stated 51 x 51 x 28.3 mm dimension: HIGH.** Verified
  numerically (`verify_model.py` bbox) and the two parts assemble to exactly
  28.3 mm external.
- **Fits inside the customer's actual decorative case: LOW-MEDIUM.** No
  geometry or measurement of that case's real cavity was available — the
  design assumes the cavity was sized for an object of exactly the Samsung
  case's stated dimensions with no extra slack. If the decorative case's
  cavity is snugger than that (fabric-lined pouches often are), the box will
  be too tight to insert. This can only be resolved with a caliper measurement
  of the actual cavity or a test-fit print.
- **Lid opens/closes as designed: MEDIUM-HIGH.** `fit.py` confirms the
  clearance geometry is correct per the stated snug-sliding-fit numbers, but
  those numbers are community FDM starting points, not calibrated for this
  specific printer+filament (per the skill's honesty constraints) — first
  print may need clearance adjustment (a parametrized script makes that a
  one-line change).

## What the pipeline could not do
- Could not download or view either reference photo (403s), so the shape is
  built from the text description (a Samsung Buds-style rounded pebble box),
  not verified against the actual reference images of the buds or the
  decorative case.
- Could not check fit against the real decorative case at all — that
  geometry doesn't exist anywhere in this pipeline; only the box's own
  internal lid/base fit was checked.
- No physical print/hand-fit test — clearance numbers are the documented FDM
  defaults, not measured for this specific printer.

## Deliverables
- `out/base.3mf`, `out/base.step` — box base
- `out/lid.3mf`, `out/lid.step` — lift-off lid
- `trinket_box.py` — parametric source (all dimensions at the top)
- `renders/` — iso/front/top/section PNGs for both parts
