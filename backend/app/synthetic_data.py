"""Synthetic PET-imaging feature generator.

This is now the ONLY synthetic-data touchpoint left in the pipeline — the
Cognitive, MRI, and Blood/CSF stages all train on real published cohorts
(see app/real_data.py, docs/DATA_NOTE.md). Real ADNI PET SUVR data requires a
signed Data Use Agreement and no freely-available real PET SUVR tabular
dataset exists publicly, so this module fills in PET stage features
conditioned on each real (OASIS) patient's actual CDR-derived diagnosis, so
the synthetic values correlate with real disease severity rather than being
generated independently. Ranges/directionality follow published ADNI PET
literature (approximate, for demo purposes — NOT derived from real subjects).
"""
import numpy as np
import pandas as pd

from app.ml.features import DIAGNOSIS_CLASSES

RNG_SEED = 42
_DX_TO_INT = {c: i for i, c in enumerate(DIAGNOSIS_CLASSES)}


def _clip(arr, lo, hi):
    return np.clip(arr, lo, hi)


def synthesize_pet(diagnosis: pd.Series, seed: int = RNG_SEED) -> pd.DataFrame:
    """diagnosis: a Series of 'CN'/'MCI'/'AD' labels (e.g. from the real
    OASIS cohort). Returns a DataFrame (same index) of synthetic PET features
    whose severity tracks the given diagnosis.
    """
    rng = np.random.default_rng(seed)
    n = len(diagnosis)
    dx = diagnosis.map(_DX_TO_INT).values
    severity = _clip(dx + rng.normal(0, 0.35, n), -0.5, 2.8)

    amyloid_suvr = _clip(rng.normal(1.05 + severity * 0.28, 0.12, n), 0.85, 2.1)
    tau_suvr = _clip(rng.normal(1.05 + severity * 0.35, 0.15, n), 0.8, 2.6)
    fdg_suvr = _clip(rng.normal(1.35 - severity * 0.16, 0.09, n), 0.9, 1.6)

    return pd.DataFrame({
        "amyloid_suvr": amyloid_suvr.round(3),
        "tau_suvr": tau_suvr.round(3),
        "fdg_suvr": fdg_suvr.round(3),
    }, index=diagnosis.index)


if __name__ == "__main__":
    from app.real_data import load_real_cohort
    cohort = load_real_cohort()
    pet = synthesize_pet(cohort["diagnosis"])
    print(pd.concat([cohort[["diagnosis"]], pet], axis=1).groupby("diagnosis").mean())
