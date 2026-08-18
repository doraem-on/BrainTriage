"""Trains one classifier per diagnostic stage.

Cognitive, MRI, and Blood/CSF stages train on REAL published cohorts —
Cognitive & MRI on OASIS (app/real_data.load_real_cohort), Blood/CSF on a
separate real biomarker cohort (app/real_data.load_csf_cohort). PET has no
freely-available real SUVR dataset, so it stays synthetic, conditioned on
each OASIS patient's real diagnosis (app/synthetic_data.synthesize_pet).

Because Cognitive/MRI and Blood/CSF are two DIFFERENT real cohorts (no
shared subjects), a stage can only stack on an upstream risk_prob column if
that upstream model can actually be evaluated on this stage's cohort — see
STAGE_UPSTREAM_INPUTS in features.py. Concretely: the Cognitive model is
evaluated on the CSF cohort's real age/sex/MMSE (SES & education, which the
CSF study didn't collect, are imputed with the OASIS training median — the
only imputation in the pipeline, and it's disclosed here + in the Model
Card). The MRI and PET stages stay entirely within the OASIS cohort, so
their upstream risk_prob_cognitive is self-consistent with no imputation.

Each stage's classifier is a RandomForest (shap.TreeExplainer needs a tree
model that supports exact multiclass explanations). OASIS-based stages use a
train/test split grouped by subject_id, since the longitudinal file
contributes multiple visits per subject.
"""
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score

from app.ml.features import (
    STAGE_FEATURES, DIAGNOSIS_CLASSES, STAGE_DATA_SOURCE, STAGE_UPSTREAM_INPUTS,
)
from app.real_data import load_real_cohort, load_csf_cohort
from app.synthetic_data import synthesize_pet

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

DX_TO_INT = {c: i for i, c in enumerate(DIAGNOSIS_CLASSES)}


def _upstream_cols(stage: str) -> list[str]:
    return [f"risk_prob_{s}" for s in STAGE_UPSTREAM_INPUTS[stage]]


def _fit_stage(X_train, y_train, seed: int) -> RandomForestClassifier:
    clf = RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=seed
    )
    clf.fit(X_train, y_train)
    return clf


def _eval_stage(stage: str, clf, X_test, y_test, feature_cols, n_train) -> dict:
    proba_test = clf.predict_proba(X_test)
    preds = clf.predict(X_test)
    try:
        auc = roc_auc_score(y_test, proba_test, multi_class="ovr")
    except ValueError:
        auc = float("nan")
    return {
        "data_source": STAGE_DATA_SOURCE[stage],
        "accuracy": round(float(accuracy_score(y_test, preds)), 4),
        "macro_f1": round(float(f1_score(y_test, preds, average="macro")), 4),
        "roc_auc_ovr": round(float(auc), 4) if auc == auc else None,
        "n_train": int(n_train),
        "n_test": int(len(y_test)),
        "features": feature_cols,
    }


def train_all(seed: int = 42) -> dict:
    os.makedirs(MODEL_DIR, exist_ok=True)
    metrics = {}

    # ---- OASIS cohort: Cognitive, MRI, PET all live here ----
    oasis = load_real_cohort()
    y_oasis = oasis["diagnosis"].map(DX_TO_INT).values
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    tr_idx, te_idx = next(splitter.split(oasis, y_oasis, groups=oasis["subject_id"]))

    # Cognitive (no upstream inputs)
    cog_cols = STAGE_FEATURES["cognitive"] + _upstream_cols("cognitive")
    X = oasis[cog_cols].values.astype(float)
    clf_cognitive = _fit_stage(X[tr_idx], y_oasis[tr_idx], seed)
    metrics["cognitive"] = _eval_stage("cognitive", clf_cognitive, X[te_idx], y_oasis[te_idx], cog_cols, len(tr_idx))
    joblib.dump(clf_cognitive, os.path.join(MODEL_DIR, "cognitive_model.joblib"))
    oasis["risk_prob_cognitive"] = _risk_prob(clf_cognitive, X)

    # MRI (stacks on risk_prob_cognitive, self-consistent within OASIS)
    mri_cols = STAGE_FEATURES["mri"] + _upstream_cols("mri")
    X = oasis[mri_cols].values.astype(float)
    clf_mri = _fit_stage(X[tr_idx], y_oasis[tr_idx], seed)
    metrics["mri"] = _eval_stage("mri", clf_mri, X[te_idx], y_oasis[te_idx], mri_cols, len(tr_idx))
    joblib.dump(clf_mri, os.path.join(MODEL_DIR, "mri_model.joblib"))
    oasis["risk_prob_mri"] = _risk_prob(clf_mri, X)

    # PET (synthetic features conditioned on real OASIS diagnosis; stacks on
    # risk_prob_cognitive + risk_prob_mri, both self-consistent within OASIS)
    pet_synth = synthesize_pet(oasis["diagnosis"], seed=seed)
    oasis = oasis.join(pet_synth)
    pet_cols = STAGE_FEATURES["pet"] + _upstream_cols("pet")
    X = oasis[pet_cols].values.astype(float)
    clf_pet = _fit_stage(X[tr_idx], y_oasis[tr_idx], seed)
    metrics["pet"] = _eval_stage("pet", clf_pet, X[te_idx], y_oasis[te_idx], pet_cols, len(tr_idx))
    joblib.dump(clf_pet, os.path.join(MODEL_DIR, "pet_model.joblib"))

    # ---- CSF cohort: Blood/CSF stage lives here (different real patients) ----
    csf = load_csf_cohort()
    y_csf = csf["diagnosis"].map(DX_TO_INT).values

    # cross-cohort feature: evaluate the OASIS-trained cognitive model on the
    # CSF cohort's real age/sex/mmse. SES and education_years weren't
    # collected in the CSF study, so they're imputed with the OASIS
    # training-set median — the only imputation in the whole pipeline.
    ses_median = oasis.loc[tr_idx, "ses"].median()
    educ_median = oasis.loc[tr_idx, "education_years"].median()
    csf_cog_input = pd.DataFrame({
        "age": csf["age"],
        "education_years": educ_median,
        "ses": ses_median,
        "sex_male": csf["sex_male"],
        "mmse_score": csf["mmse_score"],
    })[cog_cols].values.astype(float)
    csf["risk_prob_cognitive"] = _risk_prob(clf_cognitive, csf_cog_input)

    blood_cols = STAGE_FEATURES["blood"] + _upstream_cols("blood")
    X = csf[blood_cols].values.astype(float)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_csf, test_size=0.25, random_state=seed, stratify=y_csf
    )
    clf_blood = _fit_stage(X_train, y_train, seed)
    metrics["blood"] = _eval_stage("blood", clf_blood, X_test, y_test, blood_cols, len(X_train))
    joblib.dump(clf_blood, os.path.join(MODEL_DIR, "blood_model.joblib"))

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def _risk_prob(clf, X):
    proba = clf.predict_proba(X)
    return proba[:, 1] + proba[:, 2]  # P(MCI) + P(AD)


if __name__ == "__main__":
    m = train_all()
    print(json.dumps(m, indent=2))
