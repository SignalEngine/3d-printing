# Change engine step 2: planning shows a per-part plan (build plan, 23 Sep 2026)

Spec: [[2026-09-23-change-engine-spec]] section 2. Repo `printtweak`, worktree `/root/wt-pt-partplan`, branch `build/part-plan`
(off origin/master 3c85bd4). Step 1 (#99) already gives the brief job `/job/in/model_card.json` + `model_sheet.png` and the
prompt rule "never ask for a size the card gives". This step adds the per-part plan to every option.

## What done looks like
When an upload has a model card, each option (concept) carries `partPlan`: one entry per card part saying keep / edit /
regenerate. The option card shows it in one plain line ("Keeps: Base frame, Hinge · Changes: Lid · Remakes: Face"). The
chosen plan reaches the build request as guidance (the keep/edit gates are step 3). No card → no partPlan, nothing changes.

## Shape
`partPlan: [{part: string, action: "keep" | "edit" | "regenerate", note?: string}]` on a concept.
- `part`: EXACT card part name (`card["parts"][i]["name"]`).
- `note`: optional, ≤ 120 chars, what changes ("raised JAMES on the flat top"). Only meaningful for edit/regenerate.
- Valid only if it names every card part exactly once, no unknown names, no duplicates, every action one of the three,
  at most 20 entries (card-part cap). Anything else → the concept keeps everything else and simply has NO `partPlan`.
  Never raise: the brief job has no repair turn, a bad brief is skipped entirely (`run_brief_job`, run_job.py:~877).

## Tasks
1. `worker/job/run_job.py`
   - `parse_brief(data, card_parts=None)`; `_parse_concept(c, card_parts)` adds `partPlan` only when `card_parts` is a
     non-empty list and the plan validates (rules above). Helper `_part_plan(value, card_parts) -> list | None`.
   - `run_brief_job` reads `out.parent / "in" / "model_card.json"` if present (json; any error → no card) and passes
     `[p["name"] for p in card["parts"]]`.
   - Tests in `worker/tests/test_run_job.py`: valid plan kept; unknown part / missing part / duplicate / bad action /
     note too long / not a list / no card → concept has no `partPlan` and the brief still parses. Long note: TRUNCATE to
     120, don't drop (keep it simple: one rule — truncate).
2. `worker/job/brief_prompt.md`: extend the Model card rule: when the card exists, each concept MUST include `partPlan`
   covering every card part by its exact card name, with the action and a short note for edit/regenerate; prefer keep
   for parts the change doesn't touch; `parts` still counts printed pieces. Add `partPlan` to the example JSON only as a
   separate short example line under the model-card rule (the main example has no card). Test: a
   `test_run_job.py` assertion that the prompt text contains `partPlan` (pattern already used for other prompt rules).
3. `convex/lib/briefShape.ts`: `CONCEPT` gets `partPlan: v.optional(v.array(v.object({ part: v.string(),
   action: v.union(v.literal("keep"), v.literal("edit"), v.literal("regenerate")), note: v.optional(v.string()) })))`.
   `convex/worker.ts` reportBrief: reject (ConvexError `brief_part_plan`) a partPlan over 20 entries or a note over 120
   chars (row-size guard; the worker already enforces it). Test in `convex/worker.test.ts`.
4. `components/chat/BriefChat.tsx`: under `concept-how`, when `c.partPlan?.length`, one `<span className="concept-plan">`:
   groups in order keep → "Keeps", edit → "Changes", regenerate → "Remakes"; each group `Label: name, name`, groups joined
   by ` · `; omit empty groups. Notes are NOT shown in the line (the `how` text carries the idea). Minimal CSS next to the
   existing `.concept-unverified` rule (same muted small text). Test in `components/chat/BriefChat.test.tsx`: the line
   text for a 3-group plan; absent when no partPlan.
5. Build request (`convex/designs.ts` ~line 179, the `approach` line): when the chosen concept has a partPlan, append
   `Part plan: keep Base frame unchanged; edit Lid (raised JAMES on the flat top); regenerate Face (...).` Keep parts
   are listed as "keep X unchanged". Test in the existing designs test file that covers the approach line (grep
   `Chosen approach`).

## Out of scope (later steps)
Card persisted to storage, keep/edit gates, source parts in the build sandbox (step 3). Revise/tweak planning with a
card, pricing from the plan (step 4). Don't touch `worker/card.py` or model-forge.

## Checks the builder must run and paste
- `npx tsc --noEmit` (exit code), `npx vitest run` (summary line), worker pytest for `test_run_job.py` + `test_worker.py`
  (summary line). Capture exit codes; never `| tail && git commit`.
- Sabotage: make `_part_plan` accept an unknown part name → at least one new test goes red → restore → grep the
  sabotage marker is gone BEFORE commit.
- Don't `git add -A` (node_modules is a symlink). Commit with explicit paths. Do not push or open a PR.

## Staging proof (brain, after gates)
Worker-only for the job image + Convex staging + web: staging is shared, announce on the board. Hinged box upload
("put JAMES on the lid") → options show Keeps: body, hinge · Changes: lid, zero size questions about card numbers.
Frankenstein → witch → an option shows Keeps: frame · Remakes: face.
