# TweakMyPart: predict the build cost before "Approve and build", price it at cost + 40 % (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/price-prediction`, cut from `origin/master` (≥ 124b352). Real `node_modules` (check `[ -L node_modules ]`; `next dev --webpack`). Never touch `/root/printtweak`, the service, Convex env, `/etc/printtweak/*`, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Run `python3 /root/.claude/scripts/surface-sweep.py approveBrief FILE_PRICE_PENCE costSummary designCosts jobUsd typesafe "Approve and build" quotedPricePence --out spec/surfaces.md` and account for every hit. TypeSafe: mock in tests (the conftest fixture already blocks the API); the key is only in the worker's env — Convex cannot call TypeSafe, so any TypeSafe scoring runs on the worker (see §1).

## Why (James, 22 Sep 00:20)
"We will want dynamic pricing and price prediction before they click go on the build. If it costs us £3 to build we charge enough to profit by 40 percent, rounded up to the nearest 10p." Tonight's real numbers: wall clamp $3.06 build + ~$0.14 brief ≈ £2.55; caddy $2.83 with a failed attempt; single knobs ≈ $0.6–0.9.

## Pricing rule — `convex/lib/pricing.ts`
`buildPricePence(predictedUsd)`: `gbp = predictedUsd × USD_TO_GBP × 1.4`, rounded UP to the nearest 10p, floor £2.00 (a tiny knob still costs a brief + a build). Export the constants (`MARGIN = 0.4`, `ROUND_PENCE = 10`, `FLOOR_PENCE = 200`) and a pure `roundUpTo10p`. Unit-test the rounding (£2.55 → £3.60; £2.549 cost × 1.4 = £3.5686 → £3.60; £1.00 → £2.00 floor).

## 1. Prediction — where the numbers come from
Predicted AI cost in USD for a design = `brief cost so far (actual, from its jobs)` + `predicted build cost`. Predicted build cost, computed on the HOST when the brief is reported (`worker/worker.py process_brief`, before `reportBrief`) so the number is already on the design when the customer sees the concepts:
- **Base**: median actual `costUsd` of the last 30 READY designs' successful `design` jobs, bucketed by the chosen concept's declared part count (1 / 2 / 3+; the brief's concept gains `parts: n` — add it to the concept schema and the prompt: "how many separate printed pieces this approach needs"). Fewer than 5 samples in a bucket → fall back to the all-bucket median; none → the fixed table `{1: 0.9, 2: 1.8, 3: 3.0}` USD.
- **Complexity multiplier** from one TypeSafe `score` question on the concept's `how` + the request ("how mechanically complex is this to model: simple solid / a few features / mating parts or moving parts / threads or mechanisms"), levels → ×1.0 / ×1.2 / ×1.5 / ×1.8. API down → ×1.3.
- **Failure allowance**: × (1 + failed-build rate over the last 30 designs, capped at 0.5).
- Store per concept: `concepts[i].predictedUsd` and `concepts[i].pricePence` (= `buildPricePence(brief cost so far + predictedUsd)`), plus `design.quotedPricePence` once the customer picks a concept (`pickConcept` copies it; `approveBrief` refuses if missing when concepts exist). The quoted price is binding: the actual cost is recorded beside it, never re-charged.

## 2. What the customer sees — `components/chat/BriefChat.tsx`
- Each concept card shows its price chip: "£3.60 to build" (a muted "est." tooltip-free suffix, e.g. `£3.60 · est.`). The recommended card can be dearer; say nothing about cost in the `why`.
- The Approve step says **"Approve and build · £3.60"**. When payments are off (personal mode today) the button reads "Approve and build · £3.60 (free while testing)" so James can check the predictions. No Stripe work in this build.
- The ready page's price card (admin Cost card) shows quoted vs actual and the margin actually made.

## 3. Admin accuracy — `convex/admin.ts`, `/admin/costs`
- `costSummary` adds `prediction: { n, mape, medianAbsErrUsd, under: count, over: count }` over ready designs that have both numbers, and a small "Predicted vs actual" table (last 10: name, predicted, actual, quoted price, margin made). Margin made = quoted price − actual cost × USD_TO_GBP.

## Tests and proof
- Pricing unit tests (rounding, floor, margin). Prediction: bucket medians, fallbacks, multiplier mapping, failure allowance, API-down path (mocked TypeSafe) — worker pytest. Convex: concept `parts`/`predictedUsd`/`pricePence` validated and sanitised in `reportBrief`; `pickConcept` sets `quotedPricePence`; `approveBrief` refuses without it when concepts exist; admin accuracy numbers on a seeded set.
- Chat: price chips on cards, the Approve label, fixture `/dev/motion?state=chat` updated; screenshot `spec/motion/chat-prices-390.png`.
- Sandbox: none needed (the brief prompt gains one field — check `parse_brief` accepts a missing `parts` on old shapes and defaults to 1).
- `run-limited npx vitest run`, worker pytest, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, anything not verified; Convex changes (deploy), worker + prompt changes (image rebuild + worker restart). No new dependencies. Do not touch Stripe/payments flags.
