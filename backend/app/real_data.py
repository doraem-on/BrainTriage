"""Loads the real OASIS cohort used to train the Cognitive and MRI stage models.

Source: Kaggle dataset jboysen/mri-and-alzheimers (CC0-1.0), which republishes
tabular subject data from:

  OASIS-1 cross-sectional cohort:
    Marcus DS, Wang TH, Parker J, Csernansky JG, Morris JC, Buckner RL. (2007)
    Open Access Series of Imaging Studies (OASIS): Cross-Sectional MRI Data in
    Young, Middle Aged, Nondemented, and Demented Older Adults. Journal of
    Cognitive Neuroscience, 19, 1498-1507.

  OASIS-2 longitudinal cohort:
    Marcus DS, Fotenos AF, Csernansky JG, Morris JC, Buckner RL. (2010) Open
    Access Series of Imaging Studies: Longitudinal MRI Data in Nondemented and
    Demented Older Adults. Journal of Cognitive Neuroscience, 22, 2677-2684.

CDR (Clinical Dementia Rating) is used only to DERIVE the diagnosis label
(CDR 0 -> CN, CDR 0.5 -> MCI, CDR >= 1 -> AD) and is deliberately NOT included
as an input feature — including it would let the model trivially look up the
label it's supposed to predict.

The two CSVs ship in app/data/ (tiny, CC0-licensed) so this loader has no
runtime dependency on Kaggle credentials.
"""
import os

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EXTERNAL_DATA_DIR = os.path.join(os.path.dirname(__file__), "data_external")


def _cdr_to_diagnosis(cdr: float) -> str:
    if cdr == 0:
        return "CN"
    if cdr == 0.5:
        return "MCI"
    return "AD"


def load_real_cohort() -> pd.DataFrame:
    """Returns a DataFrame with columns: subject_id, age, education_years,
    ses, sex_male, mmse_score, etiv, nwbv, asf, diagnosis.
    One row per (subject, visit) — the longitudinal file contributes one row
    per visit for the same subject, so downstream splitting must group by
    subject_id to avoid leaking a subject's later visit into the test set.
    """
    cross = pd.read_csv(os.path.join(DATA_DIR, "oasis_cross-sectional.csv"))
    cross = cross.rename(columns={
        "ID": "subject_id", "Educ": "education_years", "SES": "ses",
        "MMSE": "mmse_score", "CDR": "cdr", "eTIV": "etiv", "nWBV": "nwbv", "ASF": "asf",
    })
    cross["sex_male"] = (cross["M/F"] == "M").astype(int)
    cross = cross.dropna(subset=["cdr", "mmse_score", "education_years"])

    long = pd.read_csv(os.path.join(DATA_DIR, "oasis_longitudinal.csv"))
    long = long.rename(columns={
        "Subject ID": "subject_id", "EDUC": "education_years", "SES": "ses",
        "MMSE": "mmse_score", "CDR": "cdr", "eTIV": "etiv", "nWBV": "nwbv", "ASF": "asf",
    })
    long["sex_male"] = (long["M/F"] == "M").astype(int)
    long = long.dropna(subset=["cdr", "mmse_score", "education_years"])

    cols = ["subject_id", "Age", "education_years", "ses", "sex_male", "mmse_score", "etiv", "nwbv", "asf", "cdr"]
    df = pd.concat([cross[cols], long[cols]], ignore_index=True)
    df = df.rename(columns={"Age": "age"})

    # SES (Hollingshead index) has some residual missingness even after the
    # essential-column dropna above; impute with the cohort median.
    df["ses"] = df["ses"].fillna(df["ses"].median())

    df["diagnosis"] = df["cdr"].apply(_cdr_to_diagnosis)
    df = df.drop(columns=["cdr"])

    return df.reset_index(drop=True)


def load_csf_cohort() -> pd.DataFrame:
    """Real CSF (lumbar puncture) biomarker cohort used for the Blood stage.

    Source: Dakterzada F, Jove M, Huerto R, Carnes A, Sol J, Pamplona R,
    Pinol-Ripoll G. (2023) Changes in Plasma Neutral and Ether-Linked Lipids
    Are Associated with The Pathology and Progression of Alzheimer's Disease.
    Aging and Disease, 14(5), 1728. DOI: 10.34810/data614 (CC BY-NC-ND per
    the dataset's own license statement — see docs/DATA_NOTE.md). Not
    committed to the repo; run `python fetch_real_data.py` first.

    Returns a DataFrame with columns: age, sex_male, mmse_score,
    apoe4_positive, csf_amyloid, csf_ttau, csf_ptau, diagnosis.
    """
    path = os.path.join(EXTERNAL_DATA_DIR, "csf_biomarkers.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run `python fetch_real_data.py` from backend/ "
            "first (requires a Kaggle API token at ~/.kaggle/kaggle.json)."
        )
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Age": "age", "MMSE": "mmse_score", "Diagnostic": "diagnosis",
        "CSF Amyloid (pg/mL)": "csf_amyloid", "CSF Total tau (pg/mL)": "csf_ttau",
        "CSF Phosphorylated tau (pg/mL)": "csf_ptau",
    })
    df["sex_male"] = (df["Sex"] == "Male").astype(int)
    df["apoe4_positive"] = (df["APOE4"] == "Yes").astype(int)
    df["diagnosis"] = df["diagnosis"].map({
        "Control": "CN", "Mild Cognitive Impairment": "MCI", "Alzheimer's Disease": "AD",
    })

    cols = ["age", "sex_male", "mmse_score", "apoe4_positive", "csf_amyloid", "csf_ttau", "csf_ptau", "diagnosis"]
    df = df.dropna(subset=["csf_amyloid", "csf_ttau", "csf_ptau", "apoe4_positive", "diagnosis"])
    return df[cols].reset_index(drop=True)


if __name__ == "__main__":
    d = load_real_cohort()
    print("OASIS:", d.shape)
    print(d["diagnosis"].value_counts())

    c = load_csf_cohort()
    print("\nCSF:", c.shape)
    print(c["diagnosis"].value_counts())
