# Fabric (print-in-place linked tiles)

A flexible sheet printed flat in one go: tiles linked like chainmail, no supports, no assembly.
Generator: `scripts/fabric.py`. Tests: `tests/test_fabric.py`. Spec: vault `2026-09-26-fabric-spec`.
Two tiles: `--tile drape` (v2, draping) and `--tile square` (v1, the default until TweakMyPart moves its preview + price to drape). Both share the outline fill, CLI,
sidecar (with a `"tile"` key) and `--check`.

## Drape tile (v2; becomes the default once TweakMyPart switches)
- Every tile is identical: a plate (1.2 mm) with a raised dome (1 mm), a BAR on its +x/+y edges (1.2 mm octagonal rod
  held between two posts, a 2.4 mm bridge) and a RING on its -x/-y edges (octagonal loop, 0.85 mm wall). A neighbour's
  ring encircles this tile's bar: loop through loop, so every link is a chain link. Edge tiles omit the features that face
  a missing neighbour.
- The hinge axis is the shared edge line at the bar's centre height `drape_dims(gap)["zc"]` (1.9 mm at gap 0.4). The plates
  and posts are cut back inside a 22 degree wedge around that axis, so a linked pair folds +-30 degrees (tested; +-45 also
  clears) without the tiles touching.
- Tested contracts: every neighbour pair (edge and diagonal) >= gap - 0.02 apart; captive: moving one tile 2 mm along
  +-x, +-y (and +z for at least one of each pair, and every tile is locked in +z) collides; DRAPE: rotating either tile
  of every pair +-30 degrees about the hinge axis does not intersect the other, and a tile slides 0.3 mm toward its
  neighbour freely; the SQUARE tile fails the same fold test (positive control); one watertight body per tile; every downward
  face <= 45 degrees off vertical or a flat bridge <= 6 mm; `slice_gate --supports none` and `verify_model --bodies N` pass on
  a 5 x 5 sheet; `--check` passes on a drape sheet and still catches fused / squeezed / forged sheets.
- Sizes: pitch 8 (default; >= 6), height set by the ring (`2 * ring apothem`: 3.6 / 3.8 / 4.0 mm at gap 0.3 / 0.4 / 0.5), gap
  0.1-0.6. `--height` is ignored for this tile. Rings reach ~2 mm beyond the outline on the -x/-y sides.
- verify_model prints "needs supports" for it: that is the bar bridges (2.4 mm, anchored at both ends), see the swatch README.

## Square tile (`--tile square`, v1)
- One tile shape on a checkerboard: "A" has bridges (an arch over a slot in the plate) on its +-x sides and
  tabs on +-y; "B" is A rotated 90 degrees. A tab lies in the neighbour's slot, under its bridge, and ends in
  an upturned lip beyond the bridge, so the pair can't slide apart or lift out.
- Every face between neighbours keeps `gap` clearance (tested: min distance >= gap - 0.02, incl. diagonals).
- Captive (tested): moving one tile 2 mm along +-x, +-y makes it hit its neighbour; +z is caught for the
  tab tile of each pair, and every tile is locked in +z by at least one neighbour.
- Print flat: every tile on z=0, overhangs are vertical or a straight bridge <= 3.2 mm, smallest feature
  >= 0.8 mm (bar 1.2, leg 1.0, lip 1.0, tab 2.0). Plate 1.2 mm thick, total height `--height` (3.0).
- Sizes are fixed except pitch/gap/height; pitch must leave a 1.2 mm plate waist (>= ~9 mm at gap 0.4).
- It does NOT drape: the tab sits in a slot only `gap` tall, so folding a pair collides (tested).

## Fill rules
Tiles sit on a pitch grid from the outline's bbox corner; a cell is kept if >= half of it is inside the outline.
Only the largest connected group is kept (islands dropped, reported). Links (bars, rings, tabs, bridges) facing a missing neighbour
are omitted. Sheet must fit 256 x 256 mm, else refused (exit 2).

## CLI
`fabric.py --outline rect:W,H | rrect:W,H,R | circle:D | heart:W | poly:"x,y x,y ..." | text:ABC --tile drape|square --pitch 8|10 --height 3.0 --gap 0.4 --out f.3mf [--swatch] [--tiles-glb f-tiles.glb]`
- Writes one 3MF object per tile (`tile-r<row>-c<col>`) and `<out>.json` (tile, tiles, pitch, gap, outline, bbox).
- `--tiles-glb X-tiles.glb` also writes one glTF node per tile (origin at its bbox centre) and `X-tiles.json` (tiles + `links`,
  one pair per hinge): what the lander's cloth viewer reads. Examples: `models/fabric-examples/` (drape; `*-square*` = v1).
- `text:` letters are 5 pitches tall (FreeSans Bold); thin strokes lose cells, so expect dropped islands.
- `--swatch`: three 40 x 40 patches at gap 0.30 / 0.40 / 0.50 (left to right, 50 mm pitch) with an unlinked
  tag below each (3 / 4 / 5 dots); JSON `patches` maps gap to dots.

## Tuned gap
Default 0.4 mm is a PLACEHOLDER (community starting point, not calibrated for this printer/filament).
Print `models/fabric-swatch-drape/swatch.3mf` (or `fabric-swatch/` for the square tile), pick the patch that flexes freely without fusing, then update
`DEFAULT_GAP` in `fabric.py` and this line.
