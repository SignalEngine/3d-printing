# TweakMyPart: multi-part designs (builder handover)

You are the BUILDER. Build only this, then stop and report. Repo `SignalEngine/printtweak`, worktree on branch `build/multipart`, cut from `master` (`488d5b7`). Real `node_modules`. Site is live: never touch `/root/printtweak`, the service, Convex env, or run convex deploy/dev against prod (anonymous codegen only; delete `.convex/` and `.env.local` before committing).

## Why (evidence, 15 Sep live runs)
Pill box: the sandbox built `tray.3mf` and `lid.3mf`, each passing its checks, then ran out of budget without ever writing the single `model.3mf`/`model.step` the pipeline demands ("no model produced", $2.00). Trinket box (lid + box) and Netgate bracket failed the same way in spirit. Single-body parts (knob, trophy) pass. Retained evidence: `/var/lib/printtweak/failed/jh77dfepdk93htbdb3x2rdwp9d8ef16s/attempt1/`.

## Contract change: a design is a list of parts
1. **Sandbox output** (`worker/job/run_job.py`, `system_prompt.md`): the deliverable is `/job/out/parts.json`: `[{"name": "tray", "file": "tray.3mf", "step": "tray.step", "count": 1}, ...]` (1..8 parts; names `[a-z0-9-]`, files inside `/job/out`). A single-part design is the same list with one entry. Keep accepting the old `model.3mf` + `model.step` by treating it as `[{"name": "model", ...}]`. The system prompt states this on line 1 ("Deliverable: /job/out/parts.json listing every printable part") and says: export parts as soon as they pass, before polishing; multi-part designs must be separate files, not one merged body. The self-check (verify_model + slice_gate) runs per part; `built` requires every part to pass.
2. **Budget** (`worker/job/run_job.py` `build_options`): `max_budget_usd` 2.0 for a request the classifier deems single-part, 4.0 otherwise. Classifier: the request mentions lid, lids, parts, compartments, snap, hinge, bracket+ears, or "set of" → multi-part. Test it.
3. **Host gates** (`worker/gates.py`): `run_all(out_dir, expected_text, progress)` reads `parts.json`, runs verify_model / slice_gate / render / GLB export per part; text_check only on the part whose name matches the request's text target (default: the largest). Quote = sum of hours and grams over parts; per-part quotes kept in `quote.parts`. Render: one front view per part, plus a combined GLB (`model.glb` with all parts side by side, 10 mm gaps) for the preview.
4. **Upload + Convex** (`worker/worker.py`, `convex/worker.ts`, `convex/schema.ts`, `convex/designs.ts`): `files` becomes `{ glb, front, parts: [{ name, threeMf, step, front }] }`. `designs.get` returns `partDownloads: [{ name, threeMfUrl, stepUrl }]` when payments are off. Keep `threeMfUrl`/`stepUrl` for one-part designs.
5. **Page** (`app/design/[id]/page.tsx`): the tablet shows the combined GLB; the download card lists each part with 3MF / STEP buttons and a "Download all (zip)" that fetches every file client-side and zips them (`fflate`, add to deps); the quote line shows total hours/grams and "N parts".
6. **Tests**: parts.json parsing and validation (sandbox and host), per-part gate run with a fake runner, quote summation, legacy single-file path, classifier, Convex `reportResult` with parts, `designs.get` partDownloads, page renders N part rows (jsdom test).

## Verification after merge (brain does this, not you)
Rerun the pill box and the trinket box from the test account; both must reach `ready` with 5 and 2 parts.

## Hard rules
- `[ -L node_modules ]` before npm; `run-limited` for heavy commands; no secrets; no root GATES.md.
- Tests RED then GREEN; full vitest + worker pytest (use a venv with pytest) + `npx tsc --noEmit` green at the end.
- No self-review, merge or push. Report RED/GREEN, file:line, and that `run_job.py`/`system_prompt.md` changed (image rebuild).
