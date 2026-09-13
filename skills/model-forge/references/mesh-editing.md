# Editing Downloaded Models (STL / 3MF / STEP)

## First: triage the file type — it decides everything
| Format | What it is | Edit capability |
|---|---|---|
| STEP/STP | Real BREP CAD | Full: fillets, holes, resize features, measure exactly. Import into build123d. |
| 3MF | Mesh + metadata | Same as STL geometrically |
| STL/OBJ | Triangle soup | Transforms, booleans, split, repair, measure. **No feature edits.** |

**Always tell the user**: if the model source (Printables, MakerWorld, GrabCAD, Thingiverse) offers STEP or F3D→STEP, grab that instead of STL. Saves an hour of mesh wrestling.

## The honest capability line for STL
CAN: scale (global or per-axis), mirror, rotate, cut sections off, boolean add/subtract shapes (add a mounting tab, cut a hole at given coords, split for build plate), merge parts, hollow/shell (roughly), repair, measure, remesh/decimate.
CANNOT (without remodelling): "make the wall 1 mm thicker", "change M4 holes to M5", "extend just the arm", parametric anything. The features don't exist in the data.

**Decision rule**: if the request is a feature edit on an STL of a simple-to-medium part → remodel it in build123d from measurements taken off the mesh. Usually faster and yields an editable master. Only fight the mesh for organic/sculpted shapes.

## Workflow for an incoming mesh
```python
import trimesh
m = trimesh.load("thing.stl", force="mesh")
m.merge_vertices()
print(m.is_watertight, m.body_count, m.extents, m.volume/1000)
```
1. **Verify before editing** — downloaded STLs are frequently broken already. If not watertight, repair FIRST (below), else booleans will fail or produce garbage.
2. **Units sanity**: an STL has no units. If extents look 25.4× off, it was inches: `m.apply_scale(25.4)`. If a "phone stand" is 4 mm tall, ask the user for one known dimension and scale to it.
3. **Measure** what you need: `m.bounds`, section slices (`m.section(plane_origin, plane_normal)`) to get hole positions/diameters, `trimesh.proximity` for thicknesses.

## Repair ladder (in order, stop when watertight)
```python
m.update_faces(m.unique_faces()); m.remove_unreferenced_vertices()
trimesh.repair.fix_winding(m); trimesh.repair.fix_normals(m)
trimesh.repair.fill_holes(m)
```
If still broken (real-world proof: repair could NOT fix self-intersection-type errors):
```python
# Nuclear option — manifold3d rebuilds a guaranteed-manifold mesh
from trimesh.interfaces import ... # not needed; use manifold directly:
import manifold3d, numpy as np
mf = manifold3d.Manifold(manifold3d.Mesh(m.vertices.astype(np.float32), m.faces.astype(np.uint32)))
res = mf.to_mesh(); m2 = trimesh.Trimesh(res.vert_properties[:, :3], res.tri_verts)
```
manifold3d also gives robust booleans (`+`, `-`, `^` on Manifold objects) — prefer it over trimesh's boolean engine for anything that matters.

## Boolean edits on meshes
```python
cutter = trimesh.creation.cylinder(radius=2.1, height=50)      # M4 clearance hole
cutter.apply_translation([x, y, 0])
result = trimesh.boolean.difference([m, cutter], engine="manifold")
```
Then run the full verification battery on the result — booleans are exactly where meshes break.

## Splitting for the build plate
```python
top = m.slice_plane([0,0,z], [0,0,1], cap=True)
bot = m.slice_plane([0,0,z], [0,0,-1], cap=True)
```
Add alignment: cut matching Ø3.2 holes in both halves, join with 3 mm filament pins. Offer this whenever a model exceeds 256 mm or prints better in halves.

## Delivery
Export edited meshes as **3MF** (+ STL if asked). Note in the reply which operations were done and that the part is mesh-only (no editable master), unless you remodelled — then deliver STEP + 3MF + the .py.

## Bambu Studio 3MF anatomy (reverse-engineered, verified by successful in-place patch)
A Bambu project 3MF is a zip:
- `3D/3dmodel.model` — root. `<resources>` holds one `<object>` per print object, each containing `<components>` with `p:path="/3D/Objects/object_N.model"`, an `objectid` (sub-object id inside that file), and the **true placement transform** (12 floats, row-vector convention: `M[:3,:3]=R.T`, translation last 3). `<build>` items place whole objects on plates.
- `3D/Objects/object_N.model` — actual meshes as sub-`<object>`s with vertex/triangle XML. **File numbering does NOT match settings object ids** — always resolve through the root components.
- `Metadata/model_settings.config` — object/part names, print settings. **The `matrix` metadata on parts is text-tool/gizmo data, NOT geometry placement** — applying it puts geometry in the wrong place (cost an hour; the root component transforms are the real ones).
- Multi-color text = separate mesh parts inside the same object; slicer merges overlapping bodies of one object, so a name embedded 0.5 mm into a wall prints fused and is colorable via AMS.

### In-place patch recipe (add a body to an existing object)
1. Insert new sub-`<object id="X" type="other">` with mesh XML into the right `object_N.model` (mimic existing UUID pattern).
2. Add a `<component ... objectid="X" transform="identity">` to the owning object in the root file.
3. Add a `<part>` entry in model_settings.config (name + identity matrix).
4. Validate: XML parses (`xml.dom.minidom`), whole file reloads in trimesh with +1 geometry, extract the new mesh back out and diff vertices (expect 0.0000 deviation).
5. Flag honestly that Bambu Studio is the final acceptance test.

## Working with text already on a model
- **Read it with OCR as ground truth** (apt-get install tesseract-ocr; pytesseract): project the text mesh to 2D with matplotlib PolyCollection, OCR it. For cylinder-wrapped text, unwrap first: least-squares circle fit in the wrap plane, then u = θ·R. Reading direction/mirroring is easy to get wrong — OCR of the *existing* text in the same projection is the reference that proves your added text is oriented correctly.
- **Orientation trap**: a model's "up" may be -Y or anything; infer from content (e.g. reading order of existing text), and verify added text by OCR in an outside-view unwrap, not by reasoning alone.

## Placing new features on a mesh surface
- **Free-space mapping**: ray-cast a (θ, y) grid from outside toward the axis; first-hit radius map reveals walls, pockets, windows. Face-center histograms FAIL on coarse meshes (large triangles → sparse centers → false holes).
- **Curved text generation**: matplotlib `TextPath` → polygons; assign letter counters (holes in a/e/o/…) by **containment**, never `unary_union` (it destroys the holes — verified failure); `trimesh.creation.extrude_polygon` per glyph; cylindrically wrap vertices (θ = x/R at wall radius, r = R_embed + z). Embed base ~0.5 mm into the wall, raise ~0.8–1.0 mm proud.
- **Every added body must intersect the parent** — check per-body boolean intersection volume > 0 with manifold engine. A floating letter prints in mid-air.
