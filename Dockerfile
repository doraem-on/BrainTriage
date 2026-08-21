# Multi-stage build: compile the React frontend, then copy it into the
# Python backend's image so the whole app deploys as ONE service — the
# FastAPI app serves the built frontend directly (see app/main.py), so
# there's no separate static site, no cross-origin URL, no CORS dance.

FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
# Empty on purpose: same-origin requests once the backend serves this build
# (see api.js — "??" preserves an explicitly-empty string, unlike "||").
ENV VITE_API_BASE_URL=""
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist /app/frontend_dist

EXPOSE 8000
# Fetches the real CSF biomarker cohort using KAGGLE_USERNAME/KAGGLE_KEY
# (platform secrets, not baked into the image) at container start, not
# build time, so the credentials never need to touch the build layer.
# Fails fast (&&, not ;) if that fetch fails, rather than starting in a
# silently-broken state where the CSF stage can't train.
CMD ["sh", "-c", "python fetch_real_data.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
