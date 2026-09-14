# Builder handover: TweakMyPart mascot clip player

You are the BUILDER. Build only what this handover describes, then stop and report.

- Repo: `SignalEngine/printtweak`, a worktree on branch `build/mascot-player`, cut from `master` (Tasks 1-6 merged). `node_modules` is a real install.
- Context: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md` ("Design pass" and "Mascot LOCKED" bullets). The product name users see is **TweakMyPart**.
- Page styling is NOT in scope (a separate design step follows). Place the mascot cleanly in the existing plain pages.

## Assets (already made, do not regenerate)

Copy from `/root/3d-printing/vault/Design/tweakmypart-mascot/web/` into `public/mascot/`: `idle-print`, `focus-finish`, `grab-look`, `exit`, `return-wave` — each an `.mp4` (632x818, H.264, 24 fps, no audio, black background crushed to true black) plus a `.jpg` poster of its first frame. Commit them (each is under ~1.5 MB).

The clips chain end-to-start: `idle-print` → `focus-finish` → `grab-look` → `exit` (ends on empty black) → `return-wave` → `idle-print`. `idle-print` also loops onto itself.

## Build

1. `components/Mascot.tsx` (client component), a sequence player:
   - Two stacked `<video muted playsInline preload="auto">` elements; switch clips by loading the next clip into the hidden one and crossfading opacity over 200 ms when it can play (`canplay`), then swap roles. `mix-blend-mode: screen` on the videos so the black background vanishes on a dark surface; on a light page, sit the mascot on a dark rounded panel.
   - Default: `idle-print` on loop. Every 3rd loop (make it a prop `storyEvery`, default 3), play the story once: `focus-finish` → `grab-look` → `exit` → `return-wave`, then back to looping `idle-print`.
   - Prop `mode`: `"idle"` (default, as above) or `"working"` (loop `idle-print` only, no story; used while a design job runs).
   - Decide the next clip ONLY on `ended` of the current clip, never per animation frame. (Accelion's Orbi player re-derived its clip every frame and a random pick reset the video `src` ~60x/second so crossfades never completed: `/root/accelion-ai/vault/Features/orbi.md`, "Real bug found and fixed while gating this".)
   - Prefetch all 5 clips once on mount with `fetch(url)` (cache warm only) so the story does not stall on a cold network.
   - `prefers-reduced-motion: reduce` → show the `idle-print.jpg` poster only, no video.
   - Decorative: `aria-hidden="true"` on the wrapper; no focusable elements.
   - Size by prop `height` (default 320 px), width follows 632:818.
2. Place it:
   - `app/page.tsx` (landing): beside or above the heading, `mode="idle"`.
   - `app/design/[id]/page.tsx`: `mode="working"` while status is `queued`, `designing` or `checking`; `mode="idle"` otherwise.
3. Tests (vitest, jsdom or happy-dom environment for this file only via a `// @vitest-environment jsdom` comment; add the dev dependency if missing, after the `[ -L node_modules ]` check):
   - the clip order after `ended` events follows the chain above, story starting on loop `storyEvery`;
   - `mode="working"` never leaves `idle-print`;
   - reduced motion renders the poster image and no `<video>`.
   Keep the sequencing logic in a pure function (`nextClip(state, mode, storyEvery)`) so it is tested without media APIs.

## Hard rules

- Never run `npm ci`/`npm install`/`rm -rf node_modules` without checking `[ -L node_modules ]` first.
- Heavy commands through `run-limited`, one at a time.
- Do not create or edit the root `GATES.md`. Do not touch Convex, the worker, or `proxy.ts`.
- Tests RED first, then GREEN; full `run-limited npx vitest run` and `npx tsc --noEmit` pass at the end.
- Do not review your own work, merge, or push. Commit on your branch; report RED/GREEN, file:line of each change, and asset sizes.
