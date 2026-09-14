"""Poop bag holder v4: replace the 4 raised serif letter shells with POOP debossed 0.8 mm into the lid.

Why: v3's raised serif text printed badly. Toolpaths were complete, but hairline serifs plus 32-36
retract/z-hop cycles per letter layer x 25 layers left the letters stringy and slumped.
Input: holder_v3.stl (already upright; lid top z=68.04, flat to r~22, lid >= 3.02 mm thick under the text).
"""
import numpy as np, trimesh
from build123d import BuildSketch, Text, Align, extrude, export_stl, Pos

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_SIZE = 13.0               # ~36 x 9 mm, about the old text's 36.9 x 10.3 mm footprint
CENTER = (0.0, 0.4)            # old text centre
LID_TOP = 68.04
DEPTH = 0.8                    # leaves >= 2.2 mm of lid

src = trimesh.load("holder_v3.stl", force="mesh"); src.merge_vertices()
body = sorted(src.split(only_watertight=False), key=lambda b: -b.volume)[0]   # drop the 4 letter shells

with BuildSketch() as sk:
    Text("POOP", font_size=FONT_SIZE, font_path=FONT, align=(Align.CENTER, Align.CENTER))
bb = sk.sketch.bounding_box()
cutter = Pos(CENTER[0], CENTER[1], LID_TOP - DEPTH) * extrude(sk.sketch, amount=DEPTH + 1.0)   # pokes 1 mm above the lid
export_stl(cutter, "text_cutter.stl", tolerance=0.01, angular_tolerance=0.1)
cut = trimesh.load("text_cutter.stl", force="mesh")

out = trimesh.boolean.difference([body, cut], engine="manifold")
out.merge_vertices(); out.update_faces(out.nondegenerate_faces()); out.remove_unreferenced_vertices()
shells = [b for b in out.split(only_watertight=False) if abs(b.volume) > 1.0]
assert len(shells) == 1 and shells[0].is_watertight, [(round(b.volume, 2), b.is_watertight) for b in shells]
out = shells[0]
out.export("holder_v4.stl"); out.export("holder_v4.3mf")

# stroke width of the new text (fraction of letter area narrower than 2 line widths = 0.84 mm)
from shapely.geometry import Polygon
from shapely.ops import unary_union
polys = []
for f in sk.sketch.faces():
    outer = [(v.X, v.Y) for v in f.outer_wire().positions([i / 200 for i in range(201)])]
    holes = [[(v.X, v.Y) for v in w.positions([i / 120 for i in range(121)])] for w in f.inner_wires()]
    polys.append(Polygon(outer, holes).buffer(0))
g = unary_union(polys); A = g.area
thin = 100 * (A - g.buffer(-0.42).buffer(0.42).area) / A
print(f"text {bb.size.X:.1f} x {bb.size.Y:.1f} mm at centre {CENTER}; letter area {A:.1f} mm2; area narrower than 0.84 mm: {thin:.0f}%")
print(f"volume {body.volume/1000:.2f} -> {out.volume/1000:.2f} cm3 (removed {body.volume-out.volume:.1f} mm3; expected ~{A*DEPTH:.1f})")
