#!/usr/bin/env bash
# Real depth-rendered views (f3d under Xvfb) — iso/top/front/section PNGs.
# Falls back to render_views.py's painter's-algorithm matplotlib grid if f3d
# is missing or fails (no GPU display / no f3d binary on this box).
#
# Usage: render.sh <model.stl|.3mf|.step> <out-prefix> [--section]
# Writes <out-prefix>-iso.png, -front.png, -top.png, and -section.png (if
# --section) else -iso-rear.png. Section view is exported by build123d/trimesh
# to a temp STL since f3d cannot cut a live section plane headlessly.
set -euo pipefail

MODEL="${1:?usage: render.sh <model> <out-prefix> [--section]}"
PREFIX="${2:?usage: render.sh <model> <out-prefix> [--section]}"
SECTION=0
[ "${3:-}" = "--section" ] && SECTION=1

PY=/root/3d-printing/.venv/bin/python
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v f3d >/dev/null 2>&1 || ! command -v xvfb-run >/dev/null 2>&1; then
    echo "f3d/xvfb-run not found — falling back to matplotlib grid" >&2
    exec "$PY" "$HERE/render_views.py" "$MODEL" "${PREFIX}-grid.png" $( [ "$SECTION" = 1 ] && echo --section )
fi

# f3d only reads mesh formats — convert STEP/3MF to a temp STL first.
STL="$MODEL"
TMP_STL=""
case "$MODEL" in
    *.step|*.stp|*.STEP|*.STP)
        TMP_STL="$(mktemp --suffix=.stl)"
        "$PY" -c "from build123d import import_step, export_stl; export_stl(import_step('$MODEL'), '$TMP_STL', tolerance=0.01, angular_tolerance=0.1)"
        STL="$TMP_STL"
        ;;
    *.3mf|*.3MF)
        TMP_STL="$(mktemp --suffix=.stl)"
        "$PY" -c "import trimesh; trimesh.load('$MODEL', force='mesh').export('$TMP_STL')"
        STL="$TMP_STL"
        ;;
esac
cleanup() { [ -n "$TMP_STL" ] && rm -f "$TMP_STL"; }
trap cleanup EXIT

render_view() {
    local out="$1" dir="$2"
    xvfb-run -a f3d "$STL" --output="$out" --resolution=800,600 --up=+Z --camera-direction="$dir"
}

render_view "${PREFIX}-iso.png" "-1,1,-1.2"
render_view "${PREFIX}-front.png" "0,1,0"
render_view "${PREFIX}-top.png" "0,0,-1"

if [ "$SECTION" = 1 ]; then
    SECTION_STL="$(mktemp --suffix=.stl)"
    "$PY" -c "
import trimesh
m = trimesh.load('$STL', force='mesh')
zc = m.bounds.mean(0)[2]
cut = m.slice_plane(plane_origin=[0, 0, zc], plane_normal=[0, 0, -1], cap=True)
cut.export('$SECTION_STL')
"
    xvfb-run -a f3d "$SECTION_STL" --output="${PREFIX}-section.png" --resolution=800,600 --up=+Z --camera-direction="1,1,1.2"
    rm -f "$SECTION_STL"
else
    render_view "${PREFIX}-iso-rear.png" "1,-1,-1.2"
fi

echo "wrote ${PREFIX}-{iso,front,top,$( [ "$SECTION" = 1 ] && echo section || echo iso-rear )}.png"
