"""Tests for scripts/thread.py. Run: /root/3d-printing/.venv/bin/python -m unittest skills/model-forge/tests/test_thread.py
(unittest, not pytest: the model-forge venv has no pytest). SKIP_SLOW=1 skips the full three-thread demo (~30 s)."""
import math, os, subprocess, sys, tempfile, unittest
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, SCRIPTS)
import thread as T  # noqa: E402
from build123d import Pos  # noqa: E402


def fit(a, b):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fit.py"), a, b], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    gap = None
    for line in r.stdout.splitlines():
        if line.startswith("minimum gap:"):
            gap = float(line.split()[2])
    return ("INTERFERE" if "RESULT: INTERFERE" in r.stdout else "CLEARANCE" if gap is not None else "UNKNOWN"), gap


def mesh(part):
    d = tempfile.mkdtemp()
    T.export_3mf(part, f"{d}/p.3mf")
    m = trimesh.load(f"{d}/p.3mf", force="mesh")
    m.merge_vertices()
    return m


def crest_lock(m, R, lead, pitch, hand, zlo, zhi):
    """How tightly the crest vertices fit a helix of this lead/pitch/hand: 1.0 = every one on it, ~0 = none.
    Along a right-hand crest z - lead*theta/2pi is constant (mod pitch); a left-hand one uses +."""
    v = m.vertices
    p = v[(np.hypot(v[:, 0], v[:, 1]) > R - 0.02) & (v[:, 2] > zlo) & (v[:, 2] < zhi)]
    theta = np.arctan2(p[:, 1], p[:, 0])
    phase = (p[:, 2] - (1 if hand == "right" else -1) * lead * theta / (2 * math.pi)) / pitch * 2 * math.pi
    return float(abs(np.exp(1j * phase).mean()))


class Refusals(unittest.TestCase):
    def test_refuse_fine_pitch(self):
        with self.assertRaisesRegex(ValueError, "heat-set"):
            T.external_thread(10, 1.5, 20)

    def test_refuse_small_major(self):
        with self.assertRaisesRegex(ValueError, "heat-set"):
            T.internal_thread(6, 2.5, 10)

    def test_refuse_pitch_too_coarse_for_diameter(self):
        with self.assertRaisesRegex(ValueError, "too coarse"):
            T.external_thread(8, 6, 20)

    def test_refuse_bad_hand_and_starts(self):
        with self.assertRaises(ValueError):
            T.external_thread(10, 3, 20, hand="up")
        with self.assertRaises(ValueError):
            T.external_thread(10, 3, 20, starts=9)


class Geometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.right = mesh(T.external_thread(10, 3, 20))
        cls.left = mesh(T.external_thread(10, 3, 20, hand="left"))
        cls.two = mesh(T.external_thread(12, 3, 24, starts=2))

    def test_watertight(self):
        for m in (self.right, self.left, self.two):
            self.assertTrue(m.is_watertight and m.is_winding_consistent and m.volume > 0)

    def test_hands_are_mirror_images_with_a_core(self):
        """A misfired OCC fuse once dropped the core of every left-hand 1-start thread (volume 433 vs 1726)."""
        r, l = T.external_thread(10, 3, 30), T.external_thread(10, 3, 30, hand="left")
        self.assertAlmostEqual(r.volume / l.volume, 1.0, delta=0.01)
        self.assertGreater(r.volume, math.pi * 3.8 ** 2 * 30)                       # more than the bare core
        self.assertAlmostEqual(self.left.volume / self.right.volume, 1.0, delta=0.01)

    def test_pitch_starts_and_hand(self):
        self.assertGreater(crest_lock(self.right, 5.0, 3, 3, "right", 4, 16), 0.8)
        self.assertLess(crest_lock(self.right, 5.0, 3, 3, "left", 4, 16), 0.5)       # wrong hand does not fit
        self.assertLess(crest_lock(self.right, 5.0, 3, 2.5, "right", 4, 16), 0.5)    # wrong pitch does not fit
        self.assertGreater(crest_lock(self.left, 5.0, 3, 3, "left", 4, 16), 0.8)
        self.assertLess(crest_lock(self.left, 5.0, 3, 3, "right", 4, 16), 0.5)
        self.assertGreater(crest_lock(self.two, 6.0, 6, 3, "right", 5, 19), 0.8)     # 2 starts: lead 6, a crest every 3
        self.assertLess(crest_lock(self.two, 6.0, 3, 3, "right", 5, 19), 0.5)        # read as 1 start: does not fit


class Fit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.bolt_path = f"{cls.d}/bolt.3mf"
        T.export_3mf(T.bolt(10, 3, 16), cls.bolt_path)

    def nut(self, name, part):
        p = f"{self.d}/{name}.3mf"
        T.export_3mf(part, p)
        return p

    def test_seated_nut_clears_by_the_declared_clearance(self):
        n = self.nut("ok", Pos(0, 0, T.seat_z(4, 3)) * T.nut(10, 3, 6))
        kind, gap = fit(self.bolt_path, n)
        self.assertEqual(kind, "CLEARANCE")
        self.assertGreaterEqual(gap, 0.4 - 1e-3)

    def test_sabotage_out_of_phase_nut_is_caught(self):
        n = self.nut("phase", Pos(0, 0, T.seat_z(4, 3) + 1.5) * T.nut(10, 3, 6))     # half a lead off
        kind, gap = fit(self.bolt_path, n)
        self.assertTrue(kind == "INTERFERE" or gap < 0.3, f"a half-lead phase error slipped through: {kind} {gap}")

    def test_sabotage_zero_clearance_nut_is_caught(self):
        n = self.nut("tight", Pos(0, 0, T.seat_z(4, 3)) * T.nut(10, 3, 6, clearance_mm=-0.02))   # cutter shrinks to +0
        kind, gap = fit(self.bolt_path, n)
        self.assertTrue(kind == "INTERFERE" or gap < 0.1, f"a no-clearance nut slipped through: {kind} {gap}")


@unittest.skipIf(os.environ.get("SKIP_SLOW"), "slow")
class Demo(unittest.TestCase):
    def test_demo_all_three_threads(self):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "thread.py"), "demo", "--all", "--out",
                            tempfile.mkdtemp()], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("DEMO PASS: 3 of 3", r.stdout)


if __name__ == "__main__":
    unittest.main()
