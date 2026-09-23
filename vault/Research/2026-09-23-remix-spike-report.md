# Remix spike: two real models through today's system (23 Sep 2026)

Brief: [[2026-09-23-remix-a-model-brief]] and [[2026-09-23-revise-a-project-brief]].
Method: a new staging user uploaded each file through the real Attach button, ticked the rights box, took the
recommended option, answered every question, and paid with the Stripe test card. Nothing was kept from the spike.

| | Local edit | Full recreate |
|---|---|---|
| Model | *Print in Place Hinged Box* (Standard Digital File Licence) | *Frankenstein light-switch cover* (CC BY-SA, 8 bodies) |
| Ask | Keep it exactly, hinge included, add JAMES raised on the lid | Same idea as a witch: fits a UK switch, snaps together the same way |
| Options stage | 3 sensible options (emboss / plaque / inset letters) | Understood the mechanism: "same two-part design … snap frame as the original" |
| Questions | **Asked the customer to measure their own upload** ("How long is the flat top of the lid?") | Rocker vs toggle (good); "width of the switch plate opening" (a measurement it could have taken from the file) |
| Price shown | £2.00, the same as a new build | £2.30, the same as a new build |
| Build | **Crashed twice** (0.8 and 2.7 min): `CLIJSONDecodeError: JSON message exceeded maximum buffer size of 1048576 bytes` | **Failed twice** (about 24 min each, 4 attempts): base frame had 5 bodies (4 snap pegs not joined to the frame) |

## What the failures say (verified from logs and kept failure output)
1. **Nothing measures the upload.** The planning stage and the build both work from the words, not the mesh, so the
   customer is asked for dimensions that are sitting in the file they sent.
2. **"Keep what works" is not kept.** The witch option promised the original's snap frame. The build made a new frame from
   assumed UK switch sizes (`assumptions.txt`: "Standard UK single-gang switch: 86x86mm … assumed") and got the snap
   pegs wrong. The original's frame, which already works, was never reused.
3. **Large uploads crash the job.** A tool result over the Agent SDK's 1 MB message buffer kills the run (most likely
   raw mesh read from the 3MF). An engineering bug: raise the SDK buffer and never read raw mesh into the conversation.
4. **The retry is not told the real reason.** Attempt 2 repeated the loose-pegs mistake: the host passes the gate NAME
   ("verify_model") rather than the gate's FAIL line ("Body count 5, expected 1").
5. **Cost:** about 96 minutes of subscription on one failed recreate. Remix prices match a new build even for "add a name".
6. MakerWorld 3MFs carry `Title`, `Designer` and `License` in their metadata, so the rights check can read the licence.

## Approaches for the change engine (remix AND revise use the same one)
**A. Measure first, pass through what works, change only what's asked (recommended).**
The host analyses the upload before planning: parts/bodies, sizes, flat faces, mechanisms (reusing
`measure_mechanism.py`). The plan works per part: each part is **kept byte-identical**, **edited locally** on the
original mesh (add text, extend, cut), or **regenerated** in the new theme around the kept parts' interfaces. The witch
becomes: keep the Frankenstein base frame as-is, regenerate only the face to fit its pegs. Revise-your-own-design is the
same engine, with STEP parts instead of meshes. Price follows the parts that change.
*Cost:* about 2–3 sessions for the engine and the analysis, plus fixes 3 and 4 (about 1 hour).

**B. Rebuild everything in CAD from measurements.** Measure the upload, then model every part fresh in build123d.
One pipeline, but organic shapes (faces, animals) can't be rebuilt in CAD and fidelity is lost: exactly the fox/dog
and witch cases. Rejected for remix; fine for mechanical parts.

**C. A as the engine, plus pick-the-part in 3D.** The customer taps the part (or spot) to change in the 3D viewer:
the start of James's "click and comment" idea. The same engine as A with a better way to say *which* part.
*Cost:* A plus about 1–2 sessions of viewer UI.

## Recommendation
Build **A** first, then **C**'s tap-to-select as the first step toward 3D comments. Fix the 1 MB crash and the
retry reason now: they hurt every upload and every retry today.
