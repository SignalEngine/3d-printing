# TweakMyPart: "My prints" — find every design again (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/my-prints`, cut from `origin/master` (≥ PR #68). Real `node_modules` (check `[ -L node_modules ]`; `next dev --webpack` in a worktree). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), committed last. Load `impeccable`'s `reference/craft-floor.md` and `emil-design-eng` before UI code. Run `python3 /root/.claude/scripts/surface-sweep.py listMine AuthBar site-header designs.get files.front quote status --out spec/surfaces.md` and account for every hit.

## Why (James, 21 Sep 21:00)
"It made a nice print but then I lost it. Can we have a My prints area please?" There is no page that lists a customer's designs; the only way back is the URL.

## What the customer sees
1. **`/prints`** (route group `app/(main)/prints/page.tsx`, signed-in only; signed-out → the sign-in prompt the other pages use). Heading "My prints". A responsive grid of cards (1 column ≤ 480 px, 2 ≤ 900 px, 3 above), newest first. Each card: the front render (`files.front` → a storage URL; the assembled render if that is what the ready page shows — use whatever `designs.get` would give as the picture; a neutral placeholder tile with the mascot's small avatar when there is none yet), the design name (the same `designNoun` rule the ready page uses, else the first line of the request truncated to 60 chars), a status pill (Thinking · Questions · Building · Ready · Failed · Declined, colour from the existing status tokens), the date (`Today 16:24`, `Yesterday`, `21 Sep`), and for ready designs one line `3 pieces · 37 g · 1.8 h`. The whole card links to `/design/[id]`. Ready cards get a small **Download 3MF** (single part) or **Download all (zip)** (multi) shortcut using the same `saveAs` path as `PartDownloads`.
2. **Header**: "My prints" link in `AuthBar` next to "Design my part" when signed in (desktop and phone; on phones keep it to an icon+label that fits with the two buttons — check 360 px). Also a "My prints" link at the top of the ready page beside the heading ("← My prints").
3. **Empty state**: the mascot `idle` small, "Nothing here yet. Design your first part." with the button.
4. Nothing else: no delete, no rename, no search (say so in the report if you think one is needed).

## Data
- `designs:listMine` returns whole rows today; change it to return only what the cards need: `{ _id, status, createdAt (_creationTime), name (computed: designNoun of files.parts names, else request first line), frontUrl (storage URL, null if none), pieces, grams, hours, partDownloads (ready only: names + 3MF urls) }`, newest first, capped at 100. Do not leak other users' rows (the `by_user` index already scopes it; test it).

## Tests and proof
- Convex: `listMine` shape, newest first, only the caller's designs, cap.
- Page: cards render each status, links go to the design, download shortcut only on ready, empty state, signed-out state.
- Fixture `/dev/motion?state=prints` (six designs across statuses) — screenshots at 360, 390, 1280 px in `spec/motion/prints-*.png`, no horizontal overflow; one recording `spec/motion/prints-mobile.webm` scrolling the grid and tapping a card (reduce-motion OFF).
- `run-limited npx vitest run`, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Report RED/GREEN, file:line, screenshot paths, anything not verified; Convex changes (deploy). No new dependencies. Every control labelled, focus visible, contrast ≥ 4.5:1, tap targets ≥ 44 px.
