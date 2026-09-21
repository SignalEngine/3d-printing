# TypeSafe AI (Jev) spike — 21 Sep 2026

James asked whether https://docs.typesafe.ai could help. Jev is a "System One" classifier: one POST (`https://api.typesafe.ai/v1/systemone`, bearer key, `model: "jev-latest"`) with a `state` and named questions (`noul` true/false → probability; `choice` → option + probabilities + confidence; `score` → rubric level). Priced $42 per billion input tokens.

**Spike (real data, 20 hand-labelled cases):** 14 concept cases ("does this approach depend on something the customer ruled out?") from James's two caddy designs, the G7 lessons sandbox runs and three realistic negatives; 6 budget cases ("one part or several?").

| | result |
|---|---|
| agreement | 19 / 20 |
| median latency | 0.63 s (max 0.67 s) |
| tokens / cost for all 20 | 10,087 / ≈ $0.0004 |
| miss | caddy "rod through the existing holes" scored 0.19 — the messages in that state said "top is curved and no holes, needs to clip onto the sides", not "the holes don't line up"; arguably a label problem |

Budget cases were 6/6 with ≥ 0.97 confidence — better than the regex in `classify_multipart`.

**Decision:** wire it (plan `vault/Plans/2026-09-21-tweakmypart-typesafe-gates-plan.md`): concept filter on the host after the brief job (drop p ≥ 0.7, never below 2 concepts, log "dropped X: needs Y you ruled out"), budget from a choice question (fallback to the regex when the API is down), refusal pre-check later. Key lives in `/etc/printtweak/typesafe.env` (systemd EnvironmentFile), never in the repo. Eval script + cases kept in this session's scratchpad `typesafe/` (copy into `worker/tests/typesafe/` in the build).
