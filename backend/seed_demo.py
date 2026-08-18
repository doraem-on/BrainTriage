"""Populates the local DB with demo patients drawn from the real OASIS
cohort, spanning the full urgency spectrum, so the dashboard/queue looks
alive on first run.

These are real (de-identified) OASIS research subjects, so we label them by
their original OASIS subject ID rather than inventing names — attaching a
fabricated identity to a real, anonymized research subject would misrepresent
who they are.

The Blood/CSF stage has no real measurement for OASIS subjects (it's a
different cohort — see docs/DATA_NOTE.md), so for demo purposes we borrow the
REAL CSF values from an actual patient in the CSF cohort with the SAME real
diagnosis, rather than synthesizing anything — every number in this demo
seed is a genuine measurement from a real research participant, just not
always the same participant across stages. Only PET, which has no real
dataset available at all, uses synthetic values (conditioned on the real
OASIS diagnosis), matching how the PET stage is trained.

Run from backend/: python seed_demo.py (requires `python fetch_real_data.py` first)
"""
import random

import pandas as pd
from sqlmodel import Session

from app.database import engine, init_db
from app.models import Patient
from app.ml.pipeline import run_pipeline
from app.real_data import load_real_cohort, load_csf_cohort
from app.synthetic_data import synthesize_pet
from datetime import datetime, timezone

N_DEMO = 15  # 5 per diagnosis class


def main():
    init_db()
    cohort = load_real_cohort()
    csf_cohort = load_csf_cohort()

    # sample across the diagnosis spectrum rather than randomly, so the
    # seeded queue actually spans low/moderate/high/critical urgency
    per_class = N_DEMO // 3
    picks = []
    for dx in ["CN", "MCI", "AD"]:
        subset = cohort[cohort["diagnosis"] == dx]
        picks.append(subset.sample(n=min(per_class, len(subset)), random_state=11))
    sample = pd.concat(picks).reset_index(drop=True)

    pet_synth = synthesize_pet(sample["diagnosis"], seed=11)

    with Session(engine) as session:
        for i, row in sample.iterrows():
            cognitive = {"mmse_score": row.mmse_score, "ses": row.ses}
            patient = Patient(
                external_id=f"OASIS-{row.subject_id}",
                name=f"Research Subject {row.subject_id}",
                age=row.age,
                sex="male" if row.sex_male == 1 else "female",
                education_years=row.education_years,
                cognitive_data=cognitive,
            )
            data = {
                "age": row.age, "education_years": row.education_years,
                "sex_male": row.sex_male, **cognitive,
            }

            # randomly let some patients have gone further in the pipeline already
            depth = random.choices([0, 1, 2, 3], weights=[0.3, 0.3, 0.25, 0.15])[0]
            if depth >= 1:
                # borrow a real CSF-cohort patient's real biomarkers, matched
                # by this subject's real diagnosis (see module docstring)
                match = csf_cohort[csf_cohort["diagnosis"] == row.diagnosis]
                if len(match):
                    donor = match.sample(n=1, random_state=i).iloc[0]
                    blood = {
                        "apoe4_positive": int(donor.apoe4_positive),
                        "csf_amyloid": float(donor.csf_amyloid),
                        "csf_ttau": float(donor.csf_ttau),
                        "csf_ptau": float(donor.csf_ptau),
                    }
                    patient.blood_data = blood
                    data.update(blood)
            if depth >= 2:
                mri = {"etiv": row.etiv, "nwbv": row.nwbv, "asf": row.asf}
                patient.mri_data = mri
                data.update(mri)
            if depth >= 3:
                pet = {
                    "amyloid_suvr": pet_synth.loc[i, "amyloid_suvr"],
                    "tau_suvr": pet_synth.loc[i, "tau_suvr"],
                    "fdg_suvr": pet_synth.loc[i, "fdg_suvr"],
                }
                patient.pet_data = pet
                data.update(pet)

            result = run_pipeline(data)
            patient.last_result = result
            patient.last_evaluated_at = datetime.now(timezone.utc)

            session.add(patient)
        session.commit()
    print(f"Seeded {len(sample)} demo patients from the real OASIS cohort.")


if __name__ == "__main__":
    main()
