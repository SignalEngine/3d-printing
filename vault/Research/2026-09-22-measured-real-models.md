# What proven MakerWorld prints actually measure (22 Sep)

James downloaded 7 models; measured with `skills/model-forge/scripts/measure_mechanism.py` (gap between
every pair of separate bodies, thinnest wall, gear tooth count/module). The tool was validated first on
two gears whose real numbers are known (16 teeth module 2.0 → read 16 @ 1.96; 24 @ 2.0 → 24 @ 1.98).

| model | what it shows | measured | our rule before |
|---|---|---|---|
| 4-ring print-in-place spinner ("Tread — Outer Ring Only") | rings rotating against each other | **0.71–0.73 mm** between all rings; its gear 24 teeth, module 1.76 | 0.4 mm |
| Spherical snap-fit ball joint | ball in socket | **0.000 mm — they touch**; socket relies on flex | "prefer a C-socket", no number |
| Hinged box | print-in-place hinge | gaps 0.000–0.084 mm — NOT usable: the tool cannot yet tell a touching hinge from a body it split wrongly | — |
| Planetary gears fidget spinner | planetary set | not measured: the file times out (heavy mesh) | — |
| estabilizador2, Frankenstein switch, Single Color | James's own prints, not print-in-place | no pair within 3 mm | — |

**Rules corrected from this:** 17 and 33 (ring-on-ring 0.7 mm, not 0.4), 16 (a snap-in ball joint is
modelled touching, no clearance).

**Tool limits, stated plainly:** wall thickness is a ray probe (good to ~0.1 mm on ribs, blind to thin
curved shells seen edge-on); bodies that a 3MF stores as one shell are not separated; very heavy meshes
time out. First run of the tool was wrong in two ways (every body read as a gear; every gap read as
0.004 mm because 3MF placement transforms were not applied) — both fixed before any number above.
