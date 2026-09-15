"""Poop bag holder v5b: stencil POOP cut through, split 'PO | OP' around the bag-roll peg pad.

v5 kept a 5 mm pad over the peg, but the pad filled ~half of each O (render + OCR 'FCJF').
v5b: font 11, the two halves pushed apart so neither O touches the pad; pad r=4.2 (peg join r 3.6 + 0.6).
"""
import sys, numpy as np, trimesh
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union
from build123d import BuildSketch, Text, Align

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_SIZE, CY = 11.0, 0.4
BRIDGE_W, PEG_PAD_R, PAD_MARGIN, FLAT_R = 1.2, 4.2, 0.6, 21.0
CUT_Z = (64.4, 69.0)

with BuildSketch() as sk:
    Text("POOP", font_size=FONT_SIZE, font_path=FONT, align=(Align.CENTER, Align.CENTER))
letters = []
for f in sk.sketch.faces():
    outer = [(v.X, v.Y + CY) for v in f.outer_wire().positions([i / 240 for i in range(241)])]
    holes = [[(v.X, v.Y + CY) for v in w.positions([i / 160 for i in range(161)])] for w in f.inner_wires()]
    letters.append(Polygon(outer, holes).buffer(0))
letters.sort(key=lambda g: g.centroid.x)
from shapely.affinity import translate
need = PEG_PAD_R + PAD_MARGIN
dx_left = max(0.0, letters[1].bounds[2] + need)      # left O's right edge must sit at x <= -need
dx_right = max(0.0, need - letters[2].bounds[0])      # right O's left edge must sit at x >= +need
letters = [translate(g, -dx_left) for g in letters[:2]] + [translate(g, dx_right) for g in letters[2:]]
far = max(Point(0, 0).distance(Point(x, y)) for g in letters for x, y in g.exterior.coords)
print(f"split: left pair -{dx_left:.2f} mm, right pair +{dx_right:.2f} mm; farthest letter point r={far:.2f} (flat lid r {FLAT_R}) -> {'PASS' if far <= FLAT_R - 0.5 else 'FAIL'}")

bridges = []
for i, g in enumerate(letters):
    xmin, ymin, xmax, ymax = g.bounds
    for ring in g.interiors:
        c = Polygon(ring).centroid
        bridges.append(box(c.x - BRIDGE_W / 2, c.y, c.x + BRIDGE_W / 2, ymax + 1))
        if i in (1, 2):
            bridges.append(box(c.x - BRIDGE_W / 2, ymin - 1, c.x + BRIDGE_W / 2, c.y))
        else:
            bridges.append(box(c.x, c.y - BRIDGE_W / 2, xmax + 1, c.y + BRIDGE_W / 2))
text = unary_union(letters)
pad = Point(0, 0).buffer(PEG_PAD_R, 64)
print(f"text stroke area under the pad: {text.intersection(pad).area:.2f} mm2 (v5 pad removed a lot; want 0)")
cut2d = text.difference(unary_union(bridges)).difference(pad).intersection(Point(0, 0).buffer(FLAT_R, 128))
material = Point(0, 0).buffer(FLAT_R, 128).difference(cut2d)
n = len(material.geoms) if isinstance(material, MultiPolygon) else 1
print(f"CHECK lid connected: {n} piece(s) -> {'PASS' if n == 1 else 'FAIL'}")
print(f"CHECK peg join solid: {Point(0,0).buffer(3.6,64).intersection(cut2d).area:.2f} mm2 cut over peg -> {'PASS' if Point(0,0).buffer(3.6,64).intersection(cut2d).area < 0.01 else 'FAIL'}")
thin = 100 * (text.area - text.buffer(-0.42).buffer(0.42).area) / text.area
print(f"strokes narrower than 0.84 mm: {thin:.0f}%; cut area {cut2d.area:.1f} mm2 in {len(getattr(cut2d,'geoms',[cut2d]))} openings")

src = trimesh.load("holder_v3.stl", force="mesh"); src.merge_vertices()
body = sorted(src.split(only_watertight=False), key=lambda b: -b.volume)[0]
pieces = [trimesh.creation.extrude_polygon(p, CUT_Z[1] - CUT_Z[0]) for p in getattr(cut2d, "geoms", [cut2d])]
cutter = trimesh.boolean.union(pieces, engine="manifold") if len(pieces) > 1 else pieces[0]
cutter.apply_translation([0, 0, CUT_Z[0]])
out = trimesh.boolean.difference([body, cutter], engine="manifold")
out.merge_vertices(); out.update_faces(out.nondegenerate_faces()); out.remove_unreferenced_vertices()
shells = [b for b in out.split(only_watertight=False) if abs(b.volume) > 1.0]
assert len(shells) == 1 and shells[0].is_watertight, [(round(b.volume, 2), b.is_watertight) for b in shells]
out = shells[0]; out.export("holder_v5b.stl"); out.export("holder_v5b.3mf")
print(f"body vol {body.volume/1000:.2f} -> {out.volume/1000:.2f} cm3 (removed {body.volume-out.volume:.1f}; expected ~{cut2d.area*2.99:.0f})")
