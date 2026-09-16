# TweakMyPart: the brief step — questions + 2D storyboard before the 3D build (spec + builder handover)

James (16 Sep, recording 16:51): "It started instantly, building without asking any questions… it should say, here's a 2D render of what it could look like — extremely cheap — and once they're happy and all the questions have been asked and approved, then it goes into this." Chosen: **always**, for every request.

## Flow
1. Customer submits the request (unchanged form) → design `status: "brief"` (new), a `jobs` row of `kind: "brief"`.
2. The worker runs a **brief job** in the same sandbox image with a small budget ($0.15, `max_turns` 6, Haiku via the SDK — `model: "claude-haiku-4-5-20251001"`): output `/job/out/brief.json` = `{ questions: [{ id, text, options?: string[], default: string }] (2–4), sketch: "<svg…>" , summary: string }`. The sketch is an honest schematic: an SVG with the main outline(s), overall dimensions written on dimension lines, part count, lettering position if any — not a rendering. The system prompt for this job is a new `worker/job/brief_prompt.md`; no model-forge tools are needed, no Python.
3. Host uploads nothing: `worker:reportBrief({ secret, jobId, brief })` stores the brief on the design (`brief: { questions, sketch, summary, answers?: Record<id, string>, approvedAt? }`; sketch capped at 60 KB and sanitised: strip `<script>`, `on*=` attributes, external hrefs — render it inside an `<img src="data:image/svg+xml,…">`, never inline HTML).
4. Brief page (`status === "brief"`): the tablet shows the sketch (the mascot in `presenting`), the questions as a short form with the defaults pre-filled (chips for options, text for free answers), a one-line summary ("A lidded box 51 × 51 × 28.3 mm, lift-off lid, 2 parts"), and **Approve and build** / **Change my request**. Approve → `designs:approveBrief({ designId, answers })` → `status: "queued"`, the answers are appended to the request the design job sees (`request + "\n\nAnswers:\n- Q: A"`), the normal design job is created.
5. Failure of the brief job (timeout, bad JSON): skip the step — go straight to `queued` with a log line "Skipped the questions this time"; never block a customer on it.
6. Limits: a brief costs nothing against the free-design counter; the daily cap counts its $.

## Tests
Convex: brief status transitions, `reportBrief` validation (question count, sketch size, sanitiser rejects scripts/handlers/hrefs), `approveBrief` appends answers and queues the design job, failed brief → queued. Worker: brief job runner parses/validates `brief.json`, budget/turns applied, failure path. Page: renders questions with defaults, approve calls the mutation, sketch shown via data URL. Live proof (brain): knob request → brief in ≤ 60 s with a sketch + questions → approve → design job runs as today.

## Estimate
One builder session (~2 h) + image rebuild + a live run. Depends on the working-page layout build being merged first (same page files).
