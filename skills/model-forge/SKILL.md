---
name: model-forge
description: Create, edit, repair, and verify 3D-printable models (STL/STEP/3MF) for James's Bambu Lab A1, delivering print-ready files for Bambu Studio. Use this skill whenever the user wants to design a part, bracket, mount, holder, case, adapter, clip, jig, stand, enclosure, spacer, or any physical object; wants to edit, resize, fix, split, or combine a downloaded 3D model; mentions STL, STEP, 3MF, CAD, 3D printing, Bambu, MakerWorld, Printables, or Thingiverse; or asks whether something is printable. Trigger even for vague requests like "can you make me a thing that holds X" — that is a modelling request.
---

# Model Forge — CAD for the Bambu A1

Produce **verified, print-ready** models. The bar: every delivered file has passed the automated battery AND a visual render inspection. Never deliver an unverified file.

## Stack (all proven working in this environment)
On this VPS the stack lives in a venv — use its python for everything (no --break-system-packages):
```bash
PY=/root/3d-printing/.venv/bin/python
S=/root/.claude/skills/model-forge/scripts
# (re)install: $PY -m pip install build123d trimesh manifold3d matplotlib rtree shapely networkx lxml
# networkx+lxml are required for trimesh to LOAD .3mf (missing = verify crashes)
```
Work files go in `/root/3d-printing/models/<name>/`. Below, read `python3 scripts/…` as `$PY $S/…`.
- **build123d** — parametric BREP CAD (OpenCASCADE). Primary modelling tool.
- **trimesh + manifold3d** — mesh verification, repair, robust booleans.
- Read `references/build123d-patterns.md` before writing any CAD code (proven patterns + real pitfalls).
- Read `references/fdm-design-rules.md` before setting any dimension that mates, flexes, or bears load.
- For incoming STL/3MF/STEP files, read `references/mesh-editing.md` first (includes Bambu 3MF anatomy + in-place patching).
- For any interactive/visual deliverable (HTML viewer, preview page), read `references/interactive-deliverables.md` — headless-browser input simulation is MANDATORY before delivery, not just rendering.

## Step 0 — Interrogate the request (before any code)
Missing requirements are the top cause of reprints. If any of these are unknown and matter for the part, ask (use tappable options on mobile; batch into ONE round of questions, max 3):

1. **Function & load**: what does it hold/do, roughly what weight, which direction?
2. **Critical dimensions & mating parts**: what must it fit? Exact measurements of the mating object (ask user to caliper it; phone-photo of the object next to a ruler also works — Claude can read it).
3. **Fit type** for any interface: press / snug / loose (drives clearances).
4. **Fasteners**: screws available? Heat-set inserts on hand or not?
5. **Material** they'll print in (default PLA; steer per design-rules if load/heat/outdoor).

Don't ask about things that don't affect the part, and don't ask what can be assumed and stated ("assumed M4 clearance holes — say if different"). State every assumption explicitly in the final reply.

**Fit-critical parts**: offer the tolerance test coupon (patterns file) on first occurrence; if the user has calibrated clearances from a previous coupon, use those numbers.

## Step 1 — Model
- Parametrize all key dimensions at the top of the .py.
- Comment the orientation choice: which face is on the bed and why (strength: layer lines are weak in Z — see design rules).
- Prefer single closed-profile extrudes/revolves over boolean unions (manifold-error source #1).
- Design FOR the chosen print orientation: 45° rule, chamfered bottom edges, bridging limits, hole compensation (+0.2 mm vertical holes).

## Step 2 — Verify (mandatory, no exceptions)
```bash
python3 scripts/verify_model.py out.3mf            # hard checks must PASS
python3 scripts/render_views.py out.3mf view.png --section   # then LOOK at it
```
- verify_model.py: watertight, winding, body count, build volume (256³), volume, overhang %, bed contact, thin walls, mass estimate. Exit 0 required.
- render_views.py output MUST be viewed with the view tool. Check: features on correct faces, correct side/mirroring, holes where intended, proportions plausible against stated dimensions. Use `--section` whenever there are internal features.
- **Primary real render (true depth, lighting) — f3d under Xvfb** (osmesa/egl backends write nothing on this VPS; plain f3d core-dumps without a display). Export STL first, then:
  `xvfb-run -a f3d out.stl --output=iso.png --resolution=800,600 --up=+Z --camera-direction=-1,1,-1.2`
  Swap `--camera-direction` for other views (0,0,-1 top; 0,1,0 front). Don't pass `--edges`: it draws the tessellation, and long sliver triangles show up as fake dark bars.
- A geometrically-valid model with holes in the wrong face has happened in practice; the render catches what the numbers can't.
- On any FAIL: fix the geometry at the source (don't blind-repair your own generated model) and re-run BOTH steps. Iterate until clean.

## Step 3 — Deliver
Copy to outputs and present:
1. **`.3mf`** — primary; Bambu Studio native (drag in, slice, print).
2. **`.step`** — editable master for future revisions.
3. **`.py`** — the parametric source (mention it exists; user can request tweaks as "make X 5 mm wider").
STL only if explicitly requested.
4. If the user is on mobile or asks to *see* the model: offer/build a self-contained HTML viewer (see `references/interactive-deliverables.md`) — phones cannot open 3MF locally (Bambu Handy lacks local file import).

Final reply must state, briefly: dimensions, assumptions made, print orientation (which face down), suggested settings for the part class (layer/walls/infill from design-rules table), material note if relevant, support/brim note if warranted. No essays — a tight block.

## Editing downloaded models
Follow `references/mesh-editing.md`. Key rules:
- STEP in → full CAD edits. STL in → transforms/booleans/repair/split only; **feature edits require remodelling** — say so plainly and offer to remodel from measurements (usually faster and better).
- Verify the incoming file BEFORE editing (downloaded meshes are often already broken); repair first, edit second, verify again after.
- Check units: dimension looks 25.4× off → it's inches.

## Meta-rule from real failures
Every deliverable type needs verification OF ITS OWN KIND. Geometry was verified while the viewer UI shipped broken twice (off-frame camera, then dead touch controls) — because "verify" was interpreted as "verify the mesh". The test must exercise what the user will actually do: for models, slice-readiness + visual render; for viewers, simulated touch input + pixel assertions; for patched project files, roundtrip re-extraction. If the user's first action with the artifact hasn't been simulated, it isn't verified.

## Honesty constraints
- Clearance/tolerance numbers are community starting points, not calibrated facts for this printer+filament — label them as such and push the test coupon for fit-critical work.
- Verification proves geometry, not real-world fit or strength. Say what was checked, not more.
- If a request exceeds what mesh editing can do, or a shape is beyond reliable code-CAD (organic sculpts), say so immediately rather than delivering a bad approximation.
