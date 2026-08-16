"""Populates the local DB with a handful of demo patients spanning the full
urgency spectrum, so the dashboard/queue looks alive on first run.
Run from backend/: python seed_demo.py
"""
import random

from sqlmodel import Session

from app.database import engine, init_db
from app.models import Patient
from app.ml.pipeline import run_pipeline
from app.synthetic_data import generate_cohort
from datetime import datetime, timezone

DEMO_NAMES = [
    "Asha Verma", "Ram Bihari Singh", "Meena Kumari", "Deepak Oraon",
    "Sunita Devi", "Prakash Chandra Toppo", "Lalita Mahato", "Suresh Munda",
    "Kiran Bala", "Anil Kumar Sahu", "Geeta Rani", "Ravi Shankar Prasad",
]


def main():
    init_db()
    cohort = generate_cohort(n_patients=len(DEMO_NAMES), seed=7)

    with Session(engine) as session:
        for i, (name, row) in enumerate(zip(DEMO_NAMES, cohort.itertuples())):
            cognitive = {
                "moca_score": row.moca_score, "mmse_score": row.mmse_score,
                "cdr_global": row.cdr_global, "cdr_sob": row.cdr_sob,
                "family_history": row.family_history, "memory_complaint": row.memory_complaint,
            }
            patient = Patient(
                external_id=f"DEMO-{1000 + i}",
                name=name,
                age=row.age,
                sex=random.choice(["female", "male"]),
                education_years=row.education_years,
                cognitive_data=cognitive,
            )
            data = {"age": row.age, "education_years": row.education_years, **cognitive}

            # randomly let some patients have gone further in the pipeline already
            depth = random.choices([0, 1, 2, 3], weights=[0.3, 0.3, 0.25, 0.15])[0]
            if depth >= 1:
                blood = {
                    "apoe4_alleles": row.apoe4_alleles, "abeta42_40_ratio": row.abeta42_40_ratio,
                    "p_tau181": row.p_tau181, "nfl": row.nfl, "gfap": row.gfap,
                }
                patient.blood_data = blood
                data.update(blood)
            if depth >= 2:
                mri = {
                    "hippocampal_volume": row.hippocampal_volume,
                    "entorhinal_thickness": row.entorhinal_thickness,
                    "whole_brain_volume": row.whole_brain_volume,
                    "ventricular_volume": row.ventricular_volume,
                    "wmh_volume": row.wmh_volume,
                }
                patient.mri_data = mri
                data.update(mri)
            if depth >= 3:
                pet = {
                    "amyloid_suvr": row.amyloid_suvr, "tau_suvr": row.tau_suvr, "fdg_suvr": row.fdg_suvr,
                }
                patient.pet_data = pet
                data.update(pet)

            result = run_pipeline(data)
            patient.last_result = result
            patient.last_evaluated_at = datetime.now(timezone.utc)

            session.add(patient)
        session.commit()
    print(f"Seeded {len(DEMO_NAMES)} demo patients.")


if __name__ == "__main__":
    main()
