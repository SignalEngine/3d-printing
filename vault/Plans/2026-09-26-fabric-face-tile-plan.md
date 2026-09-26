# Fabric tile v3: flat-face fine tile (~7 mm) for face-down art (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]]. It builds ON the face engrave ([[2026-09-26-fabric-engrave-plan]], `--engrave`), so
start after that merges.

Why:
- Face-down engrave (James's one-layer emboss, one filament swap) needs a big flat face on each tile.
- Our drape tile touches the bed with a ~5 mm square per 8 mm cell. The square tile's crosses leave gaps where the
  design falls.
- So the engraved faces read as sparse dots (`models/fabric-engrave/*-face.png`).
- NASA fabric works because each tile is almost all flat face, with the links on the back.
- James also wants finer silhouettes: a 7 mm cell keeps more of a shape than 8/10.

James chose this over pixel-style on the current tiles.

References, for the IDEA only (never copy geometry):
- NASA fabric files `/root/intentos/vault/inbox-files/tg-2026-09-26-08*`;
- Giant Fidget Fabric `/root/intentos/vault/inbox-files/tg-2026-09-26-160939-Huge+Fidget+Fabric.3mf`: 7 x 7 x 2.5 mm
  tiles, a flat face on the bed, links on top. Look at its thumbnails / slice a corner to understand the linking
  principle. Licence BY-SA, so our geometry must be our own.

## Worktree
`3d-printing`: `/root/wt-3dp-face`, branch `build/fabric-face-tile` (off origin/master AFTER the engrave merges).
Python `/root/3d-printing/.venv/bin/python`.

## Deliverables
1. **`fabric.py --tile face`:**
   - pitch default 7.0; the same CLI, outlines, sidecar, `--check`, `--tiles-glb`, first-layer relief and
     `--engrave`.
   - Geometry is the builder's choice within the contract. Suggested: each tile is a flat square plate at z = 0
     (cell minus gap) with link features on its TOP (back) side only: posts/loops and hooks/arches that capture the
     neighbours, checkerboard-alternated like the others.
   - Printable flat: bridges ≤ 6 mm, overhangs ≤ 45°, features ≥ 0.8 mm, supports none.
   - `DEFAULT_TILE` stays `square`: TweakMyPart's preview/price aren't switched here.
2. **Contract, as tests** (the existing both-tile contract tests run for ALL THREE tiles):
   - **Face coverage (new, the reason for v3):** the section at z = 0.1 covers ≥ 75 % of the sheet's cell area,
     measured on a 5x5 sheet: sum of tile sections / (tiles × pitch²). The drape and square tiles are asserted to
     FAIL this, as the positive control.
   - gap ≥ gap − 0.02; captive (2 mm ±x/±y/+z collides);
   - **fold:** every neighbour pair folds ±20° without intersecting. Target ±30°; record the measured max in
     `references/fabric.md`;
   - one watertight body per tile; bed-level gap (relief); bed contact ≥ `MIN_CONTACT` — pick the floor for a 7 mm
     tile from its plate area and say why;
   - `slice_gate --supports none` on a 5x5 sheet; `--check` passes, and a fused pair goes red;
   - min pitch validated by building one tile (like drape) → a table per gap 0.3–0.6.
3. **The engrave works on it:** with the face masks from `models/fabric-engrave/face-*.json`, the engraved area kept
   (after the rim/contact clip) is ≥ 60 % of the mask area inside the outline. Assert this for the ghost face.
4. **Test models (`models/fabric-face/`)**, pitch 7, gap 0.4, relief on, engraved faces:
   - pumpkin, bat, ghost, star coaster (outlines as in `models/fabric-engrave/build.py`);
   - face renders (shared XY frame, bottom view mirrored);
   - the fresh-context blind read (a subagent sees ONLY the render and must name the design + describe the face).
     Paste the answers.
   - One A1 plate (256 x 256, ≥ 10 mm apart), sliced → hours/grams; a README with the swap at layer 2 (Bambu: Change
     filament at layer 2; load the FACE colour first) and settings: No brim, supports off, elephant foot 0.15, 2
     walls.
   - A tile close-up render (iso from the back) so the brain can judge the links.
5. **Swatch:** `--swatch --tile face` (gaps 0.3/0.4/0.5) in `models/fabric-swatch-face/`.

## Checks
`/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests` (run-limited, exit code captured before
commit). Sabotage:
- face plate shrunk to 50 % → the coverage test goes red;
- the hook's capture removed → captive goes red.
Restore, then `rg SABOTAGE` returns nothing. Explicit-path commits; don't push.

## Not in this plan
TweakMyPart switching tile/preview/price; the per-use picker; hex/triangle tiles.
