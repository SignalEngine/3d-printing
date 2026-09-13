"""
5-part pill organiser to fit a 255 x 70 x 30 mm envelope (customer's stated
external dims). Scheme: 1 base tray with 4 equal compartments + 4 identical
snap-in lids that recess flush into a rabbet at the top of each compartment
= 5 parts total, matching the customer's "Number of parts: 5".

Orientation: base prints bottom-face-down (flat, no supports). Lid prints
flat, notch-face up (flat, no supports).

Coordinate system: X = long axis (255mm), Y = depth (70mm), Z = up (30mm),
origin at the tray's bottom-left-front corner. All exports share this system
so fit.py can check the lid against the tray directly.
"""
from build123d import *

# ---------------- parameters (mm) ----------------
L, W, H = 255.0, 70.0, 30.0        # outer envelope (customer spec)
WALL = 2.0                          # end wall / divider / side wall thickness
N = 4                               # compartments = lids
COMP_W = 61.25                      # inner compartment length (X): (255 - 2*2 - 3*2)/4
COMP_Y = W - 2 * WALL               # inner compartment depth (Y) = 66
CAV_Z0 = WALL                       # cavity floor sits on top of the 2mm base
RABBET_H = 1.5                      # depth of the top recess the lid sits in
CAV_Z1 = H - RABBET_H               # cavity clear height stops here (28.5) -> 26.5mm pill depth
LEDGE = 2.0                         # rabbet shelf width (lid rests on this)
CLR = 0.2                           # snug sliding-fit clearance per side (fdm-design-rules.md)
NOTCH_R = 5.0                       # thumb notch radius, cut into the front rim + lid edge

LID_X = COMP_W - 2 * LEDGE - 2 * CLR   # 56.85
LID_Y = COMP_Y - 2 * LEDGE - 2 * CLR   # 61.60
LID_T = RABBET_H - 0.1                 # 1.4  (0.1mm vertical clearance so it doesn't stand proud)

MIN3 = (Align.MIN, Align.MIN, Align.MIN)
CTR_MINZ = (Align.CENTER, Align.CENTER, Align.MIN)
CTR3 = (Align.CENTER, Align.CENTER, Align.CENTER)


def comp_x0(i):
    return WALL + i * (COMP_W + WALL)


# ---------------- base tray ----------------
with BuildPart() as base:
    Box(L, W, H, align=MIN3)
    for i in range(N):
        x0 = comp_x0(i)
        xc = x0 + COMP_W / 2
        # main cavity (pill compartment), overlapped 0.05mm past the rabbet
        # boundary so the two subtract boxes don't share a coincident face
        with Locations(Pos(x0, WALL, CAV_Z0 - 0.05)):
            Box(COMP_W, COMP_Y, (CAV_Z1 - CAV_Z0) + 0.1, align=MIN3, mode=Mode.SUBTRACT)
        # rabbet (lid recess) at the top, narrower by LEDGE on each side
        with Locations(Pos(x0 + LEDGE, WALL + LEDGE, CAV_Z1 - 0.05)):
            Box(COMP_W - 2 * LEDGE, COMP_Y - 2 * LEDGE, RABBET_H + 1.0, align=MIN3, mode=Mode.SUBTRACT)
        # thumb notch: half-round cut into the front rim, centred on the
        # compartment, so a fingertip can pry the lid up
        with Locations(Pos(xc, W, CAV_Z1 - 0.1)):
            Cylinder(NOTCH_R, RABBET_H + 1.2, align=CTR_MINZ, mode=Mode.SUBTRACT)
    # anti-elephant-foot chamfer on the bottom outer perimeter
    chamfer(base.faces().sort_by(Axis.Z)[0].edges(), 0.4)

export_step(base.part, "base.step")
m = Mesher(); m.add_shape(base.part); m.write("base.3mf")
export_stl(base.part, "base.stl", tolerance=0.005, angular_tolerance=0.05)

# ---------------- lid (x4, identical) ----------------
with BuildPart() as lid:
    Box(LID_X, LID_Y, LID_T, align=MIN3)
    # lead-in chamfer on the bottom edges so it drops into the rabbet easily
    chamfer(lid.faces().sort_by(Axis.Z)[0].edges(), 0.3)
    with Locations(Pos(LID_X / 2, LID_Y, LID_T / 2)):
        Cylinder(NOTCH_R - 0.3, LID_T + 1.0, align=CTR3, mode=Mode.SUBTRACT)

export_step(lid.part, "lid.step")
m = Mesher(); m.add_shape(lid.part); m.write("lid.3mf")
export_stl(lid.part, "lid.stl", tolerance=0.005, angular_tolerance=0.05)

# lid placed in compartment 0's rabbet, in the BASE's own coordinate system,
# so fit.py checks the real assembled clearance (not two independent parts
# each re-zeroed to their own origin).
x0 = comp_x0(0)
lid_pos = Pos(x0 + LEDGE + CLR, WALL + LEDGE + CLR, CAV_Z1)
export_stl(lid_pos * lid.part, "lid_placed.stl", tolerance=0.005, angular_tolerance=0.05)

# ---------------- delivery plate: base + 4 lids laid out on one 3mf ----------------
# Lids placed in the free bed area behind the tray (Y 74-203), well inside
# the 256x256 A1 bed, in a 2x2 grid — a real print-plate layout, not just a
# concept. Bambu Studio can re-arrange on import if preferred.
gap = 5.0
lid_positions = [
    (0.0, W + 4.0),
    (LID_X + gap, W + 4.0),
    (0.0, W + 4.0 + LID_Y + gap),
    (LID_X + gap, W + 4.0 + LID_Y + gap),
]
mp = Mesher()
mp.add_shape(base.part)
for (px, py) in lid_positions:
    mp.add_shape(Pos(px, py, 0) * lid.part)
mp.write("assembly.3mf")

print("base bbox check L,W,H:", L, W, H)
print("compartment inner (W x D x clear-depth):", COMP_W, COMP_Y, CAV_Z1 - CAV_Z0)
print("lid size:", LID_X, LID_Y, LID_T)
print("assembly plate footprint Y max:", lid_positions[-1][1] + LID_Y)
