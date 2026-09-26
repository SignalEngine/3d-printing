# Fabric (print-in-place linked tiles)

A flexible sheet printed flat in one go: square tiles linked like chainmail, no supports, no assembly.
Generator: `scripts/fabric.py`. Tests: `tests/test_fabric.py`. Spec: vault `2026-09-26-fabric-spec`.

## Tile contract
- One tile shape on a checkerboard: "A" has bridges (an arch over a slot in the plate) on its +-x sides and
  tabs on +-y; "B" is A rotated 90 degrees. A tab lies in the neighbour's slot, under its bridge, and ends in
  an upturned lip beyond the bridge, so the pair can't slide apart or lift out.
- Every face between neighbours keeps `gap` clearance (tested: min distance >= gap - 0.02, incl. diagonals).
- Captive (tested): moving one tile 2 mm along +-x, +-y makes it hit its neighbour; +z is caught for the
  tab tile of each pair, and every tile is locked in +z by at least one neighbour.
- Print flat: every tile on z=0, overhangs are vertical or a straight bridge <= 3.2 mm, smallest feature
  >= 0.8 mm (bar 1.2, leg 1.0, lip 1.0, tab 2.0). Plate 1.2 mm thick, total height `--height` (3.0).
- Sizes are fixed except pitch/gap/height; pitch must leave a 1.2 mm plate waist (>= ~9 mm at gap 0.4).

## Fill rules
Tiles sit on a pitch grid from the outline's bbox corner; a cell is kept if >= half of it is inside the outline.
Only the largest connected group is kept (islands dropped, reported). Tabs/bridges facing a missing neighbour
are omitted. Sheet must fit 256 x 256 mm, else refused (exit 2).

## CLI
`fabric.py --outline rect:W,H | rrect:W,H,R | circle:D | heart:W | poly:"x,y x,y ..." | text:ABC --pitch 10 --height 3.0 --gap 0.4 --out f.3mf [--swatch]`
- Writes one 3MF object per tile (`tile-r<row>-c<col>`) and `<out>.json` (tiles, pitch, gap, outline, bbox).
- `text:` letters are 5 pitches tall (FreeSans Bold); thin strokes lose cells, so expect dropped islands.
- `--swatch`: three 40 x 40 patches at gap 0.30 / 0.40 / 0.50 (left to right, 10 mm apart) with an unlinked
  tag below each (3 / 4 / 5 dots); JSON `patches` maps gap to dots.

## Tuned gap
Default 0.4 mm is a PLACEHOLDER (community starting point, not calibrated for this printer/filament).
Print `models/fabric-swatch/swatch.3mf`, pick the patch that flexes freely without fusing, then update
`DEFAULT_GAP` in `fabric.py` and this line.
