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

**Signed-in tests (printtweak #81, 2026-09-22):** 3/3 pass against staging. `e2e/auth.ts` signs in by loading the
app, waiting for `window.Clerk.loaded`, then `Clerk.client.signIn.create({ strategy: "ticket", ticket })` and
`setActive`. A `?__clerk_ticket=` URL does not work here: the app has no SignIn component (it uses Clerk's hosted
portal), so the URL form lands on the sign-in page. All e2e files use an absolute `PT_BASE_URL`.

**Railway gotcha:** the CLI acts on whatever environment the folder is linked to. Always pass `--environment staging`
when setting staging variables; one key once landed on a stray copy of the staging service in production.

**Gotchas:**
- The staging worker runs whatever commit `stage-deploy` last checked out into `/root/printtweak-staging`, not master.
- **Sandbox image (22 Sep):** the staging worker runs `PRINTTWEAK_JOB_IMAGE=printtweak-job:staging` (line in `worker-staging.env`; the setting ships with the ask-before-changing PR — until that merges, only that branch's worker reads it). `stage-deploy` does NOT build the image. For a change to `worker/job/*` (prompts, run_job.py), build it from the branch: copy `worker/job` to a scratch dir, add `/root/3d-printing/skills/model-forge` and `/root/3d-printing/orcaslicer`, then `docker build -t printtweak-job:staging <dir>`. Never use `setup_network.sh` for staging: it rebuilds `:latest` and restarts the live proxy.
- The Clerk development secret and Stripe test keys are set by James; staging cannot sign anyone in until the Clerk key is on Railway staging.
- Design and research: `~/.claude/stack-research/staging-environments-2026-09-22.md` (LaunchEngine gets the same pattern next).
