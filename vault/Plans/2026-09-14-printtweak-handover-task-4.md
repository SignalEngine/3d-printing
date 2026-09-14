# Builder handover: PrintTweak Task 4 (in-container job runner), personal mode

You are the BUILDER. Implement **only Task 4** of the plan, then stop and report.

- Plan: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md`. Read, in this order: "Update 2026-09-14: personal mode" (it OVERRIDES the task text where they differ), Global Constraints, File Structure, Task 4.
- Spec: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-spec.md` §0 and §3 (context).
- You are in a worktree of `SignalEngine/printtweak` on branch `build/task4-runner`, cut from `master` (Tasks 1-3 and the email-relink fix merged).

## What Task 4 builds

`worker/job/run_job.py` + `worker/job/system_prompt.md` + `worker/tests/test_run_job.py`: one Agent SDK session inside the sandbox image that designs or edits one part from `/job/in/request.json` and writes `/job/out/result.json`, `model.3mf`, `model.step`. The interface and code are in the plan's Task 4; implement them as written.

## Personal-mode notes for Task 4

1. The SDK authenticates with `CLAUDE_CODE_OAUTH_TOKEN` from the container environment (James's subscription). `build_options` must NOT set an API key. Keep `max_budget_usd=2.0` and `max_turns=80` so one bad job can't burn the subscription.
2. The live smoke run (plan Task 4 Step 6) needs the token. Check first: `[ -r /etc/printtweak/worker.env ] && grep -q '^CLAUDE_CODE_OAUTH_TOKEN=' /etc/printtweak/worker.env`. If the token isn't available, skip Step 6 and report `LIVE SMOKE: SKIPPED — needs James's claude setup-token token`. Never fake it.
3. When the token is available, load it with `set -a; source /etc/printtweak/worker.env; set +a` and pass `-e CLAUDE_CODE_OAUTH_TOKEN` (name only) plus `--memory 3g --memory-swap 3g` to `docker run`. Never print, echo or log the token.
4. `run_job.py` and `system_prompt.md` currently exist as untracked placeholders written by `setup_network.sh`; replace them with the real files and commit them. After editing, rebuild the image with `run-limited bash worker/setup_network.sh`.

## Hard rules learned today

- **Never run `npm ci`, `npm install` or `rm -rf node_modules` without checking `[ -L node_modules ]` first.** A symlinked `node_modules` points at `/root/intentos/node_modules`; installing through it wiped that shared folder on 2026-09-14. Task 4 is Python only and needs no npm.
- Python tests: `python3 -m pytest worker/tests/test_run_job.py -q` (install pytest into a venv under `worker/.venv` if needed; never into the system Python used by other projects).
- Heavy commands (docker build, docker run) through `run-limited`, one at a time.
- Do NOT create or edit a root `GATES.md` (other branches change it and merges conflict). Put acceptance gates and evidence in your report.

## Rules

- Tests RED first (placeholder `run_job.py` has no `load_request`), then GREEN. Paste both outputs.
- Do not review your own work, merge, or push to `master`. Commit on your branch (message: `feat(worker): in-container Agent SDK job runner`) and report: RED output, GREEN output, live smoke result or SKIPPED line, file:line of each change.
