# TweakMyPart ready page: no long small-mascot loop, no black box, the files card always there (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/ready-entrance`, cut from `origin/master` (≥ 0a6f34a). Real `node_modules` (check `[ -L node_modules ]`; never npm install into a symlink). Never touch `/root/printtweak`, the services, Convex env, or run `convex deploy`/`convex dev` against prod. `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), commit your work, ledger last. Load `animate` and `emil-design-eng` before UI code.

## Why (James, 22 Sep 17:15, screen recording of his finished knob, desktop)
"It starts out with him really small, and it goes on for ages, running through his loop, and just doing weird motions. Then eventually it clips to this next one, which isn't full screen — that looks really weird, he should be invisible. And this side is completely empty… nothing I can do here to download or pay." Frames: 0–15 s the full-body mascot small in the top-left of a large dark card with "Show preview" buttons; ~21 s the tablet transform clip plays inside a visible BLACK RECTANGLE on the dark grey card; ~41 s tablet mode with the knob; the right column only "Checked: …", "Change something" and "What happened" (downloads were hidden by a server rule — fixed in PR #85; the price card is hidden while SHOW_PRINT_QUOTE is off, so nothing replaced it).

## 1. Entrance (`components/design/ReadyPage.tsx`, `components/mascot/TabletPreview.tsx`)
- A live transition to ready (not a reload) goes straight to the tablet: skip the full-body `done` beat entirely; play the transform-in clip at full stage size (the same crop/size as tablet mode, so nothing jumps), then the parts fly together as today. Total entrance ≤ 5 s. A reload lands directly in tablet mode (as today).
- No "Show preview" button state on a ready design at all (the tablet IS the preview); "Back" in tablet mode is removed on the ready page.
- **No black box:** the clips are black-backgrounded and composited with `mix-blend-mode: screen`; on the card's dark grey gradient the black edges show as a rectangle. Fix both ways: the ready stage behind the mascot is pure black (`#000`, with the existing orange glow as a radial gradient on top), AND the video/still layer gets `mask-image: radial-gradient(ellipse at center, #000 62%, transparent 100%)` (with `-webkit-` prefix) so any edge fades into the stage. Check it on the working page too (same component) — no rectangle there either.

## 2. The files card is always there (`ReadyPage.tsx`)
- When `partDownloads` exist, the right column's first card is "Your files": piece count, the per-part Download 3MF / STEP buttons and "Download all (zip)" — whether or not the print quote is shown. When the design was the welcome build, a small line "Your free first build"; when paid, "Paid £3.60". The print price rows stay hidden while SHOW_PRINT_QUOTE is off.
- "Checked: …" mechanics line moves inside that card, under the buttons.

## 3. Proof
- Unit: live ready transition → no `done` beat, transform starts immediately, fly-in follows; reload → tablet at once; files card renders with quote hidden; welcome/paid line; mechanics line inside the card.
- Recordings (fixture `/dev/motion?state=ready`, reduce-motion OFF, 1280×800 and 390×844): `spec/motion/ready-entrance-{desktop,mobile}.webm` — frame-review with timestamps: no small full-body mascot, no black rectangle at any frame (sample the pixels at the video's corners vs the stage background in 3 frames and report the difference), fly-in by ≤ 5 s, files card visible from the first frame.
- `run-limited npx vitest run`, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Commit your work. Report RED/GREEN, file:line, recording timestamps and the corner-pixel numbers, anything not verified. No new dependencies.
