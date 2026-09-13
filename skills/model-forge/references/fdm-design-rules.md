# FDM Design Rules — Bambu Lab A1

## Printer facts (verified from Bambu spec sheet)
- Build volume 256×256×256 mm. Nozzle 0.4 mm stainless (stock), hotend to 300°C, bed to 100°C.
- Open frame, no enclosure: PLA / PETG / TPU are the sane materials. ABS/ASA will warp — steer the user away unless they have an enclosure.
- Textured PEI plate: bottom face comes out textured; slight first-layer squish rounds bottom edges ~0.1–0.2 mm.

## Material choice (default recommendations)
| Use | Material | Why |
|---|---|---|
| Visual, brackets, jigs, indoor | PLA | Stiffest of the three, easiest, cheap |
| Outdoor, hot car, load over time | PETG | PLA creeps under sustained load and softens ~55°C |
| Flexible, grippy, impact | TPU | Print slow |
Warn on: PLA for anything clamped/tensioned long-term (creep) or in sun/car (heat).

## Dimensional rules (0.4 nozzle, defaults)
These are well-established community starting points, NOT calibrated facts for this specific printer+filament. First fit-critical print should include a test coupon (see build123d-patterns.md).

- **Min wall**: 0.8 mm (2 perimeters). Prefer ≥1.6 mm structural, ≥2.4 mm load-bearing.
- **Min feature/pin**: ≥2 mm dia; pins <3 mm snap easily.
- **Clearances between mating printed parts** (per side, diametral for holes):
  - Press/friction fit: 0.05–0.1 mm
  - Snug sliding fit: 0.15–0.2 mm
  - Free sliding / assembly fit: 0.25–0.3 mm
  - Print-in-place moving joints: ≥0.4 mm gap
- **Vertical holes shrink** ~0.1–0.3 mm on FDM. For accurate holes: add +0.2 mm to design diameter, or design undersize and drill. Horizontal (side-facing) holes sag on top — teardrop or chamfer them, or accept ovality.
- **First-layer holes/slots**: elephant's foot eats ~0.1–0.2 mm; chamfer bottom edges 0.3–0.5 mm × 45° (also easier removal from textured plate).

## Overhangs, bridges, orientation
- Self-supporting up to ~45° from vertical; A1 with good cooling handles ~55–60° in PLA but design to 45°.
- Bridges: clean to ~10 mm, acceptable to ~25 mm in PLA. Longer → add sacrificial support or chamfer.
- Circular horizontal holes >8 mm dia print poorly on top — teardrop shape or bridge-friendly diamond top.
- **Layer lines are the weak direction** (roughly 40–60% of in-plane strength). Orient so load is in-plane, not peeling layers apart. A snap-fit cantilever printed vertically WILL snap at a layer line — orient flexing features flat.
- Prefer chamfers over fillets on bottom edges (fillet at bed = mini-overhang).

## Fasteners & joints
- **Heat-set inserts** (best for repeated assembly): M3 standard insert → 4.0 mm hole, depth ≥ insert length +1 mm, wall around ≥2 mm. M4 → 5.6 mm, M5 → 6.4 mm. (Sizes vary by insert brand — check the insert datasheet if known; these fit common Ruthex/CNC Kitchen style.)
- **Captured hex nuts**: pocket = nut width-across-flats +0.2 mm, thickness +0.1 mm. M3 nut: 5.7 mm AF ⇒ 5.9 mm pocket.
- **Screw into plastic directly**: works for low-load; hole = thread minor dia (M3 → 2.5 mm).
- **Printed threads**: fine at ≥M8 with 0.2 mm layer height; below M8 use inserts/nuts. Model threads at 0.2 layer height max.
- **Counterbores** over countersinks (countersink cone = overhang when printed upside down, and cap heads look better).

## Print-setting suggestions to give the user per part class
| Part class | Layer | Walls | Infill |
|---|---|---|---|
| Visual | 0.12–0.16 | 2 | 10–15% |
| Functional (brackets, mounts) | 0.2 | 3–4 | 25–40% gyroid |
| Structural / load | 0.2 | 4–6 | 40%+ or solid near stress |
Walls beat infill for strength — say so when it matters.

## Bed adhesion
Contact area <~100 mm² or tall+thin → recommend brim. Point/line contact with bed → reorient or add integrated tabs.
