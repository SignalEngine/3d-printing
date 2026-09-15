# Builder handover: TweakMyPart Task 8 code (funnel page, visit events, deploy readiness)

You are the BUILDER. Build only this, then stop and report.

- Repo `SignalEngine/printtweak`, worktree on branch `build/task8-funnel`, cut from `master` (`5dd9817`, design pass merged). `node_modules` is a real install.
- Plan: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md`, Task 8 Steps 1-4 (code only). Deploy (Step 5) and live test (Step 6) are NOT yours.

## Differences from the plan text
1. Paths are at the repo root: `app/admin/funnel/page.tsx`, `convex/funnel.ts`, `convex/funnel.test.ts`. No `src/`.
2. Personal mode: there is no `paid` event yet; keep it in `NAMES` so the table is ready for payments.
3. Style the admin page with the existing design system (`app/globals.css` classes `.card`, headings), title "TweakMyPart funnel". `proxy.ts` already protects `/admin(.*)`.
4. Visit recorder: a small client component in `app/page.tsx` calling `api.funnel.recordVisit` once per browser session (`sessionStorage` flag in try/catch, `utm_source` passed through). Store `source` on the event if the `events` schema allows it; if it does not, add an optional `source: v.optional(v.string())` field to `events` in `convex/schema.ts` with a test. Skip the `/api/visit` fallback route.
5. `recordVisit` is public and unauthenticated: cap `source` at 100 characters, and ignore it rather than throwing if longer.

## Deploy readiness (small, no new services)
6. Confirm `npm run build` succeeds with only `NEXT_PUBLIC_CONVEX_URL` set to a placeholder (Clerk keyless). If it fails, fix the cause, don't stub Clerk.
7. `next start` must honour Railway's `PORT`: check that `package.json` `start` is `next start` (Next reads `PORT`). No Dockerfile, no railway.json unless the build proves one is needed.
8. Add a `## Deploy (personal mode)` section to `README.md` listing the env vars by name only and where each lives: Railway (`NEXT_PUBLIC_CONVEX_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`), Convex (`CLERK_JWT_ISSUER_DOMAIN`, `ALLOWED_EMAILS`, `ADMIN_EMAILS`, `WORKER_SECRET`, `SITE_URL`; `PAYMENTS_ENABLED` and `RESEND_API_KEY` unset), VPS `/etc/printtweak/worker.env` (`CONVEX_URL`, `WORKER_SECRET`, `CLAUDE_CODE_OAUTH_TOKEN`). Link `/root/3d-printing/vault/Plans/2026-09-15-tweakmypart-go-live-checklist.md` for the steps.

## Hard rules
- `[ -L node_modules ]` check before any npm command; heavy commands through `run-limited`, one at a time.
- No real keys anywhere; test emails like `admin@example.com`.
- Do not create or edit the root `GATES.md`. Do not touch the worker or the mascot components.
- Tests RED first, then GREEN; full `run-limited npx vitest run` and `npx tsc --noEmit` pass at the end.
- Do not review your own work, merge or push. Commit on your branch; report RED/GREEN, the `npm run build` result, file:line of each change.
