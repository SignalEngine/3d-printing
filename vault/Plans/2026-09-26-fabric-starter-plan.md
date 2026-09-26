# Fabric starter page: "Design your own fabric" (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]]. James, 26 Sep: customers shouldn't have to know the right words. A dedicated "Design
fabric" flow always uses the fabric tool. Tile-style choice (square / hex / scales, with pictures) comes only once hex
and scales exist.

## The idea
A preset fabric order is fully specified by the customer's picks: shape, size, and text for a name tag. So it needs NO
AI:
- the host runs `fabric.py` directly with those parameters;
- runs the fabric gates (`--check`, verify `--bodies`, slice with no supports);
- renders and ships.
Seconds, pennies, deterministic. A custom shape ("a dinosaur") stays in the normal chat, where the fabric rule
already applies.

## Worktree
`printtweak`: `/root/wt-pt-fabstart`, branch `build/fabric-starter` (off origin/master). model-forge doesn't change.

## A. Page: `/design/fabric` (Next.js, `app/(main)/design/fabric/`)
- **Shape picker:** round coaster, square coaster, bookmark (rounded ends), heart, name tag (text), patch
  (rounded square). Each is a card with a small SVG outline. One tap selects it.
- **Size:**
  - one number in mm for round, square, heart and patch (the overall width);
  - length and width for the bookmark;
  - text + letter height for the name tag.
  - Sensible defaults (coaster 90, heart 110, bookmark 150 x 45, patch 80, name tag: letters 25 mm).
  - Limits come from the bed (256) and the generator (pitch 10): the smallest item is at least 3 x 3 tiles.
- **Live preview, client-side and honest:** an SVG of the actual tile grid inside the chosen outline, using the same
  "keep a tile if at least half of it is inside" rule as `fabric.py`, plus the tile count and approximate print
  time/grams from a simple per-tile rate.
  - Port only the outline + cell-keep rule to TypeScript: circle, rect, heart polygon (same formula as
    `models/fabric-examples` heart), rounded rect, and text via a canvas mask.
  - Test that TS counts match `fabric.py` for the presets (fixtures generated once with the Python CLI and committed
    as JSON).
- **Price:** shown before ordering. Use the existing pricing (`buildPricePence`) with a predicted cost from tile count;
  no LLM cost. The free first build and payments follow the existing flow (`startOrAwaitPayment`).
- **"Make it" button** → the new mutation. **"Something else? Describe it"** → `/design/new?q=a <shape> made of
  printable fabric`.
- Design stack (§16): `impeccable` craft pass, the TweakMyPart design system (PRODUCT.md / DESIGN.md), mobile-first
  375 px. The lander links (`#fabric` chips and "Design fabric") point here.

## B. Convex
- `designs.createFabric` mutation:
  - args `{ shape: "round"|"square"|"bookmark"|"heart"|"nametag"|"patch", widthMm, lengthMm?, text?, letterMm? }`;
  - validates ranges server-side (never trust the page);
  - applies the same auth / allowlist / daily cap / open-designs guards as `designs.create` (reuse the helpers);
  - creates a design with `request` = a plain sentence ("A 90 mm round fabric coaster"), `fabric: {…params}`, and no
    brief (status straight to payment/queued via `startOrAwaitPayment`);
  - enqueues a job of the new kind `"fabric"`.
- Schema:
  - job `kind` adds `"fabric"`;
  - design gets `fabric: v.optional(v.object({shape, widthMm, lengthMm?, text?, letterMm?}))`;
  - `claimNext` passes the fabric params to the worker.

## C. Worker (`worker/worker.py`)
- `process_fabric(job, …)`, routed in `run_one` for kind `"fabric"`:
  - build the outline spec from the params. circle:D, rect:W,H; for the heart, the same polygon code as the
    examples, moved into model-forge as `fabric.py --outline heart:W`. Allowed: a tiny model-forge addition in
    `/root/wt-3dp-fabheart`, merged first. Name tag: `text:"..."` at the letter height. Patch: a rounded rect polygon;
  - run `fabric.py` into `out/fabric.3mf` + sidecar; write `parts.json`;
  - run `gates.run_all` (the fabric path already exists), the render and the GLB; no vision judge (nothing to judge
    against a free-text request, and the geometry is deterministic);
  - `_ship` as usual, with cost 0 for the LLM.
- Failure (e.g. text too long for the bed) → a plain customer reason, and the free try is refunded (existing path).

## D. Tests (each red without its code)
- TS:
  - preview tile counts match the Python fixtures for each preset;
  - the page renders presets, the size inputs have labels, and "Make it" calls `createFabric` with the right params.
- Convex:
  - `createFabric` validates ranges and applies the guards;
  - it creates a `fabric` job with params;
  - `claimNext` passes the params.
- Worker: `process_fabric` for circle 90 ships 69 tiles, uses no LLM (no docker runner call), and gives a failure
  reason for an oversize name tag.

## Checks the builder runs and pastes (capture exit codes)
`npx tsc --noEmit`, `npx vitest run`, worker pytest (`/root/printtweak/worker/.venv/bin/python -m pytest -q
worker/tests -p no:cacheprovider`), model-forge pytest if touched. Explicit-path commits; don't push.

## Staging proof (brain)
- Open `/design/fabric` on a 375 px phone viewport.
- Pick a heart at 110 mm; the preview shows 56 tiles.
- Make it → ready in under 2 minutes, "56 linked tiles", one 3MF.
- Design gate: `design-gate.sh <staging>/design/fabric --viewport mobile --flow ...`.
