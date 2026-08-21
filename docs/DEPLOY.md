# Deploying BrainTriage publicly

The whole app — FastAPI backend, ML models, and the built React frontend —
ships as **one Docker container** (see `Dockerfile` at the repo root). The
backend serves the frontend directly, so there's one URL and no CORS setup
to get right.

This has been built and run locally end-to-end in Docker (`docker build` +
`docker run`, verified the login flow, auto-seeded demo data, SPA routing,
and that the frontend correctly makes same-origin API calls) — but not
against Render itself, since that needs an account only you can create.

## Steps (Render, ~5 minutes)

1. Go to [render.com](https://render.com) and sign in (GitHub login is easiest).
2. **New +** → **Blueprint** → connect your GitHub account → select the
   `BrainTriage` repo. Render will detect `render.yaml` automatically.
3. It'll prompt you for these secrets before deploying:
   - `KAGGLE_USERNAME` / `KAGGLE_KEY` — from
     [kaggle.com/settings](https://www.kaggle.com/settings) → API → **Create
     New Token** (downloads a `kaggle.json`; the two values inside it are
     what go here). Required — the CSF/Blood stage fetches its real training
     data from Kaggle at container start.
   - `ANTHROPIC_API_KEY` — **optional**. Leave blank and the AI Assistant tab
     just shows its "not configured" card. Only set this if you're fine with
     a public link being able to spend against your key — there's no
     per-visitor rate limiting on that endpoint yet.
4. Click **Apply** / **Deploy Blueprint**. First build takes a few minutes
   (Node + Python + model training on container start).
5. You'll get a URL like `https://braintriage.onrender.com`. The demo
   credentials (`admin` / `braintriage2026`) are pre-filled behind the
   "Continue as Demo Admin" button on the login page — anyone with the link
   can explore with one click.

## Things worth knowing about the free tier

- **Cold starts**: Render's free web services spin down after ~15 minutes of
  no traffic and take ~30–60s to wake back up on the next request. If you're
  demoing live, load the link a minute before you need it.
- **Data resets on restart**: the free tier has no persistent disk, so the
  SQLite database (patient records) and trained models reset to a fresh
  auto-seeded demo cohort every time the service restarts or redeploys. For
  a public demo this is actually convenient — it self-cleans — but don't
  expect anything entered by a visitor to persist long-term.
- **Changing the demo password**: edit `ADMIN_USERNAME` / `ADMIN_PASSWORD` in
  the Render dashboard's environment variables for this service (or in
  `render.yaml` before deploying) if you want this instance to require a
  real login instead of being fully public.

## If you'd rather use a different platform

Any platform that can run a Dockerfile and inject environment variables at
runtime works the same way — Railway, Fly.io, a VPS, etc. The required env
vars are exactly the ones in `render.yaml`. The one Render-specific piece is
the Blueprint auto-detection; elsewhere you'd point the platform at the
`Dockerfile` and set the same env vars by hand.
