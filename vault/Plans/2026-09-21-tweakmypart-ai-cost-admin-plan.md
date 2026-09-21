# TweakMyPart: what each model costs us in tokens (admin), and hide printing/posting for now (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/ai-cost-admin`, cut from `origin/master` (≥ 8bc6aee). Real `node_modules` (check `[ -L node_modules ]`; `next dev --webpack`). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Run `python3 /root/.claude/scripts/surface-sweep.py costUsd printPricePence "Print + post" hours grams FILE_PRICE_PENCE requireAdmin funnel --out spec/surfaces.md` and account for every hit. Another builder is editing `components/prints/PrintCard.tsx` and `TabletPreview.tsx` on a sibling branch — do NOT touch those files; hide card fields server-side in `listMine` instead.

## Why (James, 21 Sep 22:40)
"For now we will just charge for model download, not printing, so I want to know the cost token-wise for the model creation only. Hide details about printing and posting until we are sure about the costs." Every job row already has `costUsd` from the sandbox (brief, design, tweak, retry) but nothing adds it up per design or shows it anywhere; TypeSafe calls are not costed at all.

## 1. Cost per design — `convex/admin.ts` (new), `convex/worker.ts`, `convex/schema.ts`
- `jobs` gains `tokens?: { input, output, cacheRead? }` when the sandbox reports them (extend `result.json`/`reportResult`/`reportBrief` payloads — `run_job.py` already has the SDK result usage; pass it through if present, else leave undefined). TypeSafe usage from `worker/typesafe.py` is written to the job as `typesafeUsd` (input tokens × $42/1e9, output at the same rate unless the docs say otherwise; cite the page in the code comment).
- `admin:designCosts({ designId })` (admin only, `requireAdmin` pattern from `convex/lessons.ts`): `{ jobs: [{ kind, state, costUsd, typesafeUsd, tokens, minutes, startedAt }], totalUsd, totalGbp (USD_TO_GBP from limits), filePricePence, marginGbp }`.
- `admin:costSummary({ days })`: per day and overall: designs started, ready, failed; total USD; median and p90 USD per READY design (brief + design + tweaks + retries + typesafe); median minutes; top 5 most expensive designs (id, name, USD, why: attempts/tweaks). Cap the scan at 2,000 jobs.

## 2. Admin pages — `app/(main)/admin/costs/page.tsx`, and a "Cost" panel on the design page for admins
- `/admin/costs`: the summary table (last 7 / 30 days toggle), the top-5 list linking to designs, and one line "Download price £5 vs median AI cost £X → margin £Y per ready design". Plain `card` styling like the funnel page; phone-safe (no horizontal overflow at 360 px).
- On `/design/[id]` when the signed-in user is an admin (`ADMIN_EMAILS`, same check the funnel uses): a collapsed "Cost (admin)" card under "What happened": each job with kind, minutes, USD, TypeSafe pennies, tokens; total; margin vs £5. Never rendered for non-admins (test it).

## 3. Hide printing and posting for now — `convex/designs.ts` (`get`, `listMine`), `components/design/ReadyPage.tsx`, `components/PartDownloads.tsx`
- A single server-side flag `SHOW_PRINT_QUOTE` (env, default off): when off, `designs.get` returns `quote: null`-equivalent for the customer (keep `pieces`), `listMine` returns `grams`/`hours` as null; the ready page shows "N pieces" but no "PLA · h · g" line and no "Print + post … coming soon" row. The download buttons stay. When on, everything renders as today. Admin still sees the real quote in the Cost card.
- Turnaround estimate (print time + queue + 1 working day) is NOT built now — record it in `vault/Plans/…` as the next step; James chose it for later.

## Tests and proof
- Convex: `designCosts` sums jobs incl. typesafeUsd and is admin-only; `costSummary` medians/p90 on a seeded set; `get`/`listMine` hide the quote when the flag is off and show it when on.
- Worker: tokens/typesafeUsd reported (mocked SDK result + mocked typesafe).
- Pages: `/admin/costs` renders the summary; non-admin gets the same refusal the funnel gives; the design Cost card only for admins; ready page without the print rows when hidden.
- Screenshots `spec/motion/admin-costs-390.png`, `admin-costs-1280.png`, `ready-no-print-390.png`.
- `run-limited npx vitest run`, worker pytest, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, anything not verified; Convex changes (deploy), worker/run_job changes (image rebuild + worker restart). No new dependencies. Do not touch `PrintCard.tsx` or `TabletPreview.tsx`.
