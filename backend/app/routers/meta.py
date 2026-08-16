import json
import os

from fastapi import APIRouter

from app.ml.features import (
    STAGE_ORDER, STAGE_LABELS, STAGE_FEATURES, FEATURE_LABELS,
    FEATURE_HIGHER_IS_WORSE, ESCALATION_THRESHOLDS, STAGE_COST_UNITS,
    DIAGNOSIS_CLASSES,
)

router = APIRouter(prefix="/api/meta", tags=["meta"])

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
            "Models are trained on a SYNTHETIC cohort generated to match documented "
            "population statistics from published ADNI/OASIS cohort literature "
            "(MoCA/MMSE/CDR ranges, plasma biomarker panels, FreeSurfer MRI volumetrics, "
            "amyloid/tau/FDG PET SUVR conventions). No real ADNI/OASIS subject-level "
            "data is included — both require a signed Data Use Agreement. Swap in a "
            "real, credentialed data loader before any clinical use."
        ),
        "intended_use": (
            "Research / hackathon demonstration of an adaptive, cost-aware diagnostic "
            "triage pipeline. NOT a validated clinical diagnostic device."
        ),
    }
