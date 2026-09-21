# TweakMyPart brief v3: concepts first, then measurements with "measure this" diagrams (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/brief-concepts`, cut from `origin/master` **after the chat-wait PR (build/chat-wait) has merged** — the brain cuts the worktree. Real `node_modules` (check `[ -L node_modules ]`; `next dev --webpack` in a worktree if Turbopack rejects a symlink). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Run `python3 /root/.claude/scripts/surface-sweep.py sketch sanitizeSketch parse_brief reportBrief approveBrief reviseBrief questions concepts --out spec/surfaces.md` and account for every hit.

## Why (James, 21 Sep, live)
His yarn-caddy request: the AI proposed hooking a bar into the pegboard holes and asked for measurements; James: "They can't clip into those holes — different on both sides and not in the same place, needs to clip over." Only then did it propose edge clips. "It should have talked about multiple solutions first and showed me them before making measurements to something that would not have worked." And: "some people won't understand 'inside face to inside face' — show a sketch and say the distance between here and here."

## Flow (replaces the single questions step)
1. **Concepts** — the brief job returns `concepts: [{ id, title, how: "<one or two sentences>", sketch: "<svg>", pros: [..], cons: [..], unverified: "<what the photo could not confirm, or empty>" }]` (2–3, genuinely different: e.g. edge clip vs through-hole bar vs friction spacer), with `recommended: "<id>"` and a one-line `why`. Each concept sketch: the object in outline with the part drawn in the accent colour, one view, ≤ 8 KB.
2. In the chat, he says "Here are a few ways to do it" and each concept is a card bubble (title, sketch, how, pros/cons, the unverified note in amber) with a **Go with this** chip; the recommended one is marked. Picking a concept calls `designs:pickConcept({ designId, conceptId })`.
3. **Measurements** — `questions` are returned per concept (`concepts[i].questions`, 2–4 each, each measurement question with `diagram: "<svg>"`: the object outline with only that measurement drawn arrow-to-arrow and a 3–6 word label a child could follow, ≤ 8 KB; choice questions get no diagram). After a pick, the chosen concept's questions arrive one at a time as today, each measurement one with its diagram card above the answer control (tap to enlarge). No second model call is needed for the pick (the questions came with the concepts).
4. `approveBrief({ designId, answers })` appends "Chosen approach: <title> — <how>" plus the answers to the request as today; `reviseBrief` (cap 3) still re-runs the whole brief with the extra text (e.g. "the holes don't line up") and the customer picks again.
5. Failure paths unchanged (`briefSkipped`). The overall sketch bubble stays for the chosen concept (its sketch) with the summary.

## Contract changes
- `brief.json`: `{ summary, concepts: [...], recommended, why }`; `sketch` at top level is no longer required (the chosen concept's sketch is used). `parse_brief` validates: 2–3 concepts, each with `id` `[a-z0-9-]+`, title ≤ 80 chars, `how`, `sketch` ≤ 8 KB, 2–4 questions, diagrams ≤ 8 KB each; whole brief ≤ 160 KB. Keep accepting the old shape (`questions` + `sketch` at top level) by wrapping it as one concept.
- Convex: `brief` on the design stores `concepts` (sanitise every sketch/diagram with `sanitizeSketch`), `recommended`, `chosenConcept?`; `reportBrief` validators updated; `pickConcept` mutation (design must be in `brief`, concept must exist); `designs.get` returns them; `approveBrief` requires a chosen concept when concepts exist.
- `worker/job/brief_prompt.md`: the engineering section now ends with "propose 2–3 different approaches, recommend one and say why; for each, list what the photo could not confirm (hole alignment, hidden thickness)"; measurement questions must include the diagram; keep the whole thing fast (no long prose).

## Cost and time check (report the numbers)
Sandbox runs of the fixture request (`kind: "brief"`, `printtweak-job:latest` with the new prompt + run_job mounted), three runs: median `costUsd` and wall time vs the current single-concept brief (currently ~$0.16 / 25 s on Sonnet with thinking disabled — do not change the model or thinking settings).

## Tests and proof
- Worker: `parse_brief` new shape + legacy wrap + size limits; prompt contains the concepts and diagram rules.
- Convex: `reportBrief` sanitises all sketches/diagrams and stores concepts; `pickConcept` validation; `approveBrief` refuses without a pick when concepts exist and appends the chosen approach; `designs.get` shape.
- Chat: concept cards render with the recommended mark, picking sends `pickConcept`, then the chosen concept's questions arrive one at a time with diagram cards where present; enlarge works; revise re-asks.
- Fixture `/dev/motion?state=chat`: two concepts, pick, three questions (two with diagrams). Record `spec/motion/chat-concepts-mobile.webm` (390×844) and `chat-concepts-desktop.webm`; frame-review and cite timestamps.
- `run-limited npx vitest run`, worker pytest (`/tmp/claude-0/-root-3d-printing/b59e9ac3-f8b5-4a83-98d1-e5d6fbb04e3c/scratchpad/ptvenv/bin/python -m pytest worker/tests -q`), `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, cost/time medians, recording timestamps, anything not verified; the prompt and run_job changed (image rebuild). No new dependencies. Do not change the brief model or thinking settings.
