# TweakMyPart: TypeSafe (Jev) as a fast typed judge — concept filter and part-count budget (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/typesafe-gates`, cut from `origin/master` (≥ 938e0ea). Real `node_modules` (check `[ -L node_modules ]`). Never touch `/root/printtweak`, the service, Convex env, `/etc/printtweak/*`, or run `convex deploy`/`convex dev` against prod. `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Run `python3 /root/.claude/scripts/surface-sweep.py classify_multipart process_brief reportBrief concepts max_budget_usd request.json --out spec/surfaces.md` and account for every hit. The API key is in `/etc/printtweak/typesafe.env` (`TYPESAFE_API_KEY=…`): your tests must NOT need it (mock the HTTP call); the one live check at the end reads it via `set -a; . /etc/printtweak/typesafe.env` inside a script and never prints it.

## Why (James, 21 Sep 20:30: "can this help us anywhere?" → spike 19/20)
Spike (`vault/Research/2026-09-21-typesafe-spike.md`): a `noul` question "does this approach depend on something the customer ruled out?" agreed with hand labels on 19/20 real cases (the miss was a label problem), a `choice` "one part or several?" was 6/6 at ≥ 0.97, median 0.63 s, ≈ $0.00002 per question. Today those two decisions are a prompt rule (half-fails) and a regex.

## API (from docs.typesafe.ai/api.md)
`POST https://api.typesafe.ai/v1/systemone`, headers `Authorization: Bearer <key>`, `Content-Type: application/json`, body `{ "state": <string|object>, "model": "jev-latest", "questions": { "<id>": { "type": "noul"|"choice"|"score", "instructions": "...", "criteria": {...} } } }` → `{ "model", "answers": { "<id>": { "type", "noul": 0..1 } | { "type", "choice", "probabilities", "confidence" } }, "usage": { "input_tokens", "output_tokens" } }`. 401/422/429/529 errors; back off on 429/529. The eval script and 20 cases: copy `/tmp/claude-0/-root-3d-printing/b59e9ac3-f8b5-4a83-98d1-e5d6fbb04e3c/scratchpad/typesafe/{eval.py,cases.json}` into `worker/tests/typesafe/` (keep as a manual live check, marked so pytest skips it without the key).

## 1. `worker/typesafe.py` (host)
`ask(state, questions, timeout=8.0) -> dict | None` using urllib (no new deps), key from `TYPESAFE_API_KEY` env, one retry with backoff on 429/529, `None` on any failure (network, 4xx, missing key) — callers fall back. Log one line per call to the worker log: question ids, latency, tokens. `enabled()` = key present and `TYPESAFE_DISABLED` unset.

## 2. Concept filter — `worker/worker.py` `process_brief`, before `worker:reportBrief`
For each concept, state = `{ "customer_messages": <request incl. later paragraphs + Known so far>, "proposed_approach": "<title> — <how>" }`, question `ruled_out` (noul, the spike's exact instructions/criteria). Drop concepts with `noul >= 0.7`; never drop below 2 concepts (keep the lowest-scoring ones; if the recommended one was dropped, recommend the lowest-scoring survivor and set `why` to "the first idea needed something you ruled out"). Log customer-facing: `Set aside "<title>": it needs something you said isn't there`. On `None` (API down): keep all, log nothing customer-facing. All calls for one brief in ONE request (questions map keyed by concept id) so it is one round trip.

## 3. Part-count budget — `worker/worker.py` when writing `in/request.json` for a design job
Question `parts` (choice: `one` / `several`, the spike's instructions) on the full request; write `"multipart": true|false` into `request.json`. `worker/job/run_job.py`: `classify_multipart` becomes `req.get("multipart")` when present, else today's regex (fallback, and for the brief job).

## 4. Proof
- Worker pytest with a mocked `ask`: filter drops ≥ 0.7, keeps ≥ 2, re-recommends, logs; `None` keeps all; budget flag written and read; regex fallback; one-request batching.
- Live check script `worker/tests/typesafe/live_check.sh` (brain runs it): runs `eval.py` (expect ≥ 19/20) and one real `process_brief`-shaped filter call on the caddy concepts from `cases.json`.
- `run-limited npx vitest run` (unchanged), worker pytest, `npx tsc --noEmit` green. No Convex or UI change.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, anything not verified; worker.py + run_job change (worker restart + image rebuild). No new dependencies. Never print or commit the key; `.env*` stays gitignored.
