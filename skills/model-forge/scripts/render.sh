#!/usr/bin/env bash
# Real depth-rendered views (f3d under Xvfb) — iso/top/front/section PNGs.
# Falls back to render_views.py's painter's-algorithm matplotlib grid if f3d
# is missing or fails (no GPU display / no f3d binary on this box).
#
# Usage: render.sh <model.stl|.3mf|.step> <out-prefix> [--section] [--section-z <mm>]
# Writes <out-prefix>-iso.png, -front.png, -top.png, and -section.png (if
# --section, cut at --section-z or mid-Z by default) else -iso-rear.png.
# Section view is exported by build123d/trimesh to a temp STL since f3d
# cannot cut a live section plane headlessly.
#
# NOTE on the top view: f3d degenerates to a BLANK frame when --up is
# parallel to --camera-direction (up=+Z looking straight down +Z gave 0%
# non-background pixels — verified in practice). Top uses --up=+Y instead;
# iso/front keep --up=+Z since their view direction isn't parallel to it.
set -euo pipefail

MODEL="${1:?usage: render.sh <model> <out-prefix> [--section] [--section-z <mm>]}"
PREFIX="${2:?usage: render.sh <model> <out-prefix> [--section] [--section-z <mm>]}"
shift 2
SECTION=0
SECTION_Z=""
while [ $# -gt 0 ]; do
    case "$1" in
        --section) SECTION=1; shift ;;
        --section-z) SECTION_Z="$2"; SECTION=1; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

PY=/root/3d-printing/.venv/bin/python
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v f3d >/dev/null 2>&1 || ! command -v xvfb-run >/dev/null 2>&1; then
    echo "f3d/xvfb-run not found — falling back to matplotlib grid" >&2
    exec "$PY" "$HERE/render_views.py" "$MODEL" "${PREFIX}-grid.png" $( [ "$SECTION" = 1 ] && echo --section )
fi

# f3d only reads mesh formats — convert STEP/3MF to a temp STL first.
# Paths go through sys.argv, never interpolated into the python -c string
# (a filename containing a quote used to crash or inject into the script).
STL="$MODEL"
TMP_STL=""
SECTION_STL=""
case "$MODEL" in
    *.step|*.stp|*.STEP|*.STP)
        TMP_STL="$(mktemp --suffix=.stl)"
        "$PY" - "$MODEL" "$TMP_STL" <<'PYEOF'
import sys
from build123d import import_step, export_stl
model, out = sys.argv[1], sys.argv[2]
export_stl(import_step(model), out, tolerance=0.01, angular_tolerance=0.1)
PYEOF
        STL="$TMP_STL"
        ;;
    *.3mf|*.3MF)
        TMP_STL="$(mktemp --suffix=.stl)"
        "$PY" - "$MODEL" "$TMP_STL" <<'PYEOF'
import sys, trimesh
model, out = sys.argv[1], sys.argv[2]
trimesh.load(model, force="mesh").export(out)
PYEOF
        STL="$TMP_STL"
        ;;
esac
cleanup() { [ -n "$TMP_STL" ] && rm -f "$TMP_STL"; [ -n "$SECTION_STL" ] && rm -f "$SECTION_STL"; true; }
trap cleanup EXIT

render_view() {
    local out="$1" dir="$2" up="${3:-+Z}"
    xvfb-run -a f3d "$STL" --output="$out" --resolution=800,600 --up="$up" --camera-direction="$dir"
}

render_view "${PREFIX}-iso.png" "-1,1,-1.2" "+Z"
render_view "${PREFIX}-front.png" "0,1,0" "+Z"
render_view "${PREFIX}-top.png" "0,0,-1" "+Y"

if [ "$SECTION" = 1 ]; then
    SECTION_STL="$(mktemp --suffix=.stl)"
    "$PY" - "$STL" "$SECTION_STL" "${SECTION_Z:-}" <<'PYEOF'
import sys, trimesh
model, out, z = sys.argv[1], sys.argv[2], sys.argv[3]
m = trimesh.load(model, force="mesh")
zc = float(z) if z else m.bounds.mean(0)[2]
cut = m.slice_plane(plane_origin=[0, 0, zc], plane_normal=[0, 0, -1], cap=True)
cut.export(out)
PYEOF
    xvfb-run -a f3d "$SECTION_STL" --output="${PREFIX}-section.png" --resolution=800,600 --up=+Z --camera-direction="1,1,1.2"
else
    render_view "${PREFIX}-iso-rear.png" "1,-1,-1.2" "+Z"
fi

echo "wrote ${PREFIX}-{iso,front,top,$( [ "$SECTION" = 1 ] && echo section || echo iso-rear )}.png"
