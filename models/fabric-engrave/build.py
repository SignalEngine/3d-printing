#!/usr/bin/env python3
"""Build the fabric face-engrave test models + the print plate. Run from anywhere:
    /root/3d-printing/.venv/bin/python models/fabric-engrave/build.py [--preview]

Each design = an outline (reused from models/fabric-tests/<name>.3mf.json) + a bold face drawn as polygons in the outline's
frame (mm, origin at the outline's bounding-box corner, seen from the TOP; the face side is the bed side, so a person looking at
the face sees the sheet mirrored). Every face is symmetric about the sheet's vertical axis so the mirror changes nothing.
The polygons are committed as face-<name>.json and cut ONE layer into the face (fabric.py --engrave). --preview writes only
outline+design drawings to /tmp (no models)."""
import json, math, os, subprocess, sys
import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "skills", "model-forge", "scripts")
sys.path.insert(0, SCRIPTS)
import fabric  # noqa: E402

GAP = 0.4
DEPTH = 0.2


def spec_of(name):
    return json.load(open(os.path.join(HERE, "..", "fabric-tests", f"{name}.3mf.json")))["outline"]


def oval(cx, cy, rx, ry):
    return affinity.scale(Point(cx, cy).buffer(1, 32), rx, ry)


def star(cx, cy, r_out, r_in, n=5):
    pts = [(cx + (r_out if i % 2 == 0 else r_in) * math.sin(math.pi * i / n),
            cy + (r_out if i % 2 == 0 else r_in) * math.cos(math.pi * i / n)) for i in range(2 * n)]
    return Polygon(pts)


def ghost_face(cx, cy):
    return [oval(cx - 17, cy + 10, 6, 9), oval(cx + 17, cy + 10, 6, 9),
            Point(cx, cy - 15).buffer(9, 32).difference(Point(cx, cy - 15).buffer(4.5, 32))]


def pumpkin_face(cx, cy):
    zig = LineString([(cx + dx, cy - 30 if i % 2 else cy - 22) for i, dx in enumerate((-30, -20, -10, 0, 10, 20, 30))]).buffer(1.75, cap_style=2, join_style=2)
    return [Polygon([(cx - 28, cy + 2), (cx - 4, cy + 2), (cx - 16, cy + 18)]), Polygon([(cx + 4, cy + 2), (cx + 28, cy + 2), (cx + 16, cy + 18)]),
            Polygon([(cx - 5, cy - 8), (cx + 5, cy - 8), (cx, cy + 0)]), zig]


def bat_face(cx, cy):
    fang = lambda x: Polygon([(x - 3.5, cy - 6), (x + 3.5, cy - 6), (x, cy - 17)])
    return [oval(cx - 14, cy + 10, 6, 8), oval(cx + 14, cy + 10, 6, 8),
            box(cx - 16, cy - 6, cx + 16, cy - 1), fang(cx - 9), fang(cx + 9)]


def coaster_face(cx, cy):
    return [star(cx, cy, 34, 14)]


# name: (tile, face fn)
DESIGNS = {
    "pumpkin-drape": ("drape", "pumpkin-drape", pumpkin_face, "jack-o'-lantern: triangle eyes, triangle nose, zigzag mouth"),
    "bat-drape": ("drape", "bat-drape", bat_face, "two oval eyes and a fanged mouth"),
    "ghost-drape": ("drape", "ghost-square", ghost_face, "two oval eyes and an O mouth"),
    "ghost-square": ("square", "ghost-square", ghost_face, "two oval eyes and an O mouth (square tile, to compare)"),
    "coaster90-drape": ("drape", "coaster90-drape", coaster_face, "a five-point star"),
}
# plate 256 x 256, >= 10 mm between designs, origin = the sheet's own frame corner (fabric.py --origin shifts every tile)
PLATE = ["bat-drape", "pumpkin-drape", "ghost-drape", "ghost-square"]
LAYOUT = {"bat-drape": (0, 0), "pumpkin-drape": (158, 0), "ghost-drape": (0, 90), "ghost-square": (124, 90)}


def face_json(name, polys):
    path = os.path.join(HERE, f"face-{name}.json")
    doc = {"note": "polygons in the outline's frame: mm, origin at the outline's bounding-box corner, seen from the top; "
                   "cut one layer into the face by fabric.py --engrave",
           "polys": [[[round(x, 3), round(y, 3)] for x, y in p.exterior.coords[:-1]] for g in polys for p in getattr(g, "geoms", [g])]}
    json.dump(doc, open(path, "w"), indent=1)
    return path


def _polys(cs):
    from functools import reduce
    ps = [Polygon(p) for p in cs.to_polygons() if len(p) >= 3]
    return reduce(lambda a, b: a.symmetric_difference(b), ps) if ps else Polygon()


def render_face(tiles, depth, out_png, title):
    """The FACE as a person sees it (the bed side): colour 1 = material below z = depth, colour 2 = what shows in the pockets
    (material only above it). One shared XY frame for every tile (world coordinates, no per-tile centring), x mirrored."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig, ax = plt.subplots(figsize=(9, 9), facecolor="#8a8f98")
    ax.set_facecolor("#8a8f98")
    for col, pick in (("#15151a", "one"), ("#f4f1e8", "two")):
        verts = []
        for _, _, _, m in tiles:
            man = fabric._manifold(m)
            a, b = _polys(man.slice(depth / 2)), _polys(man.slice(depth + 0.1))
            g = a if pick == "one" else b.difference(a)
            for p in getattr(g, "geoms", [g]):
                if p.geom_type == "Polygon" and not p.is_empty:
                    verts.append(np.asarray(p.exterior.coords))
        ax.add_collection(PolyCollection(verts, facecolors=col, edgecolors="none"))
    allv = np.vstack([m.vertices for _, _, _, m in tiles])
    lo, hi = allv.min(0)[:2], allv.max(0)[:2]
    ax.set_xlim(hi[0] + 2, lo[0] - 2)             # x runs right to left: the face seen from below
    ax.set_ylim(lo[1] - 2, hi[1] + 2)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(f"{title}: face view (colour 1 dark, colour 2 white)", color="white", fontsize=10)
    fig.savefig(out_png, dpi=100, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def preview(name, tile, outline, polys):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pitch = fabric.TILE_PITCH[tile]
    o = fabric.Outline(spec_of(outline), pitch)
    cells, _ = fabric.fill(o, pitch)
    fig, ax = plt.subplots(figsize=(9, 9))
    for r, c in cells:
        ax.add_patch(plt.Rectangle((c * pitch, r * pitch), pitch, pitch, fc="#ddd", ec="#888", lw=.5))
    for g in polys:
        for p in getattr(g, "geoms", [g]):
            ax.fill(*p.exterior.xy, fc="#c33", alpha=.6)
    ax.set_aspect("equal"); ax.autoscale()
    fig.savefig(f"/tmp/engrave-preview-{name}.png", dpi=70)
    plt.close(fig)


def readme(name, tile, what, info, res):
    return f"""# {name} (face engrave, one filament swap)

{what}. Tile: **{tile}**, {info['tiles']} tiles, engraved {info['engrave_depth']:g} mm into the face.

**Load the FACE colour (colour 1) first.** Bambu Studio: slice, open Preview, drag the layer slider to **layer {info['swap_layer']}**,
right-click the `+` and choose **Change filament**. The A1 pauses once (after layer {info['swap_layer'] - 1}); load colour 2 and resume. No swap back.
The bed side is the face. The design shows in colour 2 in the pockets cut into it.

- Print flat, supports OFF. Settings: no brim, elephant foot 0.15, 2 walls, 0.20 mm layers.
- Swap at layer {info['swap_layer']} (Z {info['swap_z_mm']:g} mm). Colour 1 is layer 1 (the face), colour 2 fills the pockets from layer 2.
- Every tile keeps a {fabric.RIM:g} mm colour-1 rim so it still sticks to the bed: {info['engrave_clipped_tiles']} tiles had the design clipped to keep their bed grip; {info['engrave_dropped']} design pieces under 0.8 mm wide dropped.
- The design is drawn in the outline's top view (`face-{name}.json`); a person looking at the face sees it mirrored left-right (these faces are symmetric).
- Check: `fabric.py --check {name}.3mf --gap {GAP}` -> ok={res['ok']}, {res['tiles']} tiles, {res['bodies']} bodies, min gap {res['min_gap_mm']} mm, {res['fused_pairs']} fused.
- Rebuild: `build.py`.
"""


def main():
    pv = "--preview" in sys.argv
    reports = {}
    for name, (tile, outline, face_fn, what) in DESIGNS.items():
        pitch = fabric.TILE_PITCH[tile]
        spec = spec_of(outline)
        o = fabric.Outline(spec, pitch)
        cells, _ = fabric.fill(o, pitch)      # centre the face on the tiles, not on the outline's bounding box
        rs, cs = [r for r, _ in cells], [c for _, c in cells]
        polys = face_fn((min(cs) + max(cs) + 1) * pitch / 2, (min(rs) + max(rs) + 1) * pitch / 2)
        if pv:
            preview(name, tile, outline, polys)
            continue
        mask = face_json(name, polys)
        out = os.path.join(HERE, f"{name}.3mf")
        rc = fabric.main(["--outline", spec, "--tile", tile, "--gap", str(GAP), "--engrave", mask, "--engrave-depth", str(DEPTH), "--out", out])
        if rc:
            raise SystemExit(f"{name}: fabric.py exit {rc}")
        info = json.load(open(out + ".json"))
        res = fabric.check_sheet(out, GAP)
        assert res["ok"] and res["fused_pairs"] == 0, (name, res)
        tiles, _ = fabric.build_sheet(spec, pitch, None if tile == "drape" else 3.0, GAP, tile=tile, engrave=mask, engrave_depth=DEPTH)
        cont = [round(fabric.bed_contact(m), 1) for _, _, _, m in tiles]
        render_face(tiles, DEPTH, os.path.join(HERE, f"{name}-face.png"), name)
        open(os.path.join(HERE, f"README-{name}.md"), "w").write(readme(name, tile, what, info, res))
        reports[name] = {"tile": tile, "tiles": info["tiles"], "swap_layer": info["swap_layer"], "swap_z_mm": info["swap_z_mm"], "bbox": info["bbox"],
                         "engrave_clipped_tiles": info["engrave_clipped_tiles"], "engrave_dropped": info["engrave_dropped"],
                         "min_bed_contact_mm2": min(cont), "check": res}
        print(name, json.dumps(reports[name]))
    if pv:
        return
    json.dump(reports, open(os.path.join(HERE, "report.json"), "w"), indent=1)
    build_plate()


def build_plate():
    parts, rects, layout, swap = [], [], [], set()
    for name in PLATE:
        tile, outline, _, _ = DESIGNS[name]
        pitch = fabric.TILE_PITCH[tile]
        tiles, info = fabric.build_sheet(spec_of(outline), pitch, None if tile == "drape" else 3.0, GAP, origin=LAYOUT[name], prefix=f"{name}-",
                                         tile=tile, engrave=os.path.join(HERE, f"face-{name}.json"), engrave_depth=DEPTH)
        parts += tiles
        swap.add(info["swap_z_mm"])
        x0, y0, x1, y1 = info["bbox"]
        rects.append(box(x0, y0, x1, y1))
        layout.append({"design": name, "tile": tile, "tiles": info["tiles"], "at_mm": list(LAYOUT[name]), "size_mm": [round(x1 - x0, 1), round(y1 - y0, 1)]})
    assert len(swap) == 1, swap
    swap_z = swap.pop()
    gaps = [a.distance(b) for i, a in enumerate(rects) for b in rects[i + 1:]]
    allv = np.vstack([m.vertices for _, _, _, m in parts])
    ext = (allv.max(0) - allv.min(0)).round(1).tolist()
    assert ext[0] <= 256 and ext[1] <= 256, ext
    assert min(gaps) >= 10, f"designs closer than 10 mm: {min(gaps):.1f}"
    out = os.path.join(HERE, "print-plate.3mf")
    fabric.export(parts, [], out)
    res = fabric.check_sheet(out, GAP)
    doc = {"layout": layout, "extents_mm": ext, "min_gap_between_designs_mm": round(min(gaps), 1), "swap_z_mm": swap_z,
           "swap_layer": round(swap_z / fabric.LAYER_H) + 1, "tiles": len(parts), "check": res,
           "not_on_plate": [n for n in DESIGNS if n not in PLATE]}
    sl = subprocess.run([sys.executable, os.path.join(SCRIPTS, "slice_gate.py"), out, "--supports", "none"], capture_output=True, text=True, timeout=1800)
    doc["slice_gate"] = [l for l in sl.stdout.splitlines() if l.split(":")[0] in ("estimated print time", "filament", "supports", "RESULT")]
    doc["slice_gate_rc"] = sl.returncode
    json.dump(doc, open(os.path.join(HERE, "print-plate.json"), "w"), indent=1)
    render_face(parts, DEPTH, os.path.join(HERE, "print-plate-face.png"), "print-plate")
    print("print-plate", json.dumps(doc))


if __name__ == "__main__":
    main()
