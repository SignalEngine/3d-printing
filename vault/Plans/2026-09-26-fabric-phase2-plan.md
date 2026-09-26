# Fabric phase 2: fabric orders in TweakMyPart (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]]. Phase 1 is merged (model-forge #14: `skills/model-forge/scripts/fabric.py`, CLI
`--outline rect:W,H|circle:D|poly:"x,y ..."|text:"..." --pitch --height --gap --out X.3mf`; it writes `X.3mf` (one
object per tile) plus `X.3mf.json` {tiles, pitch, height, gap, outline, bbox, dropped_islands}). The default gap stays
0.4 mm until James prints the swatch.

## Worktrees
- `3d-printing`: `/root/wt-3dp-fabric2`, branch `build/fabric-check`. Merges FIRST (the job image copies model-forge).
- `printtweak`: `/root/wt-pt-fabric`, branch `build/fabric-orders`.

## Goal
"A 90 mm round fabric coaster" (or a bookmark, a heart, a name tag) goes through the real customer path:
- the brief offers fabric options;
- the sandbox runs the generator and never hand-models tiles;
- the host verifies it is REAL fabric (many separate captive tiles, gaps held), slices it, the judge looks at it, and
  it ships.

## A. model-forge `fabric.py` (3d-printing)
1. New `--check X.3mf [--gap G]` mode, printing one JSON line:
   `{"ok", "tiles", "bodies", "min_gap_mm", "fused_pairs", "detail"}`.
   - Load every object of the 3MF, placed.
   - `bodies` = the number of objects (each must be one watertight body).
   - For every pair of objects whose bounding boxes are within `pitch` of each other, measure the minimum distance
     (manifold/trimesh proximity; reuse whatever the phase 1 tests use).
   - `ok` = bodies ≥ 2 AND no pair closer than `G - 0.05` AND no pair intersecting (`fused_pairs == 0`).
   - It must finish in < 60 s for a 256 x 256 mm sheet at pitch 9 (about 800 tiles): neighbour pruning by grid, not
     all pairs.
2. Tests in `tests/test_fabric.py`:
   - `--check` on a generated circle passes;
   - the same sheet with two tiles merged into one object (fused) → `ok:false`, fused_pairs ≥ 1;
   - a sheet whose tiles were moved 0.2 mm closer → `ok:false`;
   - a timing test on a 200 x 200 sheet < 60 s.

## B. Sandbox (printtweak `worker/job/system_prompt.md`, `run_job.py`)
1. A system prompt rule: a request for FABRIC (chainmail, "NASA fabric", a flexible or bendy sheet, a fabric
   coaster/bookmark/patch) is ALWAYS made with
   `python /opt/model-forge/scripts/fabric.py --outline ... --out /job/out/<name>.3mf`.
   - Never model tiles yourself.
   - The outline comes from the request: `circle:D`, `rect:W,H`, `poly:"x,y ..."` for a shape (heart, star, leaf,
     drawn at the requested size), `text:"NAME"`.
   - `parts.json`: one part `{name, file: <name>.3mf, step: null, count: 1}`.
   - No `checks.json` is needed (one part).
   - `fabric.py` refuses sizes over the bed and pitches that are too small: follow its message, don't fight it.
2. `parse_parts` / `load_parts` accept `step: null` for a part whose `<file>.json` sidecar exists with a `tiles` key
   (fabric). Without a sidecar, a null step still fails as today for a fresh design.
3. The sandbox's own `run_checks` for a fabric part (sidecar present) runs `verify_model --bodies <tiles>` and
   `slice_gate --supports none`, never the default `--bodies 1`.
4. `brief_prompt.md`: when the request is fabric, the concepts are fabric ITEMS/shapes (e.g. round coaster, square
   coaster, bookmark with rounded ends):
   - the questions ask the overall size (a measurement) and, for text, the words;
   - never ask for tile geometry;
   - `parts: 1`.

## C. Host (printtweak `worker/gates.py`, `worker/worker.py`)
1. `gates.load_parts` accepts `step: null` for a part with a fabric sidecar in `out/` (same rule as the sandbox).
2. `gates.run_all`, for a fabric part (sidecar with `tiles`):
   - run `fabric.py --check <file> --gap <sidecar gap>`; `ok:false` is a failure with a plain reason ("the fabric's
     tiles are fused together", or "tiles are closer than the print gap");
   - `verify_model --bodies <tiles>`;
   - slice with `--supports none`;
   - a mechanics line `"<name>: <tiles> linked tiles, <gap> mm gap"` (ok) for the ready page.
   - The sandbox writes the sidecar, so don't trust its `tiles` field for anything except the expected body count:
     `--check` re-measures the real geometry.
3. No support fins on a fabric part. The worker upload skips `step` when it is null (already true).

## D. Tests (both repos) — each red without its fix
- Sandbox: a fabric part with a null step and a sidecar is accepted; without the sidecar it is refused; run_checks
  asks for `--bodies <tiles>`.
- Host: a fabric sheet from `fabric.py` passes `run_all` (real generator, real check); a fused sheet fails with the
  fused reason; a missing sidecar with a null step fails `load_parts`.
- Brief: the prompt text contains the fabric rule.
- Sabotage: disable the `--check` call in run_all → the fused-sheet test goes red. Restore, then `rg SABOTAGE`
  returns nothing.

## Checks the builder runs and pastes (capture exit codes; never `| tail && git commit`)
- 3d-printing: `/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests`.
- printtweak: `npx tsc --noEmit`, `npx vitest run`, and `/root/printtweak/worker/.venv/bin/python -m pytest -q
  worker/tests -p no:cacheprovider`.
- Commit with explicit paths (symlinked `node_modules` / `.venv`: never `git add -A`). Don't push.

## Staging proof (brain)
"A 90 mm round fabric coaster" → options are fabric items → build → ready. The ready page shows "69 linked tiles,
0.4 mm gap", it slices with no supports, and the download is one 3MF with the tiles.

## Not in this phase
Pictures, colours, hex tiles, straps, remix of uploaded fabric (later phases).
