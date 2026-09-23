# Revise a design as a project: brief (James, 23 Sep 2026)

Told to the TweakMyPart session in chat on 23 Sep, during the remix-a-model spike. It belongs with
[[2026-09-23-remix-a-model-brief]]: both take an existing model plus a change, then either edit it locally or rethink it.

## What James said (condensed, his words where possible)
- People will use TweakMyPart to invent new things. They give a wrong measurement, or print it and "it doesn't
  actually clip in". Instead of starting over they come back to the same project.
- The current "type in changes" didn't work well when he tested it ("change it by 10 millimetres"). What he actually
  wanted was to "fundamentally go back and see if there's a different concept": "that didn't work whatsoever, let's
  rethink", or "change the clip bit to something else". **Same subject, remember the project, different route.**
- **Pricing:** a change on top of a model we already made should be predicted at a LOWER cost, but never free, "then
  you could start out with something very cheap and then start adding things to it and just pay a tiny price".
  "Very clever with the pricing, but fair." Micro-changes on an existing model vs a redesign.
- **Project page:** "almost like a whole project so that we can see individual things, and we can edit almost anything."
- **Comment in 3D:** open the model in 3D, click a piece, and a comment box appears: "so that we don't have to use
  English in order to comment". Several comments around the model; the system reads them all and either makes the changes
  or asks a question (e.g. the real measurement).
- **Images:** the system can ask "send me an image of this on this angle" to understand it better.

## What exists today (checked in code, 23 Sep)
- Ready page "Change something" -> `designs:addTweak` -> a `tweak` job. `FREE_TWEAKS = 3`, then `tweak_limit` (no paid
  tweak). `convex/lib/limits.ts`.
- **A tweak only sends ONE part**: `claimNext` passes a single `previous.step`, the largest part by weight. On a multi-part
  design a change to any other part cannot work. A likely cause of the poor result.
- No re-concept after ready: the brief (options/questions) is done once. "Change the approach" exists only BEFORE build.
- Versions are stored per job (`versions` table) and the ready page shows downloads. There is no project view across rounds.
- Cost prediction exists for first builds (`predictionStats`, `worker/predict.py`); nothing prices a change.

## Pieces (to order with James)
1. Change engine: an existing model (own or uploaded) plus a change, as a local edit (keep mesh) or a re-concept (keep
   intent). Shared with remix.
2. Project page: every version/round, per-part edits, re-concept from any point.
3. Change pricing: predicted from the size of the change, floor above zero, capped below a fresh build.
4. Point-and-comment in 3D, plus the system asking for a photo from a given angle.
