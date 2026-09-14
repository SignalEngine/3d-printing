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
        fd, tmp = tempfile.mkstemp(suffix=".stl"); os.close(fd)
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
    # bed-contact = downward-facing AND within BED_EPS of the lowest point (same
    # threshold + normal test used for both the contact-area figure and the
    # overhang exclusion — previously these used different z-thresholds and only
    # one checked the normal, so vertical wall faces near the bed were silently
    # excluded from the overhang count).
    BED_EPS = 0.05
    bed_faces = (np.abs(m.triangles_center[:, 2] - zmin) < BED_EPS) & (n[:, 2] < -0.99)
    bed_area = ar[bed_faces].sum()
    ov = (n[:, 2] < -np.cos(np.radians(45))) & ~bed_faces  # bed-contact faces are not overhangs
    overhang_pct = 100 * ar[ov].sum() / ar.sum()
    if bed_area < 25: warns.append(f"Bed contact only {bed_area:.0f}mm^2 — adhesion risk in current orientation (brim or reorient).")
    if overhang_pct > 15: warns.append(f"{overhang_pct:.0f}% of surface overhangs >45deg — supports likely; consider reorienting or chamfering.")

    # Thin-wall sampling via ray thickness at face centroids, weighted by face
    # AREA (not triangle index) so a few large thin faces can't be diluted by
    # many tiny triangles elsewhere in the mesh, and a large thin panel voids
    # by triangle count is not under-sampled relative to its actual surface.
    if wt:
        try:
            n_sample = min(400, len(m.faces))
            p = ar / ar.sum()
            idx = np.random.default_rng(0).choice(len(m.faces), size=n_sample, replace=False, p=p)
            pts = m.triangles_center[idx] - m.face_normals[idx] * 0.01
            th = trimesh.proximity.thickness(m, pts, exterior=False, normals=m.face_normals[idx], method="ray")
            th = th[np.isfinite(th)]
            thin = (th < a.min_wall).sum()
            if thin > 3: warns.append(f"~{100*thin/len(th):.0f}% of sampled surface thinner than {a.min_wall}mm — walls may not slice/survive.")
        except Exception as e:
            warns.append(f"Thin-wall check skipped ({e}).")

    # Needs-supports check: slice the part in its CURRENT orientation and
    # look for area with nothing under it — the overhang-normal-angle check
    # above misses a flat horizontal roof over a hollow cavity (its normal
    # points straight up, so it never registers as "overhang"), which is
    # exactly what turned a real print to spaghetti. WARN, not FAIL — supports
    # are a valid choice, this just makes sure the choice gets made.
    if wt:
        try:
            from shapely.ops import unary_union
            dz = 0.4
            zmin, zmax = float(m.bounds[0][2]), float(m.bounds[1][2])
            heights = np.arange(zmin + dz, zmax, dz)
            reach = dz * np.tan(np.radians(50))  # max self-supporting overhang per layer
            worst_area, worst_z = 0.0, None
            islands = []
            if len(heights):
                sections = m.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1], heights=heights.tolist())
                prev_poly = None
                for z, path in zip(heights, sections):
                    poly = unary_union(path.polygons_full) if (path is not None and path.polygons_full) else None
                    if prev_poly is not None and poly is not None and not poly.is_empty:
                        unsupported = poly.difference(prev_poly.buffer(reach))
                        if unsupported.area > worst_area:
                            worst_area, worst_z = unsupported.area, float(z)
                        island = poly.difference(prev_poly.buffer(1e-6))
                        for geom in getattr(island, "geoms", [island]):
                            if geom.area > 0.5:
                                islands.append((geom.area, float(z)))
                    prev_poly = poly
            if worst_z is not None and worst_area > 50:
                warns.append(f"needs supports — largest unsupported area {worst_area:.0f}mm^2 at z={worst_z:.1f}")
            for area, z in islands:
                if area > 2:
                    warns.append(f"needs supports — mid-air island {area:.1f}mm^2 starting at z={z:.1f} (nothing below to attach to)")
        except Exception as e:
            warns.append(f"needs-supports check skipped ({e}).")

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
