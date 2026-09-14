# Gates: model-forge quote gate + text OCR check

OWNS: skills/model-forge/scripts/slice_gate.py, skills/model-forge/scripts/text_check.py, skills/model-forge/tests/run_gates.sh, skills/model-forge/SKILL.md

Scope: extend slice_gate.py with a cost/quote block and optional limit flags; add text_check.py (OCR-verify ordered text via cross-section + tesseract); wire both into run_gates.sh as gate_quote / gate_text; document both in SKILL.md. Per vault/Plans/2026-09-13-model-forge-quote-text-gates.md.

- [x] G1: quote gate prints cost lines and PASSes with no flags (existing behaviour preserved)
  CHECK: bash skills/model-forge/tests/run_gates.sh quote
  EXPECT: QUOTE_GATE_OK
  EVIDENCE: manual; RED before implementation (`unknown gate: quote`, exit 2); GREEN after: `ok: cube, no flags (exit 0)` with `print hours:`/`cost floor:` lines present, full `run_gates.sh quote` output ends `QUOTE_GATE_OK`.

- [x] G2: quote gate FAILs when --max-hours is exceeded (trophy, 15h+)
  CHECK: bash skills/model-forge/tests/run_gates.sh quote
  EXPECT: QUOTE_GATE_OK
  EVIDENCE: manual; trophy.3mf --max-hours 6 -> `print hours: 15.25`, `QUOTE FAIL: print hours 15.25 > --max-hours 6.0`, `RESULT: FAIL`, exit 1. Gate assertion `ok: trophy over max-hours (exit 1)`.

- [x] G3: quote gate PASSes when under both --max-hours and --max-grams (pillbox assembly)
  CHECK: bash skills/model-forge/tests/run_gates.sh quote
  EXPECT: QUOTE_GATE_OK
  EVIDENCE: manual; assembly.3mf --max-hours 6 --max-grams 60 -> print hours 2.86, material 24.2g, RESULT: PASS, exit 0. Gate assertion `ok: pillbox under limits (exit 0)`.

- [x] G4: quote gate computes price-per-printer-hour and PASSes/FAILs against --min-gbp-per-hour correctly (knob passes, trophy fails at --price 25)
  CHECK: bash skills/model-forge/tests/run_gates.sh quote
  EXPECT: QUOTE_GATE_OK
  EVIDENCE: manual; knob.3mf --price 5 -> price per printer-hour £13.50, RESULT: PASS. trophy.3mf --price 25 -> £1.20/hr, QUOTE FAIL, RESULT: FAIL, exit 1.

- [x] G5: text_check.py reads raised text off a build123d plate via cross-section OCR and PASSes on a correct --expect
  CHECK: bash skills/model-forge/tests/run_gates.sh text
  EXPECT: TEXT_GATE_OK
  EVIDENCE: manual; RED before implementation (script did not exist / `unknown gate: text`, exit 2). GREEN: HELLO plate --expect HELLO --axis z -> `best read: HELLO (axis z, offset 3.9mm, rotation 0)`, RESULT: PASS, exit 0.

- [x] G6: text_check.py FAILs on a wrong --expect string (negative control) and on overlapping text at the same spot
  CHECK: bash skills/model-forge/tests/run_gates.sh text
  EXPECT: TEXT_GATE_OK
  EVIDENCE: manual; HELLO plate --expect WORLD -> RESULT: FAIL, exit 1 (closest reads listed, none contain WORLD). HELLO+WORLD extruded at the same location --expect HELLO -> illegible OCR output, RESULT: FAIL, exit 1.

- [x] G7: text_check.py reads the real trophy.stl fixture correctly (CONGRATULATION passes, CONGRATULATIONS fails)
  CHECK: bash skills/model-forge/tests/run_gates.sh text
  EXPECT: TEXT_GATE_OK
  EVIDENCE: manual; trophy.stl --expect CONGRATULATION -> best read matches (axis y, rotation 270 mirrored), RESULT: PASS, exit 0. trophy.stl --expect CONGRATULATIONS -> RESULT: FAIL, exit 1 (no read contains the extra S).

- [x] G8: full gate runner still passes end to end with the two new gates wired in, nothing previously green regresses
  CHECK: bash skills/model-forge/tests/run_gates.sh all
  EXPECT: ALL_GATES_OK
  EVIDENCE: manual; full run prints CHECKER_GATE_OK, RENDER_GATE_OK, FEATURES_GATE_OK, FIT_GATE_OK, SLICE_GATE_OK, QUOTE_GATE_OK, TEXT_GATE_OK, DOCS_GATE_OK, ALL_GATES_OK, exit 0. Run twice (once before SKILL.md edit, once after) — same result both times.

- [x] G9: SKILL.md documents both commands and the "never judge text from the iso view" rule
  CHECK: bash -c 'grep -q "text_check.py" skills/model-forge/SKILL.md && grep -q "slice_gate.py" skills/model-forge/SKILL.md && grep -qi "iso view" skills/model-forge/SKILL.md && echo SKILL_DOC_OK'
  EXPECT: SKILL_DOC_OK
  EVIDENCE: manual; command run directly, printed `SKILL_DOC_OK`, exit 0.

# Gates: model-forge issue #2 fixes + needs-supports check

OWNS: skills/model-forge/scripts/features.py, skills/model-forge/scripts/fit.py, skills/model-forge/scripts/verify_model.py, skills/model-forge/scripts/slice_gate.py, skills/model-forge/tests/run_gates.sh, skills/model-forge/SKILL.md

Scope: fix issue #2 items 1-3 (thin-floor blind hole misread as through, corner/edge contact misread as gap, first-fit hole matching order bug), add a "needs supports" WARN to verify_model.py, add `--supports none|tree|normal` to slice_gate.py. Per vault/Plans/2026-09-14-model-forge-issue-2.md.

- [x] F1: features.py probes 0.02mm (not 0.2mm) past each cylinder end, so a 0.1mm blind-hole floor reads as blind, not through
  CHECK: bash skills/model-forge/tests/run_gates.sh features
  EXPECT: FEATURES_GATE_OK
  EVIDENCE: manual; RED before fix: Box(20,20,10) with Ø4 hole 9.9mm deep from +Z (0.1mm floor) → `face=through Z`, gate assertion `FAIL: expected exit 0, got 1`. GREEN after: `face=+Z`, `ok: 0.1mm-floor blind hole classifies as +Z (exit 0)`. Existing through-hole and plate+boss cases (`hole through Z despite boss`) still pass unchanged.

- [x] F2: fit.py distance queries use mesh vertices ∪ surface samples (both directions, fixed RNG seed), so corner/edge-only contact reads a real near-zero gap, repeatably
  CHECK: bash skills/model-forge/tests/run_gates.sh fit
  EXPECT: FIT_GATE_OK
  EVIDENCE: manual; RED before fix: two 20x20x10 boxes touching at one corner → `minimum gap` varied 0.1997/0.3028/0.3516mm across 3 runs (matches issue #2's reported 0.16-0.26mm, changing each run). GREEN after: `corner-touch gaps over 3 runs: [0.0, 0.0, 0.0]`. Crossed-bars (gap 0.0, area 4.54mm²) and 0.5mm-separated-bars (gap 0.5, area 0.0) cases unchanged and still pass.

- [x] F3: features.py --expect matching sorts expected and found diameters within each face group before matching, instead of list order
  CHECK: bash skills/model-forge/tests/run_gates.sh features
  EXPECT: FEATURES_GATE_OK
  EVIDENCE: manual; RED before fix: found diameters in BREP order [4.1, 3.9] on face +Z, expected [4.0, 4.2] tol 0.15 → `FAIL: expected exit 0, got 1` (greedy list-order match paired 4.0→4.1, then 4.2 had nothing left within tolerance). GREEN after: `ok: sorted-diameter first-fit matches 3.9->4.0 and 4.1->4.2 (exit 0)`. A genuinely missing third expected hole (Ø5.0) still FAILs: `ok: genuinely missing hole still FAILs (exit 1)`.

- [x] F4: verify_model.py WARNs "needs supports" when the part, sliced in its current orientation (section_multiplane, dz=0.4), has a layer with >50mm² unsupported by the buffered layer below (50° self-supporting angle), or a mid-air island >2mm² with nothing below it
  CHECK: bash skills/model-forge/tests/run_gates.sh supports
  EXPECT: SUPPORTS_GATE_OK
  EVIDENCE: manual; RED before implementation: closed-top tube (r_out 26, r_in 23, h 60, 3mm roof) → no "needs supports" text anywhere in verify_model.py output (`FAIL: expected 'needs supports' WARN`). GREEN after: `needs supports — largest unsupported area 1593mm^2 at z=27.2` (roof spans z 27-30) — WARN only, `RESULT: PASS`, exit 0 (supports are a valid choice, not a hard fail). Same tube with no roof (open both ends): no "needs supports" WARN, `ok: open tube PASS (exit 0)`.

- [x] F5: slice_gate.py takes --supports none|tree|normal (default none), overrides enable_support/support_type on the OrcaSlicer process settings, prints whether supports were on, and reports the filament delta against a no-support baseline slice when available
  CHECK: bash skills/model-forge/tests/run_gates.sh slice_supports
  EXPECT: SLICE_SUPPORTS_GATE_OK
  EVIDENCE: manual; RED before implementation: `--supports tree` → argparse error, unrecognised argument, exit 2. GREEN after: closed-top tube with `--supports tree` → `supports: tree`, `filament delta vs no supports: +8.3g`, `RESULT: PASS`, exit 0.

- [x] F6: full gate runner passes end to end with the new gates wired in, nothing previously green regresses; run twice for repeatability
  CHECK: bash skills/model-forge/tests/run_gates.sh all
  EXPECT: ALL_GATES_OK
  EVIDENCE: manual; two consecutive full runs both print CHECKER_GATE_OK, RENDER_GATE_OK, FEATURES_GATE_OK, FIT_GATE_OK, SLICE_GATE_OK, QUOTE_GATE_OK, TEXT_GATE_OK, SUPPORTS_GATE_OK, SLICE_SUPPORTS_GATE_OK, DOCS_GATE_OK, ALL_GATES_OK, exit 0.
