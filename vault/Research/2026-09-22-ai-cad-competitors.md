# AI-CAD competitor facts — 2026-09-22

Facts only, one source per claim, "not stated" where the site is silent. Gathered via WebFetch on the given URLs + linked pricing/docs pages, plus one web search per product for real-world reports.

## 1. AiCadGen — aicadgen.com

| Question | Answer | Source |
|---|---|---|
| Output | STEP (AP242 B-Rep), STL, OBJ, also DXF/PDF drawings per marketing search result | [aicadgen.com/use-cases/mechanical-parts](https://aicadgen.com/use-cases/mechanical-parts), search result |
| Input | Text-to-model only; no image-to-model mentioned | same |
| Approach | Not disclosed beyond "generated parametrically from your numbers" | same |
| Accuracy/editable | Claims exact dimension honouring ("60mm is 60.000mm"), editable B-Rep bodies opening in SolidWorks/Fusion/FreeCAD, feature-recognition can rebuild a parametric tree | same |
| Manifold/printability | Not explicitly stated on this page; a `/3d-printing` use-case page exists (not fetched) | same |
| Pricing | "Subscriptions from $5/mo", 7-day free trial, credit-based, credits don't roll over, commercial licence on paid plans | [aicadgen.com/pricing](https://aicadgen.com/pricing) |
| API/SDK | Not mentioned anywhere fetched | both pages above |
| Stage | Live (active billing, no beta/waitlist language); copyright 2026 | pricing page |
| 3D-printing positioning | Homepage tagline calls itself "AI CAD generator — text to printable STL, STEP & DXF" | search result title |
| User reports | None found on Reddit/HN in search; only marketing "best AI CAD tools" listicles reference it | WebSearch, no direct community threads found |

## 2. Ragnar — ragnar.build/text-to-step

| Question | Answer | Source |
|---|---|---|
| Output | STEP (AP214), STL, DXF (beta), GLB | [ragnar.build/text-to-step](https://ragnar.build/text-to-step) |
| Input | Both — text-to-model and image-to-model (photos/renders/sketches), plus can import existing STEP/DXF | same |
| Approach | B-Rep geometry with "true features" (fillets as arcs, holes as cylinders), not frozen mesh; no LLM/kernel name given | same |
| Accuracy/editable | Claims "fully editable in any professional CAD software", feature-recognition compatible, "production-grade geometry" for manufacturing/3D printing/CNC | same |
| Manifold/printability | Claimed suitable for 3D printing and CNC; no manifold-check or tolerance spec stated | same |
| Pricing | Free tier: 15 credits/month, no card required; usage-based credits (2.5–14 credits/part depending on complexity); cancel anytime | same |
| API/SDK | Not stated — no API/SDK link found on the page | same |
| Stage | Live app at app.ragnar.build; copyright shows "2026" | same |
| 3D-printing positioning | Explicit — "production-grade geometry suitable for manufacturing, 3D printing, CNC" | same |
| User reports | No Reddit/HN discussion found; search returned unrelated "Ragnar" results (video game, RAG library) — the product has effectively no visible community footprint | WebSearch |

## 3. Scenario PartCrafter — help.scenario.com

| Question | Answer | Source |
|---|---|---|
| Output | Mesh only — `.glb`, 2–16 separate meshes per generation, geometry only, **no textures** (as of 07/21/2025) | [help.scenario.com article](https://help.scenario.com/articles/2351493058-partcrafter-generate-in-parts-the-essentials) |
| Input | Image-to-3D only (single RGB image); not text-to-model | same |
| Approach | "Compositional latent diffusion transformers with hierarchical attention"; trained on 130,000+ labeled meshes from Objaverse/ShapeNet/ABO | same |
| Accuracy/editable | No dimensional-accuracy or manifold claim; explicitly a segmentation/mesh-splitting model, not solid CAD; user cannot choose which parts split out, only how many (2–16) | same |
| Printability | Not addressed on this page | same |
| Pricing | Not stated on this page (no pricing/free-tier info found) | same |
| API/SDK | Yes — "available via the Scenario API", docs at docs.scenario.com; open-source model, GitHub repo (wgsxm/PartCrafter), NeurIPS 2025 paper | same, [GitHub](https://github.com/wgsxm/PartCrafter) |
| Stage | Live inside Scenario web app + API; research paper accepted NeurIPS 2025 | same |
| 3D-printing positioning | None stated — positioned as a game-asset/3D-content generation model, not a printing tool | same |
| User reports | No Reddit reviews found; coverage is academic (arXiv) and Scenario's own comparison articles vs Hunyuan/Tripo/Rodin/Trellis | WebSearch |

## 4. Zoo (formerly KittyCAD) — zoo.dev/zookeeper

| Question | Answer | Source |
|---|---|---|
| Output | Not explicitly listed on the zookeeper page itself ("fully editable 3D models"); Zoo's separate Text-to-CAD product is known (external sources) to export STEP/other CAD formats via its KittyCAD design API | [zoo.dev/zookeeper](https://zoo.dev/zookeeper); [3dprintingindustry.com](https://3dprintingindustry.com/news/open-source-ai-text-to-cad-software-by-zoo-unlocks-accessible-3d-design-236964/) |
| Input | Text-to-model via conversational prompts; image-to-model not mentioned on this page | zoo.dev/zookeeper |
| Approach | "AI-native CAD platform built on our high-performance geometry engine"; generates code in Zoo's own **KCL** language rather than a mesh; agent can "inspect, snapshot, and debug geometry" | same |
| Accuracy/editable | Claims "production-ready CAD", "fully editable", dimensional accuracy emphasized via mm/inch examples; no explicit tolerance/thread/fit claim | same |
| Printability | Not explicitly mentioned; framed around "real-world manufacturing workflows" generally, not 3D printing specifically | same |
| Pricing | Free plan + Pro plan exist but exact tier numbers did not load on the fetched page; Enterprise = "unlimited Zookeeper credits" | [zoo.dev/zoo-pricing](https://zoo.dev/zoo-pricing) |
| API/SDK | Yes — API and Zoo MCP, "metered separately", pay-as-you-go, no charge for failed calls; exact per-call rates not disclosed on the pages fetched; no self-host option found | [zoo.dev/api-pricing](https://zoo.dev/api-pricing) |
| Stage | Live, actively developed (2026 copyright, 2026 blog activity referenced by third-party review). Rebranded from KittyCAD to Zoo Jan 2024 | search result citing 3dprintingindustry.com and getleo.ai |
| Company stage | Total raised **$35.5M** across pre-seed/seed rounds (Undeterred Capital, Liquid 2 Ventures, Venrex, a16z, Madrona, Nat Friedman among investors); founded as KittyCAD 2021, HQ Inglewood, California; "Seed VC-III" latest round per search, i.e. no Series A yet as of search date | WebSearch citing Crunchbase/PitchBook aggregation; [zoo.dev/zookeeper](https://zoo.dev/zookeeper) (address) |
| 3D-printing positioning | Not explicit on this page | zoo.dev/zookeeper |
| User reports | Named by a third-party comparison (getleo.ai) as one of three tools "getting the most traction" in text-to-CAD alongside Adam (Datagrok, YC W25) and Spectral Labs SGS-1; no direct Reddit thread found | WebSearch |

## 5. PrintPal — printpal.io/ai-cad-modeler

| Question | Answer | Source |
|---|---|---|
| Output | STL, 3MF, STEP (AP214 B-Rep, "faceted geometry" per site's own wording), OFF, raw OpenSCAD source | [printpal.io/ai-cad-modeler](https://printpal.io/ai-cad-modeler) |
| Input | Both — text-to-CAD ("M3 corner bracket, 30mm legs") and image-to-CAD (hand sketches, photos, technical drawings) | same |
| Approach | Generates **parametric OpenSCAD code** (not a raw mesh or opaque B-Rep), compiled client-side via WebAssembly for live preview; uses `@feature`-tagged comments for stable references; BOSL2 library for standard parts (gears etc.) | same |
| Accuracy/editable | Claims: dimensions adjustable via sliders/code; auto-validation for manifold/watertight/min-wall-thickness; "design contract" brief+checklist before generation; bounding-box check of output vs committed envelope; auto-repair loop for OpenSCAD compile errors | same |
| Printability | Explicit manifold/watertight/wall-thickness checks claimed (see above) — most specific printability claim of the five products | same |
| Pricing | Free: browser rendering/export/history always free, 10 AI generations/month, no card. Paid: pay-as-you-go credits ($1=100 credits; basic part ~8cr/$0.08, detailed ~40cr/$0.40) or Membership $20/mo ($192/yr) for 2,500 credits/mo (~62 detailed parts). Enterprise: custom + API access | [printpal.io/cad-agent-pricing](https://printpal.io/cad-agent-pricing) |
| API/SDK | Yes, documented: `POST /api/generate`, `GET /api/generate/{id}/status`, `GET /api/generate/{id}/download`; API-key auth (`pp_live_...`); official Python + JS client libs (open-source on GitHub); rate limits 50 req/min, 10k/day, 5 concurrent; cost from 4 credits (~$0.04) for a 256³ default-quality mesh up to 100 credits (~$1) for a 1536³ textured mesh — note this pricing table describes **mesh generation**, distinct from the OpenSCAD/CAD-agent pricing above; no self-host option documented | [printpal.io/api/documentation](https://printpal.io/api/documentation) |
| Stage | Live, no beta/waitlist language | cad-agent-pricing page |
| Company | Founded 2021, Chicago IL; "Incubator/Accelerator, Alive" status; NVIDIA Inception Program listed as an affiliation (not confirmed as investment) | [cbinsights.com/company/printpalio](https://www.cbinsights.com/company/printpalio) |
| 3D-printing positioning | Explicit and central — targets "engineers, makerspaces, hardware startups, educators, print farms, OpenSCAD power users"; contrasts itself with "throwaway STLs" by emphasizing re-customizable parametric output | printpal.io/ai-cad-modeler |
| User reports | No Reddit reviews found; only PrintPal's own blog/resources pages and a SelfCAD blog post ("PrintPal AI 3D Generator: All You Need to Know") surfaced | WebSearch |

## Cross-cutting note on user reports

None of the five products turned up a genuine Reddit/HN/YouTube user thread in search — the space is young enough (or low-visibility enough) that coverage is limited to vendor pages, listicle blogs ("Best AI CAD Tools 2026"), and arXiv papers. One relevant general finding from academic sources (CADSmith, CAD-Coder papers): text-to-CAD LLM pipelines commonly fail to produce valid/geometrically-correct code in a single pass and need iterative geometric-validation loops to catch dimensional errors — directly relevant to any vendor claiming "exact dimensions" or "manifold" with no stated verification loop (AiCadGen, Ragnar, Zoo make such claims without describing a verification step; PrintPal is the only one of the five that explicitly describes a validation/auto-repair loop).

## For a builder of a rival product

| Product | (a) Competitor to "plain-English → custom printable part"? | (b) Usable as a component for us? |
|---|---|---|
| **AiCadGen** | Yes, direct — text-to-solid-CAD for makers/engineers, STEP+STL output, positions itself for 3D printing | Not obviously — no API, closed pipeline, no reason to route through a rival's product |
| **Ragnar** | Yes, direct — text/image-to-STEP for CNC/printing, cheap credit pricing, likely the closest positioning match of the five | No API found; could only be studied for UX/pricing, not integrated |
| **Scenario PartCrafter** | No — it's an image-to-mesh part-splitter for game/3D-content assets, no CAD/print positioning, geometry-only mesh output, no textures | **Yes, plausibly** — it is open-source (GitHub) with a published API, and does exactly "mesh-to-multi-part-mesh" splitting; could be evaluated as a component for splitting a single generated mesh into printable sub-parts before a mesh-to-solid conversion step, since it's already live via docs.scenario.com and free to inspect on GitHub |
| **Zoo / Zookeeper (KittyCAD)** | Yes, but enterprise/manufacturing-workflow framed rather than hobbyist-printing framed; well-funded ($35.5M), most established brand in text-to-CAD | Their underlying **KittyCAD geometry engine + API is the most credible "text-to-STEP as a component" candidate** of the five — it's a real funded geometry kernel with a metered API (not just a wrapper around an LLM), so if a licensable/API tier exists it's worth a direct pricing conversation rather than treating them purely as a competitor |
| **PrintPal** | Yes, most directly comparable — same audience (makers/print farms), OpenSCAD-based parametric output, explicit manifold/wall-thickness checks, has a public API | Their **API is fully documented and cheap** (per-call credit pricing, Python/JS clients) — could technically be called as a mesh-generation backend, but doing so would mean building on a direct competitor's infrastructure; more useful as a reference for what a "design contract + auto-validate" pipeline looks like than as a component to depend on |

**Overall**: AiCadGen, Ragnar, Zoo, and PrintPal are all real competitors for "describe a part in English, get a printable model" — Ragnar and PrintPal are closest in positioning/pricing to a hobbyist/maker rival product. PartCrafter is not a competitor at all; it's a narrow open-source mesh-splitting model that is the one candidate worth evaluating as a licensable/self-hostable component (mesh → separated parts) rather than a rival to beat.
