# Builder handover: TweakMyPart, pieces count and per-piece print rule

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/pieces`, cut from `master`. Real `node_modules`. Site is live: do not touch `/root/printtweak`, the service, Convex env, or run convex deploy/dev against prod (anonymous codegen only; delete `.convex/` and `.env.local` before committing).

James's decision (15 Sep, after the first multi-part design): show pieces, not designs, and apply the print refusal per piece.

## Build
1. `convex/lib/pricing.ts` `printQuote`: when `quote.parts` exists, evaluate the 8 h / 150 g refusal per piece (each part's own `hours`/`grams`, i.e. one piece, not `count` × part); refuse only if any single piece exceeds a limit, and return `printRefusal: "too_long" | "too_heavy"` plus `refusedPart: name`. The price when allowed sums over pieces (`hours * count`, `grams * count`). Single-part quotes (no `parts`) unchanged. Tests: pill box shape (tray 8.9 h ×1, lid 1.5 h ×4) → refused, refusedPart "tray"; a 2-part box with 3 h + 3 h → allowed and priced on the total; legacy single quote unchanged.
2. `designs.get`: expose `pieces` = sum of `count` over parts (1 for legacy) and `designsCount` = parts length.
3. Page `app/design/[id]/page.tsx`: quote line "Print time 14.9 h · 122 g of PLA · 5 pieces (2 designs)"; for one part: "1 piece". Refusal text names the piece: "Too big to print for you: the tray takes over 8 hours. The files are yours to print." Part rows show "lid ×4".
4. Tests: pricing unit tests above; `designs.get` pieces; page renders the pieces line and the named refusal (jsdom test on a small presentational component, like `PartDownloads`).

## Hard rules
- `[ -L node_modules ]` before npm; `run-limited` for heavy commands; no secrets; no root GATES.md.
- Tests RED then GREEN; full vitest + `npx tsc --noEmit` green (worker untouched).
- No self-review, merge or push. Report RED/GREEN and file:line.
