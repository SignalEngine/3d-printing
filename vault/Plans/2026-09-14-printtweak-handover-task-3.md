# Builder handover: PrintTweak Task 3 (sandbox), personal mode

You are the BUILDER. Implement **only Task 3** of the plan, then stop and report.

- Plan: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md`. Read, in this order: "Update 2026-09-14: personal mode" (it OVERRIDES Task 3 where they differ), Global Constraints, File Structure, Task 3.
- Spec: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-spec.md` §0 and §3 (context).
- You are in a worktree of `SignalEngine/printtweak` on branch `build/task3-sandbox`, cut from `master` (Tasks 1-2 merged).

## Personal-mode changes to Task 3 (from the plan's update section)

1. `worker/proxy/proxy.py` does NOT inject any key and does NOT read `ANTHROPIC_API_KEY`. It forwards `/v1/*` to `https://api.anthropic.com`, passing the request's own auth headers through (drop only hop-by-hop headers: host, content-length, transfer-encoding, connection). Everything else returns 403.
2. The job container receives `-e CLAUDE_CODE_OAUTH_TOKEN` (variable name only, value from the caller's exported environment) and never `ANTHROPIC_API_KEY`. Keep `ANTHROPIC_BASE_URL=http://proxy:8080`.
3. `worker/setup_network.sh` must not require `ANTHROPIC_API_KEY`. It may source `/etc/printtweak/worker.env` if it exists but must work without it (the proxy container needs no secrets).
4. Sandbox test changes (`worker/tests/sandbox_test.sh`):
   - Test 1: the container env must contain no `WORKER_SECRET`, `CONVEX`, `STRIPE` or `sk-ant-api` values. The OAuth token is expected, so don't flag `CLAUDE_CODE_OAUTH_TOKEN`.
   - Test 4 ("reaches Anthropic through the proxy"): run a one-line Agent SDK query inside the container (`/opt/venv/bin/python -c` using `claude_agent_sdk.query` with `model="claude-haiku-4-5-20251001"`, `max_turns=1`, `max_budget_usd=0.05`, prompt "Reply with OK") and assert a `ResultMessage` with `is_error == False`.
   - If `CLAUDE_CODE_OAUTH_TOKEN` is not available (not exported and not in `/etc/printtweak/worker.env`), test 4 prints `SKIP: needs James's token (claude setup-token)` and the script ends with `SANDBOX_OK_EXCEPT_LIVE` instead of `SANDBOX_OK`. Do not fake a pass.
   - Tests 2, 3, 5, 6, 7 unchanged.
5. Never print, echo, log or commit the token. Read it only as `source /etc/printtweak/worker.env` inside the test/setup script; it may not be readable by you (mode 600) — if not, treat it as unavailable (point 4).

## Environment notes (verified by the brain)

- Docker 29, cgroup v2. Existing `printtweak-*` images/networks: none.
- Model-forge lives at `/root/3d-printing/skills/model-forge`; OrcaSlicer at `/root/3d-printing/orcaslicer` (380 MB). `setup_network.sh` copies both into the build context; add `worker/job/model-forge/` and `worker/job/orcaslicer/` to `.gitignore` and never commit them.
- The VPS has ~3 GB RAM free, shared with other sessions: run `docker build` and every other heavy command through `run-limited`, one at a time.
- `run_job.py` / `system_prompt.md` are Task 4. For Task 3, `setup_network.sh` writes placeholders only if they are missing (as the plan shows). Don't commit placeholders.
- The job image must also symlink `/root/3d-printing/.venv/bin/python` → `/opt/venv/bin/python` (plan Task 3 note), because model-forge scripts hardcode that path.

## Rules

- Run `/unlazy tree 2` on Task 3 first and write `GATES.md` at the worktree root; commit it last.
- Show `sandbox_test.sh` RED before building (no image/network), then GREEN (or `SANDBOX_OK_EXCEPT_LIVE` without the token). Do the plan's sabotage check (job container on `bridge` → test 3 must FAIL), then revert.
- Do not review your own work, merge, or push to `master`. Commit on your branch and report: RED output, GREEN output, sabotage output, files changed with file:line, image sizes, and anything that blocked.
