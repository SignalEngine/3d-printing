# PrintTweak MVP: design spec

**Status:** design approved section by section by James, 2026-09-13. Awaiting his review of this written spec before the build plan.
**Domain:** printtweak.com (free on the Verisign registry, 13 Sep 2026; not bought yet; .co.uk not checked).
**Why:** test real interest in "describe a part, or upload your model, and AI makes it print-ready", using a 14-day LaunchEngine campaign.
**Evidence it rests on:** [[2026-09-13-3d-print-business-ideas]] rounds 3-4 and [[2026-09-13-3d-print-business-research]].

## 0. Update 2026-09-14: personal mode first (overrides the sections below where they conflict)

James decided PrintTweak runs **only for him, on his own Claude subscription**, before any other users.

Why (official Anthropic docs, read 14 Sep 2026):
- Own subscription in scripts is supported: `claude setup-token` issues a one-year `CLAUDE_CODE_OAUTH_TOKEN` "for CI pipelines, scripts, or other environments where interactive browser login isn't available", which "authenticates with your Claude subscription"; environment credentials apply to "the CLI and the surfaces that wrap it, including … the Agent SDK" ([authentication](https://code.claude.com/docs/en/authentication.md)).
- Other people signing in with their subscriptions is not allowed: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Use the API key authentication methods… instead." ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview.md)).
- Sharing James's subscription with other users would be account sharing, so personal mode means the site is locked to his email.

What changes:
- **Auth for AI:** the worker uses James's `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`), not an Anthropic Console API key. No PrintTweak Console workspace for now.
- **Access:** `ALLOWED_EMAILS` (James only). Anyone else signing in is refused.
- **Sandbox:** the job container holds the token (only James submits requests, so there is no stranger prompt-injection path); the proxy becomes a pass-through to `api.anthropic.com` `/v1/*` and the internal network still blocks everything else.
- **Vision check:** runs as a short Agent SDK query on Haiku reading the render file, because the plain `anthropic` API client cannot use a subscription token.
- **Deferred until other users exist:** payments (Stripe), the public free-try limits' commercial role, and the 14-day LaunchEngine interest test. Those need API-key mode: each user brings their own Anthropic API key, or a PrintTweak Console workspace pays.
- **Domain:** optional for personal use (a Railway subdomain works).

## 1. What it is

One chat where someone either **describes a part** ("a knob, 15 mm tall, M5 hole") or **attaches their own model** ("make it 2 mm wider, add my name"). The AI designs or edits it with the model-forge pipeline, checks it, and shows a 3D preview with a price. They pay £5 to download the print-ready file, or pay a quote to have it printed and posted in the UK.

Evidence behind the shape:
- 4 of 4 real functional requests from r/3Dprintmything became valid, sliced parts in 4-32 minutes of agent time (round 4 test).
- Reddit demand is mostly "design me X" (commissions) and "print my file"; only 6 of ~230 posts asked to modify an existing model. The upload path is included because James wants it, not because demand is proven.
- No marketplace (MakerWorld, Printables, Thangs, Cults3D) has chat-to-edit today; Bambu is shutting its own AI tools on 20 Sep 2026 over quality.
- Only ~1-2% of households own a printer, so the printed option matters.

## 2. User flow

1. **Landing:** "Describe a part, or upload your model", plus 3 real examples (knob, pill box, rack bracket from the round 4 test).
2. **Email sign-in** (Clerk magic link).
3. **Chat:** the AI asks up to 3 questions (size, what it fits, material). Optional attachment: STL/3MF/STEP or a photo. An upload requires a ticked box: "I own this or have the creator's permission."
4. **Queue + live status:** queued → designing → checking → ready. Email when ready (typically 5-30 minutes).
5. **Preview:** three.js 3D viewer plus the quote block (print hours, grams, £5 file, printed price for UK).
6. **Tweak in chat** ("2 mm wider") → re-run.
7. **Pay:** £5 → download 3MF + STEP; or pay the print price + UK address → order goes to James's print queue (he prints and posts via Royal Mail).

**Free limits:** 2 free designs per email, 3 tweaks each.

**Out of scope for the MVP:**
- organic sculpts and figurines (the AI declines politely)
- multicolour / AMS, EU shipping
- fetching MakerWorld or other links (upload only; MakerWorld's terms ban automated access)
- account features beyond a "My designs" list

## 3. Architecture

### Front end
- New repo, same stack as SignalSprint: Next.js 16, Convex, Clerk (email magic link), Stripe, three.js 0.170.
- Hosted on **Railway** with its own domain. Vercel was considered; its free Hobby tier bans commercial use, so it would have needed Pro at $20/seat/month.
- The 3D viewer reuses the phone-viewer recipe in `skills/model-forge/references/interactive-deliverables.md`.

### Convex (source of truth)
Tables:
- `users`: email, free designs used, campaign source (UTM).
- `designs`: request text, upload file ref + rights tickbox, status, tweaks used, quote, files (3MF, STEP, GLB, renders), check results.
- `messages`: chat per design.
- `jobs`: kind (design | tweak), state, AI cost (USD), error, timestamps.
- `orders`: kind (file | print), Stripe session id, paid, UK address (print), fulfilment state.
- `events`: visit, sign_up, design_started, preview_delivered, paid.

Job states: `queued → designing → checking → ready | failed | declined`. Download URLs are issued only after the Stripe webhook marks the order paid.

### Worker (this VPS, one systemd service)
- Polls Convex for the next queued job, **one at a time** (James chose the VPS over a dedicated box to keep the test at £0 extra).
- Holds the only Convex worker token. Downloads inputs into a per-job folder.
- Runs each job in a **throwaway Docker container**:
  - `--memory 3g --cpus 2`, a PIDs limit, non-root user;
  - model-forge scripts mounted read-only;
  - no host secrets and no Convex token inside;
  - network egress only to a host-side proxy for the Anthropic API, which adds the API key, so the container never holds it.
- Inside the container: Claude Agent SDK (Python, `claude-agent-sdk` 0.2.x) on Sonnet 5 runs model-forge: design or edit → `verify_model.py` → `render.sh` → `text_check.py` (when text is ordered) → `slice_gate.py` quote.
- Limits per job: `max_budget_usd` (hard AI spend cap per run), `max_turns`, and a 35-minute hard timeout. The SDK also reports `total_cost_usd` when the run ends, which is stored on the job. (Correction 13 Sep: an earlier draft said the SDK had no spend cap; `max_budget_usd` is in `ClaudeAgentOptions`, claude-agent-sdk 0.2.152.)
- The worker uploads files and status back to Convex, then removes the container.

### Separate check before "ready"
A second, cheap vision call (Haiku) sees only the front render and the customer's request, and must agree they match. The designing agent never approves its own work (the same builder/reviewer split used everywhere else).

### Keys
A **new Anthropic Console workspace** for PrintTweak, with its own API key and a monthly spend limit. At the limit the API returns 429 instead of charging.

### Upgrade path
The same container image runs on a dedicated box pointed at the same Convex. No code change, only a second worker.

## 4. Limits, pricing, refusals, failures

**Limits**
- 2 free designs + 3 tweaks each per email.
- Daily cap: stop taking new jobs once today's summed AI cost reaches £15 (a setting).
- Queue cap: 20 waiting. Beyond that the user sees "We're busy, email me when there's space."
- Uploads: models ≤ 25 MB, photos ≤ 10 MB.
- The Anthropic workspace spend limit is the final backstop.

**Prices**
- File download: £5.
- Printed: `max(£15, cost floor + £8 × print hours)` + Royal Mail. Cost floor comes from `slice_gate.py`. No print quote over 8 hours or 150 g; the file download is still offered.

**Refused (free try not used)**
- organic sculpts and figurines
- weapons, weapon parts, knives
- trademarked characters and logos

**Failures (free try refunded)**
- Fails the checks after retries → "We couldn't make this reliably" + Telegram alert to James.
- Vision check disagrees → one automatic retry, then fail as above.
- Timeout, 429, or crash → job failed; the worker moves to the next job.

**Payments and ops**
- Download link only after the Stripe webhook confirms payment.
- A print order needs a UK address; James gets a Telegram alert for every print order.
- Worker health check: if it stops, the queue waits and James gets a Telegram alert.

## 5. Tests (each shown failing first, then passing)

1. `skills/model-forge/tests/run_gates.sh all` stays green.
2. **Sandbox:** from inside a job container, reading host files or env fails, reaching any host except the Anthropic proxy fails, and a job allocating over 3 GB is killed.
3. **Limits:** a 3rd free design is refused; the daily £ cap stops new jobs; the 21st queued job gets "busy".
4. **Refunds:** a forced job failure gives the free try back.
5. **Payments** (Stripe test mode): the download URL is refused before the webhook and works after.
6. **Vision check:** a deliberately mismatched render (wrong file swapped in) fails.
7. **Live end-to-end:** the 5 real r/3Dprintmything requests from round 4 go through the live site to previews + quotes; one paid test download completes; one print order produces a Telegram alert.

## 6. James's setup list

These need his accounts:
- Buy printtweak.com.
- ~~Anthropic Console: new workspace, API key, monthly spend limit.~~ Deferred (personal mode): instead run `claude setup-token` once and put the token in `/etc/printtweak/worker.env` on the VPS.
- Stripe: £5 file product in live mode.
- Approve new Clerk, Convex and Railway projects (created by the build session if logged in).

## 7. LaunchEngine interest test (14 days)

- Add printtweak.com as a LaunchEngine product. Candidate communities: r/functionalprint, r/BambuLab, r/3Dprinting. Check each subreddit's self-promotion rules first.
- Funnel page (admin only): visits → sign-ups → designs started → previews delivered → paid.
- **Kill if fewer than 50 sign-ups or fewer than 5 paid orders** after 14 days.

## 8. Estimate

About 2 days of sessions: Sonnet builder panes per slice, the brain running tests, /jury and review-gate, then the live end-to-end run. External waits only: domain DNS (hours) and any Stripe live-mode checks.

## 9. Open items and known risks

- **VPS capacity:** ~3 GB RAM free with other sessions and engines running. One job at a time; a campaign spike means queue waits. Move to a dedicated box if the queue cap trips often.
- **Mesh edits on uploads are less reliable** than parametric designs: 5 geometry bugs on the first in-house STL edit. Expect a higher failure/refund rate on the upload path.
- **Legal:** the uploader-responsibility tickbox plus takedown is standard, but untested against a service that actively modifies files. Functional parts are low risk; decorative rebuilds are not (hence the refusals).
- **AI cost per design** is estimated at $0.20-1.50 (round 4 token counts at Sonnet 5 list prices), not measured per run. The live end-to-end run records the real cost.
- **Mirrored text** on a real part would still pass `text_check.py`.
- **No physical print yet** of any AI-designed part, so real-world fit is unproven. Print the pill box and knob before launch.
