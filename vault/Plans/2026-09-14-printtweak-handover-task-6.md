# Builder handover: PrintTweak Task 6 (front end, allowlist, review follow-ups), personal mode

You are the BUILDER. Implement **only Task 6** of the plan, then stop and report.

- Plan: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md`. Read, in this order: "Update 2026-09-14: personal mode" (it OVERRIDES the task text where they differ), Global Constraints, Task 6, "Review follow-ups". This handover overrides all of them where they differ.
- Spec: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-spec.md` §0 and §2 (context).
- Worktree of `SignalEngine/printtweak` on branch `build/task6-frontend`, cut from `master` (Tasks 1-5 merged). `node_modules` is a real install, not a symlink.
- Design polish is NOT in scope. James chose: plan layout now, design pass later. Keep the plan's plain markup; semantic elements, every input labelled, visible focus.

## Repo facts that differ from the plan text

1. The app lives at the repo root: `app/`, `components/` (no `src/`). `@/*` maps to `./*`. So pages go in `app/page.tsx`, `app/design/new/page.tsx`, `app/design/[id]/page.tsx`, and the viewer in `components/ModelViewer.tsx`.
2. Next 16 route guard is `proxy.ts` (not `middleware.ts`). Change `createRouteMatcher(["/server"])` to `["/design(.*)", "/admin(.*)"]`.
3. Limits live in `convex/lib/limits.ts`; `requireUser` in `convex/users.ts` is keyed by Clerk token only (PR #2). The plan's "emailVerified before email linking" follow-up is moot: there is no email linking any more. Do not add it.
4. No `.env.local` and no Clerk keys exist in this repo on the VPS. `npm run dev` also starts `convex dev`, which needs a login. See "Playwright" below.

## Personal-mode changes (build these)

1. **Allowlist** in `requireUser`, before the token lookup or any insert: read `process.env.ALLOWED_EMAILS` (comma-separated, trim, lower-case). Refuse with `ConvexError("not_allowed")` when the list is empty/unset, when `identity.email` is not in it, or when `identity.emailVerified !== true`. Tests (convex-test `withIdentity`): allowed + verified passes; other email refused and creates no `users` row; allowed but `emailVerified: false` refused; unset `ALLOWED_EMAILS` refuses everyone.
2. **No payments** (Task 7 deferred). Add `PAYMENTS_ENABLED` env (unset = false):
   - `canStartDesign`/`canTweak` callers skip the free-design and free-tweak limits when payments are off. `globalGate` (daily £ cap, queue cap) ALWAYS applies: it protects the subscription. Tests: 3rd design allowed with payments off; refused with `free_limit` when `PAYMENTS_ENABLED=true`; daily cap still refuses with payments off.
   - `designs.get` returns `threeMfUrl` and `stepUrl` (from `design.files`) only when payments are off; `null` when on. Test both.
   - Design page: no `/api/checkout`, no pay buttons. Show the quote as information (print time, grams, cost floor, or the too-big reason), then links "Download 3MF" and "Download STEP" when the URLs are present.
3. **Landing copy:** heading stays "Describe a part, or upload your model" (the smoke test pins it). Add "Private beta". Remove "2 free" and the £5 / print-and-post sentence. Button: "Start a design".
4. **Error copy** on the new-design form: `not_allowed` → "This is a private beta. Your email isn't on the list."; `too_long` → "Keep it under 2,000 characters."; `upload_too_large` / `upload_type` → the same wording as the browser checks.

## Review follow-ups (build these, failing test first)

1. Server-side upload validation in `designs.create`: `ctx.db.system.get(uploadId)`; model ext (`.stl .3mf .step .stp` from `uploadName`) max 25 MB, photo (`.jpg .jpeg .png .webp`) max 10 MB; anything else `ConvexError("upload_type")`, over size `ConvexError("upload_too_large")`. Test: a 26 MB stored model blob is refused; a small `.png` passes.
2. Text caps: `request` and tweak `text` over 2,000 characters → `ConvexError("too_long")`. Tests for both.
3. Tweak failure message: in `finishUnsuccessful`, `job.kind === "tweak"` stores "That change didn't work. Your tweak has been refunded." Test on the stored message text.
4. Tweak jobs need the previous STEP: `claimNext` returns `previousStepUrl` (`ctx.storage.getUrl(design.files.step)` when `kind === "tweak"` and `design.files` exists, else `null`). Test: a tweak claim on a ready design includes it. In `worker/worker.py` `process`, inside the per-attempt `try`, next to the upload download: `if job.get("previousStepUrl"): (job_dir / "in" / "previous.step").write_bytes(requests.get(job["previousStepUrl"], timeout=120).content)`. Python test with a fake runner and a monkeypatched `requests.get`: the file exists when the runner is called. Run `worker/.venv` (create it with `python3 -m venv worker/.venv && worker/.venv/bin/pip install -r worker/requirements.txt pytest`).
5. Ready email: build `convex/email.ts` as the plan shows (it no-ops without `RESEND_API_KEY`). Keep the plan's test.

## Playwright

- Chromium is already in `~/.cache/ms-playwright`. Add `@playwright/test` as a devDependency (`[ -L node_modules ]` check first, then `run-limited npm install -D @playwright/test`); do not run `npx playwright install`.
- Without Clerk keys `next dev` may refuse to start. Try `run-limited npx next dev -p 3100` with no env. If it does not serve `/`, report `E2E: SKIPPED - needs Clerk dev keys in .env.local` and paste the error. Never fake it or stub Clerk out of `proxy.ts`. Point the tests at `PT_BASE_URL` (default `http://localhost:3100`).
- If it serves, run the smoke tests and take one screenshot at 375x812 of `/` (`npx playwright screenshot`). Read it once, fix clipping.

## Hard rules learned

- **Never run `npm ci`, `npm install` or `rm -rf node_modules` without checking `[ -L node_modules ]` first.** A symlinked `node_modules` points at `/root/intentos` and installing through it wiped another project's packages on 2026-09-14.
- Heavy commands (`vitest`, `next dev`, `npm install`) through `run-limited`, one at a time.
- Do NOT create or edit the root `GATES.md`. Put gates and evidence in the report.
- Never print or commit secrets. `ALLOWED_EMAILS` values do not go in code or tests beyond fake addresses like `me@example.com`.

## Rules

- Tests RED first, then GREEN. Paste both outputs.
- Full Convex suite (`run-limited npx vitest run`) and worker pytest must pass at the end; `npx tsc --noEmit` clean on touched files.
- Do not review your own work, merge, or push. One or more commits on your branch; report: RED/GREEN outputs, E2E result or SKIPPED line, file:line of each change, and anything in this handover you could not do.
