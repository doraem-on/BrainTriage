from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Patient, AssessmentHistory
from app.schemas import PatientCreate, PatientRead, StageSubmit
from app.ml.pipeline import run_pipeline
from app.ml.features import STAGE_ORDER

router = APIRouter(prefix="/api/patients", tags=["patients"])

STAGE_DATA_FIELD = {
    "cognitive": "cognitive_data",
    "blood": "blood_data",
    "mri": "mri_data",
    "pet": "pet_data",
}


def _assembled_patient_data(patient: Patient) -> dict:
    merged: dict = {"age": patient.age, "education_years": patient.education_years}
    for stage in STAGE_ORDER:
        d = getattr(patient, STAGE_DATA_FIELD[stage])
        if d:
            merged.update(d)
    return merged


def _evaluate_and_store(patient: Patient, session: Session) -> dict:
    data = _assembled_patient_data(patient)
    result = run_pipeline(data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["message"])

    patient.last_result = result
    patient.last_evaluated_at = datetime.now(timezone.utc)
    session.add(patient)

    history = AssessmentHistory(
        patient_id=patient.id,
        last_stage=result["last_stage"],
        final_risk_probability=result["final_risk_probability"],
        predicted_class=result["predicted_class"],
        urgency=result["urgency"],
        result=result,
    )
    session.add(history)
    session.commit()
    session.refresh(patient)
    return result


@router.post("", response_model=PatientRead)
def create_patient(payload: PatientCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Patient).where(Patient.external_id == payload.external_id)).first()
    if existing:
        raise HTTPException(status_code=409, detail="external_id already exists")

    patient = Patient(
        external_id=payload.external_id,
        name=payload.name,
        age=payload.age,
        sex=payload.sex,
        education_years=payload.education_years,
        cognitive_data=payload.cognitive.model_dump(),
    )
    session.add(patient)
    session.commit()
    session.refresh(patient)

    _evaluate_and_store(patient, session)
    session.refresh(patient)
    return patient


@router.get("", response_model=list[PatientRead])
def list_patients(session: Session = Depends(get_session)):
    return session.exec(select(Patient).order_by(Patient.created_at.desc())).all()


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, session: Session = Depends(get_session)):
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")
    return patient


@router.post("/{patient_id}/stage", response_model=PatientRead)
def submit_stage(patient_id: int, payload: StageSubmit, session: Session = Depends(get_session)):
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")
    if payload.stage not in STAGE_DATA_FIELD or payload.stage == "cognitive":
        raise HTTPException(status_code=400, detail="stage must be one of: blood, mri, pet")

    setattr(patient, STAGE_DATA_FIELD[payload.stage], payload.data)
    session.add(patient)
    session.commit()
    session.refresh(patient)

    _evaluate_and_store(patient, session)
    session.refresh(patient)
    return patient


@router.get("/{patient_id}/history")
def get_history(patient_id: int, session: Session = Depends(get_session)):
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")
    rows = session.exec(
        select(AssessmentHistory)
        .where(AssessmentHistory.patient_id == patient_id)
        .order_by(AssessmentHistory.evaluated_at)
    ).all()
    return [
        {
            "evaluated_at": r.evaluated_at,
            "last_stage": r.last_stage,
            "final_risk_probability": r.final_risk_probability,
            "predicted_class": r.predicted_class,
            "urgency": r.urgency,
        }
        for r in rows
    ]


@router.delete("/{patient_id}")
def delete_patient(patient_id: int, session: Session = Depends(get_session)):
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")
    for r in session.exec(select(AssessmentHistory).where(AssessmentHistory.patient_id == patient_id)).all():
        session.delete(r)
    session.delete(patient)
    session.commit()
    return {"ok": True}
