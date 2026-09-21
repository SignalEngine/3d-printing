#!/usr/bin/env python3
"""Printed threads that tessellate watertight — the replacement for bd_warehouse IsoThread.

A coarse trapezoidal profile (30 deg flanks, flat crest, flat root) swept along a helix, fused
with a core and trimmed by a chamfered envelope, so there are no zero-thickness edges for the
mesher to choke on. Coarse ON PURPOSE: FDM rounds off anything finer than pitch 2 mm / M8.

    from thread import external_thread, internal_thread, bolt, nut, seat_z, export_3mf
    b = bolt(10, 3, 40)                          # M10x3 bolt, hex head below z=0, thread z 0..40
    n = Pos(0, 0, seat_z(12, 3)) * nut(10, 3, 8) # nut clearance 0.4 mm, seated on the thread
    export_3mf(b, "bolt.3mf"); export_3mf(n, "nut.3mf")

Conventions (the host gate re-checks all of them):
  * Solids are coaxial with Z; the thread starts at z=0 with the helix at angle 0.
  * pitch_mm = distance between neighbouring threads (crest to crest, any start);
    lead = pitch * starts = axial advance per turn.
  * A thread is a helix, so shifting a part along Z is the same as turning it. Keep a nut on
    its bolt's thread by seating it at z = k * lead (seat_z() rounds for you), otherwise the
    two threads are out of phase and fit.py reports INTERFERE.
  * internal_thread() returns the CUTTER — the void the male occupies plus `clearance_mm`.
    Subtract it from your own body; nut() does that for a hex nut.
  * Clearance 0.4 mm suits PLA on a 0.4 mm nozzle; declare the same number in checks.json.

Self-check:  python3 thread.py demo [--all | --major 10 --pitch 3 --starts 1] --out DIR
  writes bolt.3mf + nut.3mf, runs verify_model.py on both and fit.py on the seated pair.
"""
import argparse, math, os, re, subprocess, sys
from build123d import Align, Axis, Cylinder, Helix, Mesher, Part, Plane, Polyline, Pos, \
    BuildLine, BuildSketch, RegularPolygon, chamfer, extrude, make_face, sweep

MIN_PITCH_MM = 2.0
MIN_MAJOR_MM = 8.0
MESH_MARGIN_MM = 0.02        # tessellation shaves ~0.01 mm off a measured gap; the cutter carries it so a 0.4 clearance MEASURES >= 0.4
MIN_ROOT_R_MM = 2.0          # radius left under the root — below this the core is a toothpick
HERE = os.path.dirname(os.path.abspath(__file__))
_TOO_FINE = "use a heat-set insert (or a pin / ratchet strip) instead of a printed thread"


def _check(major_mm, pitch_mm, length_mm, starts, hand, flank_deg):
    if pitch_mm < MIN_PITCH_MM or major_mm < MIN_MAJOR_MM:
        raise ValueError(f"printed thread M{major_mm:g}x{pitch_mm:g} is too fine for FDM (need pitch >= "
                         f"{MIN_PITCH_MM:g} mm and major >= {MIN_MAJOR_MM:g} mm): {_TOO_FINE}")
    if starts not in (1, 2, 3, 4):
        raise ValueError("starts must be 1-4")
    if hand not in ("right", "left"):
        raise ValueError("hand must be 'right' or 'left'")
    if not 15 <= flank_deg <= 40:
        raise ValueError("flank_deg must be 15-40 (30 = ISO-like)")
    if length_mm < pitch_mm:
        raise ValueError(f"length {length_mm:g} mm is shorter than one pitch ({pitch_mm:g} mm)")


def _root(major_mm, pitch_mm, flank_deg):
    """Root radius: tooth base 0.6 pitch, crest flat 0.15 pitch, flanks at flank_deg."""
    return major_mm / 2 - (0.6 - 0.15) * pitch_mm / 2 / math.tan(math.radians(flank_deg))


def _threaded(major_mm, pitch_mm, length_mm, starts, hand, flank_deg, grow, trim, hollow=False):
    """Thread solid over z 0..length. grow > 0 offsets every surface outward (female cutter), grow < 0 inward
    (male clearance). trim=True chamfers both ends 45 deg down to the root; False leaves flat ends."""
    tan, cos = math.tan(math.radians(flank_deg)), math.cos(math.radians(flank_deg))
    crest = 0.15 * pitch_mm                                       # male tooth width at the crest
    R, root = major_mm / 2, _root(major_mm, pitch_mm, flank_deg)
    if root < MIN_ROOT_R_MM:
        raise ValueError(f"pitch {pitch_mm:g} mm is too coarse for M{major_mm:g}: {_TOO_FINE}, or a larger diameter")
    half = lambda r: crest / 2 + (R - r) * tan + grow / cos      # half tooth width at radius r, flank moved by grow
    r_in, r_out = root + grow - 0.2, R + grow                     # r_in sits inside the core so the fuse overlaps
    if half(r_out) < 0.12 or 2 * half(r_in) > pitch_mm - 0.1 or (grow > 0 and pitch_mm - 2 * half(root + grow) < 0.4):
        raise ValueError(f"clearance {abs(grow):g} mm leaves the nut a ridge thinner than one nozzle at pitch {pitch_mm:g} mm — "
                         f"use pitch >= 2.5 mm, or a smaller clearance_mm (not below 0.3 for PLA)")
    lead = pitch_mm * starts
    lead_turns = math.ceil(2 * pitch_mm / lead)                   # overshoot in whole leads keeps the phase at z=0
    over = lead * lead_turns
    pts = [(r_in, -half(r_in)), (r_out, -half(r_out)), (r_out, half(r_out)), (r_in, half(r_in))]
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    path = Helix(pitch=lead, height=length_mm + 2 * over, radius=r_in, lefthand=hand == "left")
    tooth = sweep(sk.sketch, path=path, is_frenet=True)
    span = length_mm + 2 * over
    teeth = [tooth.rotate(Axis.Z, 360 / starts * k) for k in range(starts)]
    # OCC's cylinder-vs-helical-sweep fuse silently misfires for some seam angles (two loose solids, or the core
    # dropped), so turn the core's seam until the fuse is ONE solid holding core + most of the teeth. Checked, never assumed.
    for seam in (0, 37, 90, 270, 150, 180, 210, 120, 240):
        core = Cylinder(root + grow, span, align=(Align.CENTER, Align.CENTER, Align.MIN))
        if hollow:
            core = core - Cylinder(root + grow - 1.2, span, align=(Align.CENTER, Align.CENTER, Align.MIN))
        body = core.rotate(Axis.Z, seam)
        want = core.volume + 0.6 * sum(t.volume for t in teeth)
        for t in teeth:
            body = body + t
        if len(body.solids()) == 1 and body.is_valid and body.volume > want:
            break
    else:
        raise RuntimeError(f"thread fuse failed for M{major_mm:g}x{pitch_mm:g} — try a different length or pitch")
    env_r = r_out + 0.5
    env = Cylinder(env_r, length_mm, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if trim:
        env = chamfer(env.edges(), min(env_r - root - grow, length_mm / 2 - 0.01))
    out = _one(Pos(0, 0, -over) * body & env, "trim")
    low = 0.95 * math.pi * (root + grow) ** 2 * length_mm * (0.4 if hollow else 1.0)   # the core alone, less chamfer and bore
    if not low < out.volume < math.pi * r_out ** 2 * length_mm:
        raise RuntimeError(f"thread trim gave a wrong volume for M{major_mm:g}x{pitch_mm:g} — try a different length")
    return out


def _one(shape, what):
    """A boolean result must be ONE valid solid — OCC reports some failed booleans as success."""
    if len(shape.solids()) != 1 or not shape.is_valid:
        raise RuntimeError(f"thread boolean '{what}' did not give one valid solid — change length or pitch a little")
    return shape


def external_thread(major_mm, pitch_mm, length_mm, starts=1, hand="right", clearance_mm=0.0, flank_deg=30, core=True):
    """Male thread, z 0..length, ends chamfered. clearance_mm shrinks it (leave 0; put the clearance on the
    female side). core=False gives a hollow crown (wall >= 1.2 mm) to cut your own bore through."""
    _check(major_mm, pitch_mm, length_mm, starts, hand, flank_deg)
    return _threaded(major_mm, pitch_mm, length_mm, starts, hand, flank_deg, -abs(clearance_mm), True, not core)


def internal_thread(major_mm, pitch_mm, length_mm, starts=1, hand="right", clearance_mm=0.4, flank_deg=30):
    """Female thread CUTTER, z 0..length, flat ends: subtract it from your body. Extend it past the faces you
    cut through in whole leads (shift by -k*lead) so the thread phase still matches the bolt."""
    _check(major_mm, pitch_mm, length_mm, starts, hand, flank_deg)
    return _threaded(major_mm, pitch_mm, length_mm, starts, hand, flank_deg, abs(clearance_mm) + MESH_MARGIN_MM, False)


def _hex(af_mm, height_mm):
    return extrude(RegularPolygon(radius=af_mm / math.sqrt(3), side_count=6), amount=height_mm)


def bolt(major_mm, pitch_mm, length_mm, starts=1, hand="right", head=None, flank_deg=30):
    """Bolt: thread z 0..length, hex head z -h..0 (head=("hex", across_flats_mm, height_mm), default 1.5 x / 0.7 x major)."""
    kind, af, h = head or ("hex", round(1.5 * major_mm, 1), round(0.7 * major_mm, 1))
    if kind != "hex":
        raise ValueError("only a hex head is built in — make other heads yourself and fuse them at z=0")
    shank = external_thread(major_mm, pitch_mm, length_mm, starts, hand, 0.0, flank_deg)
    return _one(Pos(0, 0, -h) * _hex(af, h) + shank, "bolt head fuse")


def nut(major_mm, pitch_mm, height_mm, starts=1, hand="right", clearance_mm=0.4, af_mm=None, flank_deg=30):
    """Hex nut z 0..height, threaded through. Seat it on a bolt at z = k*lead (seat_z)."""
    lead = pitch_mm * starts
    over = lead * math.ceil(1.0 / lead)
    cutter = Pos(0, 0, -over) * internal_thread(major_mm, pitch_mm, height_mm + 2 * over, starts, hand,
                                                clearance_mm, flank_deg)
    blank = _hex(af_mm or round(1.6 * major_mm, 1), height_mm)
    out = _one(blank - cutter, "nut cut")
    bore = math.pi * (_root(major_mm, pitch_mm, flank_deg) + clearance_mm + MESH_MARGIN_MM) ** 2 * height_mm
    if out.volume > blank.volume - 0.9 * bore:                          # a silently skipped cut leaves the blank whole
        raise RuntimeError("nut thread cut did not remove the bore — change height or pitch a little")
    return out


def seat_z(z_mm, pitch_mm, starts=1):
    """z nearest to z_mm where a part with this thread sits in phase with the bolt (a whole number of leads)."""
    lead = pitch_mm * starts
    return round(z_mm / lead) * lead


def export_3mf(part, path):
    """3MF with a deflection fine enough that a thread's gap measures true (the Mesher default is coarser)."""
    m = Mesher()
    m.add_shape(part, linear_deflection=0.01, angular_deflection=0.1)
    m.write(path)


def _run(script, *args):
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def _demo_one(name, major, pitch, starts, out):
    os.makedirs(out, exist_ok=True)
    lead, length, height, clearance = pitch * starts, 30.0, 8.0, 0.4
    z = seat_z((length - height) / 2, pitch, starts) or lead
    export_3mf(bolt(major, pitch, length, starts), f"{out}/bolt.3mf")
    export_3mf(Pos(0, 0, z) * nut(major, pitch, height, starts, clearance_mm=clearance), f"{out}/nut.3mf")
    fails = []
    for part in ("bolt", "nut"):
        code, text = _run("verify_model.py", f"{out}/{part}.3mf")
        if code != 0:
            fails.append(f"verify_model {part} exit {code}: {text.strip().splitlines()[-1] if text.strip() else ''}")
    code, text = _run("fit.py", f"{out}/bolt.3mf", f"{out}/nut.3mf")
    gap = re.search(r"minimum gap: ([\d.]+)", text)
    if "RESULT: CLEARANCE" not in text or not gap:
        fails.append(f"fit.py: {'INTERFERE' if 'INTERFERE' in text else 'no clearance'}")
    elif float(gap.group(1)) < clearance - 1e-3:                # the host gate's own bar (mechanics.py)
        fails.append(f"fit.py gap {gap.group(1)} < {clearance:g}")
    print(f"{'FAIL' if fails else 'ok'}: {name} nut at z={z:g}, gap {gap.group(1) if gap else '?'} mm"
          + "".join(f"\n  {f}" for f in fails))
    return not fails


def demo(args):
    cfgs = [("M8x2.5", 8, 2.5, 1), ("M10x3", 10, 3, 1), ("M12x3-2start", 12, 3, 2)] if args.all else \
           [(f"M{args.major:g}x{args.pitch:g}" + (f"-{args.starts}start" if args.starts > 1 else ""),
             args.major, args.pitch, args.starts)]
    passed = sum(_demo_one(n, ma, p, s, os.path.join(args.out, n) if args.all else args.out) for n, ma, p, s in cfgs)
    print(f"DEMO {'PASS' if passed == len(cfgs) else 'FAIL'}: {passed} of {len(cfgs)}")
    return 0 if passed == len(cfgs) else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="build bolt + nut, verify_model.py both, fit.py the seated pair")
    d.add_argument("--out", required=True)
    d.add_argument("--all", action="store_true", help="M8x2.5, M10x3 and M12x3 2-start")
    d.add_argument("--major", type=float, default=10)
    d.add_argument("--pitch", type=float, default=3)
    d.add_argument("--starts", type=int, default=1)
    sys.exit(demo(ap.parse_args()))
