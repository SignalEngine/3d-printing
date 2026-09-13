# STL edit lessons: poop bag holder (2026-09-13)

Job: James's downloaded "Poop Bag Holder - No Holes - Flexi" STL. Two changes: turn the hexagon pattern into dog-bone holes, and add a loop for a treat-pouch snap hook (gate opening 4.54 mm). Result: `models/poop-bag-holder/holder_v3.3mf`. It passes every gate and slices on the A1: about 4 h, 23.1 cm³.

## What went wrong on attempt 1, and the root causes
1. **`trimesh.Trimesh.section()` returned identical data at every Z** for this mesh: the same area and radii at z=1 and z=69. Every measurement built on it was wrong, including a wall radius of 22.55 (really 23.0). `section_multiplane()` gave correct, varying slices. **Rule: never trust `section()` for per-height measurement; use `section_multiplane` and sanity-check that values change with Z.**
2. **The source file's tube was tilted 1.90°.** Measured from a fixed vertical axis, the wall looked barrel-shaped (radius drifting 24.9 → 23.6). Fitting circles to the inner bore at several heights showed the centre moving linearly (resid 0.005 mm): a straight tube on a tilted axis. **Rule: fit the axis as a 3D line from the bore at several Z, stand the part upright, then measure.** This also raised bed contact from 11 to 74 mm².
3. **The hexagons were sunken panels (r=25.0 in a 26.0 skin), not raised ridges.** Shading in the renders was ambiguous. An unwrapped radius map (ray-cast from outside, theta vs Z, coloured by radius; `radius_map_aligned.png`) made it obvious. **Rule: for any cylinder-ish mesh edit, make the unwrapped radius map first; it shows cells, slots, clips and threads at a glance.**
4. **Bone cutters were never moved to their row height**: a z variable existed but was never used, so every bone was cut at z=0 into the thread. Caught only by rendering from below. **Rule: render every side, including underneath, before trusting an edit.**
5. **Bone pitch of 24° at r=24 is a 10 mm arc, less than the 13 mm bone**, so bones merged into slots. Check spacing in mm, not degrees.

## What worked
- An acceptance gate (`gate.py`) compares the edit to the original in the upright frame: panels gone, bones through, slot IoU, thread and lid unchanged, loop present, watertight. Proven both ways: the broken v2 fails 5 of 7 checks and v3 passes all 7.
- A gate measurement bug of its own: a bone on the back wall lined up with the slot, so rays passed straight through and slot IoU dropped to 0.857. Fixed by treating "ray passes through" as open. Always inspect the pixels that differ before blaming the model.
- Filling panels to the measured skin *minimum* (25.92) means the fill is never proud of the facets. The leftover step is 0.07 mm, under half a 0.2 mm layer.
- Loop design: 3.6 mm tangential bar (passes the 4.54 mm gate), 45° underside, teardrop hole with the apex up, embedded 1 mm into the 3 mm wall. Printable without support.

## Phone 3D viewer (Artifact)
- Recipe that works under the Artifact CSP: an importmap pointing `three` and `three/addons/` at jsdelivr `three@0.160.0`, `OrbitControls` for touch, and geometry embedded as base64 Float32/Uint32 arrays (no fetch, no loader). 79k triangles → 1.9 MB page. `camera.up = (0,0,1)` keeps the print frame, so there's no axis remap and no mirror risk.
- The headless test (`viewer.test.mjs`: CDP touch drag, pinch, cancelled touch, view buttons, 0x0 iframe start, over http) caught two bugs a screenshot never would:
  1. Lifting two fingers after a pinch fired two touch `pointerup` events within 320 ms, which counted as a double-tap and reset the zoom. A double tap must mean two single-finger taps that moved less than 10 px and lasted under 250 ms.
  2. A `change` listener marked the view "user zoomed" while the iframe was still 0x0 (the camera sat at its default spot before any fit), so the model was never framed. Only count real gestures (`end`), and only after the first fit.
- Also: no `<meta charset>` meant · × ³ rendered as mojibake over plain http. Use HTML entities, and keep the page ASCII-only.
- Pixel coverage stats matched exactly between two different views. That was a coincidence of the same silhouette, but it was only resolved by looking at both screenshots. Never trust a pixel metric without viewing the image once.
- Not verified: the live Artifact host itself (it needs claude.ai auth). Tested locally over http with the same CDN URLs.

## Tooling notes
- f3d `--camera-direction` is the direction the camera LOOKS. To face a feature at angle θ, use (-cos θ, -sin θ, …).
- f3d with `--up=+Z` and a straight-down camera renders blank. Use `--up=+Y` for top and bottom views (fixed in model-forge v2 render.sh).
- `verify_model.py --bodies N` is needed when text is separate shells (4 letters + 1 body here).
