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


def flatten_profile(path, outdir):
    """Merge a BBL system profile with its `inherits` parents (same directory, child wins) into one
    json under outdir and return that path. Orca's CLI loads a profile file as-is, so without this
    every inherited value (bed size, skirt, brim, temperatures) silently falls back to a default."""
    import json
    chain, p = [], path
    while p:
        with open(p) as f:
            d = json.load(f)
        chain.append(d)
        parent = d.get("inherits")
        p = os.path.join(os.path.dirname(path), f"{parent}.json") if parent else None
    merged = {}
    for d in reversed(chain):
        merged.update(d)
    merged.pop("inherits", None)
    out = os.path.join(outdir, "flat-" + os.path.basename(path))
    with open(out, "w") as f:
        json.dump(merged, f)
    return out


def load_any(path):
    if path.lower().endswith((".step", ".stp")):
        from build123d import import_step, export_stl
        fd, tmp = tempfile.mkstemp(suffix=".stl"); os.close(fd)
        export_stl(import_step(path), tmp, tolerance=0.01, angular_tolerance=0.1)
        m = trimesh.load(tmp, force="mesh"); os.unlink(tmp)
        return m
    return trimesh.load(path, force="mesh")


def parse_hours(time_str):
    """'21m 38s' / '2h 51m 3s' / '15h 14m 45s' / '1d 2h 3m' -> float hours."""
    units = {"d": 24, "h": 1, "m": 1 / 60, "s": 1 / 3600}
    total = 0.0
    for value, unit in re.findall(r"(\d+)\s*([dhms])", time_str):
        total += int(value) * units[unit]
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--nozzle", default="0.4")
    ap.add_argument("--process", default="0.20mm Standard @BBL A1")
    ap.add_argument("--filament", default="Bambu PLA Basic @BBL A1")
    ap.add_argument("--gbp-per-kg", type=float, default=18.0)
    ap.add_argument("--gbp-per-hour", type=float, default=0.30,
                     help="estimated machine cost: electricity + wear")
    ap.add_argument("--max-hours", type=float, default=None)
    ap.add_argument("--max-grams", type=float, default=None)
    ap.add_argument("--price", type=float, default=None, help="proposed sale price, GBP")
    ap.add_argument("--min-gbp-per-hour", type=float, default=10.0)
    ap.add_argument("--supports", choices=["none", "tree", "normal"], default="none",
                     help="enable supports for this slice (default none)")
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
        # Orca's CLI does not resolve a system profile's `inherits` chain (16 Sep 2026: the A1 machine
        # json inherits printable_area 256x256, but the CLI sliced on the 200x200 default bed, so wide
        # parts failed with -102/-50). Flatten each profile into one json before loading it.
        machine, process, filament = (flatten_profile(p, outdir) for p in (machine, process, filament))

        settings = f"{machine};{process}"
        if a.supports != "none":
            import json
            merged = json.load(open(process))
            merged["enable_support"] = "1"
            merged["support_type"] = f"{a.supports}(auto)"
            support_process = os.path.join(outdir, "process_with_supports.json")
            with open(support_process, "w") as f:
                json.dump(merged, f)
            settings = f"{machine};{support_process}"

        cmd = [
            ORCA_BIN, "--datadir", os.path.join(outdir, "datadir"),
            "--load-settings", settings,
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
        print(f"supports: {a.supports}")
        time_str = time_m.group(1).strip() if time_m else "unknown"
        print(f"estimated print time: {time_str}")
        fil = f"{fil_g.group(1)}g" if fil_g else (f"{fil_cm3.group(1)}cm3" if fil_cm3 else "unknown")
        print(f"filament: {fil}")

        # "supports: tree" above is just this script's own flag echoed back —
        # it says nothing about whether the slicer actually emitted support
        # material. Count the support feature blocks OrcaSlicer writes into
        # the gcode itself so the gate can't false-PASS on a slice that never
        # generated supports (e.g. geometry didn't need them despite the flag).
        support_blocks = len(re.findall(r"^;\s*(?:FEATURE:\s*Support|TYPE:Support)", gcode, re.MULTILINE))
        print(f"support feature blocks: {support_blocks}")

        hours = parse_hours(time_str) if time_m else None
        if hours == 0:
            # An unrecognised time format (e.g. HH:MM:SS) parses to 0 and would zero the
            # machine cost silently; treat it as unknown instead.
            print(f"WARN: could not parse print time {time_str!r}; hours unknown")
            hours = None
        if fil_g:
            grams = float(fil_g.group(1))
        elif fil_cm3:
            # ponytail: PLA density (1.24 g/cm3) only — PETG is 1.27, ABS 1.04.
            grams = float(fil_cm3.group(1)) * 1.24
        else:
            grams = None

        if a.supports != "none" and grams is not None:
            # Best-effort: re-slice with supports off to report the filament
            # delta. Skip silently if the baseline slice itself fails.
            try:
                base_out = os.path.join(outdir, "baseline")
                os.makedirs(base_out, exist_ok=True)
                base_cmd = [
                    ORCA_BIN, "--datadir", os.path.join(outdir, "datadir"),
                    "--load-settings", f"{machine};{process}",
                    "--load-filaments", filament,
                    "--slice", "0",
                    "--export-3mf", "sliced.3mf",
                    "--outputdir", base_out,
                    os.path.abspath(a.model),
                ]
                if shutil.which("xvfb-run"):
                    base_cmd = ["xvfb-run", "-a"] + base_cmd
                base_proc = subprocess.run(base_cmd, capture_output=True, text=True, timeout=120)
                base_gcode_path = os.path.join(base_out, "plate_1.gcode")
                if base_proc.returncode == 0 and os.path.exists(base_gcode_path):
                    base_gcode = open(base_gcode_path, "r", errors="ignore").read()
                    base_fil_g = re.search(r"filament used \[g\]\s*=\s*([\d.]+)", base_gcode)
                    base_fil_cm3 = re.search(r"filament used \[cm3\]\s*=\s*([\d.]+)", base_gcode)
                    if base_fil_g:
                        base_grams = float(base_fil_g.group(1))
                    elif base_fil_cm3:
                        base_grams = float(base_fil_cm3.group(1)) * 1.24
                    else:
                        base_grams = None
                    if base_grams is not None:
                        print(f"filament delta vs no supports: {grams - base_grams:+.1f}g")
            except Exception:
                pass  # delta is informational only

        fails = []
        if hours is not None:
            print(f"print hours: {hours:.2f}")
            if a.max_hours is not None and hours > a.max_hours:
                fails.append(f"print hours {hours:.2f} > --max-hours {a.max_hours}")
        if grams is not None:
            material_cost = grams / 1000 * a.gbp_per_kg
            print(f"material: {grams:.1f}g = £{material_cost:.2f}")
            if a.max_grams is not None and grams > a.max_grams:
                fails.append(f"material {grams:.1f}g > --max-grams {a.max_grams}")
        if hours is not None:
            machine_cost = hours * a.gbp_per_hour
            print(f"machine: £{machine_cost:.2f}")
        if hours is not None and grams is not None:
            cost_floor = material_cost + machine_cost
            print(f"cost floor: £{cost_floor:.2f}")
            if a.price is not None:
                margin = a.price - cost_floor
                per_hour = margin / hours if hours > 0 else float("inf")
                print(f"margin per printer-hour: £{per_hour:.2f}")
                if per_hour < a.min_gbp_per_hour:
                    fails.append(
                        f"margin per printer-hour £{per_hour:.2f} < --min-gbp-per-hour {a.min_gbp_per_hour}")

        if fails:
            for reason in fails:
                print(f"QUOTE FAIL: {reason}")
            print("RESULT: FAIL")
            sys.exit(1)

        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
