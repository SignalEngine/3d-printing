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
