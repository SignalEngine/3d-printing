# Fabric face engrave: one-layer design cut into the face, one swap (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]] ("Two-tone decision").
- James has no AMS and prints face-down, like NASA fabric; the bed side is the face.
- His method (tested in Bambu): emboss the design ONE layer into the face, then swap filament. Layer 1 = colour 1 face;
  the cut-in design starts at layer 2, so after the swap it shows colour 2.
- The picture is sub-tile: detail finer than a tile (eyes, a mouth) shows.
- It replaces the parked raised-cap branch `build/fabric-two-tone`. Don't build on it; borrow its sidecar/README
  wording if useful.

## Worktree
`3d-printing`: `/root/wt-3dp-engrave`, branch `build/fabric-engrave` (off origin/master). Python
`/root/3d-printing/.venv/bin/python`.

## Generator (`scripts/fabric.py`)
- **`--engrave SPEC`**: the design mask in the outline frame (mm, same frame as `--outline`). Accepted forms:
  - `poly:"x,y x,y|x,y ..."`;
  - a JSON file `{"polys": [...]}`;
  - `image:PATH` (a black-on-white drawing: dark = design). Reuse `silhouette.py`'s threshold/alpha loading; keep ALL
    blobs, not just the largest; scale to the outline's width.
- `--engrave-depth` defaults to 0.2, one layer at 0.20. Refuse anything other than a whole multiple of 0.2 up to 0.4.
- **Cut:** each tile loses (mask ∩ its z < depth section). The cut is from z = 0 up.
- **Every tile keeps a colour-1 rim so it still sticks to the bed:**
  - a band `RIM` = 1.0 mm inside the tile's bed section is never cut;
  - bed contact at z = 0.1 stays ≥ `MIN_CONTACT`;
  - where the mask would take more, clip the mask, and record `engrave_clipped_tiles` in the sidecar.
  - The pocket is bridged at layer 2 from the rim. Keep every pocket ≤ 6 mm across in its narrowest direction; the
    rim does this at pitch 8/10.
- **Min feature:** drop mask pieces narrower than 0.8 mm (two lines at a 0.4 nozzle). Record `engrave_dropped` in the
  sidecar.
- **Sidecar** adds: `engrave` (spec), `engrave_depth`, `swap_layer` (= depth / 0.2 + 1), `swap_z_mm` (= depth), the
  clipped/dropped counts.
- **README per model:**
  - "Load the FACE colour first. Bambu Studio → Preview → layer slider at layer {swap_layer} → right-click + → Change
    filament. The A1 pauses once; load colour 2."
  - Settings: No brim, supports off, elephant foot 0.15, 2 walls.
- No 3MF colour-change embedding. Bambu CLI behaviour is unverified, and James sets the change by hand.

## Test models (`models/fabric-engrave/`), both with the relief ON and gap 0.4
Draw bold faces as polygons in `build.py`, committed as `face-<name>.json`, sized so that features are ≥ 3 mm:
- pumpkin-drape: triangle eyes, triangle nose, zigzag mouth;
- bat-drape: two eyes plus a fanged mouth;
- ghost-drape and ghost-square: oval eyes and an "O" mouth;
- coaster90-drape: a star.
Outlines: reuse the existing `models/fabric-tests/*.3mf.json` outline specs (don't read tile geometry).

For each model:
- a **face render**: the bottom view mirrored as seen from the face. Colour 1 = sections at z < depth, colour 2 = the
  rest. Use one shared XY frame (`path.to_2D(to_2D=np.eye(4))`), NOT per-section centring.
- A fresh-context subagent sees ONLY each face render and must name the design and describe the face. Paste its
  answers.

Plate: as many as fit on 256 x 256 with ≥ 10 mm apart. Mixed tiles are fine because the swap Z is the same for all.
Slice it (slice_gate, supports none) → hours/grams; face render of the plate.

## Tests (`tests/test_fabric.py`), each red without its code
- Cut depth: inside the mask (away from the rim), the tile section at z = 0.1 is empty. Outside the mask, the section
  at z = 0.1 equals the un-engraved build.
- The rim holds, and bed contact is ≥ `MIN_CONTACT` for every tile, even with a mask covering the whole sheet (the
  clip path).
- The contract is unchanged: gap, captive, drape fold ±30°, one watertight body per tile, bed-level gap, `--check`.
- A mask piece of 0.5 mm is dropped and counted.
- `image:` of a synthetic PNG (two black dots) gives 2 pockets in the right tiles.
- Sabotage: RIM = 0 → the contact test goes red. Restore, then `rg SABOTAGE` returns nothing.

## Checks
`/root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests` (run-limited, exit code captured before
commit). Explicit-path commits; don't push.
