# Fabric test designs (26 Sep 2026)

Built with the real generator (`fabric.py`); every design passes `fabric.py --check` (no fused tiles, 0.4 mm gaps).

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
supports none: PASS, 4.4 h, 38 g PLA (A1, 0.20 mm Standard). Print flat, supports OFF.
Each design also has `-tiles.glb` (one node per tile) + `-tiles.json` (links) for the lander's cloth viewer.
