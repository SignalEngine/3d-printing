#!/usr/bin/env python3
"""Text check: OCR-verify that a model actually carries the ordered text.

A render can mislead (iso view read a trophy's text backwards in practice).
This takes real cross-sections through the mesh, renders each as a black-on-
white silhouette, and reads it with tesseract in every rotation/mirror so
orientation can't hide a wrong or missing letter.

Usage: python3 text_check.py <model.stl|.3mf|.step> --expect "TEXT" [--axis x|y|z] [--steps 12]
Exit 0 = PASS, 1 = FAIL (text not found), 2 = ERROR (tesseract missing).
"""
import os, sys, argparse, subprocess, shutil, tempfile, re
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AXES = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}


def load_any(path):
    if path.lower().endswith((".step", ".stp")):
        from build123d import import_step, export_stl
        fd, tmp = tempfile.mkstemp(suffix=".stl"); os.close(fd)
        export_stl(import_step(path), tmp, tolerance=0.01, angular_tolerance=0.1)
        m = trimesh.load(tmp, force="mesh"); os.unlink(tmp)
        return m
    return trimesh.load(path, force="mesh")


def normalize(text):
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def sections_for_axis(mesh, axis_name):
    normal = AXES[axis_name]
    axis_i = normal.index(1)
    lo, hi = mesh.bounds[0][axis_i], mesh.bounds[1][axis_i]
    margin = (hi - lo) * 0.05
    heights = np.linspace(lo + margin, hi - margin, STEPS)
    origin = mesh.bounds[0].copy()
    origin[axis_i] = 0.0
    paths = mesh.section_multiplane(plane_origin=origin, plane_normal=normal, heights=heights)
    return [(axis_name, h, p) for h, p in zip(heights, paths) if p is not None and len(p.polygons_full)]


def render_section(path2d, outfile):
    fig, ax = plt.subplots()
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    for poly in path2d.polygons_full:
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor="black", edgecolor="none")
        for interior in poly.interiors:
            xi, yi = interior.xy
            ax.fill(xi, yi, facecolor="white", edgecolor="none")
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(outfile, dpi=150, bbox_inches="tight", pad_inches=0.3, facecolor="white")
    plt.close(fig)


def ocr_all_orientations(png_path):
    from PIL import Image
    im = Image.open(png_path).convert("L")
    reads = []
    for rotation in (0, 90, 180, 270):
        rotated = im.rotate(rotation, expand=True, fillcolor=255)
        for mirrored, img in ((False, rotated), (True, rotated.transpose(Image.FLIP_LEFT_RIGHT))):
            fd, tmp = tempfile.mkstemp(suffix=".png"); os.close(fd)
            img.save(tmp)
            proc = subprocess.run(["tesseract", tmp, "stdout", "--psm", "6"],
                                   capture_output=True, text=True)
            os.unlink(tmp)
            reads.append((proc.stdout.strip(), rotation, mirrored))
    return reads


STEPS = 12


def main():
    global STEPS
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--expect", required=True)
    ap.add_argument("--axis", choices=["x", "y", "z"], default=None)
    ap.add_argument("--steps", type=int, default=12)
    a = ap.parse_args()
    STEPS = a.steps

    if not shutil.which("tesseract"):
        print("ERROR: tesseract not found on PATH.")
        sys.exit(2)

    mesh = load_any(a.model)
    axes = [a.axis] if a.axis else ["x", "y", "z"]

    expect_norm = normalize(a.expect)
    all_reads = []  # (normalized_text, raw_text, axis, offset, rotation, mirrored)

    with tempfile.TemporaryDirectory() as tmpdir:
        for axis_name in axes:
            for section_axis, height, path2d in sections_for_axis(mesh, axis_name):
                png = os.path.join(tmpdir, f"sec_{section_axis}_{height:.2f}.png")
                render_section(path2d, png)
                for raw, rotation, mirrored in ocr_all_orientations(png):
                    norm = normalize(raw)
                    if norm:
                        all_reads.append((norm, raw, section_axis, height, rotation, mirrored))

    matches = [r for r in all_reads if expect_norm and expect_norm in r[0]]
    if matches:
        norm, raw, axis_name, height, rotation, mirrored = matches[0]
        mirror_str = " mirrored" if mirrored else ""
        print(f"best read: {raw} (axis {axis_name}, offset {height:.1f}mm, "
              f"rotation {rotation}{mirror_str})")
        print("RESULT: PASS")
        sys.exit(0)

    print(f"expected: {a.expect} (normalized: {expect_norm})")
    if all_reads:
        # rank by longest common substring length with the expected text, best first
        def score(r):
            norm = r[0]
            best = 0
            for i in range(len(norm)):
                for j in range(i + 1, len(norm) + 1):
                    if norm[i:j] in expect_norm:
                        best = max(best, j - i)
            return best
        ranked = sorted(all_reads, key=score, reverse=True)[:3]
        for norm, raw, axis_name, height, rotation, mirrored in ranked:
            mirror_str = " mirrored" if mirrored else ""
            print(f"closest read: {raw!r} (axis {axis_name}, offset {height:.1f}mm, "
                  f"rotation {rotation}{mirror_str})")
    else:
        print("no text read from any section.")
    print("RESULT: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
