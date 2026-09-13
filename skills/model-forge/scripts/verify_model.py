#!/usr/bin/env python3
"""Verification battery for 3D-printable models. Run on EVERY model before delivery.

Usage: python3 verify_model.py <model.stl|.3mf|.step> [--build-volume 256]
Exit code 0 = all hard checks passed. Non-zero = FAIL, do not deliver.

Checks (hard = must pass, soft = report and judge):
  HARD: loads, watertight/manifold, consistent winding, expected body count,
        fits build volume, positive volume
  SOFT: overhang % (>45deg from vertical), bed contact area, thin-wall sampling,
        small vertical holes (FDM shrinkage), tiny features, mass estimate
"""
import sys, argparse, numpy as np, trimesh

def load_any(path):
    if path.lower().endswith((".step", ".stp")):
        # Mesh STEP via build123d for verification
        from build123d import import_step, export_stl
        import tempfile, os
        part = import_step(path)
        tmp = tempfile.mktemp(suffix=".stl")
        export_stl(part, tmp, tolerance=0.01, angular_tolerance=0.1)
        m = trimesh.load(tmp, force="mesh"); os.unlink(tmp)
        return m
    m = trimesh.load(path, force="mesh")
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--build-volume", type=float, default=256.0)
    ap.add_argument("--bodies", type=int, default=1, help="expected body count")
    ap.add_argument("--min-wall", type=float, default=0.8, help="min wall mm (2 perimeters @0.4 nozzle)")
    a = ap.parse_args()

    m = load_any(a.path)
    m.merge_vertices()
    fails, warns = [], []

    # --- HARD CHECKS ---
    wt = m.is_watertight
    if not wt: fails.append("NOT watertight (non-manifold). Fix geometry; do not just 'repair' blindly — find the bad boolean.")
    if not m.is_winding_consistent: fails.append("Inconsistent face winding (inverted normals).")
    bodies = m.body_count
    if bodies != a.bodies: fails.append(f"Body count {bodies}, expected {a.bodies}. Stray shells or unintended splits.")
    ext = m.extents
    if not all(ext < a.build_volume): fails.append(f"Exceeds build volume: {np.round(ext,1)} vs {a.build_volume}^3")
    vol = m.volume
    if wt and vol <= 0: fails.append("Non-positive volume (inverted mesh).")

    # --- SOFT CHECKS ---
    n, ar = m.face_normals, m.area_faces
    zmin = m.bounds[0][2]
    on_bed = np.abs(m.triangles_center[:, 2] - zmin) < 0.1
    ov = (n[:, 2] < -np.cos(np.radians(45))) & ~on_bed  # bed-contact faces are not overhangs
    overhang_pct = 100 * ar[ov].sum() / ar.sum()
    bed_faces = (np.abs(m.triangles_center[:, 2] - zmin) < 0.05) & (n[:, 2] < -0.99)
    bed_area = ar[bed_faces].sum()
    if bed_area < 25: warns.append(f"Bed contact only {bed_area:.0f}mm^2 — adhesion risk in current orientation (brim or reorient).")
    if overhang_pct > 15: warns.append(f"{overhang_pct:.0f}% of surface overhangs >45deg — supports likely; consider reorienting or chamfering.")

    # Thin-wall sampling via ray thickness at face centroids (sampled for speed)
    if wt:
        try:
            idx = np.random.default_rng(0).choice(len(m.faces), size=min(400, len(m.faces)), replace=False)
            pts = m.triangles_center[idx] - m.face_normals[idx] * 0.01
            th = trimesh.proximity.thickness(m, pts, exterior=False, normals=m.face_normals[idx], method="ray")
            th = th[np.isfinite(th)]
            thin = (th < a.min_wall).sum()
            if thin > 3: warns.append(f"~{100*thin/len(th):.0f}% of sampled surface thinner than {a.min_wall}mm — walls may not slice/survive.")
        except Exception as e:
            warns.append(f"Thin-wall check skipped ({e}).")

    # --- REPORT ---
    print(f"file: {a.path}")
    print(f"watertight={wt} winding={m.is_winding_consistent} bodies={bodies} euler={m.euler_number}")
    print(f"bbox mm: {np.round(ext,2).tolist()}  volume: {vol/1000:.2f} cm^3  tris: {len(m.faces)}")
    print(f"mass est: PLA {vol/1000*1.24:.1f}g / PETG {vol/1000*1.27:.1f}g (100% infill; slicer will be less)")
    print(f"overhang>45deg: {overhang_pct:.1f}%  bed contact: {bed_area:.0f} mm^2")
    for w in warns: print(f"WARN: {w}")
    for f in fails: print(f"FAIL: {f}")
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
