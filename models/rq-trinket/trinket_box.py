"""Trinket box sized to replace a Samsung Galaxy Buds case inside a decorative
outer case. Rounded-corner "pebble" box (base) + lift-off lid with a friction
skirt that plugs into the cavity from the top.

Orientation: printed with the open cavity face UP (base) and lid top face UP
(lid) — both are flat-bottomed, no overhangs beyond the 45 deg rule (only the
bottom chamfer and the skirt lead-in chamfer are angled, both <=45 deg).

Assumptions (customer did not supply, no calliper/photo-with-ruler available):
  - 51 x 51 x 28.3 mm is the box's OUTER envelope (matches the stated Samsung
    Buds case size the decorative case was built around) — built at that size
    exactly, no extra shrink, since the decorative case's cavity already has
    clearance for a case of that stated size.
  - Wall 1.8 mm / floor 2.0 mm — visual/light-duty trinket box, not load-bearing.
  - Lid = lift-off cap with an internal friction skirt (see REPORT.md for why
    a hinge was rejected).
  - Fit class: snug sliding (0.15 mm/side, per fdm-design-rules.md) so the lid
    opens by hand pull with no thumb notch needed.
"""
from build123d import *

# ---- Parameters (mm) ----
OUTER_L = 51.0
OUTER_W = 51.0
TOTAL_H = 28.3
CORNER_R = 12.0            # outer corner radius -> pebble/buds-case footprint
WALL = 1.8                 # base side wall thickness
FLOOR = 2.0                # base floor thickness
LID_TOP = 3.0              # lid top panel thickness
SKIRT_DEPTH = 4.0          # lid skirt engagement into the base cavity
FIT_CLEARANCE = 0.15       # per-side clearance, snug sliding fit
TOP_EDGE_FILLET = 1.5      # rounded top rim on the base
LID_EDGE_FILLET = 2.0      # rounded top edge on the lid (visible "pebble" look)
BOTTOM_CHAMFER = 0.4       # anti-elephant-foot, base underside
SKIRT_LEAD_IN = 0.4        # chamfer on skirt tip for easy insertion

BASE_H = TOTAL_H - LID_TOP        # 25.3 mm, floor -> rim, external
CAVITY_H = BASE_H - FLOOR         # 23.3 mm usable depth
assert SKIRT_DEPTH < CAVITY_H, "skirt would bottom out in the cavity"

INNER_L = OUTER_L - 2 * WALL
INNER_W = OUTER_W - 2 * WALL
INNER_R = max(CORNER_R - WALL, 1.0)

# ---------------- Base ----------------
with BuildPart() as base:
    with BuildSketch(Plane.XY):
        RectangleRounded(OUTER_L, OUTER_W, radius=CORNER_R)
    extrude(amount=BASE_H)

    # rounded top rim (soften the edge the lid sits against)
    top_edges = base.faces().sort_by(Axis.Z)[-1].edges()
    fillet(top_edges, TOP_EDGE_FILLET)

    # hollow the cavity from the top down, leaving FLOOR mm at the bottom
    top_face = base.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top_face):
        RectangleRounded(INNER_L, INNER_W, radius=INNER_R)
    extrude(amount=-(BASE_H - FLOOR), mode=Mode.SUBTRACT)

    # anti-elephant-foot chamfer on the bed-contact edge
    bottom_edges = base.faces().sort_by(Axis.Z)[0].edges()
    chamfer(bottom_edges, BOTTOM_CHAMFER)

export_step(base.part, "out/base.step")
mesher = Mesher()
mesher.add_shape(base.part)
mesher.write("out/base.3mf")
export_stl(base.part, "out/base.stl", tolerance=0.005, angular_tolerance=0.05)

# ---------------- Lid ----------------
skirt_L = INNER_L - 2 * FIT_CLEARANCE
skirt_W = INNER_W - 2 * FIT_CLEARANCE
skirt_R = max(INNER_R - FIT_CLEARANCE, 0.8)

with BuildPart() as lid:
    with BuildSketch(Plane.XY):
        RectangleRounded(OUTER_L, OUTER_W, radius=CORNER_R)
    extrude(amount=LID_TOP)

    # rounded top edge -> the visible "pebble" shape from the reference photo
    top_edges = lid.faces().sort_by(Axis.Z)[-1].edges()
    fillet(top_edges, LID_EDGE_FILLET)

    # friction skirt hanging down from the underside
    bottom_face = lid.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom_face):
        RectangleRounded(skirt_L, skirt_W, radius=skirt_R)
    extrude(amount=SKIRT_DEPTH, mode=Mode.ADD)

    # lead-in chamfer on the skirt tip so the lid registers before it grips
    tip_edges = lid.faces().sort_by(Axis.Z)[0].edges()
    chamfer(tip_edges, SKIRT_LEAD_IN)

export_step(lid.part, "out/lid.step")
mesher = Mesher()
mesher.add_shape(lid.part)
mesher.write("out/lid.3mf")
export_stl(lid.part, "out/lid.stl", tolerance=0.005, angular_tolerance=0.05)

# assembled-position export (lid seated on the base) — for fit.py only, since
# fit.py needs both meshes in one shared coordinate system, not each part's
# own local origin
assembled_lid = Pos(0, 0, BASE_H) * lid.part
export_stl(assembled_lid, "out/lid_assembled.stl", tolerance=0.005, angular_tolerance=0.05)

print("Base bbox:", base.part.bounding_box().size)
print("Lid  bbox:", lid.part.bounding_box().size)
print("Assembled external height (base rim + lid top):", BASE_H + LID_TOP)
