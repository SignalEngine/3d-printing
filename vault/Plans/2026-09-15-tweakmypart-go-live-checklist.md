# TweakMyPart go-live checklist (personal mode)

For James. About 45 minutes of clicking, done in any order within each step. **Never paste a key or token into Claude, chat, Telegram or a file in a repo.** Where a value is secret, the step says exactly where it goes.

What is already done: the site code (Tasks 1-6 + design pass, merged), the job sandbox and worker code on the VPS. What this checklist does: gives the site a login (Clerk), a database (Convex), a web address (Railway) and the worker's Claude access (your subscription token). Payments, a custom domain and emails stay off for now.

---

## 1. Clerk (sign-in), about 10 min

1. Go to https://dashboard.clerk.com and click **Create application**. Name it **TweakMyPart**. Sign-in options: tick **Email** only (email code or magic link). Create.
2. **Configure → Restrictions (or Allowlist):** turn on the allowlist and add your own email. (The site also checks its own allowlist; this stops strangers even getting an account.)
3. **Configure → JWT templates → New template → Convex.** Keep the name **convex** exactly. Save.
4. **Configure → API keys.** Keep this tab open; you need three values:
   - **Publishable key** (starts `pk_`), goes into Railway in step 3.
   - **Secret key** (starts `sk_`), goes into Railway in step 3.
   - **Frontend API URL** (looks like `https://xxxx.clerk.accounts.dev`), goes into Convex in step 2.

## 2. Convex (database), about 10 min

1. In your SSH session run: `cd /root/printtweak && npx convex login`, open the link it prints, approve.
2. Then: `npx convex deploy`. Say yes to creating a production deployment. It prints a URL like `https://something.convex.cloud`. That URL is not secret; tell Claude it.
3. Set the sign-in link (not secret): `npx convex env set CLERK_JWT_ISSUER_DOMAIN https://xxxx.clerk.accounts.dev` (your Frontend API URL from 1.4).
4. Set who may use it: `npx convex env set ALLOWED_EMAILS you@example.com` (your email, the same one as in Clerk).
5. Tell Claude "Convex done". Claude then sets the rest itself without showing values: `WORKER_SECRET` (a random secret shared with the worker), `ADMIN_EMAILS`, and `SITE_URL` once Railway gives an address.

## 3. Railway (web address), about 10 min

1. https://railway.com → **New Project → Deploy from GitHub repo → SignalEngine/printtweak**.
2. In the service → **Variables**, add:
   - `NEXT_PUBLIC_CONVEX_URL` = the Convex URL from 2.2
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` = Publishable key from 1.4
   - `CLERK_SECRET_KEY` = Secret key from 1.4
3. **Settings → Networking → Generate Domain.** You get an address like `tweakmypart-production.up.railway.app`. Not secret; tell Claude it.
4. In Clerk → **Domains / Allowed origins**, add that Railway address.

## 4. Worker token (your Claude subscription), about 5 min

This lets the design worker on the VPS use your Claude plan. Do it in **your own** SSH shell, not through Claude.

1. Run `claude setup-token`, follow the browser login, and copy the token it prints.
2. Run these three lines. The second one waits for you to paste the token; nothing is shown and nothing is saved in your shell history:
   ```bash
   sudo mkdir -p /etc/printtweak && sudo touch /etc/printtweak/worker.env && sudo chmod 600 /etc/printtweak/worker.env
   read -rs TOKEN && echo "CLAUDE_CODE_OAUTH_TOKEN=$TOKEN" | sudo tee /etc/printtweak/worker.env >/dev/null && unset TOKEN
   sudo grep -c '^CLAUDE_CODE_OAUTH_TOKEN=.\+' /etc/printtweak/worker.env
   ```
   The last line must print `1`.
3. Tell Claude "token done". Claude adds `CONVEX_URL` and `WORKER_SECRET` to that file without printing the token.

## 5. Then Claude does the rest

- Runs the sandbox test with your token (the live checks skipped in Tasks 3-5).
- Starts the worker service and checks its heartbeat in Convex.
- Opens the Railway address, signs you in, and runs the 5 real requests end to end (knob, trinket box, trophy, Netgate bracket, pill box), recording time, result and whether the 3D preview loads on a phone.

## Later, not now
Payments (Stripe), tweakmypart.com domain, ready emails (Resend), other users (API-key mode).
