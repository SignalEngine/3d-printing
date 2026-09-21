# TweakMyPart: the build page on desktop = he holds the tablet too, and it narrates while it thinks (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/working-desktop-live`, cut from `origin/master` (≥ 14bcde7). Real `node_modules` (check `[ -L node_modules ]`; `next dev --webpack` if Turbopack rejects a symlink). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Load `animate` and `emil-design-eng` before UI code. Run `python3 /root/.claude/scripts/surface-sweep.py working-stage WorkingPreviewCard StepsCard WhatsDoing working-phone WorkingScreen describe_message _text_line include_partial_messages --out spec/surfaces.md` and account for every hit. Another builder is working on `worker/job/run_job.py` (mechanical gates, `parse_checks`) in a sibling branch — keep your run_job change inside the message loop / options and `_text_line`, nothing else, so the merge is clean.

## Why (James, 21 Sep 17:50, desktop, 5 min into a build)
"Building your part page is the same, and boring." What he saw: an empty stage (the mascot loops on the left), a small tablet card on the right with ONE log line, the rail, the log. One new line in five minutes, because the design job only logs on tool calls and a long code-writing turn is silent.

## 1. Desktop = the phone layout, bigger — `components/design/WorkingPage.tsx`, `app/globals.css`
- Delete the desktop grid branch (`.working-stage`, `WorkingPreviewCard`, `StepsCard`, `WhatsDoing` — remove them and their tests if nothing else uses them; the surface sweep tells you). One tree for every width: the mascot in tablet mode (`TabletPreview` with `screen={<WorkingScreen …/>}`, `skipIntro`) as the stage; the strip (step + elapsed + last two lines) and version chips; the composer and request below. Desktop ≥ 1024 px: the stage takes the left ~58% at `min(78vh, 820px)` tall, the strip + chips + composer stack on the right, vertically centred; the tablet screen therefore is ~2× the old card. 721–1023 px: stacked like the phone but centred at max 560 px wide.
- The heading row stays. The full-screen viewer stays.

## 2. It narrates while it thinks — `worker/job/run_job.py`, `worker/job/system_prompt.md`
- Design job options: `include_partial_messages=True`. In the message loop, handle the SDK's stream events: accumulate the current assistant text; whenever the accumulated text reaches a sentence end (`.`/`:`/newline) or 90 chars, pass that sentence through `_text_line` (the existing customer-facing filter — extend it to drop code, paths, JSON and anything with `/job`, `python`, backticks) and append it to `log.jsonl`, at most one line per 8 s and never a duplicate of the last line. Full `AssistantMessage` text is then NOT re-logged (dedupe by content).
- Prompt rule: "Before each step that takes a while (writing or rewriting build.py, a long check), say in ONE short sentence what you are about to do and why, in words a customer understands (e.g. 'Cutting the slot 0.3 mm wider so the rod slides freely'). Keep it to one sentence; do not narrate code."
- Result: a line at least every ~20 s during a normal run. The host tail (`_tail_log`) already forwards new lines; no worker change.
- `WorkingScreen`: when no line has arrived for 15 s, show a small "thinking · m:ss" ticker under the last line (client-side, elapsed since the last line); it disappears on the next line.

## 3. Proof
- Unit: one tree at both widths (jsdom `matchMedia` stub as the phone test does); the old components gone; the thinking ticker appears after 15 s with fake timers and clears on a new line.
- Worker pytest: a fake stream of partial text deltas produces the expected sentence lines, rate-limited (fake clock), deduped against the full message; `_text_line` drops code/paths; prompt needle test.
- Fixture `/dev/motion?state=working&play=1` at 1280×800 and 390×844: record `spec/motion/working-desktop-tablet.webm` and re-record `working-mobile-tablet.webm`; frame-review with timestamps: the big tablet screen types lines, a version prints in, the ticker shows during a quiet stretch.
- `run-limited npx vitest run`, worker pytest, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, recording timestamps, anything not verified; run_job + prompt change (image rebuild). No new dependencies. Keep every control labelled, focus visible, contrast ≥ 4.5:1.
