"""
RQ-Trophy — "CONGRATULATION" word-trophy, personalisable base line.
Recreates the reference's freestanding-word-on-a-base look with a
cantilevered final letter, adapted because the target word (14 letters,
no natural single-line fit in a 150x150mm envelope) needed 4 stacked
lines instead of the reference's single line.

Coordinate convention: X = width (left-right), Z = height (up, print
direction), Y = depth. Foot occupies Y 0..D_FOOT (extends back for a
stable footprint); panel+letters project forward from Y=0 into -Y.
Bottom face (Z=0) sits on the bed.

Structural note (the one real engineering addition vs. the reference):
a thin backing panel runs behind all four text lines so each line has
continuous support down to the base — without it, stacked lines with
gaps between them would be unprintable floating shells. The panel's
right edge is a shallow (~6 deg from vertical) diagonal gusset that
carries the last line's final letter "N" out past the visible base
foot's edge, giving the "overhanging last letter" look while staying
self-supporting (well under the 45 deg FDM overhang limit).
"""
from build123d import *

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# --- parameters (mm) ---
W_FOOT = 130.0          # base foot width (the part that visibly "ends")
D_FOOT = 30.0           # base foot depth (front-to-back) — stability footprint
H_FOOT = 14.0           # base foot height
PANEL_T = 6.0           # backing panel thickness (behind the letters)
LETTER_DEPTH = 10.0     # how far letters project forward off the panel
OVERHANG_X = 145.0      # trapezoid top-right X (how far the gusset reaches)
Z_TOP = 151.0           # overall top of panel/letters
FONT_SIZE = 42.0        # -> ~29.5mm cap height on LiberationSans-Bold
LINE_GAP = 6.0          # vertical gap between text lines
CHAMFER_BOTTOM = 0.4    # anti-elephant's-foot on the bottom edge
PERSONAL_TEXT = "PERSONALISED TEXT HERE"
PERSONAL_FONT_SIZE = 7.0
PERSONAL_DEBOSS = 0.6

LINES = ["CONG", "RATU", "LAT", "ION"]  # CONG+RATU+LAT+ION = CONGRATULATION


def glyph_face(word, size, **kwargs):
    with BuildSketch(Plane.XZ) as sk:
        Text(word, font_size=size, font_path=FONT,
             align=(Align.MIN, Align.MIN), **kwargs)
    return sk.sketch


# --- base foot (thick plinth, full depth, gives the part its footprint) ---
with BuildPart() as foot_bp:
    Box(W_FOOT, D_FOOT, H_FOOT, align=(Align.MIN, Align.MIN, Align.MIN))
    bottom_edges = foot_bp.faces().sort_by(Axis.Z)[0].edges()
    chamfer(bottom_edges, CHAMFER_BOTTOM)
foot = foot_bp.part

# --- backing panel: trapezoid profile in XZ, extruded backward 0..-PANEL_T ---
# overlaps 0.1mm down into the foot to keep the union manifold-safe
pts = [(0, H_FOOT - 0.1), (W_FOOT, H_FOOT - 0.1), (OVERHANG_X, Z_TOP), (0, Z_TOP)]
with BuildSketch(Plane.XZ) as psk:
    with BuildLine():
        Polyline(*pts, close=True)
    make_face()
panel = extrude(psk.sketch, amount=PANEL_T)

trophy_body = foot + panel

# --- text lines: extrude forward off the panel's front face (Y=0 -> -LETTER_DEPTH) ---
# Stack bottom-up in READING order reversed (last word "ION" nearest the base,
# first word "CONG" at the top) so the word reads top-to-bottom normally and the
# overhanging final letter ("N") sits low, near the base edge — like the reference.
baseline_z = H_FOOT
letters = []
for word in reversed(LINES):
    face = glyph_face(word, FONT_SIZE)
    bb = face.bounding_box()
    if word == LINES[-1]:
        x_start = OVERHANG_X - 5.0 - bb.size.X  # right edge lands 5mm inside gusset limit
    else:
        x_start = (W_FOOT - bb.size.X) / 2
    shifted_face = Pos(x_start, -PANEL_T, baseline_z) * face
    solid = extrude(shifted_face, amount=LETTER_DEPTH)
    letters.append(solid)
    baseline_z += bb.size.Z + LINE_GAP

part = trophy_body
for l in letters:
    part = part + l

# --- personalisation line, debossed into the foot's front face (Y=0) ---
with BuildSketch(Plane.XZ) as pesk2:
    with Locations((W_FOOT / 2, H_FOOT / 2)):
        Text(PERSONAL_TEXT, font_size=PERSONAL_FONT_SIZE, font_path=FONT,
             align=(Align.CENTER, Align.CENTER))
personal_solid = extrude(pesk2.sketch, amount=-PERSONAL_DEBOSS)
part = part - personal_solid

export_step(part, "trophy.step")
mesher = Mesher()
mesher.add_shape(part)
mesher.write("trophy.3mf")
export_stl(part, "trophy.stl", tolerance=0.005, angular_tolerance=0.05)
bb = part.bounding_box()
print("done. bbox X:%.1f..%.1f Y:%.1f..%.1f Z:%.1f..%.1f" % (
    bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z))
