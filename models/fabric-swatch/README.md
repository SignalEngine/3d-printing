# Fabric gap swatch (26 Sep 2026)

Print `swatch.3mf` flat, no supports (A1, PLA, 0.20 mm Standard). Left to right:

| Patch | Gap | Tag dots |
|-------|-----|----------|
| 1 (x 0-40)   | 0.30 mm | 3 |
| 2 (x 50-90)  | 0.40 mm | 4 |
| 3 (x 100-140) | 0.50 mm | 5 |

Each patch is 4 x 4 linked tiles (pitch 10, height 3.0). Tags are separate, unlinked plates below each patch.
Pick the patch that flexes freely without fusing; that gap becomes the default.

Slice (slice_gate, supports none, whole plate): 41m 40s (0.69 h), 7.7 g, cost floor £0.30, RESULT: PASS.
Renders: `render-iso.png`, `render-top.png` (also front / iso-rear). JSON: `swatch.json`.
Not proven: real-print fit. Geometry gap/captive checks pass; whether 0.3 fuses on this printer is unknown.
