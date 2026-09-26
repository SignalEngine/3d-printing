# Fabric test designs (26 Sep 2026)

Built with the real generator (`fabric.py`), rebuilt 26 Sep with the first-layer relief (bed level inset 0.3 mm for the first 0.4 mm, so squash can't fuse neighbours; full footprint kept where tiles are far apart, min bed contact drape 28.5 / square 64.1 mm^2); every design passes `fabric.py --check` (no fused tiles, 0.4 mm gaps).

| Design | Tile | Tiles | Size (mm) | Verdict |
|---|---|---|---|---|
| pumpkin-drape | drape | 78 | 87 x 79 | good: pumpkin + stem reads clearly |
| bat-drape | drape | 101 | 143 x 71 | ok: wings, ears, feet; chunky |
| ghost-square | square | 74 | 110 x 100 | good: round head, arms, 3-scallop hem |
| coaster90-drape | drape | 98 | 87 x 87 | good |
| coaster90-square | square | 69 | 90 x 90 | good (the old tile, for comparison) |
| bookmark-drape | drape | 104 | 151 x 47 | good |
| name tag (text) | square | — | — | DROPPED: separate letters can't link into one sheet (needs a backing: the "picture on fabric" phase) |

**Print plate** (`print-plate.3mf`): bat + pumpkin + coaster (drape) and ghost (square), 239 x 189 mm; slice_gate with
supports none: PASS, 4.4 h, 38.7 g PLA (A1, 0.20 mm Standard). Print flat, supports OFF.
Each design also has `-tiles.glb` (one node per tile) + `-tiles.json` (links) for the lander's cloth viewer.

## Two-tone, one swap, no AMS (face-down, like NASA fabric)
The side on the bed is the face (it picks up the plate texture). Load the FACE colour first.
1. Bambu Studio: open `print-plate.3mf`, slice, open Preview.
2. Drag the layer slider to **layer 3 (0.6 mm)**, right-click the `+` → **Change filament**.
3. Print. The A1 pauses once after layer 2; swap to colour 2 and resume. No swap back.
Result (`print-plate-face-two-tone.png`): the face is colour 1, and colour 2 shows as thin outlines where the
first-layer relief steps in and between tiles. Settings: No brim, supports off, elephant foot 0.15, 2 walls.
