#!/usr/bin/env python3
"""Fabric generator: print-in-place linked-tile sheet (chainmail style) filling an outline.

One tile shape, checkerboard: "A" tiles have bridges (arch over a slot) on their +-x sides and tabs on +-y;
"B" tiles are A rotated 90 degrees. A tab reaches under the neighbour's bridge and ends in an upturned lip
that catches the bridge, so the pair cannot slide apart. Every tab/bridge face keeps `gap` clearance.
Printable flat, no supports: every overhang is vertical or a straight bridge <= 3.2 mm; every tile sits on z=0.

Usage: fabric.py --outline rect:W,H | rrect:W,H,R | circle:D | heart:W | poly:"x,y x,y ..." | text:"ABC" [--pitch 10] [--height 3.0]
                 [--gap 0.4] --out fabric.3mf [--swatch]
Writes <out> (one 3MF object per tile, `tile-r<row>-c<col>`) and <out>.json. Exit 2 = refused (bed / bad input).

       fabric.py --check X.3mf [--gap G]   re-measures the real geometry, prints one JSON line
                 {"ok","tiles","bodies","min_gap_mm","fused_pairs","detail"}; exit 0 if ok else 1.
"""
import argparse, json, math, os, sys
import numpy as np
import trimesh
import manifold3d as m3d

BED = 256.0
DEFAULT_GAP = 0.4        # placeholder until James's swatch print picks the real value
PLATE_T = 1.2            # plate + tab thickness (6 layers at 0.2)
TAB_W, LEG_W, BAR_U0, BAR_W, LIP_W = 2.0, 1.0, 0.6, 1.2, 1.0
LIP_H = 1.2              # lip rise above the tab; must exceed gap to catch the bridge
MIN_FEATURE = 0.8


def _box(x0, x1, y0, y1, z0, z1):
    return m3d.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def _oriented(n, o0, o1, t0, t1, z0, z1):
    """Box from outward-distance range [o0,o1] along unit normal n and tangent range [t0,t1] (tangent = n rotated 90)."""
    tx, ty = -n[1], n[0]
    xs = sorted((n[0] * o0 + tx * t0, n[0] * o1 + tx * t1))
    ys = sorted((n[1] * o0 + ty * t0, n[1] * o1 + ty * t1))
    return _box(xs[0], xs[1], ys[0], ys[1], z0, z1)


def tile_manifold(pitch, height, gap, present, lip_h=LIP_H):
    """Tile in its own frame (centre at origin). present: {(nx,ny): bool} neighbour on that local side.
    Bridge sides are +-x, tab sides are +-y."""
    hg, half = gap / 2, pitch / 2
    w = half - hg
    sw = TAB_W / 2 + gap                       # slot half width
    bar_u1 = BAR_U0 + BAR_W
    lip_u0 = bar_u1 + gap
    tab_u = lip_u0 + LIP_W                     # tab tip, measured inward from the neighbour's plate edge
    slot_u = tab_u + gap
    plate = _box(-w, w, -w, w, 0, PLATE_T)
    adds = []
    for n in ((1, 0), (-1, 0)):                # bridge sides
        if not present[n]:
            continue
        plate = plate - _oriented(n, half - hg - slot_u, half, -sw, sw, -1, PLATE_T + 1)
        for t0, t1 in ((sw, sw + LEG_W), (-sw - LEG_W, -sw)):
            adds.append(_oriented(n, half - hg - bar_u1, half - hg - BAR_U0, t0, t1, 0, height))
        adds.append(_oriented(n, half - hg - bar_u1, half - hg - BAR_U0, -sw - LEG_W, sw + LEG_W,
                              PLATE_T + gap, height))
    for n in ((0, 1), (0, -1)):                # tab sides
        if not present[n]:
            continue
        adds.append(_oriented(n, half - hg - 0.6, half + hg + tab_u, -TAB_W / 2, TAB_W / 2, 0, PLATE_T))
        if lip_h > 0:
            adds.append(_oriented(n, half + hg + lip_u0, half + hg + tab_u, -TAB_W / 2, TAB_W / 2,
                                  PLATE_T, PLATE_T + lip_h))
    out = plate
    for a in adds:
        out = out + a
    return out


def _to_trimesh(man, rot90=False, shift=(0, 0)):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=float)[:, :3].copy()
    if rot90:
        v[:, 0], v[:, 1] = -v[:, 1].copy(), v[:, 0].copy()
    v[:, 0] += shift[0]
    v[:, 1] += shift[1]
    return trimesh.Trimesh(v, np.asarray(mesh.tri_verts), process=False)


# ---------------------------------------------------------------- outlines
class Outline:
    def __init__(self, spec):
        self.spec = spec
        kind, _, arg = spec.partition(":")
        self.mask = None
        if kind in ("rect", "rrect", "circle", "poly", "heart"):
            from shapely.geometry import Point, Polygon, box
            if kind == "rect":
                w, h = (float(x) for x in arg.split(","))
                poly = box(0, 0, w, h)
            elif kind == "rrect":                # rounded rectangle: rrect:W,H,R (R capped at half the short side)
                w, h, r = (float(x) for x in arg.split(","))
                r = min(r, w / 2, h / 2)
                poly = box(r, r, w - r, h - r).buffer(r, 64)
            elif kind == "heart":                # heart:W, the classic parametric heart scaled to W mm wide
                w = float(arg)
                pts = [(16 * math.sin(t) ** 3, 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
                       for t in (2 * math.pi * i / 200 for i in range(200))]
                k = w / 32.0                     # the curve is exactly 32 units wide
                poly = Polygon([(x * k, y * k) for x, y in pts])
            elif kind == "circle":
                d = float(arg)
                poly = Point(d / 2, d / 2).buffer(d / 2, 128)
            else:
                pts = [tuple(float(v) for v in p.split(",")) for p in arg.split()]
                poly = Polygon(pts)
                if not poly.is_valid or poly.area <= 0:
                    raise ValueError("poly outline is not a valid polygon")
            x0, y0, x1, y1 = poly.bounds
            from shapely import affinity
            self.poly = affinity.translate(poly, -x0, -y0)
            self.w, self.h = x1 - x0, y1 - y0
        elif kind == "text":
            from PIL import Image, ImageDraw, ImageFont
            self.px = 4                          # pixels per mm of mask
            font_path = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
            font = ImageFont.truetype(font_path, 400) if os.path.exists(font_path) else ImageFont.load_default(size=400)
            l, t, r, b = font.getbbox(arg)
            img = Image.new("L", (r - l, b - t), 0)
            ImageDraw.Draw(img).text((-l, -t), arg, fill=255, font=font)
            self.text_scale = None               # size set by caller via scale_to()
            self.text_img = img
            self.poly = None
            self.w = self.h = None
        else:
            raise ValueError(f"unknown outline {spec!r}; use rect:W,H | rrect:W,H,R | circle:D | heart:W | poly:\"x,y ...\" | text:ABC")

    def scale_to(self, height_mm):
        """text only: scale so the ink is height_mm tall, and build the mask."""
        img = self.text_img
        if img.height == 0 or img.width == 0:
            raise ValueError("text outline is empty")
        k = height_mm * self.px / img.height
        img = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))))
        self.mask = np.asarray(img) > 127
        self.h, self.w = img.height / self.px, img.width / self.px

    def fraction(self, x0, y0, x1, y1):
        if self.mask is None:
            from shapely.geometry import box
            b = box(x0, y0, x1, y1)
            return self.poly.intersection(b).area / b.area
        H = self.mask.shape[0]                   # image y grows downward
        cols = slice(max(0, round(x0 * self.px)), max(0, round(x1 * self.px)))
        rows = slice(max(0, H - round(y1 * self.px)), max(0, H - round(y0 * self.px)))
        cell = self.mask[rows, cols]
        return cell.sum() / ((x1 - x0) * (y1 - y0) * self.px ** 2)


def fill(outline, pitch):
    """Cells kept (>= half footprint inside), largest connected component only. Returns (cells, dropped)."""
    nx, ny = math.ceil(outline.w / pitch - 1e-9), math.ceil(outline.h / pitch - 1e-9)
    kept = {(r, c) for r in range(ny) for c in range(nx)
            if outline.fraction(c * pitch, r * pitch, (c + 1) * pitch, (r + 1) * pitch) >= 0.5}
    comps, seen = [], set()
    for s in sorted(kept):
        if s in seen:
            continue
        comp, stack = set(), [s]
        while stack:
            r, c = stack.pop()
            if (r, c) in comp:
                continue
            comp.add((r, c))
            stack += [n for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if n in kept and n not in comp]
        seen |= comp
        comps.append(comp)
    if not comps:
        return set(), 0
    comps.sort(key=len, reverse=True)
    return comps[0], len(comps) - 1


# ---------------------------------------------------------------- sheet
def check_params(pitch, height, gap):
    slot_u = BAR_U0 + BAR_W + gap + LIP_W + gap
    waist = 2 * (pitch / 2 - gap / 2 - slot_u)
    if waist < 1.2:
        raise ValueError(f"pitch {pitch} too small for gap {gap}: plate waist {waist:.1f} mm < 1.2 mm")
    if height < PLATE_T + gap + MIN_FEATURE:
        raise ValueError(f"height {height} too low: bridge needs >= {PLATE_T + gap + MIN_FEATURE:.1f} mm")
    if gap < 0.1:
        raise ValueError("gap must be >= 0.1 mm")
    if gap > 0.6:   # the lip (1.2 mm) must out-rise the gap to catch the bridge, and the bridge span (2 + 2*gap) stays <= 3.2 mm
        raise ValueError(f"gap {gap} too large: tiles would slide apart (max 0.6 mm)")


def build_sheet(spec, pitch, height, gap, origin=(0.0, 0.0), prefix="", lip_h=LIP_H):
    """Returns (tiles, info). tiles: [(name, row, col, trimesh)]."""
    check_params(pitch, height, gap)
    o = Outline(spec)
    if spec.startswith("text:"):
        o.scale_to(5 * pitch)
    cells, dropped = fill(o, pitch)
    if not cells:
        raise ValueError("outline holds no tile (nothing has half a pitch inside it)")
    rows = [r for r, _ in cells]; cols = [c for _, c in cells]
    wx, wy = (max(cols) - min(cols) + 1) * pitch, (max(rows) - min(rows) + 1) * pitch
    if wx > BED or wy > BED:
        raise ValueError(f"sheet is {wx:.0f} x {wy:.0f} mm, bigger than the {BED:.0f} x {BED:.0f} mm bed: shrink the outline")
    cache, tiles = {}, []
    for r, c in sorted(cells):
        typ = (r + c) % 2
        present = {}
        for n in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d = n if typ == 0 else (-n[1], n[0])   # local side -> world direction
            present[n] = (r + d[1], c + d[0]) in cells
        key = (typ, tuple(sorted(present.items())))
        if key not in cache:
            cache[key] = tile_manifold(pitch, height, gap, present, lip_h)
        mesh = _to_trimesh(cache[key], rot90=bool(typ),
                           shift=(origin[0] + c * pitch + pitch / 2, origin[1] + r * pitch + pitch / 2))
        tiles.append((f"{prefix}tile-r{r}-c{c}", r, c, mesh))
    allv = np.vstack([t[3].vertices for t in tiles])
    info = {"tiles": len(tiles), "pitch": pitch, "height": height, "gap": gap, "outline": spec,
            "bbox": [round(float(v), 3) for v in (*allv.min(0)[:2], *allv.max(0)[:2])],
            "dropped_islands": dropped}
    return tiles, info


def tag_tile(n_dots, origin, prefix="tag"):
    w, h, d = 18.0, 8.0, 1.6
    base = _box(0, w, 0, h, 0, PLATE_T)
    span = (n_dots - 1) * 3.2
    for i in range(n_dots):
        x = w / 2 - span / 2 + i * 3.2
        dot = m3d.Manifold.cylinder(0.6 + 0.2, d / 2, d / 2, 24).translate((x, h / 2, PLATE_T - 0.2))
        base = base + dot
    return f"{prefix}-{n_dots}", _to_trimesh(base, shift=origin)


def build_swatch(pitch, height):
    gaps, tiles, patches, tags = (0.30, 0.40, 0.50), [], [], []
    for k, g in enumerate(gaps):
        x0 = k * 50.0
        t, info = build_sheet("rect:40,40", pitch, height, g, origin=(x0, 0.0), prefix=f"g{g:.2f}-")
        tiles += t
        n = 3 + k
        patches.append({"gap": g, "dots": n, "origin": [x0, 0.0], "tiles": info["tiles"], "name": f"g{g:.2f}"})
        tags.append(tag_tile(n, (x0 + 11.0, -20.0)))
    return tiles, tags, patches


def export(tiles, extra, path):
    scene = trimesh.Scene()
    for name, _, _, m in tiles:
        scene.add_geometry(m, node_name=name, geom_name=name)
    for name, m in extra:
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(path)


def _manifold(mesh):
    return m3d.Manifold(m3d.Mesh(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces, dtype=np.uint32)))


def check_sheet(path, gap=DEFAULT_GAP):
    """Measure a fabric 3MF as printed: one watertight body per object, no pair closer than gap - 0.05, none fused."""
    res = {"ok": False, "tiles": 0, "bodies": 0, "min_gap_mm": None, "fused_pairs": 0, "detail": ""}
    try:
        scene = trimesh.load(path)
        objs = [(node, scene.geometry[scene.graph[node][1]].copy().apply_transform(scene.graph[node][0]))
                for node in scene.graph.nodes_geometry]
    except Exception as e:   # not a readable 3MF scene: say so in the JSON line, never crash (review P3)
        res["detail"] = f"not a readable fabric 3MF: {type(e).__name__}"
        return res
    res["tiles"] = len(objs)
    bad = [n for n, m in objs if not m.is_watertight]
    if bad:
        res["detail"] = f"not watertight: {', '.join(bad[:3])}"
        return res
    for _, m in objs:                       # two tiles merged into one object = one object, several bodies
        n = len(m.split(only_watertight=False))
        res["bodies"] += n
        res["fused_pairs"] += max(0, n - 1)
    mans = [_manifold(m) for _, m in objs]
    # the tile size comes from the GEOMETRY (median footprint), never from the sandbox's sidecar (review P2: a sidecar
    # pitch of -1000 switched every pair off); every object must be tile-sized: two tiles fused into one solid are
    # twice as big, and a stray shell or an ordinary part is not a tile at all
    # equal tiles have equal VOLUME (both orientations are the same shape): a fused pair has ~2x, a stray shell ~0
    vols = [abs(float(m.volume)) for _, m in objs]
    vmed = float(np.median(vols)) if vols else 0.0
    odd = [objs[i][0] for i, v in enumerate(vols) if v > 1.5 * vmed or v < 0.5 * vmed]
    if len(objs) >= 4 and odd:
        res["fused_pairs"] += sum(1 for v in vols if v > 1.5 * vmed)
        res["detail"] = f"not a sheet of equal tiles: {', '.join(odd[:3])}"
        return res
    feet = [float(np.ptp(m.bounds, axis=0)[:2].max()) for _, m in objs]
    ext = float(np.median(feet)) if feet else 1.0
    pitch = max(feet) if feet else 1.0   # neighbour pruning from the measured tiles, never the sidecar
    grid = {}
    for i, (_, m) in enumerate(objs):       # neighbour pruning: bucket by centre, look at the 3 x 3 buckets around
        cx, cy = m.bounds.mean(axis=0)[:2]
        grid.setdefault((int(cx // ext), int(cy // ext)), []).append(i)
    search = max(gap, 0.1) + 0.5
    min_gap = None
    for (gx, gy), ids in grid.items():
        for i in ids:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for j in grid.get((gx + dx, gy + dy), ()):
                        if j <= i:
                            continue
                        a, b = objs[i][1].bounds, objs[j][1].bounds
                        if (np.maximum(a[0] - b[1], b[0] - a[1])[:2] > pitch).any():
                            continue
                        d = mans[i].min_gap(mans[j], search)
                        if d < 1e-6:
                            res["fused_pairs"] += 1
                        if min_gap is None or d < min_gap:
                            min_gap = d
    res["min_gap_mm"] = None if min_gap is None else round(float(min_gap), 3)
    if len(objs) < 4:
        res["detail"] = "fewer than 4 tiles: not a fabric"
    elif res["fused_pairs"]:
        res["detail"] = "the fabric's tiles are fused together"
    elif min_gap is not None and min_gap < gap - 0.05:
        res["detail"] = f"tiles are closer than the print gap ({min_gap:.2f} mm < {gap} mm)"
    else:
        res["ok"] = True
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outline", default="rect:40,40")
    ap.add_argument("--pitch", type=float, default=10.0)
    ap.add_argument("--height", type=float, default=3.0)
    ap.add_argument("--gap", type=float, default=DEFAULT_GAP)
    ap.add_argument("--out")
    ap.add_argument("--swatch", action="store_true")
    ap.add_argument("--check", metavar="X.3mf")
    a = ap.parse_args(argv)
    if a.check:
        res = check_sheet(a.check, a.gap)
        print(json.dumps(res))
        return 0 if res["ok"] else 1
    if not a.out:
        ap.error("--out is required")
    try:
        if a.swatch:
            tiles, tags, patches = build_swatch(a.pitch, a.height)
            allv = np.vstack([m.vertices for _, _, _, m in tiles] + [m.vertices for _, m in tags])
            info = {"swatch": True, "pitch": a.pitch, "height": a.height, "tiles": len(tiles), "tags": len(tags),
                    "patches": patches, "gap": [p["gap"] for p in patches],
                    "bbox": [round(float(v), 3) for v in (*allv.min(0)[:2], *allv.max(0)[:2])],
                    "outline": "3 x rect:40,40"}
            if info["bbox"][2] - info["bbox"][0] > BED or info["bbox"][3] - info["bbox"][1] > BED:
                raise ValueError("swatch does not fit the bed")
        else:
            tiles, info = build_sheet(a.outline, a.pitch, a.height, a.gap)
            tags = []
        export(tiles, tags, a.out)
    except ValueError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    with open(a.out + ".json", "w") as f:
        json.dump(info, f, indent=1)
    if info.get("dropped_islands"):
        print(f"note: dropped {info['dropped_islands']} disconnected island(s)")
    print(f"wrote {a.out}: {info['tiles']} tiles" + (f" + {len(tags)} tags" if tags else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
