# Change engine step 3: build keeps, edits and regenerates the REAL source parts (build plan, 23 Sep 2026)

Spec: [[2026-09-23-change-engine-spec]] §3 + James's 23 Sep evening feedback (in the spec). Step 2 (#102) is live: each
concept carries `partPlan` [{part, action keep|edit|regenerate, note}] and the build request gets a text `Part plan:` line.

## What done looks like (James's words)
The witch is the ORIGINAL Frankenstein base plate reworked (re-cut so the plate itself reads as a witch), fitted to the
kept frame. It is not an overlay and not a from-scratch lookalike. The hinged box keeps its body byte-for-byte and gets
JAMES on its real lid. Options show a real picture of the customer's part, not only a line sketch.

## Worktrees
- `3d-printing` (model-forge): `/root/wt-3dp-source`, branch `build/source-parts`. It must merge FIRST: the job image
  copies model-forge at build time, and the host gates run it directly.
- `printtweak`: `/root/wt-pt-step3`, branch `build/change-engine-build`.

## A. model-forge `scripts/model_card.py` (3d-printing)
1. `load_parts` also returns each instance's 4x4 transform, so the result is (name, canonical mesh, placed meshes,
   transforms). Existing callers keep working.
2. New `--source-dir DIR`: for each part, write the canonical mesh as `DIR/<slug>.stl` plus `DIR/parts.json`:
   `[{"name": <card name>, "slug": <[a-z0-9-]>, "file": "<slug>.stl", "instances": [<4x4 row-major>...]}]`.
   Slug = lowercase, runs of non-[a-z0-9] become `-`, trimmed, ≤40 chars, deduped with `-2`, `-3`.
   The card JSON gets `slug` on every part.
3. New `--tiles-dir DIR`: keep the per-part render PNGs that `build_sheet` already makes (today they're deleted) as
   `DIR/<slug>.png`.
4. Tests: `hinged-box.3mf` and `frankenstein-switch.3mf` (`/var/lib/printtweak/test-models/`). Every part is exported,
   applying `instances[i]` to `<slug>.stl` reproduces the placed mesh (bbox within 0.01 mm), slugs are unique and valid,
   and there is one tile per part. Gear detection still reports the 20-tooth gear on Frankenstein (23 Sep lesson:
   re-test real files after ANY model_card change).

## B. Host: the design job gets the source (printtweak `worker/worker.py`, `worker/card.py`)
1. `card.build` gains `source_dir` / `tiles_dir` args that pass the new flags.
2. `process()` for a design job with a mesh upload (.stl/.3mf/.obj) AND a partPlan: run the card with
   `--source-dir job_dir/in/source`. Write `in/model_card.json`, and put `partPlan` into `request.json`.
   If the card fails, drop `partPlan` from request.json (the build falls back to today's behaviour) and log it.
3. The partPlan arrives structured, not only as text. `convex/worker.ts` (claim payload, around line 143) adds the chosen
   concept's `partPlan` (via `chosenOf`) for design jobs. Tweak jobs don't get it (step 4).
4. The brief job also runs with `--tiles-dir`, uploads each tile with the existing `_upload()`, and sends
   `partImages: [{part: <card name>, storageId}]` (≤ 20) to `reportBrief`. That's stored on `design.brief.partImages`, and
   the design query resolves each to a URL.

## C. Sandbox (printtweak `worker/job/run_job.py`, `system_prompt.md`, `brief_prompt.md`)
1. When `request.json` has `partPlan`, the build prompt adds a block that points at `/job/in/source/parts.json` +
   `model_card.json` and says, per action:
   - **keep:** output the part with `name` = its slug, file = the source mesh converted to .3mf unchanged, same
     instance count. (The host enforces this anyway, see D.)
   - **edit:** load `/job/in/source/<slug>.stl` with trimesh and change only the requested region with manifold3d
     booleans (union/difference, text as a solid), following `references/mesh-editing.md`. Declare the region in
     `checks.json` `edits: [{part: <slug>, region: {min:[x,y,z], max:[x,y,z]}}]` in the part's own coordinates.
   - **regenerate:** model it fresh in build123d, fitted to the kept parts. Declare `mates` against the kept parts'
     slugs so the mechanics gate measures the real fit.
   - A remix never adds a separate add-on/overlay part. Every output part is a card part.
   - `assembly.json`: kept and edited parts use the source instance poses (the host overwrites keep parts anyway).
2. `brief_prompt.md` (remix = card present):
   - Every concept changes the customer's own parts (edit or regenerate). Never propose an overlay, cover or add-on
     piece.
   - Changing a part's outline or look (a witch silhouette) is an **edit** of that part that keeps its mounting features
     (holes, cutouts, pegs), or a **regenerate** fitted to them.
   - partPlan entries gain `label`: a short plain name for the customer ("Lid", "Base plate"), ≤ 30 chars.
3. `_part_plan` accepts `label` (a string, trimmed and capped at 30; missing → none). The Convex `PART_PLAN` gets
   `label: v.optional(v.string())`. `reportBrief` drops a plan whose label is over 60 UTF-16 units (same drop-not-throw
   rule as notes).

## D. Host gates (printtweak `worker/gates.py` or a new `worker/source_gate.py`; wire it into `run_all` before mechanics)
1. **Keep, by construction:** for each keep part, the host REPLACES `out/<slug>.3mf` with the source mesh (converted
   in model-forge's venv, like the other gates) and REPLACES its `assembly.json` instances with the source poses.
   The poses come from the 4x4 transforms, converted with the exact inverse of `assemble_glb.pose()`. Test the
   round-trip against pose(): position within 1e-6 and the rebuilt matrix within 1e-6.
   Missing from `parts.json`, or the wrong count → failure `a part you asked to keep is missing: <label or name>`.
   After the swap, check the output against the source (volume within 0.1 %, bbox within 0.05 mm) as a belt.
2. **Edit gate:** sample 3000 points on the SOURCE surface OUTSIDE the declared region (expanded by 1 mm). Every point
   must be within 0.05 mm of the output part's surface (`trimesh.proximity.closest_point`). Fail →
   `the <label> changed outside the part you asked to change`. If there's no `edits` entry for an edit part →
   `mechanics`-style undeclared failure. A declared region covering > 80 % of the part's bbox volume → failure
   `edit region too large: use regenerate` (stops declaring the whole part).
3. **Regenerate:** there's no new gate. The existing mechanics gate measures `mates` against the kept parts (a multi-part
   design must declare checks.json already).
4. Gate FAIL lines flow into `previousFailures` like every other gate (worker.py:466-472), so attempt 2 sees them.

## E. UI (printtweak `components/chat/BriefChat.tsx`, `convex/designs.ts`)
1. The option card, above the sketch: when `brief.partImages` exists, show the real render of each part the option
   edits or regenerates, captioned `Your <label>: this is what changes`. Kept parts are not shown. Alt text =
   caption. Max 3 images per card.
2. The `concept-plan` line uses `label` when present, else the card name.
3. The approveBrief `Part plan:` text uses `label (card name)`.

## Out of scope
Pricing from the plan, revise/tweak with a partPlan, the project page (step 4). Click-to-comment (§6).

## Checks the builder runs and pastes (capture exit codes; never `| tail && git commit`)
- 3d-printing: model_card tests on both real 3MFs (above) + the existing model-forge test suite.
- printtweak: `npx tsc --noEmit`, `npx vitest run`, and worker pytest with `/root/printtweak/worker/.venv/bin/python -m
  pytest -q worker/tests`. Summary lines + exit codes.
- New tests (both sides):
  - keep swap: a sandbox output with a CHANGED keep part ends up byte-equal to the source after the gate, and the
    assembly pose is restored;
  - missing keep part → failure;
  - edit outside the region → failure, inside → pass;
  - region > 80 % → failure;
  - pose round-trip;
  - partPlan reaches request.json only when the card succeeded;
  - `partImages` stored and shown;
  - label capped.
  Build the edit-gate tests from a real part: the hinged-box lid from the source export, plus a manifold3d-embossed
  box on its flat face.
- Sabotage, and paste the output of each:
  (1) disable the keep swap → the keep test goes red;
  (2) make the edit gate ignore the region → the outside-edit test goes red.
  Restore, then `rg SABOTAGE` returns nothing BEFORE commit.
- Commit with explicit paths (node_modules/.venv are symlinks; never `git add -A`). Don't push, don't open PRs.

## Staging proof (brain, after gates; James OK'd staging deploys for this work)
Merge model-forge first → staging image built from both branches → `stage-deploy.sh`.
1. Hinged box "JAMES on the lid": the body is byte-equal to the source, JAMES is raised on the real lid, it slices,
   and the hinge gaps are unchanged.
2. Frankenstein → witch: the frame, handle, gears, rack and guide are byte-equal to the source. The base plate is
   re-cut to a witch look with its switch cutout + screw holes in place, and the mates pass against the real frame.
   The ready page shows the reworked plate.
3. The option cards show the real part renders.
