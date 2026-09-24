"""slice_gate --allow-open: a customer's own non-watertight kept part is sliced as-is with a WARN; without it, refused.
Run: /root/3d-printing/.venv/bin/python -m unittest skills/model-forge/tests/test_slice_gate.py"""
import os, subprocess, sys, tempfile, unittest
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "slice_gate.py")
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import slice_gate  # noqa: E402


@unittest.skipUnless(os.path.exists(slice_gate.ORCA_BIN), "OrcaSlicer not installed")
class AllowOpen(unittest.TestCase):
    def test_open_mesh_refused_by_default_and_sliced_as_is_with_allow_open(self):
        box = trimesh.creation.box((20, 20, 10))
        box.faces = box.faces[:-1]   # drop one triangle: not watertight
        path = tempfile.mktemp(suffix=".stl")
        box.export(path)
        r = subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True, timeout=600)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not watertight", r.stdout)
        r = subprocess.run([sys.executable, SCRIPT, path, "--allow-open"], capture_output=True, text=True, timeout=600)
        self.assertEqual(r.returncode, 0, r.stdout[-500:])
        self.assertIn("WARN: mesh is not watertight", r.stdout)
        self.assertIn("print hours:", r.stdout)


if __name__ == "__main__":
    unittest.main()
