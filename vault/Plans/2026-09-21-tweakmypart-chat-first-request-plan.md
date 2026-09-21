# TweakMyPart: chat-first request page — you talk to the mascot, he replies (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/chat-first-request`, cut from `origin/master`. Real `node_modules` (check `[ -L node_modules ]`). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only; delete `.convex/` and `.env.local` before committing). `run-limited` for heavy commands. `GATES.md` at the worktree root before code (`/unlazy tree N`), committed last. Load the `animate`, `emil-design-eng` skills and `impeccable`'s `reference/craft-floor.md` before UI code. Run `python3 /root/.claude/scripts/surface-sweep.py brief approveBrief BriefPage messages addTweak Mascot MascotState nextClip --out spec/surfaces.md` and account for every hit.

## Why (James, 21 Sep, phone)
"It's meant to be like you talking to a little animated guy and then he reacts as you talk to him. You type things in and then he replies back." Today: a form beside a mascot, then a separate questions page. Chosen: **replace the request form with a conversation**, same backend.

## What the customer sees (`/design/new`, then `/design/[id]` while `status === "brief"`)
1. **Stage**: the mascot large (desktop: left ~45%, full stage height; phone: top ~45vh, full width), in `listening` while you type, `thinking` after you send, `presenting` when he replies. A **Hide him** toggle (persisted in localStorage) collapses the mascot to a 56 px avatar beside the thread; **Show him** brings him back.
2. **Thread** (right on desktop, below on phone): chat bubbles. The first bubble is his: "What do you need made? Sizes in mm, holes, what it has to fit — or snap a photo of the spot." The composer at the bottom: textarea (Enter sends, Shift+Enter newline), an **attach** button (photo/model; camera capture on phones, same limits and the rights tick only for model files), and Send. Your message appears as your bubble; the attached photo shows as a thumbnail in your bubble.
3. **Sending** creates the design exactly as today (`designs.create`) and navigates to `/design/[id]`, which renders the same thread component (the request + the brief live on the design). While the brief job runs he is `thinking` and a typing indicator shows (three dots, 20–90 s). Reduced motion: static dots.
4. **His replies** = the brief, delivered one question at a time: each question is a bubble with tap-to-answer chips (options) or a short inline input pre-filled with the default and a "Use this" button; answering reveals the next question (200 ms slide-in), and he plays a short `presenting` beat per reply. After the last question: a bubble with the **sketch** (the paper card, tappable to enlarge) and the summary, then two chips: **Approve and build** / **Change something** (which focuses the composer; the customer's next message re-runs the brief with the extra text appended — `designs:reviseBrief({ designId, text })`, new mutation: appends to `request`, resets `brief`, creates another brief job; cap 3 revisions).
5. **Approve** calls the existing `designs:approveBrief` with the collected answers → the page switches to the working page as today (versions on the tablet, chips, rail, log). The thread stays available as "What happened" on the ready page.
6. Failure paths: brief skipped (job failed) → his bubble "I'll start from what you told me" and straight to working; allowlist / limits errors render as his bubble with the mapped `messageFor` text, not a red box.
7. Landing "Design my part" → `/design/new` unchanged.

## Data
- No schema change for the thread: the request text, `brief.questions`, `brief.answers`, `brief.sketch`, `brief.summary` and `messages` (existing table for tweaks) are enough. `answers` are written by `approveBrief` as today. Add `brief.revisions: number` (optional) for the cap.
- `designs.get` already returns `brief`; add `briefRevisions`.

## Motion (real events only)
- Mascot: `listening` on composer focus with text, `thinking` between send and reply, one `presenting` beat per reply bubble, `oops` on an error bubble. Reuse `nextClip.beat()`.
- Bubbles: 200 ms slide-up + fade; the typing indicator pulses; chips press with a 120 ms scale.
- `prefers-reduced-motion`: instant.

## Tests and proof
- Unit: composer sends on Enter, attach limits + rights tick for models only (photo none), first bubble present, questions revealed one at a time with defaults, Approve calls `approveBrief` with all answers, revise cap 3, error bubble mapping, hide/show persisted.
- Convex: `reviseBrief` appends text, resets the brief, queues a brief job, cap 3.
- Fixture: `/dev/motion?state=chat` (thread with a photo bubble, three questions answered in play mode, sketch, approve) — record `spec/motion/chat-desktop.webm` and `chat-mobile.webm` (reduce-motion OFF), frame-review both and cite timestamps.
- `run-limited npx vitest run`, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, recording timestamps, anything not verified. No new dependencies. Keep every control labelled, focus visible, contrast ≥ 4.5:1. Do not change the worker or the brief job; the backend contract is the existing `create` / `reportBrief` / `approveBrief` plus the new `reviseBrief`.
