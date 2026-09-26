# Fabric two-tone (one filament swap): raised detail tiles in colour 2 (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]] ("Two-colour design"). James wants to test black + white two-tone next, with the same
or better shapes. It builds ON the first-layer relief ([[2026-09-26-fabric-first-layer-plan]]), so start after that
merges (same file).

## Worktree
`3d-printing`: `/root/wt-3dp-twotone`, branch `build/fabric-two-tone`.

## Method (any printer, one swap)
- Selected tiles (the "detail" cells: a face, eyes, a mouth) get a **raised cap**: they are `RAISE` (0.6 mm = 3
  layers) taller than the rest.
  - Drape tile: raise the dome/top.
  - Square tile: raise the plate top.
  - It must not break the gap/captive/fold contract. The cap sits inside the tile's top footprint, away from links.
- Everything prints in colour 1 up to the normal tile height, then ONE swap to colour 2, so only the raised caps come
  out colour 2. No swap back.
- **Swap height:** the first layer above the normal tile top.
  - Compute it from the generator's own numbers and layer height 0.20 (first layer 0.20): report `swap_z_mm` and
    `swap_layer`.
- **Embed the colour change in the 3MF** so Bambu Studio opens with it set:
  - Bambu's project metadata `Metadata/custom_gcode_per_layer.xml` (plate 1, a filament change at `top_z` = swap_z,
    extruder 2 / colour #FFFFFF, mode single-extruder).
  - Research the exact schema from Bambu Studio / OrcaSlicer source (both open source; OrcaSlicer is at
    `/root/3d-printing/orcaslicer`: grep `custom_gcode_per_layer`) and write exactly that. Two filaments are defined
    in `Metadata/project_settings.config` (black, white).
  - If exact embedding can't be confirmed from the source, still write it and SAY SO in the report; the README then
    tells James how to add the change manually.
- **README per model:** "Colour 1 = black, colour 2 = white. The colour change is at layer N (Z mm). Bambu Studio
  shows it on the layer slider; on an A1 without an AMS the printer pauses for you to swap."

## Generator changes (`scripts/fabric.py`)
- `--raise-mask PATH|poly:...` (cells whose centre falls inside get a raised cap) and `--raise 0.6`.
- The sidecar records `raised_tiles`, `swap_z_mm` and `swap_layer`.
- `--two-tone "#000000,#FFFFFF"` writes the 3MF colour-change metadata + filament colours.

## Test models (`models/fabric-two-tone/`), with first-layer relief ON and the fixed gap
Each design gets a detail mask (drawn as polygons in the build script, committed as `detail-<name>.json`):
- **pumpkin** (drape): jack-o'-lantern face; triangle eyes + zigzag mouth as raised cells.
- **bat** (drape): two eyes.
- **ghost** (drape AND square, so the tiles can be compared): two eyes + an "O" mouth.
- **round coaster** (drape): a simple star or a heart in the middle.
Also a **print plate** with as many as fit on the A1 (256 x 256), with ≥ 10 mm between designs. Slice it
(slice_gate, supports none) and report hours/grams. Renders: top view coloured (colour 1 dark, raised caps white),
e.g. by exporting the caps as a separate coloured mesh for the render only.

## Tests (`tests/test_fabric.py`), each red without its code
- Raised tiles: exactly the cells inside the mask are RAISE taller; the others are unchanged.
- The contract still holds with raised tiles (gap, captive, drape fold ±30°, bodies, bed contact, bed-level gap).
- `swap_z_mm` is above every un-raised tile top and below every raised tile top.
- The 3MF contains the colour-change metadata at `swap_z_mm`, and 2 filament colours.
- Sabotage: raise 0 → the raised-tile test goes red. Restore, then `rg SABOTAGE` returns nothing.

## Checks (builder pastes; exit codes captured)
`/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests`. Explicit-path commits; don't push.

## Known traps (brain, after #19 merged)
- `check_sheet` flags tiles whose volume differs from the median as "not equal tiles"/"fused". Raised tiles are bigger:
  teach `--check` to read `raised_tiles` from the sidecar (or allow the cap volume), and keep a test that a real fused
  pair on a two-tone sheet still goes red.
- First-layer relief (#19, `relieve_sheet`) runs after tile build; the cap must not change the z < FOOT_H section.
- Drape tile: the cap must not collide with a neighbour when folded ±30° (the drape test covers it; run it on raised tiles).
