#!/usr/bin/env python3
"""Hand-calc strength check for a printed rectangular-section feature (snap-fit cantilever or a loaded beam/arm).
Not FEA — a rule-of-thumb estimate. stdlib only, no CAD dependency: the caller (worker/mechanics.py) measures the
part's real geometry separately and passes the declared numbers here.

Usage: strength.py --row '{"feature": "cantilever", "length_mm": 20, "thickness_mm": 1.5, "width_mm": 10,
                            "material": "PLA", "layers": "along", "repeated": false,
                            "deflection_mm": 1.0, "force_n": null}'
Exactly one of deflection_mm / force_n must be non-null.

Prints one line starting "PASS: " or "FAIL: ", ending with "(estimated)". Exit 0 on PASS, 1 on FAIL.

No --row: runs an assert-based self-check of the maths and prints "SELF-CHECK OK".
"""
import argparse, json, sys

# Rule-of-thumb strain allowances (%), one-time bend vs a fatigue-loaded repeated snap. references/mechanisms.md.
STRAIN_LIMIT = {"PLA": {False: 2.0, True: 1.0}, "PETG": {False: 4.0, True: 2.0}}
# Tensile/bending strength (MPa) of a well-printed part; halved when the load crosses layer lines ("across").
MATERIAL_MPA = {"PLA": 50.0, "PETG": 45.0}
SAFETY_FACTOR = 2.0


def cantilever_strain_pct(deflection_mm: float, thickness_mm: float, length_mm: float) -> float:
    """ε = 1.5 * y * t / L^2 (fractional), returned as a percentage."""
    return 1.5 * deflection_mm * thickness_mm / (length_mm ** 2) * 100.0


def bending_stress_mpa(force_n: float, length_mm: float, width_mm: float, thickness_mm: float) -> float:
    """σ = 6FL / (w t^2); N/mm^2 == MPa, no unit conversion needed."""
    return 6.0 * force_n * length_mm / (width_mm * thickness_mm ** 2)


def check(row: dict) -> tuple[bool, str]:
    material, layers, repeated = row["material"], row["layers"], row["repeated"]
    length, thickness, width = row["length_mm"], row["thickness_mm"], row["width_mm"]
    deflection, force = row.get("deflection_mm"), row.get("force_n")

    if deflection is not None:
        strain = cantilever_strain_pct(deflection, thickness, length)
        # An arm printed upright bends across its layer lines: half the strain budget (mechanisms.md rule 21).
        limit = STRAIN_LIMIT[material][repeated] * (0.5 if layers == "across" else 1.0)
        ok = strain <= limit
        return ok, f"Clip bends {strain:.2f}% ({material} limit {limit:g}%) (estimated)"

    stress = bending_stress_mpa(force, length, width, thickness)
    strength = MATERIAL_MPA[material] * (0.5 if layers == "across" else 1.0)
    allowable = strength / SAFETY_FACTOR
    margin = allowable / stress if stress > 0 else float("inf")
    ok = stress <= allowable
    if ok:
        return True, f"Arm holds {force:.0f} N with {margin:.1f}× margin (estimated)"
    return False, f"Arm needs {stress:.1f} MPa under {force:.0f} N, only {allowable:.1f} MPa allowed (estimated)"


def _selftest() -> None:
    # James, 22 Sep plan: PLA, L 20, t 1.5, y 1 -> ~0.56% strain.
    strain = cantilever_strain_pct(1.0, 1.5, 20.0)
    assert abs(strain - 0.5625) < 1e-6, strain
    ok, text = check({"feature": "cantilever", "length_mm": 20, "thickness_mm": 1.5, "width_mm": 10,
                       "material": "PLA", "layers": "along", "repeated": False, "deflection_mm": 1.0, "force_n": None})
    assert ok and "0.56%" in text, text

    # A bend well past the PLA one-time limit fails.
    ok, _ = check({"feature": "cantilever", "length_mm": 10, "thickness_mm": 2, "width_mm": 10,
                    "material": "PLA", "layers": "along", "repeated": False, "deflection_mm": 5, "force_n": None})
    assert not ok

    # A force well inside a generous margin passes; the same force on "across" layers (half strength) fails.
    ok_along, _ = check({"feature": "beam", "length_mm": 30, "thickness_mm": 4, "width_mm": 15,
                          "material": "PLA", "layers": "along", "repeated": False, "deflection_mm": None, "force_n": 20})
    ok_across, _ = check({"feature": "beam", "length_mm": 30, "thickness_mm": 4, "width_mm": 15,
                           "material": "PLA", "layers": "across", "repeated": False, "deflection_mm": None, "force_n": 20})
    assert ok_along and not ok_across

    # Same bend, same clip: allowed along the layers, refused when the arm prints upright (half the budget).
    row = {"feature": "cantilever", "length_mm": 20, "thickness_mm": 1.5, "width_mm": 10,
           "material": "PLA", "layers": "along", "repeated": False, "deflection_mm": 2.5, "force_n": None}
    ok_flat, _ = check(row)
    ok_up, text_up = check({**row, "layers": "across"})
    assert ok_flat and not ok_up, (ok_flat, ok_up, text_up)
    assert "limit 1%" in text_up, text_up
    print("SELF-CHECK OK")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", help="JSON object; see module docstring")
    args = ap.parse_args()
    if not args.row:
        _selftest()
        return
    row = json.loads(args.row)
    has_defl = row.get("deflection_mm") is not None
    has_force = row.get("force_n") is not None
    if has_defl == has_force:
        print("FAIL: loads row needs exactly one of deflection_mm or force_n")
        sys.exit(1)
    ok, text = check(row)
    print(("PASS: " if ok else "FAIL: ") + text)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
