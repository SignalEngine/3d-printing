# TweakMyPart chat: auto-scroll, and show what he's doing while the questions are prepared (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/chat-wait`, cut from `origin/master`. Real `node_modules` (check `[ -L node_modules ]`; in a worktree use `next dev --webpack` if Turbopack rejects a symlink). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod. `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Run `python3 /root/.claude/scripts/surface-sweep.py progress jobLog _tail_log process_brief medianDesignMs log --out spec/surfaces.md` and account for every hit.

## Why (James, 21 Sep, on his phone in the new chat)
"Needs to auto scroll down." "It is now thinking but taking a long time — can we speed it up or at least say what it's thinking about and a wait time to keep people on?" The brief job (Sonnet, thinking capped) takes ~3 min and today the chat shows only three dots.

## 1. Auto-scroll (`components/chat/*`)
- The thread scrolls to the newest bubble whenever a bubble, question, sketch or progress line is added, and when the composer grows — unless the reader has scrolled up more than ~80 px from the bottom (then a small "↓ New" pill appears; tapping it scrolls down and re-sticks). Use `scrollIntoView({ block: "end", behavior: reduced ? "auto" : "smooth" })` on a sentinel element.
- On phones, focusing the composer must not hide the last bubble: scroll after the on-screen keyboard resizes the viewport (`visualViewport` resize event).

## 2. Real progress lines from the questions step (worker + prompt)
- `worker/job/brief_prompt.md`: add a rule — "Before each step, append ONE short line (≤ 60 chars, present tense, customer-facing) to `/job/out/progress.txt`: e.g. `Looking at your photo`, `Working out what it's made of and where the load goes`, `Choosing a mechanism that prints well`, `Writing your questions`, `Drawing the sketch`. Use Write with the full file content each time (you have no append tool)." Keep it to 3–6 lines.
- `worker/worker.py` `process_brief`: start a tail thread like `_tail_log` on `out/progress.txt` (poll 3 s, forward only new lines, stop when the container exits) → `_progress(convex, secret, job, "brief", line)`. `worker:progress` must accept stage `"brief"` (extend the validator) and append to `jobLog` as today.
- Fallback when no line has arrived after 25 s: the page shows "Thinking it through…" (client-side), not a fake step.

## 3. Wait time (`convex/designs.ts`, chat page)
- `designs.get` adds `medianBriefMs` (median of the last 20 finished `brief` jobs with a brief, min sample 3; else null) and `briefStartedAt`.
- Under the typing dots: the latest progress line, then a muted "usually about N min · M:SS so far". If `medianBriefMs` is null: "usually a few minutes".
- The typing indicator stays; the mascot is `thinking`; when a progress line arrives he does one `presenting` beat? No — keep him `thinking` (beats are for replies).

## 4. Tests and proof
- Chat unit tests: auto-scroll calls on new content, sticky-bottom rule, "New" pill when scrolled up, progress line + wait text rendering, fallback after 25 s (fake timers).
- Convex: `progress` accepts stage `brief`; `medianBriefMs` computed only from brief jobs.
- Worker: `process_brief` forwards new progress lines in order and stops at exit (fake runner writes lines mid-run).
- Fixture: `/dev/motion?state=chat&play=1` shows progress lines arriving at 5 s intervals; record `spec/motion/chat-wait-mobile.webm` (390×844) and frame-review: the thread stays scrolled to the bottom as bubbles arrive.
- `run-limited npx vitest run`, worker pytest (`/tmp/claude-0/-root-3d-printing/b59e9ac3-f8b5-4a83-98d1-e5d6fbb04e3c/scratchpad/ptvenv/bin/python -m pytest worker/tests -q`), `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, recording timestamps, anything not verified, and that the prompt changed (image rebuild). No new dependencies. Do not change the brief model or thinking settings (the brain is measuring those separately).
