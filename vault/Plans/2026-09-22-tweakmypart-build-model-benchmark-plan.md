# TweakMyPart: can a cheaper OpenRouter model do the build? — benchmark (builder handover)

You are the BUILDER. Build the harness, then stop and report; the BRAIN runs the paid runs. Repo `SignalEngine/printtweak`, worktree on branch `build/model-benchmark`, cut from `origin/master` (≥ 124b352). Never touch `/root/printtweak`, the service, Convex env, `/etc/printtweak/*`, any key file, or `printtweak-job:latest`. `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. No self-review, merge or push.

## Why (James, 22 Sep 00:40)
"I wonder if something cheaper from OpenRouter could do the build bit? Can we figure out a test?" The design job runs Claude Sonnet 5 through the Claude Agent SDK ($1–3 per build). `claude-mm` on this box already drives the same harness against OpenRouter's Anthropic-compatible endpoint, so the sandbox can too. James approved: models GLM-5.2, Qwen3 Coder, DeepSeek V4 (whichever ids OpenRouter serves on that path); spend cap **$15** total on OpenRouter.

## 1. Model override in the sandbox — `worker/job/run_job.py`
- `DESIGN_MODEL` env (default `claude-sonnet-5`) used for the design job's `ClaudeAgentOptions(model=…)`; `BRIEF_MODEL` untouched. The SDK already honours `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` from the environment — confirm which variable `claude-mm` sets for OpenRouter (read `$(which claude-mm)`; copy its exact env, including any `ANTHROPIC_AUTH_TOKEN` vs `ANTHROPIC_API_KEY` choice and the `/api` base path) and document it in the script. Production is unaffected: the worker never sets `DESIGN_MODEL`.
- Budget: the job's `max_budget_usd` must still apply; on OpenRouter the SDK's cost accounting may be wrong or zero — also cap by **turns** (`max_turns` 60 for the benchmark) and by wall clock (the existing 35 min).

## 2. The benchmark script — `worker/tests/bench/run_bench.sh` + `bench.py`
- Inputs: a models list (`sonnet` = baseline through the normal proxy on the subscription; `zai/glm-5.2`, `qwen/qwen3-coder`, `deepseek/deepseek-v4` via OpenRouter — the script first calls OpenRouter's `/api/v1/models` to confirm each id exists and prints the substitutes it picked), 4 fixture requests: `worker/tests/bench/requests/{knob,pillbox,bracket-ears,two-clip-strut}.json` (write them from the fixtures we already use in tests; the strut one is the caddy-style 3-part design so mechanics runs).
- Per run: fresh `/job` dir, local image tag `printtweak-job:bench` (build it from the worktree like `thread_sandbox_run.sh` did), `docker run` with the same flags as `worker.py JOB_DOCKER_ARGS` plus `-e DESIGN_MODEL -e ANTHROPIC_BASE_URL -e <auth var>` (for OpenRouter runs; the sonnet run keeps the proxy + OAuth token). Then the HOST gates exactly as production: `gates.run_all` (verify, slice, text, mechanics) and `vision_check` — record each gate's result.
- Spend guard: before every OpenRouter run read `/api/v1/credits` (or `/api/v1/auth/key` usage) and stop when spend since the benchmark started ≥ $15; also stop a model after 2 total failures.
- Output `spec/bench/results.md` + `results.json`: one row per run — model, request, built?, gates passed (list), vision passed?, parts count, cost (SDK-reported; and for OpenRouter the delta from the credits endpoint, which is the real number), wall minutes, turns, plus the front render path for the brain's visual look. A summary table: per model — success rate over the 4 requests, mean cost per successful build, mean minutes; verdict rule stated: a model only qualifies if it passes all four; then rank by cost per success.
- Runs: 1 per (model, request) = 12 OpenRouter runs + 4 Sonnet; the script accepts `--repeat 2` for a second pass on qualifying models.

## 3. What the BUILDER runs and what the BRAIN runs
- Builder: unit tests for `DESIGN_MODEL` plumbing (mocked SDK) and for `bench.py`'s summary maths; build `printtweak-job:bench`; a dry run of the script with `--dry-run` (prints the 16 docker commands and the model-id check) — no paid calls. The Sonnet baseline runs (subscription, 4 runs) may be run by the builder if the worker token is available in its environment; if not, leave them to the brain.
- Brain: exports the OpenRouter key from where `claude-mm` reads it (never printed), runs the script, looks at the renders, writes the verdict into `vault/Research/2026-09-22-build-model-benchmark.md`.

## Hard rules
Report RED/GREEN, file:line, the dry-run command list, and anything not verified. No new dependencies. Never print or commit keys. Do not change the production model or prompt.
