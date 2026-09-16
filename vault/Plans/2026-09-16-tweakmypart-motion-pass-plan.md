# TweakMyPart: motion pass on the product pages (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/motion-pass`, cut from `origin/master`. Real `node_modules` (check `[ -L node_modules ]` before any npm). The site is live: never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod. `run-limited` for heavy commands. Write `GATES.md` at the worktree root before code (`/unlazy tree N`), commit it last. Run `python3 /root/.claude/scripts/surface-sweep.py Mascot MascotState ModelViewer VersionChips revealKey prefers-reduced-motion --out spec/surfaces.md` first and account for every hit. **Before any UI code, load the `animate` and `emil-design-eng` skills and `impeccable`'s `reference/craft-floor.md`; follow them.**

## Why
James (16 Sep): "Is it all fully animated and working?" — it is not. Today only the mascot video, the tablet transform clip, the pulsing step dot and the orbitable viewer move. New versions just pop onto the tablet. This pass makes the 20-minute working page feel alive, honestly: every motion is triggered by a real event (a new version, a check passing, ready).

## 0. A fixture page so motion can be recorded without signing in
- `app/dev/motion/page.tsx`: renders **the real working and ready page components** (extract them from `app/design/[id]/page.tsx` into `components/design/WorkingPage.tsx` and `ReadyPage.tsx` taking a `design` prop; the route keeps its Convex query and passes the result through) with fixture data from `public/fixtures/knob-design.json`, versions `[{n:1, name:"knob", glbUrl:"/fixtures/knob-v1.glb"}, {n:2, …"/fixtures/knob-v2.glb"}]`, final `/fixtures/knob-final.glb`, front `/fixtures/knob-front.png` (files supplied by the brain under `public/fixtures/`; add them to git).
- A `?play=1` mode advances a scripted timeline (queued 2 s → designing, version 1 at 6 s, version 2 at 12 s, checking at 16 s with the three checks ticking, rendering 20 s, ready 24 s) so a 30 s recording shows everything. `?state=working|ready&v=N` jumps to a state.
- The route returns `notFound()` unless `process.env.NEXT_PUBLIC_DEV_FIXTURES === "1"`; never set that on Railway. Not linked from anywhere.

## 1. Motion spec (working page)
- **New version arrives**: the viewer keeps the previous version until the new GLB has loaded, then the new part "prints in": a three.js clipping plane rises from the bed to the top over 1.4 s (ease-out), with a thin accent-coloured (`--accent`) horizontal line at the clip height; the old version cross-fades out during the first 300 ms. Implement as a `revealKey` prop on `ModelViewer` (changes → replay). The tablet header label ("knob · version 2") crossfades.
- **Version chips**: the new chip slides in from the right (240 ms, ease-out) and takes the accent state; the previous current chip settles to the done style. The dashed "next" chip breathes (opacity 0.5→0.8, 2 s loop).
- **Mascot beats**: on each new version, `Mascot` plays `presenting` once, then returns to `working`/`printing`; on `checking` → `checking`; on ready → `done` → reveal → tablet (existing). Extend `nextClip.ts` with a one-shot `beat(state)` that returns to the previous loop; no new video clips.
- **Steps card**: a step turning done fills its dot with a 300 ms scale-in and draws a 12 px tick (SVG stroke-dashoffset, 250 ms); the current dot keeps the pulse.
- **"What it's doing"**: a new line slides up 8 px + fades in (200 ms); the oldest line fades out; max 4 lines.
- **Elapsed**: ticks every second (exists); the "usually X–Y min" label stays static.
- **Tablet loading** (before version 1): the waiting placeholder shows a slow scan line (accent, 3 s loop) instead of a static message.
- Everything respects `prefers-reduced-motion: reduce` → instant state changes, no loops except the mascot video (which already stops on reduced motion? check; if not, show its poster frame).

## 2. Ready page
- On ready: quote rows stagger in (60 ms apart, 200 ms each); the download rows lift 2 px on hover with a 120 ms transition; the "final" chip gets the teal state with the same slide-in.
- The tablet dials keep working; the transform clip stays.

## 3. Landing (small)
- Hero tablet card: crossfade between `/examples/knob.png` and the same image with the "print-in" line effect every 4 s is NOT wanted — instead a single subtle loop: the accent scan line sweeps the render once every 6 s. Nothing else on the landing changes.

## 4. Tests and proof
- Unit (vitest): `revealKey` change replays the reveal (mock the animation clock); chips get the enter class on a new version; `beat()` returns to the previous loop; reduced-motion disables loops; fixture route 404s without the env flag.
- **Recording is mandatory**: with `NEXT_PUBLIC_DEV_FIXTURES=1 run-limited npx next dev -p 3999` (no Clerk needed for `/dev/motion` — make sure the route is outside the Clerk-protected matchers in `proxy.ts`, and that `ConvexClientProvider`/`ClerkProvider` tolerate the page: wrap the fixture page in its own minimal layout if the root layout's providers throw without keys), record `/dev/motion?play=1` at 1280×800 and 390×844 with Playwright `recordVideo` (reduce-motion OFF), 30 s each, into `spec/motion/working-desktop.webm` and `working-mobile.webm`, plus `ready-desktop.webm`. The brain `/watch`es them.
- `run-limited npx vitest run`, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
- No self-review, merge or push. Report RED/GREEN, file:line, recording paths, and anything not verified.
- No new dependencies (three.js is present; CSS keyframes for the rest). Keep the GLB-first rule: never replace the real version with a fake animation.
- Extracting the page components must not change behaviour: the existing page tests keep passing unchanged.
