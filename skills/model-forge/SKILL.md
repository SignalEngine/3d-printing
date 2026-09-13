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
# (re)install: $PY -m pip install build123d trimesh manifold3d matplotlib rtree shapely networkx lxml bd_warehouse
# networkx+lxml are required for trimesh to LOAD .3mf (missing = verify crashes)
# bd_warehouse adds threads/fasteners/gears (see references/build123d-patterns.md)
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
python3 scripts/verify_model.py out.3mf                         # hard checks must PASS
bash scripts/render.sh out.stl /tmp/view --section               # real f3d render, then LOOK at it
python3 scripts/features.py out.step --expect holes.json          # hole geometry vs intended sizes/faces
python3 scripts/fit.py lid.stl box.stl                            # clearance/interference between mating parts
python3 scripts/slice_gate.py out.3mf --max-hours 6 --price 25    # real slice + print time/cost + optional quote limits
python3 scripts/text_check.py out.3mf --expect "CONGRATULATION"   # OCR-verify ordered text actually reads correctly
```
- **verify_model.py**: watertight, winding, body count, build volume (256³), volume, overhang %, bed contact, thin walls (area-weighted sampling), mass estimate. Exit 0 required. Default `--bodies 1` FAILs a legitimate multi-colour/multi-material part (separate letter/logo shells embedded in the base body) — pass `--bodies N` for the actual expected shell count on those.
- **render.sh**: real depth-rendered PNGs via f3d under Xvfb — `<prefix>-iso.png`, `-front.png`, `-top.png`, and `-section.png` (with `--section`) or `-iso-rear.png` (without). Pass `--section-z <mm>` to cut somewhere other than the default mid-Z. Falls back to `render_views.py`'s matplotlib grid if f3d/xvfb-run are missing. Output MUST be viewed with the view tool: check features on correct faces, correct side/mirroring, holes where intended, proportions plausible against stated dimensions. Use `--section` whenever there are internal features.
  A geometrically-valid model with holes in the wrong face has happened in practice; the render catches what the numbers can't.
- **features.py**: lists every hole (diameter, depth, axis, which face) straight off the BREP (STEP input required — needs real CAD geometry, not a mesh). Pass `--expect holes.json` to hard-fail on a hole with the wrong diameter or on the wrong face — catches "M3 not M4" or "hole on the wrong face" as a number, before it needs a render to spot. **Limitation: axis-aligned holes only** — it snaps the hole's axis to the nearest cardinal (X/Y/Z), so an angled/compound-angle hole reports the wrong axis. Also, `"face"` is not the same shape as `"axis"`: a through-hole reports `"through Z"`, a blind hole reports `"+Z"`/`"-Z"` — write `--expect` entries with the right one or they'll never match. **Known limits (issue #2):** a blind hole whose floor is thinner than ~0.2 mm reads as `through`; `--expect` matching is first-fit, so two near-equal diameters on one face can false-FAIL. Check those cases with the section render.
- **fit.py**: for any assembly of ≥2 parts that mate (lid/box, clip/rail, pin/bushing) — export both from the SAME coordinate system, then check clearance/interference/contact area between them. `verify_model.py` only checks single bodies; this is the second check for anything that has to fit another part. **Known limit (issue #2):** the gap is measured from surface samples, so contact only at a corner or edge can read up to ~0.3 mm too high, and it varies run to run. Treat any reported gap under 0.5 mm as possible contact, and confirm with a render before calling it clear.
- **slice_gate.py**: a real headless slice through OrcaSlicer on a Bambu Lab A1 profile (0.4mm nozzle, `0.20mm Standard`, `Bambu PLA Basic`). Reports estimated print time and filament use. "Watertight" is not "slices clean" — this refuses non-manifold meshes itself, since OrcaSlicer will silently slice one without complaint. It also WARNs (not fails) when multiple watertight shells overlap each other (union volume < sum of body volumes) — `is_watertight` only checks each shell individually, so it misses this; it's a WARN because embedded multi-colour text/logo shells legitimately overlap the base body and the slicer merges them fine. Needs the OrcaSlicer AppImage extracted once — if `scripts/slice_gate.py` reports it's missing:
  ```bash
  curl -sL -o /tmp/orca.AppImage "$(curl -sL https://api.github.com/repos/OrcaSlicer/OrcaSlicer/releases/latest | python3 -c "import json,sys; d=json.load(sys.stdin); print(next(a['browser_download_url'] for a in d['assets'] if 'Linux_AppImage_Ubuntu2404_V' in a['name']))")"
  chmod +x /tmp/orca.AppImage && cd /tmp && ./orca.AppImage --appimage-extract
  mkdir -p /root/3d-printing/orcaslicer && mv squashfs-root /root/3d-printing/orcaslicer/
  # also needs: apt-get install -y libglu1-mesa libwebkit2gtk-4.1-0
  ```
- **slice_gate.py** also prints a cost block after any successful slice: `print hours`, `material` (g and £), `machine` (£), `cost floor` (£), and — with `--price` — `price per printer-hour`. It only FAILs (`QUOTE FAIL`, exit 1) when `--max-hours`/`--max-grams`/`--min-gbp-per-hour` (with `--price`) is given and exceeded; no flags = info only, same PASS as before. See a model's print time and cost before quoting it.
- **text_check.py**: any part carrying ordered text (a name, initials, a message) must pass this before delivery. It cross-sections the mesh and OCRs each slice in every rotation/mirror — catches wrong, missing, or overlapping-and-illegible text that a render can miss. Judge text and legibility from the front/orthographic view or a cross-section render, never the iso view — an iso render misled a real review on 2026-09-13 (the text was actually correct).
- On any FAIL: fix the geometry at the source (don't blind-repair your own generated model) and re-run every step above. Iterate until clean.

## Step 3 — Deliver
Copy to outputs and present:
1. **`.3mf`** — primary; Bambu Studio native (drag in, slice, print).
2. **`.step`** — editable master for future revisions.
3. **`.py`** — the parametric source (mention it exists; user can request tweaks as "make X 5 mm wider").
STL only if explicitly requested.
4. If the user is on mobile or asks to *see* the model: offer/build a self-contained HTML viewer (see `references/interactive-deliverables.md`) — phones cannot open 3MF locally (Bambu Handy lacks local file import).

Final reply must state, briefly: dimensions, assumptions made, print orientation (which face down), suggested settings for the part class (layer/walls/infill from design-rules table), material note if relevant, support/brim note if warranted, and print hours / grams / cost floor from `slice_gate.py`. No essays — a tight block.

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
