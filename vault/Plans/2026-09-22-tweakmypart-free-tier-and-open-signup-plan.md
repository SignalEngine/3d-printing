# TweakMyPart freemium build 2: free-tier limits, pricing page, open sign-ups switch, legal pages (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/free-tier-open-signup`, cut from `origin/master` (after PR #76, Stripe pay-per-build). Real `node_modules` (check `[ -L node_modules ]`; `next dev --webpack`). Never touch `/root/printtweak`, the service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only). `run-limited` for heavy commands. `GATES.md` before code (`/unlazy tree N`), **committed** (commit your work; the ledger last). Load `impeccable`'s `reference/craft-floor.md` and the `copywriting` skill before the pricing page. Run `python3 /root/.claude/scripts/surface-sweep.py ALLOWED_EMAILS isAllowed requireUser reviseBrief create briefRevisions FREE_DESIGNS canStartDesign quotedPricePence --out spec/surfaces.md` and account for every hit.

Spec (approved): `/root/3d-printing/vault/Plans/2026-09-22-tweakmypart-freemium-spec.md`. Go-live checklist: `/root/3d-printing/vault/Plans/2026-09-22-tweakmypart-go-live-checklist.md`.

## 1. Free question rounds: 10 per calendar month (`convex/users.ts`, `convex/designs.ts`, `convex/lib/limits.ts`)
- A "question round" = one brief job: `designs.create` and `designs.reviseBrief` each count one. Stored as `users.roundsMonth` ("2026-09") + `users.roundsUsed`; a new month resets. The 11th round in a month throws `round_limit` (`lib/messages.ts`: "You've used this month's 10 free design chats. They reset on the 1st — or go Premium for unlimited."). Premium does not exist yet: leave a single `hasPremium(user)` returning false, used here.
- Replace the old lifetime `FREE_DESIGNS`/`canStartDesign`/`freeDesignsUsed` gate completely (remove the dead code and its tests, keep `freeDesignsUsed` in the schema as optional for old rows).
- Per-account burst guard (review of PR #76, P2): at most 3 designs in `brief`/`queued`/`designing` per account at once → `too_many_open` ("Finish or delete one of your open designs first.").

## 2. Complex warning and refusal (`convex/designs.ts` approve path, `components/chat/BriefChat.tsx`)
- Quote > £6: the approve step shows, above the button, "This is a complex part (several pieces or moving parts). It can take up to 30 minutes." Quote > £15: approve refuses with `too_complex` ("This one's too complex for now — try splitting it into simpler parts.") and the concept card shows the price struck through with that note. Constants in `convex/lib/pricing.ts` (`COMPLEX_WARN_PENCE = 600`, `MAX_BUILD_PENCE = 1500`).

## 3. Pricing page `/pricing` (`app/(main)/pricing/page.tsx`) and header link
- Three columns: **Free** (10 design chats a month, concepts and measurements, your first build free up to £3), **Pay per build** (price shown before you build, typically £2–£4 for a simple part; if we can't make it you're refunded), **Premium £9.99/month** ("coming soon" badge: £12 of builds a month, unlimited chats, priority). One primary action "Start designing" → `/design/new`. Honest copy, no fake testimonials. Link "Pricing" in the header and the footer. Phone first; screenshot 390 and 1280.

## 4. Open sign-ups switch (`convex/users.ts`)
- `OPEN_SIGNUPS=true` (env) lets any **verified** email through `requireUser`; unverified still refused with today's message. `ALLOWED_EMAILS` keeps working when `OPEN_SIGNUPS` is unset (private mode, today's prod). Tests for all four combinations.

## 5. Legal pages `/privacy` and `/terms`
- Pages rendered from `content/privacy.md` and `content/terms.md` (plain Markdown, rendered with what the repo already has — no new dependency; if nothing renders Markdown, write them as simple JSX paragraphs). Content: the two drafts in the go-live checklist, with `[your name or company]` and `[contact email]` left as visible placeholders — James fills them in. Footer links on every page; a one-line "By signing in you agree to our Terms and Privacy notice" under the sign-in button.

## Tests and proof
- Convex: round counting (create + revise, monthly reset, 11th refused, premium bypass stub), burst guard, complex warn/refuse, open-signups matrix, old free-design gate gone.
- UI: warning and refusal copy, pricing page renders the three tiers and links, footer links, sign-in agreement line. Screenshots `spec/motion/pricing-390.png`, `pricing-1280.png`, `approve-complex-390.png`.
- `run-limited npx vitest run`, worker pytest, `npx tsc --noEmit`, `run-limited npx next build` green.

## Hard rules
No self-review, merge or push. Commit your work. Report RED/GREEN, file:line, anything not verified. No new dependencies. Payments and open sign-ups stay OFF in prod (env untouched).
