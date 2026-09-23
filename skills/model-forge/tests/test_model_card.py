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
    def test_timeout_kills_group(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            mc.run_group(["sh", "-c", "sleep 300 & sleep 301"], 1)
        time.sleep(0.5)
        left = subprocess.run(["pgrep", "-f", "sleep 30[01]"], capture_output=True, text=True).stdout.split()
        self.assertEqual(left, [])


if __name__ == "__main__":
    unittest.main()
