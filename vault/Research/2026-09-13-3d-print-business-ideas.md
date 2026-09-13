# 3D print business ideas: panel results

2026-09-13. Built on [[2026-09-13-3d-print-business-research]]. Process: problem statement → 5 blind proposers (MiniMax, GLM, Gemini, GPT, DeepSeek) → scored by the brain session → critique panel on the winner → web fact-check. Run id `20260913-153240`.

**Grades:** VERIFIED = checked source. INFERRED = reasoning, not evidenced.

## The brief the panel got

Profitable, defensible business using 3D printing plus the customiser/model-generation stack. Targets: buyer cannot get it from a free customiser or a £2 Etsy print; >£10 gross per printer-hour; low labour per order; a specific reachable buyer with a painful need; starts on 1-3 A1s. Banned: generic print farm, "customise anything" site, selling STLs, generic print-your-file service.

## Scores (1-5 per axis; Worth = value + distinctiveness + prior art, Doable = fit + cost + reversibility + confidence)

| Idea | Worth /15 | Doable /20 | Total | Reason |
|---|---|---|---|---|
| Tactile + braille room signs from a door schedule | 12 | 14 | 26 | Compliance purchase, batchable flat prints, no free tool does braille |
| Custom 10"/19" rack mounts from a device list | 10 | 15 | 25 | Real homelab/MSP demand; many buyers own printers and free STLs abound |
| Discontinued caravan interior parts by model/year | 12 | 13 | 25 | Strongest pain, older non-printer buyers, fitment database is a moat; needs real parts to validate |
| Vet surgical planning models | 10 | 9 | 19 | Scan-to-model is hard, slow sales, liability |
| Custom electronics enclosures | 4 | 13 | 17 | Tried and failed (XPAD, Reddit Sep 2026); JLC/PCBWay cheap |

What would have to be true for enclosures to beat signs: makers without printers or CAD skills exist in volume and pay £50+ — no evidence of that.

## After critique + fact-check: signs dropped from winner to "spike first"

The fact-check found three things that change the score:

1. **UK signs use Grade 2 (contracted) braille**, not Grade 1 as the proposal assumed. VERIFIED (3 sources). Translation is harder; mistakes matter more.
2. **A specialist braille-sign maker warns 3D-printed tactile signs suffer adhesion failure and warping "months to years" later.** Industry uses UV print, photopolymer, or raster acrylic beads. No one found selling BS 8300 FDM braille signs. VERIFIED (Pictobraille), no counter-evidence.
3. **The braille dot geometry sits in BS EN ISO 17049 (paywalled).** Can't confirm an A1 hits it without buying the standard. VERIFIED gap.

In its favour: incumbents charge a lot — one 150×150mm tactile sign from RS PRO is £45-54. VERIFIED. Headroom exists if the print quality does.

Critique-panel cruxes still open: does a blind reader read FDM dots after 100 disinfectant wipes; do schools/care homes require fire-rated sign material; do facilities managers buy before an audit forces them; will sign shops leave trade suppliers.

**Revised read (INFERRED):** signs is now the highest-risk idea, not the best. It lives or dies on one cheap physical test — print plates, have blind readers try them, wipe them 100 times.

## Caravan parts: fact-check

- Demand evidenced only anecdotally: a forum thread on "no longer available" parts, one hobbyist printing replacements. Existing UK Etsy caravan sellers make small accessories, not discontinued trim. Possible real gap, volume unproven.
- UK touring-caravan fleet size not found (needs CRiS/NCC data).

## Graft worth keeping from any winner

From caravan parts: **a fitment database** — every confirmed order (model/year/measurement/fit result) makes the next order instant. This is the moat the research said configurators lack, and it applies to rack mounts too (device library).

## Do not build

- Electronics enclosures — the exact failure mode already on Reddit.
- Vet models — regulatory and sales-cycle cost far above a solo founder's reach.
- Any portal before a paid pilot — every critique flagged "validation too small" as a repeat pattern.

## Before committing to any of the top three (mechanical checks)

| Idea | Check | Kill if |
|---|---|---|
| Signs | Print 5 plates PLA+PETG; blind-reader test; 100 wipe cycles; buy/borrow ISO 17049 dot spec and measure with calipers | <80% cells read correctly, or dot height below spec after wipes |
| Rack mounts | Post 3 rendered configs on r/homelab, r/Ubiquiti with a pre-order link | <10 paid orders at £50+ in 14 days |
| Caravan parts | Find 20 real "discontinued part" requests across caravantalk / ukcampsite / Facebook groups for one make; list 10 parts; check eBay sold prices | <20 requests for one make, or sold prices under £25 |

## Round 1 decision

James picked the caravan parts demand check (logged). Result: **not measured, not dead**. Forums (caravantalk, motorhomefacts) and eBay sold listings blocked every scraper, so ~5 Swift requests were found and prices were not checked. Positive sign: motorhome3dprints.com (UK) already sells printed motorhome replacement parts.

---

# Round 2 (same day): Halloween, photo-to-print, missed models, AI Remix SaaS

James asked: would his printed T-Rex skull sell, how were trends found, what about an AI photo → questions → quote → print site, what did we miss, and should model-forge become a £5 "AI remix" SaaS. Run id `20260913-155420`.

## Honest answer: how trends were found

Badly in round 1: /last30days was blocked by Reddit partway through and found nothing on YouTube; the web agents mostly read printer-seller SEO lists. No sold counts. Round 2 tried Etsy bestseller badges, eBay sold listings and MakerWorld download counts, but **Etsy, eBay and MakerWorld all block scrapers** (WebFetch and Firecrawl including stealth proxy). VERIFIED. Real numbers need James's own browser (Claude-in-Chrome) or a paid Apify Etsy/eBay actor.

Free method James can use by hand: Etsy search → note "Bestseller" / "Popular now" badges and "X people bought this in the last 24 hours"; eBay → filter Sold items; MakerWorld/Printables → sort by downloads in a category. Paid: eRank, EverBee, Alura (not tested).

## T-Rex skull + Halloween

- Skulls, pumpkin/glow lamps, ghosts, articulated dragons/skeletons, door toppers, tombstones recur as Halloween sellers. INFERRED from search snippets, no sold counts.
- T-Rex skulls on Etsy run ~£20 small up to large 29cm prints; painted, aged or glow versions price higher. INFERRED.
- **The popular MakerWorld "T-rex Skull" (TreeD-prints) needs a paid commercial licence to sell prints.** VERIFIED. Downloaded file = cannot sell without the licence; own design = fine.
- Avoid Universal Monsters etc. (trademark).

## Photo / idea → AI → quote → print

- Nobody runs the full loop. Bambu MakerLab, Meshy/Tripo, Backflip make decorative meshes. VERIFIED
- **No tool infers real dimensions from an ordinary photo** — "fix my broken thing from a photo" is unsolved unless narrowed to a catalogued product family. VERIFIED (no counter-evidence)
- Household printer ownership ~1-2%; >70% of entry buyers churn. "Everyone has a printer" is false. VERIFIED-ish
- Demand for "make it for me": r/3Dprintmything 45k members; Fiverr/Upwork CAD $50-500/part. VERIFIED
- Where AI quality is enough today: pet memorial / photo gifts, minis of yourself.

## AI Remix SaaS (James's idea)

- No chat-edit feature on MakerWorld, Printables, Thangs, Cults3D. VERIFIED (search, not exhaustive)
- Bambu shuts PrintMon Maker + AI Scanner on 20 Sep 2026 citing quality/UX, promises redesigned AI tools. VERIFIED
- **MakerWorld ToS bans automated/AI access to its content; default licence bans derivatives; CC-ND forbids remix.** Paste-a-link is blocked; user upload + per-licence check is the only clean path. VERIFIED
- The in-house poop-bag holder remix had 5 geometry bugs on attempt 1 and needed several rounds plus a custom gate ([[2026-09-13-stl-edit-lessons]]). Per-remix cost at £5 likely thin. INFERRED (not measured)
- MakerWorld ~10M MAU, 2.6M models. VERIFIED

## Missed models with revenue evidence

Contract manufacturing for other sellers (Slant 3D, $1.5M raise, scaling to 3,000 printers); print-farm software (Printago, AutoFarm3D); tabletop terrain Patreons; jigs/fixtures for local manufacturers (gap, unproven); architectural models (slow B2B).

## Round 2 proposals, scored

| Idea | Worth /15 | Doable /20 | Total | Reason |
|---|---|---|---|---|
| Own-brand personalised occasion shop: AI generates original Halloween→Christmas designs, buyer personalises, proof, print (proposers 1+2 merged) | 12 | 15 | 27 | Proven Etsy category, sidesteps licences, uses the pipeline on sources you own |
| Photo → stylised relief luminaries/plaques: ghost pet, pet memorial lamp (proposers 3+4 merged) | 12 | 15 | 27 | Within today's AI capability, emotional £50+ gift; muddy-relief risk untested |
| Photo → 3D figurine (proposer 5) | 10 | 13 | 23 | Mesh quality in single-colour PLA is the weak point |
| AI Remix SaaS as pitched (James) | 10 | 12 | 22 | Unbuilt wedge, but licence wall, reliability and £5 economics |

Every proposer that scored the Remix SaaS gave it ~3/10 standalone and ~8/10 as the internal engine of a shop that owns its designs.

Merged winner = occasion shop with the photo-relief luminary as the hero product.

## Round 2 critique (idea-panel)

Agreed by all three perspectives:
- The £3-6k Halloween revenue estimate is unevidenced.
- Single-colour glow PLA is a visual weakness next to multicolour and resin decor.
- Personalised items carry more disputes and refunds than generic ones.
- Lithophane lamps are the proven fallback format.
- Etsy's AI-disclosure rules add friction the plan ignored.

Disagreements and their cruxes:
1. **Demand, not production, is the bottleneck** (skeptic, and James's own past pattern of "test from outside first"). Doubling SKUs does nothing if a zero-review shop gets no impressions.
2. **New Etsy shop in 5 selling weeks:** one side says 7 sales/day, the other says 1-3/day at best. Crux: does a new shop exit ad learning within 14 days?
3. **Relief vs lithophane:** a front-lit PLA depth relief may read as a topographic blob; a backlit lithophane hides muddy mid-tones and is proven. Crux: can a stranger identify the pet in a relief without being told?
4. **Margin at realistic volume:** at 2 sales/day after ~12% Etsy fees, £6-12 per-sale ad cost, postage and 25% failures, margin may be negative.

Revised plan (INFERRED, brain judgement):
- **Test demand before building any web app.** Build nothing platform-shaped this season.
- Hero product becomes the **pet lithophane lamp**; the relief becomes a 5-photo side test.
- Add earlier gates: day 7 ≥50 impressions/day; day 14 ≥1 organic sale; stop ads if cost per sale >£12.
- Check the Royal Mail 2026 Halloween last-posting date (the assumed ~28 Oct is unverified).
- Keep proofs manual; no auto-approve until a dispute rate is measured.

## Kill/thrive test for the pick

| Day | Check | Stop if |
|---|---|---|
| 0-3 | 5 own-design listings live (2 personalised Halloween, 2 pet lithophane lamp, 1 skull size ladder), real photos of real prints | — |
| 7 | Etsy stats impressions, ads at £5/day | <50 impressions/day across listings |
| 14 | Orders | 0 organic sales, or ad cost per sale >£12 |
| 21 | Margin per bed-hour from real orders | <£10 gross/bed-hour → no 2nd printer |

## Round 2 decision

James parked it. Later the same day he asked for live data via his Chrome, dropped the lithophane lamp (electric parts + supply chain + support), and asked for deeper research on the "remix and customise anything" SaaS.

---

# Round 3: live browser data, pet photo-to-3D, remix legality

## T-Rex skull

James's skull is a Smithsonian 3D scan (3d.si.edu). Smithsonian models marked **CC0** may be used for any purpose including products; some scans are **non-commercial only**. The model page blocked fetching, so the exact licence is unchecked: look for the CC0 label on the model page before selling. VERIFIED (licence scheme), UNCHECKED (this file).

## Live browser pass (James's Chrome, 13 Sep 2026)

- **Etsy UK blocked every search even in a real browser** (bot wall). **eBay sold listings forced sign-in.** No sold counts. VERIFIED
- MakerWorld "t rex skull": 682 results; top = "T-Rex Skeleton Kit Card" 46.8k downloads, 17.3k likes. VERIFIED
- MakerWorld "halloween": 999+ results; top hit is a generic "Tiny Flexi Snake" (60.9k downloads) — search mixes in non-Halloween trending prints. VERIFIED
- r/3Dprintmything has **46,139** members (about.json). The 3.4K browser reading was a misread. VERIFIED

## Reddit: do people ask to modify existing models? (JSON pass, James's Chrome)

- ~230 posts read across 8 subreddit×query combinations (r/3Dprinting, r/BambuLab, r/3Dprintmything, r/functionalprint, r/prusa3d; "modify", "remix", "customise", "edit stl", "resize", "add text", etc.).
- **Only 6 genuine "modify this existing model" requests** (~2-3%): 4 functional, 2 decorative; 2 offered to pay. VERIFIED (for what was read)
- The rest: **"design me something new" commissions** and **"print my file for me"** requests (both common in r/3Dprintmything), plus word-match noise.
- Limits: 31 of 39 counted cells were never read at title level; Reddit search matches words, not phrases; r/3Dprintmything "remix"/"customise" searches hung. So this is a sample, not a census.
- **Reading:** on Reddit, the demand is for *new designs from a description* and *printing*, not for *remixing an existing file*. Weak evidence against "lots of people ask to remix", stronger signal for "design it for me". INFERRED

## eBay UK sold listings (James signed in; ~last 90 days)

| Search | Sold results | Price (sold) |
|---|---|---|
| 3d printed t rex skull | 10 | £2.77-40, median £19.43 (22 Jul-9 Sep) |
| t rex skull replica | 23 | £7.91-258.80, median £27.99 |
| 3d printed skull halloween | 68 | — |
| 3d printed pet figurine | 12 | £2.49-44.37; photo-to-pet services £14.99-73.50 |
| 3d printed replacement part | 193 | — |
| 3d printed halloween | 633 | newest ~150 sampled |
| 3d printed dragon | 904 | newest ~150 sampled |
| custom 3d printed | 1,800+ | newest ~150 sampled |

VERIFIED counts as shown by eBay; broad searches include loose keyword matches, so large totals overstate exact-category sales.

**Reading (INFERRED):**
- **T-Rex skull as a product: thin.** ~10 sold across all UK eBay sellers in ~7 weeks at ~£19. A side listing, not a business.
- **Dragons and Halloween sell in volume** but are the commodity end (many sellers, low prices).
- **"Custom 3d printed" (1,800+) and replacement parts (193)** are the largest non-commodity signals, and match the Reddit finding that people want things *made for them*.

## Pet photo → 3D market

- AI tools (PrintPal, Sloyd, Tripo, Meshy) sell digital files/credits, not printed objects. VERIFIED (browser)
- Printed-figurine services with review data: Cuddle Clones $99 for 4", ~3 weeks, full colour, Trustpilot 4.6 (144); my3dselfie 4.9★ (584, Judge.me); my3dfigure.com 3.8★ (252); my3d-figurine.com 2.3★ (7). Quality is uneven. VERIFIED
- Bambu shuts PrintMon Maker + AI Scanner 20 Sep 2026, official reason model quality/UX. VERIFIED
- Reading: this market is occupied, and AI mesh-generation-as-a-tool is being cut back while print-and-post fulfilment survives. INFERRED

## Remix SaaS: legal reality (not legal advice)

- "Uploader is responsible for permission + notice-and-takedown" is standard (Shapeways model), but **untested against a service that actively modifies files with AI**. Pop Mart v Bambu (Labubu files on MakerWorld) settled before trial, so nothing decided. VERIFIED
- **Functional parts:** measurements and function generally aren't protected by copyright → "rebuild from scratch with same dimensions" is low risk (design right/patents can still apply). INFERRED from doctrine
- **Decorative/character models:** a from-scratch rebuild that looks the same is still likely a derivative copy; Star Athletica (US 2017) makes protection of decorative useful articles easier, not harder. INFERRED, no direct case
- MakerWorld Standard licence bans remixes; Exclusive licence allows derivatives only on MakerWorld — an off-platform remix service breaches both. CC-ND is broken by any edit. VERIFIED
- Low-risk framings: functional parts, user's own designs, CC0/CC-BY sources, personal-use exports with no hosting/sharing. High-risk: decorative/character rebuilds, paste-a-link fetching, ND/Standard/Exclusive-licence files.

---

# Round 4: can "describe it, AI designs it" answer real requests? (test, 13 Sep 2026)

James picked this test. Method: pull real r/3Dprintmything posts from the last 30 days via his Chrome, then run model-forge on 5 of them, one Sonnet 5 agent each, fully autonomous (no questions to the customer; assumptions written down). The brain session then re-ran `verify_model.py` on every file and viewed renders itself.

## Demand found while picking requests

- r/3Dprintmything: **46,139 members, 188 posts in 30 days.** VERIFIED
- **Only 7 of 188 (~4%) were genuine "design this from a description" requests.** Most posters already had a file (Printables/MakerWorld/Etsy link) and just wanted it printed. VERIFIED
- The only price in the threads: a UK pill-box poster called a £55 quote too much; a commenter said ~£6 material, "I'd charge £25 plus postage". VERIFIED

## Results

| Request | Gates (agent) | Brain re-check | Agent time | Tokens | Fix rounds | Print | Verdict |
|---|---|---|---|---|---|---|---|
| Glass knob, 15mm, M5 hole, dome | all PASS | verify PASS | 4 min | 102k | 1 (tool bug) | 22 min, 1 cm³ | Good; dome shape guessed |
| Trinket box to fit earbud case, 51×51×28.3 | all PASS incl. lid fit | verify PASS | 5 min | 108k | 1 | 2h53, 22 g | Good to stated size; real case fit unknown |
| Pill box, 5 parts, 255×70×30 | all PASS incl. fit | verify PASS; render looks right | 16 min | 170k | 0 design | 2h51, 24 g (≈44p) | Good; layout guessed (photo blocked) |
| Netgate 2100 10" 1U rack bracket, 3 parts | all PASS incl. holes | verify PASS; brain render looks right | 32 min | 255k | 2 (7 bugs caught by gates) | 9h24, 128 g | Plausible; device dims sourced online, weight unpublished |
| "Congratulation" trophy, 150 mm | all PASS, agent said render PASS | verify PASS; **brain render: letters overlap, word unreadable** | 15 min | 155k | 3 | **15h15, 122 g** | **Fail**: not sellable, and too slow to print |

Every reference photo returned 403 to the VPS, so all five were designed from text only.

## What this proves (VERIFIED unless marked)

1. **Functional parts from a text description work.** 4 of 4 functional requests produced valid, sliced, plausible parts in 4-32 minutes of agent time.
2. **Decorative text/art is where it breaks**, and **the agent passed its own broken render.** An independent visual review is mandatory; the model that built it cannot be the one that approves it (same rule as the builder/reviewer split).
3. **Gates check printability, not sellability.** The trophy passed every gate but needs 15 hours on the printer. A paid service needs a print-time / material / price check before quoting.
4. **Real-world fit is still unproven**: no part has been physically printed. Clearances are community defaults, not calibrated to James's A1.
5. **AI cost per design:** 102k-255k tokens per run on Sonnet 5 ($2/M input, $10/M output, $0.20/M cache read; claude.com/pricing, 13 Sep 2026). The input/output/cache split wasn't recorded, so the cost is estimated at **roughly $0.20-$1.50 per design**. INFERRED
6. **Customer photos:** blocked here only because the VPS can't reach Reddit's image host. In a real product the customer uploads directly, so this is not a product blocker. INFERRED

## Economics sketch (INFERRED)

- Price anchor from the thread: ~£25 + postage for a one-off printed part. Fiverr/Upwork design-only: $50-500.
- Cost per order: AI ~£0.15-1.20, material £0.05-2.50, printer time 0.4-9 h, Royal Mail + packaging ~£3-4 (unpriced), plus human review of every render (~2-5 min).
- **Demand is the constraint:** ~7 genuine design requests/month in the main UK+US request sub. A service would need its own acquisition (search ads for "custom 3d printed part", which had 1,800+ eBay sales), not Reddit alone.

## Side tests
- Relief vs lithophane: print 5 diverse pet photos both ways, post blind, ask "what is this?".
- T-Rex skull: sell only if own design or a commercial licence is bought.
