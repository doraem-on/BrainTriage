"""Feature schemas for each diagnostic stage.

Three of four stages train on real, published research data:
  - Cognitive & MRI: the OASIS cross-sectional + longitudinal cohorts.
  - Blood/CSF: a real cerebrospinal-fluid biomarker cohort (Dakterzada et al.
    2023) — labeled "Blood" in the UI/cost model for pipeline-narrative
    consistency, but the real measurements are CSF (lumbar puncture), which
    is why its cost/invasiveness sits between a blood draw and an MRI.
  - PET: no real, freely-available PET SUVR tabular dataset exists (ADNI's
    requires a signed Data Use Agreement), so this stage remains synthetic.

See docs/DATA_NOTE.md for full provenance, citations, and licenses.

Each stage's classifier is trained with its own real features PLUS a fixed
set of upstream risk_prob_* columns (STAGE_UPSTREAM_INPUTS below) — NOT
simply "every prior stage" — because Cognitive+MRI live on one real cohort
(OASIS) and Blood/CSF lives on a different one (Dakterzada et al.), so a
stage can only stack on an upstream risk score if that upstream model can
legitimately be evaluated on (a subset of) this stage's own cohort. See
app/ml/train.py for exactly how each cross-cohort risk_prob is computed.
"""

STAGE_ORDER = ["cognitive", "blood", "mri", "pet"]

STAGE_LABELS = {
    "cognitive": "Cognitive Screening",
    "blood": "CSF Biomarkers (Lumbar Puncture)",
    "mri": "MRI Volumetrics",
    "pet": "PET Imaging",
}

# Approximate relative cost/invasiveness, used purely for UI + reporting.
STAGE_COST_UNITS = {
    "cognitive": 1,
    "blood": 6,   # CSF via lumbar puncture: more invasive than a routine blood draw
    "mri": 12,
    "pet": 40,
}

# Which upstream stages' risk_prob_* columns feed into each stage's model.
STAGE_UPSTREAM_INPUTS = {
    "cognitive": [],
    "blood": ["cognitive"],
    "mri": ["cognitive"],
    "pet": ["cognitive", "mri"],
}

# Whether the stage's training features/labels come from real data, and
# which real cohort — or "synthetic" if generated (conditioned on a real
# diagnosis label so the pipeline stays internally consistent, but not real
# measurements). Surfaced in the Model Card so nobody mistakes one for
# the other.
STAGE_DATA_SOURCE = {
    "cognitive": "real_oasis",
    "blood": "real_csf",
    "mri": "real_oasis",
    "pet": "synthetic",
}

COGNITIVE_FEATURES = [
    "age",
    "education_years",
    "ses",           # Hollingshead socioeconomic index, 1 (highest) - 5 (lowest)
    "sex_male",       # 0/1, derived from patient.sex
    "mmse_score",    # 0-30, lower = worse
]

BLOOD_FEATURES = [
    "apoe4_positive",   # 0/1, carries at least one APOE e4 allele
    "csf_amyloid",       # pg/mL, lower = more amyloid pathology
    "csf_ttau",           # pg/mL, higher = worse (total tau)
    "csf_ptau",           # pg/mL, higher = worse (phosphorylated tau)
]

MRI_FEATURES = [
    "etiv",   # estimated total intracranial volume, mm^3
    "nwbv",   # normalized whole brain volume, fraction of eTIV, lower = worse
    "asf",     # atlas scaling factor
]

PET_FEATURES = [
    "amyloid_suvr",   # SUVR, >1.1 typically considered amyloid-positive
    "tau_suvr",        # SUVR
    "fdg_suvr",         # SUVR, lower = worse (hypometabolism)
]

STAGE_FEATURES = {
    "cognitive": COGNITIVE_FEATURES,
    "blood": BLOOD_FEATURES,
    "mri": MRI_FEATURES,
    "pet": PET_FEATURES,
}

FEATURE_LABELS = {
    "age": "Age",
    "education_years": "Education (years)",
    "ses": "Socioeconomic Index (1=highest–5=lowest)",
    "sex_male": "Sex: Male",
    "mmse_score": "MMSE Score",
    "apoe4_positive": "APOE4 Positive",
    "csf_amyloid": "CSF Amyloid-β (pg/mL)",
    "csf_ttau": "CSF Total Tau (pg/mL)",
    "csf_ptau": "CSF Phosphorylated Tau (pg/mL)",
    "etiv": "Estimated Total Intracranial Volume (mm³)",
    "nwbv": "Normalized Whole Brain Volume",
    "asf": "Atlas Scaling Factor",
    "amyloid_suvr": "Amyloid PET SUVR",
    "tau_suvr": "Tau PET SUVR",
    "fdg_suvr": "FDG PET SUVR",
}

# Directionality: True means "higher value = higher AD risk"
FEATURE_HIGHER_IS_WORSE = {
    "age": True,
    "education_years": False,
    "ses": True,
    "sex_male": False,
    "mmse_score": False,
    "apoe4_positive": True,
    "csf_amyloid": False,
    "csf_ttau": True,
    "csf_ptau": True,
    "etiv": False,
    "nwbv": False,
    "asf": True,
    "amyloid_suvr": True,
    "tau_suvr": True,
    "fdg_suvr": False,
}

DIAGNOSIS_CLASSES = ["CN", "MCI", "AD"]  # Cognitively Normal / Mild Cognitive Impairment / Alzheimer's Disease

# Escalation thresholds on cumulative risk probability (P(MCI) + P(AD)) that
# gate advancement to the next, more expensive/invasive stage.
ESCALATION_THRESHOLDS = {
    "cognitive": 0.30,  # below this -> routine monitoring, skip CSF panel
    "blood": 0.45,        # below this -> monitor, skip MRI
    "mri": 0.60,           # below this -> monitor, skip PET
}

# Abstention: if the top two predicted classes are separated by less than
# this margin, the model's call is too close to trust at face value — flag
# it and escalate to the next stage regardless of whether the raw risk
# probability cleared ESCALATION_THRESHOLDS. This is what stops the pipeline
# from forcing a confident-looking recommendation out of a genuinely
# ambiguous case.
ABSTENTION_MARGIN = 0.15

# Which features are meaningful to run a counterfactual ("what if this had
# been X instead") against — clinical measurements, not fixed demographic/
# genetic attributes (age, sex, APOE4 genotype, SES, education aren't
# "what if" in the same sense).
COUNTERFACTUAL_ELIGIBLE = {
    "mmse_score", "csf_amyloid", "csf_ttau", "csf_ptau",
    "etiv", "nwbv", "asf", "amyloid_suvr", "tau_suvr", "fdg_suvr",
}

# Plausible clinical range per feature, used to bound the counterfactual
# search (and reused by the frontend What-If sliders via GET /api/meta/schema).
FEATURE_RANGES = {
    "age": (55, 95),
    "education_years": (0, 20),
    "ses": (1, 5),
    "sex_male": (0, 1),
    "mmse_score": (0, 30),
    "apoe4_positive": (0, 1),
    "csf_amyloid": (200, 1000),
    "csf_ttau": (100, 700),
    "csf_ptau": (20, 250),
    "etiv": (1100, 2100),
    "nwbv": (0.6, 0.85),
    "asf": (0.85, 1.6),
    "amyloid_suvr": (0.8, 2.2),
    "tau_suvr": (0.8, 2.6),
    "fdg_suvr": (0.85, 1.6),
}
