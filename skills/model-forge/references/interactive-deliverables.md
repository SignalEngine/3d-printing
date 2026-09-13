# Interactive / Visual Deliverables (HTML viewers, previews)

Users often can't open STL/3MF/STEP on their phone (verified: Bambu Handy cannot open local 3MF — long-standing open feature request; Android 3MF viewer support is poor). A self-contained HTML three.js viewer solves this. But interactive deliverables have their own failure modes — two shipped broken in practice before this checklist existed.

## Hard rule
**An interactive artifact is unverified until a headless browser has (a) rendered it at the target viewport, (b) had its pixels asserted, and (c) had its INPUT simulated.** "It renders" is not verification — a viewer shipped with perfect rendering and completely dead touch controls.

## Verification loop (Playwright, proven in this environment)
```bash
pip install playwright --break-system-packages -q && playwright install chromium --with-deps
```
```python
b = p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
ctx = b.new_context(viewport={"width":412,"height":915}, has_touch=True)
```
Test matrix, all mandatory for a 3D viewer:
1. **Zero pageerror** at load (catches missing libs instantly).
2. **Pixel assertions** on screenshots — model coverage % of canvas, centroid ≈ (0.5, 0.5), feature-color pixel counts (e.g. "the red name must be visible in the initial view": count red pixels). Do this in portrait AND landscape.
3. **Touch drag** via CDP `Input.dispatchTouchEvent` → assert rotation state changed.
4. **Pinch** (two-point CDP touch) → assert zoom state changed.
5. **Stale-pointer recovery**: touchStart then touchCancel, then a fresh drag must still rotate and tracked-pointer count must be 0.
6. **Mouse path** and **button clicks**.
Expose a test hook in the page: `window.__state = ()=>({az,el,dist,...,pts:pts.size})`.

## Headless-harness gotchas (cost real debugging time)
- **rAF is throttled headless** — animated values lag. Assert synchronous *targets* (e.g. `taz`), not animated positions; a "failed" animation assertion was harness throttling, not a bug.
- **CDP touch latency can exceed 1s** under swiftshader — time-window logic (double-tap) must be tested by dispatching `PointerEvent`s *inside the page* via `evaluate`, not through CDP.
- Screenshot `view` rendering to Claude can fail; pixel analysis with numpy is the fallback ground truth.

## Design rules for phone-delivered viewers
- **Inline every JS library** (fetch three.min.js, embed in a `<script>` tag). A CDN dependency is a blank-screen risk; the headless test itself failed on CDN load. ~600 KB extra is fine.
- **Auto-frame the camera from the computed bounding box** (`1.15 * bounding_radius / tan(min(vfov,hfov)/2)`), never hardcoded distances — a hardcoded camera put the model off-screen on a real phone.
- **Never trust mentally-derived rotation angles.** A flip about X negates z and maps azimuth θ → 180°−θ; the "front/back" buttons shipped swapped because the angle was guessed. Derive it, then *verify empirically* with a feature-color pixel check per view.
- Embed geometry as rounded float arrays + index arrays in JSON (≈180 KB for ~8.5k tris); build `BufferGeometry` manually — no loader dependencies. three.js r128 on cdnjs lacks OrbitControls; write manual controls.
- Robust pointer pattern (all of these existed because their absence broke a real device):
  - `touch-action:none` on canvas PLUS non-passive `touchstart/touchmove` preventDefault
  - `pts.set()` before `setPointerCapture` (wrapped in try/catch)
  - `pointerup`/`pointercancel` listeners on **window**, plus `lostpointercapture` and `blur` → clear all state; a single leaked pointer makes every later one-finger drag register as a pinch = frozen model
  - reset pinch baseline (`lastD=0`) on every pointerdown
  - resize/orientation handling via ResizeObserver + visualViewport; recompute framing on resize but only set `dist=FIT` on first frame (a resize handler that reset zoom made pinch appear broken)
- Quality-of-life: double-tap to reframe, view-preset buttons that lerp the turntable, per-part visibility chips.

## Artifact-iframe rule (learned from a real blank-screen on device)
File:// testing is NOT sufficient. Claude's artifact viewer loads HTML in an iframe whose canvas reports ~0 size at first layout. A one-shot camera-framing latch captured garbage and never recovered -> UI rendered, scene invisible. Mandatory test: host page that embeds the artifact in a 0x0 iframe and only sizes it after ~500ms; assert scene pixel coverage after. Code rules: skip resize() when w or h < 20; recompute framing on every resize until the user zooms; add setTimeout retries (120/400/1000ms).

## Axis-remap trap
Swapping two axes in a Matrix4 (e.g. X_w=mesh.y, Y_w=mesh.x) is a REFLECTION (det=-1): geometry is silently mirrored. Use a proper rotation (e.g. Rz90: X_w=-mesh.y, Y_w=mesh.x), det=+1. Check the determinant of any hand-built transform.

## Proven recipe on this VPS (2026-09-13, poop bag holder)
- Template + test to copy: `models/poop-bag-holder/viewer.template.html` and `viewer.test.mjs` (Playwright from `/root/intentos/node_modules`, served over `python3 -m http.server`, because Chrome refuses a file:// iframe inside a setContent host).
- three@0.160.0 via importmap on jsdelivr + OrbitControls (touch built in) + base64 typed-array geometry. This avoids the r128 "no OrbitControls" gap and needs no fetch, so it's CSP-safe.
- Double-tap to reset must ignore multi-finger lifts, or pinch looks broken. Mark "user zoomed" only on a gesture `end` after the first fit, or a 0x0 iframe start never frames the model.
- ASCII-only page (use HTML entities), and look at every screenshot you compute pixel stats on.

## Mechanism simulators
For moving assemblies, ship an interactive sim: real part meshes + the SAME verified kinematic model used in numeric verification (never a second implementation), a slider/drag for the input DOF, state readout, X-ray toggle (default ON so the mechanism is visible), click/snap feedback. Assert in headless: state machine cycles correctly, moving part's pixels shift between states, schematic added parts (levers etc.) stay geometrically clear of real parts across the full input range. Schematic parts must attach at physically plausible pivots - a floating lever destroys trust in an otherwise-correct sim.

## Orientation assertions (a handle shipped lying sideways along its axle)
Position/rotation-value asserts are NOT enough for placed meshes: a wrong axis mapping passes them while the part lies visibly sideways. For every mesh added to a scene, assert its WORLD bounding-box proportions match intent (e.g. handle: tall in Y, narrow in X; gear: its known width along the axle axis). Expose a __orient() hook returning Box3 sizes per part and check them headlessly. This is pixel-free and catches axis-mapping mistakes that no state assertion will.

Measure orientation boxes at the mechanism's NEUTRAL pose: Box3 of a part inside a rotated
group smears across axes (a 55-degree-thrown handle reads as 'deep in Z' and fails a correct
check). Zero the input DOF before asserting, or measure geometry-local boxes.
