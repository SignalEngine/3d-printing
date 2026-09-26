"""fabric.py contract: gap, captive, bodies, outline fill, bed, slices with no supports, swatch.
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


def sheet(spec, gap, pitch=10.0):
    return fabric.build_sheet(spec, pitch, 3.0, gap)


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


class Gap(unittest.TestCase):
    def test_gap_every_neighbour_pair(self):
        for gap in (0.3, 0.5):
            tiles, _ = sheet("rect:40,40", gap)
            pairs = list(itertools.combinations([(r, c, m) for _, r, c, m in tiles], 2))
            checked = 0
            for (r1, c1, a), (r2, c2, b) in pairs:
                if max(abs(r1 - r2), abs(c1 - c2)) <= 1:      # edge and diagonal neighbours
                    checked += 1
                    self.assertGreaterEqual(min_distance(a, b), gap - 0.02, f"gap {gap} r{r1}c{c1}-r{r2}c{c2}")
            self.assertGreater(checked, 40)


class Captive(unittest.TestCase):
    def test_captive_every_neighbour_pair(self):
        tiles, _ = sheet("rect:40,40", 0.4)
        n = 0
        for _, _, a, b in neighbours(tiles):
            n += 1
            for mv in ((2, 0, 0), (-2, 0, 0), (0, 2, 0), (0, -2, 0)):
                self.assertGreater(overlap(a, b, mv), 0.01, f"move a {mv}")
                self.assertGreater(overlap(b, a, mv), 0.01, f"move b {mv}")
            # +z: the tab tile is caught by the bridge tile's bar (the bridge tile itself lifts free of that pair)
            self.assertGreater(max(overlap(a, b, (0, 0, 2)), overlap(b, a, (0, 0, 2))), 0.01, "no +z lock")
        self.assertEqual(n, 24)

    def test_every_tile_locked_in_z(self):
        tiles, _ = sheet("rect:40,40", 0.4)
        by = {(r, c): m for _, r, c, m in tiles}
        for (r, c), m in by.items():
            hit = any(overlap(m, by[d], (0, 0, 2)) > 0.01 for d in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if d in by)
            self.assertTrue(hit, f"tile r{r}c{c} lifts free")


class Bodies(unittest.TestCase):
    def test_3mf_objects_match_json_and_are_watertight(self):
        out = os.path.join(TMP, "b.3mf")
        self.assertEqual(fabric.main(["--outline", "rect:40,40", "--out", out]), 0)
        info = json.load(open(out + ".json"))
        scene = trimesh.load(out)
        self.assertEqual(len(scene.geometry), info["tiles"])
        self.assertEqual(info["tiles"], 16)
        for name, g in scene.geometry.items():
            self.assertTrue(g.is_watertight, name)
            self.assertEqual(g.body_count, 1, name)
            self.assertTrue(name.startswith("tile-r"), name)
            self.assertAlmostEqual(g.bounds[0][2], 0.0, 5)


class Outline(unittest.TestCase):
    def test_rect_16(self):
        self.assertEqual(sheet("rect:40,40", 0.4)[1]["tiles"], 16)

    def test_circle_single_sheet_inside(self):
        tiles, info = sheet("circle:60", 0.4)
        cells = {(r, c) for _, r, c, _ in tiles}
        self.assertEqual(len(fabric.fill(fabric.Outline("circle:60"), 10)[0]), len(cells))
        seen, stack = set(), [next(iter(cells))]
        while stack:
            r, c = stack.pop()
            if (r, c) in seen:
                continue
            seen.add((r, c))
            stack += [n for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if n in cells]
        self.assertEqual(seen, cells)
        for _, r, c, _ in tiles:
            centre = np.array([c * 10 + 5, r * 10 + 5])
            self.assertLessEqual(np.linalg.norm(centre - 30), 30 + 5)

    def test_trimmed_edges_have_no_dangling_feature(self):
        tiles, _ = sheet("circle:60", 0.4)
        by = {(r, c): m for _, r, c, m in tiles}
        for (r, c), m in by.items():                       # tile bbox must stay within own cell + nothing outside kept cells
            lo, hi = m.bounds
            for x, y in ((lo[0], lo[1]), (hi[0], hi[1])):
                cell = (int(y // 10), int(x // 10))
                if x % 10 == 0 or y % 10 == 0:
                    continue
                self.assertIn(cell, by, f"tile r{r}c{c} pokes into empty cell {cell}")

    def test_text_outline_builds(self):
        tiles, info = fabric.build_sheet("text:HI", 10.0, 3.0, 0.4)
        self.assertGreater(info["tiles"], 3)


class Bed(unittest.TestCase):
    def test_too_big_refused(self):
        out = os.path.join(TMP, "big.3mf")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fabric.py"), "--outline", "rect:300,100", "--out", out],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("bed", r.stderr)
        self.assertFalse(os.path.exists(out))


@unittest.skipUnless(os.path.exists(slice_gate.ORCA_BIN), "OrcaSlicer not installed")
class Prints(unittest.TestCase):
    def test_slices_with_no_supports_and_verifies(self):
        out = os.path.join(TMP, "p.3mf")
        fabric.main(["--outline", "rect:40,40", "--out", out])
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "slice_gate.py"), out, "--supports", "none"],
                           capture_output=True, text=True, timeout=900)
        self.assertIn("RESULT: PASS", r.stdout, r.stdout[-800:])
        self.assertNotIn("needs supports", r.stdout)
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "verify_model.py"), out, "--bodies", "16"],
                           capture_output=True, text=True, timeout=900)
        self.assertIn("RESULT: PASS", r.stdout, r.stdout)
        self.assertNotIn("needs supports", r.stdout)
        self.assertNotIn("thinner", r.stdout)


class Swatch(unittest.TestCase):
    def test_swatch(self):
        out = os.path.join(TMP, "s.3mf")
        self.assertEqual(fabric.main(["--swatch", "--out", out]), 0)
        info = json.load(open(out + ".json"))
        self.assertEqual(info["tiles"], 48)
        self.assertEqual(info["tags"], 3)
        self.assertEqual([(p["gap"], p["dots"]) for p in info["patches"]], [(0.3, 3), (0.4, 4), (0.5, 5)])
        scene = trimesh.load(out)
        self.assertEqual(len(scene.geometry), 51)
        for g in scene.geometry.values():
            self.assertTrue(g.is_watertight)
        x0, y0, x1, y1 = info["bbox"]
        self.assertLessEqual(x1 - x0, 256)
        self.assertLessEqual(y1 - y0, 256)
        self.assertGreaterEqual(y0, -25)
        self.assertEqual(scene.bounds[0][2], 0)


if __name__ == "__main__":
    unittest.main()
