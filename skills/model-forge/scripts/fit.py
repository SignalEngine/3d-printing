#!/usr/bin/env python3
"""Check the fit between two named parts (lid/box, clip/rail, pin/hole housing...)
that share the same coordinate system (export both from the same assembly —
don't re-zero either one).

Usage: python3 fit.py part_a.stl part_b.stl [--contact-eps 0.05]

Reports exactly one of:
  INTERFERE: parts overlap. Prints interference volume (mm^3) — the offending
             oversize amount — and its bounding-box footprint.
  CLEARANCE: parts don't overlap. Prints the minimum gap (mm) between surfaces
             (checked both A->B and B->A — a one-directional check can miss
             the true closest pair when the meshes have very different
             triangle density), and the "contact area" — surface area of A
             within --contact-eps of B (0 for a loose fit, >0 for a
             touching/press fit).
  UNKNOWN:   the interference boolean itself failed (exit 2). This is NOT a
             clearance pass — a broken boolean tells you nothing about fit,
             so it must not be reported as CLEARANCE.

Exit 0 on INTERFERE/CLEARANCE, 2 on UNKNOWN, unless a file fails to load.
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
    ap.add_argument("--engine", default=None, help="trimesh boolean engine override (mainly for testing the UNKNOWN path)")
    a = ap.parse_args()

    A = load_any(a.part_a)
    B = load_any(a.part_b)
    A.merge_vertices(); B.merge_vertices()
    print(f"A: {a.part_a}  bbox={np.round(A.extents,2).tolist()}  watertight={A.is_watertight}")
    print(f"B: {a.part_b}  bbox={np.round(B.extents,2).tolist()}  watertight={B.is_watertight}")

    try:
        inter = trimesh.boolean.intersection([A, B], engine=a.engine, check_volume=False)
        overlap_vol = inter.volume if inter is not None and len(inter.faces) else 0.0
    except Exception as e:
        # A failed boolean is UNKNOWN, never a silent CLEARANCE — a broken
        # intersection tells you nothing about whether the parts fit.
        print(f"RESULT: UNKNOWN")
        print(f"interference boolean failed: {e}")
        sys.exit(2)

    if overlap_vol > 1e-6:
        bb = inter.bounds
        print(f"RESULT: INTERFERE")
        print(f"interference volume: {overlap_vol:.3f} mm^3")
        print(f"interference footprint (mm): {np.round(bb[1]-bb[0], 2).tolist()}")
        sys.exit(0)

    # No overlap: minimum surface-to-surface distance in BOTH directions,
    # measured over DENSE SURFACE SAMPLES rather than mesh vertices — two
    # faces can touch across their interior (no vertex anywhere near the
    # contact patch) while still reporting a large vertex-to-surface gap.
    n_samples = 4000
    samples_a, _ = trimesh.sample.sample_surface_even(A, n_samples)
    samples_b, _ = trimesh.sample.sample_surface_even(B, n_samples)
    _, dist_a_to_b, _ = B.nearest.on_surface(samples_a)
    _, dist_b_to_a, _ = A.nearest.on_surface(samples_b)
    min_gap = float(min(dist_a_to_b.min(), dist_b_to_a.min()))
    touching = dist_a_to_b < a.contact_eps
    contact_area = float(touching.mean() * A.area)

    print("RESULT: CLEARANCE")
    print(f"minimum gap: {min_gap:.4f} mm")
    print(f"contact area (faces within {a.contact_eps}mm): {contact_area:.2f} mm^2")


if __name__ == "__main__":
    main()
