# TweakMyPart freemium: free to talk, pay to build (spec for approval)

James, 22 Sep: "Make it like PipeVoice: a free tool, easy to sell. If something costs me money, like a complex model, warn them and charge, or require a premium monthly account with limits."

## What the numbers say (22 Sep benchmarks and prod data)

| cost to us | Sonnet 5 via API |
|---|---|
| Questions round (photo, concepts, measurement diagrams) | ≈ $0.14 (£0.11) |
| Simple one-part build (knob, bracket) | $0.55 to $0.75 |
| Two-part build (pill box) | ≈ $0.82 |
| Three-part mechanism (clamp strut) | ≈ $2.70 |

- **There is no free build engine.** Cheap OpenRouter models were no cheaper per good build once repeated (GLM-5.2: 7/9, about $1.13), and a free Gemini key falls back to paid capacity after a few requests.
- **Free chat is cheap:** £0.11 to £0.56 per active free user a month.
- **Free Sonnet builds are expensive:** one free build per user costs about £0.71 to £1.16 a month each, which needs roughly a 1-in-10 conversion to Premium to pay for itself.
- **Launch blocker:** builds today run on James's personal Claude Max subscription. Serving customers that way is very likely against Anthropic's terms, so launch means moving the worker to an Anthropic API key, and the costs above become real. Check the terms before going public.

## The tiers

### Free (account required, Clerk sign-in as today)
- Chat with the mascot, photo reading, 2 to 3 concepts, measurement diagrams, the estimated build price. **Cap: 10 question rounds a month** (worst case about £1.10 per user).
- My prints, delete, viewing anything they already paid for.
- **No free builds**, except the one welcome build below.
- **Welcome build:** the first build on a new account is free when its predicted price is at most **£3.00**, so the first experience is complete. Worst case about £2.10 per signup, once.

### Pay per build
- The price shows before building, as now: predicted AI cost × 1.4, rounded up to 10p, floor £2. The quote is binding.
- "Approve and build · £3.60" opens Stripe Checkout; the build job is queued only after the payment webhook confirms.
- **Complex warning:** above £6 the approve step says "This is a complex part (several pieces, moving parts). It takes up to 30 minutes." Above £15 the build is refused with "too complex for now, try splitting it".
- **Failed build:** one automatic retry at our cost; if that fails too, a full automatic refund and a "we couldn't make this" message. The customer never pays for a failure.
- Tweaks after a build: priced the same way (a tweak's predicted cost × 1.4, floor £1).

### Premium, £9.99 a month (Stripe subscription)
- **£12 of build credit a month**, measured in the same quoted prices, so any mix of parts (for example four simple parts, or one 3-part mechanism and a knob). Unused credit does not roll over.
- Unlimited question rounds, priority in the queue, tweaks drawn from the same credit.
- Over the allowance: pay per build at 20% off.
- Cancel any time from a Stripe customer portal link.
- **Our cost if a subscriber uses everything:** £12 of quoted builds cost us about £8.60, plus about £1 of question rounds, plus about £0.45 Stripe fees, so roughly break-even at full use and profitable for typical use. Tune the credit after a month of real data from the admin cost page.

## What already exists
- Price prediction, the binding quote, the admin cost page with predicted vs actual (PR #71, #73).
- `paymentsEnabled()` flag, `FREE_DESIGNS`/`canStartDesign` limits, an unused `orders` table with a `stripeSessionId` index.
- Clerk accounts, My prints, the daily spend cap.

## What gets built (three builds, in order)
1. **Stripe pay-per-build:** Checkout session at approve, webhook to queue the job, refund on double failure, `orders` rows, receipts by Stripe. Test mode first. Uses the `stripe-best-practices` skill.
2. **Free-tier limits:** question-round counter, welcome build, complex warning and refusal thresholds, the paywall copy, a pricing page.
3. **Premium subscription:** Stripe subscription and customer portal, a credit ledger (monthly grant, debits per quote, refunds back to credit), header credit badge, 20% off overage.

Then the lander refresh, written from these tiers.

## Success criteria (checked end to end in Stripe test mode)
- A new free user can chat, see concepts and a price, get one welcome build, and is asked to pay for the second.
- A paid build charges exactly the quoted price, and a failed build refunds automatically.
- A Premium user's builds debit credit; at zero credit they see the 20%-off price.
- The admin cost page shows margin per build and per subscriber.

## Decisions for James (recommended defaults above)
1. Premium price and credit: £9.99 with £12 of credit?
2. Welcome build: yes, first build free up to £3?
3. Free question-round cap: 10 a month?
