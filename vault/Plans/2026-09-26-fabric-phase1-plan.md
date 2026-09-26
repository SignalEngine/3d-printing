# Fabric phase 1: square cross-link generator + gap swatch (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]]. Repo `3d-printing` (model-forge skill), worktree `/root/wt-3dp-fabric`, branch
`build/fabric-generator` (off origin/master). Python: `/root/3d-printing/.venv/bin/python` (trimesh, manifold3d,
build123d, numpy, shapely if present; check before using; add NO new dependency without saying so).
Reference files are OTHER PEOPLE'S (licence: Standard Digital File License / BY): look at them for ideas only, never
copy their geometry: `/root/intentos/vault/inbox-files/tg-2026-09-26-08*`.

## Deliverables
1. `skills/model-forge/scripts/fabric.py`: a library + CLI.
   `fabric.py --outline rect:W,H | circle:D | poly:"x,y x,y ..." | text:"ABC" --pitch 10 --height 3.0 --gap 0.4
   --out fabric.3mf [--swatch]`
   - **Tile design: checkerboard of two tile types.**
     - "A" tiles are a square plate with a low BRIDGE (arch) along each edge.
     - "B" tiles are a square plate with a TAB on each side. The tab reaches under the neighbouring A tile's bridge
       and ends in a small upturned LIP that catches the bridge, so the pair can't slide apart.
     - Every B tab sits under an A bridge with `gap` clearance on every face.
     - The builder may refine this design (it's a known printable chainmail pattern), but the checks below are the
       contract.
   - **Printable flat on the A1 with NO supports:**
     - every overhang ≤ 45°, or a straight bridge ≤ 6 mm span;
     - first layer flat on z = 0 for every tile;
     - smallest feature ≥ 0.8 mm (2 perimeters at 0.4 nozzle).
   - **Filling an outline:** place tiles on the pitch grid; keep a tile only if at least half its footprint is inside
     the outline. The kept tiles must form ONE connected sheet (drop islands and say so). Anchor cells (tabs/bridges
     facing a missing neighbour) are trimmed: no dangling tab without its bridge.
   - **Output:** one 3MF, one object per tile (named `tile-r<row>-c<col>`), sized to fit 256 x 256 mm, else refuse
     with a clear message. Also write `<out>.json`: tile count, pitch, gap, outline, bbox.
   - **`--swatch`:**
     - one plate with three 40 x 40 mm patches, left to right at gap 0.30 / 0.40 / 0.50 mm, 10 mm apart;
     - a small solid tag tile (not linked) below each patch with 3 / 4 / 5 embossed dots;
     - the JSON lists which patch is which.
2. `skills/model-forge/tests/test_fabric.py` (unittest style like `test_model_card.py`). **These are the contract:**
   - Gap: for every pair of neighbouring tiles, the minimum distance ≥ `gap - 0.02` (trimesh proximity on sampled
     surfaces or manifold distance). Test at gap 0.3 and 0.5 on a 4x4 rectangle.
   - Captive: for every neighbour pair, moving one tile 2 mm along +x, −x, +y, −y and +z makes it intersect the
     other (manifold3d boolean intersection volume > 0.01 mm³). They're locked in every direction; they only flex
     within the gap.
   - Bodies: the number of objects in the 3MF equals the tile count in the JSON, and each tile is exactly one
     watertight body.
   - Outline fill: `circle:60` gives a single connected sheet; nothing sits outside the circle by more than half a
     pitch; `rect:40,40` at pitch 10 gives 16 tiles.
   - Bed: `rect:300,100` refuses with a message.
   - Prints: `slice_gate.py` on the 4x4 sheet with `--supports none` → RESULT: PASS, and `verify_model.py
     --bodies 16`… (verify_model runs per mesh: check it with the combined mesh and `--bodies N`). If slice_gate warns
     "needs supports", that is a FAIL of this test.
   - Swatch: `--swatch` writes 3 x 16 linked tiles + 3 tags, the JSON maps the gaps, and it fits the bed.
3. `skills/model-forge/references/fabric.md` (≤ 60 lines): what fabric is, the tile contract, the CLI, and the tuned
   default gap (placeholder until James's print).
   - `SKILL.md`: a pointer line in the references list.
4. The swatch for James, in `models/fabric-swatch/`:
   - `swatch.3mf` + `swatch.json`;
   - a render: `render.sh` iso + top PNGs;
   - the slice numbers (hours/grams) in `models/fabric-swatch/README.md`, saying which patch is which gap.

## Checks the builder runs and pastes (capture exit codes; never `| tail && git commit`)
- `/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests` (the whole model-forge suite).
- Sabotage 1: set the lip height to 0 → the captive test goes red. Sabotage 2: make the gap 0 in the geometry
  while keeping the JSON at 0.4 → the gap test goes red. Restore, then `rg SABOTAGE` returns nothing.
- Commit with explicit paths (`.venv` is a symlink; never `git add -A`). Don't push, don't open a PR.

## Not in this phase
TweakMyPart integration, pictures, colours, hex, straps, clothing, remix (later phases in the spec).
