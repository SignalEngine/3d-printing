"""Poop bag holder v5c: POOP cut through as ONE stencil word, moved up to clear the bag-roll peg.

v5b split the word 'PO | OP' around the peg; James: 'it should say poop'.
The O's cross the peg join at the lid centre, so the word shifts up (+Y) until no letter touches
the peg pad, at the largest font that still fits inside the flat lid.
"""
import numpy as np, trimesh
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.affinity import translate
from shapely.ops import unary_union
from build123d import BuildSketch, Text, Align

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
BRIDGE_W, PEG_PAD_R, PAD_MARGIN, FLAT_R, EDGE_MARGIN = 1.2, 4.2, 0.6, 21.0, 0.8
CUT_Z = (64.4, 69.0)

def layout(size):
    with BuildSketch() as sk:
        Text("POOP", font_size=size, font_path=FONT, align=(Align.CENTER, Align.CENTER))
    L = []
    for f in sk.sketch.faces():
        outer = [(v.X, v.Y) for v in f.outer_wire().positions([i / 240 for i in range(241)])]
        holes = [[(v.X, v.Y) for v in w.positions([i / 160 for i in range(161)])] for w in f.inner_wires()]
        L.append(Polygon(outer, holes).buffer(0))
    L.sort(key=lambda g: g.centroid.x)
    ymin = min(g.bounds[1] for g in L)
    dy = (PEG_PAD_R + PAD_MARGIN) - ymin          # lowest point of the word sits just above the pad
    L = [translate(g, 0, dy) for g in L]
    far = max(Point(0, 0).distance(Point(x, y)) for g in L for x, y in g.exterior.coords)
    return L, dy, far

size = 14.0
while size > 6:
    letters, dy, far = layout(size)
    if far <= FLAT_R - EDGE_MARGIN:
        break
    size -= 0.25
print(f"font {size:.2f}: word shifted +{dy:.2f} mm in Y; farthest point r={far:.2f} (limit {FLAT_R-EDGE_MARGIN})")

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
cut2d = text.difference(unary_union(bridges)).difference(pad).intersection(Point(0, 0).buffer(FLAT_R, 128))
material = Point(0, 0).buffer(FLAT_R, 128).difference(cut2d)
n = len(material.geoms) if isinstance(material, MultiPolygon) else 1
print(f"CHECK one word, no letter under the pad: {text.intersection(pad).area:.2f} mm2 -> {'PASS' if text.intersection(pad).area < 0.01 else 'FAIL'}")
print(f"CHECK lid connected: {n} piece(s) -> {'PASS' if n == 1 else 'FAIL'}")
print(f"CHECK peg join solid: {Point(0,0).buffer(3.6,64).intersection(cut2d).area:.2f} mm2 cut -> {'PASS' if Point(0,0).buffer(3.6,64).intersection(cut2d).area < 0.01 else 'FAIL'}")
thin = 100 * (text.area - text.buffer(-0.42).buffer(0.42).area) / text.area
gaps = [round(letters[i + 1].bounds[0] - letters[i].bounds[2], 2) for i in range(3)]
print(f"strokes narrower than 0.84 mm: {thin:.0f}%; letter gaps {gaps} mm (even spacing = reads as one word); cut {cut2d.area:.1f} mm2")

src = trimesh.load("holder_v3.stl", force="mesh"); src.merge_vertices()
body = sorted(src.split(only_watertight=False), key=lambda b: -b.volume)[0]
pieces = [trimesh.creation.extrude_polygon(p, CUT_Z[1] - CUT_Z[0]) for p in getattr(cut2d, "geoms", [cut2d])]
cutter = trimesh.boolean.union(pieces, engine="manifold") if len(pieces) > 1 else pieces[0]
cutter.apply_translation([0, 0, CUT_Z[0]])
out = trimesh.boolean.difference([body, cutter], engine="manifold")
out.merge_vertices(); out.update_faces(out.nondegenerate_faces()); out.remove_unreferenced_vertices()
shells = [b for b in out.split(only_watertight=False) if abs(b.volume) > 1.0]
assert len(shells) == 1 and shells[0].is_watertight, [(round(b.volume, 2), b.is_watertight) for b in shells]
out = shells[0]; out.export("holder_v5c.stl"); out.export("holder_v5c.3mf")
print(f"body vol {body.volume/1000:.2f} -> {out.volume/1000:.2f} cm3 (removed {body.volume-out.volume:.1f}; through-cut expects ~{cut2d.area*2.99:.0f})")
