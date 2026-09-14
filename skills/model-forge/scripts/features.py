#!/usr/bin/env python3
"""List holes (diameter, depth, axis, face) from CAD geometry, and optionally
check them against intended sizes/positions.

Reads holes straight off the BREP (cylindrical faces where the surface curves
toward the axis — build123d's is_circular_concave), not off a tessellated
mesh, so diameter and axis are exact, not sampled.

Usage:
  python3 features.py part.step
  python3 features.py part.step --expect holes.json
holes.json: [{"diameter": 4.0, "face": "+Z", "tol": 0.15}, ...]
"face" is one of +X/-X/+Y/-Y/+Z/-Z (blind hole opening on that face) or
"through X"/"through Y"/"through Z" (drilled all the way through the part
along that axis). Exit 0 only if every found hole matches exactly one
expected entry and every expected entry is matched (no extras, no misses).
"""
import sys, argparse, json
import numpy as np
from build123d import import_step, GeomType

AXIS_NAMES = ["X", "Y", "Z"]


def axis_index(direction):
    d = np.array(direction)
    idx = int(np.argmax(np.abs(d)))
    return idx


def find_holes(part):
    holes = []
    for f in part.faces():
        if f.geom_type != GeomType.CYLINDER or not f.is_circular_concave:
            continue
        cyl = f.geom_adaptor().Cylinder()
        ax = cyl.Axis()
        direction = (ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z())
        idx = axis_index(direction)
        loc = ax.Location()
        loc_arr = np.array([loc.X(), loc.Y(), loc.Z()])
        bb = f.bounding_box()
        fmin, fmax = np.array(tuple(bb.min)), np.array(tuple(bb.max))
        depth = float(fmax[idx] - fmin[idx])
        name = AXIS_NAMES[idx]

        # Probe 0.02mm beyond each end of the cylinder along its own axis: a
        # point NOT inside the solid there means that end is an opening —
        # independent of the part's overall bounding box (a boss/feature
        # elsewhere in the part must not change this hole's classification).
        # 0.02mm keeps the probe inside a thin blind floor (issue #2: 0.2mm
        # overshot a 0.1mm floor and read the hole as through).
        probe_min = loc_arr.copy(); probe_min[idx] = fmin[idx] - 0.02
        probe_max = loc_arr.copy(); probe_max[idx] = fmax[idx] + 0.02
        open_min = not part.is_inside(tuple(probe_min))
        open_max = not part.is_inside(tuple(probe_max))
        if open_min and open_max:
            face = f"through {name}"
        elif open_max:
            face = f"+{name}"
        elif open_min:
            face = f"-{name}"
        else:
            face = f"internal {name}"  # blind hole that doesn't reach an outer face

        center_arr = loc_arr.copy()
        center_arr[idx] = (fmin[idx] + fmax[idx]) / 2.0
        holes.append({
            "diameter": round(f.radius * 2, 3),
            "depth": round(depth, 3),
            "axis": name,
            "face": face,
            "center": [round(c, 3) for c in center_arr.tolist()],
        })
    return holes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--expect", help="JSON file of expected holes")
    ap.add_argument("--tol", type=float, default=0.15, help="default diameter match tolerance mm")
    a = ap.parse_args()

    part = import_step(a.path)
    holes = find_holes(part)
    print(f"{len(holes)} hole(s) found:")
    for h in holes:
        print(f"  Ø{h['diameter']}mm  depth={h['depth']}mm  axis={h['axis']}  face={h['face']}  center={h['center']}")

    if not a.expect:
        sys.exit(0)

    expected = json.load(open(a.expect))
    unmatched_expected = []
    unmatched_found = []
    # Match within each face group by diameter order (smallest-to-smallest),
    # not list order — two near-equal diameters on one face otherwise
    # false-FAIL depending on which found the scan happens to hit first.
    faces = {h["face"] for h in holes} | {e["face"] for e in expected}
    for face in faces:
        exp_group = sorted((e for e in expected if e["face"] == face), key=lambda e: e["diameter"])
        found_group = sorted((h for h in holes if h["face"] == face), key=lambda h: h["diameter"])
        remaining_found = list(found_group)
        for exp in exp_group:
            match = next((h for h in remaining_found if abs(h["diameter"] - exp["diameter"]) <= exp.get("tol", a.tol)), None)
            if match is not None:
                remaining_found.remove(match)
            else:
                unmatched_expected.append(exp)
        unmatched_found.extend(remaining_found)

    ok = True
    for exp in unmatched_expected:
        print(f"FAIL: expected hole Ø{exp['diameter']}mm on face {exp['face']} not found")
        ok = False
    for h in unmatched_found:
        print(f"FAIL: unexpected hole Ø{h['diameter']}mm on face {h['face']} (center={h['center']})")
        ok = False
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
