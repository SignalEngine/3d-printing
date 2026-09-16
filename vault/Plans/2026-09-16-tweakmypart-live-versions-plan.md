# TweakMyPart: live versions — the tablet shows every version the AI builds (builder handover, part 1 of the redesign)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/live-versions`, cut from `origin/master`. Real `node_modules` (check `[ -L node_modules ]` before any npm). The site is live: never touch `/root/printtweak`, the systemd service, Convex env, or run `convex deploy`/`convex dev` against prod (anonymous codegen only; delete `.convex/` and `.env.local` before committing). Use `run-limited` for heavy commands. Write `GATES.md` at the worktree root before code (`/unlazy tree N`), commit it last. Run `python3 /root/.claude/scripts/surface-sweep.py versions versions.jsonl addVersion glbUrl --out spec/surfaces.md` first and account for every hit.

## Why
James (16 Sep): "are we able to show the AI really modelling it in real time?" Chosen: version-by-version build-up. The sandbox agent runs its modelling script several times per job (each run re-exports `<name>.3mf`); today only the final file reaches the customer. Every script run that produces a new 3MF becomes a **version**: a small GLB, uploaded within seconds, listed on the design, shown on the tablet by the (separate) front-end build. Honest: a version is a real file the AI exported, never an animation.

## Contract (the front-end build depends on these exact names)
- Convex table `versions`: `{ jobId: Id<"jobs">, designId: Id<"designs">, n: number, name: string, glb: Id<"_storage">, at: number, note?: string }`, index `by_design` on `["designId", "n"]`.
- `designs.get` gains `versions: { n, name, glbUrl, at, note? }[]` (ascending `n`, at most the last 12) and `latestGlbUrl: string | null` (the newest version's GLB while the design is not ready; the final `files.glb` once ready).
- Mutation `worker:addVersion({ secret, jobId, n, name, glb, at, note? })`: validates secret and that the job is `running`; ignores `n` already stored (idempotent); caps at 20 versions per job (drops the request beyond that, returns `{ stored: false }`).

## 1. Sandbox: detect a new export and write a GLB (`worker/job/run_job.py`)
- After every message in `_drain` (cheap: a stat of `/job/out/*.3mf`), call `snapshot_versions(out_dir, state)`. For each `<name>.3mf` whose mtime/size differs from `state["seen"][name]`, export `/job/out/versions/v<N>-<name>.glb` with trimesh (`trimesh.load(path, force="mesh").export(glb_path)`; skip on any exception, never fail the job) and append one line to `/job/out/versions.jsonl`: `{"n": N, "name": name, "glb": "versions/v3-tray.glb", "at": <unix ms>, "note": <last log line, e.g. "Building the shape">}`. `N` counts per job across all parts (1, 2, 3…). Debounce: ignore a file whose mtime is < 2 s old (still being written). Hard cap 20 snapshots; after that stop snapshotting.
- `describe_message` unchanged. Nothing else in the sandbox changes; the final deliverable is still `parts.json`.

## 2. Host: forward versions as they appear (`worker/worker.py`)
- `_tail_log` already polls `out/log.jsonl` every 3 s: extend it (or add a sibling thread with the same interval and lifetime) to tail `out/versions.jsonl`. For each new line: `_upload(convex, secret, out / line["glb"])` (existing helper, 3 retries), then `convex.mutation("worker:addVersion", {...})`. An upload or mutation failure logs and continues; it never fails the job.
- Also emit a progress line through the existing `_progress`: `"Version 3: tray"` (uses `name`), so the plain-English log shows it.
- `_retain_failure` already copies `out/`, so failed attempts keep their versions.

## 3. Convex (`convex/schema.ts`, `convex/worker.ts`, `convex/designs.ts`)
- Table and mutation per the contract. `designs.get`: resolve `glbUrl` via `ctx.storage.getUrl` for the last 12 versions; `latestGlbUrl` per the contract.
- `claimNext`/`reportResult` unchanged. No deletion of versions when a job ends (they are the design's history; a retry attempt keeps numbering by starting from the highest stored `n + 1` — pass `state["n"]` start from the host: on attempt 2 the host writes `in/version_start.txt` with the next `n`, and `snapshot_versions` reads it once).

## 4. Tests (RED first, then GREEN)
- `worker/tests/test_run_job.py`: `snapshot_versions` — new 3mf → one jsonl line + glb (fake exporter injected); unchanged file → nothing; changed mtime → n increments; cap at 20; file younger than 2 s ignored; exporter exception ignored.
- `worker/tests/test_worker.py`: fake runner writes `versions.jsonl` + glb files mid-run → `worker:addVersion` called once per line with the uploaded id, in order, and a `"Version 1: …"` progress line; upload failure → no addVersion for that line, job still completes; attempt 2 passes `version_start`.
- Convex (`convex/worker.test.ts`, `convex/designs.test.ts`): addVersion secret check, running-job check, idempotent `n`, cap 20; `designs.get` returns `versions` ascending with urls and `latestGlbUrl` (version while working, `files.glb` when ready).
- Full suite green at the end: `run-limited npx vitest run`, worker pytest in a venv with pytest (`/tmp/claude-0/-root-3d-printing/b59e9ac3-f8b5-4a83-98d1-e5d6fbb04e3c/scratchpad/ptvenv/bin/python -m pytest worker/tests -q` works), `npx tsc --noEmit`.

## Verification after merge (brain does this, not you)
Knob from the test account: `designs.get` shows ≥ 2 versions before `ready`, each GLB loads, `latestGlbUrl` flips to the final GLB at ready. Image rebuild required (`run_job.py` changed) — say so in the report.

## Hard rules
- No self-review, merge or push. Report RED/GREEN counts, file:line for every change, and anything you could not test.
- No new dependencies (trimesh is already in the sandbox venv; check `worker/job/requirements*.txt` / Dockerfile for it and say if it is missing).
- Keep the sandbox change tiny and exception-safe: a snapshot bug must never cost a job.
