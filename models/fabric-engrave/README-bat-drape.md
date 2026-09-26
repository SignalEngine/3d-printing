# bat-drape (face engrave, one filament swap)

two oval eyes and a fanged mouth. Tile: **drape**, 101 tiles, engraved 0.2 mm into the face.

**Load the FACE colour (colour 1) first.** Bambu Studio: slice, open Preview, drag the layer slider to **layer 2**,
right-click the `+` and choose **Change filament**. The A1 pauses once (after layer 1); load colour 2 and resume. No swap back.
The bed side is the face. The design shows in colour 2 in the pockets cut into it.

- Print flat, supports OFF. Settings: no brim, elephant foot 0.15, 2 walls, 0.20 mm layers.
- Swap at layer 2 (Z 0.2 mm). Colour 1 is layer 1 (the face), colour 2 fills the pockets from layer 2.
- Every tile keeps a 1 mm colour-1 rim so it still sticks to the bed: 0 tiles had the design clipped to keep their bed grip; 3 design pieces under 0.8 mm wide dropped.
- The design is drawn in the outline's top view (`face-bat-drape.json`); a person looking at the face sees it mirrored left-right (these faces are symmetric).
- Check: `fabric.py --check bat-drape.3mf --gap 0.4` -> ok=True, 101 tiles, 101 bodies, min gap 0.4 mm, 0 fused.
- Rebuild: `build.py`.
