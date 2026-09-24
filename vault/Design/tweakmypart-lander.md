# TweakMyPart lander — the robot gives the tour (23 Sep 2026)

Branch `build/lander-redesign` (printtweak), merged as PR #93 (`d121202`, 23 Sep). Comp: https://claude.ai/artifact/3JHaB9bjtmuX3WgfNWEKkY
Plan + 7 review rounds: `docs/2026-09-23-lander-tour-plan.md`, `docs/2026-09-23-lander-review-{1..7}.md`. Product record: `PRODUCT.md`.

## What it is
- Desktop (≥1024 px): content left, sticky stage right with the mascot at ≥80% of viewport height. `components/lander/useActiveSection.ts` picks the section; `lib/landerGuide.ts` maps section → mascot clip + speech bubble. Examples section swaps him for `TabletPreview`: the real GLB on his tablet, parts fly plate → assembly, gears turn (`ModelViewer` `spin` prop, speeds from `lib/gearSpin.ts`).
- Mobile: big waving robot in the first screen; tablet card with example pills. Six later sections open with a large Tweak and a coloured speech bubble beside him in the page flow (PR #103). Each pose has a still poster and an MP4 loop that starts when the section is visible, pauses offscreen, and remains a still when reduced motion is requested. The fixed floating guide was removed after James saw it cover content and look transparent on his phone.
- Logo: robot head, `components/Logo.tsx`, favicon `app/icon.svg`.
- Hero form → `/design/new?q=…`; NewChat seeds its composer from `q` (never auto-sends).
- **Rule (James): the bubble never covers his face.** Head boxes live in `TabletPreview.tsx` (`HEAD_BOX`, `TABLET_HEAD_BOX`); `lib/bubblePosition.ts` places the bubble above him and shrinks the frame on short windows. Tests cover 1024×600 → 1440×900 in both poses.

## Examples are real builds
`scripts/lander/manifest.json` → `scripts/lander/ingest.py` (worker venv) builds assembled/plate GLBs with `worker.assembly`, reads print hours/grams + mechanics lines from `worker.gates.run_all`, spin from checks.json → `lib/landerExamples.json`; `scripts/lander/stills.mjs` renders stills. Builds came from `worker/tests/bench/run_bench.sh --image printtweak-job:latest` (production job image, no retry). Adapt requests: bench copies `requests/uploads/<uploadName>` into the job.
On the page (all passed every gate): 3-gear spinner, 3:1 gear pair with crank, screw-top jar, spool holder, basket wheel, cable clip, door hook, clip arm +10 mm (adapt), dog-paw jar keeping the original thread (adapt).
Failed first attempt (not shown): full planetary gearbox (max turns), planetary fidget, rack & pinion, tube squeezer, allen-key stand (vision).

## Chat sketches
Real output of the product's concept step (bench `kind: brief`, request "a hook to hang my headphones under my desk") in `lib/landerBrief.json`, rendered as `<img>` data URLs via `lib/sanitizeSvg.ts`. The first version used dev-fixture placeholder SVGs; James: "I have no idea what's going on in them".

## Found while building
- **Gear gate bug (live):** `worker/mechanics.py` centre distance is `m(za+zb)/2` for every pair, so ring gears (planetary) and racks always fail even when correct. Ring gears fixed by #92. **Racks fixed by #97 (shipped 23 Sep 11:21):** gears row `"rack": true`, rack origin on its pitch line, +X length, +Y teeth; host sweeps pinion turn + rack slide. Proven end to end: a real rack & pinion build passed ("Rack meshes: pinion 15t, 0.3 mm backlash, turns freely"). Prod ship = pull /root/printtweak, build printtweak-job:latest from a temp copy (NOT setup_network.sh — it recreates the shared proxy), restart printtweak-worker + -brief.
- The shared `ModelViewer` default part tint is now warm tan (James approved; changes the ready/working pages too).
- **Phone scroll jank = the live 3D tablet (confirmed on James's phone, 23 Sep).** A temporary `?diag` overlay with per-suspect switches proved it: smooth with 3D off. Fix: on phones the tablet shows `still.png` while scrolling; "Spin it in 3D" mounts the live viewer (no WebGL until tapped). Desktop keeps live 3D at pixel ratio ≤1.5. Lesson: headless SwiftShader numbers pointed the right way but only the device proved it; build the switch-board diag on round one.
- Staging Convex holds the unmerged fins schema (`fins3mf`); pushing another branch's Convex to staging fails schema validation. Web-only staging deploy: `railway up --project 2bea4410-… --environment staging --service printtweak-staging --ci <worktree>`.

## Phone review rounds 9–11 (PR #101, 23 Sep)
- Mascot is named **Tweak**. The phone hero plays `hello` once, then idles without the arm-across-chest `idle-3` clip. `components/mascot/Mascot.tsx` uses `endedRef` so React StrictMode cannot re-pick a clip that is still playing and interrupt the wave.
- Chat concepts are labelled sketches from the real brief flow (#98). The chat steps have large numbered headings and short supporting lines. Adapt examples were replaced with changes visible in a before/after view; the lightbox lets visitors rotate real GLBs. Pricing cells are links; the closer uses a dark band.
- `scripts/lander/turntables.mjs` pre-renders 36-frame WebP turn sprites for adapt pairs and workshop tiles, and 8-second MP4 assembly/turn loops for featured examples. The phone tablet plays a loop until “Spin it in 3D” mounts WebGL. The screw-jar lid screws on in its loop. The stills renderer hides development overlays so the Next “N” badge is absent from posters.
- Basket wheel was removed; rack and pinion was added after the gear gate fix (#97). The gear pair starts handle-front (`yaw0`). Tapping the live 3D tablet after “Spin it in 3D” opens the large lightbox, as do adapt pairs and workshop tiles. A real sideways drag stops auto-turn; vertical scrolling does not.
- The round-11 floating phone guide was retired in PR #103 (`f22c552`, 24 Sep). `components/lander/SectionGuide.tsx` puts Tweak and his contrasting speech bubble in each phone section. The six sections use `listening`, `presenting`, `point`, `focus` and `thinking` poses; the examples bubble follows the selected example. MP4 loops load only when a guide enters view (35% threshold), pause offscreen and yield to still posters under reduced motion. The poster/video uses `mix-blend-mode: screen` on the page ground to remove its black background without fading Tweak. Desktop does not load these clips.
- James's 24 Sep phone recording asked to remove the static “More from the workshop” gallery because it did not show motion or allow interaction. PR #103 removed it; the rotating, tappable featured examples remain. The gallery can return when there are real user examples to show.

## Hero idea box + upload tiles (PR #105, 24 Sep)

James: the first box should take an idea; uploading a photo or model is a main feature and needs obvious buttons; the hero must say both "tweak an existing part" and "idea factory".

- H1 "Tweak a part you've got. / Or invent one from an idea.", eyebrow "AN IDEA FACTORY FOR 3D PRINTS".
- Multi-line idea box directly under the H1 (phone mascot moved below it). "Add a photo" / "Upload a model" tiles + drag-and-drop, on phone and desktop.
- File handoff to `/design/new`: a GET form can't carry a File and signed-out visitors go through Clerk's hosted sign-in (full reload), so `lib/pendingUpload.ts` parks it in IndexedDB under a UUID token that rides in `?upload=`. Submit awaits the write; `/design/new` takes it once, per token (two tabs keep their own); entries older than 1 h are pruned. If the write fails, the hero stays put and says so.
- Live `37b4c36`, Railway deploy `fba152d5` SUCCESS; checked at 1440 and 390: both tiles visible above the fold, 0 overflow, 0 console errors.
