# Fabric face-engrave test models (26 Sep 2026)

One-layer design cut into the face (bed side), one filament swap at layer 2 (Z 0.2 mm), no AMS. Built by `build.py`
(`fabric.py --engrave face-<name>.json`), relief on, gap 0.4. Load the FACE colour first; Bambu Studio layer slider at layer 2,
right-click `+` -> Change filament (see `README-<name>.md`). `<name>-face.png` = the face as seen from the bed side (dark = colour 1, white = colour 2).

| Model | Tile | Tiles | Design | Min bed contact |
|---|---|---|---|---|
| pumpkin-drape | drape | 78 | triangle eyes, nose, zigzag mouth | 25.9 mm2 |
| bat-drape | drape | 101 | oval eyes, fanged mouth | 25.9 mm2 |
| ghost-drape | drape | 114 | oval eyes, O mouth | 25.9 mm2 |
| ghost-square | square | 74 | oval eyes, O mouth | 55.4 mm2 |
| coaster90-drape | drape | 98 | star | 25.9 mm2 |

Plate `print-plate.3mf` (bat + pumpkin + ghost-drape + ghost-square, 244 x 189 mm, >= 11 mm apart; coaster does not fit): slice_gate supports none PASS, 4h 37m, 40.2 g.
(`fabric.py --check` reports "fused" on any plate that mixes drape and square tiles, same as the older fabric-tests plate: per-model checks pass.)

## Honest legibility result
On the drape tile the pocket is limited by the 25 mm2 bed-contact floor, so each tile shows only a ~2.5 mm white square (or a clipped fragment).
The face reads as a sparse dot mosaic, not a drawing. On the square tile the pockets are thin slivers. Blind reads of the face renders: see the build report.
