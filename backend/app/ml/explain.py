"""Per-patient explainability using exact SHAP values for the tree models."""
import os

import joblib
import numpy as np
import shap

from app.ml.features import FEATURE_LABELS, DIAGNOSIS_CLASSES

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

_explainer_cache: dict[str, shap.TreeExplainer] = {}
_model_cache: dict[str, object] = {}


def _load_model(stage: str):
    if stage not in _model_cache:
        _model_cache[stage] = joblib.load(os.path.join(MODEL_DIR, f"{stage}_model.joblib"))
    return _model_cache[stage]


def _load_explainer(stage: str):
    if stage not in _explainer_cache:
        clf = _load_model(stage)
        _explainer_cache[stage] = shap.TreeExplainer(clf)
    return _explainer_cache[stage]


def explain_prediction(stage: str, feature_cols: list[str], x_row: np.ndarray) -> list[dict]:
    """Returns a ranked list of {feature, label, contribution, value} for the
    'AD-leaning' direction, i.e. summed SHAP contribution toward MCI+AD classes.
    """
    explainer = _load_explainer(stage)
    shap_values = explainer.shap_values(x_row.reshape(1, -1))

    # shap_values shape handling: list per class (older API) or ndarray (n, features, classes)
    if isinstance(shap_values, list):
        # sum contribution toward class 1 (MCI) and class 2 (AD)
        contrib = np.array(shap_values[1][0]) + np.array(shap_values[2][0])
    else:
        arr = np.asarray(shap_values)
        if arr.ndim == 3:
            contrib = arr[0, :, 1] + arr[0, :, 2]
        else:
            contrib = arr[0]

    items = []
    for i, col in enumerate(feature_cols):
        label = FEATURE_LABELS.get(col, col.replace("risk_prob_", "Prior stage risk: ").replace("_", " "))
        items.append({
            "feature": col,
            "label": label,
            "value": float(x_row[i]),
            "contribution": float(contrib[i]),
        })
    items.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    return items
