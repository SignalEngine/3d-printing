"""Poop bag holder v5: POOP cut all the way through the lid as a stencil.

Decisions (James, 2026-09-14): stencil bridges hold the letter counters; a solid pad over the bag-roll peg.
Measured on v4/v3: lid top z=68.04, underside ~65.05, flat to r~22; peg centred (0,0), r 3.2 (3.6 at the lid join);
4 letters, 4 enclosed counters; O strokes cross within r<4 of the peg centre.
Starts from the text-free v3 body (letter shells dropped) so bridges keep the full 3 mm lid thickness.
"""
import numpy as np, trimesh
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union
from build123d import BuildSketch, Text, Align

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_SIZE, CX, CY = 13.0, 0.0, 0.4
BRIDGE_W = 1.2          # ~3 nozzle lines
PEG_PAD_R = 5.0         # solid lid over the peg (peg r 3.6 at the join)
FLAT_R = 21.0           # never cut past the flat lid area
CUT_Z = (64.4, 69.0)    # below the lid underside (65.05) to above the top (68.04)

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
        is_o = i in (1, 2)
        bridges.append(box(c.x - BRIDGE_W / 2, c.y, c.x + BRIDGE_W / 2, ymax + 1))            # up
        if is_o:
            bridges.append(box(c.x - BRIDGE_W / 2, ymin - 1, c.x + BRIDGE_W / 2, c.y))        # down
        else:
            bridges.append(box(c.x, c.y - BRIDGE_W / 2, xmax + 1, c.y + BRIDGE_W / 2))        # right (P bowl)
cut2d = unary_union(letters).difference(unary_union(bridges)).difference(Point(0, 0).buffer(PEG_PAD_R, 64))
cut2d = cut2d.intersection(Point(0, 0).buffer(FLAT_R, 128))

# CHECK 1: lid material inside the flat area stays ONE connected piece (no counters fall out)
material = Point(0, 0).buffer(FLAT_R, 128).difference(cut2d)
n_pieces = len(material.geoms) if isinstance(material, MultiPolygon) else 1
print(f"CHECK lid connected: {n_pieces} piece(s) -> {'PASS' if n_pieces == 1 else 'FAIL'}")
# CHECK 2: peg join fully covered by solid lid
peg_uncovered = Point(0, 0).buffer(3.6, 64).intersection(cut2d).area
print(f"CHECK peg join solid: uncut area over peg r3.6 missing {peg_uncovered:.2f} mm2 -> {'PASS' if peg_uncovered < 0.01 else 'FAIL'}")
print(f"cut-through area {cut2d.area:.1f} mm2 in {len(getattr(cut2d, 'geoms', [cut2d]))} opening(s); bridges {len(bridges)}")

src = trimesh.load("holder_v3.stl", force="mesh"); src.merge_vertices()
body = sorted(src.split(only_watertight=False), key=lambda b: -b.volume)[0]
pieces = [trimesh.creation.extrude_polygon(p, CUT_Z[1] - CUT_Z[0]) for p in getattr(cut2d, "geoms", [cut2d])]
cutter = trimesh.util.concatenate(pieces); cutter.apply_translation([0, 0, CUT_Z[0]])
out = trimesh.boolean.difference([body, trimesh.boolean.union(pieces and [cutter], engine="manifold")], engine="manifold")
out.merge_vertices(); out.update_faces(out.nondegenerate_faces()); out.remove_unreferenced_vertices()
shells = [b for b in out.split(only_watertight=False) if abs(b.volume) > 1.0]
assert len(shells) == 1 and shells[0].is_watertight, [(round(b.volume, 2), b.is_watertight) for b in shells]
out = shells[0]
out.export("holder_v5.stl"); out.export("holder_v5.3mf")
print(f"body vol {body.volume/1000:.2f} -> {out.volume/1000:.2f} cm3 (removed {body.volume-out.volume:.1f} mm3; lid-thickness estimate {cut2d.area*3.0:.0f})")
# CHECK 3: really through: a ray straight down through an opening centre hits nothing until the bore floor region
c = cut2d.representative_point()
loc, _, _ = out.ray.intersects_location([[c.x, c.y, 80]], [[0, 0, -1]], multiple_hits=True)
zs = sorted(loc[:, 2], reverse=True)
print(f"CHECK through: ray down at ({c.x:.1f},{c.y:.1f}) first hit z={zs[0] if zs else None} (lid top is 68.04) -> {'PASS' if not zs or zs[0] < 64 else 'FAIL'}")
