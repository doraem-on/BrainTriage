"""Adaptive multi-stage inference: run only the stages a patient's evidence
justifies, fuse cumulative risk, and explain the final call.

This is the core "prioritization" logic: instead of running every patient
through all four stages (cheap cognitive screening all the way to costly PET
imaging), each stage's output is checked against an escalation threshold. A
patient whose cognitive screen is unremarkable never needs a blood draw or a
scan; a patient who screens ambiguous at blood biomarkers gets escalated to
MRI; only genuinely high-risk, diagnostically ambiguous cases reach PET. This
mirrors real diagnostic triage and is what makes the system useful in
resource-constrained settings (e.g. limited PET/MRI slots).
"""
import os

import joblib
import numpy as np

from app.ml.features import (
    STAGE_ORDER, STAGE_FEATURES, ESCALATION_THRESHOLDS,
    DIAGNOSIS_CLASSES, STAGE_COST_UNITS,
)
from app.ml.explain import explain_prediction, _load_model

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")


def _cumulative_columns(stage: str) -> list[str]:
    idx = STAGE_ORDER.index(stage)
    return [f"risk_prob_{s}" for s in STAGE_ORDER[:idx]]


def run_pipeline(patient_data: dict) -> dict:
    """patient_data: dict with keys for whichever stage features are
    available (cognitive always required; blood/mri/pet optional — if
    missing, the pipeline stops at the last stage with data and reports a
    recommendation rather than fabricating a result for missing stages).
    """
    stage_results = []
    cumulative = {}
    last_completed = None
    diagnosis_proba = None

    for stage in STAGE_ORDER:
        feats = STAGE_FEATURES[stage]
        if not all(f in patient_data and patient_data[f] is not None for f in feats):
            # No data for this stage (either not collected yet, or gated out)
            break

        feature_cols = feats + _cumulative_columns(stage)
        x_row = np.array([
            cumulative[c] if c.startswith("risk_prob_") else patient_data[c]
            for c in feature_cols
        ], dtype=float)

        clf = _load_model(stage)
        proba = clf.predict_proba(x_row.reshape(1, -1))[0]
        risk_prob = float(proba[1] + proba[2])  # P(MCI) + P(AD)
        cumulative[f"risk_prob_{stage}"] = risk_prob
        diagnosis_proba = proba

        explanation = explain_prediction(stage, feature_cols, x_row)

        threshold = ESCALATION_THRESHOLDS.get(stage)
        escalate = threshold is not None and risk_prob >= threshold

        stage_results.append({
            "stage": stage,
            "risk_probability": round(risk_prob, 4),
            "class_probabilities": {c: round(float(p), 4) for c, p in zip(DIAGNOSIS_CLASSES, proba)},
            "escalated": bool(escalate) if threshold is not None else None,
            "threshold": threshold,
            "top_contributors": explanation[:5],
            "cost_units": STAGE_COST_UNITS[stage],
        })
        last_completed = stage

        if threshold is not None and not escalate:
            break  # gated: stop here, route to monitoring

    if last_completed is None:
        return {"error": "insufficient_data", "message": "Cognitive screening data is required."}

    final_probs = {c: round(float(p), 4) for c, p in zip(DIAGNOSIS_CLASSES, diagnosis_proba)}
    predicted_class = DIAGNOSIS_CLASSES[int(np.argmax(diagnosis_proba))]
    final_risk = stage_results[-1]["risk_probability"]

    reached_pet = last_completed == "pet"
    if final_risk < 0.30:
        urgency = "low"
        recommendation = "Routine monitoring; re-screen in 12 months."
    elif final_risk < 0.55:
        urgency = "moderate"
        recommendation = f"Elevated risk signal at {stage.capitalize()} stage; re-screen in 6 months or escalate sooner if symptoms progress."
    elif final_risk < 0.75:
        urgency = "high"
        recommendation = "Refer to specialist for confirmatory workup." if not reached_pet else "Refer to specialist; imaging-confirmed elevated risk."
    else:
        urgency = "critical"
        recommendation = "Immediate specialist referral recommended."

    total_cost_units = sum(s["cost_units"] for s in stage_results)
    max_cost_units = sum(STAGE_COST_UNITS.values())

    return {
        "stages_completed": [s["stage"] for s in stage_results],
        "last_stage": last_completed,
        "reached_pet": reached_pet,
        "stage_results": stage_results,
        "final_class_probabilities": final_probs,
        "predicted_class": predicted_class,
        "final_risk_probability": final_risk,
        "urgency": urgency,
        "recommendation": recommendation,
        "cost_units_used": total_cost_units,
        "cost_units_saved": max_cost_units - total_cost_units,
        "max_cost_units": max_cost_units,
    }
