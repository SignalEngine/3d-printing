# TweakMyPart: the build asks before changing the customer's chosen approach (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/ask-before-changing`, cut from `origin/master` (≥ 42862f2). Real `node_modules` (check `[ -L node_modules ]` — do NOT remove the symlink or run npm install into it; if you need your own, `rm node_modules && npm ci` inside your worktree only after checking it is a symlink). Never touch `/root/printtweak`, the services, Convex env, `/etc/printtweak/*`, or run `convex deploy`/`convex dev` against prod. `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), commit your work, ledger last. Run `python3 /root/.claude/scripts/surface-sweep.py reportResult outcome declined needs_decision assumptions.txt finishUnsuccessful startOrAwaitPayment status --out spec/surfaces.md` and account for every hit (every place that switches on design `status` or job `outcome` must handle the new one).

## Why (James, 22 Sep 16:10)
He picked "print the M5 thread into the knob"; the build found it couldn't (the thread tool refuses < M8), silently made a hole for a brass heat-set insert, and the ready page never said so. "I don't see a thread on the inside." Chosen: **ask before changing** — the build stops and asks when it can't do what was chosen; small assumptions are shown on the ready page.

## 1. The sandbox can stop and ask (`worker/job/system_prompt.md`, `worker/job/run_job.py`)
- Prompt rule: "If the customer's chosen approach cannot be built as described (a feature the tools refuse, a mechanism that cannot work at these sizes, a missing measurement you cannot sensibly assume), do NOT substitute something else. Before modelling, write `/job/out/needs_decision.json` = `{ "question": "<one plain sentence>", "why": "<one sentence>", "options": [{ "id": "<slug>", "label": "<short>", "detail": "<one sentence>" }] }` with 2–3 options (the closest buildable alternatives, best first) and stop. Small, safe assumptions (a wall thickness, a chamfer, a fit clearance) are NOT decisions: make them and write each as one line in `/job/out/assumptions.txt`."
- `run_job.py`: `parse_decision` validates the file (2–3 options, ids `[a-z0-9-]+`, lengths capped: question ≤ 200, why ≤ 200, label ≤ 60, detail ≤ 200); if valid and no parts were exported → `result.json` `{ "outcome": "needs_decision", "decision": {…}, "costUsd": … }`. Invalid → ignored (normal flow).

## 2. The host and Convex (`worker/worker.py`, `convex/worker.ts`, `convex/schema.ts`, `convex/designs.ts`)
- `reportResult` accepts `outcome: "needs_decision"` + `decision`; the job is `done`; the design goes to `status: "needs_decision"` with `decision` stored (sanitised strings). **No retry, no refund, no free-try refund**: a paid order or the welcome build stays attached to the design — the customer has not been charged twice and is not charged again.
- `designs:decide({ designId, optionId })` (owner only, status `needs_decision`, option must exist): appends "Decision: <question> → <label> — <detail>" to the request, clears `decision`, re-queues the design job directly (the existing `queueDesignJob`; payment already covered). Max 2 decisions per design (`decisionsUsed`); the third stop is treated as a failure (normal failure path: retry/refund).
- `assumptions.txt` (≤ 1,000 chars, sanitised) is sent with a ready result and stored as `design.assumptions: string[]`.
- Every `status` switch (My prints pill "Needs your answer", admin, `designs.get`, `listMine`, the design page router) handles `needs_decision`.

## 3. What the customer sees (`app/(main)/design/[id]/page.tsx`, a small `DecisionCard`, `ReadyPage.tsx`)
- `needs_decision`: the mascot (`thinking` pose) and a chat bubble "Before I build, one question" with the question, the why in muted text, and one button per option (label + detail). Tapping → `decide`, then the working page. Telegram alert to James (`alerts` row) so a waiting customer isn't missed.
- Ready page: a small "What I assumed" list under the price card from `design.assumptions` (only when non-empty).
- `lib/messages.ts` mappings for new errors.

## Tests and proof
- Worker pytest: `parse_decision` valid/invalid/caps; a fake run that writes needs_decision.json and no parts → outcome `needs_decision`; assumptions forwarded on ready.
- Convex: `needs_decision` result stores the decision, no retry/refund/order change; `decide` appends and re-queues once, owner-only, option must exist, cap 2 then failure path; `listMine`/`get` shapes; assumptions stored.
- UI: the decision card renders and calls `decide`; the ready page shows assumptions only when present; My prints pill.
- Sandbox proof (real run, local image tag `printtweak-job:ask`, API-key mode through the live proxy — ask the brain to run it if you cannot): request "a knob 20 mm wide, 15 mm tall. Chosen approach: print the M5 thread straight into the knob" → expect `needs_decision` with options like "brass heat-set insert" / "4.2 mm tapping hole". Report cost/time.
- `run-limited npx vitest run`, worker pytest, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Commit your work. Report RED/GREEN, file:line, anything not verified. No new dependencies.
