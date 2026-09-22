# TweakMyPart go-live checklist (open sign-ups to anyone)

James, 22 Sep: open it up so others can sign up, once the paid path is ready. Chosen: open fully, not a waitlist and not a free beta on his subscription.

## Build work (the brain dispatches and verifies)
- [x] **Freemium build 1** — Stripe pay-per-build and the welcome build (in progress, build-1201).
- [x] **Freemium build 2** — 10 free question rounds a month, complex warning above £6 and refusal above £15, a pricing page, the paywall copy.
- [x] **Open sign-ups switch** (built, off) — `OPEN_SIGNUPS=true` lets any verified email use the product; `ALLOWED_EMAILS` stays for the private mode. A refused address still gets the current clear message.
- [x] **Worker on an Anthropic API key** (LIVE since 22 Sep 15:10: knob built in 3.2 min, $0.51 on the key) — the job proxy injects `ANTHROPIC_API_KEY` from `/etc/printtweak/worker.env` instead of forwarding James's Claude login token. Question rounds, builds and the preview judge all move over; the admin cost page is then real money.
- [x] **Privacy and terms pages** (live with placeholders for James) — `/privacy` and `/terms`, linked in the footer and at sign-up, from the drafts below after James edits them.
- [ ] **Launch smoke test** — a stranger account (fresh Gmail) signs up, gets the welcome build, pays for a second build in Stripe live mode with a real card, and a forced failure refunds.

## James's part (about 20 minutes; I never see the keys)
1. **Anthropic API key:** console.anthropic.com, add billing and a monthly spend limit (suggest £100 to start), create a key, then put it on the VPS with the command I send.
2. **Stripe:** activate the account for live payments (business details, bank account), create the webhook endpoint I give you, then set the live secret key and webhook secret with the command I send.
3. **Legal pages:** read the drafts, fill in your name or company and contact address, and say "approved".
4. **Final yes** to flip sign-ups open.

## Draft: privacy notice (for James to edit — not legal advice)
- **Who we are:** TweakMyPart, run by [your name or company], [contact email]. We are the data controller.
- **What we collect:** your email and name from sign-in (Clerk); what you type and the photos or model files you upload; the designs we make for you; payment records (card details stay with Stripe; we never see them).
- **Why:** to design and deliver your parts, to take payment, to email you when a part is ready, and to improve how we design parts (for example, corrections you give are reused, without your name or email, to avoid the same mistake for other customers).
- **Who processes it for us:** Clerk (sign-in), Convex (database and file storage, EU region), Railway (website hosting), Anthropic (AI that reads your request and photos and writes the design; not used to train their models under their commercial terms), TypeSafe (checks whether a suggested approach fits what you said), Stripe (payments), Resend (emails).
- **How long:** designs and uploads stay until you delete them from My prints or close your account; payment records are kept for 6 years for tax.
- **Your rights:** access, correction, deletion, and complaint to the ICO. Email [contact email].

## Draft: terms (for James to edit — not legal advice)
- The service designs 3D-printable files from your description. You are responsible for checking a part is suitable and safe for its use; don't use our parts where a failure could hurt someone.
- You must own or have permission for anything you upload.
- We refuse weapons, weapon parts, trademarked characters and logos, and anything unsafe.
- Prices are shown before each build and are what you pay. If we can't make your part, you're refunded automatically.
- Premium renews monthly until you cancel; unused credit doesn't roll over.
- The files are yours to print for yourself and to sell prints of; you may not resell the design files as your own design service.
- We may suspend accounts that abuse the service. English law applies.
