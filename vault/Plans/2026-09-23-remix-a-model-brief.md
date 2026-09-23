# Remix a model — feature brief from James's lander feedback (23 Sep 2026)

Source: James's narrated screen recording `/root/intentos/vault/inbox-files/2026-09-23 14-07-36 2026-09-23 14-07-36 - tweakmypart.mp4` (10:06), section **02:48–06:24**. Transcript (Whisper) at `/tmp/claude-0/-root-printtweak/a7c41ba2-3e2b-416f-8ff1-d17d868bb869/scratchpad/fb/` (scratch; the quotes below are the durable record).
James: "I know that the system does not work like this yet" — this is a NEW capability, handed from the lander session.

## What he wants, in his words
- "Already got a model? He'll change it — this is just too simplistic … there's obviously no difference" (the lander's 'clip arm +10 mm' example). "It should be something that I can send you a model and then we can test to see if it makes something and changes it."
- Examples he pointed at on **MakerWorld → Trending** (03:28–05:31): ghost candle holder → "change the ghosts to witches"; spinning octopus → change it to something else; dachshund catch-all tray → "a different breed of dog"; loud whistle → "add a name to it, add text, add a little face to the side"; articulated skeleton → "change the whole thing completely"; keyring/fidget fox → "change that to a dog instead of a fox", or "a different type of Minecraft thing".
- "You could pick something that's trending and then change it … it's essentially like giving them a concept."
- Two modes, his split (05:40–06:07):
  1. **Total change** ("change everything"): "I would give you this model and then you would look at it, see how it's made, and then recreate it in total" — understand the mechanism/structure (print-in-place joints, clip, tray shape) and rebuild it in the new theme, keeping what makes it work.
  2. **Local edit** ("extend his tail", "extend these key rings out lower", add text/name/face): "then obviously you just use the original model and extend its tail" — keep the original mesh, change one region.
- "We'd ask them for an image or something like that" for the new subject (e.g. a photo of their dog breed).
- "We need to be able to demonstrate clearly that we can … take something and completely change it and keep everything [that works]."

## What exists today (checked)
- Uploads: STL/3MF/STEP accepted (`lib/upload.ts`), request.json `uploadName`, file at `/job/in/<name>`; the design job gets "The customer attached …". Worked for simple edits in bench runs (clip arm +10 mm in 1.2 min; paw-shaped jar keeping the thread in 10 min).
- Tools in model-forge: `references/mesh-editing.md`, `scripts/measure_mechanism.py` (branch build/measure-mechanism, not merged), `vault/Research/2026-09-22-measured-real-models.md` (downloaded MakerWorld mechanisms measured; planetary spinner times out; hinge gaps unreadable).
- Real MakerWorld test files already in `/root/intentos/vault/inbox-files/`: `tg-…Planetary+Gears+Fidget+Spinner…3mf`, `…Spherical+snap-fit+ball+joint…3mf`, `…Hinged+Box.3mf`, `…Tread+-+Outer+Ring+Only.3mf`.
- Licensing: MakerWorld models carry their creators' licences (many are non-commercial / no-derivatives). A remix feature that sells prints or files of a derivative needs a licence check before it ships. Unverified what TweakMyPart's position is — decide with James.

## Suggested first step (the receiving session decides)
Design-shaped ask → questions + options before code (CLAUDE.md pipeline). A cheap first proof: take 2 real models (one local edit: whistle + name; one total change: fox fidget → dog) through the current design job with the upload attached, see where it breaks, and write the plan from the failures.
