# TweakMyPart staging

Shipped 2026-09-22 (printtweak #78). A copy of TweakMyPart that runs the same code on a separate backend, so
changes are proven before they reach tweakmypart.com.

| Piece | Live | Staging |
|---|---|---|
| Site | tweakmypart.com (Railway `printtweak`, env `production`) | printtweak-staging-staging.up.railway.app (Railway `printtweak-staging`, env `staging`) |
| Backend | Convex project `tweakmypart` | Convex project `tweakmypart-staging` (its production deployment) |
| Login | Clerk production | Clerk **development** instance (sign-in tokens + test users work) |
| Payments | Stripe live | Stripe **test** keys |
| Worker | `printtweak-worker.service`, code from `/root/printtweak` | `printtweak-worker-staging.service`, code from `/root/printtweak-staging`, env `/etc/printtweak/worker-staging.env` (loaded last) |
| Email | Resend | none (no key set, so nothing sends) |

**Use it:**
- Deploy a branch: `scripts/stage-deploy.sh <worktree>` (locked; refuses a dirty tree; checks the URL returns 200 with the banner).
- Copy live data in: `scripts/staging-snapshot.sh` (`--dry-run` first). Token, secret, webhook and Stripe id fields are blanked by `scripts/scrub-snapshot.mjs`.
- Signed-in tests: `CLERK_SECRET_KEY_STAGING=$(cat ~/.config/tweakmypart-clerk-dev-sk) PT_BASE_URL=<staging url> npx playwright test e2e/staging-authed.spec.ts`; seed the persona with `scripts/staging-seed-users.mjs`.
- Staging shows a STAGING banner and is noindex; live does not (checked after the merge).

**Gotchas:**
- The staging worker runs whatever commit `stage-deploy` last checked out into `/root/printtweak-staging`, not master.
- The Clerk development secret and Stripe test keys are set by James; staging cannot sign anyone in until the Clerk key is on Railway staging.
- Design and research: `~/.claude/stack-research/staging-environments-2026-09-22.md` (LaunchEngine gets the same pattern next).
