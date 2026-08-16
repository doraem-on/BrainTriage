"""Synthetic patient cohort generator.

Real ADNI/OASIS imaging & biomarker data require a signed Data Use Agreement
and cannot be fetched programmatically. To keep this pipeline fully runnable
end-to-end, we generate a synthetic cohort whose per-feature ranges and
inter-feature correlations are set to match the documented population
statistics from published ADNI/OASIS cohort papers (approximate, for
demo/dev purposes only — NOT derived from real subject records).

Swap this module for a real loader (see docs/DATA_NOTE.md) once your team has
ADNI/OASIS access; the rest of the pipeline (features.py, train.py, pipeline.py)
is written against the same column names and needs no changes.
"""
import numpy as np
import pandas as pd

from app.ml.features import DIAGNOSIS_CLASSES

RNG_SEED = 42


def _clip(arr, lo, hi):
    return np.clip(arr, lo, hi)


def generate_cohort(n_patients: int = 1500, seed: int = RNG_SEED) -> pd.DataFrame:
    """Generate a synthetic longitudinal-style cohort with a ground-truth
    diagnosis label and features across all four stages. Diagnosis prevalence
    roughly follows ADNI's enrolled-cohort mix (CN-heavy, enriched for MCI)."""
    rng = np.random.default_rng(seed)

    # 0=CN, 1=MCI, 2=AD roughly 40/40/20 (ADNI enrollment is MCI-enriched)
    dx = rng.choice([0, 1, 2], size=n_patients, p=[0.40, 0.40, 0.20])
    severity = dx + rng.normal(0, 0.35, n_patients)  # continuous latent severity
    severity = _clip(severity, -0.5, 2.8)

    age = _clip(rng.normal(73 + severity * 2.5, 6.5, n_patients), 55, 92)
    education_years = _clip(rng.normal(15 - severity * 0.4, 3, n_patients), 6, 20)
    apoe4_alleles = _clip(
        rng.binomial(2, _clip(0.12 + severity * 0.18, 0, 0.85)), 0, 2
    )
    family_history = (rng.random(n_patients) < _clip(0.15 + severity * 0.12, 0, 0.75)).astype(int)

    moca_score = _clip(rng.normal(28 - severity * 6.5, 2.2, n_patients), 0, 30)
    mmse_score = _clip(rng.normal(29 - severity * 5.0, 1.8, n_patients), 0, 30)
    cdr_global = np.select(
        [severity < 0.5, severity < 1.4, severity < 2.1],
        [0.0, 0.5, 1.0],
        default=2.0,
    )
    cdr_sob = _clip(rng.normal(severity * 3.2, 1.1, n_patients), 0, 18)
    memory_complaint = (rng.random(n_patients) < _clip(0.20 + severity * 0.28, 0, 0.95)).astype(int)

    abeta42_40_ratio = _clip(rng.normal(0.12 - severity * 0.025, 0.012, n_patients), 0.04, 0.16)
    p_tau181 = _clip(rng.normal(14 + severity * 14, 6, n_patients), 5, 90)
    nfl = _clip(rng.normal(22 + severity * 18, 9, n_patients), 8, 140)
    gfap = _clip(rng.normal(110 + severity * 60, 35, n_patients), 40, 400)

    hippocampal_volume = _clip(rng.normal(3900 - severity * 550, 300, n_patients), 2200, 4700)
    entorhinal_thickness = _clip(rng.normal(3.4 - severity * 0.45, 0.28, n_patients), 1.6, 4.2)
    whole_brain_volume = _clip(rng.normal(1050000 - severity * 55000, 55000, n_patients), 820000, 1200000)
    ventricular_volume = _clip(rng.normal(28000 + severity * 12000, 8000, n_patients), 8000, 90000)
    wmh_volume = _clip(rng.normal(3500 + severity * 3200, 2500, n_patients), 100, 30000)

    amyloid_suvr = _clip(rng.normal(1.05 + severity * 0.28, 0.12, n_patients), 0.85, 2.1)
    tau_suvr = _clip(rng.normal(1.05 + severity * 0.35, 0.15, n_patients), 0.8, 2.6)
    fdg_suvr = _clip(rng.normal(1.35 - severity * 0.16, 0.09, n_patients), 0.9, 1.6)

    df = pd.DataFrame({
        "age": age.round(1),
        "education_years": education_years.round(1),
        "moca_score": moca_score.round(0),
        "mmse_score": mmse_score.round(0),
        "cdr_global": cdr_global,
        "cdr_sob": cdr_sob.round(1),
        "family_history": family_history,
        "memory_complaint": memory_complaint,
        "apoe4_alleles": apoe4_alleles.astype(int),
        "abeta42_40_ratio": abeta42_40_ratio.round(4),
        "p_tau181": p_tau181.round(2),
        "nfl": nfl.round(2),
        "gfap": gfap.round(2),
        "hippocampal_volume": hippocampal_volume.round(0),
        "entorhinal_thickness": entorhinal_thickness.round(2),
        "whole_brain_volume": whole_brain_volume.round(0),
        "ventricular_volume": ventricular_volume.round(0),
        "wmh_volume": wmh_volume.round(0),
        "amyloid_suvr": amyloid_suvr.round(3),
        "tau_suvr": tau_suvr.round(3),
        "fdg_suvr": fdg_suvr.round(3),
        "diagnosis": [DIAGNOSIS_CLASSES[d] for d in dx],
    })
    return df


if __name__ == "__main__":
    cohort = generate_cohort()
    print(cohort.describe())
    print(cohort["diagnosis"].value_counts())
