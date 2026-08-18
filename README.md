# BrainTriage

AI-driven prioritization for early Alzheimer's diagnostic pathways — built for
the **Precision Care Challenge 2026**.

Most AD-risk demos run every patient through every test. BrainTriage models
the actual clinical constraint: MRI and PET slots are scarce, so the system
only escalates a patient to the next, more expensive/invasive stage
(**Cognitive → Blood → MRI → PET**) when the cumulative risk evidence
justifies it. Everything else is routed to routine monitoring. The dashboard
reports how much diagnostic capacity that saves across the cohort.

**⚠️ Three of four stages train on real published data; PET alone is
synthetic — see [docs/DATA_NOTE.md](docs/DATA_NOTE.md) for the per-stage
breakdown before showing this to a clinical audience.**

## What's inside

- **Adaptive 4-stage pipeline** with per-stage stacked classifiers
  (RandomForest; each stage sees its own features + upstream risk scores).
- **Real data for 3 of 4 stages**: Cognitive and MRI train on 606 real
  OASIS subject-visits (CC0), Blood/CSF trains on a real 198-patient CSF
  biomarker cohort (Dakterzada et al. 2023). Grouped/stratified splits so no
  subject leaks between train and test. PET stays synthetic, conditioned on
  each real subject's actual diagnosis — see [docs/DATA_NOTE.md](docs/DATA_NOTE.md).
- **Exact SHAP explainability** per prediction — top contributing factors,
  direction of effect.
- **Cost-aware triage queue** — patients ranked by urgency, with an
  estimated-resource-saved metric vs. running everyone through the full
  pipeline.
- **Longitudinal trajectory view** — risk over repeated assessments.
- **One-click clinician PDF report** per patient.
- **Model Card** — accuracy/F1/ROC-AUC *and data source* per stage, surfaced
  both in the API (`GET /api/meta/model-card`) and the dashboard.
- **What-If Simulator** — drag a slider on any real recorded feature (MMSE,
  CSF tau, hippocampal volume, …) and watch the model's risk estimate update
  live, stateless, nothing saved (`POST /api/patients/{id}/simulate`).
- **Diagnostic Resource Optimizer** — tell it how many CSF/MRI/PET slots a
  clinic has this week and it ranks the patients actually awaiting that test
  by risk, scheduling the scarce slots to whoever benefits most
  (`GET /api/queue/optimize`, `/optimize` page).
- **Auto-generated plain-English risk narrative** per stage, built from the
  same SHAP contributions as the explainability chart.
- **3D neural-network brain visualization** (Three.js, procedural — no
  external assets) as the dashboard hero and sidebar accent.

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
python fetch_real_data.py   # pulls the CSF cohort (needs ~/.kaggle/kaggle.json); OASIS is already committed
python seed_demo.py            # optional: populate demo patients
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
  data/                    real OASIS CSVs (CC0), committed, see docs/DATA_NOTE.md
  data_external/           real CSF biomarker CSV (CC BY-NC-ND), fetched not committed
  real_data.py             loads + cleans both real cohorts
  synthetic_data.py        synthetic PET features, conditioned on real diagnosis
  ml/features.py           per-stage feature schema, upstream-stacking, data source
  ml/train.py              trains + persists one classifier per stage
  ml/pipeline.py           adaptive inference: run only justified stages, fuse risk
  ml/explain.py            SHAP-based per-prediction explainability
  routers/                 patients, queue, meta, report (PDF) endpoints
frontend/src/
  pages/                   Dashboard, NewPatient, PatientDetail
  components/               pipeline visualization, explainability chart,
                             trajectory chart, stage intake forms, model card
docs/DATA_NOTE.md          data provenance & how to swap in real ADNI/OASIS access
```
