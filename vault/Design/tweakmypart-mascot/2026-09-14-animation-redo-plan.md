# TweakMyPart mascot: animation redo plan

Research: `vault/Research/2026-09-14-mascot-animation-research.md`.

## What James saw, confirmed by /watch (68 s review reel, 1 fps + chest crops)

| Problem | Where | Cause |
|---|---|---|
| Legs locked, only head and arms move | idle A/B, listening, thinking, point, oops | start pose is flat and symmetric; prompts never named weight or legs |
| Printer blobs, nozzle never traces paths | all clips, worst in idle A 00:09-00:12 and focus 00:18-00:21 | a video model has no idea what a toolpath is |
| Hand goes through the closed door, cat duplicated | grab 00:23-00:31 | one prompt asked for door + reach + look + close in 7 s |
| Smile far too big | grab, exit, return 00:21-00:41 | "big happy smile" in the prompt, no magnitude limit |
| Chat clips barely move; point aims at his own chest; oops never shrugs | 00:42-01:07 | one generic verb per clip, 5 s, long negative prompt |
| Return starts small and floating; exit smears at the edge | 00:34-00:36 | forced black start/end frames |

## Fixes (from the research, ranked)

1. **Weight-bearing start pose.** A new resting keyframe with weight on one leg, knee soft, torso slightly tilted, one shoulder forward. Image-to-video models cannot invent weight the first frame does not show.
2. **Beat-by-beat prompts with timings** ("0-2 s: weight settles onto right leg, left heel lifts; 2-4 s: ..."), legs and weight named in every clip, arcs and ease-in / overshoot / settle language.
3. **Aliveness in the loose parts:** spools spin down, cables sway and lag, antenna wobbles.
4. **Face on a leash:** "small, subtle" before every LED clause; negative prompt `exaggerated smile, large facial expression`.
5. **Short negative prompt** (5-6 terms matched to our failures): `frozen legs, symmetric static stance, exaggerated smile, morphing face, floating, foot sliding`.
6. **Printing is composited, not generated.** Generate the chest chamber dark and empty with the print head parked; render a real toolpath animation (perimeters, 45° infill raster, travel moves, layer steps) from our own slicer G-code of a real model; track the chamber window's four corners per frame and warp the render into it with a warm glow grade. Correct by construction.
7. **Story split into single-beat clips:** door opens (hinged, stays attached) → hand reaches in through the open door → lifts the part out → looks at it (subtle smile) → door swings shut with the chamber empty. Walk-off and walk-in as real steps with no forced black frames; fade to black in post.
8. **Chat clips 8 s with 2-3 beats** instead of 5 s with one verb; idles as 2-3 short variants shuffled so repetition is not visible within 90 s.

## Test result (14 Sep, approved by James: "Approve B's approach, roll out")

Test B (weight-bearing pose + beat prompts + short negative, cfg 0.5) moved his legs: lean, knee bend, a foot re-planted, return. Test A with the same prompt mostly stood still, so 2 seeds per clip stay worthwhile. The G-code composite tracked the chest window in both (template-match score median 0.88 / 0.64, no lost frames). Remaining issues: the keyframe still showed a parked print head above the drawn nozzle (next keyframe removes the head), and the face flattened briefly in B's head turn.

Pipeline: `toolpath_render.py` (G-code → glowing print loop) and `composite_print.py` (OpenCV bezel tracking + screen blend into the build-plate box), both in the session scratchpad until the site build copies them into the repo.

## Order and cost

1. Test ONE clip end to end first: new keyframe (~$0.12) + idle A with every prompt fix (2 seeds, ~$1.80) + composited printing (script, no fal cost). Show James before anything else is spent.
2. If approved: idle B/C, the 5 chat clips at 8 s, and the story beats: about 14 clips x ~$0.90 = ~$12.
3. Then the preview-moment clips (chest zoom → tablet, knob twist): ~$1.50.
