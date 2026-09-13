# 3D printing

<!-- One-paragraph project description: what it is, who it's for. Fill in. -->

## Session start
1. `git pull`
2. Read `vault/Inbox.md` — triage: done → remove, actionable → plan
3. End of session: commit + push

## Vault is the knowledge base
`vault/` is the source of truth. Search it before asking for context:
`python3 /root/.claude/scripts/brain-search.py <terms>` (run from inside this
project — it indexes THIS space's vault + memory only). File expensive
syntheses (root causes, research, decisions) back as vault pages before ending
the turn. Update the vault after: new feature, schema change, new route.

## SCOPE GUARD (read first)
The pipeline below runs ONLY for "build/fix X end-to-end". If the ask is a SINGLE
step — "review this", "critique this plan", "just plan it", "what do you think" — do
THAT step and STOP. A review is not a licence to ship. When unsure of scope, do less
and ask.

## Design-shaped asks need OPTIONS, not just critique
A critique panel can only tell you whether YOUR idea is good; it can never say
"there's a better approach". When more than one solution could be right — "rework X",
"X is hard to use", any UI/UX/flow call — do NOT jump to code:
1. **Questions** — `superpowers:brainstorming` (machine-wide skill, available in every
   space): one question at a time, with the human, until the intent is actually pinned.
   What does done look like, who is it for, what must not change. Its OUTPUT is the
   problem statement — write it to a .md and hand that to step 2. Most of the value of
   this whole pipeline lives here: a panel handed a vague brief returns a vague map.
2. **Generate** — `idea-options.sh <problem.md>` (in `/root/diff-jury`): state the
   PROBLEM, not your solution. Blind parallel proposers, one judge, one recommendation.
3. **Critique the winner** — `idea-panel.sh` / `/panel`.
4. **Log the pick** — `idea-decide "<ref>" "<choice + why>"`, which feeds later runs.
A bug with one obvious right answer skips all of this. If you cannot name the single
correct outcome, it is design, not a bug.

## Quality pipeline
- Non-trivial plan/idea/copy → `/panel` critique before building
- Mechanically-checkable "done" → `/gate`: write the acceptance gate FIRST, baseline
  must fail RED. **A gate must be provably passable AND provably failable** — validate
  it in both directions (mutate the code, watch it go red) before trusting it. A gate
  that cannot fail, or that can never pass, is worse than none.
- Every substantive diff → `/jury` (cheap diff panel) **and** `review-gate <dir>
  <builder>` (cross-lineage, repo-aware, read-only, fails closed on P1). Different
  blind spots — neither substitutes for the other. Whoever built it does not review it.
- Triage every finding against the code: a claim is a lead, not a verdict.
- Features with a runtime surface: verify the OUTCOME end-to-end, not that a page loads

## Drivers — build on the subscriptions first
**Default: `claude` (Anthropic Max).** It is a subscription, so building on it costs
nothing at the margin, while the OpenRouter drivers spend real credit per token. Build
here unless there is a reason not to.
- `cx` — codex, pinned to a cheap tier. Also a subscription, also £0 marginal. Use it
  to spread load, or when Max is capped.
- `claude-mm` / `claude-gm` — OpenRouter, per-token, UNCAPPED. These are the
  overflow valve for when both subscriptions are exhausted, not the default. They are
  the only thing that keeps working when the subs run dry, so keep them installed.

Cheap-per-token is not cheap-per-outcome: a measured builder benchmark had a /root/.claude/scripts/stack-init.sh.07/M
model burn more than the whole day's premium usage on one task it then failed.
**Never cheapen the reviewer** — review-gate and /jury stay as configured.

## Epistemic discipline
1. **A dismissal is a claim.** "Not worth it / already optimal / nothing there" needs
   EVIDENCE, same bar as a positive claim. If you haven't checked, say so or run the cheap check.
2. **Never claim done without proof.** UI renders ≠ works. Tests green ≠ tests catch bugs.
   Exercise the actual behaviour and show the evidence before "done/working/fixed".
3. **One silent run is not evidence.** An empty or failed result is not a verdict about
   a tool or a model — reproduce it before concluding, and never invent a mechanism to
   explain it without testing that mechanism in isolation.
4. **Grep the concept, not the string.** One feature's story usually lives across
   several surfaces — UI control, help text, docs, README. After changing behaviour,
   grep the feature's vocabulary and account for EVERY hit before claiming done.
Separate what you KNOW (verified) from what you INFER (guess); label which.

## Code quality
Before writing: state assumptions; push back if simpler exists. While coding: minimum
that solves the problem — no single-use abstractions, no speculative scaffolding; every
changed line traces to the request. After: build → verify → pipeline above.
Stop making it cleverer: if two revisions of the same fix each broke something new,
take the reviewer's simplest version and stop.

## Communication style
Two audiences, two shapes — pick by who reads it, not by topic.
- **Prose the user reads** → the `i-have-adhd` ruleset: lead with the action, number
  multi-step work, restate state each turn, ONE concrete next action at the end,
  specific time estimates, lists capped at 5, no preamble, no recap, no closing
  pleasantries. Explain in full when asked to walk through something.
- **Output other models read** (subagent/reviewer prompts, commit messages, PR bodies,
  tool narration) → terse and mechanical.
Not advisory: do not coach, mirror, or append strategic nudges that were not asked for.
State findings as one plain factual line where they belong, and stop.

## Files arrive from Telegram
There is no Telegram tool to connect — a background relay writes files to disk and
you read them from there.
- Photos/screenshots → `vault/screenshots/`
- Any other file (html, md, csv, pdf) → `vault/inbox-files/`
- Routing is by CAPTION: the first word picks the project ("TaylorsGym: lander.html").
  No caption means it lands in the default project, not this one.
- Replying to a notification in Telegram types that text straight into the pane the
  notification came from.
When asked about "the file I sent", look in `vault/inbox-files/` newest-first before
saying you cannot see it.

## Asking the user
Only ask when: 3+ failed attempts at the same problem, need credentials/external
service, or a design-preference call.

**When you do ask, give options to PICK, never a blank to fill.** Typing is the
expensive part — on a phone it is the whole cost. Use the `AskUserQuestion` tool: it
auto-appends an "Other" free-text option, so never hand-write one. Put the recommended
option FIRST labelled `(recommended)` and the decline option LAST — there is no
pre-selected default, so order plus label is the only default signal. Max 4 options and
4 questions per call. Fall back to a numbered list only where the tool is unavailable:

    1. Ship it as-is
    2. Fix X first, then ship
    3. Park it — I will decide tomorrow

Two to four options, each a complete decision, recommendation first. "What do you
think?" and "let me know how you want to proceed" are both a request to compose prose,
which is the thing to avoid. If genuinely open-ended, still offer the two or three
answers you expect and let him override.
