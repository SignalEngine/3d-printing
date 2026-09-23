# TweakMyPart lander — the robot gives the tour (23 Sep 2026)

Branch `build/lander-redesign` (printtweak). Comp: https://claude.ai/artifact/3JHaB9bjtmuX3WgfNWEKkY
Plan + 7 review rounds: `docs/2026-09-23-lander-tour-plan.md`, `docs/2026-09-23-lander-review-{1..7}.md`. Product record: `PRODUCT.md`.

## What it is
- Desktop (≥1024 px): content left, sticky stage right with the mascot at ≥80% of viewport height. `components/lander/useActiveSection.ts` picks the section; `lib/landerGuide.ts` maps section → mascot clip + speech bubble. Examples section swaps him for `TabletPreview`: the real GLB on his tablet, parts fly plate → assembly, gears turn (`ModelViewer` `spin` prop, speeds from `lib/gearSpin.ts`).
- Mobile: big waving robot in the first screen; tablet card with example pills; small poster "peeks" per section.
- Logo: robot head, `components/Logo.tsx`, favicon `app/icon.svg`.
- Hero form → `/design/new?q=…`; NewChat seeds its composer from `q` (never auto-sends).
- **Rule (James): the bubble never covers his face.** Head boxes live in `TabletPreview.tsx` (`HEAD_BOX`, `TABLET_HEAD_BOX`); `lib/bubblePosition.ts` places the bubble above him and shrinks the frame on short windows. Tests cover 1024×600 → 1440×900 in both poses.

## Examples are real builds
`scripts/lander/manifest.json` → `scripts/lander/ingest.py` (worker venv) builds assembled/plate GLBs with `worker.assembly`, reads print hours/grams + mechanics lines from `worker.gates.run_all`, spin from checks.json → `lib/landerExamples.json`; `scripts/lander/stills.mjs` renders stills. Builds came from `worker/tests/bench/run_bench.sh --image printtweak-job:latest` (production job image, no retry). Adapt requests: bench copies `requests/uploads/<uploadName>` into the job.
On the page (all passed every gate): 3-gear spinner, 3:1 gear pair with crank, screw-top jar, spool holder, basket wheel, cable clip, door hook, clip arm +10 mm (adapt), dog-paw jar keeping the original thread (adapt).
Failed first attempt (not shown): full planetary gearbox (max turns), planetary fidget, rack & pinion, tube squeezer, allen-key stand (vision).

## Found while building
- **Gear gate bug (live):** `worker/mechanics.py` centre distance is `m(za+zb)/2` for every pair, so ring gears (planetary) and racks always fail even when correct. Fix queued on its own branch (James, 23 Sep).
- The shared `ModelViewer` default part tint is now warm tan (James approved; changes the ready/working pages too).
- Headless Chrome on the VPS has no GPU (SwiftShader): creating the tablet's WebGL context blocks the main thread ~7 s there. Not seen on real hardware yet — phone check on staging pending.
- Staging Convex holds the unmerged fins schema (`fins3mf`); pushing another branch's Convex to staging fails schema validation. Web-only staging deploy: `railway up --project 2bea4410-… --environment staging --service printtweak-staging --ci <worktree>`.
