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

## Rollout result (14 clips, ~$11.30, /watch at 1 fps on the 101 s reel)

Worked: legs and weight now move in idle-1 (00:02-00:04), idle-2 (00:10-00:12), idle-3 step and stretch (00:18-00:21), thinking hand-to-chin with a bent knee (00:34-00:37), presenting wide sweep (00:43-00:45), point aimed outward away from his body (00:51-00:53), oops shrug palms up with a flat mouth (00:58-01:01). The composited G-code print tracks his chest through arm crossings (idle-3) and leans (point); focus builds the knob and hands off to the physical knob (00:68-00:69).

Failed: 
- **Story door and grab (00:72-00:89):** the glass turns into a flat panel sticking out sideways with a picture of another robot inside it; the knob vanishes instead of being lifted (00:79); he holds an empty fist while "looking at" it; the visor turns gold for a moment (00:84). Three prompt rounds have now failed at door + object handling, so the video model cannot be relied on for it.
- **walk-in-wave:** the blue hip spool swells into an oversized floating spool (00:97-00:99), and the enter keyframe still showed a print head that disappears by the end.
- **idle-2:** the face vanishes into the back of the visor during the head turn (00:11-00:12).
- **listening:** still close to still.
- **point:** print tracking weakest (median score 0.40); the ring sits low in the window during the lean.

## Decision (James, 14 Sep): swap the grab for a proud reveal

After focus: the finished print glows, he looks down at it, gives a small proud thumbs up, and the chamber light fades to dark so the next idle starts empty. Door and object handling dropped. Re-rolls: idle-2 (face kept toward the viewer), listening (bigger beats), walk-in (start frame is the standing pose shifted to the right edge, so the spools keep their size).

## Clip set 2 (final for now), /watch at 2 fps on the re-roll reel

- **idle-2 (re-roll):** leans in and taps the glass with his face kept visible; the composited print is drawn over his fingers while he taps (no occlusion handling yet).
- **listening (re-roll):** real motion now: leans in with a step, nods, cups a hand, open-palm "go on"; the window flashes bright for about a second near the start.
- **reveal:** thumbs up and the chamber fades to dark; his head flips oddly for about a second near the start.
- **hello (walk-in re-roll):** enters from the right with real steps, spools keep their size, waves, settles.
- Web set: `vault/Design/tweakmypart-mascot/web-v2/` (11 clips + posters, 5.9 MB). Viewer: https://claude.ai/code/artifact/9d48f7f4-9706-4fd9-b472-05fb6613ccfd

## Order and cost

1. Test ONE clip end to end first: new keyframe (~$0.12) + idle A with every prompt fix (2 seeds, ~$1.80) + composited printing (script, no fal cost). Show James before anything else is spent.
2. If approved: idle B/C, the 5 chat clips at 8 s, and the story beats: about 14 clips x ~$0.90 = ~$12.
3. Then the preview-moment clips (chest zoom → tablet, knob twist): ~$1.50.
