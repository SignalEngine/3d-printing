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
