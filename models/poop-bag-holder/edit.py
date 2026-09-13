"""Poop bag holder edit v3: sunken hexagon panels -> bone-shaped through-holes, plus a treat-pouch hook loop.

Source: original.stl (downloaded mesh). Mesh edit via manifold booleans.
Measured facts (radius map in the upright frame, radius_map_aligned.png):
  - part axis is tilted 1.90 deg in the source file; align_T.npy stands it upright (inner-bore fit, resid <0.01 mm)
  - inner bore r=23.0, outer skin r=26.0 (min 25.92 between facets), hexes are SUNKEN panels at r=25.0
  - bag slot theta -110..-68, z 13..63; leash-clip base theta 48..126, z 33..43; thread z 0..10; lid z 65..68
Output is in the upright frame: the thread end sits flat on the bed (Z up = print direction).
"""
from collections import deque
import numpy as np, trimesh
from shapely.geometry import Point, box, Polygon
from shapely.ops import unary_union

F = np.load("align_T.npy")                 # source frame -> upright frame
MAP = np.load("radius_map_aligned.npy")    # original part, rows z=2..69 (1 mm), cols theta=-180..178 (2 deg)
TH = np.arange(-180, 180, 2.0); ZS = np.arange(2, 70, 1.0)

# --- parameters (mm / deg) ---
FILL_R = (24.0, 25.92)                 # refill panels up to the measured skin minimum: never proud of the skin
FILL_Z = (13.5, 61.5)
SLOT_KEEP = (-118.0, -60.0)            # never fill or cut in this wedge (bag slot)
CLIP_BASE = (44.0, 132.0, 30.0, 46.0)  # theta lo, hi, z lo, hi: panels under the clip base are filled, no bone
BONE_LEN, BONE_SHAFT, KNOB_R = 12.0, 3.2, 2.0   # vertical bone, 12 tall x 7.2 wide: fits a 9 x 15 mm panel
BONE_R = (22.0, 27.0)                  # cut span: through the 23-26 wall only (centre peg at r=3 untouched)
# hook loop (treat-pouch snap-hook gate measured by James: 4.54 mm)
LOOP_THETA, LOOP_T, LOOP_OUT = -45.0, 3.6, 13.0  # 3.6 thick passes a 4.54 gate; -45 = nearest solid side opposite the clip
LOOP_PROFILE = [(-1.0, 42.0), (LOOP_OUT, 56.0), (LOOP_OUT, 66.0), (-1.0, 66.0)]  # (u from skin, z): 45 deg underside
HOLE_R, HOLE_U, HOLE_Z = 2.6, 7.0, 59.0          # teardrop hole, apex up, prints without support
R_SKIN = 26.0


def ang_in(a, lo, hi):
    return (a - lo) % 360 <= (hi - lo) % 360


def frame(theta_deg, z0, r0, x_axis):
    """4x4 placing local X along x_axis ('tang' or 'radial'), local Y = world up, origin at (r0, theta, z0)."""
    t = np.radians(theta_deg)
    radial = np.array([np.cos(t), np.sin(t), 0.0]); tang = np.array([-np.sin(t), np.cos(t), 0.0]); up = np.array([0, 0, 1.0])
    X = tang if x_axis == "tang" else radial
    M = np.eye(4); M[:3, 0] = X; M[:3, 1] = up; M[:3, 2] = np.cross(X, up)
    assert np.linalg.det(M[:3, :3]) > 0.999      # a rotation, never a mirror
    M[:3, 3] = radial * r0 + up * z0
    return M


def panels():
    """Sunken hex panels from the radius map: connected components of r in (24.6, 25.4), wrapping in theta."""
    mask = (MAP > 24.6) & (MAP < 25.4) & (ZS[:, None] > FILL_Z[0]) & (ZS[:, None] < FILL_Z[1])
    seen = np.zeros_like(mask); out = []
    for i0, j0 in zip(*np.nonzero(mask)):
        if seen[i0, j0]:
            continue
        q = deque([(i0, j0)]); seen[i0, j0] = True; cells = []
        while q:
            i, j = q.popleft(); cells.append((i, j))
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + di, (j + dj) % len(TH)
                if 0 <= ii < len(ZS) and mask[ii, jj] and not seen[ii, jj]:
                    seen[ii, jj] = True; q.append((ii, jj))
        if len(cells) < 20:
            continue
        ii, jj = np.array(cells).T
        a = np.radians(TH[jj]); theta = np.degrees(np.arctan2(np.sin(a).mean(), np.cos(a).mean()))
        out.append((round(float(theta), 1), round(float(ZS[ii].mean()), 1), len(cells)))
    return out


def radial_prism(poly, theta, z0, r_span):
    """Extrude a (tangential u, z) polygon radially from r_span[0] to r_span[1] at angle theta, centred at z0."""
    p = trimesh.creation.extrude_polygon(poly, r_span[1] - r_span[0])   # local Z = radial
    p.apply_transform(frame(theta, z0, 0.0, "tang") @ trimesh.transformations.translation_matrix([0, 0, r_span[0]]))
    return p


def bone():
    h = BONE_LEN / 2 - KNOB_R
    knobs = [Point(sx * KNOB_R * 0.8, sy * h).buffer(KNOB_R, 32) for sx in (-1, 1) for sy in (-1, 1)]
    return unary_union([box(-BONE_SHAFT / 2, -h, BONE_SHAFT / 2, h), *knobs])


def fill_ring():
    ring = Point(0, 0).buffer(FILL_R[1], 128).difference(Point(0, 0).buffer(FILL_R[0], 128))
    lo, hi = np.radians(SLOT_KEEP)
    wedge = Polygon([(0, 0)] + [(40 * np.cos(t), 40 * np.sin(t)) for t in np.linspace(lo, hi, 32)])
    c = trimesh.creation.extrude_polygon(ring.difference(wedge), FILL_Z[1] - FILL_Z[0])
    c.apply_translation([0, 0, FILL_Z[0]])
    return c


def loop():
    hole = unary_union([Point(HOLE_U, HOLE_Z).buffer(HOLE_R, 48),
                        Polygon([(HOLE_U - HOLE_R * 0.707, HOLE_Z + HOLE_R * 0.707), (HOLE_U, HOLE_Z + HOLE_R * 1.414),
                                 (HOLE_U + HOLE_R * 0.707, HOLE_Z + HOLE_R * 0.707)])])
    prof = Polygon(LOOP_PROFILE).difference(hole)
    fin = trimesh.creation.extrude_polygon(prof, LOOP_T)       # local X = radial offset u, Y = z, Z = thickness
    fin.apply_translation([0, 0, -LOOP_T / 2])
    fin.apply_transform(frame(LOOP_THETA, 0.0, R_SKIN, "radial"))
    return fin


if __name__ == "__main__":
    src = trimesh.load("original.stl", force="mesh"); src.merge_vertices()
    parts = sorted(src.split(only_watertight=False), key=lambda b: -b.volume)
    body, letters = parts[0], parts[1:]
    for p in parts:
        p.apply_transform(F)

    found = panels()
    keep = [(t, z) for t, z, n in found
            if not (ang_in(t, CLIP_BASE[0], CLIP_BASE[1]) and CLIP_BASE[2] < z < CLIP_BASE[3])
            and not (z > 44 and abs(((t - LOOP_THETA + 180) % 360) - 180) < 15)
            and not ang_in(t, *SLOT_KEEP)]
    print(f"panels found: {len(found)}  bones to cut: {len(keep)}")
    for t, z, n in found:
        print(f"  panel theta={t:7.1f} z={z:5.1f} px={n}  {'BONE' if (t, z) in keep else 'fill only'}")

    out = trimesh.boolean.union([body, fill_ring()], engine="manifold")
    cutters = trimesh.boolean.union([radial_prism(bone(), t, z, BONE_R) for t, z in keep], engine="manifold")
    out = trimesh.boolean.difference([out, cutters], engine="manifold")
    out = trimesh.boolean.union([out, loop()], engine="manifold")

    out.merge_vertices(); out.update_faces(out.nondegenerate_faces()); out.remove_unreferenced_vertices()
    shells = [b for b in out.split(only_watertight=False) if abs(b.volume) > 1.0]
    assert len(shells) == 1 and shells[0].is_watertight, [(round(b.volume, 2), b.is_watertight) for b in shells]
    out = shells[0]
    final = trimesh.util.concatenate([out, *letters])
    final.export("holder_v3.stl"); final.export("holder_v3.3mf")
    print(f"body watertight={out.is_watertight} vol {body.volume/1000:.2f} -> {out.volume/1000:.2f} cm3  bounds {np.round(final.bounds, 2).tolist()}")
