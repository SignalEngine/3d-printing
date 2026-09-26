# Fabric gap swatch, drape tile (26 Sep 2026)

Print `swatch.3mf` flat, no supports (A1, PLA, 0.20 mm Standard). Left to right:

| Patch | Gap | Tag dots | Tile height |
|-------|-----|----------|-------------|
| 1 (x 0-40)    | 0.30 mm | 3 | 3.6 mm |
| 2 (x 50-90)   | 0.40 mm | 4 | 3.8 mm |
| 3 (x 100-140) | 0.50 mm | 5 | 4.0 mm |

Each patch is 5 x 5 linked drape tiles (pitch 8). Tags are separate, unlinked plates below each patch.
Pick the patch that folds freely without fusing; that gap becomes the default (`DEFAULT_GAP` in `fabric.py`).

The tile: a plate with a raised dome; a bar on its +x/+y edges, a ring on its -x/-y edges. Each neighbour's ring
encircles this tile's bar, so every link is a chain link that hinges about the shared edge. Regenerate:
`fabric.py --swatch --tile drape --out swatch.3mf`. Renders: `render-iso.png`, `render-top.png` (also front / iso-rear).

Slice (`slice_gate`, supports none, whole plate): 1h 01m 20s (1.02 h), 7.83 g, cost floor £0.40, support blocks 0,
RESULT: PASS. `verify_model --bodies 78`: PASS, bodies 78, watertight.
Not proven: a real print. The geometry gap / captive / +-30 degree fold checks pass; whether 0.3 fuses on this printer
is unknown. `verify_model` warns "needs supports 136 mm^2 at z=1.6": those are the 2.4 mm bar bridges between two
posts, which its per-layer heuristic cannot see are anchored; the slicer emits no support blocks. Whether the bars
bridge cleanly on the A1 is only known after printing.
