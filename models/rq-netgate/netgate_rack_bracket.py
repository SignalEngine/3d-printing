"""
10" 1U rack shelf for Netgate 2100 firewall.
Two rack ears (front-mount, M6 clearance) + one open tray that cradles the device.
Coordinate system: X = rack width (0 = center), Y = depth (0 = rack front), Z = up.

Sources for dimensions (see REPORT.md for full citations):
- Netgate 2100: 172.7 (W) x 108 (D) x 42.2 (H) mm  [shop.netgate.com, itandgeneral.com]
- 10" mini-rack standard: 236.525 mm hole-to-hole, 1U = 44.45 mm  [geerlingguy/mini-rack]
- Netgate 2100 wall-mount keyhole spacing 140 mm (bottom) -- NOT used here (see assumptions);
  this design instead retains the device with side rails + a strap, since keyhole screw
  positions/thread size are not published and the request has no way to caliper the unit.
"""
from build123d import *

# ---- parameters (mm) ----
RACK_HOLE_SPACING = 236.525          # 10" mini-rack hole-to-hole
HOLE_X = RACK_HOLE_SPACING / 2        # 118.2625, rack mounting hole X position
EAR_H = 44.0                          # 1U height, 0.45mm under nominal 44.45 for rack clearance
RACK_HOLE_D = 6.5                     # M6 clearance
FLANGE_W = 16.0                       # ear vertical flange width (X) around the rack hole
FOOT_T = 4.0                          # ear foot thickness (Z)
# Foot reaches all the way from the rack flange (near X=118) in to under the
# tray's own floor (|X|<90) -- long enough that BOTH bolt holes land on the
# tray's native floor, so the tray itself never has to widen with a tab (a
# tab that reached out to the ears made the tray's bbox ~220mm wide, which
# empirically fails to slice on this A1 OrcaSlicer profile even though it is
# well under the 256mm bed -- see REPORT.md "pipeline limitation").
FOOT_LEN = 40.0                       # ear foot length (X), extends inward from flange
EAR_Y_DEPTH = 20.0                    # ear extrusion depth (Y)
FOOT_HOLE_D = 4.5                     # M4 clearance, ear-to-tray bolts

DEVICE_W = 172.7
DEVICE_D = 108.0
DEVICE_H = 42.2
SIDE_CLEARANCE = 3.65                 # per side; real device, not a printed mating part

TRAY_INNER_W = DEVICE_W + 2 * SIDE_CLEARANCE   # 180.0
WALL_T = 3.0
WALL_H = 12.0
FLOOR_T = 3.0
TRAY_OUTER_W = TRAY_INNER_W + 2 * WALL_T       # 186.0
TRAY_DEPTH = 130.0                             # device 108 + front/rear margin

TRAY_HALF_W = TRAY_OUTER_W / 2          # 93.0, tray's own outer edge (no tabs added)

# derived ear X coordinates (right ear; left ear mirrors X -> -X)
flange_x0 = HOLE_X - FLANGE_W / 2
flange_x1 = HOLE_X + FLANGE_W / 2
foot_x0 = flange_x0 - FOOT_LEN
# both bolt holes land on the tray's own floor (|X|<TRAY_HALF_W), clear of the
# 3mm-thick wall band (TRAY_INNER_W/2 .. TRAY_HALF_W) with margin either side
foot_hole1_x = TRAY_INNER_W / 2 - 13.0
foot_hole2_x = TRAY_INNER_W / 2 - 3.0
assert foot_x0 < foot_hole1_x < foot_hole2_x < TRAY_INNER_W / 2 < flange_x0, \
    "foot bolt holes must land on the tray's flat floor, inboard of its wall"


def build_ear(mirror: bool):
    sign = -1 if mirror else 1

    def mx(x):
        return sign * x

    with BuildPart() as ear:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                pts = [
                    (foot_x0, 0), (flange_x1, 0), (flange_x1, EAR_H),
                    (flange_x0, EAR_H), (flange_x0, FOOT_T), (foot_x0, FOOT_T),
                    (foot_x0, 0),
                ]
                Polyline(*[(mx(x), z) for x, z in pts])
            make_face()
        extrude(amount=EAR_Y_DEPTH)
        # build123d's extrude direction off Plane.XZ is not assumed -- measure it.
        y0 = ear.part.bounding_box().min.Y
        y_mid = y0 + EAR_Y_DEPTH / 2

        # rack mounting hole, axis Y, through the flange
        with Locations(Location((mx(HOLE_X), y_mid, EAR_H / 2), (90, 0, 0))):
            Cylinder(RACK_HOLE_D / 2, EAR_Y_DEPTH + 4, mode=Mode.SUBTRACT)

        # 2 foot-to-tray bolt holes, axis Z
        with Locations(
            (mx(foot_hole1_x), y_mid, FOOT_T / 2),
            (mx(foot_hole2_x), y_mid, FOOT_T / 2),
        ):
            Cylinder(FOOT_HOLE_D / 2, FOOT_T + 4, mode=Mode.SUBTRACT)

        # anti-elephant-foot chamfer on the foot's bottom outer edge
        bottom_edges = ear.faces().sort_by(Axis.Z)[0].edges()
        if len(bottom_edges) > 0:
            chamfer(bottom_edges, 0.4)

    return ear.part


def build_tray():
    hw = TRAY_OUTER_W / 2
    iw = TRAY_INNER_W / 2
    with BuildPart() as tray:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Polyline(
                    (-hw, 0), (hw, 0), (hw, WALL_H), (iw, WALL_H),
                    (iw, FLOOR_T), (-iw, FLOOR_T), (-iw, WALL_H), (-hw, WALL_H),
                    (-hw, 0),
                )
            make_face()
        extrude(amount=TRAY_DEPTH)
        # measure actual extrude direction/origin -- don't assume the sign.
        # The ear part (built on the same Plane.XZ convention) occupies Y in
        # [ear_y0, ear_y0+EAR_Y_DEPTH] with ear_y0+EAR_Y_DEPTH == 0 (its "front" is
        # at global Y=0). The tray's front must sit at the SAME Y=0 end -- that is
        # bbox.max.Y here (the tray extends backward into negative Y), not bbox.min.Y.
        by_front = tray.part.bounding_box().max.Y
        bz0 = tray.part.bounding_box().min.Z
        y_front_mid = by_front - EAR_Y_DEPTH / 2
        y_vent0 = by_front - EAR_Y_DEPTH - 30
        y_strap = by_front - EAR_Y_DEPTH - (TRAY_DEPTH - EAR_Y_DEPTH) / 2

        # ear bolt holes matching the ear feet (axis Z), both sides -- these land
        # directly on the tray's own floor (no tab needed, see FOOT_LEN comment)
        for sign in (1, -1):
            with Locations(
                (sign * foot_hole1_x, y_front_mid, bz0 + FLOOR_T / 2),
                (sign * foot_hole2_x, y_front_mid, bz0 + FLOOR_T / 2),
            ):
                Cylinder(FOOT_HOLE_D / 2, FLOOR_T + 4, mode=Mode.SUBTRACT)

        # ventilation slots under the device footprint
        vent_xs = (-60, -20, 20, 60)
        vent_len, vent_w = 70, 10
        for vx in vent_xs:
            with Locations((vx, y_vent0 - vent_len / 2, bz0 + FLOOR_T / 2)):
                Box(vent_w, vent_len, FLOOR_T + 4, mode=Mode.SUBTRACT)

        # strap slots (zip-tie/velcro over the top of the device), outside its footprint,
        # kept clear of the inner wall face (iw=90) to avoid notching the wall thin
        for sx in (-80, 80):
            with Locations((sx, y_strap, bz0 + FLOOR_T / 2)):
                Box(10, 4, FLOOR_T + 4, mode=Mode.SUBTRACT)

        # (no bottom chamfer here: vent/strap cutouts through the floor make the
        # bottom face's edge set too irregular for a reliable chamfer selection;
        # elephant-foot squish on this flat 3mm floor is cosmetic, not functional)

    return tray.part


def export_all(part, name):
    export_step(part, f"{name}.step")
    mesher = Mesher()
    mesher.add_shape(part)
    mesher.write(f"{name}.3mf")


if __name__ == "__main__":
    ear_r = build_ear(mirror=False)
    ear_l = build_ear(mirror=True)
    tray = build_tray()

    export_all(ear_r, "ear_right")
    export_all(ear_l, "ear_left")
    export_all(tray, "tray")

    print("done")
    print(f"ear_r volume={ear_r.volume:.1f} mm3, tray volume={tray.volume:.1f} mm3")
