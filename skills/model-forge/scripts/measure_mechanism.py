#!/usr/bin/env python3
"""Measure a downloaded, proven mechanism (3MF/STL/OBJ) to learn the numbers that made it work:
the gap between moving pieces, wall thickness, and gear tooth count / module.

This script is for LEARNING NUMBERS from other people's models: never copy, ship or derive
geometry from them — the measurements are not covered by the model's licence, the shapes are.
Remixing an upload is the one exception: model_card.py + the change engine keep the customer's
geometry, and only under the rights the customer has confirmed (change-engine spec, section 1).

Usage: python3 measure_mechanism.py model.3mf [--json out.json] [--samples 4000]

Prints one block per body, then the gap between every pair of bodies that are close enough
to matter. A print-in-place mechanism's smallest pair gap IS its working clearance.
"""
import argparse, json, sys
import numpy as np
import trimesh

CLOSE_MM = 3.0
GAP_SAMPLES_MAX = 700   # points sampled per body for the pair distance          # pairs further apart than this are not a joint; skip the report line
GEAR_MIN_TEETH = 6
GEAR_MAX_TEETH = 200


def bodies(path, min_volume_mm3=1.0):
    """Every separate solid in the file: scene parts first, then disconnected shells inside each."""
    loaded = trimesh.load(path)
    # scene.geometry gives the RAW meshes, all sitting at their own origin — every pair then measures a
    # nonsense ~0 gap. dump() applies each instance's placement transform, which is what a printed plate is.
    parts = loaded.dump() if isinstance(loaded, trimesh.Scene) else [loaded]
    out = []
    for p in parts:
        if not isinstance(p, trimesh.Trimesh):
            continue
        for b in p.split(only_watertight=False):
            b.merge_vertices()
            if b.volume > min_volume_mm3 and len(b.faces) > 20:
                out.append(b)
    # A plate often carries the same part instanced several times in the same spot; those coincident copies
    # read as 0.000 mm "gaps" that are not joints at all. Keep one of each (volume + centre, to 0.01 mm).
    seen, unique = set(), []
    for b in out:
        key = (round(float(b.volume), 2), tuple(np.round(b.bounds, 2).ravel()))  # full bounds: a rotated twin is a real part (review P3)
        if key in seen:
            continue
        seen.add(key); unique.append(b)
    return unique


def min_gap(a, b, samples):
    # the gap query is O(points x faces) on both meshes: a few hundred points already finds the closest
    # pair to ~0.01 mm on parts this size, and 4000 made a 200k-face box time out (22 Sep)
    samples = max(200, min(samples, GAP_SAMPLES_MAX))
    """Smallest surface-to-surface distance, sampled both ways (fit.py does the same:
    one direction misses the closest pair when triangle density differs). Negative = overlap."""
    pa = a.sample(samples)
    pb = b.sample(samples)
    d1 = trimesh.proximity.closest_point(b, pa)[1].min()
    d2 = trimesh.proximity.closest_point(a, pb)[1].min()
    return float(min(d1, d2))


def wall_thickness(mesh, samples):
    """5th-percentile thickness: from sampled surface points, ray inward, distance to the far wall.
    ponytail: a ray probe, not a medial axis — it reads thin ribs well and misses thin curved
    shells seen edge-on. Good enough to spot a 0.8 mm wall; do not quote it to 0.01 mm."""
    pts, face_idx = mesh.sample(samples, return_index=True)
    normals = mesh.face_normals[face_idx]
    origins = pts - normals * 1e-3
    hits, ray_idx, _ = mesh.ray.intersects_location(origins, -normals, multiple_hits=False)
    if len(hits) == 0:
        return None
    d = np.linalg.norm(hits - origins[ray_idx], axis=1)
    d = d[d > 1e-3]
    return float(np.percentile(d, 5)) if len(d) else None


def gear_teeth(mesh, samples=2048):
    """Tooth count from the radius-versus-angle wave of a mid-height cross-section, via FFT.
    Returns (teeth, pitch_radius_mm, module_mm) or None when the body is not gear-like."""
    ext = mesh.extents
    axis = int(np.argmin(ext))                       # a gear is a flat disc: its axis is the short side
    if ext[axis] <= 0 or max(ext) / ext[axis] < 2.0:
        return None
    wide = sorted(ext)[-2:]                          # the two in-plane sides of a gear are near equal (round)
    if wide[0] / wide[1] < 0.8:
        return None
    centre = mesh.bounds.mean(axis=0)
    normal = np.zeros(3); normal[axis] = 1.0
    section = mesh.section(plane_origin=centre, plane_normal=normal)
    if section is None:
        return None
    planar, _ = section.to_planar()
    pts = np.vstack([np.asarray(e.discrete(planar.vertices)) for e in planar.entities])
    c = pts.mean(axis=0)
    v = pts - c
    r = np.linalg.norm(v, axis=1)
    ang = np.arctan2(v[:, 1], v[:, 0])
    order = np.argsort(ang)
    grid = np.linspace(-np.pi, np.pi, samples, endpoint=False)
    rg = np.interp(grid, ang[order], r[order], period=2 * np.pi)
    spec = np.abs(np.fft.rfft(rg - rg.mean()))
    lo, hi = GEAR_MIN_TEETH, min(GEAR_MAX_TEETH, len(spec) - 1)
    if hi <= lo:
        return None
    teeth = int(lo + np.argmax(spec[lo:hi]))
    amp = spec[teeth] / (len(rg) / 2)
    mean_r = float(rg.mean())
    # A real tooth wave is BOTH a decent fraction of the radius and clearly the dominant frequency; without
    # both tests every bracket and plate came back "GEAR 6 teeth" (22 Sep, first run on James's files).
    band = np.delete(spec[lo:hi], teeth - lo)
    if amp < 0.02 * mean_r or (band.size and spec[teeth] < 2.5 * float(band.mean())):
        return None
    tooth_h = amp * 2                                 # peak-to-peak of the tooth wave
    if not (0.2 <= tooth_h <= 0.35 * mean_r):
        return None
    pitch_r = mean_r
    module = 2 * pitch_r / teeth
    if not (0.3 <= module <= 6.0):                    # outside this, it is not an FDM-printable gear
        return None
    return teeth, pitch_r, float(module)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json")
    ap.add_argument("--samples", type=int, default=2000)
    a = ap.parse_args()

    bs = bodies(a.path)
    if not bs:
        print("no solid bodies found"); sys.exit(1)
    report = {"file": a.path, "bodies": [], "pairs": []}
    print(f"{a.path}: {len(bs)} separate bodies")
    for i, m in enumerate(bs):
        g = gear_teeth(m)
        wall = wall_thickness(m, a.samples)
        row = {"i": i, "volume_mm3": round(float(m.volume), 1),
               "bbox_mm": [round(float(x), 2) for x in m.extents],
               "watertight": bool(m.is_watertight),
               "wall_p5_mm": round(wall, 2) if wall else None,
               "gear": {"teeth": g[0], "pitch_radius_mm": round(g[1], 2), "module_mm": round(g[2], 2)} if g else None}
        report["bodies"].append(row)
        line = f"  body {i}: {row['bbox_mm']} mm, {row['volume_mm3']} mm^3, thinnest wall ~{row['wall_p5_mm']} mm"
        if g:
            line += f", GEAR {g[0]} teeth, module {g[2]:.2f}"
        print(line)

    print("gaps between bodies (the working clearance of a print-in-place mechanism):")
    for i in range(len(bs)):
        for j in range(i + 1, len(bs)):
            # bounding boxes further apart than CLOSE_MM cannot have a closer surface pair: skip the sampling
            lo = np.maximum(bs[i].bounds[0], bs[j].bounds[0]) - np.minimum(bs[i].bounds[1], bs[j].bounds[1])
            if float(np.max(lo)) > CLOSE_MM:
                continue
            gap = min_gap(bs[i], bs[j], a.samples)
            if gap <= CLOSE_MM:
                report["pairs"].append({"a": i, "b": j, "gap_mm": round(gap, 3)})
                print(f"  {i}-{j}: {gap:.3f} mm")
    if report["pairs"]:
        tight = min(p["gap_mm"] for p in report["pairs"])
        report["smallest_gap_mm"] = tight
        print(f"smallest gap anywhere: {tight:.3f} mm")
    else:
        print("  none within 3 mm — this model is not print-in-place, or its parts print separately")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(report, f, indent=1)
        print(f"wrote {a.json}")


if __name__ == "__main__":
    main()
