# Builder handover: TweakMyPart, sandbox self-check and failed-output retention

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/sandbox-gates`, cut from `master`. Real `node_modules`. Site is live: do not touch `/root/printtweak`, the service, Convex env, or run convex deploy/dev against prod.

Why: live run 15 Sep, trinket box: the container reported `built` but the host's `verify_model.py` failed twice ($2.49 spent). `worker/job/run_job.py` reports `built` when `model.3mf` + `model.step` exist; it never runs the checks itself.

## Build
1. `worker/job/run_job.py`: after the agent finishes, before writing `built`, run `/opt/venv/bin/python /opt/model-forge/scripts/verify_model.py /job/out/model.3mf` and `slice_gate.py` (same args the host uses in `worker/gates.py`). If either fails and budget remains (`total_cost_usd` < 0.8 × `max_budget_usd`), send ONE follow-up turn to the agent (same session: use `ClaudeSDKClient` or a second `query` with the failure output as the prompt and `resume`/continue if the SDK supports it; otherwise a fresh `query` whose prompt includes the original request, the gate output and "fix and re-run the checks"), then re-check once. If still failing, write outcome `failed` with reason `checks: <names>` and the gate output's last 300 chars as `detail`. Tests: fake gate runner; built only when checks pass; one repair turn; failed with reason otherwise.
2. `worker/worker.py`: when host gates fail (either attempt) or the vision check disagrees, copy `job_dir/out` (model files, renders, result.json, log.jsonl) to `/var/lib/printtweak/failed/<jobId>/attempt<N>/` before cleanup (create dirs, ignore errors, cap at the newest 20 job dirs by deleting the oldest). Tests with a temp root via a module constant.
3. `worker/printtweak-worker.service`: add `StateDirectory=printtweak` is NOT enough for /var/lib; keep the plain path and `mkdir -p` in code.

## Hard rules
- `[ -L node_modules ]` before npm; `run-limited` for heavy commands; no secrets; no root GATES.md.
- Tests RED then GREEN; worker pytest + vitest + `npx tsc --noEmit` green at the end.
- No self-review, merge or push. Report RED/GREEN and file:line; note that run_job.py changed (image rebuild).
