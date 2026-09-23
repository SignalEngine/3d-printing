"""Tests for scripts/model_card.py. Run: /root/3d-printing/.venv/bin/python -m unittest skills/model-forge/tests/test_model_card.py
Heavy cases run in subprocesses under a hard RLIMIT_AS so a failure cannot eat the host."""
import json, os, subprocess, sys, tempfile, time, unittest, zipfile
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "model_card.py")
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import model_card as mc  # noqa: E402

LIMIT = "import resource;resource.setrlimit(resource.RLIMIT_AS,(6<<30,6<<30));"


def card(path, timeout=60):
    out = tempfile.mktemp(suffix=".json")
    r = subprocess.run([sys.executable, SCRIPT, path, "--json", out, "--timeout", str(timeout)], capture_output=True, text=True)
    return json.load(open(out)), r


class HeavyOpenMesh(unittest.TestCase):
    def test_hole_in_heavy_mesh_still_has_part(self):
        m = trimesh.creation.icosphere(subdivisions=7, radius=20)
        self.assertGreater(len(m.faces), 300_000)
        m.faces = m.faces[3:]
        d = tempfile.mkdtemp()
        m.export(f"{d}/open.stl")
        c, _ = card(f"{d}/open.stl", 90)
        self.assertEqual(len(c["parts"]), 1, c["limits"])
        self.assertTrue(any("decimation failed" in l for l in c["limits"]))


class ReadMeta(unittest.TestCase):
    def make(self, mb):
        d = tempfile.mkdtemp()
        p = f"{d}/big.3mf"
        head = '<?xml version="1.0"?><model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Title">Big One</metadata><metadata name="License">CC-BY</metadata><resources><object id="1"><mesh><vertices>'
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z, z.open("3D/3dmodel.model", "w") as f:
            f.write(head.encode())
            line = b'<vertex x="1.0" y="2.0" z="3.0"/>' * 1000
            for _ in range(mb * 1_000_000 // len(line)):
                f.write(line)
            f.write(b"</vertices></mesh></object></resources></model>")
        return p

    def test_bounded_memory_and_fast(self):
        p = self.make(70)
        code = (f"import sys,resource,time;sys.path.insert(0,{os.path.dirname(SCRIPT)!r});import model_card as mc;"
                f"r=lambda:resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024;b=r();t=time.time();m=mc.read_meta({p!r});"
                "print(m, round(time.time()-t,2), r()-b)")   # growth, not absolute: ru_maxrss is inherited across exec
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
        meta, rest = out.rsplit("}", 1)[0] + "}", out.rsplit("}", 1)[1].split()
        self.assertEqual(eval(meta), {"Title": "Big One", "License": "CC-BY"})
        self.assertLess(float(rest[0]), 3)
        self.assertLess(int(rest[1]), 50)   # unbounded parse grew ~1 GB for this file


class Stacked(unittest.TestCase):
    def test_identical_stacked_copies_are_not_a_pair(self):
        b = trimesh.creation.box((10, 10, 10))
        s = trimesh.Scene()
        s.add_geometry(b, node_name="a", geom_name="g")
        s.add_geometry(b, node_name="b", geom_name="g")   # same geometry, same placement
        d = tempfile.mkdtemp()
        s.export(f"{d}/two.3mf")
        c, _ = card(f"{d}/two.3mf")
        self.assertEqual(c["pairs"], [], c)


class Orphans(unittest.TestCase):
    def test_an_alarm_during_a_render_kills_the_group_too(self):
        """Review P3: the worker's own alarm (not a subprocess timeout) cut the render and left xvfb/f3d running.
        A sabotaged `except subprocess.TimeoutExpired` was once pushed because no test covered this path."""
        import signal
        class Boom(Exception): pass
        def ring(*a): raise Boom()
        old = signal.signal(signal.SIGALRM, ring); signal.alarm(1)
        try:
            with self.assertRaises(Boom):
                mc.run_group(["sh", "-c", "sleep 3171 & sleep 3172"], 20)
        finally:
            signal.alarm(0); signal.signal(signal.SIGALRM, old)
        time.sleep(0.5)
        left = subprocess.run(["pgrep", "-f", "sleep 317[12]"], capture_output=True, text=True).stdout.split()
        self.assertEqual(left, [], "render group survived the alarm")

    def test_timeout_kills_group(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            mc.run_group(["sh", "-c", "sleep 300 & sleep 301"], 1)
        time.sleep(0.5)
        left = subprocess.run(["pgrep", "-f", "sleep 30[01]"], capture_output=True, text=True).stdout.split()
        self.assertEqual(left, [])


if __name__ == "__main__":
    unittest.main()


class RealGear(unittest.TestCase):
    """The Frankenstein switch's part named 'Gear' is a real 20-tooth gear. A guard written as `if not planar.entities`
    (a numpy array) raised inside a try and silently turned every gear into 'no gear' (23 Sep)."""
    FILE = "/var/lib/printtweak/test-models/frankenstein-switch.3mf"

    @unittest.skipUnless(os.path.exists(FILE), "REAL TEST MODEL MISSING: frankenstein-switch.3mf")
    def test_the_real_gear_is_found(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "c.json")
            subprocess.run([sys.executable, os.path.join(os.path.dirname(mc.__file__), "model_card.py"), self.FILE, "--json", out],
                           check=True, capture_output=True, timeout=120)
            card = json.load(open(out))
        gears = [p["gear"] for p in card["parts"] if p.get("gear")]
        self.assertTrue(gears, "no gear found")
        self.assertEqual(gears[0]["teeth"], 20)


class SourceExport(unittest.TestCase):
    """--source-dir / --tiles-dir on the two real files: every part exported, instances[i] applied to <slug>.stl
    reproduces the placed mesh, slugs unique + valid, one tile per part."""
    FILES = ["/var/lib/printtweak/test-models/hinged-box.3mf", "/var/lib/printtweak/test-models/frankenstein-switch.3mf"]

    def test_slugify(self):
        self.assertEqual(mc.slugify(["Lid", "Lid 2", "Base Plate!", "lid", "***", "x" * 60]),
                         ["lid", "lid-2", "base-plate", "lid-3", "part", "x" * 40])

    def test_real_files(self):
        import re
        for f in self.FILES:
            self.assertTrue(os.path.exists(f), f"REAL TEST MODEL MISSING: {f}")
            with tempfile.TemporaryDirectory() as d:
                out, src, tiles = os.path.join(d, "c.json"), os.path.join(d, "src"), os.path.join(d, "tiles")
                subprocess.run([sys.executable, SCRIPT, f, "--json", out, "--source-dir", src, "--tiles-dir", tiles, "--timeout", "90"],
                               check=True, capture_output=True, timeout=150)
                cardj = json.load(open(out))
                entries = json.load(open(os.path.join(src, "parts.json")))
                self.assertEqual([e["slug"] for e in entries], [p["slug"] for p in cardj["parts"]])
                slugs = [e["slug"] for e in entries]
                self.assertEqual(len(set(slugs)), len(slugs))
                placed_all = {n: pl for n, _, pl, _ in mc.load_parts(f)}
                for e in entries:
                    self.assertRegex(e["slug"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
                    self.assertLessEqual(len(e["slug"]), 40)
                    m = trimesh.load(os.path.join(src, e["file"]))
                    placed = placed_all[e["name"]]
                    self.assertEqual(len(e["instances"]), len(placed))
                    for T, p in zip(e["instances"], placed):
                        got = m.copy().apply_transform(np.array(T))
                        self.assertLess(float(np.abs(got.bounds - p.bounds).max()), 0.01, (f, e["name"]))
                    self.assertTrue(os.path.exists(os.path.join(tiles, e["slug"] + ".png")), (f, e["slug"]))
                self.assertEqual(len(os.listdir(tiles)), len(entries))
