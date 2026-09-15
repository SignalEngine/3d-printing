"""Poop bag holder v5d: POOP centred on the lid, cut through as a stencil, EXCEPT over the bag-roll peg.

James wants a centred word (v5c sat above the peg, v5b split it). The peg joins the lid underside at
the centre (r 3.6), so within the peg pad the strokes are engraved 0.8 mm instead of cut through:
the word keeps its full outline from above and the lid stays >= 2.2 mm thick over the peg.
"""
import numpy as np, trimesh
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union
from build123d import BuildSketch, Text, Align

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_SIZE, CX, CY = 13.0, 0.0, 0.4          # same centred layout as v4
BRIDGE_W, PEG_PAD_R, FLAT_R = 1.2, 4.2, 21.0
LID_TOP, ENGRAVE = 68.04, 0.8
THROUGH_Z = (64.4, 69.0)

with BuildSketch() as sk:
    Text("POOP", font_size=FONT_SIZE, font_path=FONT, align=(Align.CENTER, Align.CENTER))
letters = []
for f in sk.sketch.faces():
    outer = [(v.X + CX, v.Y + CY) for v in f.outer_wire().positions([i / 240 for i in range(241)])]
    holes = [[(v.X + CX, v.Y + CY) for v in w.positions([i / 160 for i in range(161)])] for w in f.inner_wires()]
    letters.append(Polygon(outer, holes).buffer(0))
letters.sort(key=lambda g: g.centroid.x)
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
stencil = text.difference(unary_union(bridges))
pad = Point(0, 0).buffer(PEG_PAD_R, 64)
through2d = stencil.difference(pad).intersection(Point(0, 0).buffer(FLAT_R, 128))
engrave2d = text.intersection(pad)                     # full letter shape over the peg, engraved only

far = max(Point(0, 0).distance(Point(x, y)) for g in letters for x, y in g.exterior.coords)
print(f"centred word: font {FONT_SIZE}, centre ({CX},{CY}), farthest point r={far:.2f} (flat lid {FLAT_R}) -> {'PASS' if far <= FLAT_R - 0.5 else 'FAIL'}")
material = Point(0, 0).buffer(FLAT_R, 128).difference(through2d)
n = len(material.geoms) if isinstance(material, MultiPolygon) else 1
print(f"CHECK lid connected (through-cuts only): {n} piece(s) -> {'PASS' if n == 1 else 'FAIL'}")
print(f"CHECK nothing cut through over the peg join: {Point(0,0).buffer(3.6,64).intersection(through2d).area:.2f} mm2 -> {'PASS' if Point(0,0).buffer(3.6,64).intersection(through2d).area < 0.01 else 'FAIL'}")
print(f"engraved-only area over the peg: {engrave2d.area:.1f} mm2; through-cut area {through2d.area:.1f} mm2")

src = trimesh.load("holder_v3.stl", force="mesh"); src.merge_vertices()
body = sorted(src.split(only_watertight=False), key=lambda b: -b.volume)[0]
def prism(geom, z0, z1):
    ps = [trimesh.creation.extrude_polygon(p, z1 - z0) for p in getattr(geom, "geoms", [geom]) if p.area > 0.01]
    m = trimesh.boolean.union(ps, engine="manifold") if len(ps) > 1 else ps[0]
    m.apply_translation([0, 0, z0]); return m
cutter = trimesh.boolean.union([prism(through2d, *THROUGH_Z), prism(engrave2d, LID_TOP - ENGRAVE, THROUGH_Z[1])], engine="manifold")
out = trimesh.boolean.difference([body, cutter], engine="manifold")
out.merge_vertices(); out.update_faces(out.nondegenerate_faces()); out.remove_unreferenced_vertices()
shells = [b for b in out.split(only_watertight=False) if abs(b.volume) > 1.0]
assert len(shells) == 1 and shells[0].is_watertight, [(round(b.volume, 2), b.is_watertight) for b in shells]
out = shells[0]; out.export("holder_v5d.stl"); out.export("holder_v5d.3mf")
exp = through2d.area * 2.99 + engrave2d.area * ENGRAVE
print(f"body vol {body.volume/1000:.2f} -> {out.volume/1000:.2f} cm3 (removed {body.volume-out.volume:.1f}; expected ~{exp:.0f})")

# CHECK engraving depth over the peg + lid thickness left there
pts = [engrave2d.representative_point()]
for p in pts:
    loc, _, _ = out.ray.intersects_location([[p.x, p.y, 80.0]], [[0, 0, -1.0]], multiple_hits=False)
    top = loc[0, 2] if len(loc) else None
    print(f"CHECK engraved (not through) over the peg at ({p.x:.1f},{p.y:.1f}): surface z={top:.2f} (lid top {LID_TOP}, want {LID_TOP-ENGRAVE:.2f}) -> {'PASS' if top is not None and abs(top-(LID_TOP-ENGRAVE))<0.05 else 'FAIL'}")
c = through2d.representative_point()
loc, _, _ = out.ray.intersects_location([[c.x, c.y, 80.0]], [[0, 0, -1.0]], multiple_hits=True)
print(f"CHECK through elsewhere at ({c.x:.1f},{c.y:.1f}): first hit {'none' if not len(loc) else round(max(loc[:,2]),2)} -> {'PASS' if (not len(loc)) or max(loc[:,2]) < 64 else 'FAIL'}")
