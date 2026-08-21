# Deploying BrainTriage publicly

The whole app — FastAPI backend, ML models, and the built React frontend —
ships as **one Docker container** (see `Dockerfile` at the repo root). The
backend serves the frontend directly, so there's one URL and no CORS setup
to get right.

This has been built and run locally end-to-end in Docker (`docker build` +
`docker run`) — including with **zero environment variables set at all** —
verified: health check, frontend serving, SPA routing, login, DB auto-seed,
and the CSF/Blood stage's real training data downloading anonymously from
its public Kaggle listing (no account, no token — the `kaggle==2.2.4`
client falls back to anonymous access for public datasets).

## Environment variables — all optional

| Variable | Needed? | What it's for |
|---|---|---|
| `KAGGLE_API_TOKEN` | Only if anonymous downloads ever get rate-limited/blocked from your host's IP | Get it from [kaggle.com/settings](https://www.kaggle.com/settings) → **API Tokens** → **Generate New Token** — paste the value directly into the platform's own env var field. **Never into a chat, screenshot, or commit** — if one leaks, revoke it on that same settings page immediately. |
| `ANTHROPIC_API_KEY` | Only if you want the AI Assistant tab to actually respond | Leave unset and it shows a "not configured" card instead. No per-visitor rate limiting yet, so a public link with this set can spend against your key — set deliberately. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | No — defaults to `admin` / `braintriage2026` | Change these if you want this deployment to require a real password instead of the "Continue as Demo Admin" one-click login. |
| `JWT_SECRET` | Recommended | Any random string, signs login sessions. Render auto-generates one; set it by hand elsewhere. |

## Option A: Render (Blueprint)

1. Go to [render.com](https://render.com), sign in (GitHub login is easiest).
2. **New +** → **Blueprint** → connect GitHub → select the `BrainTriage` repo.
   Render detects `render.yaml` automatically.
3. It may prompt for `KAGGLE_API_TOKEN` / `ANTHROPIC_API_KEY` — both are
   fine to leave blank per the table above.
4. Click **Apply** / **Deploy Blueprint**. First build takes a few minutes.
5. **Note**: Render requires a card on file (a $1 verification hold, not a
   charge) before it'll provision a service via Blueprint, even on the free
   tier — this isn't documented clearly on their pricing page. If you'd
   rather not, use Option B.

## Option B: Railway (no card required for the 30-day trial)

1. Go to [railway.com](https://railway.com), sign in with GitHub.
2. **New Project** → **Deploy from GitHub repo** → select `BrainTriage`.
   Railway auto-detects the `Dockerfile` — no extra config file needed, and
   with no required env vars, it should deploy successfully with zero
   configuration.
3. **Settings** → **Networking** → **Generate Domain** for the public URL.
4. Optional: add any of the env vars from the table above under the
   service's **Variables** tab if you want them (e.g. a real admin password).
5. The 30-day / $5-credit free trial requires no card; continuing past that
   (or Render's permanent free plan) does.

## Things worth knowing about free tiers generally

- **Cold starts**: free web services on both platforms spin down after a
  period of no traffic and take ~30–60s to wake back up on the next request.
  If you're demoing live, load the link a minute before you need it.
- **Data resets on restart**: neither free tier guarantees a persistent disk,
  so the SQLite database (patient records) and trained models reset to a
  fresh auto-seeded demo cohort every time the service restarts or
  redeploys. For a public demo this is actually convenient — it self-cleans
  — but don't expect anything entered by a visitor to persist long-term.

## If you'd rather use a different platform

Any platform that can run a Dockerfile and inject environment variables at
runtime works the same way — Fly.io (requires a card for all orgs, per their
own docs), a VPS, etc. Point it at the `Dockerfile`; no env vars are
strictly required, per the table above.
