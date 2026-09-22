# TweakMyPart handover — 22 Sep 2026, 22:00

Written so a fresh session can pick this up cold. Read this, then `git pull` in `/root/3d-printing` and `/root/printtweak`.

## Live right now (tweakmypart.com)
- **Payments ON, sign-ups OPEN.** Stripe live keys on prod Convex `valiant-sockeye-361`. Always pass `--prod` to `npx convex env` — without it you are editing the DEV deployment (this cost an evening on 22 Sep).
- **Shipped today:** #84 thread/sketch rules, #85 downloads always shown, **#86 ask-before-changing**, **#87 ready-page entrance**. Both #86 and #87 were proven on staging before merge.
- **Billing: James's Claude subscription, NOT the API key** (James, 22 Sep 21:00 — "nobody else is on the site"). The proxy container runs with NO `ANTHROPIC_API_KEY`; `/etc/printtweak/proxy.env` is renamed `.disabled`; `/etc/printtweak/worker.env` has `PRINTTWEAK_AUTH=oauth`. **To switch back when real customers arrive:** rename the file back, recreate the proxy with `--env-file`, `docker network connect --alias proxy printtweak-jobs printtweak-proxy`, set `PRINTTWEAK_AUTH=api`, restart both lanes. The API key ran out of credit at ~18:20 today; James topped it up, so it works if switched back.
- **Proxy gotcha:** after recreating the proxy container you MUST run `docker network connect --alias proxy printtweak-jobs printtweak-proxy` or every job times out. `worker/setup_network.sh` does it; a hand-rolled `docker run` does not.

## In flight, not merged
**Branch `build/mechanisms-pack`** in two worktrees:
- `/root/wt-pt-mech` (printtweak) — 5 commits, head `91663ea`. Gear-mesh gate + snap-fit strength gate + the fixes below.
- `/root/wt-3dp-mech` (3d-printing) — **already merged to master** (`strength.py`, `mechanisms.md`), because the host gate reads the shared path `/root/3d-printing/skills/model-forge/`.

What it adds:
- `checks.json` gains `gears` (a, b, module, teeth_a, teeth_b) and `loads` (a clip/arm's dimensions + material + layer direction).
- Host gate `worker/mechanics.py`: centre distance vs `m(z1+z2)/2 + 0.05..0.5`, module ≥ 0.8, teeth ≥ 12, then a **coupled rotation sweep** that turns both gears together and fails on binding. It tries the tooth phases a real layout could have (half a tooth first) — a correct pair placed tooth-on-tooth used to read as binding.
- `skills/model-forge/scripts/strength.py`: cantilever strain and beam stress hand-calc. PLA 2 % one-time / 1 % repeated, PETG 4 % / 2 %, **halved when the arm prints upright**.
- **Undeclared multi-part designs now FAIL** (sandbox and host). `{"unrelated": true}` states parts that never touch. A snap-fit pill box shipped on 22 Sep with zero checks because silence used to pass.
- **The retry is told what the first attempt failed** (`previousFailures` in request.json → the prompt). It used to rebuild from the identical request and repeat the mistake.

**Gates so far:** verify-build PASS (vitest 510, worker pytest 416, tsc clean). review-gate (claude) ran three rounds: P1 merge-order, P1 flipped gear, P1 tooth phase — all fixed, plus P2s. **The jury has NOT run on the final diff — run it once before merge.**

**Blocking merge:** the staging proof. Two seeded builds must show real gear and strength lines:
- gear pair `j979qcd7zseshe5gcdkmz21mv18ew68y`, snap-lid `j97ewgb52hxeyxgwgrbfhr1sn98ew65a` (staging Convex `prod:reliable-hamster-614`).
- Evidence already obtained: the strength gate fired on a real part — *"Clip bends 0.44% (PLA limit 0.5%)"*. The gear sweep has not yet run on a real build (two attempts died for unrelated reasons: an empty API balance, then a proxy restart mid-run).

## How to run a staging test (the rule: nothing goes live unproven)
```
bash /root/printtweak/scripts/stage-deploy.sh <worktree>          # Convex + Railway + worker checkout
# sandbox image is NOT built by that script. For worker/job changes:
cp -r <worktree>/worker/job $C; cp -r /root/3d-printing/skills/model-forge $C/model-forge
cp -r /root/3d-printing/orcaslicer $C/orcaslicer; docker build -t printtweak-job:staging $C
```
Seed a design + job with `CONVEX_DEPLOYMENT=prod:reliable-hamster-614 npx convex import --append`.
Staging worker: `printtweak-worker-staging`, checkout `/root/printtweak-staging`, env `/etc/printtweak/worker-staging.env` (has `PRINTTWEAK_JOB_IMAGE=printtweak-job:staging`).
Railway uploads to staging are slow (30 min) and sometimes time out; the worker part can be done by hand: `git -C /root/printtweak-staging checkout --detach <sha> && systemctl restart printtweak-worker-staging`.

## Known bug, not yet fixed (worth doing early)
**Restarting a worker orphans its running job.** The build container keeps running with nobody listening; the job row stays `running` for 40 minutes until `claimNext`'s stale sweep marks it `worker_lost`. This ate two of James's live tweaks today (14:35, 17:39) and one staging run. Fix: on shutdown, stop the container and hand the job back to `queued`.

## Next build, agreed with James (in this order)
1. **Print orientation, strength and supports, checked together.** Today the strength gate trusts a `layers: along|across` label the model writes. Derive it instead: the part declares the direction its load acts in, and the host computes the layer penalty from that direction and the print orientation. Same slice run can report support material, so "designs that need fewer supports" becomes a measured number, not a hope. James's yarn holder **snapped** — the layer-line failure this would catch. (James, 22 Sep: "how it's printed and strength… we also need to take into account designing prints that need less supports".)
2. The worker-restart orphan bug above.
3. Measure the remaining MakerWorld models: the planetary gear spinner times out in `measure_mechanism.py` (heavy mesh), and the hinged box's gaps are unusable because the tool cannot yet tell a touching hinge from a badly split body.

## Knowledge added today (already committed)
- `skills/model-forge/references/mechanisms.md` — 37 rules: gears, hinges, snap fits, bearings, flexures, print-in-place, gyroscope, gear bearing, mid-print inserts. **Corrected from James's real prints:** rings that rotate on each other need 0.7 mm (not 0.4), and a snap-in ball joint is modelled touching.
- `vault/Research/2026-09-22-print-in-place-mechanisms.md` — sourced numbers behind those rules.
- `vault/Research/2026-09-22-measured-real-models.md` — what the downloaded models actually measure, and the tool's limits.
- `vault/Research/2026-09-22-ai-cad-competitors.md` — AiCadGen, Ragnar, Zoo, PrintPal are competitors; Scenario PartCrafter is not (it is a mesh part-splitter, open source, the only one usable as a component). **Pricing pressure is real:** PrintPal is about 24p a part, our floor is £2.
- `skills/model-forge/scripts/measure_mechanism.py` on branch `build/measure-mechanism` in `/root/wt-3dp-measure` — **not merged**. Measures gaps, walls and gear teeth from a downloaded model. Validated against gears of known size (16 @ module 2.0 → read 16 @ 1.96).

## Standing rules that bit today
- Never claim done from a builder's report: run `verify-build <worktree>` yourself, then the gates.
- `/jury` once per PR on the final diff (OpenRouter is real money). review-gate for fix rounds; pass builder `codex` to get a Claude reviewer (Codex is capped until 24 Sep).
- The brain reviews the builder's work, never the builder itself.
- Everything James decides goes through an options prompt, never a prose question.
