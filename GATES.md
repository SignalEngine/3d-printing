# GATES — fabric phase 1 (generator + swatch)

Plan: `/root/3d-printing/vault/Plans/2026-09-26-fabric-phase1-plan.md`

## 1. Gaps
CHECK: pytest test_fabric -k gap
EXPECT: every neighbour pair min distance ≥ gap-0.02 at 0.3 and 0.5.
POSITIVE CONTROL: geometry gap 0 → red.

## 2. Captive
CHECK: pytest test_fabric -k captive
EXPECT: 2 mm shift ±x ±y +z → intersection > 0.01 mm³ for every pair.
POSITIVE CONTROL: lip height 0 → red.

## 3. Bodies / outline / bed / slicing
CHECK: pytest test_fabric
EXPECT: objects == tiles, each 1 watertight body; circle fill connected; rect 40x40 → 16; 300x100 refused; slice_gate --supports none PASS.

## 4. Whole suite
CHECK: pytest skills/model-forge/tests

## MANUAL (James)
Print models/fabric-swatch/swatch.3mf; pick the gap that flexes freely without fusing → becomes the default.

## RESULTS (brain, 26 Sep)
- model-forge suite 32 passed (brain run). Builder sabotage (lip 0 → captive red; gap 0 → gap red), markers clean.
- review-gate: PASS (formatting glitch → gate said BLOCK; verdict text is PASS, no P1/P2). P3s fixed in 308e0cf
  (gap > 0.6 refused; empty text refused). Jury GLM: clean.
- Flex/drape NOT proven: flat plates hinged by edge links; James's swatch print decides.
- MANUAL: pending James's print of models/fabric-swatch/swatch.3mf.
