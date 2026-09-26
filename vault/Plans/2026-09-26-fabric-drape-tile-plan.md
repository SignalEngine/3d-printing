# Fabric tile v2: our own NASA-style draping tile (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]]. James, 26 Sep: the current square tile "looks weird", so make **our own NASA-style
tile** (small raised tiles linked by rings on all sides, which drapes like chainmail), our own geometry, and make it
the default. Reference for the IDEA only (never copy geometry): the NASA fabric files in
`/root/intentos/vault/inbox-files/tg-2026-09-26-08*` (see their renders; each tile is a small raised unit linked on
every side, and the sheet folds and drapes).

## Worktree
`3d-printing`: `/root/wt-3dp-drape`, branch `build/fabric-drape-tile`. Python `/root/3d-printing/.venv/bin/python`.

## Deliverables
1. `fabric.py --tile drape` (new tile style), with `--tile square` kept as the old one.
   - The default becomes `drape` ONLY once its tests pass. Same CLI, outlines, sidecar (add a `"tile"` key) and
     `--check`.
   - Suggested geometry (the builder may choose another if it meets the contract):
     - each tile is a small square body (pitch 6–8 mm) with a raised dome/boss on top;
     - on each of its 4 sides there's either an open LOOP (a ring standing up from the edge) or a HOOK/ring that
       passes THROUGH the neighbour's loop;
     - it alternates by checkerboard like v1, so every link is loop-through-loop;
     - all printable flat: bridges ≤ 6 mm, overhangs ≤ 45°, features ≥ 0.8 mm, first layer on z=0;
     - clearance = `gap` everywhere.
2. **The contract, as tests** (`tests/test_fabric.py`, new class `Drape`; the existing contract tests run for BOTH
   tiles):
   - **gap:** every neighbour pair ≥ gap − 0.02 apart;
   - **captive:** moving a tile 2 mm along ±x, ±y or +z collides with its neighbour (it can't come apart);
   - **DRAPE (new, the reason for v2):** for every neighbour pair, rotating one tile about the shared edge axis by +30°
     and by −30° (about the axis through the link, at the plate's mid-height) does NOT intersect the neighbour.
     Also: it slides ≥ 0.3 mm toward the neighbour without collision. The v1 square tile should FAIL this drape test:
     assert that too, as the positive control.
   - **bodies:** objects == tiles, each one watertight body;
   - **prints:** `slice_gate --supports none` passes on a 5x5 drape sheet; verify_model `--bodies N` passes;
   - **`--check`:** it passes on a drape sheet (equal volumes, gap), and the fused-pair tests still work.
3. **Swatch v2:** `--swatch --tile drape`: three 40 x 40 patches at gaps 0.3 / 0.4 / 0.5 plus tags; files in
   `models/fabric-swatch-drape/`: 3mf, json, renders and a README with slice numbers.
4. **Examples v2:** regenerate `models/fabric-examples/` with the drape tile:
   - heart-100mm and round-coaster-90mm: `.3mf`, `-tiles.glb` (one node per tile), `-tiles.json` (links), renders;
   - keep the v1 files as `*-square*` alongside.
   The lander's cloth viewer reads these files.
5. `references/fabric.md`: document both tiles, the drape contract, and the default.

## Checks (builder pastes, exit codes captured; never `| tail && git commit`)
- `/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests`.
- Sabotage: make the loop clearance 0 → the gap test goes red; remove the hook's pass-through → the captive test goes
  red. Restore, then `rg SABOTAGE` returns nothing.
- Explicit-path commits (`.venv` is a symlink). Don't push.

## Not in this plan
Switching TweakMyPart's default or the lander viewer to v2 (the brain does that after review, with the host
`--check` unchanged); hex/scale tiles.
