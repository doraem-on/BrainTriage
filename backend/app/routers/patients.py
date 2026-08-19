from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user
from app.database import get_session
from app.models import Patient, AssessmentHistory, ClinicalDecision
from app.schemas import PatientCreate, PatientRead, StageSubmit, DecisionCreate
from app.ml.pipeline import run_pipeline
from app.ml.features import STAGE_ORDER

router = APIRouter(prefix="/api/patients", tags=["patients"], dependencies=[Depends(get_current_user)])

STAGE_DATA_FIELD = {
    "cognitive": "cognitive_data",
    "blood": "blood_data",
    "mri": "mri_data",
    "pet": "pet_data",
}


def _assembled_patient_data(patient: Patient) -> dict:
    merged: dict = {
        "age": patient.age,
        "education_years": patient.education_years,
        "sex_male": 1 if patient.sex == "male" else 0,
    }
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


@router.post("/{patient_id}/simulate")
def simulate(patient_id: int, overrides: dict, session: Session = Depends(get_session)):
    """What-if: recompute risk with feature overrides layered on top of the
    patient's real recorded data, WITHOUT persisting anything. Powers the
    interactive sliders on the patient detail page — lets a clinician see
    how the model's risk score would move if e.g. MMSE dropped by 3 points,
    without touching the patient's actual record or assessment history.
    """
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")

    data = _assembled_patient_data(patient)
    data.update(overrides)
    result = run_pipeline(data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{patient_id}/decision")
def record_decision(
    patient_id: int, payload: DecisionCreate,
    session: Session = Depends(get_session), username: str = Depends(get_current_user),
):
    """Human-in-the-loop: log whether the clinician accepted or overrode the
    AI's CURRENT recommendation for this patient. Required for override:
    a reason. This is what keeps the system decision-support rather than
    autonomous — every disposition is attributable to a person and a time.
    """
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")
    if not patient.last_result:
        raise HTTPException(status_code=400, detail="patient has not been evaluated yet")
    if payload.decision not in ("accept", "override"):
        raise HTTPException(status_code=400, detail="decision must be 'accept' or 'override'")
    if payload.decision == "override" and not payload.override_reason:
        raise HTTPException(status_code=400, detail="override_reason is required when overriding")

    decision = ClinicalDecision(
        patient_id=patient_id,
        decided_by=username,
        ai_recommendation=patient.last_result["recommendation"],
        ai_urgency=patient.last_result["urgency"],
        ai_risk_probability=patient.last_result["final_risk_probability"],
        decision=payload.decision,
        override_reason=payload.override_reason,
        override_note=payload.override_note,
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)
    return decision


@router.get("/{patient_id}/decisions")
def list_decisions(patient_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(ClinicalDecision)
        .where(ClinicalDecision.patient_id == patient_id)
        .order_by(ClinicalDecision.decided_at.desc())
    ).all()


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
    for d in session.exec(select(ClinicalDecision).where(ClinicalDecision.patient_id == patient_id)).all():
        session.delete(d)
    session.delete(patient)
    session.commit()
    return {"ok": True}
