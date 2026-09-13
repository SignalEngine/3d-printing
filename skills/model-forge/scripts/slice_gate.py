#!/usr/bin/env python3
"""Slice gate: "watertight" is not the same as "slices clean". Refuses meshes
OrcaSlicer itself would silently slice anyway (it does not refuse non-manifold
input — verified in practice), then runs a real headless slice on the Bambu
Lab A1 profile and reports print time + filament use.

Usage: python3 slice_gate.py <model.stl|.3mf|.step> [--filament "Bambu PLA Basic @BBL A1"]
Exit 0 = sliced clean. Exit 1 = refused (non-manifold) or slicer failed.

Requires the OrcaSlicer AppImage extracted at ORCA_DIR (see SKILL.md Step 2).
"""
import os, sys, argparse, subprocess, shutil, tempfile, re
import trimesh

ORCA_DIR = os.environ.get("ORCA_DIR", "/root/3d-printing/orcaslicer/squashfs-root")
ORCA_BIN = os.path.join(ORCA_DIR, "bin", "orca-slicer")
PROFILES = os.path.join(ORCA_DIR, "resources", "profiles", "BBL")


def load_any(path):
    if path.lower().endswith((".step", ".stp")):
        from build123d import import_step, export_stl
        fd, tmp = tempfile.mkstemp(suffix=".stl"); os.close(fd)
        export_stl(import_step(path), tmp, tolerance=0.01, angular_tolerance=0.1)
        m = trimesh.load(tmp, force="mesh"); os.unlink(tmp)
        return m
    return trimesh.load(path, force="mesh")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--nozzle", default="0.4")
    ap.add_argument("--process", default="0.20mm Standard @BBL A1")
    ap.add_argument("--filament", default="Bambu PLA Basic @BBL A1")
    a = ap.parse_args()

    if not os.path.exists(ORCA_BIN):
        print(f"FAIL: OrcaSlicer not found at {ORCA_BIN} — see SKILL.md Step 2 for the headless install.")
        sys.exit(1)

    m = load_any(a.model)
    if not m.is_watertight:
        print("FAIL: mesh is not watertight/manifold — refusing to slice. OrcaSlicer will slice a "
              "broken mesh WITHOUT complaint, so this gate catches it upstream. Fix the geometry "
              "(see verify_model.py) before slicing.")
        sys.exit(1)

    # is_watertight passes each shell individually — it does NOT catch two
    # separate watertight bodies that self-intersect (e.g. embedded
    # multi-colour text/parts). WARN only: an embedded shell is often
    # legitimate (the slicer merges overlapping shells at slice time).
    if m.body_count > 1:
        bodies = m.split(only_watertight=False)
        sum_vol = sum(b.volume for b in bodies if b.is_watertight)
        try:
            union_vol = trimesh.boolean.union(bodies, check_volume=False).volume
        except Exception:
            union_vol = None
        if union_vol is not None and sum_vol > 0 and union_vol < 0.999 * sum_vol:
            print(f"WARN: {m.body_count} shells overlap — union volume {union_vol:.2f}mm^3 vs "
                  f"sum-of-bodies {sum_vol:.2f}mm^3. Fine for text/colour parts embedded in the "
                  "body (the slicer merges overlapping shells); check it's intended otherwise.")

    with tempfile.TemporaryDirectory() as outdir:
        machine = os.path.join(PROFILES, "machine", f"Bambu Lab A1 {a.nozzle} nozzle.json")
        process = os.path.join(PROFILES, "process", f"{a.process}.json")
        filament = os.path.join(PROFILES, "filament", f"{a.filament}.json")
        for p in (machine, process, filament):
            if not os.path.exists(p):
                print(f"FAIL: profile not found: {p}")
                sys.exit(1)

        cmd = [
            ORCA_BIN, "--datadir", os.path.join(outdir, "datadir"),
            "--load-settings", f"{machine};{process}",
            "--load-filaments", filament,
            "--slice", "0",
            "--export-3mf", "sliced.3mf",
            "--outputdir", outdir,
            os.path.abspath(a.model),
        ]
        if shutil.which("xvfb-run"):
            cmd = ["xvfb-run", "-a"] + cmd

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        gcode_path = os.path.join(outdir, "plate_1.gcode")
        if proc.returncode != 0 or not os.path.exists(gcode_path):
            print("FAIL: slice did not produce gcode.")
            print(proc.stdout[-2000:]); print(proc.stderr[-2000:])
            sys.exit(1)

        gcode = open(gcode_path, "r", errors="ignore").read()
        time_m = re.search(r"total estimated time:\s*([\dhms ]+)", gcode)
        fil_g = re.search(r"filament used \[g\]\s*=\s*([\d.]+)", gcode)
        fil_cm3 = re.search(r"filament used \[cm3\]\s*=\s*([\d.]+)", gcode)
        print(f"file: {a.model}")
        print(f"profile: A1 {a.nozzle}nozzle / {a.process} / {a.filament}")
        print(f"estimated print time: {time_m.group(1).strip() if time_m else 'unknown'}")
        fil = f"{fil_g.group(1)}g" if fil_g else (f"{fil_cm3.group(1)}cm3" if fil_cm3 else "unknown")
        print(f"filament: {fil}")
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
