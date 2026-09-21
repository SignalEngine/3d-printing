# TweakMyPart: a little diagram with every measurement question (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/measure-diagrams`, cut from `origin/master` **after the chat-wait PR (build/chat-wait) has merged** — the brain cuts the worktree. Real `node_modules` (check `[ -L node_modules ]`; `next dev --webpack` in a worktree if Turbopack rejects a symlink). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Run `python3 /root/.claude/scripts/surface-sweep.py sketch sanitizeSketch MAX_SKETCH_BYTES parse_brief reportBrief QUESTION questions --out spec/surfaces.md` and account for every hit.

## Why (James, 21 Sep)
"It's just asked me to measure the distance between the inside faces of the two side panels. I understand that, but some people won't. Make it very clear exactly what needs measuring and what it looks like — a sketch of the original object and 'the distance between here and here'."

## Contract
- Each question in `brief.json` may carry `diagram: "<svg…>"` — a small SVG (≤ 8 KB) showing the object in outline (from the photo or the request) with THE ONE measurement drawn: two arrowheads, a dimension line, and a short label ("measure this", "inside face to inside face"). Same drawing rules as the sketch (paper card, dark ink, blue dimension lines, ≥ 13 px text, 30 px margin) but simpler: one view, one measurement, nothing else labelled. Choice questions (options) get no diagram.
- `worker/job/brief_prompt.md`: rule — "For every question that asks for a measurement, add `diagram`: an outline of the object with only that measurement drawn, arrow to arrow, and a 3-6 word label a child could follow. Keep each diagram under 8 KB."
- `worker/job/run_job.py` `parse_brief`: `diagram` optional string per question, ≤ `BRIEF_DIAGRAM_MAX_BYTES = 8 * 1024`; whole brief ≤ 120 KB.
- `convex/worker.ts` `reportBrief`: validator `diagram: v.optional(v.string())`; sanitise each diagram with the same `sanitizeSketch`; reject over 8 KB. `convex/schema.ts` brief question type gains `diagram?`. `designs.get` passes it through.
- Chat page: a question bubble with a diagram shows it as a paper card (same as the sketch card, ~70% width, tap to enlarge) between the question text and the answer control; without a diagram the bubble is unchanged. Alt text = the question text.
- Fixture `/dev/motion?state=chat`: give the first two questions diagrams so they can be recorded.

## Cost check (report the numbers)
Measure before/after on the fixture request in the sandbox (`docker run … printtweak-job:latest` with `kind: "brief"`): `costUsd` and wall time with and without the diagram rule, three runs each; put the medians in the report. Expectation: +$0.02–0.05 and +5–15 s per brief.

## Tests and proof
- Worker: `parse_brief` accepts/rejects diagram sizes; prompt contains the rule. Convex: `reportBrief` sanitises diagrams, rejects > 8 KB, stores them; `designs.get` returns them. Chat: question bubble renders the diagram card only when present; enlarge works.
- Record `spec/motion/chat-diagram-mobile.webm` (390×844) and frame-review: a question with its diagram visible above the input, then enlarged.
- `run-limited npx vitest run`, worker pytest, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, cost/time medians, recording timestamps, anything not verified; the prompt changed (image rebuild). No new dependencies.
