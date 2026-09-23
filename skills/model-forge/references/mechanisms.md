# Mechanisms for FDM — gears, hinges, snap fits, bearings, flexures, print-in-place

Read this before modelling anything that moves, meshes, flexes or snaps. Printer: Bambu Lab A1, 0.4 mm nozzle, 0.2 mm layers, PLA/PETG, **no slicer hole compensation** (so size holes in the CAD). Customers' printers are not calibrated for them: use the conservative number, and write the clearance you chose in `assumptions.txt`.
Clearance table for plain fits lives in `fdm-design-rules.md` (press 0.05–0.1, snug 0.15–0.2, free 0.25–0.3 per side, print-in-place ≥ 0.4, holes +0.2 mm). This file adds the mechanism rules. Research and sources: `vault/Research/2026-09-22-print-in-place-mechanisms.md` in the 3d-printing repo. "(rot)" = rule of thumb, no hard source.

## 1. Gears
1. Module ≥ 1.0 on a 0.4 nozzle; 1.5–2.0 for anything carrying load. Never below 1.0 (teeth fuse or snap).
2. Tooth count ≥ 13 at 20° pressure angle; ≥ 9 at 25°. Use 25° for small pinions or loaded gears (thicker root); both gears in a pair MUST share module and pressure angle.
3. Centre distance = m·(z1+z2)/2 + 0.15–0.25 mm (backlash). Zero backlash binds on FDM. Declare every meshing pair in `checks.json` `gears`; the host measures the distance and turns the pair through a tooth pitch to prove it neither binds nor skips.
4. Face width 8–12 × module (rot). Hub wall ≥ 2 mm around the bore.
5. Print gears flat on the bed (bore axis vertical, teeth upright). 5 walls / ≥ 35 % infill at the root for loaded gears — say it in the print notes.
6. Herringbone for gears printed already meshed (planetary sets, gear bearings): it self-centres and takes thrust. Spur is fine for separate gears on shafts.
7. Print-in-place meshes (printed assembled): flank clearance 0.25 mm minimum, 0.3 mm on curved/complex sets.
8. Shaft retention: D-flat (flat removes 20–25 % of the diameter, rot), hex, or a heat-set insert + grub screw. Never a plain round press fit — PLA creeps loose.
9. Ratio = driven teeth / driver teeth; state it to the customer ("3:1, output turns 3× slower").
10. Worms self-lock only below ~5° lead angle; above 12–15° expect back-driving (general machine design, not FDM-tested).
11. Build every gear with its pitch axis on the part's own origin, pointing along +Z — the host measures centre distance and turns the pair about that axis, so an off-origin gear reads as the wrong distance. A rack (straight gear) instead has its origin ON its pitch line, its length running along its own +X and its teeth pointing along +Y; the host checks it by sliding it along X against the pinion's turn, not by turning it.
12. Use `bd_warehouse.gear` (SpurGear, HelicalGear, etc.) for involute profiles; do not hand-draw teeth.

## 2. Hinges, pins, ball joints, chains
13. Separate-part pin hinge: 0.3–0.4 mm radial clearance; pin ≥ 3 mm diameter.
14. Print-in-place hinge: ≥ 0.4 mm gap all round, ≥ 0.2 mm (one layer) Z gap, cone-shaped knuckle ends (45°) so nothing bridges into the gap.
15. Lay hinge and pin axes horizontal on the bed, never vertical (a vertical barrel bridges every layer through the gap and fuses).
16. 45° chamfer (0.4 mm) on the bottom edge of every knuckle against elephant's foot.
17. Ball-and-socket: prefer a C-shaped socket that flexes open (PETG) over a printed-closed gap; socket opening faces up. A proven snap-fit ball joint models the ball and socket TOUCHING (0 mm) and relies on the plastic flexing — do not design a clearance gap into a snap-in joint (measured 22 Sep).
18. Interlocking rings / chain links: **0.7 mm** where rings rotate against each other (measured on a proven 4-ring print-in-place spinner, 22 Sep: 0.71–0.73 mm between all four rings); 0.4 mm for links that only hang and articulate.
19. Clearance grows with size: ~0.4 mm for features ≤ 20 mm, up to ~1 mm at ~50 mm for nested "impossible" objects (rot, one source).

## 3. Snap fits and living hinges
20. Cantilever strain ε = 1.5·t·y / L² (t root thickness, y deflection, L length). Allowable: PLA 2 % one-time / 1 % repeated; PETG 4 % / 2 % (conservative end of 2–3 % and 3–5 % sources). Declare every clip, catch, hook or arm in `checks.json` `loads`, with `axis` = the arm's length direction as modelled/printed (not `layers` — the host derives that itself); the host computes it.
21. L/t ratio: 8–10 for PLA, 5–8 for PETG. Fillet the root (radius ≥ 0.5 t).
22. The host derives along/across from the declared `axis`: if the arm rises more than 30° off the bed (bends across its layer lines) the allowable strain is automatically halved. Prefer printing snap arms flat or on their side so they bend within layers.
23. Retaining face ≤ 45° = opens by hand; 60–90° = permanent. Lead-in 30–45°.
24. Living hinges: PETG (or PP/TPU) only, never PLA for anything that flexes more than a few times; 0.4–0.6 mm thick, layers parallel to the bend line.

## 4. Flexures, springs, cams
25. Flexures and printed springs: PETG first; keep strain < 2 %; fix fatigue with geometry (longer beam, spread strain), not layer height.
26. Never design a spring or flexure to sit pre-loaded in storage — it creeps.
27. Cam pressure angle < 30° (rot).

## 5. Bearings and bushings
28. 608 bearing (22 × 8 × 7): pocket 22.1 mm modelled (no slicer compensation) for a press fit, 7.2 mm deep, 0.5 mm × 45° lead-in chamfer. PETG tolerates 0.05 mm tighter. State "press in with a vice" in the print notes.
29. 625 (16 × 5 × 5): pocket 16.1 mm, same rules. For other sizes: OD + 0.1 mm.
30. Printed shaft in printed hole: treat as a free sliding fit (0.25–0.3 mm per side) plus the +0.2 mm hole allowance.
31. E-clip grooves on printed shafts are unproven — prefer a printed shoulder, a cap with a screw, or a steel rod with a real e-clip.

## 6. Print-in-place and "impossible" objects
32. Default moving gap 0.4 mm (0.3 mm only if the customer says their printer is tuned); never below 0.15 mm.
33. Gyroscope / nested gimbal rings: rotation axis vertical, rings concentric with a **0.7 mm** radial gap (measured, rule 18; curved surfaces fuse below ~0.25 mm); pivots as biconic (double-cone, 45°) pins sitting in matching cone sockets with 0.4 mm gap; each ring ≥ 2 mm thick. Tell the customer to twist each ring free once cool, and that a drop of oil helps.
34. Gear bearing (planetary, herringbone): all flank clearances 0.25–0.3 mm; sun, planets and ring the same module; planet count divides (ring + sun) teeth.
35. Captive parts inserted mid-print (nut, magnet, bearing): pocket with the part's clearance, top of the part at least one layer below the next layer, pause by LAYER number (height ÷ 0.2); put the layer number and part in the print notes.
36. Horizontal holes and cavities: teardrop top (45°) or a 1–2 layer sacrificial bridge that is drilled out afterwards.
37. A print-in-place mechanism is never "proven to move" by geometry alone: say "should turn freely after a twist" and list the gaps you used.
