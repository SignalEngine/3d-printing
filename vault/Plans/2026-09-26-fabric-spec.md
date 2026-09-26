# Printable fabric ("NASA fabric") for TweakMyPart (spec, 26 Sep 2026)

James, 26 Sep: "give it the power to make fabrics like 'NASA fabric'". Reference files (Telegram, 26 Sep 08:32,
`/root/intentos/vault/inbox-files/tg-2026-09-26-08*`): NASA Fabric parametric (square cross-link, 70 tiles), NASA
Fabric V2 coaster, PipeLink chainmail (two colour), NASA Fabric: Gandalf (hex tiles, raised picture, 415 tiles),
Globe (multi-colour map). All are Standard Digital File License or BY: **reference only, we never ship their geometry**.

## Decisions (James, 26 Sep)
- Customers can ask for **all four**: fabric in a shape, a picture on the fabric, a multi-colour picture, and a
  remix of an uploaded fabric file.
- **Our own tile generator**: one proven, tested generator. The AI only chooses the outline, size and picture; it
  never models tiles.
- **Square cross-link tiles first, hexagon later.**

## What fabric is (for the build)
A flat sheet of many separate tiles, each linked to its neighbours so the sheet prints in one go, flat on the bed,
with no supports, and then flexes like cloth. Each tile is its own body. Neighbours never touch; they are captive.
Tiles can't be pulled apart in any direction, but they slide and hinge within the gap.

## Phases (each ships on its own)
1. **Generator + print swatch** (model-forge `scripts/fabric.py`):
   - Square cross-link tile, parametric: pitch, tile height, link gap.
   - Fill any 2D outline (rectangle, circle, polygon, SVG path, text) with whole tiles; tiles on the edge are dropped
     if more than half is outside.
   - Export one 3MF with one object per tile (or one mesh with N bodies), sized for the A1 bed (256 mm).
   - Checks in code:
     - no two tiles touch: minimum gap ≥ the chosen clearance;
     - every neighbour pair is captive: moving one tile 2 mm along ±x, ±y or +z collides;
     - it slices with no supports.
   - Deliverable for James: a **gap swatch**, three 40 x 40 mm patches at 0.3 / 0.4 / 0.5 mm clearance, on one plate.
   - **MANUAL gate:** James prints it and says which gap flexes freely without fusing. That number becomes the
     default.
2. **TweakMyPart integration:**
   - The brief recognises a fabric request and offers shapes and sizes.
   - The sandbox calls the generator (never hand-models tiles).
   - Host gates accept the expected body count and check tile gaps. The body count, not the gap check, is what
     separates a real fabric from a fused sheet.
3. **Picture on the fabric:** an image or text becomes a height map; each tile's top gets that relief (single
   colour, like Gandalf).
4. **Multi-colour picture:**
   - Each tile, or the tile top, gets one of 2–4 colours from the image (quantised).
   - The 3MF assigns filaments per object for the A1's AMS lite.
   - The ready page says which filament goes where.
5. **Hexagon tiles:** a second tile style in the same generator.
6. **Remix an uploaded fabric:**
   - Card fixes first: the coaster crashed the 3MF parser, and PipeLink (123 MB) and Globe (63 MB) are too big to
     measure in 60 s.
   - Then "change the outline / size / picture" regenerates with OUR tiles in the new shape. We keep the customer's
     look choices, not their tile geometry, unless the tile is theirs.

## What customers can make (James, 26 Sep: "clothing, coasters, wrist bands, watch straps and more?")
- **Flat items within one bed (≤ 256 mm):** coasters, bookmarks, patches, wall hangings, placemat pieces. Phases 1–2.
- **Bands and straps:** fabric plus SOLID ends (a clasp, a buckle, or watch spring-bar lugs). That is fabric joined to
  an ordinary part: phase 2b. The generator leaves "anchor" tiles at the ends that a solid part links into.
- **Clothing:** only as panels (bed limit 256 mm) printed separately and joined with the same links along their
  edges. Later phase (after hex); needs a panel-join edge mode in the generator.

## Proof per phase
1. The generator's own tests pass (gaps, captive pairs, slicing). James prints the swatch and picks the gap. A
   40 x 40 patch flexes by hand.
2. Staging: "a 90 mm round coaster in fabric" → ready; body count = tile count; it slices with no supports.
3. Staging: "fabric bookmark with my name on it" → the name reads in relief across the tiles.
4. Staging: a 2-colour logo coaster → the 3MF opens in Bambu Studio with 2 filaments assigned.
5. Hex coaster as in 2.
6. Upload the coaster file → "make it a bookmark" → our tiles in the new outline.

## Out of scope
Shipping anyone else's tile geometry. Non-flat (draped or 3D-formed) fabric. Fabric inside other multi-part
designs, for now.

## Status
- **Phase 1 SHIPPED** (26 Sep, model-forge #14): `scripts/fabric.py` square cross-link generator + gap swatch
  (`models/fabric-swatch/`); James to print it and pick the gap (0.4 mm placeholder).
- **Phase 2 SHIPPED** (26 Sep, model-forge #15 + printtweak #109 → prod 8f30504):
  - the brief offers fabric items (one tile style, items/outlines differ);
  - the sandbox always calls fabric.py;
  - the host re-measures with `fabric.py --check` (tile size from the geometry, equal tile volumes, gap, fused pairs)
    and expects `--bodies <tiles>`, slices with no supports, no fins;
  - the ready page says "<N> linked tiles, <gap> mm gap".
  Staging proof: a 90 mm round coaster → ready, 69 tiles, no supports, ~1.5 min build.
- Lander: the "coming soon" section shipped (#108); the lander session (printtweak-1f) was told phase 2 is live and
  switches it to "available".
- Next: phase 2b straps (anchor ends), phase 3 pictures, phase 4 colours, phase 5 hex, phase 6 remix (card fixes).

## Decisions (James, 26 Sep, later)
- **Fabric starter page:** "Design your own fabric" → shape picker + size + live tile preview → order. Preset orders
  run the generator on the host with NO AI (deterministic, seconds). Custom shapes stay in the normal chat. Plan:
  [[2026-09-26-fabric-starter-plan]].
- **Tile styles with pictures** (square / hexagon / scales) are offered only once hex (phase 5) AND a scale tile exist.
  Scales are a new tile style, added to the spec.
