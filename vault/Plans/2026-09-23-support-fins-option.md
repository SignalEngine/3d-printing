# Plan: built-in support fins as a download option (TweakMyPart)

James, 23 Sep: "add support-fins as an option" → chose **full fins option now** (before auto-orient).
Source: https://github.com/gittrahan/support-fins (MIT, pinned `8d3bd0e`), live at printfins.com.
Builds on branch `build/orient-strength` (needs `supportGrams` per part from stage 1).

## What the customer gets
A part whose slice needs supports (`supportGrams > 0`) gets a second download: **"with built-in fins — print with
supports OFF"**, beside the normal 3MF/STEP. Credit line under it: "Fins by Support Fins (printfins.com)".
Parts that print without supports get no fins download. The fins file is never the default.

## Verified by the brain (23 Sep)
- The engine is 5 pure-JS modules (`web/overhangs.js planes.js fins.js prop.js inside.js`): no DOM, no three.js.
  His `prototype/verify_fins.js` runs them headless in Deno (installed: `/root/.deno/bin/deno`).
- T-shape test (60 mm bar on a 10 mm post): `buildFins(topo, analyze(topo,45,rot), rot, {mode:'stabilize', bedPad:true})`
  → 1 breakaway wall, 0 unserved overhangs, 79 ms, output watertight (4 bodies).
- **Open risk:** Orca's auto-support detection on the finned T still reported 149 support blocks (+2.3 g),
  same as unfinned. Orca auto-supports flag bridged spans the fin is meant to carry, so "Orca still wants
  supports" is NOT the right oracle. His oracle is `prototype/check_gcode.py`: slice with supports OFF and confirm
  the fin walls appear in the toolpaths. Only a real print on James's A1 proves the part comes out right.

## Build
1. Vendor the 5 modules into `worker/fins/engine/` unmodified + his LICENSE + a README line with the pinned SHA.
   `worker/fins/run_fins.js`: Deno script, args `<in.stl> <out.stl>`, tilt 0 (parts print as modelled; stage 2 will
   pass a rotation), mode `stabilize`, `bedPad: true`. Writes part+fins STL; prints one JSON line
   `{fins, unserved, seating}`. Run with `deno run --allow-read=<dir> --allow-write=<dir>` only (no net, no env),
   timeout 60 s.
2. Host step in `worker/worker.py` `_ship` (after the winner is chosen): for each part with `supportGrams > 0`:
   STL of the part (export from its 3MF/STEP with the existing trimesh tooling) → run_fins → accept only if
   `unserved == 0`, seating is not `point`, output watertight, and `slice_gate.py <finned> --supports none` slices;
   plus port `check_gcode.py`'s test (fin walls present in the gcode). Any failure = no fins download for that part,
   never a job failure. Upload as `finsStl`.
3. Convex: `files.parts[].finsStl: v.optional(v.id("_storage"))` in schema + reportResult validator; `designs.get`
   (partDownloads) returns its URL. `components/PartDownloads.tsx`: when present, one extra link
   "With built-in fins (supports off)" + the credit line. No other UI change.
4. Mechanics line for that part becomes "`<part>` needs tree supports (about N g) — or use the built-in fins download".

## Tests
- run_fins on a fixture T-shape → unserved 0, watertight output; on a plain block → no overhangs, no fins file.
- `_ship`: part with supportGrams>0 and a stubbed passing fins run → `finsStl` uploaded; failing fins run → no
  finsStl, job still ready; supportGrams 0 → fins never run.
- convex-test: reportResult accepts `finsStl`; designs.get returns its URL.
- PartDownloads renders the fins link only when present.

## Gates
Staging proof on a real design that needs supports (smallest part that exercises it — one bracket with an overhang).
**Manual gate (James):** print one finned part with supports OFF on the A1, snap the fin off, judge the surface.
