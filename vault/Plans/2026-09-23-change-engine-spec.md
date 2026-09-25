# Change engine: remix a model + revise a design (spec, 23 Sep 2026)

Decided with James on 23 Sep:
- **Approach A then C** (spike report [[2026-09-23-remix-spike-report]]).
- **Licence:** the customer confirms their rights, and No-Derivatives models are blocked.
- **Order:** remix + revise first, then the feedback drawer.

Briefs: [[2026-09-23-remix-a-model-brief]], [[2026-09-23-revise-a-project-brief]].

## The one idea
Remix (someone else's model) and revise (your own finished design) are the same job: **an existing model, split into
parts, plus a change**. For each part the plan says **keep**, **edit** or **regenerate**:
- **keep**: the part ships geometry-identical to the source (the host proves it).
- **edit**: change one region of the source mesh (add a name, extend a tail, cut a slot), leaving the rest of the mesh exactly as it was.
- **regenerate**: model the part fresh in the new theme, **fitted to the kept parts' measured interfaces** (pegs, holes,
  hinge line, outline).

The witch becomes: keep the Frankenstein base frame, regenerate only the face to fit the frame's measured pegs. The box
becomes: keep the body, edit the lid (raised JAMES on its measured flat top), keep the hinge.

## 1. Model card: measure before planning (host)
When an upload arrives (remix) or a design is ready (revise), the host writes a **model card** (JSON in storage):
- **per part:** name, bounding box, volume, watertight, body count, and the largest flat faces (size, normal, position): the space where a name fits.
- **between parts:** the smallest gap between each pair, whether they touch, and any gears found. Reuse `measure_mechanism.py`, merging branch
  `build/measure-mechanism` first. Its header rule "never derive geometry" is for LEARNING numbers from other
  people's models; remix keeps geometry under the customer's confirmed rights, and the header must say so.
- **3MF metadata:** Title, Designer, License. ND → blocked with a plain message. Others need the existing rights tick.
- **a labelled contact sheet image** (one render per part, named) so the planning model can SEE which part is which.
The card replaces `_mesh_summary` (bounding box only today) as the input to the planning stage and to the build.
**Heavy meshes** (the planetary spinner timed out) are measured on a decimated copy, capped at 60 s. If that fails, the
card says so, and planning falls back to asking the customer.

## 2. Planning (brief job)
- Reads the card and the image. Each option shows its per-part plan in plain words ("keeps: base frame, hinge · changes: face").
- **Never asks the customer for a size the card already has.** Questions are only for what the file cannot say (rocker or
  toggle switch, which breed, what name).
- "Change the approach" and re-concept work the same way for revise (see 5).

## 3. Build (sandbox)
- The sandbox gets the source parts, the card and the per-part plan (`/job/in/source/<part>.stl|.step`, `card.json`).
- **keep:** copy through. **Host gate:** the output part's volume/bbox/sampled surface matches the source within 0.05 mm;
  otherwise the build fails with "a part you asked to keep was changed".
- **edit:** mesh operations on the source (manifold3d boolean union/difference, and text as a solid) following
  `references/mesh-editing.md`. **Host gate:** the part is unchanged outside the edited region (sampled distance).
- **regenerate:** build123d as today, plus `checks.json` mates against the kept parts. The existing mechanics gate
  measures them, so the witch face must actually fit the real frame's pegs.
- **Retry reasons:** the gate's own FAIL line reaches attempt 2 (bug fix in flight, branch `fix/upload-buffer-retry-reason`).

## 4. Price
- A change is priced from the per-part plan: **keep = 0**, **edit** = a small fixed share, **regenerate** = what the
  prediction says for a new part of that size. Floor **£1**, never above a fresh build of the same design.
- Numbers come from measured cost (`predictionStats`), not guesses: log per-part cost from the first 20 changes, then set.
- Cheap-start-then-add abuse (James): each change is priced from the parts it touches. There is no free edit chain; the
  3 free tweaks become the priced change.

## 5. Revise as a project (own designs)
- A finished design is a **project**: every version and every round is kept, and any version can be the source.
- **Change** (any part, not just the largest: today's tweak sends one `previous.step`) and **Rethink**: re-run planning
  with the project's history (request, answers, what was printed, what didn't work), producing new options under
  the same project.
- The project page lists versions and parts. Each part has Download, Change and Rethink.

## 6. Next (C, later sessions)
Tap a part (then a spot) in the 3D viewer to pick what to change, which is the first step to James's click-to-comment.
After that: several pinned comments, the system asking for a photo from a given angle, and then the feedback drawer.

## Proof (acceptance)
Real models through the real customer path on staging:
1. The **hinged box** gets JAMES on the lid. The hinge part passes the keep gate, and the result prints as print-in-place (gaps unchanged).
2. The **Frankenstein switch → witch**: frame kept (gate), face regenerated, and the mates check proves the face fits the frame's pegs.
3. **Revise:** a finished multi-part design gets a change to a NON-largest part, and the other parts pass the keep gate.
4. Neither planning stage asks for a size that is in the card.
5. A ND-licensed 3MF is blocked with the plain message.
If James sends the whistle and fox from MakerWorld, they are added as 6 and 7.

## Build order (each ships on its own after staging proof)
1. Model card (1) plus merging measure_mechanism: about 1 session.
2. Planning reads the card; per-part plan in options (2): about 1 session.
   **SHIPPED 23 Sep (printtweak #102, prod 1e40200):** each concept carries `partPlan` (keep/edit/regenerate per card
   part), shown as "Keeps: … · Changes: … · Remakes: …"; a bad plan drops the plan, never the brief; the chosen plan is
   a `Part plan:` line in the build request (guidance only until step 3's gates). Staging proof: hinged box + Frankenstein
   → witch both got per-part plans; first questions asked letter height / relief depth, no card sizes.
   Follow-ups (James 23 Sep): (a) ~~an `add` action for new parts~~ DROPPED, see below. (b) plain part labels ("Lid",
   not "…v22-SOLID-1"): with step 3.
   **James, 23 Sep evening (after seeing the witch options):** a witch overlay is NOT the remix. The witch is the
   ORIGINAL base plate reworked, re-cut so the plate itself reads as a witch. Line sketches cannot show that: options
   for a remix must show a real picture of the customer's model (the card's render) with the change marked, not an SVG
   line drawing. Remix options change the source parts; no add-on overlays. Folded into step 3.
3. Build keep/edit/regenerate with the gates (3): about 1–2 sessions.
4. Revise as a project plus the Change/Rethink UI (5), and pricing (4) once cost data exists: about 1–2 sessions.

## Reshape quality: the brief must make the look concrete (James, 25 Sep)
Witch runs: a good witch appeared only when the chosen option spelled the look out (pointed hat + hooked-nose profile);
vague options ("a witch outline") produced octagons/spikes and the look judge refunded them. James: "the idea is
unclear and it's working to an impossible solution". Next change-engine PR: for a look/outline change, the brief's
option describes the exact silhouette (named features, where they sit on the part, what must stay) and its sketch
shows that outline on the real part, so the build works to a concrete target. The build side (silhouette guidance,
self-render, facing-view judge) stays as it is.
