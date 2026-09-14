#!/usr/bin/env bash
# Gate runner for model-forge v2. Each sub-command builds a fixture, runs the
# script under test, and asserts pass/fail in the direction the plan requires
# (see vault/Plans/2026-09-13-model-forge-v2.md "Gates"). Exits non-zero on
# ANY wrong result. `all` runs every gate.
set -uo pipefail

PY=/root/3d-printing/.venv/bin/python
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
S="$HERE/.."
ROOT="$(cd "$HERE/../../.." && pwd)"
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

    note "render.sh: --section on a hollow cube must show the cavity (differ from a solid cube's section by >5% of pixels)"
    "$PY" -c "
from build123d import *
export_stl(Box(20,20,20), '$TMP/hsolid.stl')
with BuildPart() as bp:
    Box(20,20,20)
    Box(16,16,16, mode=Mode.SUBTRACT)
export_stl(bp.part, '$TMP/hhollow.stl')
"
    bash "$S/scripts/render.sh" "$TMP/hsolid.stl" "$TMP/hsolid" --section >"$TMP/render_hsolid.out" 2>&1
    bash "$S/scripts/render.sh" "$TMP/hhollow.stl" "$TMP/hhollow" --section >"$TMP/render_hhollow.out" 2>&1
    "$PY" -c "
import numpy as np
from PIL import Image
a = np.array(Image.open('$TMP/hsolid-section.png').convert('L')).astype(int)
b = np.array(Image.open('$TMP/hhollow-section.png').convert('L')).astype(int)
diff = (np.abs(a - b) > 10).mean() * 100
print(f'section diff: {diff:.2f}%')
import sys; sys.exit(0 if diff > 5 else 1)
" >"$TMP/render_section_diff.out" 2>&1
    sec_exit=$?
    cat "$TMP/render_section_diff.out"
    [ "$sec_exit" = 0 ] || { echo "FAIL: hollow-cube section does not differ from solid-cube section by >5%"; ok=0; FAIL=1; }

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

    note "features.py: a through-hole must classify as 'through Z' even when a boss elsewhere changes the part's overall Z bounds"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    Box(30,30,10)
    with Locations((10,0,10)):
        Box(10,10,10)
    with Locations((-8,0,0)):
        Cylinder(2,10, mode=Mode.SUBTRACT)
export_step(bp.part, '$TMP/plateboss.step')
with BuildPart() as bp2:
    Box(30,30,10)
    Cylinder(2,10, mode=Mode.SUBTRACT)
export_step(bp2.part, '$TMP/centered.step')
"
    echo '[{"diameter":4.0,"face":"through Z","tol":0.1}]' > "$TMP/expect_boss.json"
    "$PY" "$S/scripts/features.py" "$TMP/plateboss.step" --expect "$TMP/expect_boss.json" >"$TMP/feat_boss.out" 2>&1
    assert_exit "hole through Z despite boss" 0 $?
    grep -q "through Z" "$TMP/feat_boss.out" || { echo "FAIL: expected 'through Z' classification"; FAIL=1; cat "$TMP/feat_boss.out"; }

    note "features.py: hole centre must be a real 3D point on the axis, not a point on the wall"
    "$PY" "$S/scripts/features.py" "$TMP/centered.step" >"$TMP/feat_centered.out" 2>&1
    "$PY" -c "
import re, sys
out = open('$TMP/feat_centered.out').read()
m = re.search(r'center=\[([^\]]+)\]', out)
c = [float(x) for x in m.group(1).split(',')]
ok = all(abs(v) <= 0.01 for v in c)
print('centered hole center:', c, 'ok' if ok else 'BAD')
sys.exit(0 if ok else 1)
" || { echo "FAIL: centred hole centre not within 0.01mm of [0,0,0]"; FAIL=1; }
    "$PY" "$S/scripts/features.py" "$TMP/plateboss.step" >"$TMP/feat_offset.out" 2>&1
    "$PY" -c "
import re, sys
out = open('$TMP/feat_offset.out').read()
m = re.search(r'center=\[([^\]]+)\]', out)
c = [float(x) for x in m.group(1).split(',')]
ok = abs(c[0] - (-8.0)) <= 0.01 and abs(c[1]) <= 0.01
print('offset hole center:', c, 'ok' if ok else 'BAD')
sys.exit(0 if ok else 1)
" || { echo "FAIL: offset hole centre not within 0.01mm of [-8,0,z]"; FAIL=1; }

    note "features.py: blind hole with a 0.1mm floor must classify as blind (+Z), not through Z"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    Box(20,20,10)
    with BuildSketch(bp.faces().sort_by(Axis.Z)[-1]):
        Circle(2)
    extrude(amount=-9.9, mode=Mode.SUBTRACT)
export_step(bp.part, '$TMP/thinfloor.step')
"
    echo '[{"diameter":4.0,"face":"+Z","tol":0.1}]' > "$TMP/expect_thinfloor.json"
    "$PY" "$S/scripts/features.py" "$TMP/thinfloor.step" --expect "$TMP/expect_thinfloor.json" >"$TMP/feat_thinfloor.out" 2>&1
    assert_exit "0.1mm-floor blind hole classifies as +Z" 0 $?
    grep -q "face=+Z" "$TMP/feat_thinfloor.out" || { echo "FAIL: expected face=+Z (blind), see:"; cat "$TMP/feat_thinfloor.out"; FAIL=1; }

    note "features.py: --expect matching is first-fit by sorted diameter within a face, not list order"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    Box(30,30,10)
    with BuildSketch(bp.faces().sort_by(Axis.Z)[-1]):
        with Locations((-5,-5)):
            Circle(4.1/2)
        with Locations((5,5)):
            Circle(3.9/2)
    extrude(amount=-3, mode=Mode.SUBTRACT)
export_step(bp.part, '$TMP/twoholes.step')
"
    echo '[{"diameter":4.0,"face":"+Z","tol":0.15},{"diameter":4.2,"face":"+Z","tol":0.15}]' > "$TMP/expect_twoholes.json"
    "$PY" "$S/scripts/features.py" "$TMP/twoholes.step" --expect "$TMP/expect_twoholes.json" >"$TMP/feat_twoholes.out" 2>&1
    assert_exit "sorted-diameter first-fit matches 3.9->4.0 and 4.1->4.2" 0 $?

    echo '[{"diameter":4.0,"face":"+Z","tol":0.15},{"diameter":4.2,"face":"+Z","tol":0.15},{"diameter":5.0,"face":"+Z","tol":0.15}]' > "$TMP/expect_missing.json"
    "$PY" "$S/scripts/features.py" "$TMP/twoholes.step" --expect "$TMP/expect_missing.json" >"$TMP/feat_missing.out" 2>&1
    assert_exit "genuinely missing hole still FAILs" 1 $?

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

    note "fit.py: crossed touching bars must report a near-zero gap and real contact area (not a vertex-to-surface false CLEARANCE)"
    "$PY" -c "
from build123d import *
export_stl(Box(20,2,2), '$TMP/barA.stl')
export_stl(Pos(0,0,2) * Box(2,20,2), '$TMP/barB_touch.stl')
export_stl(Pos(0,0,2.5) * Box(2,20,2), '$TMP/barB_sep.stl')
"
    "$PY" "$S/scripts/fit.py" "$TMP/barA.stl" "$TMP/barB_touch.stl" >"$TMP/fit_cross.out" 2>&1
    "$PY" -c "
import re, sys
out = open('$TMP/fit_cross.out').read()
gap = float(re.search(r'minimum gap: ([\d.]+)', out).group(1))
area = float(re.search(r'contact area.*?: ([\d.]+)', out).group(1))
print('crossed bars gap', gap, 'area', area)
sys.exit(0 if (gap <= 0.05 and 3 <= area <= 5) else 1)
" || { echo "FAIL: crossed bars expected gap<=0.05 and contact 3-5mm^2"; FAIL=1; cat "$TMP/fit_cross.out"; }

    "$PY" "$S/scripts/fit.py" "$TMP/barA.stl" "$TMP/barB_sep.stl" >"$TMP/fit_sep.out" 2>&1
    grep -q "RESULT: CLEARANCE" "$TMP/fit_sep.out" || { echo "FAIL: expected CLEARANCE for separated bars"; FAIL=1; }
    "$PY" -c "
import re, sys
out = open('$TMP/fit_sep.out').read()
gap = float(re.search(r'minimum gap: ([\d.]+)', out).group(1))
area = float(re.search(r'contact area.*?: ([\d.]+)', out).group(1))
print('separated bars gap', gap, 'area', area)
sys.exit(0 if (0.45 <= gap <= 0.55 and area == 0) else 1)
" || { echo "FAIL: separated bars expected gap 0.45-0.55 and contact 0"; FAIL=1; cat "$TMP/fit_sep.out"; }

    note "fit.py: corner-touching boxes report a near-zero gap, repeatable across 3 runs"
    "$PY" -c "
from build123d import *
export_stl(Box(20,20,10), '$TMP/cornerA.stl')
export_stl(Pos(20,20,10) * Box(20,20,10), '$TMP/cornerB.stl')
"
    for i in 1 2 3; do
        "$PY" "$S/scripts/fit.py" "$TMP/cornerA.stl" "$TMP/cornerB.stl" >"$TMP/fit_corner_$i.out" 2>&1
    done
    "$PY" -c "
import re, sys
outs = [open('$TMP/fit_corner_%d.out' % i).read() for i in (1,2,3)]
gaps = [float(re.search(r'minimum gap: ([\d.]+)', o).group(1)) for o in outs]
print('corner-touch gaps over 3 runs:', gaps)
ok = all(g <= 0.01 for g in gaps) and len(set(gaps)) == 1
sys.exit(0 if ok else 1)
" || { echo "FAIL: corner-touch gap not <=0.01mm or not identical across 3 runs"; FAIL=1; cat "$TMP/fit_corner_1.out"; }

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

gate_quote() {
    note "slice_gate.py: no flags -> PASS with print hours / cost floor lines"
    "$PY" -c "from build123d import *; export_stl(Box(20,20,10), '$TMP/cube.stl')"
    "$PY" "$S/scripts/slice_gate.py" "$TMP/cube.stl" >"$TMP/quote_cube.out" 2>&1
    assert_exit "cube, no flags" 0 $?
    grep -q "^print hours:" "$TMP/quote_cube.out" || { echo "FAIL: missing 'print hours:' line"; FAIL=1; }
    grep -q "^cost floor:" "$TMP/quote_cube.out" || { echo "FAIL: missing 'cost floor:' line"; FAIL=1; }

    note "slice_gate.py: trophy over --max-hours must FAIL"
    "$PY" "$S/scripts/slice_gate.py" "$ROOT/models/rq-trophy/trophy.3mf" --max-hours 6 >"$TMP/quote_trophy_hours.out" 2>&1
    assert_exit "trophy over max-hours" 1 $?
    grep -q "QUOTE FAIL" "$TMP/quote_trophy_hours.out" || { echo "FAIL: missing QUOTE FAIL"; FAIL=1; }
    grep -q "RESULT: FAIL" "$TMP/quote_trophy_hours.out" || { echo "FAIL: missing RESULT: FAIL"; FAIL=1; }

    note "slice_gate.py: pillbox assembly under both limits must PASS"
    "$PY" "$S/scripts/slice_gate.py" "$ROOT/models/rq-pillbox/assembly.3mf" --max-hours 6 --max-grams 60 >"$TMP/quote_pillbox.out" 2>&1
    assert_exit "pillbox under limits" 0 $?

    note "slice_gate.py: knob at --price 5 must PASS (well over min £/hr)"
    "$PY" "$S/scripts/slice_gate.py" "$ROOT/models/rq-knob/knob.3mf" --price 5 >"$TMP/quote_knob.out" 2>&1
    assert_exit "knob price 5" 0 $?
    grep -q "margin per printer-hour" "$TMP/quote_knob.out" || { echo "FAIL: missing margin-per-hour line"; FAIL=1; }

    note "slice_gate.py: trophy at --price 25 must FAIL (under min £/hr)"
    "$PY" "$S/scripts/slice_gate.py" "$ROOT/models/rq-trophy/trophy.3mf" --price 25 >"$TMP/quote_trophy_price.out" 2>&1
    assert_exit "trophy price 25" 1 $?
    grep -q "QUOTE FAIL" "$TMP/quote_trophy_price.out" || { echo "FAIL: missing QUOTE FAIL for price"; FAIL=1; }

    [ "$FAIL" = 0 ] && echo QUOTE_GATE_OK
}

gate_text() {
    note "text_check.py: build123d plate with raised HELLO reads correctly"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    with BuildSketch():
        Rectangle(60, 20)
    extrude(amount=3)
    with BuildSketch(bp.faces().sort_by(Axis.Z)[-1]):
        Text('HELLO', font_size=10)
    extrude(amount=2)
export_stl(bp.part, '$TMP/hello.stl')
"
    "$PY" "$S/scripts/text_check.py" "$TMP/hello.stl" --expect HELLO --axis z --steps 6 >"$TMP/text_hello.out" 2>&1
    assert_exit "HELLO plate reads HELLO" 0 $?
    grep -q "RESULT: PASS" "$TMP/text_hello.out" || { echo "FAIL: missing RESULT: PASS"; FAIL=1; }

    note "text_check.py: same plate, --expect WORLD must FAIL"
    "$PY" "$S/scripts/text_check.py" "$TMP/hello.stl" --expect WORLD --axis z --steps 6 >"$TMP/text_world.out" 2>&1
    assert_exit "HELLO plate does not read WORLD" 1 $?

    note "text_check.py: plate reading HELLOWORLD must not pass as HELLO (extra letters)"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    with BuildSketch():
        Rectangle(110, 20)
    extrude(amount=3)
    with BuildSketch(bp.faces().sort_by(Axis.Z)[-1]):
        Text('HELLOWORLD', font_size=10)
    extrude(amount=2)
export_stl(bp.part, '$TMP/helloworld.stl')
"
    "$PY" "$S/scripts/text_check.py" "$TMP/helloworld.stl" --expect HELLO --axis z --steps 6 >"$TMP/text_extra.out" 2>&1
    assert_exit "extra letters must not pass" 1 $?
    "$PY" "$S/scripts/text_check.py" "$TMP/helloworld.stl" --expect HELLOWORLD --axis z --steps 6 >"$TMP/text_full.out" 2>&1
    assert_exit "HELLOWORLD plate reads HELLOWORLD" 0 $?

    note "text_check.py: HELLO and WORLD extruded on top of each other must not pass as HELLO"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    with BuildSketch():
        Rectangle(60, 20)
    extrude(amount=3)
    top = bp.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top):
        Text('HELLO', font_size=10)
        Text('WORLD', font_size=10)
    extrude(amount=2)
export_stl(bp.part, '$TMP/overlap.stl')
"
    "$PY" "$S/scripts/text_check.py" "$TMP/overlap.stl" --expect HELLO --axis z --steps 6 >"$TMP/text_overlap.out" 2>&1
    assert_exit "overlapping text must not pass" 1 $?

    note "text_check.py: real trophy.stl reads CONGRATULATION"
    "$PY" "$S/scripts/text_check.py" "$ROOT/models/rq-trophy/trophy.stl" --expect CONGRATULATION >"$TMP/text_trophy_ok.out" 2>&1
    assert_exit "trophy reads CONGRATULATION" 0 $?

    note "text_check.py: real trophy.stl must NOT read CONGRATULATIONS (extra S)"
    "$PY" "$S/scripts/text_check.py" "$ROOT/models/rq-trophy/trophy.stl" --expect CONGRATULATIONS >"$TMP/text_trophy_bad.out" 2>&1
    assert_exit "trophy does not read CONGRATULATIONS" 1 $?

    [ "$FAIL" = 0 ] && echo TEXT_GATE_OK
}

gate_supports() {
    note "verify_model.py: closed-top tube (46mm-scale roof) WARNs needs supports, naming the roof z"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    Cylinder(26, 60)
    with Locations((0,0,-1.5)):
        Cylinder(23, 57, mode=Mode.SUBTRACT)
export_stl(bp.part, '$TMP/tube_roof.stl')
with BuildPart() as bp2:
    Cylinder(26, 60)
    Cylinder(23, 60, mode=Mode.SUBTRACT)
export_stl(bp2.part, '$TMP/tube_open.stl')
"
    "$PY" "$S/scripts/verify_model.py" "$TMP/tube_roof.stl" >"$TMP/supports_roof.out" 2>&1
    assert_exit "closed-top tube WARN-only, still PASS" 0 $?
    grep -qi "needs supports" "$TMP/supports_roof.out" || { echo "FAIL: expected 'needs supports' WARN"; FAIL=1; cat "$TMP/supports_roof.out"; }
    "$PY" -c "
import re, sys
out = open('$TMP/supports_roof.out').read()
m = re.search(r'needs supports.*?(\d+(?:\.\d+)?)\s*mm\^?2.*?z[= ]([\d.\-]+)', out, re.I)
if not m:
    print('FAIL: could not parse area/z from WARN line'); sys.exit(1)
area, z = float(m.group(1)), float(m.group(2))
print(f'roof unsupported area={area} at z={z}')
sys.exit(0 if (area >= 1000 and 25 <= z <= 30) else 1)
" || { echo "FAIL: expected unsupported area >=1000mm^2 near z=27-30"; FAIL=1; cat "$TMP/supports_roof.out"; }

    note "verify_model.py: same tube with no roof (open both ends) must NOT warn needs supports"
    "$PY" "$S/scripts/verify_model.py" "$TMP/tube_open.stl" >"$TMP/supports_open.out" 2>&1
    assert_exit "open tube PASS" 0 $?
    grep -qi "needs supports" "$TMP/supports_open.out" && { echo "FAIL: open tube should not warn needs supports"; FAIL=1; cat "$TMP/supports_open.out"; }

    note "verify_model.py: a Ø4 through-hole wall pattern plus a roof must not bury the headline in dozens of bridge/thread false positives — at most 3 support lines"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    Cylinder(26, 60)
    with Locations((0,0,-1.5)):
        Cylinder(23, 57, mode=Mode.SUBTRACT)
    for zz in [-20, -10, 0, 10, 20]:
        with Locations(Location((26,0,zz), (0,90,0))):
            Cylinder(2, 10, mode=Mode.SUBTRACT)
export_stl(bp.part, '$TMP/tube_holes.stl')
"
    "$PY" "$S/scripts/verify_model.py" "$TMP/tube_holes.stl" >"$TMP/supports_holes.out" 2>&1
    assert_exit "hole-pattern tube PASS (WARN only)" 0 $?
    n_lines=$(grep -c "needs supports" "$TMP/supports_holes.out")
    [ "$n_lines" -le 3 ] || { echo "FAIL: expected <=3 'needs supports' lines, got $n_lines"; FAIL=1; cat "$TMP/supports_holes.out"; }
    grep -qi "needs supports" "$TMP/supports_holes.out" || { echo "FAIL: expected at least one needs-supports WARN (the roof)"; FAIL=1; }

    [ "$FAIL" = 0 ] && echo SUPPORTS_GATE_OK
}

gate_slice_supports() {
    note "slice_gate.py: --supports tree slices the closed-top tube and reports supports were on"
    "$PY" -c "
from build123d import *
with BuildPart() as bp:
    Cylinder(26, 60)
    with Locations((0,0,-1.5)):
        Cylinder(23, 57, mode=Mode.SUBTRACT)
export_stl(bp.part, '$TMP/tube_roof2.stl')
"
    "$PY" "$S/scripts/slice_gate.py" "$TMP/tube_roof2.stl" --supports tree >"$TMP/slice_supports.out" 2>&1
    assert_exit "closed-top tube slices with --supports tree" 0 $?
    grep -qi "support" "$TMP/slice_supports.out" || { echo "FAIL: expected slice_gate.py to report supports state"; FAIL=1; cat "$TMP/slice_supports.out"; }

    [ "$FAIL" = 0 ] && echo SLICE_SUPPORTS_GATE_OK
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
    quote) gate_quote ;;
    text) gate_text ;;
    supports) gate_supports ;;
    slice_supports) gate_slice_supports ;;
    docs) gate_docs ;;
    all)
        gate_checker; gate_render; gate_features; gate_fit; gate_slice; gate_quote; gate_text; gate_supports; gate_slice_supports; gate_docs
        [ "$FAIL" = 0 ] && echo ALL_GATES_OK
        ;;
    *) echo "unknown gate: $1" >&2; exit 2 ;;
esac

exit $FAIL
