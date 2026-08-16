"""Feature schemas for each diagnostic stage.

Ranges and field names are modeled on the documented variable dictionaries
published by ADNI (adni.loni.usc.edu) and OASIS (oasis-brains.org) — e.g. MoCA/MMSE/CDR
scoring, ADNI blood biomarker panels (Amyloid-beta 42/40, p-tau181, NfL, GFAP),
FreeSurfer-derived MRI volumetrics, and Amyloid/FDG PET SUVR conventions.
This project does not ship real ADNI/OASIS subject data (both require a signed
Data Use Agreement); see docs/DATA_NOTE.md.
"""

STAGE_ORDER = ["cognitive", "blood", "mri", "pet"]

STAGE_LABELS = {
    "cognitive": "Cognitive Screening",
    "blood": "Blood Biomarkers",
    "mri": "MRI Volumetrics",
    "pet": "PET Imaging",
}

# Approximate relative cost/invasiveness, used purely for UI + reporting.
STAGE_COST_UNITS = {
    "cognitive": 1,
    "blood": 3,
    "mri": 12,
    "pet": 40,
}

COGNITIVE_FEATURES = [
    "age",
    "education_years",
    "moca_score",       # 0-30, lower = worse
    "mmse_score",        # 0-30, lower = worse
    "cdr_global",        # 0, 0.5, 1, 2, 3
    "cdr_sob",            # sum of boxes, 0-18
    "family_history",    # 0/1
    "memory_complaint",  # 0/1
]

BLOOD_FEATURES = [
    "apoe4_alleles",       # 0, 1, 2
    "abeta42_40_ratio",    # ~0.04-0.15, lower = more amyloid pathology
    "p_tau181",             # pg/mL, higher = worse
    "nfl",                   # pg/mL, higher = worse (neurodegeneration marker)
    "gfap",                  # pg/mL, higher = worse (astroglial marker)
]

MRI_FEATURES = [
    "hippocampal_volume",        # mm^3, ICV-normalized, lower = worse
    "entorhinal_thickness",      # mm, lower = worse
    "whole_brain_volume",        # mm^3, ICV-normalized, lower = worse
    "ventricular_volume",        # mm^3, higher = worse
    "wmh_volume",                  # mm^3, white-matter hyperintensity, higher = worse
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
    "moca_score": "MoCA Score",
    "mmse_score": "MMSE Score",
    "cdr_global": "CDR Global",
    "cdr_sob": "CDR Sum of Boxes",
    "family_history": "Family History of AD",
    "memory_complaint": "Subjective Memory Complaint",
    "apoe4_alleles": "APOE4 Allele Count",
    "abeta42_40_ratio": "Amyloid-β 42/40 Ratio",
    "p_tau181": "Plasma p-tau181 (pg/mL)",
    "nfl": "Neurofilament Light (pg/mL)",
    "gfap": "GFAP (pg/mL)",
    "hippocampal_volume": "Hippocampal Volume (mm³, norm.)",
    "entorhinal_thickness": "Entorhinal Cortex Thickness (mm)",
    "whole_brain_volume": "Whole Brain Volume (mm³, norm.)",
    "ventricular_volume": "Ventricular Volume (mm³)",
    "wmh_volume": "White Matter Hyperintensity Volume (mm³)",
    "amyloid_suvr": "Amyloid PET SUVR",
    "tau_suvr": "Tau PET SUVR",
    "fdg_suvr": "FDG PET SUVR",
}

# Directionality: True means "higher value = higher AD risk"
FEATURE_HIGHER_IS_WORSE = {
    "age": True,
    "education_years": False,
    "moca_score": False,
    "mmse_score": False,
    "cdr_global": True,
    "cdr_sob": True,
    "family_history": True,
    "memory_complaint": True,
    "apoe4_alleles": True,
    "abeta42_40_ratio": False,
    "p_tau181": True,
    "nfl": True,
    "gfap": True,
    "hippocampal_volume": False,
    "entorhinal_thickness": False,
    "whole_brain_volume": False,
    "ventricular_volume": True,
    "wmh_volume": True,
    "amyloid_suvr": True,
    "tau_suvr": True,
    "fdg_suvr": False,
}

DIAGNOSIS_CLASSES = ["CN", "MCI", "AD"]  # Cognitively Normal / Mild Cognitive Impairment / Alzheimer's Disease

# Escalation thresholds on cumulative risk probability (P(MCI) + P(AD)) that
# gate advancement to the next, more expensive/invasive stage.
ESCALATION_THRESHOLDS = {
    "cognitive": 0.30,  # below this -> routine monitoring, skip blood panel
    "blood": 0.45,        # below this -> monitor, skip MRI
    "mri": 0.60,           # below this -> monitor, skip PET
}
