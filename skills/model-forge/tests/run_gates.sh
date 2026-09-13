#!/usr/bin/env bash
# Gate runner for model-forge v2. Each sub-command builds a fixture, runs the
# script under test, and asserts pass/fail in the direction the plan requires
# (see vault/Plans/2026-09-13-model-forge-v2.md "Gates"). Exits non-zero on
# ANY wrong result. `all` runs every gate.
set -uo pipefail

PY=/root/3d-printing/.venv/bin/python
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
S="$HERE/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAIL=0

note() { echo "== $* =="; }
assert_exit() {
    local desc="$1" want="$2" got="$3"
    if [ "$got" != "$want" ]; then
        echo "FAIL: $desc — expected exit $want, got $got"
        FAIL=1
    else
        echo "ok: $desc (exit $got)"
    fi
}

gate_checker() {
    note "checker: sabotaged mesh must FAIL"
    "$PY" -c "
import trimesh, numpy as np
m = trimesh.creation.box((20,20,10))
m.update_faces(np.delete(np.arange(len(m.faces)), 0))
m.export('$TMP/broken.stl')
"
    "$PY" "$S/scripts/verify_model.py" "$TMP/broken.stl" >"$TMP/broken.out" 2>&1
    assert_exit "sabotaged mesh" 1 $?
    grep -q "NOT watertight" "$TMP/broken.out" || { echo "FAIL: missing NOT watertight message"; FAIL=1; }

    note "checker: good plate with a thin (0.4mm) wall must PASS with a WARN, not FAIL"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    with BuildSketch():
        Rectangle(30, 30)
    extrude(amount=0.4)
export_stl(bp.part, '$TMP/thin.stl')
"
    "$PY" "$S/scripts/verify_model.py" "$TMP/thin.stl" >"$TMP/thin.out" 2>&1
    assert_exit "thin plate" 0 $?
    grep -q "thinner than" "$TMP/thin.out" || { echo "FAIL: expected thin-wall WARN"; FAIL=1; }

    [ "$FAIL" = 0 ] && echo CHECKER_GATE_OK
}

gate_render() {
    note "render.sh: real f3d PNGs (iso/front/top/section), each >5% non-background pixels"
    "$PY" -c "from build123d import *; export_stl(Box(20,20,10), '$TMP/cube.stl')"
    bash "$S/scripts/render.sh" "$TMP/cube.stl" "$TMP/r" --section >"$TMP/render.out" 2>&1
    ok=1
    for v in iso front top section; do
        f="$TMP/r-$v.png"
        if [ ! -s "$f" ]; then echo "FAIL: missing/empty $f"; ok=0; fi
    done
    if [ "$ok" = 1 ]; then
        "$PY" -c "
import sys, numpy as np
from PIL import Image
names = sys.argv[1:]
bad = []
for n in names:
    im = np.array(Image.open(n).convert('L'))
    bg = im[0, 0]
    nonbg = (np.abs(im.astype(int) - int(bg)) > 10).mean() * 100
    print(f'{n}: {nonbg:.1f}% non-background')
    if nonbg <= 5:
        bad.append(n)
sys.exit(1 if bad else 0)
" "$TMP/r-iso.png" "$TMP/r-front.png" "$TMP/r-top.png" "$TMP/r-section.png" >"$TMP/render_px.out" 2>&1
        px_exit=$?
        cat "$TMP/render_px.out"
        if [ "$px_exit" != 0 ]; then echo "FAIL: a render came back blank (<=5% non-background)"; ok=0; fi
    fi

    note "render.sh: filename containing a single quote must not crash or inject (plain STL path)"
    mkdir -p "$TMP/quote'dir"
    cp "$TMP/cube.stl" "$TMP/quote'dir/it's a cube.stl"
    bash "$S/scripts/render.sh" "$TMP/quote'dir/it's a cube.stl" "$TMP/q" >"$TMP/render_quote.out" 2>&1
    assert_exit "quoted filename render (stl)" 0 $?
    [ -s "$TMP/q-iso.png" ] || { echo "FAIL: quoted-filename render produced no output"; ok=0; FAIL=1; }

    note "render.sh: quoted STEP filename exercises the vulnerable conversion path (python -c interpolation)"
    "$PY" -c "from build123d import *; export_step(Box(20,20,10), \"$TMP/quote'dir/it's a cube.step\")"
    bash "$S/scripts/render.sh" "$TMP/quote'dir/it's a cube.step" "$TMP/qstep" --section >"$TMP/render_quote_step.out" 2>&1
    assert_exit "quoted filename render (step, --section)" 0 $?
    [ -s "$TMP/qstep-iso.png" ] && [ -s "$TMP/qstep-section.png" ] || { echo "FAIL: quoted STEP render produced no output"; ok=0; FAIL=1; cat "$TMP/render_quote_step.out"; }

    if [ "$ok" = 1 ] && [ "$FAIL" = 0 ]; then echo RENDER_GATE_OK; else FAIL=1; cat "$TMP/render.out"; fi
}

gate_features() {
    note "features.py: hole on the wrong face must fail the --expect check"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    Box(30,30,10)
    with BuildSketch(bp.faces().sort_by(Axis.Z)[-1]):
        with Locations((5,5)):
            Circle(2)
    extrude(amount=-10, mode=Mode.SUBTRACT)
export_step(bp.part, '$TMP/hole.step')
"
    echo '[{"diameter":4.0,"face":"through Z","tol":0.1}]' > "$TMP/expect_ok.json"
    echo '[{"diameter":4.0,"face":"through X","tol":0.1}]' > "$TMP/expect_wrong.json"

    "$PY" "$S/scripts/features.py" "$TMP/hole.step" --expect "$TMP/expect_ok.json" >"$TMP/feat_ok.out" 2>&1
    assert_exit "hole on correct face" 0 $?
    "$PY" "$S/scripts/features.py" "$TMP/hole.step" --expect "$TMP/expect_wrong.json" >"$TMP/feat_wrong.out" 2>&1
    assert_exit "hole on wrong face" 1 $?

    [ "$FAIL" = 0 ] && echo FEATURES_GATE_OK
}

gate_fit() {
    note "fit.py: oversized lid -> INTERFERE with volume>0; cleared lid -> CLEARANCE"
    "$PY" -c "
from build123d import *
export_stl(Box(20,20,10), '$TMP/fitA.stl')
export_stl(Pos(19.9,0,0) * Box(20,20,10), '$TMP/fitB_over.stl')
export_stl(Pos(20.2,0,0) * Box(20,20,10), '$TMP/fitB_clear.stl')
"
    "$PY" "$S/scripts/fit.py" "$TMP/fitA.stl" "$TMP/fitB_over.stl" >"$TMP/fit_over.out" 2>&1
    grep -q "RESULT: INTERFERE" "$TMP/fit_over.out" || { echo "FAIL: expected INTERFERE"; FAIL=1; cat "$TMP/fit_over.out"; }
    grep -qE "interference volume: [1-9]" "$TMP/fit_over.out" || { echo "FAIL: expected interference volume > 0"; FAIL=1; }

    "$PY" "$S/scripts/fit.py" "$TMP/fitA.stl" "$TMP/fitB_clear.stl" >"$TMP/fit_clear.out" 2>&1
    grep -q "RESULT: CLEARANCE" "$TMP/fit_clear.out" || { echo "FAIL: expected CLEARANCE"; FAIL=1; cat "$TMP/fit_clear.out"; }

    note "fit.py: a failed interference boolean must report UNKNOWN (exit 2), never a false CLEARANCE"
    "$PY" "$S/scripts/fit.py" "$TMP/fitA.stl" "$TMP/fitB_over.stl" --engine bogus_engine_xyz >"$TMP/fit_unknown.out" 2>&1
    assert_exit "forced boolean failure" 2 $?
    grep -q "RESULT: UNKNOWN" "$TMP/fit_unknown.out" || { echo "FAIL: expected RESULT: UNKNOWN"; FAIL=1; cat "$TMP/fit_unknown.out"; }
    grep -q "RESULT: CLEARANCE" "$TMP/fit_unknown.out" && { echo "FAIL: forced failure fell through to CLEARANCE"; FAIL=1; }

    [ "$FAIL" = 0 ] && echo FIT_GATE_OK
}

gate_slice() {
    note "slice_gate.py: smoke plate slices; non-manifold mesh is refused"
    "$PY" -c "from build123d import *; export_stl(Box(20,20,10), '$TMP/cube.stl')"
    "$PY" -c "
import trimesh, numpy as np
m = trimesh.creation.box((20,20,10))
m.update_faces(np.delete(np.arange(len(m.faces)), 0))
m.export('$TMP/broken.stl')
"
    "$PY" "$S/scripts/slice_gate.py" "$TMP/cube.stl" >"$TMP/slice_ok.out" 2>&1
    assert_exit "good plate slices" 0 $?
    grep -q "RESULT: PASS" "$TMP/slice_ok.out" || { echo "FAIL: missing RESULT: PASS"; FAIL=1; }

    "$PY" "$S/scripts/slice_gate.py" "$TMP/broken.stl" >"$TMP/slice_bad.out" 2>&1
    assert_exit "broken mesh refused" 1 $?
    grep -q "refusing to slice" "$TMP/slice_bad.out" || { echo "FAIL: missing refusal message"; FAIL=1; }

    note "slice_gate.py: overlapping-but-individually-watertight shells WARN, still slice (not FAIL)"
    "$PY" -c "
import trimesh
A = trimesh.creation.box((20,20,10))
B = trimesh.creation.box((5,5,5))
B.apply_translation([0,0,2.5])
trimesh.util.concatenate([A, B]).export('$TMP/overlap.stl')
"
    "$PY" "$S/scripts/slice_gate.py" "$TMP/overlap.stl" >"$TMP/slice_overlap.out" 2>&1
    assert_exit "overlapping shells still slice" 0 $?
    grep -q "WARN:.*shells overlap" "$TMP/slice_overlap.out" || { echo "FAIL: missing overlapping-shells WARN"; FAIL=1; cat "$TMP/slice_overlap.out"; }
    grep -q "RESULT: PASS" "$TMP/slice_overlap.out" || { echo "FAIL: expected RESULT: PASS despite WARN"; FAIL=1; }

    [ "$FAIL" = 0 ] && echo SLICE_GATE_OK
}

gate_docs() {
    note "docs: bd_warehouse patterns documented and importable"
    grep -q "bd_warehouse.thread import IsoThread" "$S/references/build123d-patterns.md" || { echo "FAIL: threads not documented"; FAIL=1; }
    grep -q "bd_warehouse.fastener import" "$S/references/build123d-patterns.md" || { echo "FAIL: fasteners not documented"; FAIL=1; }
    grep -q "bd_warehouse.gear import" "$S/references/build123d-patterns.md" || { echo "FAIL: gears not documented"; FAIL=1; }
    "$PY" -c "
from bd_warehouse.thread import IsoThread
from bd_warehouse.fastener import SocketHeadCapScrew, HexNut
from bd_warehouse.gear import SpurGear
IsoThread(major_diameter=8, pitch=1.25, length=10, external=True)
SocketHeadCapScrew(size='M4-0.7', length=10, fastener_type='iso4762')
SpurGear(module=1, tooth_count=20, thickness=5, pressure_angle=20)
" >"$TMP/docs.out" 2>&1
    assert_exit "bd_warehouse imports + instantiates" 0 $?
    [ "$FAIL" = 0 ] && echo DOCS_GATE_OK
}

case "${1:-all}" in
    checker) gate_checker ;;
    render) gate_render ;;
    features) gate_features ;;
    fit) gate_fit ;;
    slice) gate_slice ;;
    docs) gate_docs ;;
    all)
        gate_checker; gate_render; gate_features; gate_fit; gate_slice; gate_docs
        [ "$FAIL" = 0 ] && echo ALL_GATES_OK
        ;;
    *) echo "unknown gate: $1" >&2; exit 2 ;;
esac

exit $FAIL
