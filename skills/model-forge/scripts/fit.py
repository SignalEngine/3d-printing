#!/usr/bin/env python3
"""Check the fit between two named parts (lid/box, clip/rail, pin/hole housing...)
that share the same coordinate system (export both from the same assembly —
don't re-zero either one).

Usage: python3 fit.py part_a.stl part_b.stl [--contact-eps 0.05]

Reports exactly one of:
  INTERFERE: parts overlap. Prints interference volume (mm^3) — the offending
             oversize amount — and its bounding-box footprint.
  CLEARANCE: parts don't overlap. Prints the minimum gap (mm) between surfaces,
             and the "contact area" — surface area of A within --contact-eps of
             B (0 for a loose fit, >0 for a touching/press fit).

Exit 0 always (this is a report, not a hard gate) unless a file fails to load.
"""
import sys, argparse
import numpy as np
import trimesh


def load_any(path):
    if path.lower().endswith((".step", ".stp")):
        from build123d import import_step, export_stl
        import tempfile, os
        fd, tmp = tempfile.mkstemp(suffix=".stl"); os.close(fd)
        export_stl(import_step(path), tmp, tolerance=0.01, angular_tolerance=0.1)
        m = trimesh.load(tmp, force="mesh"); os.unlink(tmp)
        return m
    return trimesh.load(path, force="mesh")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part_a")
    ap.add_argument("part_b")
    ap.add_argument("--contact-eps", type=float, default=0.05, help="mm — surface counted as touching within this gap")
    a = ap.parse_args()

    A = load_any(a.part_a)
    B = load_any(a.part_b)
    A.merge_vertices(); B.merge_vertices()
    print(f"A: {a.part_a}  bbox={np.round(A.extents,2).tolist()}  watertight={A.is_watertight}")
    print(f"B: {a.part_b}  bbox={np.round(B.extents,2).tolist()}  watertight={B.is_watertight}")

    try:
        inter = trimesh.boolean.intersection([A, B], check_volume=False)
        overlap_vol = inter.volume if inter is not None and len(inter.faces) else 0.0
    except Exception as e:
        print(f"WARN: interference boolean failed ({e}); falling back to distance-only check.")
        overlap_vol = 0.0

    if overlap_vol > 1e-6:
        bb = inter.bounds
        print(f"RESULT: INTERFERE")
        print(f"interference volume: {overlap_vol:.3f} mm^3")
        print(f"interference footprint (mm): {np.round(bb[1]-bb[0], 2).tolist()}")
        sys.exit(0)

    # No overlap: minimum surface-to-surface distance, and contact area.
    closest_b_on_a, dist_a_to_b, _ = B.nearest.on_surface(A.vertices)
    min_gap = float(dist_a_to_b.min())
    touching_verts = dist_a_to_b < a.contact_eps
    touching_faces = np.isin(A.faces, np.nonzero(touching_verts)[0]).all(axis=1)
    contact_area = float(A.area_faces[touching_faces].sum())

    print("RESULT: CLEARANCE")
    print(f"minimum gap: {min_gap:.4f} mm")
    print(f"contact area (faces within {a.contact_eps}mm): {contact_area:.2f} mm^2")


if __name__ == "__main__":
    main()
