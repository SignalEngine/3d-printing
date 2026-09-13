# model-forge v2: review-gate P2 fixes (before merge)

Worktree: /root/wt-model-forge-v2 (branch build/model-forge-v2, PR #1). Python: /root/3d-printing/.venv/bin/python.
Source: Codex review-gate (VERDICT PASS, no P1). The brain reproduced all 4 findings below on commit c020825.

## Rules
- Every new gate case must go RED on the current code BEFORE the fix. Paste that output, then GREEN after.
- `bash skills/model-forge/tests/run_gates.sh all` must stay ALL_GATES_OK. Update GATES.md LAST.
- Commit on the branch. Do not push, merge, or review your own work. Do not commit 00000.log, node_modules or .review-verdict.md.
- Minimum code. No new dependencies.

## F1 (P2) fit.py: false CLEARANCE on touching faces
Repro: box(20,2,2) and box(2,20,2) translated (0,0,2). True gap 0 mm, contact ~4 mm². Today: CLEARANCE, gap 9.0 mm, contact 0.00. Cause: gap is vertex-to-surface only (fit.py:~74).
Fix: min gap = min over dense surface samples of A→B and B→A (trimesh.sample.sample_surface_even, a few thousand points each). Contact area = A's sample-area fraction within --contact-eps of B.
Gate cases: crossed bars → gap ≤ 0.05 and contact 3–5 mm². Same bars separated by 0.5 mm in Z → CLEARANCE, gap 0.45–0.55, contact 0.

## F2 (P2) features.py: hole openings classified against global bounds
Repro: Box(30,30,10) − Pos(-8,0,0)*Cylinder(2,10); with no boss → "through Z", with Pos(10,0,10)*Box(10,10,10) added → "-Z". Cause: touches_min/max uses part-wide bounds (features.py:~46).
Fix: per hole, probe each end of the cylinder along its axis: a point 0.2 mm beyond each end-circle centre that is NOT inside the solid means that end is open. Both open = through; one open = blind, opening on that side.
Gate case: plate+boss → "through Z" (exit 0 with --expect through Z).

## F3 (P3) features.py: hole centre is a point on the wall
Repro: Box(30,30,10) − Cylinder(2,10) reports centre [-2,0,0]; true [0,0,0]. Also the plate case reports [-10,0,0] for a hole at (-8,0).
Fix: centre = the point on the cylinder axis at the face's mid-height (from the cylinder's axis location, not Face.center()).
Gate case: centred hole centre within 0.01 mm of [0,0,0]; the (-8,0) hole within 0.01 of [-8,0,z].

## F4 (P2) render.sh --section: camera looks at the cut from below
Repro: hollow cube 20 mm outer / 16 mm cavity. The section PNG shows a closed box from below, and the cavity is invisible (render.sh:~88).
Fix: keep the lower half and view the cut face from ABOVE (e.g. --camera-direction=-1,1,-1.2 --up=+Z).
Gate case: render --section for the hollow cube and for a solid 20 mm cube. The two section PNGs must differ in more than 5% of pixels (the cavity is visible). Prove it RED on today's code first.
