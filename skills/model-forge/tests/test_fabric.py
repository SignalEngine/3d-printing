"""fabric.py contract, for BOTH tiles (square = default for now, drape = the new draping tile): gap, captive, bodies, outline fill, bed,
slices with no supports, swatch, --check. Plus the drape contract (the reason for the drape tile) in class Drape.
Run: /root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests/test_fabric.py"""
import itertools, json, os, subprocess, sys, tempfile, unittest
import numpy as np
import trimesh
import manifold3d as m3d

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, SCRIPTS)
import fabric  # noqa: E402
import slice_gate  # noqa: E402

TMP = tempfile.mkdtemp()
HEART_DRAPE = 86        # heart:100 at pitch 8


TILES = {"drape": dict(pitch=8.0, height=None, n40=25, big="rect:160,160", heart=None),
         "square": dict(pitch=10.0, height=3.0, n40=16, big="rect:200,200", heart=56)}


def sheet(spec, gap, tile="drape"):
    return fabric.build_sheet(spec, TILES[tile]["pitch"], TILES[tile]["height"], gap, tile=tile)


def both(cls):
    """Run a contract class once per tile: <Name>_drape and <Name>_square, TILE set on each."""
    for tile in TILES:
        name = f"{cls.__name__}_{tile}"
        globals()[name] = type(name, (cls, unittest.TestCase), {"TILE": tile, "__module__": __name__})
    return cls


def manifold(mesh):
    return m3d.Manifold(m3d.Mesh(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces, dtype=np.uint32)))


def overlap(a, b, move=(0, 0, 0)):
    a = a.copy()
    a.apply_translation(move)
    return (manifold(a) ^ manifold(b)).volume()


def min_distance(a, b):
    pts = np.vstack([a.vertices, b.vertices, a.sample(2000), b.sample(2000)])
    pa = pts[: len(a.vertices)], a.sample(2000)
    d = trimesh.proximity.closest_point(b, np.vstack(pa))[1].min()
    pb = b.vertices, b.sample(2000)
    return min(d, trimesh.proximity.closest_point(a, np.vstack(pb))[1].min())


def neighbours(tiles):
    by = {(r, c): m for _, r, c, m in tiles}
    for (r, c), m in by.items():
        for d in ((r, c + 1), (r + 1, c)):
            if d in by:
                yield (r, c), d, m, by[d]


@both
class Gap:
    def test_gap_every_neighbour_pair(self):
        for gap in (0.3, 0.5):
            tiles, _ = sheet("rect:40,40", gap, self.TILE)
            pairs = list(itertools.combinations([(r, c, m) for _, r, c, m in tiles], 2))
            checked = 0
            for (r1, c1, a), (r2, c2, b) in pairs:
                if max(abs(r1 - r2), abs(c1 - c2)) <= 1:      # edge and diagonal neighbours
                    checked += 1
                    self.assertGreaterEqual(min_distance(a, b), gap - 0.02, f"gap {gap} r{r1}c{c1}-r{r2}c{c2}")
            self.assertGreater(checked, 40)


def bed_section(mesh, z):
    return manifold(mesh).slice(z).extrude(0.2)


@both
class FirstLayerRelief:
    """The bed level of every tile is inset (FOOT_IN below FOOT_H) so first-layer squash can't fuse neighbours, and no tile
    loses so much bed contact that it peels off (the bat and pumpkin drape tiles did not stick)."""

    def test_bed_level_gap(self):
        for gap in (0.3, 0.4):
            tiles, _ = sheet("rect:40,40", gap, self.TILE)
            n = 0
            for _, _, a, b in neighbours(tiles):
                for z in (0.1, 0.3):
                    n += 1
                    d = bed_section(a, z).min_gap(bed_section(b, z), 5.0)
                    self.assertGreaterEqual(d, gap + 2 * 0.3 - 0.05, f"gap {gap} z={z}")
            self.assertGreater(n, 40)

    def test_bed_contact_floor(self):
        tiles, info = sheet("rect:40,40", 0.4, self.TILE)
        contact = [fabric.bed_contact(m) for _, _, _, m in tiles]
        self.assertGreaterEqual(min(contact), fabric.MIN_CONTACT, f"min bed contact {min(contact):.1f} mm2")
        self.assertEqual((info["foot_in"], info["foot_h"]), (0.3, 0.4))   # the plan's defaults, pinned

    def test_each_tile_one_body(self):
        tiles, _ = sheet("rect:40,40", 0.4, self.TILE)
        for name, _, _, m in tiles:
            self.assertEqual(len(m.split(only_watertight=False)), 1, name)


@both
class Captive:
    def test_captive_every_neighbour_pair(self):
        tiles, _ = sheet("rect:40,40", 0.4, self.TILE)
        n = 0
        for _, _, a, b in neighbours(tiles):
            n += 1
            for mv in ((2, 0, 0), (-2, 0, 0), (0, 2, 0), (0, -2, 0)):
                self.assertGreater(overlap(a, b, mv), 0.01, f"move a {mv}")
                self.assertGreater(overlap(b, a, mv), 0.01, f"move b {mv}")
            # +z: square: the tab tile is caught by the bridge tile's bar (the bridge tile itself lifts free of that pair)
            self.assertGreater(max(overlap(a, b, (0, 0, 2)), overlap(b, a, (0, 0, 2))), 0.01, "no +z lock")
        k = int(round(len(tiles) ** 0.5))
        self.assertEqual(n, 2 * k * (k - 1))

    def test_every_tile_locked_in_z(self):
        tiles, _ = sheet("rect:40,40", 0.4, self.TILE)
        by = {(r, c): m for _, r, c, m in tiles}
        for (r, c), m in by.items():
            hit = any(overlap(m, by[d], (0, 0, 2)) > 0.01 for d in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if d in by)
            self.assertTrue(hit, f"tile r{r}c{c} lifts free")


def turn(mesh, pt, axis, deg):
    """The mesh rotated deg about the line through pt along axis."""
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(deg), axis, pt))
    return m


def hinges(tiles, pitch, z):
    """(a, b, point, axis, toward-b unit move) for every edge-neighbour pair; the hinge axis is the shared edge line at height z."""
    by = {(r, c): m for _, r, c, m in tiles}
    for (r, c), a in by.items():
        if (r, c + 1) in by:
            yield a, by[(r, c + 1)], ((c + 1) * pitch, r * pitch + pitch / 2, z), (0, 1, 0), (1, 0, 0)
        if (r + 1, c) in by:
            yield a, by[(r + 1, c)], (c * pitch + pitch / 2, (r + 1) * pitch, z), (1, 0, 0), (0, 1, 0)


class Drape(unittest.TestCase):
    """The drape contract: a linked pair folds +-30 degrees about its shared edge without the tiles touching."""

    def test_every_pair_folds_30_degrees_both_ways(self):
        for gap in (0.3, 0.4, 0.5):
            tiles, _ = sheet("rect:40,40", gap, "drape")
            zc = fabric.drape_dims(gap)["zc"]        # the hinge axis: the bar's centreline, where the ring turns
            n = 0
            for a, b, pt, ax, _ in hinges(tiles, 8.0, zc):
                n += 1
                for deg in (30, -30):
                    self.assertLess(overlap(turn(a, pt, ax, deg), b), 1e-6, f"gap {gap}: a by {deg}")
                    self.assertLess(overlap(a, turn(b, pt, ax, deg)), 1e-6, f"gap {gap}: b by {deg}")
            self.assertEqual(n, 40)

    def test_every_pair_slides_toward_the_neighbour_0_3_mm(self):
        tiles, _ = sheet("rect:40,40", 0.4, "drape")
        for a, b, _, _, toward in hinges(tiles, 8.0, 0):
            mv = tuple(0.3 * v for v in toward)
            back = tuple(-v for v in mv)
            self.assertLess(overlap(a, b, mv), 1e-6)
            self.assertLess(overlap(b, a, back), 1e-6)

    def test_the_square_tile_cannot_fold_that_way(self):
        # positive control: the same fold test must FAIL on the old tile (about the axis at plate mid-height), or it proves nothing
        tiles, _ = sheet("rect:40,40", 0.4, "square")
        hit = total = 0
        for a, b, pt, ax, _ in hinges(tiles, 10.0, fabric.PLATE_T / 2):
            total += 1
            hit += any(overlap(turn(a, pt, ax, d), b) > 0.01 for d in (30, -30))
        self.assertEqual(total, 24)
        self.assertEqual(hit, total, "the square tile folded 30 degrees on some pair: the drape test does not discriminate")

    def test_prints_flat_no_supports_geometry(self):
        # every downward face is <= 45 degrees off vertical, or a flat bridge <= 6 mm; nothing hangs below z=0
        tiles, _ = sheet("rect:40,40", 0.4, "drape")
        m = {(r, c): mm for _, r, c, mm in tiles}[(2, 2)]           # a tile with all four links
        self.assertAlmostEqual(m.bounds[0][2], 0.0, 5)
        nz = m.face_normals[:, 2]
        low = m.triangles[:, :, 2].min(axis=1) > 0.01                # faces above the bed
        steep = low & (nz < -1e-6) & (nz > -0.999)
        self.assertLessEqual((-nz[steep]).max(initial=0), np.sin(np.radians(45)) + 1e-3)
        bridges = 0
        for f, n0, o0 in zip(m.facets, m.facets_normal, m.facets_origin):
            if n0[2] < -0.999 and o0[2] > 0.01:
                bridges += 1
                self.assertLessEqual(np.ptp(m.vertices[m.faces[f]].reshape(-1, 3), axis=0)[:2].max(), 6.0)
        self.assertGreater(bridges, 0)                               # the bar and the ring roof really are bridges


@both
class Bodies:
    def test_3mf_objects_match_json_and_are_watertight(self):
        out = os.path.join(TMP, f"b-{self.TILE}.3mf")
        self.assertEqual(fabric.main(["--outline", "rect:40,40", "--tile", self.TILE, "--out", out]), 0)
        info = json.load(open(out + ".json"))
        scene = trimesh.load(out)
        self.assertEqual(len(scene.geometry), info["tiles"])
        self.assertEqual(info["tiles"], TILES[self.TILE]["n40"])
        self.assertEqual(info["tile"], self.TILE)
        for name, g in scene.geometry.items():
            self.assertTrue(g.is_watertight, name)
            self.assertEqual(g.body_count, 1, name)
            self.assertTrue(name.startswith("tile-r"), name)
            self.assertAlmostEqual(g.bounds[0][2], 0.0, 5)


@both
class Outline:
    def test_rect_n(self):
        self.assertEqual(sheet("rect:40,40", 0.4, self.TILE)[1]["tiles"], TILES[self.TILE]["n40"])

    def test_circle_single_sheet_inside(self):
        p = TILES[self.TILE]["pitch"]
        tiles, info = sheet("circle:60", 0.4, self.TILE)
        cells = {(r, c) for _, r, c, _ in tiles}
        self.assertEqual(len(fabric.fill(fabric.Outline("circle:60"), p)[0]), len(cells))
        seen, stack = set(), [next(iter(cells))]
        while stack:
            r, c = stack.pop()
            if (r, c) in seen:
                continue
            seen.add((r, c))
            stack += [n for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if n in cells]
        self.assertEqual(seen, cells)
        for _, r, c, _ in tiles:
            centre = np.array([c * p + p / 2, r * p + p / 2])
            self.assertLessEqual(np.linalg.norm(centre - 30), 30 + p / 2)

    def test_trimmed_edges_have_no_dangling_feature(self):
        p = TILES[self.TILE]["pitch"]
        tiles, _ = sheet("circle:60", 0.4, self.TILE)
        by = {(r, c): m for _, r, c, m in tiles}
        for (r, c), m in by.items():                       # no vertex of a tile may lie in a cell that holds no tile
            for x, y in m.vertices[:, :2]:
                if x % p == 0 or y % p == 0:
                    continue
                cell = (int(y // p), int(x // p))
                self.assertIn(cell, by, f"tile r{r}c{c} pokes into empty cell {cell}")

    def test_heart_100_tile_count(self):
        n = sheet("heart:100", 0.4, self.TILE)[1]["tiles"]
        self.assertEqual(n, TILES[self.TILE]["heart"] or HEART_DRAPE)

    def test_rrect_drops_the_corners_of_the_same_rect(self):
        p = TILES[self.TILE]["pitch"]
        side, r = 10 * p, 0.8 * p
        self.assertEqual(sheet(f"rect:{side},{side}", 0.4, self.TILE)[1]["tiles"], 100)
        self.assertEqual(sheet(f"rrect:{side},{side},{r}", 0.4, self.TILE)[1]["tiles"], 100)   # corners keep >= half of each corner cell
        self.assertLess(sheet(f"rrect:{side},{side},{side / 2}", 0.4, self.TILE)[1]["tiles"], 100)   # R capped at half the side = a circle

    def test_text_outline_builds(self):
        p = TILES[self.TILE]["pitch"]
        tiles, info = fabric.build_sheet("text:HI", p, TILES[self.TILE]["height"], 0.4, tile=self.TILE)
        self.assertGreater(info["tiles"], 3)


@both
class Bed:
    def test_too_big_refused(self):
        out = os.path.join(TMP, "big.3mf")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fabric.py"), "--outline", "rect:300,100", "--tile", self.TILE, "--out", out],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("bed", r.stderr)
        self.assertFalse(os.path.exists(out))


@unittest.skipUnless(os.path.exists(slice_gate.ORCA_BIN), "OrcaSlicer not installed")
@both
class Prints:
    def test_slices_with_no_supports_and_verifies(self):
        out = os.path.join(TMP, f"p-{self.TILE}.3mf")
        fabric.main(["--outline", "rect:40,40", "--tile", self.TILE, "--out", out])
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "slice_gate.py"), out, "--supports", "none"],
                           capture_output=True, text=True, timeout=900)
        self.assertIn("RESULT: PASS", r.stdout, r.stdout[-800:])
        self.assertNotIn("needs supports", r.stdout)
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "verify_model.py"), out, "--bodies", str(TILES[self.TILE]["n40"])],
                           capture_output=True, text=True, timeout=900)
        self.assertIn("RESULT: PASS", r.stdout, r.stdout)
        self.assertNotIn("thinner", r.stdout)
        if self.TILE == "square":
            self.assertNotIn("needs supports", r.stdout)
        else:
            # the drape tile's bars are 2.4 mm bridges between two posts: verify_model's per-layer heuristic reports those as
            # "unsupported area" (it cannot see the anchors). A real mid-air island would be a different line, and must not appear.
            self.assertNotIn("mid-air island", r.stdout)


@both
class Swatch:
    def test_swatch(self):
        out = os.path.join(TMP, f"s-{self.TILE}.3mf")
        self.assertEqual(fabric.main(["--swatch", "--tile", self.TILE, "--out", out]), 0)
        info = json.load(open(out + ".json"))
        n = 3 * TILES[self.TILE]["n40"]
        self.assertEqual(info["tiles"], n)
        self.assertEqual(info["tile"], self.TILE)
        self.assertEqual(info["tags"], 3)
        self.assertEqual([(p["gap"], p["dots"]) for p in info["patches"]], [(0.3, 3), (0.4, 4), (0.5, 5)])
        scene = trimesh.load(out)
        self.assertEqual(len(scene.geometry), n + 3)
        for g in scene.geometry.values():
            self.assertTrue(g.is_watertight)
        x0, y0, x1, y1 = info["bbox"]
        self.assertLessEqual(x1 - x0, 256)
        self.assertLessEqual(y1 - y0, 256)
        self.assertGreaterEqual(y0, -25)
        self.assertEqual(scene.bounds[0][2], 0)




@both
class Check:
    def _sheet(self, name, mutate=None, spec="circle:60"):
        tiles, info = sheet(spec, 0.4, self.TILE)
        if mutate:
            tiles = mutate(tiles)
        out = os.path.join(TMP, f"{self.TILE}-{name}")
        fabric.export(tiles, [], out)
        return out

    def _run(self, path):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fabric.py"), "--check", path, "--gap", "0.4"],
                           capture_output=True, text=True, timeout=300)
        return r.returncode, json.loads(r.stdout)

    def test_generated_circle_passes(self):
        rc, res = self._run(self._sheet("ck-ok.3mf"))
        self.assertTrue(res["ok"], res)
        self.assertEqual(rc, 0)
        self.assertEqual(res["bodies"], res["tiles"])
        self.assertEqual(res["fused_pairs"], 0)
        self.assertGreaterEqual(res["min_gap_mm"], 0.35)

    def test_two_tiles_merged_into_one_object_fails(self):
        def fuse(tiles):
            (n0, r0, c0, m0), (_, _, _, m1) = tiles[0], tiles[1]
            return [(n0, r0, c0, trimesh.util.concatenate([m0, m1]))] + tiles[2:]
        rc, res = self._run(self._sheet("ck-fused.3mf", fuse))
        self.assertFalse(res["ok"], res)
        self.assertGreaterEqual(res["fused_pairs"], 1)
        self.assertEqual(rc, 1)

    def test_two_tiles_joined_into_one_solid_fails(self):
        # review P2 repro: a 1 x 1 mm bridge makes tile r0c0 + r0c1 ONE solid (split() sees one piece)
        p = TILES[self.TILE]["pitch"]

        def join(tiles):
            (n0, r0, c0, m0), (_, _, _, m1) = tiles[0], tiles[1]
            solid = trimesh.boolean.union([m0, m1, fabric._to_trimesh(fabric._box(p - 1.5, p + 1.5, 1, 2, 0, 1.2))], engine="manifold")
            return [(n0, r0, c0, solid)] + tiles[2:]
        _, res = self._run(self._sheet("ck-joined.3mf", join, spec="rect:40,40"))
        self.assertFalse(res["ok"], res)

    def test_a_forged_sidecar_pitch_cannot_switch_the_check_off(self):
        # review P2: {"pitch": -1000} used to skip every pair; the tile size now comes from the geometry
        def overlap(tiles):
            (n, r, c, m) = tiles[1]; m = m.copy(); m.apply_translation((-1.0, 0, 0))
            return [tiles[0], (n, r, c, m)] + tiles[2:]
        path = self._sheet("ck-forged.3mf", overlap, spec="rect:40,40")
        with open(path + ".json", "w") as f:
            json.dump({"tiles": 16, "gap": 0.4, "pitch": -1000}, f)
        _, res = self._run(path)
        self.assertFalse(res["ok"], res)

    def test_a_non_3mf_prints_a_json_refusal(self):
        bad = os.path.join(TMP, "not-a.3mf"); open(bad, "w").write("hello")
        rc, res = self._run(bad)
        self.assertFalse(res["ok"]) ; self.assertNotEqual(rc, 0)

    def test_an_ordinary_two_body_part_is_not_fabric(self):
        # review P3: a part with a stray shell + a sidecar claiming 2 tiles must not pass as "2 linked tiles"
        body = trimesh.creation.box((40, 20, 10)); shell = trimesh.creation.box((2, 2, 2)); shell.apply_translation((25, 0, 0))
        sc = trimesh.Scene(); sc.add_geometry(body, geom_name="a"); sc.add_geometry(shell, geom_name="b")
        path = os.path.join(TMP, "ck-part.3mf"); sc.export(path)
        _, res = self._run(path)
        self.assertFalse(res["ok"], res)

    def test_tiles_moved_closer_fails(self):
        def squeeze(tiles):
            out = []
            for n, r, c, m in tiles:
                m = m.copy()
                m.apply_translation(((c - 3) * -0.2, 0, 0))     # each column 0.2 mm nearer the centre one
                out.append((n, r, c, m))
            return out
        _, res = self._run(self._sheet("ck-close.3mf", squeeze))
        self.assertFalse(res["ok"], res)
        self.assertLess(res["min_gap_mm"], 0.35)

    def test_200_sheet_under_a_minute(self):
        import time
        path = self._sheet("ck-big.3mf", spec=TILES[self.TILE]["big"])
        t0 = time.time()
        rc, res = self._run(path)
        self.assertLess(time.time() - t0, 60)
        self.assertTrue(res["ok"], res)


class Limits(unittest.TestCase):
    def test_a_gap_the_lip_cannot_catch_is_refused(self):
        # review P3: at gap >= the lip height the tiles slide apart; above 0.6 the bridge span passes 3.2 mm
        with self.assertRaises(ValueError):
            fabric.check_params(20.0, 4.0, 0.7, "square")
        fabric.check_params(10.0, 3.0, 0.6, "square")   # the largest allowed gap still passes

    def test_drape_limits(self):
        with self.assertRaises(ValueError):
            fabric.check_params(8.0, None, 0.7, "drape")       # the rings would slide off the bars
        with self.assertRaises(ValueError):
            fabric.check_params(5.0, None, 0.4, "drape")       # no room for a plate between the links
        # measured minimum buildable pitch: 6.5 @0.3, 7.5 @0.4, 8.0 @0.5, 8.5 @0.6 (check_params builds one tile to know)
        fabric.check_params(8.5, None, 0.6, "drape")
        fabric.check_params(7.5, None, 0.4, "drape")
        with self.assertRaises(ValueError):
            fabric.check_params(6.0, None, 0.4, "drape")

    def test_a_drape_pitch_gap_the_geometry_cannot_build_is_refused_not_a_crash(self):
        # review P2: 8 mm at 0.6 mm passed the arithmetic checks and crashed in drape_manifold
        with self.assertRaises(ValueError):
            fabric.check_params(8.0, None, 0.6, "drape")

    def test_square_stays_the_default_until_tweakmypart_moves_and_drape_is_one_flag_away(self):
        # the TweakMyPart host calls fabric.py WITHOUT --tile, and its preview/price assume square 10 mm tiles
        out = os.path.join(TMP, "default.3mf")
        self.assertEqual(fabric.main(["--outline", "rect:40,40", "--out", out]), 0)
        info = json.load(open(out + ".json"))
        self.assertEqual((info["tile"], info["pitch"], info["tiles"]), ("square", 10.0, 16))
        out2 = os.path.join(TMP, "drape.3mf")
        self.assertEqual(fabric.main(["--outline", "rect:40,40", "--tile", "drape", "--out", out2]), 0)
        info = json.load(open(out2 + ".json"))
        self.assertEqual((info["tile"], info["pitch"], info["tiles"]), ("drape", 8.0, 25))

    def test_empty_text_is_refused_not_a_crash(self):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fabric.py"), "--outline", "text:", "--out",
                            tempfile.mktemp(suffix=".3mf")], capture_output=True, text=True, timeout=120)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("ZeroDivisionError", r.stderr)


if __name__ == "__main__":
    unittest.main()
