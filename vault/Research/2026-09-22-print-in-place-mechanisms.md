# Print-in-place mechanisms — design rules for an AI CAD agent

Target: build123d, FDM, Bambu Lab A1, 0.4mm nozzle, 0.2mm layers, PLA/PETG.
Scope: concrete numeric rules for mechanisms that print assembled and move. `/last30days` run on this topic returned only generic social chatter (it's tuned for trending discourse, not durable technical specs) — one data point kept: a builder reported the tightest tolerance they'd achieved was a 1.76mm encoder axle in a combined FDM/SLA cassette-tape mechanism (r/3Dprinting, 4,693 upvotes), consistent with the sub-0.3mm shaft clearances below being achievable on a well-tuned printer.

Every number below is sourced where a source exists; anything unsourced is explicitly marked **[rule of thumb]**.

---

## 1. Print-in-place gyroscope (nested gimbal rings)

- **How it works / geometry trick:** rings are nested with a small gap and no bridging membrane between them — the trick is a purely geometric release, not a melted joint. Release is by breaking any thin bridging skin plus a light twist once cool. [rule of thumb — consistent across MyMiniFactory/Printables print-in-place listings]
- Radial gap of **~0.25mm** worked for straight edges but was too tight for curved/rotating ring surfaces — circular interfaces need more than a flat-edge clearance number. [source: fab.cba.mit.edu/classes/863.14, Andrew Mao gyroscope build log]
- Pivot-style (cone/ball) gyros designed for SLS/~100-micron machines are print-marginal on desktop FDM — expect to loosen the file's stock clearance. [source: myminifactory.com/object/3d-print-ball-bearing-gyroscope-48971]
- Asymmetric clearance is the trick used by print-in-place bearing collections: tighter radially (less play at inner/outer ring), looser rotationally (extra clearance at rollers/contact faces). [source: makerworld.com/en/models/45644]
- A drop of oil on the flywheel axle after printing is commonly used to free up friction — implying raw printed clearance alone is tight, not free-spinning. [rule of thumb]
- **Orientation:** print with the rotation axis vertical (Z) so each ring is a horizontal cross-section and the ring-to-ring gap is a clean horizontal bridge, not a vertical wall-to-wall gap. [rule of thumb]
- **Failure mode:** rings fuse when curved gap < ~0.25mm; pivot binds if oil/twist isn't applied post-print.

## 2. Planetary gear bearing (Emmett's) / herringbone planetary sets

- **Geometry trick:** herringbone (not straight spur) teeth self-center the planets with no cage AND let the assembly double as a thrust bearing — this is what makes it printable pre-assembled and non-disassemblable in one step. [source: thingiverse.com/thing:3178380 "Perfect Gear Bearing"; printables.com/model/114535]
- Baseline meshing-flank tolerance: **0.25mm**, ships as the default in Emmett's design remix — going tighter fuses the teeth on FDM. [source: thingiverse.com/thing:3178380]
- The original and its derivatives are parametric specifically because correct clearance is printer/material dependent — treat 0.25mm as a starting point, not a constant. [source: thingiverse.com/thing:3178380]
- No sourced backlash-in-degrees number exists for this specific design; on a 0.4mm nozzle the practical floor is module ≥1.0–1.5 to keep root walls printable at 2-3 perimeters. [rule of thumb]
- **Failure mode:** below ~module 1.0 or below ~0.2mm flank clearance, teeth fuse together during print.

## 3. Print-in-place hinges, pin joints, ball-and-socket, chains, chain mail

- Pin-to-barrel radial clearance: **0.2–0.3mm** is the commonly cited sweet spot on a well-calibrated machine; widen to **0.3–0.5mm** (some sources 0.4–0.6mm) on a looser/less-tuned setup. [source: snapmaker.com/blog/3d-printed-hinges; sovol3d.com/blogs/news/print-in-place-3d-printing]
- Equivalent hole-oversize: 0.15–0.30mm clearance per side → hole 0.30–0.60mm larger in diameter than the pin. [rule of thumb / clearance-gauge coupon testing]
- **#1 failure mode named explicitly:** the pin fuses/melds to the barrel — fix by adding clearance or dropping flow 2–5%. [source: snapmaker.com/blog/3d-printed-hinges]
- Elephant's-foot fusing the first layer of a horizontal pin joint is fixed with a **45° chamfer** on the bottom edge of the knuckle. [source: snapmaker.com/blog/3d-printed-hinges]
- **Orientation:** lay the pin/hinge axis flat in X/Y (pin horizontal on the bed) — printing the barrel stacked around a vertical pin bridges every layer through the clearance gap and is the highest fuse-risk orientation. [source: snapmaker.com/blog/3d-printed-hinges]
- Chain mail / interlocking rings: **0.2mm** gap for small/thin rings, up to **0.4mm** for larger/chunkier rings — tighter = more interlock friction/strength, looser = easier articulation. [source: formlabs.com/blog/how-to-3d-print-interlocking-joints]
- A print-in-place fidget-ring design ships with **0.7mm** standard clearance and **1.4mm** "extra-wide" for over-extruding printers — notably looser than pin-in-barrel joints, implying ring-on-ring rotating contact needs more margin than a pin bore. [source: printables.com/model/133578]
- **Ball-and-socket geometry trick:** make the socket a partial "C" opening (not fully enclosed) so it elastically flexes open to snap the ball in — this avoids needing a print-time clearance gap at all. Orient the joint so the socket opening faces up/out to avoid trapped support. [source: shapeways.com/blog/how-to-design-snap-fit-ball-joints-for-3d-printing]
- No sourced minimum wall thickness around a pin bore; a safe floor on a 0.4mm nozzle is 3 perimeters (~1.2mm). [rule of thumb]

## 4. Gears for FDM (general)

- Minimum module: FDM on a 0.4mm nozzle struggles below **module 1.0**; **module 1.5–2.0** is the sweet spot. Module 0.625 at 11 teeth (6.9mm pitch dia) has been reported working at the edge. [source: EngineerDog.com practical gear guide; Prusa forum community report]
- Minimum tooth count: **13 teeth** at 20° pressure angle, **9 teeth** at 25° pressure angle, to avoid undercut; ≥12 teeth generally to avoid a weak tooth root. [source: EngineerDog.com / Instructables gear guide]
- Pressure angle: 20° standard; **25°** widens the tooth root for more shear strength under load and is recommended over 14.5° for printed gears. [source: Instructables/Sovol gear guides]
- Don't cut tooth features finer than the 0.4mm nozzle width. [rule of thumb]
- Backlash: add **0.1–0.2mm** clearance between meshing flanks (or an equivalent center-distance increase) to absorb FDM tolerance/over-extrusion. [source: Sovol3D gear guide]
- Face width: no hard sourced minimum; common practice is face width ≈ 8–12× module. [rule of thumb, standard gear design (Norton)]
- Herringbone cancels the axial thrust a helical gear otherwise introduces; use **5 perimeters and ≥35% infill** for tooth-root strength. Orient with the bore vertical (layers run axially along the tooth face) — stronger tooth roots than flat-on-bed, where layers run across the bending load and are prone to layer-shear under shock. [source: Hackaday "Studying the Finer Points of 3D Printed Gears"; meta-matic spur gear guide]
- Worm/rack: self-locking reliably below **5° lead angle**; up to 12–15° lead angle can still be back-driven (not self-locking). A printed PLA worm gear has transmitted ~3 Nm torque in one case study. [source: worm self-locking condition μ ≥ tanλ·cosα, general machine-design reference; FacFox PEEK/FDM worm gear case study]
- Bore/shaft retention: avoid a plain press-fit bore — creep loosens it over time. Use a D-flat shaft, square drive, metal keyway, or heat-set insert + setscrew instead. No universal press-fit %; common practice is 0.1–0.3mm interference on rigid materials. [source: EngineerDog.com gear guide; rule of thumb for the interference %]
- No sourced universal strength-derating-per-module formula for PLA/PETG gears exists — the consistent advice is to oversize rather than derate by formula. [rule of thumb]
- **Failure mode:** undersized module/tooth count → snapped teeth; zero backlash → fused/binding mesh; flat-on-bed orientation on a loaded spur gear → layer-shear tooth failure.

## 5. Snap fits (cantilever, annular, torsional) and living hinges

- Cantilever strain formula: **e = 1.5·h·Y / L²** (h = arm thickness, Y = tip deflection, L = beam length); rearranged for design: **L = √(1.5·h·Y / e_allow)**. [source: standard snap-fit design manual formula, cited via filamentfeed.com / Hubs]
- Allowable strain: **PLA ≈ 2–3%**, **PETG ≈ 3–5%**. One-time-use snaps can run near the top of the range; repeated-use snaps should target well under it (no separate numeric split sourced). [source: filamentfeed.com Snap Fit Design guide; split-by-use-count is rule of thumb]
- Recommended L/t (beam length : thickness) ratio: **8:1–10:1 for PLA** (stiffer), **5:1–8:1 for PETG** (more ductile). [source: filamentfeed.com]
- Printing the cantilever arm along Z instead of flat cuts elongation-at-break by ~50% and tensile strength by 20–30% — derate allowable strain by ~50% if the arm can't be printed flat. This is why snap arms should print flat/on their side, so the flex axis lies in-plane rather than across layers. [source: filamentfeed.com]
- Undercut/retraction angle: **90°** retraction face = permanent/inseparable; **≤45°** = separable by hand; 60–90° is the practical inseparable threshold, 0–60° the practical separable range. [source: snap-fit design manual, USPTO-cited reference]
- Entrance/lead-in angle: **30–45°** for low insertion force. [source: same design manual]
- Living hinges: thickness **0.4–0.6mm** typical (2+ layers at 0.2mm LH), up to **0.5–1.2mm** for heavier-duty hinges. **PP is strongly preferred** (near-infinite fatigue life when injection molded); **PLA should never be used for a repeated-flex living hinge** — too brittle. Layers must run parallel to the hinge/bend line (perpendicular to the flex direction) — layers running across the bend cause first-flex delamination regardless of material. [source: Hubs/3ERP living hinge guides; Protolabs/Core77 living hinge guides]
- **Failure mode:** printing the flex axis across layers (Z-stacked) → delamination on first flex; PLA living hinge → snaps within a handful of cycles.

## 6. Compliant mechanisms, flexures, printed springs

- PLA cartwheel/Voronoi flexure structures endured **~58,000 cycles at 85% strain amplitude** in one bone-scaffold fatigue study. [source: PMC11314528, "Fatigue Performance of 3D-Printed PLA Scaffolds"]
- Fatigue life is dominated by geometry/strain, not layer height: layer thickness affected fatigue life by only 0.44% vs an 87% effect on flexural strength in one PLA study; 0.4mm first-layer height gave the best fatigue life vs thinner first layers. [source: ResearchGate/ADS "effects of 3D printing designs on PLA fatigue strength"]
- **PETG is favored over PLA** for functional springs/flexures (more ductile, fails less brittly); PLA is stiffer but fails at lower strain; TPU tolerates more deformation but is softer/less precise. [source: Siraya Tech / goodprints3d spring material guides]
- Printed springs/flexures held under sustained compression permanently lose free height over time (viscoelastic creep) — don't store compliant parts pre-loaded. [rule of thumb, corroborated by EngineeringPaper.xyz spring fatigue writeups]
- No hard sourced minimum flexure thickness beyond the living-hinge figure above (0.4–0.6mm) — treat that as the practical floor for a flexure on a 0.4mm nozzle too. [rule of thumb, extrapolated]
- Same layer-orientation rule as hinges: keep layers parallel to the bend axis / in the plane of flex; never stack layers across the flex direction — every flex cycle becomes a peel-stress test on a weak inter-layer bond. [rule of thumb, consistent with hinge delamination finding]
- Spring geometry: favor PETG, higher perimeter count (thin walls fail first), and minimize time spent fully compressed. [source: Siraya Tech spring guide]

## 7. Captive / "impossible" objects

- **Pause-at-height for embedded inserts (nuts, magnets, bearings):** pause by LAYER NUMBER, not raw mm — layer = target_height / layer_height. Pause after the layer that completes, before the layer that would cover the part. [source: theneverendingprojectslist.com; Bambu forum "Stop printing at layer height"]
- Design the pocket with clearance for the part to drop in freely, plus enough vertical clearance above it that the nozzle clears the part on resume. [rule of thumb]
- **Sacrificial bridging layer:** print a flat solid bridge across a hole/cavity before building the geometry above it, so the printer bridges over solid material rather than sagging into void; drill/punch it out afterward. No sourced exact thickness/perimeter count — 1–2 layers (0.2–0.4mm) is common in practice. [concept source: Hackaday "Sacrificial Bridge Avoids 3D Printed Supports"; thickness is rule of thumb]
- **Teardrop holes:** standard peak angle **45°** (matches the general FDM 45° max-overhang rule); range seen in practice 0° (plain circle) to ~50° (aggressive teardrop) depending on acceptable shape distortion. [source: snapmaker.com "45-Degree Rule in 3D Printing"; makerworld.com teardrop hole tests]
- **Support-free nested/impossible objects** (ball-in-cage, chain links, hinges): working gap **0.2–0.3mm** on a calibrated machine, **0.15mm** achievable on a very well-tuned printer, **0.4mm+** gives a loose/sloppy joint. A ~50mm-scale ball-in-cage example used ~1mm gap at that larger size — clearance scales up with feature size. [source: snapmaker.com "3D Printed Hinges: Design Rules, Tolerances & Inspiration"]
- **Z-gap for a part printed directly atop another moving part:** no sourced exact layer count; general guidance applies the same horizontal-gap logic vertically, commonly implemented as one full layer height (0.2mm at 0.2mm LH) of Z clearance. [rule of thumb]
- Dovetail/interlocking split-print joints: snug friction-fit clearance **0.1–0.15mm per mating surface** for small/precise parts (10mm pin → 10.1–10.15mm slot); up to **0.4mm per surface** for larger/chunkier assemblies. PLA is too brittle for a repeatedly-flexed dovetail — use PETG or tougher material. [source: artopiacollections.com "Design Dovetail Joints for 3D Printed Assemblies"]

## 8. Bearings in prints

- **608 bearing (22mm OD) pocket diameter:** **21.8mm for PLA**, **21.7mm for PETG** (~0.1–0.15mm undersized per side before slicer compensation). [source: tools.creative3dp.com "Press-Fit Tolerances for 3D Printing"]
- Press-fit interference: **0.05mm/side for PLA**, up to **0.10mm/side for PETG** (PETG's flex tolerates more interference without cracking). [source: tools.creative3dp.com]
- A **0.5mm × 45° lead-in chamfer** on the pocket mouth improves assembly success more than tightening tolerance further — press with a vise, not a hammer. [source: tools.creative3dp.com]
- Printed bushing (printed shaft in printed hole): no FDM-specific sourced number — apply the same calibration-dependent clearance as tolerance calibration below (0.2–0.3mm at 0.2mm layer height), since it's the same class of moving-fit problem. [rule of thumb]
- E-clip/retaining-ring groove dimensions: no FDM-specific number found. Generic metal reference for scale only: 9.5mm shaft → groove depth ≈0.9mm, width ≈1.0mm; 11.1mm shaft → groove depth ≈1.2mm, width ≈1.0mm. Scale groove depth ~8–10% of shaft diameter as a starting point, then oversize +0.1–0.2mm since printed clip prongs are less springy than steel. [source: mscdirect.com/imperialsupplies.com retaining-ring catalog — metal parts, not print-verified; scaling advice is rule of thumb]
- No FDM-specific D-flat depth or grub-screw pocket dimension was found — size the D-flat to remove ~20-25% of shaft diameter as a starting point. [rule of thumb]

## 9. Tolerance calibration practice

- **0.2mm gap** is the sliding-fit starting point on a well-calibrated printer at 0.2mm layer height; some very well-tuned printers get usable joints down to **0.15mm**. [source: snapmaker.com "3D Printed Hinges"; tools.creative3dp.com "3D Print Dimensional Accuracy"]
- **0.2–0.3mm** is the general working range reported across most FDM printers for a joint that moves without fusing (PLA). [source: snapmaker.com "3D Printed Hinges"]
- **0.4–0.5mm** is needed on less-tuned printers, larger/coarser nozzles, or rigid FDM filaments generally — cited rigid-FDM gap range is 0.2–0.5mm vs 0.05–0.1mm achievable in high-precision resin. [source: artopiacollections.com dovetail article, rigid-FDM-vs-resin comparison]
- **Why holes need extra clearance:** holes print **0.2–0.4mm undersized** because nozzle/arc compression pulls the perimeter inward on curves — a hole always needs more compensation than a straight-edge slot with the same nominal gap. [source: tools.creative3dp.com "3D Print Dimensional Accuracy"]
- **Slicer hole compensation** (horizontal expansion / XY size compensation) to counter that shrinkage: **+0.15mm per side for a 0.4mm nozzle**, **+0.25mm per side for a 0.6mm nozzle**; community-converged values cluster at **+0.2 to +0.25mm**. Applied in-slicer, shrinks outer walls and grows holes without touching the CAD model. [source: kingroon.com "Understanding Orca Slicer Hole Compensation"]
- **Orientation matters:** a gap on the horizontal axis (X/Y, printed side-by-side in the same layer) only needs the base calibrated clearance above, since it's bounded by nozzle width/wall accuracy. A gap on the Z axis is governed by layer adhesion / first-layer squish and is less repeatable — no sourced numeric delta was found; general advice is to compensate radial features via horizontal expansion rather than resizing in Z. [rule of thumb for the orientation delta itself]

---

## Rules for the agent

1. Default moving-joint clearance (pin-in-hole, ring-in-ring, sliding fit) on a calibrated A1 at 0.2mm layers: **0.2–0.3mm per side**. [snapmaker.com]
2. If the printer/tolerance is unverified or the geometry is curved (not a flat straight edge), widen the default clearance to **0.3–0.4mm per side**. [rule of thumb]
3. Never design a moving clearance below **0.15mm per side** — that is the tuned-printer floor, not a safe default. [snapmaker.com / tools.creative3dp.com]
4. Compensate holes for shrinkage separately from the joint clearance: add **+0.15mm per side** at 0.4mm nozzle (slicer horizontal expansion), on top of the design clearance above. [kingroon.com]
5. For gear-bearing / print-in-place gear meshes specifically, start flank clearance at **0.25mm** and only tighten after a test print confirms free rotation. [thingiverse.com/thing:3178380]
6. Chain-mail / ring-on-ring rotating contact needs **more** clearance than a pin-in-barrel joint at the same scale — start at **0.2mm** for small rings, up to **0.4mm** for large rings, not the pin-joint default. [formlabs.com]
7. For a ball-and-socket, prefer the geometric "C-socket" snap-open trick over a printed clearance gap — it avoids the tolerance problem entirely. [shapeways.com]
8. Orient every pin/hinge/barrel joint with its axis horizontal (flat on the bed), never vertical — vertical stacking bridges every layer through the clearance gap and is the #1 cause of fused joints. [snapmaker.com]
9. Add a **45° chamfer** on the bottom edge of any horizontal pin knuckle to prevent elephant's-foot fusing the first layer. [snapmaker.com]
10. If a pin/barrel joint prints fused, first fix is to add clearance or drop flow **2–5%** before redesigning geometry. [snapmaker.com]
11. Minimum gear module on a 0.4mm nozzle: **1.0**, sweet spot **1.5–2.0**; do not go below module 1.0 without a specific reason and a test print. [EngineerDog.com]
12. Minimum tooth count: **13 at 20° pressure angle**, **9 at 25°**; prefer 25° pressure angle for FDM gears (stronger root) over 14.5° or 20°. [Instructables/Sovol]
13. Add **0.1–0.2mm** backlash clearance between gear tooth flanks on every meshing gear pair; zero backlash reliably fuses/binds on FDM. [Sovol3D]
14. For any loaded spur/herringbone gear, orient the bore vertical (teeth axis along Z) rather than flat-on-bed, and use **≥5 perimeters, ≥35% infill** at the tooth root. [Hackaday]
15. Use herringbone (not straight spur or single helical) whenever the gear must be printed pre-meshed/assembled and self-thrust-bearing. [Hackaday, thingiverse.com]
16. Worm gears self-lock reliably only below **5° lead angle**; above ~12–15° expect back-driving. [general machine-design reference]
17. Never rely on a plain press-fit bore for gear/shaft retention on a printed part — use a D-flat, keyway, or heat-set insert + setscrew; creep will loosen a plain press fit over time. [EngineerDog.com]
18. Cantilever snap-fit strain: compute with **e = 1.5·h·Y/L²**; cap allowable strain at **2–3% for PLA**, **3–5% for PETG**. [filamentfeed.com]
19. If a snap arm must print in Z (not flat), halve the allowable-strain budget to account for the ~50% loss in elongation-at-break. [filamentfeed.com]
20. Always print snap-fit cantilever arms flat/on-side so the flex axis lies in-plane, never stacked across layers. [filamentfeed.com]
21. Use a retraction-face angle of **≤45°** for a separable snap fit, **60–90°** for a permanent one; use a **30–45°** lead-in/entrance angle for low insertion force. [snap-fit design manual]
22. Never spec PLA for a repeated-flex living hinge — treat PLA living hinges as single-use or decorative only; prefer PETG if TPU/PP isn't available. [Protolabs/Core77]
23. Living-hinge / flexure thickness floor: **0.4–0.6mm**, with layers running parallel to the bend line (perpendicular to flex direction), never across it. [Hubs/3ERP]
24. Flexure/compliant-mechanism fatigue life depends far more on strain geometry than on layer height — don't try to fix a fatigue problem by tuning layer height alone; fix the strain concentration in the geometry. [PMC11314528 / ResearchGate PLA fatigue study]
25. Prefer PETG over PLA for any part that must flex repeatedly (springs, flexures, living-hinge-adjacent) as a first material choice; use TPU only when large deformation is required and stiffness isn't. [Siraya Tech]
26. Never store a compliant/spring part pre-loaded (fully compressed/deflected) between uses — it will permanently creep and lose free geometry. [rule of thumb]
27. For a pause-insert (embedded nut/magnet/bearing), compute the pause point as an exact layer number (height ÷ layer height), not an approximate mm height. [theneverendingprojectslist.com]
28. Give every pause-insert pocket enough vertical clearance above the part for the nozzle/hot end to clear on resume. [rule of thumb]
29. Add a sacrificial solid bridging layer (1–2 layers, 0.2–0.4mm) over any cavity/hole that needs to print flat before continuing upward, and plan to remove it post-print. [Hackaday concept, thickness rule of thumb]
30. Use a teardrop profile (not a plain circle) for any unsupported hole whose axis is horizontal; default peak angle **45°**. [snapmaker.com]
31. Scale nested/impossible-object clearance with feature size: **~0.2–0.3mm** at small scale (≤~20mm feature), up to **~1mm** at large scale (~50mm feature) — do not use one fixed gap across wildly different sizes. [snapmaker.com]
32. For split-print dovetail/interlocking joints, use **0.1–0.15mm per surface** for a snug precision fit, up to **0.4mm per surface** for a larger/looser assembly fit; avoid PLA for a joint that will be repeatedly flexed apart. [artopiacollections.com]
33. Size a 608-bearing press-fit pocket at **21.8mm for PLA / 21.7mm for PETG** (22mm OD bearing), i.e. ~0.1–0.15mm interference per side. [tools.creative3dp.com]
34. Add a **0.5mm × 45°** lead-in chamfer to every bearing press-fit pocket mouth. [tools.creative3dp.com]
35. Treat printed-shaft-in-printed-hole bushings as a standard moving joint: apply the same 0.2–0.3mm clearance rule (#1), not a press-fit rule — there's no verified FDM-specific bushing number beyond that. [rule of thumb]
36. When sizing a printed e-clip/retaining groove, start groove depth at ~8–10% of shaft diameter, then add +0.1–0.2mm beyond scaled-metal dimensions since printed prongs are less springy than steel. [rule of thumb, scaled from metal retaining-ring catalog data]
37. Always compensate hole diameters for slicer/print shrinkage separately from mechanical clearance — holes print smaller than modeled due to arc compression on curves. [tools.creative3dp.com]
38. Prefer designing clearance into horizontal (X/Y) mating features over vertical (Z) ones where possible — horizontal gaps are governed by nozzle width/wall accuracy and are more repeatable than Z-axis first-layer squish effects. [rule of thumb]
39. When in doubt on any clearance number in this document, print a tolerance test coupon (a small set of stepped clearances, e.g. 0.1/0.15/0.2/0.25/0.3/0.4mm) on the actual printer/material before committing to a full mechanism — every source above says exact clearance is printer- and material-dependent. [thingiverse.com/thing:3178380, general convergent advice across sources]
40. Never claim a print-in-place mechanism "will move" from geometry alone without a physical print — several core numbers in this document (Z-gap-for-stacked-parts, FDM bushing clearance, sacrificial-bridge thickness) have no hard source and are marked rule of thumb; treat those as starting points requiring test-print verification, not guarantees.
