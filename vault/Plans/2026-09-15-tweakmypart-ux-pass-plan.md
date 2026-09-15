# TweakMyPart UX pass: the working page and the ready page

Why: the first live runs (15 Sep) work end to end in 2-3 minutes, but the page shows a static "Designing your part" heading and a fidgeting mascot for the whole run, then a bare Ready card. James: "boring and blank and no clear indication of what's happening". James chose all four: live progress steps, live design log, stage-matched mascot, a test login (done: `james+clerk_test@powleads.com`, dev code).

## 1. Worker reports stages and log lines (Convex + worker)

- New mutation `worker:progress({secret, jobId, stage, line?})`. `stage` ∈ `queued | designing | checking | rendering | ready`. Stores `stage` and `stageAt` on the job, appends `line` (≤ 200 chars) to a new `jobLog` table (`jobId, text, at`), capped at the last 60 lines per job.
- `worker.py` calls it: `designing` when the container starts, then relays the agent's progress: run_job.py already sees every SDK message; it writes one short line per tool call or assistant text to `/job/out/log.jsonl` (append-only, the host tails it every 3 s and forwards new lines). `checking` when gates start (one line per gate: "Checked it's watertight", "Sliced: 0.4 h, 1 g", "Text matches"), `rendering` during render + vision, `ready` at report.
- `designs.get` returns `stage`, `stageAt`, `log` (last 30 lines) and `elapsedMs`.
- Failure wording: if the failure came from OUR checks (gate or vision after a built model) the user message is "Our checks failed on our side, not yours — we're retrying" and the worker retries once automatically before reporting failed. Only a declined design says "we can't make this".

## 2. Working page

- Progress rail with the four steps lit in order, elapsed time counting up, and "usually 2-4 min" (median of the last 20 ready jobs, computed in `designs.get`; fallback text until there are 5).
- Live log under the rail: newest line at the bottom, auto-scroll, monospace-lite, one accent dot pulsing on the current line. The user's request and any earlier chat stay above it.
- Mascot: `working` = idle-1/2/3 while queued; `printing` (idle clips, print composite already baked in) while designing; `focus` clip looping while checking/rendering; then `done` → reveal → tablet.
- Mobile: rail collapses to "Step 2 of 4 · Designing · 1:42".

## 3. Ready page

- Tablet preview stays the centrepiece; beside it a single card: quote line, then two real buttons (`Download 3MF`, `Download STEP`) and a muted "Print + post £19 (coming soon)" line.
- Remove the mini second mascot; `point` is not used here. Keep one character on the page.
- Chat: request and log collapse into "What happened" (expandable); the tweak box becomes a chat composer with the reply appearing as a new "You:" bubble and the page going back to the working rail.
- Hide Chrome's picture-in-picture controls on all mascot videos (`disablePictureInPicture`, `controlsList="nodownload noplaybackrate"`).

## 4. Tests and proof

- Convex tests: progress mutation validates stage and secret, log cap at 60, `designs.get` exposes stage/log/elapsed, own-check failures retry once then fail with the new wording.
- Worker tests: log tail forwards new lines only; gate lines emitted; retry path.
- Recorded run with the test login (the `pt-liverun.mjs` recorder): rail advances through all four steps, log shows ≥ 5 lines, mascot state changes with the stage, Ready shows buttons and no second mascot. `/watch` the recording before showing James.

Estimate: one builder session (~2 h) + one live recording run (~$0.35).
