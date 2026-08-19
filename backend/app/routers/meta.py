import json
import os

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.ml.features import (
    STAGE_ORDER, STAGE_LABELS, STAGE_FEATURES, FEATURE_LABELS,
    FEATURE_HIGHER_IS_WORSE, ESCALATION_THRESHOLDS, STAGE_COST_UNITS,
    DIAGNOSIS_CLASSES, STAGE_DATA_SOURCE, FEATURE_RANGES, ABSTENTION_MARGIN,
)

router = APIRouter(prefix="/api/meta", tags=["meta"], dependencies=[Depends(get_current_user)])

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts")


@router.get("/schema")
def get_schema():
    return {
        "stage_order": STAGE_ORDER,
        "stage_labels": STAGE_LABELS,
        "stage_features": STAGE_FEATURES,
        "feature_labels": FEATURE_LABELS,
        "feature_higher_is_worse": FEATURE_HIGHER_IS_WORSE,
        "escalation_thresholds": ESCALATION_THRESHOLDS,
        "stage_cost_units": STAGE_COST_UNITS,
        "diagnosis_classes": DIAGNOSIS_CLASSES,
        "stage_data_source": STAGE_DATA_SOURCE,
        "feature_ranges": FEATURE_RANGES,
        "abstention_margin": ABSTENTION_MARGIN,
    }


@router.get("/model-card")
def get_model_card():
    metrics_path = os.path.join(MODEL_DIR, "metrics.json")
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
    return {
        "metrics": metrics,
        "data_provenance": (
            "THREE of four stages train on REAL, published, publicly licensed data. "
            "Cognitive and MRI: the OASIS-1 cross-sectional and OASIS-2 longitudinal "
            "cohorts (Marcus et al. 2007, 2010), via the CC0-licensed Kaggle mirror "
            "jboysen/mri-and-alzheimers (606 subject-visits after cleaning); diagnosis "
            "labels come from each subject's real Clinical Dementia Rating (CDR 0 -> CN, "
            "0.5 -> MCI, >=1 -> AD), with CDR itself excluded from the model inputs to "
            "avoid leaking the label. Blood/CSF: a real cerebrospinal-fluid biomarker "
            "cohort of 198 patients (Dakterzada et al. 2023, Aging and Disease; CC "
            "BY-NC-ND, fetched at setup time rather than redistributed in-repo — see "
            "docs/DATA_NOTE.md). The Cognitive model's risk score is cross-evaluated on "
            "this cohort's real age/sex/MMSE, with SES and education (not collected in "
            "that study) imputed from the OASIS training median — the only imputation "
            "anywhere in this pipeline. PET stage is SYNTHETIC, conditioned on real OASIS "
            "diagnoses: no freely-available real PET SUVR dataset exists, and ADNI's "
            "requires a signed Data Use Agreement we don't have. See "
            "stage_data_source on GET /api/meta/schema for the machine-readable version."
        ),
        "intended_use": (
            "Research / hackathon demonstration of an adaptive, cost-aware diagnostic "
            "triage pipeline. NOT a validated clinical diagnostic device."
        ),
    }
