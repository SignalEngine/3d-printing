# TweakMyPart go-live: run the worker on an Anthropic API key instead of James's Claude login (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/api-key-worker`, cut from `origin/master` (≥ 84ee59f). Never touch `/root/printtweak`, the running service, `/etc/printtweak/*`, the running proxy container, Convex env, or `printtweak-job:latest`/`printtweak-proxy:latest`. `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), commit your work, ledger last. Run `python3 /root/.claude/scripts/surface-sweep.py CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_API_KEY JOB_DOCKER_ARGS proxy setup_network worker.env --out spec/surfaces.md` and account for every hit.

## Why
Go-live checklist (`/root/3d-printing/vault/Plans/2026-09-22-tweakmypart-go-live-checklist.md`): every AI call (question rounds, builds, the preview judge) currently runs on James's personal Claude Max login (`CLAUDE_CODE_OAUTH_TOKEN` passed into each job sandbox; the proxy forwards the caller's auth). Serving the public that way is very likely against Anthropic's terms. Launch needs an API key with billing — and the key must never enter a sandbox, where the model's Bash tool could read it.

## Design (API-key mode, off until switched on)
- **Switch:** `PRINTTWEAK_AUTH=api` in `/etc/printtweak/worker.env` (read by `worker.py`); default/absent = today's `oauth` mode, byte-identical behaviour.
- **Worker** (`worker/worker.py`): in `api` mode the job `docker run` args carry `-e ANTHROPIC_API_KEY=proxy-injected` and NOT `CLAUDE_CODE_OAUTH_TOKEN` (build `JOB_DOCKER_ARGS` from a function of the mode; brief, design, tweak and vision jobs all use it). In `oauth` mode exactly today's args.
- **Proxy** (`worker/proxy/proxy.py`): if its own env has `ANTHROPIC_API_KEY`, it drops any incoming `authorization`/`x-api-key` header and sets `x-api-key: <real key>`; it also drops an `anthropic-beta` value containing `oauth` if present. Without the env var it forwards as today. The key is read at start-up, never logged, never echoed in a response.
- **Proxy start** (`worker/setup_network.sh`): runs the proxy container with `--env-file /etc/printtweak/proxy.env` when that file exists (it holds only `ANTHROPIC_API_KEY=…`, mode 600, created by James from a command the brain gives him); otherwise as today.
- **Cost accounting**: nothing changes — the SDK already reports `total_cost_usd`; in API mode that is now real money, which the admin cost page shows.

## Tests and proof
- Worker pytest: `oauth` mode args unchanged (snapshot of today's list); `api` mode args contain the dummy key and no OAuth token; every job kind uses the same function.
- Proxy tests (aiohttp test client with a fake upstream): with the env key set, the upstream sees `x-api-key: <key>` and no `authorization`, and an `oauth` beta flag is removed; without it, headers pass through untouched; the key never appears in any response body or header.
- A local end-to-end proof WITHOUT a real key: run a proxy container on a throwaway name with `ANTHROPIC_API_KEY=sk-ant-fake` against a local fake upstream (`OR_UPSTREAM`-style override you add for tests only), fire one request from a job-shaped container, and show the fake upstream received the fake key and the container never had it (`docker exec … env`).
- `run-limited npx vitest run` (unchanged), worker pytest, `npx tsc --noEmit` green.

## Hard rules
No self-review, merge or push. Commit your work. Report RED/GREEN, file:line, anything not verified (the real-key round trip is the brain's job after James adds the key). No new dependencies. Never print, log or commit a key.
