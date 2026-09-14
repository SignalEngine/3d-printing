# model-forge: fix issue #2 + add a "needs supports" check

Worktree: /root/wt-mf-issue2 (branch fix/model-forge-issue-2, cut from origin/master). Python: /root/3d-printing/.venv/bin/python.
Skill: skills/model-forge/. Gate runner: skills/model-forge/tests/run_gates.sh.

## Rules
- Every new gate case goes RED on the current code BEFORE the fix. Paste that output, then GREEN after.
- `run_gates.sh all` must end ALL_GATES_OK. Update GATES.md LAST (create a fresh section for this build).
- Commit on the branch. Do not push, merge, or review your own work. Minimum code, no new dependencies.
- Use `trimesh.Trimesh.section_multiplane` for layer slicing. `section()` returned identical data at every Z on a real part (vault/Research/2026-09-13-stl-edit-lessons.md).

## F1 features.py: thin-floor blind hole reads as through (issue #2 item 1)
Repro: Box(20,20,10) − Ø4 hole 9.9 mm deep from +Z (0.1 mm floor) → reports `through Z`. The end probe steps 0.2 mm past the hole end, which jumps the floor.
Fix: probe 0.02 mm beyond each cylinder end instead of 0.2.
Gates: 0.1 mm floor → `+Z` (blind). The existing through-hole and plate+boss cases stay `through Z`.

## F2 fit.py: corner/edge contact reads as a gap (issue #2 item 2)
Repro: two boxes (20,20,10), the second translated (20,20,10), touching at one corner. Reported gap 0.16–0.26 mm, changing each run (true 0).
Fix: distance query points = mesh vertices ∪ surface samples, in both directions. Fixed RNG seed so output is repeatable.
Gates: corner-touch → gap ≤ 0.01, identical output over 3 runs. Crossed bars (gap ≤ 0.05, contact 3–5 mm²) and 0.5 mm separated bars (gap 0.45–0.55) still pass.

## F3 features.py: first-fit hole matching (issue #2 item 3)
Repro: found diameters [4.1, 3.9] on one face, expected [4.0, 4.2], tol 0.15 → FAIL, though 3.9→4.0 and 4.1→4.2 is valid.
Fix: within each face group, sort expected and found by diameter and match in order.
Gates: that case → PASS. A genuinely missing hole still FAILs.

## F4 verify_model.py: warn when the part needs supports (NEW, caused a real failed print)
What happened: James's poop bag holder printed thread-end down with no supports and turned to spaghetti. The closed lid is a 46 mm roof over a hollow tube: 1,532 mm² unsupported at z=65.4. The checker's overhang % (12.3% of all surface) and the slice gate (supports off) both passed it.
Fix: slice the mesh in its current orientation at dz=0.4 with section_multiplane. For each layer, unsupported = this layer − (previous layer buffered by dz·tan 50°). Report the largest unsupported area and its z, plus mid-air island starts (polygons with no overlap with the layer below, area > 0.5 mm²). WARN "needs supports" when any layer's unsupported area > 50 mm² or any island > 2 mm², printing the z of each. WARN, not FAIL, because supports are a valid choice.
Gates: closed-top tube (r_out 26, r_in 23, h 60, 3 mm roof), open end down → WARN naming a roof area ≥ 1,000 mm² near the roof z. The same tube with no roof → no supports WARN. Reference numbers: `models/poop-bag-holder/holder_v3.stl` gives ~1,532 mm² at z≈65.
SKILL.md Step 2: a "needs supports" WARN means slice with supports and state the support type in the delivery. Never tell the user "no supports" unless this check is clean.

## F5 slice_gate.py: slice with supports
Add `--supports none|tree|normal` (default none), passed as an OrcaSlicer settings override (enable_support + support_type). Look at how slice_gate already builds its process/filament settings. Print whether supports were on.
Gates: the closed-top tube slices with `--supports tree` (exit 0). Report the filament delta against `none` in the output if Orca provides it, otherwise skip that.
