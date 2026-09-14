# Builder handover: TweakMyPart real pages: styled site, mascot player, tablet preview

You are the BUILDER. Build only what this handover describes, then stop and report.

- Repo: `SignalEngine/printtweak`, worktree on branch `build/design-pass`, cut from `master` (Tasks 1-6 merged, `64532b0`). `node_modules` is a real install.
- Context: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md` ("Update 2026-09-14: personal mode", Brand, Design pass) and `/root/3d-printing/vault/Design/tweakmypart-mascot/2026-09-14-animation-redo-plan.md`. The name users see is **TweakMyPart**.
- Working reference (open it, copy its behaviour, not its markup): `/tmp/claude-0/-root-3d-printing/b59e9ac3-f8b5-4a83-98d1-e5d6fbb04e3c/scratchpad/mascot/v2/index.html`. It contains a working clip sequencer (two stacked videos, crossfade on `canplay`) and a working tablet preview (transform clip → loading screen → three.js on the tablet screen → dials → reverse clip).
- James: "lets make the actual page and system; we can play with the animation later". So: every clip is a swappable file behind a manifest; no animation tuning in code.

## Assets

Copy `/root/3d-printing/vault/Design/tweakmypart-mascot/web-v2/*` into `public/mascot/` and commit (about 7 MB). Files: `hello, idle-1, idle-2, idle-3, listening, thinking, presenting, point, oops, focus, reveal` (`.mp4` + `.jpg` poster), `tab-transform.mp4`, `tab-transform-rev.mp4`, `tablet.jpg` (816x1054).
Create `public/mascot/manifest.json` listing each clip file, poster, and `loop` (idles true, others false). All clips start and end on the same resting pose except `hello` (starts off screen) and the tab clips.

## Build

1. **Look (dark, one system).** Tokens as CSS variables in `app/globals.css` (Tailwind 4 is installed): ground `#0b0d10`, card `#15181d`, line `#262b33`, text `#eceff2`, muted `#9ba4ae`, accent orange `#f08a3c`, focus teal `#46c7b5`. Fonts via `next/font/google`: Bricolage Grotesque (headings), Instrument Sans (body). Mobile-first; 16 px side gutter; buttons and links look clickable; visible focus ring; every input labelled. No purple gradients, no emoji markers.

2. **`components/mascot/Mascot.tsx`** (client): a clip player driven by a `state` prop.
   - Two stacked `<video muted playsInline>` elements, crossfade 200 ms on `canplay`, `mix-blend-mode: screen` on a dark panel so the black background vanishes.
   - `state`: `"hello"` (plays once, then idle), `"idle"` (shuffle idle-1/2/3, never the same twice in a row), `"listening"`, `"thinking"`, `"working"` (idles only), `"done"` (focus then reveal, once, then calls `onDone`), `"oops"` (once, then idle), `"point"`, `"presenting"`. One-shot clips return to idle on `ended`.
   - The next clip is decided ONLY on `ended` or a `state` change, never per animation frame (Accelion's Orbi bug: re-deriving per frame reset `src` 60x/s).
   - Pure function `nextClip(current, state, rng)` holds the logic; unit-test it.
   - Prefetch the manifest's clips once on mount (`fetch`, cache warm only).
   - `prefers-reduced-motion: reduce` → poster image only.
   - Decorative: `aria-hidden`, no focus targets.

3. **`components/mascot/TabletPreview.tsx`** (client): the design-ready moment.
   - Props: `glbUrl: string | null`, `loading: boolean`, `onExit()`.
   - Plays `tab-transform.mp4`, then shows `tablet.jpg`, then overlays a screen box at **left 28.5%, top 42%, width 43.2%, height 26.3%** of the tablet image. While `loading` or no `glbUrl`: loading text + orange bar. Otherwise: the existing `components/ModelViewer.tsx` logic (GLTF) rendered inside that box.
   - Two dial buttons (left 21% / right 79%, top 56%, width 10%): drag or arrow keys rotate the model (left = spin, right = tilt) and the dial rotates with it. `aria-label`s on both.
   - "Back" plays `tab-transform-rev.mp4` then calls `onExit`.
   - Reduced motion: skip the clips, show the tablet still directly.
   - Keep the screen-box numbers in one exported constant.

4. **Pages.**
   - `app/page.tsx` landing: heading "Describe a part, or upload your model" (the e2e test pins it), "Private beta" tag, `<Mascot state="hello">`, the three examples, "Start a design" button.
   - `app/design/new/page.tsx`: layout mascot beside the form (below it on mobile). `listening` while the textarea has focus and text changes, `thinking` while submitting, `oops` on error.
   - `app/design/[id]/page.tsx`:
     - queued/designing/checking → `working`, with the status line.
     - First time a design becomes `ready` in this page session: `done` (focus + reveal), then `<TabletPreview glbUrl={design.glbUrl} />`. A design that was already `ready` on load goes straight to the tablet (still plays the transform).
     - Beside the tablet: quote info, Download 3MF / STEP links, the tweak form. `point` plays when the downloads first appear.
     - failed/declined → `oops` + the reason.
     - Chat messages list styled as a conversation.
   - Keep all Task 6 behaviour and error copy; don't change Convex, the worker or `proxy.ts`.

5. **Tests.**
   - vitest (jsdom for component files via `// @vitest-environment jsdom`): `nextClip` covers hello→idle, idle never repeats, one-shots return to idle, `done` = focus→reveal→onDone, reduced motion renders a poster and no video.
   - `TabletPreview` shows the loading state when `glbUrl` is null.
   - Keep `e2e/smoke.spec.ts` passing (heading + examples, sign-in redirect).

## Hard rules

- `[ -L node_modules ]` check before any npm command; heavy commands through `run-limited`, one at a time.
- Do not create or edit the root `GATES.md`.
- Tests RED first, then GREEN. Full `run-limited npx vitest run` and `npx tsc --noEmit` pass at the end.
- Do not review your own work, merge or push. Commit on your branch.
- Report: RED/GREEN, file:line of each change, asset sizes, anything not done.
