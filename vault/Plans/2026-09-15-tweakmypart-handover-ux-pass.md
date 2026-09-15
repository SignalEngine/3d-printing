# Builder handover: TweakMyPart UX pass

You are the BUILDER. Implement `/root/3d-printing/vault/Plans/2026-09-15-tweakmypart-ux-pass-plan.md` sections 1-4, then stop and report.

- Repo `SignalEngine/printtweak`, worktree on branch `build/ux-pass`, cut from `master`. `node_modules` is a real install. Paths are at the repo root (`app/`, `components/`, `convex/`, `worker/`, `test/`).
- The site is LIVE (Railway deploys `master`; the worker runs from `/root/printtweak` as a systemd service). Do not touch `/root/printtweak`, the service, or Convex env. Do not run `npx convex deploy`/`dev` against prod; use `CONVEX_AGENT_MODE=anonymous npx convex dev --once --typecheck disable` only if you need codegen, then delete the `.convex/` and `.env.local` it leaves behind before committing.
- Existing pieces to reuse: `components/mascot/Mascot.tsx` (`state` prop, `nextClip.ts`), `components/mascot/TabletPreview.tsx`, `lib/messages.ts`, design tokens in `app/globals.css`. Worker: `worker/worker.py` (`process`, `run_one`, `_report`), `worker/gates.py`, `worker/job/run_job.py` (SDK message loop). Convex: `convex/worker.ts` (`claimNext`, `reportResult`, `finishUnsuccessful`), `convex/designs.ts` (`get`), `convex/schema.ts`.
- Worker Python env: `worker/.venv` (create with `python3 -m venv worker/.venv && run-limited worker/.venv/bin/pip install -r worker/requirements.txt pytest`). The job container image is NOT rebuilt by you; changes to `worker/job/run_job.py` must be reported so the brain rebuilds the image (`run-limited bash worker/setup_network.sh`).
- Keep all existing tests green; add the tests in plan section 4. Playwright smoke must still pass.

## Hard rules
- `[ -L node_modules ]` check before any npm command; heavy commands through `run-limited`, one at a time.
- No secrets in code or tests; no root `GATES.md`.
- Tests RED first, then GREEN. Full `run-limited npx vitest run`, worker pytest, and `npx tsc --noEmit` pass at the end.
- Do not review your own work, merge or push. Commit on your branch; report RED/GREEN, file:line per change, and whether `worker/job/run_job.py` or the Dockerfile changed.
