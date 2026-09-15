# Builder handover: TweakMyPart, humanise the live log

You are the BUILDER. Build only this, then stop and report.

- Repo `SignalEngine/printtweak`, worktree on branch `build/humanise-log`, cut from `master`. `node_modules` is a real install. Site is live; do not touch `/root/printtweak`, the service, Convex env, or run `npx convex deploy`/`dev` against prod (anonymous codegen only if needed; delete `.convex/` and `.env.local` before committing).
- Today the design page's live log shows raw lines from `worker/job/run_job.py::describe_message` ("Using Bash", "Using Read") and gate lines from `worker/gates.py`. James: turn them into plain English a customer understands.

## Build
1. `worker/job/run_job.py`: replace `describe_message` with a mapper that produces at most one plain line per assistant message:
   - `ToolUseBlock` → by tool and input: `Write`/`Edit` of a `.py` under /job → "Writing the model code"; `Bash` whose command contains `verify_model` → "Checking the model is solid"; `slice_gate` → "Slicing it for the printer"; `text_check` → "Checking the text is readable"; `render` → "Rendering a preview"; `fit.py`/`features.py` → "Checking the measurements"; any other Bash running python → "Building the shape"; `Read` → skip; anything else → skip.
   - `TextBlock` → the first sentence, ≤ 120 chars, only if it does not contain a file path, backticks, or code-like tokens (`def `, `import `, `=`); otherwise skip.
   - Collapse consecutive identical lines (do not append a line equal to the previous appended line).
   Tests in `worker/tests/test_run_job.py`: each mapping, the skip rules, the de-dupe.
2. `worker/gates.py` gate lines (the `progress` callback): "Checked it's watertight", "Sliced: {hours} h, {grams} g", "Text reads correctly", "Preview rendered", "Exported the 3D preview"; on a failed gate: "Our {name} check failed". Tests.
3. `worker/worker.py`: the vision stage line "Comparing the preview with your request" before the vision check; on retry the existing RETRY_LINE stays.
4. Page: no change needed unless lines exceed the card; keep the pulsing dot.

## Hard rules
- `[ -L node_modules ]` before any npm command; `run-limited` for heavy commands.
- Tests RED first, then GREEN; full vitest + worker pytest + `npx tsc --noEmit` green at the end.
- No self-review, merge or push. Report RED/GREEN and file:line; state that `run_job.py` changed (the brain rebuilds the job image).
