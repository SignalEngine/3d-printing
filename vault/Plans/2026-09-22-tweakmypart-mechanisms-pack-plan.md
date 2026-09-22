# TweakMyPart: mechanisms pack — gears, hinges, snap fits, bearings, strength (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/mechanisms-pack`, cut from `origin/master` (≥ 227c4f1). The model-forge skill changes go in the SECOND worktree `/root/wt-3dp-mech` (repo `3d-printing`, branch `build/mechanisms-pack`, path `skills/model-forge/`); never edit `/root/3d-printing` itself. The job image copies the skill in at build time. Never touch `/root/printtweak`, `/root/printtweak-staging`, the services, Convex env, `/etc/printtweak/*`, `printtweak-job:latest` or `:staging`. `run-limited` for heavy commands. Real `node_modules` check (`[ -L node_modules ]`); `next build --webpack`, never a Turbopack root. `GATES.md` before code (`/unlazy tree N`), committed last. Surface sweep: `python3 /root/.claude/scripts/surface-sweep.py checks.json parse_checks LIMITS mechanics motion gears loads --out spec/surfaces.md`, account for every hit. No self-review, merge or push.

## Why (James, 22 Sep 18:00)
"I have an idea for a relatively complex build to test the engineering skill set. Have we loaded it with engineering tactics — stress testing, 3D print tactics, bindings, how to make gearing?" Today the sandbox has good print rules (`references/fdm-design-rules.md`) and real host gates (watertight, slice, mate clearances, hole sizes, motion collision sweep, printed threads ≥ M8), but gears are a 3-line snippet, nothing checks that gears mesh, nothing calculates strength, and hinges / snap fits / print-in-place / bearings / springs / cams have no rules. James chose: build this pack before his test.

## 1. Reference — `skills/model-forge/references/mechanisms.md` (new) + pointer in `SKILL.md`
**The BRAIN writes this file** from a research pass (James, 18:05: "research 3D engineering tactics — a gyroscope, print-in-place things that seem impossible but work"). Builder: create only a stub with the headings below and the SKILL.md pointer; do not invent the numbers. The gates in §2–§3 must not depend on its text. The numbers below are the starting draft the research will confirm or correct:
- **Gears (FDM, 0.4 nozzle):** module ≥ 1.0 (1.5 preferred for load); ≥ 13 teeth at 20° pressure angle (undercut below); both gears share module + pressure angle; centre distance = m·(z1+z2)/2 + 0.15–0.25 mm backlash; face width 6–10 × module; print flat; herringbone/helical for quiet or high-load (still printable flat); shaft bore as a D-flat or hex, not round-only; hub ≥ 2 mm wall; ratio from tooth counts, state it. Racks: same module, pitch line offset. Use `bd_warehouse.gear` (SpurGear etc.) and say how it was checked (see §2).
- **Hinges:** pin hinge 0.3–0.4 mm radial clearance; print-in-place hinge 0.4–0.5 mm gap with cone knuckles, ≥ 0.2 mm Z gap; living hinges only in PETG/PP, never PLA (0.3–0.5 mm thick).
- **Snap fits:** cantilever strain ε = 1.5·y·t / L² (y deflection, t root thickness, L length); allowable PLA ≈ 2% one-time / 1% repeated, PETG ≈ 4% / 2% (rule of thumb); root fillet; print the beam flat (layer lines along it).
- **Press fits and bearings:** press fit −0.1 to −0.15 mm on diameter; 608 bearing (22 × 8 × 7) pocket 22.1–22.15 mm, 7.2 mm deep, lead-in chamfer; printed bushing 0.2–0.3 mm clearance; shafts: D-flat or 8 mm steel rod.
- **Springs / flexures, cams:** printed flexures only in PETG, keep strain < 2%; cam pressure angle < 30°.
- **Print-in-place:** ≥ 0.3 mm XY gap and ≥ 0.2 mm Z gap between moving parts; no support inside the gap.

## 2. Gear mesh gate — `checks.json` `gears`, host `worker/mechanics.py`, sandbox `worker/job/run_job.py parse_checks`
- New `checks.json` key `gears: [{"a","b","module","teeth_a","teeth_b","note"?}]` (limit 4). Validated on both sides like the other keys (names exist, numbers finite: module 0.3–10, teeth 6–300).
- Host re-checks from the PLACED parts (assembly.json): (1) the two gears' axes are parallel and the measured centre distance is within [m·(z1+z2)/2 + 0.05, + 0.5] mm; (2) module ≥ 0.8 and teeth ≥ 12, else fail with a customer line; (3) a coupled rotation sweep: rotate `a` by θ and `b` by −θ·z_a/z_b about their own axes over at least one tooth pitch in 8 steps, and fail if they intersect at any step (binding) or the minimum gap exceeds 0.6 mm (not meshing). Reuse the existing motion-sweep / fit.py distance code; no new dependency.
- Customer line on pass, e.g. "Gears mesh: 3:1, 0.2 mm backlash, turns freely"; on fail the repair prompt says which check failed.
- Prompt rule: any meshing gears → declare them in `gears` (REQUIRED, like mates).

## 3. Strength check — `checks.json` `loads`, `skills/model-forge/scripts/strength.py` (new, stdlib only)
- `loads: [{"part","feature":"cantilever"|"beam","length_mm","thickness_mm","width_mm","deflection_mm"?|"force_n"?,"material":"PLA"|"PETG","layers":"along"|"across","repeated":bool,"note"?}]` (limit 6).
- `strength.py`: rectangular-section hand calc — deflection given → strain (snap formula); force given → bending stress σ = 6·F·L/(w·t²) vs strength (PLA 50 MPa, PETG 45 MPa; × 0.5 when layers are "across"; safety factor 2). Pass/fail with the numbers. `__main__` self-check with asserts, plus pytest.
- Host runs it on the declared rows and also measures the part's bounding size so a declared thickness larger than the part itself fails ("declared 4 mm but the part is 2.1 mm thick" style check via features.py or bounds — keep it simple and state its ceiling in a `ponytail:` comment).
- Customer line: "Clip bends 1.1% (PLA limit 2%)" / "Arm holds 20 N with 2.4× margin". It is a hand calc, not FEA — say "estimated".
- Prompt rule: any snap fit, clip, cantilever, bracket arm or hook → declare it in `loads`.

## 4. Prompt — `worker/job/system_prompt.md`
One short block: for gears, hinges, snaps, bearings, springs, cams or print-in-place read `references/mechanisms.md` first; declare `gears` and `loads` in checks.json. Keep the "ask before changing" rule intact.

## Tests and proof
- pytest: parse_checks both sides accept/reject `gears`/`loads`; centre-distance window; coupled sweep on a synthetic pair (two bd_warehouse spur gears at the right distance pass; 1 mm too close fails as binding; 1 mm too far fails as not meshing — build the fixtures in the model-forge venv like the existing mechanics tests); strength maths (a known cantilever: PLA, L 20, t 1.5, y 1 → ε = 0.56%); a declared-too-thick row fails.
- Mutation: break the centre-distance check and show the binding test goes red.
- `run-limited npx vitest run`, worker pytest, model-forge tests, `npx tsc --noEmit`, `run-limited npx next build --webpack` green.
- Sandbox proof is the BRAIN's job on staging (`printtweak-job:staging` built from this branch + the skill branch): fixtures "a 3:1 spur gear pair on 8 mm shafts in a small frame, hand crank" and "a pill box with a snap-fit lid". Leave both request JSONs in `worker/tests/bench/requests/` (gear-pair.json, snap-lid.json).

## Hard rules
Report RED/GREEN, file:line, anything not verified. No new dependencies. Worker/prompt changes need an image rebuild + worker restart (brain does it). Do not change prices, payments or the brief prompt.
