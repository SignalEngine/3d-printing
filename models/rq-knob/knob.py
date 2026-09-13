"""
Cylindrical knob replacement — M5 tap-drill hole in one flat end, slight dome
on the other end. Reddit request 2026-08-24.

Print orientation: flat (hole) face DOWN on the bed, dome UP.
  - hole axis vertical -> best roundness/straightness for the tap drill to follow
  - flat face gives full 14mm-diameter bed contact for adhesion
  - dome is a shallow spherical cap, self-supporting (low rise, no overhangs > 45 deg)
"""
from build123d import *

# --- parameters (mm) ---
RADIUS = 7.0          # customer-stated
HEIGHT_TOTAL = 15.0   # customer-stated, includes dome
DOME_RISE = 2.0       # ASSUMED: "slight dome" -> shallow spherical cap
CYL_HEIGHT = HEIGHT_TOTAL - DOME_RISE

# M5 hole: customer wants an UNTHREADED pilot for hand-tapping, not a printed thread.
# Standard metric coarse M5x0.8 tap drill = 4.2mm. Vertical printed holes shrink
# ~0.1-0.3mm (fdm-design-rules.md) -> design +0.2mm oversize so the as-printed hole
# is close to the true 4.2mm tap-drill size.
TAP_DRILL_NOMINAL = 4.2
HOLE_DIA_DESIGN = TAP_DRILL_NOMINAL + 0.2   # 4.4mm
HOLE_DEPTH = 10.0     # ASSUMED: not specified; ~2x M5 major dia of thread engagement + margin
BOTTOM_CHAMFER = 0.4  # anti-elephant's-foot on the bed-contact edge

# dome cap, built OUTSIDE the BuildPart context: a Sphere() created *inside* a
# BuildPart auto-unions itself at the origin before any .scale()/Pos() transform
# is applied (learned the hard way — left a stray sphere fused at z=0). Build and
# transform it standalone, then add the finished solid.
dome = Pos(0, 0, CYL_HEIGHT) * Sphere(RADIUS).scale((1, 1, DOME_RISE / RADIUS))

with BuildPart() as knob:
    # cylindrical body, flat end at Z=0 (bed), sketch on XY at Z=0
    with BuildSketch(Plane.XY):
        Circle(RADIUS)
    extrude(amount=CYL_HEIGHT)

    # dome cap on top face
    add(dome, mode=Mode.ADD)

    # anti-elephant's-foot chamfer on the bottom bed-contact edge
    bottom_edge = knob.faces().sort_by(Axis.Z)[0].edges()
    chamfer(bottom_edge, BOTTOM_CHAMFER)

    # M5 tap-drill pilot hole, blind, drilled up from the bottom (bed) face
    bottom_face = knob.faces().sort_by(Axis.Z)[0]
    with Locations(bottom_face):
        Hole(radius=HOLE_DIA_DESIGN / 2, depth=HOLE_DEPTH)

export_step(knob.part, "out.step")
mesher = Mesher()
mesher.add_shape(knob.part)
mesher.write("out.3mf")
export_stl(knob.part, "out.stl", tolerance=0.005, angular_tolerance=0.05)

print(f"radius={RADIUS} height_total={HEIGHT_TOTAL} dome_rise={DOME_RISE} "
      f"hole_dia_design={HOLE_DIA_DESIGN} hole_depth={HOLE_DEPTH}")
