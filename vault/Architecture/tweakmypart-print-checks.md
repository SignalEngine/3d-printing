# TweakMyPart: host print checks: strength, supports, restart recovery

Live since 23 Sep 2026 (printtweak #89, #90; 3d-printing #8).

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

## Deploy notes
- Host and sandbox image must ship together (the `checks.json` contract changed).
- Rebuild only the job image when the proxy is unchanged: `setup_network.sh` also recreates the proxy, which
  breaks any running job container (other sessions run bench jobs on the same network).
- Next: support fins download (`vault/Plans/2026-09-23-support-fins-option.md`), then stage 2 auto-orient.
