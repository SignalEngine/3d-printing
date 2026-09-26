# Fabric from any shape: picture trace + word-to-silhouette (build plan, 26 Sep 2026)

Spec: [[2026-09-26-fabric-spec]]. It builds ON the fabric starter page ([[2026-09-26-fabric-starter-plan]]), so start
only after that merges. James, 26 Sep:
- "build the silhouette upload trace too";
- the picture needn't be black and white, because we make it black and white;
- for "a pumpkin / pet shaped / whatever", the AI draws the silhouette and then we trace it.

Decisions:
- **Word → shape:** the AI draws the silhouette as a vector drawing. It costs pennies, and there's no copyright risk
  and no image-model account. No web image search.
- **Photos:** automatic background cut-out with a small free model on OUR server. It costs nothing per use.

## Current state (26 Sep afternoon)
- The starter page is LIVE (printtweak #113): `app/(main)/design/fabric/FabricStarterClient.tsx`,
  `convex/lib/fabricPreview.ts` (client preview + parity fixtures), `createFabric` + the `fabric` job kind,
  `worker.process_fabric` (host runs fabric.py, no AI), the brief lane takes fabric jobs.
- fabric.py (model-forge) has `--outline poly:/heart:/rrect:/circle:/rect:/text:`, `--tile square|drape` (default
  square), `--tiles-glb`, and `--check`. Add `image:` here; the preview must use the SAME tile as the build (the
  default square today, pitch 10).
- Prior art for a host-side trace: none. For a short AI job, reuse the `vision_check` container pattern
  (`worker/vision_check.py` + `worker/job/vision_job.py`).

## Worktrees
- `3d-printing` (model-forge): `/root/wt-3dp-trace`, branch `build/fabric-trace`. Merges first.
- `printtweak`: `/root/wt-pt-trace`, branch `build/fabric-silhouette` (off origin/master AFTER the starter page
  merges).

## A. model-forge
1. **`scripts/silhouette.py`:** any image → a clean black-on-white silhouette PNG + the outline polygon.
   - Input types:
     - PNG with transparency: alpha → mask.
     - Plain background (logo, drawing): Otsu threshold on luminance, pick the side that is NOT touching the image
       border.
     - Photo (busy background): background removal with `rembg` (onnxruntime, CPU; model `isnet-general-use` or
       `u2net`; measure which gives the cleaner pet/object mask on 3 test photos you make or find with a permissive
       licence; note the model size and runtime).
   - Clean-up: keep the largest connected blob, fill holes smaller than one tile, smooth, then simplify the outline
     (Douglas-Peucker ~0.5 % of width).
   - Output JSON: `{ok, outline: [[x,y]...] (mm at the requested width), mask_png, method: alpha|threshold|rembg,
     detail}`.
   - Refuse with a plain reason if the shape is too thin to hold tiles at pitch 10 (the result would be under 3
     tiles, or split into islands).
   - Add `rembg` + `onnxruntime` to the 3d-printing venv ONLY; say so in the report with sizes. The job image is
     unaffected, because trace runs on the host.
2. **`fabric.py --outline image:PATH[@W]`:** trace via silhouette.py, then fill with tiles at width W mm.
3. **`fabric.py --outline heart:W`** already exists from the starter-page work (check). Reuse the pattern.
4. Tests: a synthetic black circle PNG traces to about a circle, and its tile count is within 10 % of `circle:D`; a
   transparent PNG uses the alpha method; a white-background logo uses threshold; an image that is all noise is
   refused; a too-thin shape (1 px line) is refused. A rembg test runs on one small committed test photo you generate
   (e.g. a rendered object on a busy synthetic background), so no downloaded copyrighted photos; skip with a reason if
   the model can't load.

## B. TweakMyPart starter page: two more cards
- **"Your own picture":**
  - upload (png/jpg/webp, ≤ 8 MB) → a Convex action/worker preview job traces it;
  - the page shows the silhouette over the photo plus the live tile preview;
  - the customer confirms or retakes, sets the width, then "Make it" → the fabric job with `shape: "image"`, the
    storage id, and the traced outline (stored, so the build is the exact confirmed shape).
- **"Describe a shape"** (e.g. "a pumpkin", "a sitting cat"):
  - a small AI job draws a single closed silhouette as an SVG path;
  - reuse the vision_check container pattern (a short sandbox run on the subscription, Haiku/Sonnet, tight prompt:
    one closed outline, recognisable at a glance, no holes smaller than 10 mm, no thin spikes);
  - the host rasterises it and runs silhouette.py (the same trace + clean-up), and the customer sees it and confirms.
  - Cost: log it on the job (expected pennies). Rate-limit it like brief rounds, and the free-rounds counter applies.
- **Worker:** `process_fabric` accepts `shape: "image"` with a stored outline. No AI at build time: the outline was
  confirmed by the customer.
- **Preview jobs:** a new job kind `"silhouette"` (upload trace or word draw). Returns the outline + mask PNG
  (storage) to the page. Upload-trace jobs cost nothing; word jobs log their AI cost.
- **Safety:** uploaded images are data. Strip EXIF. Refuse anything that isn't an image. Size caps.

## Fit within the fabric (James, 26 Sep: "it needs to fit within the fabric")
Every shape becomes whole 10 mm tiles, so detail finer than about 2 tiles (whiskers, thin legs, a stalk) is lost.
- The preview ALWAYS shows the TILED result (the kept cells), never just the smooth silhouette. The customer
  confirms what will actually print.
- A readability check at tile resolution:
  - refuse or warn if the kept cells lose more than ~30 % of the silhouette area, or split it into islands;
  - suggest the width at which the shape keeps its features ("looks better at 160 mm").
- The word-shape prompt asks for a bold, chunky silhouette with no parts thinner than 2 tiles at the chosen size.
- Hex/scale tiles later: the same rule at their own cell size.

## C. Tests (each red without its code)
- model-forge as above.
- Worker:
  - the silhouette job traces a synthetic PNG into an outline;
  - process_fabric with a stored outline ships N tiles and never calls the sandbox;
  - the word job builds a prompt and parses one closed path (fake client);
  - a bad SVG → a plain refusal.
- Convex:
  - createFabric with `shape: "image"` requires a confirmed outline (bounded point count, finite, within the bed);
  - the silhouette job flow;
  - guards apply.
- TS:
  - the cards render;
  - upload → preview state → confirm;
  - labels on the inputs.

## Checks (builder pastes, exit codes captured)
model-forge pytest, `npx tsc --noEmit`, `npx vitest run`, worker pytest. Explicit-path commits; don't push.

## Staging proof (brain)
1. Upload a pet-like test photo → silhouette shown → confirm at 120 mm → ready, "N linked tiles".
2. "a pumpkin" → a drawn silhouette that reads as a pumpkin → confirm → ready.
3. design-gate on the starter page on mobile with the new cards.
