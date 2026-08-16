# BrainTriage

AI-driven prioritization for early Alzheimer's diagnostic pathways — built for
the **Precision Care Challenge 2026**.

Most AD-risk demos run every patient through every test. BrainTriage models
the actual clinical constraint: MRI and PET slots are scarce, so the system
only escalates a patient to the next, more expensive/invasive stage
(**Cognitive → Blood → MRI → PET**) when the cumulative risk evidence
justifies it. Everything else is routed to routine monitoring. The dashboard
reports how much diagnostic capacity that saves across the cohort.

**⚠️ Runs entirely on a synthetic demo cohort — see [docs/DATA_NOTE.md](docs/DATA_NOTE.md)
before showing this to a clinical audience.**

## What's inside

- **Adaptive 4-stage pipeline** with per-stage stacked classifiers
  (RandomForest; each stage sees its own features + upstream risk scores).
- **Exact SHAP explainability** per prediction — top contributing factors,
  direction of effect.
- **Cost-aware triage queue** — patients ranked by urgency, with an
  estimated-resource-saved metric vs. running everyone through the full
  pipeline.
- **Longitudinal trajectory view** — risk over repeated assessments.
- **One-click clinician PDF report** per patient.
- **Model Card** — accuracy/F1/ROC-AUC per stage plus an explicit data
  provenance & intended-use disclosure.

## Architecture

```
backend/   FastAPI + SQLite (SQLModel) + scikit-learn + SHAP
frontend/  React (Vite) + Recharts
```

## Running locally

### 1. Backend (http://localhost:8000)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed_demo.py     # optional: populate demo patients
uvicorn app.main:app --reload --port 8000
```

Models train automatically on first startup (a few seconds) if no trained
artifacts exist yet; API docs at http://localhost:8000/docs.

### 2. Frontend (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Repo layout

```
backend/app/
  synthetic_data.py     synthetic ADNI/OASIS-schema cohort generator
  ml/features.py         per-stage feature schema, escalation thresholds
  ml/train.py             trains + persists one classifier per stage
  ml/pipeline.py          adaptive inference: run only justified stages, fuse risk
  ml/explain.py            SHAP-based per-prediction explainability
  routers/                 patients, queue, meta, report (PDF) endpoints
frontend/src/
  pages/                   Dashboard, NewPatient, PatientDetail
  components/               pipeline visualization, explainability chart,
                             trajectory chart, stage intake forms, model card
docs/DATA_NOTE.md          data provenance & how to swap in real ADNI/OASIS access
```
