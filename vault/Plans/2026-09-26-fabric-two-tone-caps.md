# Fabric two-tone: caps big enough to read as a face (continuation, 26 Sep 2026)

Continues [[2026-09-26-fabric-two-tone-plan]] (built as 3eeeb36 on `build/fabric-two-tone`, worktree
`/root/wt-3dp-twotone`, unpushed). Brain review: the mechanism works, but the faces don't read.
- The caps are small dots: drape 3.2 mm disc, square 2x4 mm block. They are confined to the link-free top area.
- At pitch 8 a pumpkin face shows as a dot grid.

James chose: bigger caps, then print.

## Change (`scripts/fabric.py`, both tiles)
- **Mushroom cap:** keep the current column (its footprint is clear of the links).
  - Above the highest link feature + gap, flare it out at ≤ 45° (prints without support) to a flat top covering as
    much of the tile's cell as the contract allows. Target: the top is the cell minus `gap` per side.
  - The white layers are the top ≥ 2 layers (0.4 mm) of the cap. The swap stays one Z per plate.
- **Contract:**
  - gap ≥ `gap` everywhere, including cap to cap and cap to the neighbour's links;
  - captive holds; one watertight body per tile; bed contact and bed-level gap unchanged;
  - **fold:** plain–plain and plain–raised pairs still fold ±30° on the drape tile. Raised–raised pairs may fold
    less, because the face area is allowed to be stiffer. Measure it and record `raised_fold_deg` in the sidecar. It
    must be ≥ 10°, never fused. The square tile keeps its current (non-fold) contract.
  - If a full-cell top can't meet this, take the biggest cap that does and report its size.
- **Faces that read:** redraw the masks so every feature is ≥ 2 cells (triangle eyes about 3 cells, a mouth as a row
  of ≥ 4 cells). Pumpkin, bat (eyes), ghost drape + square (eyes + "O" mouth), coaster heart.
  - Render the top view in colour 1 dark + caps white.
  - A fresh-context check: a subagent sees ONLY the top render and must name what it is (pumpkin / ghost / bat) and
    say where the face is. Paste its answer.

## Regenerate
`models/fabric-two-tone/*`, both plates re-sliced (slice_gate, supports none) → hours/grams, READMEs with swap layer +
Z. Report the actual cap top size in mm per tile type.

## Tests (red without the change)
- The cap top area per raised tile ≥ 60 % of the cell area (or the reported max, asserted exactly).
- The contract tests above for raised tiles, including cap-to-cap gap on adjacent raised tiles and the ±30°
  plain–raised fold.
- `raised_fold_deg` ≥ 10 and recorded.
- Sabotage: flare off → the area test goes red. Restore, then `rg SABOTAGE` returns nothing.

## Checks
`/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests` (run-limited, exit code captured before
commit). Explicit-path commits on the same branch; don't push; don't commit `.ref-*`.
