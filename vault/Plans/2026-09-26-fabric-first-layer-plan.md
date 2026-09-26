# Fabric: first-layer relief so tiles don't fuse at the bed (build plan, 26 Sep 2026)

James printed the test plate (A1, 0.4 nozzle, 0.20 mm layers, PLA): after about 30 min "the square one looks all
linked together" (fused). Likely cause: first-layer squash ("elephant's foot"). The first layer prints wider, so the
0.4 mm gaps close at bed level. The square tile has long parallel edges at z=0, which is the worst case. Photo
pending.

## Worktree
`3d-printing`: `/root/wt-3dp-foot`, branch `build/fabric-first-layer`. Python `/root/3d-printing/.venv/bin/python`.

## Change (model-forge `scripts/fabric.py`, BOTH tiles)
- **Bottom relief:** for every tile, the part below z = `FOOT_H` (0.4 mm = 2 layers at 0.20) is inset by `FOOT_IN`
  (0.3 mm) from its footprint. This is a bevel/step, so the gap between neighbours at bed level is ≥ gap + 2 x
  FOOT_IN.
- Implement with manifold3d/trimesh, e.g. `tile = (tile − slab(z<FOOT_H)) ∪ extrude(offset(slice(tile, z=FOOT_H/2),
  −FOOT_IN), FOOT_H)`, or equivalent.
- Keep every tile ONE watertight body, printable flat (a 0.3 mm step is a trivial overhang).
- Don't shrink features that are thinner than 2 x FOOT_IN + 0.8 at the bed (they would vanish): inset those less, or
  skip them, but the gap rule below must still hold.
- `FOOT_IN` / `FOOT_H` are constants plus CLI flags (`--foot-in`, `--foot-h`). The defaults are ON. The sidecar
  records them.

## Tests (`tests/test_fabric.py`), each red without the change
- **Bed-level gap:** for every neighbour pair, slice both tiles at z = 0.1 and z = 0.3; the minimum 2D distance
  between their sections is ≥ gap + 2 x FOOT_IN − 0.05. Run it for both tiles at gap 0.3 and 0.4.
- All existing contract tests still pass for both tiles: gap overall ≥ gap, captive, drape fold ±30°, bodies, slices
  with no supports, `--check`.
- Sabotage: set FOOT_IN = 0 → the bed-level gap test goes red. Restore, then `rg SABOTAGE` returns nothing.

## Also
- Regenerate `models/fabric-tests/*` (the same designs + the print plate) and `models/fabric-examples/*` with the
  relief, and re-slice the plate (report hours/grams).
- `references/fabric.md`: document the relief, and tell users to keep "Elephant foot compensation" at the default or
  on.

## Checks (builder pastes, exit codes captured)
`/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests`. Explicit-path commits; don't push.
