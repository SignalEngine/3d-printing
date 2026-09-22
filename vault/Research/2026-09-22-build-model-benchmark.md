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
