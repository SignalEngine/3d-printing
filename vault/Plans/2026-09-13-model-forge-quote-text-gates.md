# model-forge: quote gate + text check

James picked this on 2026-09-13 after the round 4 test ran model-forge on 5 real r/3Dprintmything requests ([[2026-09-13-3d-print-business-ideas]]). Two real gaps:

1. **Nothing checks whether a model is worth printing.** The trophy passed every gate but needs 15h15 and 122 g; the rack bracket 9h24. A service must see print time, material and cost before quoting.
2. **Nothing mechanically checks that text says what was ordered.** A reviewer (the brain) misread the trophy from the perspective iso render. A spike proved a cross-section plus tesseract reads text reliably: a "HELLO" plate reads `HELLO`, the trophy reads `CONG RATU LAT ION` once rotated 270° and mirrored.

Out of scope: an independent render-review step (not demonstrated as needed by this test), photo input, any web app.

## Build

### 1. Quote gate: extend `scripts/slice_gate.py` (no new file)

After a successful slice, always print a cost block, and fail only when a limit flag is given and exceeded.

- Parse the estimated time into hours. Formats seen: `21m 38s`, `2h 51m 3s`, `15h 14m 45s`; allow `1d 2h 3m`.
- Grams: use `filament used [g]`; if absent, `cm3 × 1.24` (PLA density). Mark it `ponytail:` (PETG 1.27, ABS 1.04).
- New flags, all optional:
  - `--gbp-per-kg` (default 18)
  - `--gbp-per-hour` machine cost (default 0.30, electricity + wear; label it an estimate)
  - `--max-hours H`, `--max-grams G`
  - `--price P` (proposed sale price, £) with `--min-gbp-per-hour` (default 10)
- Output lines (exact prefixes, tests grep them):
  - `print hours: 2.85`
  - `material: 24.2g = £0.44`
  - `machine: £0.86`
  - `cost floor: £1.30`
  - with `--price`: `price per printer-hour: £8.77` (price minus cost floor, divided by hours)
- Any exceeded limit prints `QUOTE FAIL: <reason>` for each and ends with `RESULT: FAIL`, exit 1. Otherwise `RESULT: PASS`, exit 0.
- No flags → behaviour unchanged apart from the extra info lines (existing gate_slice tests must still pass).

### 2. Text check: new `scripts/text_check.py`

`text_check.py <model.stl|.3mf|.step> --expect "TEXT" [--axis x|y|z] [--steps 12]`

- Load the mesh (reuse slice_gate's `load_any` pattern; copy it, don't import across scripts).
- For each axis to scan (the given one, or all three if omitted), take `--steps` evenly spaced cross-section planes strictly inside the bounds. Use `mesh.section_multiplane` (the vault lessons file shows `section()` can return identical data at every height on some meshes).
- Draw each section's `polygons_full` filled black on white (holes white) with matplotlib, `bbox_inches="tight"`, padding 0.3, dpi 150.
- OCR each image in 8 orientations (rotate 0/90/180/270, each also mirrored) with the `tesseract` CLI, `--psm 6`. No pytesseract dependency.
- Normalise both expected and read text: uppercase, keep A-Z and 0-9 only. PASS if the normalised expected text is a substring of any normalised read.
- Output: `best read: <text> (axis y, offset -8.0mm, rotation 270 mirrored)`, then `RESULT: PASS` exit 0, or `RESULT: FAIL` exit 1 listing the 3 closest reads. Missing tesseract → `RESULT: ERROR` exit 2.
- Keep it under ~120 lines. No abstractions used once.

### 3. SKILL.md

- Step 2: add both commands with one-line purpose each, e.g.
  `python3 scripts/slice_gate.py out.3mf --max-hours 6 --price 25` and `python3 scripts/text_check.py out.3mf --expect "CONGRATULATION"`.
- Rule: any part carrying ordered text must pass `text_check.py`.
- Rule: judge text and legibility from the front/orthographic view or a cross-section, never the iso view (the iso view misled a real review on 2026-09-13).
- Step 3 final reply: include print hours, grams and cost floor from the slice gate.
- Keep SKILL.md tight: add lines, don't add sections.

## Gates (each must fail RED first)

Add `gate_quote` and `gate_text` to `tests/run_gates.sh`, wire both into the `case` block and `all`. Fixtures:

| Gate | Input | Expected |
|---|---|---|
| quote | cube (existing fixture) no flags | exit 0, `print hours:` and `cost floor:` lines present |
| quote | `models/rq-trophy/trophy.3mf --max-hours 6` | exit 1, `QUOTE FAIL`, `RESULT: FAIL` |
| quote | `models/rq-pillbox/assembly.3mf --max-hours 6 --max-grams 60` | exit 0 |
| quote | `models/rq-knob/knob.3mf --price 5` | exit 0 (≈£13/printer-hour) |
| quote | `models/rq-trophy/trophy.3mf --price 25` | exit 1 (under £10/printer-hour) |
| text | build123d plate with raised "HELLO", `--expect HELLO` | exit 0 |
| text | same plate, `--expect WORLD` | exit 1 |
| text | plate with "HELLO" and "WORLD" extruded on top of each other at the same spot, `--expect HELLO` | exit 1 (overlapping text must not pass) |
| text | `models/rq-trophy/trophy.stl --expect CONGRATULATION` | exit 0 |
| text | `models/rq-trophy/trophy.stl --expect CONGRATULATIONS` | exit 1 |
| existing | `run_gates.sh all` | `ALL_GATES_OK`, nothing previously passing now fails |

Show every new gate RED before implementing (script missing / flag unknown is an acceptable RED), then GREEN. Paste both outputs in the report. Fixture paths are relative to the worktree root (`$HERE/../../../models/...`).

## Builder notes (read before coding)

- Work ONLY in the worktree you were given. Skill source: `skills/model-forge/` in that worktree. `~/.claude/skills/model-forge` symlinks to the MAIN checkout; never edit it.
- Python: `/root/3d-printing/.venv/bin/python` (build123d, trimesh, manifold3d, matplotlib, PIL present). `tesseract` 5.3.4 is at `/usr/bin/tesseract`.
- OrcaSlicer is already installed at `/root/3d-printing/orcaslicer/squashfs-root` (slice_gate finds it). Slicing the trophy takes well under the 120 s timeout in practice; if it times out, raise the timeout to 300 and say so.
- Spike code that already worked (section → black-on-white PNG → tesseract) is described above; don't redesign it.
- Before coding, run `/unlazy tree 2 <this plan>` and write `GATES.md` at the worktree root. Commit it LAST.
- stdlib and existing deps first. Mark shortcuts with `ponytail:` comments.
- Do NOT review your own work, merge, or push to master. Commit on the worktree branch and report: gates RED output, gates GREEN output, files changed, anything that blocked.

## Cost

One Sonnet builder session (~1-2 hours), then the brain runs `verify-build`, `/jury` and `review-gate`, and sabotages both new gates once to prove they can fail.
