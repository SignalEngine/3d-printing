# TweakMyPart: host print checks: strength, supports, restart recovery

Live since 23 Sep 2026 (printtweak #89–#92, #94–#96; 3d-printing #8).

## Strength follows the print direction (#90)
- `checks.json` `loads` rows declare `axis` = the arm's length direction in the part's own coordinates. Parts
  print as modelled (Z up), so that is the print direction too. The old model-written `layers` label is gone.
- Host (`worker/mechanics.py _layers_from_axis`): unit axis with |z| > 0.5 (rises > 30° off the bed) → `across`
  → half the strain/strength budget in `strength.py`. The mechanics line says "printed flat/upright".

## Supports are measured (#90)
- Host slices every part with `slice_gate.py --supports tree`. `support feature blocks` > 0 → a second slice
  without supports gives `supportGrams`. Blocks without a readable delta still count as needing supports (0.1 g).
- `quote.parts[].supportGrams` is stored in Convex (validator + schema).
- **Retry once, then ship:** if attempt 1 passes every check but needs supports, attempt 2 is told
  "needs N g of supports — redesign…" and the customer log says "It needs print supports — redesigning…".
  The attempt with fewer support grams ships (attempt 2 on a tie). Any attempt-2 failure ships attempt 1.
  Supports never fail a job.
- Ready page: one "Checked:" line per part, either "prints without supports" or "needs tree supports (about N g)".
- Staging proof (23 Sep): T-shaped post, attempt 1 needed supports (0.6 h, 6 g). The retry printed support-free
  (0.3 h, 3.8 g).

## Supports retry respects the customer (#95)
- A part needs supports only at >= 1 g (`SUPPORT_RETRY_THRESHOLD_G`), judged per part. Below that: "prints without
  supports", no retry, no fins. **Unproven by a print**: settle it with one real print of a 0.5–0.9 g part.
- Before the retry, one TypeSafe judgment ("accepted") over the request (approach + answers): accepted -> ship attempt 1.
  TypeSafe off/failing -> retry as before. Staging proof: the T-post (2.2 g, "supports are fine") shipped in about 2 min
  with no redesign, where the jack took about 20 min with a redesign.
- `_tail_log` sends "Still working on it — N min so far" after 60 s of silence (tests only, not yet seen live), and drops
  narration that starts lowercase or has < 3 words (cut-off model remarks). Host check lines never pass through it.

## Question answers survive a reload (#96)
- `designs:saveAnswer` stores each answer in `brief.draftAnswers` as it is given (owner-only, brief stage, chosen
  approach's question ids only, 200 chars). BriefChat seeds its progress from it. Staging proof: answered, reloaded,
  and the answer was still shown with the next question live.

## Staging deploys prove the commit (#94)
- `/api/version` returns the build commit (Railway git SHA on live; `public/build-sha.txt` written by stage-deploy for
  `railway up`). `stage-deploy.sh` polls it until it matches HEAD, and warns when another worktree deployed within 60 min
  (`/tmp/tweakmypart-stage-last`). Live check: `curl https://tweakmypart.com/api/version`.
- Staging is ONE shared site: another session's deploy replaced mine 2 min later on 23 Sep. Say on the session board
  before deploying.

## Stale sweep keys on last activity (#90)
`claimNext` fails a `running` job as `worker_lost` 40 min after `max(startedAt, stageAt)`, not after the claim.
Every log line refreshes `stageAt`, so a live two-attempt build is never swept.

## Restart recovery (#89)
- Job containers carry `--label printtweak.lane=<lane>`: `all` (main), `brief`, `staging-all`.
- A job stores `lane` when claimed. At startup a worker kills its own lane's containers, confirms none survived,
  then `worker:releaseLane` requeues its running jobs. After the 3rd release the job is failed and refunded
  instead (a job that crashes the worker cannot loop).
- Proven on staging: the planted orphan was killed within 1 s, the decoy with another label was untouched, and
  the job was requeued and reclaimed.

## Built-in support fins download (#91)
- Engine: Support Fins by gittrahan (MIT, printfins.com), vendored unmodified @ 8d3bd0e in `worker/fins/engine/`,
  run headless by Deno (`worker/fins/run_fins.js`, sandboxed to a scratch dir): stabilize mode (tines on), bed pad on.
- For every shipped part with `supportGrams > 0`, `worker/fins_pipeline.py build_fins` makes a 3MF with the fins as a
  separate object. It is kept only if: 0 unserved overhangs, not seated on a point, every body watertight, it slices with
  supports off, and every fin wall (picked by SHAPE: >= 3 mm tall and long) has its own extrusion in the gcode.
- **OrcaSlicer rotates parts when it places them** (a jack was turned 45°). `slice_check.py` maps gcode back through
  the build-item transform in the sliced 3MF. Translation-only registration found 0 fin extrusions and silently
  dropped the download.
- Every decline logs `fins declined: <reason>` to the worker journal (`journalctl -u printtweak-worker`).
- Stored as `files.parts[].fins3mf`; PartDownloads shows "With built-in fins — print with supports off" plus the credit.
- Staging proof: the 3D cross shipped with a fins 3MF (part + fins objects, slices supports-off 0.73 h / 7.8 g).
  **Not yet printed.** James's A1 print is the real test.
- Payoff is small at the modelled orientation (the cross: fins ~2 g vs supports 0.3 g). The big wins come from tilted
  strong orientations (the author measured a bracket going from 25 h to 10 h), i.e. stage 2 auto-orient.

## Ring / planetary gears (#92)
- `gears` rows take `"internal": true` (b = ring, teeth_b > teeth_a, gap >= 10 teeth).
- Centre = m(zb-za)/2 with the backlash **inside** it (-0.5..-0.05 mm). Moving the planet outward drives it into the ring's
  teeth. Measured on a real 40T m2 ring + 16T planet: overlaps at nominal+0.2, clears at nominal-0.2.
- The sweep turns planet and ring the same way. Real fixture: `worker/tests/fixtures/mech/ring-40.3mf`.

## Deploy notes
- Host and sandbox image must ship together (the `checks.json` contract changed).
- Rebuild only the job image when the proxy is unchanged: `setup_network.sh` also recreates the proxy, which
  breaks any running job container (other sessions run bench jobs on the same network).
- Next: stage 2 auto-orient (reuse `worker/fins/engine` orient.js `suggestStrengthPose` — not vendored yet), then James prints a finned part.
