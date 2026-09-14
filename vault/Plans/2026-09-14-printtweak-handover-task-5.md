# Builder handover: PrintTweak Task 5 (host worker, independent gates, vision check), personal mode

You are the BUILDER. Implement **only Task 5** of the plan, then stop and report.

- Plan: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md`. Read, in this order: "Update 2026-09-14: personal mode" (it OVERRIDES the task text where they differ, including the Task 5 memory-cap bullet), Global Constraints, File Structure, Task 5.
- Spec: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-spec.md` §0 and §3-§4 (context).
- You are in a worktree of `SignalEngine/printtweak` on branch `build/task5-worker`, cut from `master` (Tasks 1-4 merged).

## Personal-mode changes to Task 5

1. **AI auth:** the worker never uses an API key. `worker.env` holds `CONVEX_URL`, `WORKER_SECRET`, `CLAUDE_CODE_OAUTH_TOKEN`. The systemd unit keeps `EnvironmentFile=/etc/printtweak/worker.env`.
2. **Job containers:** `JOB_DOCKER_ARGS` must include `--memory 3g --memory-swap 3g` (Task 3 proved `--memory` alone lets a job spill into swap) and pass the token as `-e CLAUDE_CODE_OAUTH_TOKEN` (name only; the worker's own environment supplies the value, so it never appears in a process listing). Keep `--network printtweak-jobs`, `--pids-limit 512`, `--user 10001:10001`, `--read-only`, the `/tmp` tmpfs and `ANTHROPIC_BASE_URL=http://proxy:8080`. Do NOT pass `ANTHROPIC_API_KEY`.
3. **Vision check:** `vision_check.matches` must NOT use the `anthropic` client (it can't use a subscription token). Run it as a second, short container job with the same `JOB_DOCKER_ARGS`: a tiny script in the image (or `python -c` via `--entrypoint`) that calls `claude_agent_sdk.query(model="claude-haiku-4-5-20251001", allowed_tools=["Read"], max_turns=3, max_budget_usd=0.2)`, reads `/job/out/view-front.png`, and prints the JSON `{"match": bool, "reason": str}`. Keep the plan's `matches(front_png, request, client=None)` signature so the unit tests can inject a fake; parse the reply the same way (unparseable → `match: False`). If the vision script lives in the image, add it to `worker/job/` and rebuild with `run-limited bash worker/setup_network.sh`.
4. **Refunds and failures** follow the merged Convex code: `reportResult` only accepts running jobs; a `ready` report needs `quote` and `files`; failed/declined tweaks restore the design to ready (all handled server-side — don't duplicate it in the worker).
5. **Live runs need James's token.** Unit tests use fakes and need no token. For the plan's live vision sabotage (Task 5 Step 5) check first: `[ -r /etc/printtweak/worker.env ] && grep -q '^CLAUDE_CODE_OAUTH_TOKEN=' /etc/printtweak/worker.env`. If absent, skip it and report `LIVE VISION CHECK: SKIPPED — needs James's claude setup-token token`. Never fake it. When present, load with `set -a; source /etc/printtweak/worker.env; set +a` and never print the token.
6. **Don't enable or start the systemd service.** Write `worker/printtweak-worker.service` only; the brain installs it after review.

## Hard rules learned

- **Never run `npm ci`, `npm install` or `rm -rf node_modules` without checking `[ -L node_modules ]` first.** `/root/.local/bin/verify-build` line 16 creates `node_modules -> /root/intentos/node_modules` in any worktree without one; installing through that link wiped intentos's shared packages on 2026-09-14. Task 5 is Python only and needs no npm.
- Python: a venv at `worker/.venv` (already git-ignored); never install into the system Python.
- Heavy commands (docker build/run, pytest with containers) through `run-limited`, one at a time.
- Do NOT create or edit a root `GATES.md`. Put acceptance gates and evidence in the report.

## Rules

- Tests RED first (modules missing), then GREEN. Paste both outputs.
- Do not review your own work, merge, or push to `master`. Commit on your branch (message: `feat(worker): host gates, vision check, poll loop, systemd unit`) and report: RED output, GREEN output, the live vision result or SKIPPED line, file:line of each change.
