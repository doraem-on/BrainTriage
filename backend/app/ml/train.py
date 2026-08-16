"""Trains one classifier per diagnostic stage.

Each stage's model is a stacked classifier: it sees that stage's own features
PLUS the risk probabilities output by all upstream stages (cumulative
evidence), mirroring how a clinician updates their belief as new tests come
in. Models are small gradient-boosted trees so shap.TreeExplainer is exact
and fast (needed for the per-patient explainability panel).
"""
import json
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score

from app.ml.features import STAGE_ORDER, STAGE_FEATURES, DIAGNOSIS_CLASSES
from app.synthetic_data import generate_cohort

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")


def _cumulative_columns(stage: str) -> list[str]:
    idx = STAGE_ORDER.index(stage)
    return [f"risk_prob_{s}" for s in STAGE_ORDER[:idx]]


def train_all(n_patients: int = 1500, seed: int = 42) -> dict:
    os.makedirs(MODEL_DIR, exist_ok=True)
    df = generate_cohort(n_patients=n_patients, seed=seed)
    y = df["diagnosis"].map({c: i for i, c in enumerate(DIAGNOSIS_CLASSES)}).values

    train_idx, test_idx = train_test_split(
        np.arange(len(df)), test_size=0.25, random_state=seed, stratify=y
    )

    metrics = {}
    risk_prob_frame = df.copy()

    for stage in STAGE_ORDER:
        feature_cols = STAGE_FEATURES[stage] + _cumulative_columns(stage)
        X = risk_prob_frame[feature_cols].values.astype(float)

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # RandomForest (not GradientBoosting): shap.TreeExplainer only supports
        # multiclass output for a subset of tree models, RandomForest included.
        clf = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=seed
        )
        clf.fit(X_train, y_train)

        proba_test = clf.predict_proba(X_test)
        preds = clf.predict(X_test)
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average="macro")
        try:
            auc = roc_auc_score(y_test, proba_test, multi_class="ovr")
        except ValueError:
            auc = float("nan")

        metrics[stage] = {
            "accuracy": round(float(acc), 4),
            "macro_f1": round(float(f1), 4),
            "roc_auc_ovr": round(float(auc), 4) if auc == auc else None,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "features": feature_cols,
        }

        joblib.dump(clf, os.path.join(MODEL_DIR, f"{stage}_model.joblib"))

        # produce this stage's risk_prob (P(MCI)+P(AD)) for the FULL frame,
        # to feed as an input feature to the next stage
        full_proba = clf.predict_proba(risk_prob_frame[feature_cols].values.astype(float))
        risk_prob_frame[f"risk_prob_{stage}"] = full_proba[:, 1] + full_proba[:, 2]

    # background reference sets for SHAP (small sample for speed)
    bg = df.sample(n=min(200, len(df)), random_state=seed)
    bg_path = os.path.join(MODEL_DIR, "background.joblib")
    joblib.dump({"background": risk_prob_frame.loc[bg.index]}, bg_path)

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    joblib.dump(df, os.path.join(MODEL_DIR, "reference_cohort.joblib"))

    return metrics


if __name__ == "__main__":
    m = train_all()
    print(json.dumps(m, indent=2))
