# Data Provenance

**Three of BrainTriage's four stages now train on real, published, publicly
licensed data.** The split is per-stage, surfaced live at
`GET /api/meta/model-card` and `GET /api/meta/schema` (`stage_data_source`),
plus the "Model Card" panel on the dashboard.

| Stage | Data source | Cohort |
|---|---|---|
| Cognitive | **Real** | OASIS cross-sectional + longitudinal (606 subject-visits) |
| Blood/CSF | **Real** | Dakterzada et al. 2023 CSF biomarker cohort (198 patients) |
| MRI | **Real** | Same OASIS cohorts, volumetric columns |
| PET | Synthetic | No freely available real PET SUVR dataset exists |

## Real data #1: OASIS via Kaggle (committed to the repo)

`backend/app/data/oasis_cross-sectional.csv` and `oasis_longitudinal.csv` are
real, de-identified, publicly released research data — the Kaggle mirror
[`jboysen/mri-and-alzheimers`](https://www.kaggle.com/datasets/jboysen/mri-and-alzheimers)
(**CC0-1.0**), which republishes:

- **OASIS-1 cross-sectional**: Marcus DS, Wang TH, Parker J, Csernansky JG,
  Morris JC, Buckner RL. (2007) Open Access Series of Imaging Studies
  (OASIS): Cross-Sectional MRI Data in Young, Middle Aged, Nondemented, and
  Demented Older Adults. *Journal of Cognitive Neuroscience*, 19, 1498-1507.
- **OASIS-2 longitudinal**: Marcus DS, Fotenos AF, Csernansky JG, Morris JC,
  Buckner RL. (2010) Open Access Series of Imaging Studies: Longitudinal MRI
  Data in Nondemented and Demented Older Adults. *Journal of Cognitive
  Neuroscience*, 22, 2677-2684.

After dropping rows with no clinical evaluation on record: **606 real
subject-visits** (341 CN / 193 MCI / 72 AD), with age, education years,
socioeconomic index, sex, MMSE score, and three MRI volumetric measures
(eTIV, nWBV, ASF). `backend/app/real_data.py::load_real_cohort()`.

**Diagnosis labels come from each subject's real Clinical Dementia Rating**
(CDR 0 → CN, 0.5 → MCI, ≥1 → AD) — the standard OASIS convention. CDR is
deliberately **excluded** from the model's input features, since including
it (the thing the label is derived from) would let the model trivially look
up the answer.

CC0 is public domain, so these CSVs are committed directly to the repo — no
Kaggle account needed to run BrainTriage. To refresh:
`kaggle datasets download -d jboysen/mri-and-alzheimers --unzip`.

## Real data #2: CSF biomarkers (fetched, not committed)

`backend/app/data_external/csf_biomarkers.csv` is real, published clinical
research: 212 plasma/CSF samples (20 controls, 89 MCI, 103 AD) with age, sex,
MMSE, APOE4 status, and CSF amyloid/total-tau/phosphorylated-tau — via the
Kaggle mirror
[`fereshtehjozaghkar/plasma-lipidomics-in-alzheimers-disease`](https://www.kaggle.com/datasets/fereshtehjozaghkar/plasma-lipidomics-in-alzheimers-disease):

> Dakterzada F, Jové M, Huerto R, Carnes A, Sol J, Pamplona R, Piñol-Ripoll G.
> (2023) Changes in Plasma Neutral and Ether-Linked Lipids Are Associated
> with The Pathology and Progression of Alzheimer's Disease. *Aging and
> Disease*, 14(5), 1728. DOI: [10.34810/data614](https://doi.org/10.34810/data614)

**License caveat:** the dataset's own description states **CC BY-NC-ND**
(noncommercial, no-derivatives) — Kaggle's platform-level license tag says
Apache-2.0, but we treat the author's explicit statement as authoritative.
Noncommercial use (this is a noncommercial student hackathon project) is
fine; to avoid redistributing a copy of the dataset itself under an
ambiguous license, **this CSV is not committed to the repo** — it's fetched
at setup time via `backend/fetch_real_data.py` (requires a Kaggle API token
at `~/.kaggle/kaggle.json`) and gitignored. If you plan to use this project
commercially or publish/share the dataset file itself, contact the original
authors first.

The technically-real measurements here are CSF (cerebrospinal fluid, via
lumbar puncture), not a venous blood draw — the UI still calls this stage
"Blood" in the pipeline narrative for simplicity, but labels it precisely
("CSF Biomarkers (Lumbar Puncture)") in the stage detail, and its cost/
invasiveness score sits between a blood draw and an MRI to reflect that.

Because Cognitive/MRI (OASIS) and Blood/CSF (Dakterzada et al.) are two
**different real cohorts with no shared subjects**, the pipeline's stage
stacking is deliberately NOT "every prior stage feeds the next" — see
`STAGE_UPSTREAM_INPUTS` in `backend/app/ml/features.py`. Concretely: the
Cognitive model IS evaluated on the CSF cohort's real age/sex/MMSE to
produce a cross-cohort `risk_prob_cognitive` feature — but since that study
didn't collect SES or education, those two are imputed with the OASIS
training-cohort median. **This is the only imputation anywhere in the
pipeline**, and it's disclosed in the Model Card text, not just here. The
MRI and PET stages stay entirely within the OASIS cohort, so their upstream
`risk_prob_cognitive` is self-consistent with zero imputation.

## The one remaining synthetic stage: PET

No freely-available real PET SUVR tabular dataset was found (checked Kaggle
broadly — biomarker/SUVR/ADNI-PET searches turned up nothing legitimately
real and openly licensed). Real ADNI PET data exists but requires a signed
Data Use Agreement and manual, credentialed registration — not something
that can be scripted.

`backend/app/synthetic_data.py::synthesize_pet()` generates PET features for
each real OASIS subject, **conditioned on that subject's real CDR-derived
diagnosis**, so the synthetic values correlate with real disease severity
rather than being independently random. This keeps the pipeline internally
consistent, but the actual SUVR *values* are not measurements from any real
person. Ranges/directionality approximate published ADNI PET literature.

## Demo-seeded patients (`backend/seed_demo.py`)

Seeded patients are real OASIS subjects, labeled by their original OASIS
subject ID ("Research Subject OAS2_0049") — never a fabricated name. Their
Blood/CSF-stage demo values are **borrowed from a real CSF-cohort patient
with the same real diagnosis** (not synthesized) — every number in the demo
seed is a genuine measurement from an actual research participant, just not
always the same participant across every stage for the same seeded patient.
Only the seeded PET values are synthetic, matching how the PET stage itself
is trained.

## Swapping in real ADNI PET data later

`app/ml/features.py`, `app/ml/train.py`, and `app/ml/pipeline.py` are written
against fixed column names (`STAGE_FEATURES`), not against the generator.
Once your team has credentialed ADNI access, write a loader producing real
`amyloid_suvr`, `tau_suvr`, `fdg_suvr` columns joined to real diagnoses, swap
it in for `synthesize_pet()` in `train.py`, retrain, and re-seed.

## Honesty checklist before any real clinical demo

- [ ] Say plainly which stages are real vs. synthetic — the Model Card does
      this automatically, don't paper over it in a slide deck.
- [ ] Don't claim validated clinical accuracy — even the real-data stages
      are evaluated on small (142/50-subject) held-out test splits, not a
      clinical validation study.
- [ ] Don't attach names to the seeded OASIS demo subjects — they're real
      de-identified research participants.
- [ ] Respect the CSF dataset's stated noncommercial/no-derivatives terms —
      don't redistribute the raw file or use this commercially without
      contacting the original authors.
- [ ] This is a triage-prioritization prototype, not a diagnostic device.
- [ ] Don't claim RINPAS "reviewed" or "validated" anything unless that
      genuinely happened and they've agreed to be cited that way.
