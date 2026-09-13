# 10" 1U rack bracket for Netgate 2100

Reddit request (r/3Dprintmything, 2026-08-17): a 10" 1U mounting bracket for a
Netgate 2100, because the only existing one is UK-only and bundled with a
device purchase. (Same post also wanted brackets for a StarTech eSATA PCIe
card in a Lenovo M920x — out of scope, not addressed here.)

Autonomous run: no live customer to interrogate, so Step 0 questions are
answered with a stated assumption instead, per instructions.

## Dimension sources

| Fact | Value | Source |
|---|---|---|
| Netgate 2100 W x D x H | 172.7 x 108 x 42.2 mm | shop.netgate.com/products/2100-base-pfsense, corroborated by itandgeneral.com/pfsense-uk/netgate-2100 |
| Netgate 2100 weight | not published | checked shop.netgate.com, itandgeneral.com, Netgate manual PDF — none list it |
| Netgate 2100 ports | WAN (RJ45/SFP combo) + 4x LAN, USB2, mini-USB console, power, reset — all on one "rear" face; front face is LEDs only | docs.netgate.com/pfsense/en/latest/solutions/netgate-2100/io-ports.html |
| Netgate 2100 wall-mount keyhole spacing | 140 mm, bottom of unit | docs.netgate.com/pfsense/en/latest/solutions/netgate-2100/wall-mount.html |
| 10" mini-rack hole-to-hole spacing | 236.525 mm | github.com/geerlingguy/mini-rack, mini-rack.jeffgeerling.com |
| 1U height | 44.45 mm (same as 19" standard) | same source |
| 10" panel nominal width | 254 mm (10 in) | standard definition, cross-checked against the mini-rack doc's "~220mm max horizontal clearance" figure |

## Questions I would have asked the customer (answered with assumptions instead)

1. Netgate 2100 weight? Not published anywhere I could find. Assumed <=700 g
   (typical for a small fanless ARM box) and designed the joints with margin
   well beyond that (M4 bolted joints + continuous PLA side walls).
2. Do you have a 10" rack rail with round/square holes, or cage nuts?
   Assumed a plain round-hole rail and put an M6 clearance hole (6.5 mm) at
   each ear per the brief's own suggestion ("M6 or rack-standard"). If the
   rail actually uses cage nuts or a different screw size, the hole diameter
   is one parameter (RACK_HOLE_D) to change and re-run.
3. Is the rail front-only, or is there a rear rail too? Assumed front-only
   (typical for small/light 10" mini-racks) — this design is a front-mount
   cantilever shelf, not a 4-post tray.
4. Do you want the Netgate's own wall-mount keyholes used to bolt it down?
   Not used. The keyhole positions are documented for wall mounting only, and
   nothing published gives the exact screw type/thread expected in them, so a
   generic strap/rail retention was used instead (works regardless of the
   unit's own mounting hardware).

## Design

Three parts, 10" mini-rack standard, 1U:

- ear_right.step/.3mf, ear_left.step/.3mf — front rack ears. Each has one
  M6 clearance hole (6.5 mm, axis horizontal/front-to-back, matching a real
  rail's screw direction) at the 236.525/2 = 118.26 mm rack-hole position,
  and a foot with two M4 clearance holes (4.5 mm, vertical) that bolt up into
  the tray.
- tray.step/.3mf — an open channel (side walls 12 mm tall, floor 3 mm) sized
  180 mm inner width (172.7 mm device + 3.65 mm/side clearance) x 130 mm
  deep, open front AND back so the Netgate's ports are reachable from either
  end regardless of which way it's installed. 4 ventilation slots under the
  device footprint, 2 strap slots (for a zip-tie or velcro strap over the top
  of the unit — belt-and-braces retention since the device's own mounting
  hardware isn't used).
- Assembly: ear feet bolt to the underside of the tray's front end with 2x M4
  bolts each (nut or heat-set insert), tray then rests on the ear feet; M6
  (or rail-appropriate) screws through the ears into the rack rail.

## Gates — PASS/FAIL and fix rounds

All three parts went through 2 fix rounds before final PASS on every gate.

### Round 1 bugs found and fixed
1. verify_model.py FAIL (tray): non-manifold — a mounting tab was unioned
   onto the tray with a coincident face (zero overlap). Fixed per
   build123d-patterns.md golden rule: overlap unioned boxes by 0.1 mm instead
   of sharing an exact face.
2. verify_model.py FAIL (tray): bounding box 256.52 mm exceeded the 256 mm A1
   build volume — a tab reached too far outward. Fixed by pulling the tab
   back to the flange's inner edge only.
3. Render showed no holes at all on the ear (features.py found only 1 of 3
   expected holes, with a wrong depth/position). Root cause: build123d's
   extrude() off Plane.XZ in this environment extrudes in -Y, not the
   assumed +Y — a convention not stated in the skill's reference docs. Every
   subsequent Locations() coordinate computed against an assumed 0..N range
   was therefore wrong. Fixed by measuring the actual post-extrude bounding
   box and computing all hole/feature offsets from the measured origin
   instead of an assumed one — done for both the ear and the tray.
4. A rotated-cylinder subtract built via algebra (Pos(...) * Rot(...) *
   Cylinder(...)) inside a BuildPart context double-added geometry (the
   Cylinder() constructor auto-registers itself into the part at creation
   time, before the outer transform is applied). Fixed by using
   Locations(Location(pos, rotation)) + Cylinder(..., mode=Mode.SUBTRACT)
   directly, the correct/safe builder-mode pattern (verified against an
   analytically-known expected volume before trusting it on the real part).
5. Two of the tray's M4 holes landed under the 12 mm-thick side wall instead
   of the 3 mm floor, producing accidental blind holes where a through hole
   was intended (features.py caught this precisely — reported depth 3.6-5 mm
   / face=-Z instead of through Z). Fixed by repositioning the hole
   X-coordinates onto the floor, clear of the wall band.
6. verify_model.py WARN: ~1% of sampled surface under the 0.8 mm min-wall
   guidance — a strap slot notched into the side wall, leaving ~0.5 mm of
   wall locally. Fixed by narrowing/repositioning the strap slots clear of
   the wall.

### Round 2 — pipeline limitation found
7. slice_gate.py FAIL (tray only): mesh watertight per verify_model.py and
   trimesh directly, but OrcaSlicer's headless CLI refused to produce gcode
   (return -50) for the ~220 mm-wide tray (tray body 186 mm + tabs reaching
   out to the ear positions). Bisection testing with plain parametric boxes
   showed this threshold is not a clean function of width, depth, diagonal,
   or footprint area — e.g. a 220x50mm box sliced fine, 220x51mm did not; a
   190x130mm box sliced fine, a 200x100mm box (smaller area) did not. This
   looks like an instability/bug in this OrcaSlicer build's headless
   auto-arrange, not a real "doesn't fit the 256 mm bed" constraint —
   confirmed by testing much larger objects (160x160, 190x130) that sliced
   fine. Fix applied: redesigned so the tray itself never needs to be wider
   than its own 186 mm body — the ear's foot was lengthened (25 mm -> 40 mm)
   to reach in under the tray's native floor instead of the tray growing a
   tab out to meet the ear. Final tray bbox: 186 x 130 x 12 mm, confirmed
   slice_gate.py PASS.

### Final gate results (after fixes)

| Part | verify_model.py | render.sh (visual) | features.py (holes) | fit.py | slice_gate.py |
|---|---|---|---|---|---|
| ear_right | PASS (watertight, 1 body, in-volume) | PASS — hole on correct face, correct axis, L-bracket shape confirmed | PASS — 3/3 holes match expected diameter/axis/face | PASS — flush 0-gap contact with tray, no interference | PASS — 1h 25m 51s, 7.43 cm3 |
| ear_left | PASS | PASS (mirror of right, confirmed) | PASS — 3/3 | PASS — flush 0-gap contact with tray, no interference | PASS — 1h 25m 19s, 7.43 cm3 |
| tray | PASS (watertight, 1 body, in-volume, no thin-wall warning) | PASS — vent slots, strap slots, mounting holes all on correct faces | PASS — 4/4 holes match expected diameter/axis/face | PASS — flush 0-gap contact with both ears; device envelope test shows clean clearance | PASS — 6h 32m 49s, 44.92 cm3 |

Device-fit check: a 172.7x108x42.2 mm envelope box (exact Netgate 2100
dimensions) placed inside the tray's inner cavity, resting on the floor, was
run through fit.py against the tray — result CLEARANCE, 0 interference,
matching the intended 3.65 mm/side gap. Also checked in 3D that the ear feet
(which sit underneath the tray floor in the assembly) do not intersect the
device envelope (which sits on top of the floor) — no overlap in Z.

## Print summary

- Total: ~128 g PLA (ear x2 approx 20.4 g each, tray approx 87.7 g), approx
  9h24m combined print time on the A1 (0.4 nozzle, 0.20 mm Standard, Bambu
  PLA Basic) — ears 1h25m each, tray 6h33m (large flat panel, default
  full-density top/bottom solid layers over a big footprint; a
  lower-infill/faster process preset would cut this significantly if speed
  matters more than strength margin here).
- Print orientation: both ears print foot-down as modeled (self-supporting,
  no orientation change needed) — the M6 rack hole prints horizontally
  through the standing flange (minor top sag expected on a clearance hole,
  acceptable; ream if snug). The tray prints floor-down, walls up, fully flat
  and self-supporting.
- Suggested settings: 0.2 mm layer, 3-4 walls, 25-40% infill (functional
  bracket class per fdm-design-rules.md); brim not needed (bed contact area
  is generous on all three parts).
- Hardware needed (not printed): 2x M6 rack screws (size per the customer's
  actual rail), 4x M4x12 bolts + nuts (or heat-set inserts in the ear feet),
  1x zip-tie or velcro strap.

## Confidence

- Fits the 10" rack: HIGH. The 236.525 mm hole spacing and 44.45 mm 1U
  height are well-documented community/industry-standard figures with a
  citable source, and the ear geometry was verified numerically
  (features.py) to have the rack hole at exactly that position.
- Fits the Netgate 2100 device: MEDIUM-HIGH. The device's W/D/H are
  corroborated by two independent sources and match to the mm, and the
  3.65 mm/side clearance was checked geometrically (fit.py, clean clearance,
  no interference). Docked from "high" because: (a) device weight is
  unverified/assumed, so the strap/rail retention hasn't been load-tested
  even virtually; (b) the port-side assumption (ports on one "rear" long
  face, confirmed by Netgate's own I/O-ports doc but without a labeled
  diagram of which physical edge) is mitigated by design — the tray is open
  at BOTH ends, so this doesn't actually matter for cable access either way
  — but it's still an assumption about the device I could not independently
  confirm with a photo/caliper.
- No physical unit was calipered or test-fit — this is a from-spec design
  based on published dimensions, not a print-and-check iteration; the
  standard tolerance-coupon caveat applies if a snug/press fit mattered here
  (it doesn't — this is a loose clearance fit by design).

## What the pipeline could not do

- Could not resolve the OrcaSlicer headless slice failure's root cause (item
  7 above) — worked around it by keeping all delivered parts under the
  apparent safe threshold rather than diagnosing the slicer's internal
  arrange logic, which is out of scope for a CAD model job.
- Could not verify the Netgate 2100's weight or exact port-panel photo — no
  official spec sheet published it, and there's no physical unit or customer
  to caliper/photograph it (this is an autonomous run with no live customer,
  per the task).
- chamfer() on the tray's bottom edges failed (ChFi3d_Builder: only 2
  faces — the vent/strap cutouts made the bottom face's edge topology too
  irregular for a reliable edge selection) — left un-chamfered; this is
  cosmetic (elephant's-foot squish on a flat, non-mating floor face), not a
  functional gap.
