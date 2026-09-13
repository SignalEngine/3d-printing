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

## Decision

Pending James's pick. Log with `idea-decide "20260913-153240" "<choice + why>"`.
