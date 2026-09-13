#!/usr/bin/env python3
"""Render a model to a multi-view PNG. MANDATORY step: geometric checks pass on
models that are valid but functionally wrong (holes in the wrong face, mirrored
parts, features on the wrong side). You must LOOK at the render with the view tool.

Usage: python3 render_views.py <model.stl|.3mf|.step> <out.png> [--section]
Produces 4 views: iso, front, top, + either second iso or a Z-section cut
(--section shows internal voids/holes — use for anything with internal features).
"""
import sys, argparse, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def load_any(path):
    if path.lower().endswith((".step", ".stp")):
        from build123d import import_step, export_stl
        import tempfile, os
        tmp = tempfile.mktemp(suffix=".stl")
        export_stl(import_step(path), tmp, tolerance=0.01, angular_tolerance=0.1)
        m = trimesh.load(tmp, force="mesh"); os.unlink(tmp); return m
    return trimesh.load(path, force="mesh")

def draw(ax, mesh, elev, azim, title):
    ax.add_collection3d(Poly3DCollection(mesh.triangles, facecolors="#8fb4cf",
                                         edgecolor="none", linewidth=0, alpha=1.0, shade=True))
    b = mesh.bounds; c = b.mean(0); r = (b[1]-b[0]).max()/2*1.05
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(title, fontsize=9)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model"); ap.add_argument("out")
    ap.add_argument("--section", action="store_true", help="4th view = Z midplane cut")
    a = ap.parse_args()
    m = load_any(a.model)
    fig = plt.figure(figsize=(13, 3.6))
    views = [(28, -55, "iso"), (2, -90, "front"), (89, -90, "top")]
    for i, (e, az, t) in enumerate(views):
        draw(fig.add_subplot(1, 4, i+1, projection="3d"), m, e, az, t)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    if a.section:
        zc = m.bounds.mean(0)[2]
        cut = m.slice_plane(plane_origin=[0, 0, zc], plane_normal=[0, 0, -1], cap=True)
        draw(ax4, cut, 35, -55, "section @ mid-Z")
    else:
        draw(ax4, m, 28, 125, "iso rear")
    plt.tight_layout(); plt.savefig(a.out, dpi=100)
    print("wrote", a.out)

if __name__ == "__main__":
    main()
