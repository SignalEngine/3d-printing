# Continuation: fabric first-layer relief (the previous builder stalled; its work is UNCOMMITTED in this worktree)

Worktree `/root/wt-3dp-foot` (branch `build/fabric-first-layer`). Original plan:
`/root/3d-printing/vault/Plans/2026-09-26-fabric-first-layer-plan.md`. It adds bed contact ≥ 25 mm² per tile for BOTH
tiles; the drape shapes didn't stick to the bed.

State left by the previous builder (uncommitted):
- FOOT_IN 0.3 / FOOT_H 0.4 relief;
- bed-level gap test + bed-contact floor test (both green);
- the drape contact give-back;
- sabotages done;
- plate re-sliced: 4.36 h, 36.9 g.
Two tests are RED: `Prints_drape` and `Prints_square` `test_slices_with_no_supports_and_verifies`. verify_model says
"thinner than 0.8 mm": the square plate above the 0.4 ledge is 0.8 mm, and drape has a 0.44 mm ledge over the ring
bottom plus 0.6 mm feet.

## Brain decision
1. Thicken `PLATE_T` from 1.2 to 1.4 mm for BOTH tiles.
2. Do NOT loosen verify_model or relax that test.
3. If DRAPE still has thin-feature samples, fix the geometry: feet ≥ 0.8 mm wide, and every ledge ≥ 0.8 mm thick.
4. Keep ALL other tests green: gap, captive, drape ±30° fold, bodies, bed contact ≥ 25 mm², bed-level gap, `--check`,
   slices with no supports.

## Then
- Full suite: `/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests` (capture the exit code).
- Regenerate `models/fabric-tests/*`, `models/fabric-examples/*` and the print plate; re-slice the plate (report
  hours/grams).
- Re-run both sabotages (FOOT_IN = 0 → the bed-gap test red; drop the contact give-back → the contact test red).
  Restore, then `rg SABOTAGE` returns nothing.
- Commit with explicit paths (`.venv` is a symlink; never `git add -A`). Don't push.
