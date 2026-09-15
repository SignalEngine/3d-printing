# Builder handover: PrintTweak Tasks 1-2

You are the BUILDER. Implement **only Task 1 and Task 2** of the plan, then stop and report.

- Plan: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-plan.md` (read Global Constraints, File Structure, Task 1, Task 2).
- Spec: `/root/3d-printing/vault/Plans/2026-09-13-printtweak-mvp-spec.md` (context only).

## Differences from the plan text

- The repo already exists: `SignalEngine/printtweak` (private) with a README on `master`. You are in a worktree of it on a build branch. **Skip Task 1 Step 1's `gh repo create`, `--clone` and `git checkout -b`.** Scaffold into the current directory: `npm create convex@latest . -- -t nextjs-clerk` (keep README.md; merge if the template overwrites it).
- `npx convex dev` needs a Convex login/project. If it prompts for login and you cannot complete it, use `npx convex codegen` only if it works offline; otherwise STOP and report "needs Convex login" rather than faking generated files. convex-test does not need a deployment.
- Do not create Clerk, Stripe, Railway or Anthropic resources. Tasks 1-2 need none.

## Rules

- Run `/unlazy tree 2` on Tasks 1-2 first and write `GATES.md` at the worktree root; commit it last.
- Every test RED first, then GREEN. Paste both outputs in your report.
- Do not review your own work, merge, or push to `master`. Commit on your branch and report: RED output, GREEN output, files changed, anything that blocked.
