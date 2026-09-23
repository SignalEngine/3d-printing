# Feedback drawer with a free-build reward: brief (James, 23 Sep 2026)

Told to the TweakMyPart session in chat on 23 Sep.

## What James said
- An easy way to give feedback, "literally at the bottom, like a pull-out screen", on mobile and desktop.
- For launch and the first users (including the free version). Questions like: how did you find it, did you find it okay,
  **where did you hear about us**, what was the problem with the build, was it a good experience, was it a good UI,
  what other features would you want.
- **If the feedback is useful, the user is credited with another free build.** "This will allow our first 10, 20 users to
  give feedback and use it for free. Won't cost us very much."
- The purpose: improve the system and the UI, find missing features, **learn where users came from (marketing)**, and
  learn what they'll actually use it for.

## What exists today (to check before designing)
- The free first build (`usedFreeTry`) and the paid build flow via Stripe (verified on staging 23 Sep).
- No feedback UI and no build-credit concept beyond the free first try. Not yet checked: whether admin can grant a free build.

## Open decisions (for James)
- Who decides that feedback is "useful" (auto rule / AI judge / James approves in admin), and the cap (first N users only?).
- Where the drawer lives: every page, or only after a build / on the ready page.
- One short form vs questions that change depending on where the user is (after a failed build: "what went wrong").
