# TweakMyPart: mechanical gates — prove the parts fit and work before "ready" (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/mechanical-gates`, cut from `origin/master` (≥ 14bcde7). Real `node_modules` (check `[ -L node_modules ]`). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Run `python3 /root/.claude/scripts/surface-sweep.py run_all gates.py fit.py features.py assembly.json checks.json verify_model slice_gate --out spec/surfaces.md` and account for every hit.

## Why (James, 21 Sep 17:45)
"Does this check the piece, to make sure threads are going the right way and mechanics are working, like the skill usually does by running tests?" Today the host gates are: watertight + printability (`verify_model.py`), slice (`slice_gate.py`), lettering (`text_check`), and a vision judge comparing the render to the request. Nothing on the host checks that two parts FIT (clearance / interference), that a rod passes through the hole meant for it, or that a thread's pitch, handedness and clearance match between the parts. The model-forge skill has `fit.py` (min gap / interference between two parts in one frame) and `features.py` (hole geometry vs intended sizes) but nothing forces the sandbox to run them, and the host never re-runs them.

## 1. The sandbox declares the mechanics — `worker/job/system_prompt.md`, `worker/job/run_job.py`
New deliverable `/job/out/checks.json`, written with `parts.json` (and required whenever there are 2+ parts or any moving/mating feature):
```json
{ "mates": [ { "a": "rod", "b": "wall-clip", "kind": "loose|snug|press|thread", "min_gap_mm": 0.3, "note": "rod through the clip eyelet" } ],
  "threads": [ { "male": "rod", "female": "sleeve", "pitch_mm": 3.0, "starts": 2, "hand": "right", "major_mm": 8.0, "clearance_mm": 0.4 } ],
  "holes": [ { "part": "wall-clip", "expect": "holes.json" } ],
  "motion": [ { "moving": "rod", "in": "sleeve", "axis": [0,0,1], "travel_mm": 18, "note": "turning the sleeve draws the clips in" } ] }
```
Prompt rules: name every mating pair and every thread; `min_gap_mm` from the fit type (loose 0.3–0.5, snug 0.15–0.25, press ≤ 0.1, thread = clearance); the sandbox runs `fit.py` itself on each mate before finishing and fixes interference; state handedness explicitly and make both parts of a thread pair use the same pitch/starts/hand. `parse_checks` in `run_job.py` validates names against parts.json and numbers finite/positive; a missing file with 2+ parts is a soft failure logged "No mechanics declared" (the design still ships — see gate 2 for what blocks).

## 2. The host re-runs the mechanics — `worker/gates.py` (`run_all`), `worker/mechanics.py` (new)
Using `assembly.json` placements (already produced): for each mate, place both parts in the assembly frame and run `fit.py` (through the model-forge venv subprocess like `assembly.py` does): **INTERFERE → gate fails** (log "`rod` and `wall-clip` overlap by N mm³ — sending it back"), CLEARANCE below `min_gap_mm` → fail, otherwise log "`rod` fits `wall-clip`: gap 0.32 mm". For each thread pair: check both parts' declared pitch/starts/hand match (a mismatch fails), and run `fit.py` on the pair with the thread clearance. For `holes`, run `features.py --expect`. For `motion`: translate the moving part along the axis over `travel_mm` in 4 steps and run `fit.py` at each — any interference fails ("`rod` jams in `sleeve` after 9 mm"). A failed mechanics gate is a normal gate failure: the design job gets its repair turn as today (the failure text is fed back) and the customer sees the log line.
- Mechanics lines go to the log with the other gate lines (customer-facing wording, ≤ 100 chars).
- `designs.get` exposes `mechanics: [{ text, ok }]` from the job result so the ready page can show "Checked: rod fits the clip (0.3 mm gap) · thread pitch matches · slides 18 mm free" under the price card (`components/PartDownloads.tsx` or the ready side panel — one small list, no new card). Legacy designs: nothing shown.

## 3. Proof
- Worker pytest: `parse_checks` valid/invalid/missing; `mechanics.py` with two small 3MF fixtures (a peg and a plate with a hole): loose fit passes with the gap reported; an oversized peg INTERFERES and fails; pitch mismatch fails; motion sweep catches a jam (fixture with a stop). Sabotage: shrink `min_gap_mm` → passes; grow the peg by 1 mm → fails.
- Convex: `reportResult` accepts `mechanics`; `designs.get` returns it; ready page renders the list (test).
- Sandbox run (report cost/time): the fixture "two clips joined by a threaded rod" request through `printtweak-job:latest` with the new prompt + run_job mounted — does the model write `checks.json` with the thread pair and mates? 2 runs; paste the files in the report.
- `run-limited npx vitest run`, worker pytest, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, anything not verified; prompt + run_job change (image rebuild), gates/worker change (worker restart), Convex change (deploy). No new dependencies (use the model-forge venv subprocess as `assembly.py` does). Do not weaken any existing gate.
