# Builder handover: PrintTweak fix — remove email relinking (post-merge Codex P1)

You are the BUILDER. Implement only this fix, then stop and report.

## Why

The post-merge Codex review of `SignalEngine/printtweak` master (`f37408c`) found, and the brain confirmed:

- **P1:** `convex/users.ts` `requireUser` links a new Clerk token to an existing user **by email** and patches that row's `tokenIdentifier`. If Alice changes her Clerk email and Bob later registers her old address, Bob takes over Alice's user row and can read and tweak her designs.
- **P2:** when `designs.create` then throws `free_limit`, the whole mutation rolls back, including the relink, so a recreated account can't see its designs.

Decision (brain): remove the relink. Users are identified by Clerk token only. Account ownership never transfers by email. The "recreate account resets free designs" gap comes back; that's accepted in personal mode and tracked in the plan for API-key mode.

## Change

1. `convex/users.ts` `requireUser`: delete the `by_email` lookup and the `tokenIdentifier` patch. Flow: look up by token → return if found → otherwise insert (email stored lower-cased) and emit `sign_up`. Keep `currentUser` as is.
2. `convex/schema.ts`: keep the `by_email` index (harmless, needed later for email-keyed quota). Don't remove it.
3. `convex/designs.test.ts`: replace the test "same email on a new account shares the free limit" with:
   - **"a new account with the same email cannot see another account's designs"**: `clerk|alice` with `former@company.test` creates a design; `clerk|bob` with `Former@Company.test` calls `api.designs.listMine` → `[]`, and `api.designs.get({designId})` → `null`; then Bob creates his own design successfully; the users table has 2 rows; Alice's row still has `tokenIdentifier === "clerk|alice"`.
   - Write this test FIRST and show it failing against current `master` (Bob currently takes over Alice's row), then make the change and show it passing.

## Rules

- Work only in the worktree you were given (branch `build/fix-email-link`, cut from `master`).
- Heavy commands through `run-limited`, one at a time: `run-limited npx vitest run`, `run-limited npx tsc --noEmit` (must be 0 errors).
- Do not touch `worker/` or anything from Task 3.
- Do not review your own work, merge, or push to `master`. Commit on your branch (message: `fix: never relink accounts by email (Codex P1)`) and report RED output, GREEN output, tsc output, file:line of each change.
- Do NOT create or edit a root `GATES.md` for this fix (the Task 3 branch also changes it, and both merging would conflict). Put your acceptance gates and their evidence in the report instead.
