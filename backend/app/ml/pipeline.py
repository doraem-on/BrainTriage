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

On top of that, each stage carries an uncertainty/abstention layer: a
prediction whose top two classes are within ABSTENTION_MARGIN of each other
is too close to call, so the pipeline escalates to the next stage REGARDLESS
of whether the raw risk probability cleared the numeric threshold — "I'm not
confident enough, get more evidence" rather than forcing a confident-looking
number out of a genuinely ambiguous case.
"""
import os

import joblib
import numpy as np

from app.ml.features import (
    STAGE_ORDER, STAGE_FEATURES, ESCALATION_THRESHOLDS,
    DIAGNOSIS_CLASSES, STAGE_COST_UNITS, STAGE_UPSTREAM_INPUTS, STAGE_LABELS,
    STAGE_DATA_SOURCE, ABSTENTION_MARGIN, COUNTERFACTUAL_ELIGIBLE,
    FEATURE_RANGES, FEATURE_HIGHER_IS_WORSE, FEATURE_LABELS,
)
from app.ml.explain import explain_prediction, _load_model

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")


def _build_narrative(stage: str, predicted_class: str, risk_prob: float, top_contributors: list[dict]) -> str:
    class_text = {
        "CN": "cognitively normal", "MCI": "mild cognitive impairment", "AD": "Alzheimer's disease",
    }[predicted_class]
    drivers = [c for c in top_contributors if c["contribution"] > 0][:2]
    protectors = [c for c in top_contributors if c["contribution"] < 0][:1]

    sentence = (
        f"At the {STAGE_LABELS[stage]} stage, the model estimates a {risk_prob:.0%} probability "
        f"of MCI or AD, most consistent with {class_text}."
    )
    if drivers:
        driver_text = " and ".join(f"{d['label'].lower()} ({d['value']:.2g})" for d in drivers)
        sentence += f" This is driven primarily by {driver_text}."
    if protectors:
        p = protectors[0]
        sentence += f" {p['label']} ({p['value']:.2g}) is comparatively reassuring."
    return sentence


def _cumulative_columns(stage: str) -> list[str]:
    # Which upstream risk_prob_* a stage's model actually consumes — a real
    # patient always has all of these available by the time they reach this
    # stage (each is computed from their own prior stage in this same
    # pipeline run), so no imputation is needed at inference time; the
    # cross-cohort imputation in train.py is a training-time-only concern.
    return [f"risk_prob_{s}" for s in STAGE_UPSTREAM_INPUTS[stage]]


def _entropy_uncertainty(proba: np.ndarray) -> float:
    """Normalized Shannon entropy of the class distribution, 0 (certain) to
    1 (maximally uncertain — uniform over all 3 classes)."""
    p = np.clip(proba, 1e-12, 1.0)
    h = -np.sum(p * np.log(p))
    return float(h / np.log(len(proba)))


def _compute_counterfactual(clf, feature_cols, x_row, top_contributors, target_ceiling):
    """Finds the smallest change to the single most-responsible modifiable
    feature that would drop predicted risk below target_ceiling, by grid
    search (RandomForest predict_proba isn't guaranteed smooth, so a search
    is more honest than assuming linearity). Returns None if no eligible
    driver was found, or if even the most favorable plausible value in
    FEATURE_RANGES doesn't get there.
    """
    candidates = [
        c for c in top_contributors
        if c["contribution"] > 0 and c["feature"] in COUNTERFACTUAL_ELIGIBLE and c["feature"] in feature_cols
    ]
    if not candidates:
        return None
    driver = candidates[0]
    feature = driver["feature"]
    idx = feature_cols.index(feature)
    current_value = x_row[idx]
    lo, hi = FEATURE_RANGES[feature]
    higher_is_worse = FEATURE_HIGHER_IS_WORSE[feature]
    healthy_bound = lo if higher_is_worse else hi

    steps = np.linspace(current_value, healthy_bound, 16)[1:]
    for candidate_value in steps:
        trial = x_row.copy()
        trial[idx] = candidate_value
        proba = clf.predict_proba(trial.reshape(1, -1))[0]
        risk = float(proba[1] + proba[2])
        if risk < target_ceiling:
            return {
                "feature": feature,
                "label": FEATURE_LABELS[feature],
                "current_value": round(float(current_value), 2),
                "counterfactual_value": round(float(candidate_value), 2),
                "resulting_risk": round(risk, 4),
            }
    return None


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

        upstream_stages = STAGE_UPSTREAM_INPUTS[stage]
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
        stage_predicted_class = DIAGNOSIS_CLASSES[int(np.argmax(proba))]

        sorted_proba = np.sort(proba)[::-1]
        confidence_margin = float(sorted_proba[0] - sorted_proba[1])
        uncertainty = _entropy_uncertainty(proba)
        abstain = confidence_margin < ABSTENTION_MARGIN

        threshold = ESCALATION_THRESHOLDS.get(stage)
        risk_crossed = threshold is not None and risk_prob >= threshold
        escalate = risk_crossed or (threshold is not None and abstain)
        if risk_crossed:
            escalation_reason = "risk_threshold"
        elif escalate:
            escalation_reason = "low_confidence"
        else:
            escalation_reason = None

        counterfactual = _compute_counterfactual(
            clf, feature_cols, x_row, explanation, threshold if threshold is not None else 0.5
        )

        stage_results.append({
            "stage": stage,
            "risk_probability": round(risk_prob, 4),
            "class_probabilities": {c: round(float(p), 4) for c, p in zip(DIAGNOSIS_CLASSES, proba)},
            "escalated": bool(escalate) if threshold is not None else None,
            "escalation_reason": escalation_reason,
            "threshold": threshold,
            "threshold_distance": round(threshold - risk_prob, 4) if threshold is not None else None,
            "confidence_margin": round(confidence_margin, 4),
            "uncertainty": round(uncertainty, 4),
            "abstain": abstain,
            "top_contributors": explanation[:5],
            "counterfactual": counterfactual,
            "cost_units": STAGE_COST_UNITS[stage],
            "data_source": STAGE_DATA_SOURCE[stage],
            "narrative": _build_narrative(stage, stage_predicted_class, risk_prob, explanation),
            # this stage's own raw input values (not the upstream risk_prob_*
            # columns) — used by the frontend's What-If simulator to seed
            # slider baselines with the patient's actually recorded data
            "inputs": {f: patient_data[f] for f in feats},
            # which upstream stages' risk scores fed this prediction, and
            # what those scores were — the "evidence provenance" trail
            "upstream_evidence": {s: round(cumulative[f"risk_prob_{s}"], 4) for s in upstream_stages},
        })
        last_completed = stage

        if threshold is not None and not escalate:
            break  # gated: stop here, route to monitoring

    if last_completed is None:
        return {"error": "insufficient_data", "message": "Cognitive screening data is required."}

    final_probs = {c: round(float(p), 4) for c, p in zip(DIAGNOSIS_CLASSES, diagnosis_proba)}
    predicted_class = DIAGNOSIS_CLASSES[int(np.argmax(diagnosis_proba))]
    final_stage_result = stage_results[-1]
    final_risk = final_stage_result["risk_probability"]

    reached_pet = last_completed == "pet"
    if final_risk < 0.30:
        urgency = "low"
        recommendation = "Routine monitoring; re-screen in 12 months."
    elif final_risk < 0.55:
        urgency = "moderate"
        recommendation = f"Elevated risk signal at {last_completed.capitalize()} stage; re-screen in 6 months or escalate sooner if symptoms progress."
    elif final_risk < 0.75:
        urgency = "high"
        recommendation = "Refer to specialist for confirmatory workup." if not reached_pet else "Refer to specialist; imaging-confirmed elevated risk."
    else:
        urgency = "critical"
        recommendation = "Immediate specialist referral recommended."

    if final_stage_result["abstain"]:
        recommendation += (
            f" Note: prediction confidence at this stage is low (top two outcomes separated by only "
            f"{final_stage_result['confidence_margin']:.0%}) — clinical judgment should weigh more heavily "
            f"than the numeric score here."
        )

    missing_stages = [s for s in STAGE_ORDER if s not in [r["stage"] for r in stage_results]]

    total_cost_units = sum(s["cost_units"] for s in stage_results)
    max_cost_units = sum(STAGE_COST_UNITS.values())

    return {
        "stages_completed": [s["stage"] for s in stage_results],
        "missing_stages": missing_stages,
        "last_stage": last_completed,
        "reached_pet": reached_pet,
        "stage_results": stage_results,
        "final_class_probabilities": final_probs,
        "predicted_class": predicted_class,
        "final_risk_probability": final_risk,
        "final_confidence_margin": final_stage_result["confidence_margin"],
        "final_uncertainty": final_stage_result["uncertainty"],
        "abstained": final_stage_result["abstain"],
        "urgency": urgency,
        "recommendation": recommendation,
        "cost_units_used": total_cost_units,
        "cost_units_saved": max_cost_units - total_cost_units,
        "max_cost_units": max_cost_units,
    }
