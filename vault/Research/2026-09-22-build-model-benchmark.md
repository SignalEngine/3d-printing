# Can a cheaper OpenRouter model do the build? — benchmark, 22 Sep 2026

James asked; cap $15. Harness: `worker/tests/bench` (PR #74): the real sandbox job (`DESIGN_MODEL` override) through a bench-only OpenRouter proxy, then the production host gates (watertight, slice, mechanics) and the vision judge. Four fixed requests: knob (1 part), pill box with lid (2), bracket with ears (1), two-clip strut with a rod (3, mechanics). One run each. Real OpenRouter spend: **$2.95**.

| model | passed | mean $/good build | mean min | notes |
|---|---|---|---|---|
| Claude Sonnet 5 (prod) | **4/4** | $1.17 (subscription) | 10.4 | strut 30 min / $2.68 |
| DeepSeek V4 pro | 2/4 | $0.44 SDK-reported; real OR $ ≈ $0.88 on the pill box | 6.0 | knob 1.8 min; pill box 20 min; bracket + strut "no model produced" within 2 min |
| GLM-5.2 | 2/4 (pill box lost to a vision-judge crash, not the model) | $0.10 | 8.7 | strut: 26 min, nothing produced |
| Qwen3 Coder | 1/4 | $0.26 | 1.5 | pill box failed checks; bracket failed the preview (no ears); strut stopped after 2 failures |

**Verdict: stay on Sonnet 5.** No cheap model built the 3-part strut, and where they succeeded the real OpenRouter cost was not below Sonnet's (DeepSeek pill box $0.88 vs $0.82). The one-part knob is the only case a cheap model wins on price, and that is the design that costs $0.55 anyway.

Caveats: n=1 per cell; the GLM pill-box run needs a re-run (harness bug: the vision judge container failed); DeepSeek "no model produced" in under two minutes on two requests looks like a tool-use/format failure on the Anthropic-compatible path rather than a modelling failure — worth one look before ruling it out for single-part work. Renders and job dirs: `spec/bench/renders/`, `/tmp/pt-bench/`.

Follow-up options (not started): route single-part, no-mechanics requests to DeepSeek behind a flag with Sonnet fallback on failure (saves ~$0.2 per knob-class build); re-benchmark quarterly.

## Addendum — Qwen3-VL in the photo slots (22 Sep, ~$0.16 spent)

**Questions step on James's caddy photo + his three messages** (brief_prompt as system, no tools, parsed with the real `parse_brief`):

| model | time | cost | concepts |
|---|---|---|---|
| Claude Sonnet 5 | 120 s | $0.128 | 3/3 respect "clip on, no holes, pull in": bridge clip + screw, hook brackets + turnbuckle, ratchet strap round both walls. Clean sketches, diagrams on every measurement |
| Qwen3-VL 235B instruct | 77 s | $0.005 | 2/3 sound; #3 "spring clip presses against the inner faces to pull them together" is physically backwards (pushes out — what he ruled out). Sketches usable |
| Qwen3-VL 32B instruct | 45 s | $0.002 | #3 asks "the diameter of the hole where the clip attaches" — ignores "no holes"; one sketch was an invalid SVG |

**Preview judge** (request + first front render, 11 real renders + 4 swapped pairs; NOTE: production also passes the answers, assumptions and a multi-part sheet, so absolute scores here are low for everyone): Haiku 4.5 10/15 ($0.017), Qwen3-VL 235B 9/15 ($0.003), 32B 9/15 ($0.001). All caught the swapped (wrong-object) pairs; the misses are false rejections of good parts. No quality edge; Haiku already costs ~$0.001 per check.

**Verdict:** keep Sonnet for the questions step (it is the customer's first impression, and saving $0.12 per design is small next to the $1–3 build) and Haiku for the judge. Qwen3-VL 235B is the one to revisit if brief volume makes $0.13 matter — pair it with the TypeSafe ruled-out filter, which targets exactly its failure.

## Addendum 2 — fair rerun (22 Sep, budget cap fixed)

James asked whether the test was fair. It was not quite: the Claude harness prices unknown models at Claude rates, so its budget cap stopped GLM's strut ("over budget" at a harness-counted $4.06, real $0.71) and Qwen's pill box early. Fix: `DESIGN_MAX_BUDGET_USD` override (bench only; prod default unchanged), real OpenRouter spend guard + 60 turns kept. Reran the four failed cells:

| cell | before | fair rerun |
|---|---|---|
| GLM-5.2 / 3-part strut | stopped by the mispriced cap | **PASS** — 31 min, real **$1.36** (Sonnet: 30 min, $2.68) |
| Qwen3 Coder / pill box | stopped by the cap | built, preview judge rejected — 16 min, $0.65 |
| DeepSeek V4 / bracket | quit after 13 turns | **PASS** — 2.2 min, **$0.07** |
| DeepSeek V4 / strut | quit after 8 turns | quit again after 22 turns, $0.14 |

GLM's original pill box lost only to a judge-container crash; its renders (round box + matching lid) look right to me — counted as a pass by the brain's look, not the judge.

**Corrected tally (n=1):** GLM-5.2 4/4, real OpenRouter ≈ $2.06 total (≈ $0.51 per build) vs Sonnet 4/4 at $4.69 API-equivalent ($1.17). DeepSeek 3/4 (no multi-part mechanism). Qwen3 Coder 1/4.

**Revised verdict:** GLM-5.2 is a real candidate at ~half the API cost, same speed. Caveats: n=1; today Sonnet runs on the Max subscription (£0 marginal), so the saving only exists once builds are paid on the API; the harness is Claude-tuned. Next step if wanted: 2 more repeats of GLM on all four (~$5) before routing any real traffic, then GLM-first with Sonnet fallback on failure. Spend so far ≈ $5.6 of the $15 cap.

## Addendum 3 — GLM-5.2 repeats (22 Sep, stopped by the $7 cap after 5 of 8 runs)

| run | result | real OpenRouter $ | min |
|---|---|---|---|
| knob r2 | pass | 1.17 | 9.1 |
| pill box r2 | pass | 2.50 | 9.7 |
| bracket r2 | pass | 0.81 | 8.3 |
| strut r2 | **fail** (no model) | 0.80 | 17.0 |
| knob r3 | **fail** (host mechanics gate: hole sizes wrong) | 0.58 | 10.0 |

**All GLM runs (9):** 7 pass, 2 fail (78 %). Real spend ≈ $7.9 → **≈ $1.13 per successful build**, with huge variance (the same knob cost $0.04 once and $1.17 the next time). Sonnet: 4/4, $1.17 API-equivalent. Caveat: the usage-counter delta includes any other OpenRouter use on the key during the runs (one jury run overlapped knob r2).

**Final verdict: stay on Sonnet 5.** Once repeated, GLM is not cheaper per good build and is less reliable; the first-round cheap numbers were luck. Total benchmark spend ≈ $12.2 of the $15 cap. Harness stays in the repo (`worker/tests/bench`, PRs #74/#75) for a re-test when new models ship.

## Addendum 4 — Gemini on James's free Google AI Studio key (22 Sep)

Routed through OpenRouter BYOK (a test call confirmed `is_byok: true`, $0). First attempt: all runs failed instantly with 0 tokens (the free quota refusing the first request; a hand-run a minute later worked). Rerun, stopped by the $3 cap after 4 runs:

| model | knob | pill box | real OpenRouter $ |
|---|---|---|---|
| Gemini 3.1 Pro preview | pass, 2.1 min | pass, 6.2 min | $0.17 + $0.83 |
| Gemini 3.8 Flash | pass, 8.7 min | fail — host mechanics gate: box/lid thread mismatch | $0.72 + $1.03 |

**The free key did not make builds free:** $3.40 was charged on OpenRouter for 4 runs — inferred to be OpenRouter falling back to its paid Google capacity when the free quota rate-limited the build's rapid requests (not verified per request; the activity API was not available). A build is 30–60 requests in a few minutes; a free key cannot carry that, let alone for many users. **Free Gemini builds are not viable.** Gemini 3.1 Pro (paid) is the most promising non-Claude builder seen so far (2/2 simple parts, knob at $0.17 vs Sonnet $0.55) — n=2, bracket and strut untested.

**Spend note:** total benchmark OpenRouter spend ≈ **$15.6, about $0.60 over the $15 James approved** — the cap is checked before each run, so the last Gemini run overshot it.

**Impact on the freemium plan:** there is no free build engine. Realistic free tier = chat, photo reading, concepts and measurements free (≈ £0.11–0.56 per active free user a month on Sonnet), every build priced (cost + 40 %) or covered by a Premium monthly allowance.
