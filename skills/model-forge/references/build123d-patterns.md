# build123d Patterns & Pitfalls (verified in this environment, v0.11.x)

Primary stack: **build123d** (BREP kernel = OpenCASCADE). CadQuery 2.8 also installed-tested and fine as fallback, but build123d is the actively-developed successor — default to it.

Install (already proven working):
```bash
pip install build123d trimesh manifold3d matplotlib --break-system-packages -q
```

## Golden rules (learned from real failures in this environment)
1. **Prefer a single extruded/revolved profile over unioning boxes.** A CadQuery union of two boxes produced 4 broken faces / non-manifold STL that repair could not fix; rebuilding as one closed 2D profile → extrude was instantly watertight. Booleans on coincident faces are the #1 manifold-error source. If you must union, overlap bodies by 0.01–0.1 mm rather than sharing an exact face.
2. **Geometric validity ≠ correctness.** A model passed every mesh check with its screw holes drilled into the wrong face. Rendering + looking caught it. Never skip the render step.
3. Export **3MF + STEP always**, STL only if asked. 3MF is Bambu Studio's native format (units, no STL ambiguity); STEP is the editable master for the next iteration.
4. Tessellate fine: `export_stl(part, f, tolerance=0.005, angular_tolerance=0.05)` — coarse default tessellation shows as faceting on curved surfaces at A1 quality.
5. Parametrize everything at the top of the script. The user WILL ask for “same but 5 mm wider”. Keep the .py so regeneration is one edit.

## Core patterns

### Skeleton (builder mode)
```python
from build123d import *

# --- parameters (mm) ---
L, W, T = 60, 40, 4

with BuildPart() as part:
    with BuildSketch(Plane.XY):
        RectangleRounded(L, W, radius=3)
    extrude(amount=T)
    # top-face features
    with Locations(part.faces().sort_by(Axis.Z)[-1]):
        with GridLocations(40, 20, 2, 2):
            CounterBoreHole(radius=1.7, counter_bore_radius=3.25, counter_bore_depth=2)  # M3 cap
    fillet(part.edges().filter_by(Axis.Z), 2)          # vertical edges
    chamfer(part.faces().sort_by(Axis.Z)[0].edges(), 0.4)  # bottom anti-elephant-foot

export_step(part.part, "out.step")
mesher = Mesher(); mesher.add_shape(part.part); mesher.write("out.3mf")
export_stl(part.part, "out.stl", tolerance=0.005, angular_tolerance=0.05)
```

### L-profile (the union-free way to make brackets)
```python
with BuildPart() as br:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline((0,0),(40,0),(40,4),(4,4),(4,45),(0,45),(0,0))
        make_face()
    extrude(amount=60)
```

### Selectors you'll actually use
```python
part.faces().sort_by(Axis.Z)[-1]        # top face
part.faces().filter_by(Plane.XY)        # horizontal faces
part.edges().filter_by(Axis.Z)          # vertical edges
part.edges().group_by(Axis.Z)[-1]       # topmost edge group
part.faces().sort_by(SortBy.AREA)[-1]   # largest face
```

### Holes
```python
Hole(radius=2.1)                                   # through, M4 clearance (+0.2 FDM comp)
CounterBoreHole(1.7, 3.25, 2.0)                    # M3 cap screw
CounterSinkHole(1.7, 3.4, counter_sink_angle=90)   # avoid if printed cone faces down
```

### Hex nut pocket (M3)
```python
with BuildSketch(pocket_face):
    RegularPolygon(radius=(5.9/2)/cos(radians(30)), side_count=6, major_radius=True)
extrude(amount=-2.6, mode=Mode.SUBTRACT)
```
(5.9 = 5.7 AF + 0.2 clearance; polygon radius from across-flats = AF/2/cos30.)

### Embossed/debossed text
```python
with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):
    Text("V2", font_size=8)
extrude(amount=-0.6, mode=Mode.SUBTRACT)   # deboss prints cleaner than emboss on top faces
```

### Threads (only ≥M8)
```python
# pip install bd_warehouse --break-system-packages
from bd_warehouse.thread import IsoThread
```

### Tolerance test coupon (offer before first fit-critical part)
One plate with 5 holes Ø10.0/10.1/10.2/10.3/10.4 + one Ø10.0 peg. User prints once, reports which fits how; store result and use as the calibrated clearance thereafter.

### Import for editing
```python
part = import_step("thing.step")   # full BREP: can fillet, cut, measure faces
mesh = import_stl("thing.stl")     # tessellated ShapeList — booleans OK-ish, feature edits NO (see mesh-editing.md)
```

## Pitfalls hit in practice
- `fillet` on an empty edge selection raises `Fillets requires that edges be selected` — selectors silently match nothing; print `len(edges)` when unsure.
- Workplane origin confusion: `Locations` on a face uses the face's local frame — a hole "at (0,0)" lands at the face centroid, not global origin. Render early.
- Coordinate sanity: decide once (e.g. XY = bed, Z = up = print direction) and comment it in the script.
- `slice_plane`/section in trimesh needs `cap=True` for solid-looking cuts.
- Don't trust `Mesher` defaults for curvature-heavy parts; check triangle count in verify output.
