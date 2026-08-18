from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Patient
from app.ml.features import STAGE_COST_UNITS, STAGE_ORDER, STAGE_LABELS

router = APIRouter(prefix="/api/queue", tags=["queue"])

URGENCY_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


def _next_stage(last_stage: str) -> str | None:
    idx = STAGE_ORDER.index(last_stage)
    return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else None


@router.get("")
def get_priority_queue(session: Session = Depends(get_session)):
    patients = session.exec(select(Patient)).all()
    rows = []
    for p in patients:
        r = p.last_result or {}
        rows.append({
            "id": p.id,
            "external_id": p.external_id,
            "name": p.name,
            "age": p.age,
            "urgency": r.get("urgency", "unassessed"),
            "final_risk_probability": r.get("final_risk_probability"),
            "predicted_class": r.get("predicted_class"),
            "last_stage": r.get("last_stage"),
            "recommendation": r.get("recommendation"),
            "last_evaluated_at": p.last_evaluated_at,
        })
    rows.sort(key=lambda row: (
        URGENCY_ORDER.get(row["urgency"], 99),
        -(row["final_risk_probability"] or 0),
    ))
    return rows


@router.get("/stats")
def get_queue_stats(session: Session = Depends(get_session)):
    patients = session.exec(select(Patient)).all()
    total = len(patients)
    by_urgency = {"critical": 0, "high": 0, "moderate": 0, "low": 0, "unassessed": 0}
    total_cost_used = 0
    total_cost_max = 0
    stage_reach = {"cognitive": 0, "blood": 0, "mri": 0, "pet": 0}

    for p in patients:
        r = p.last_result or {}
        urgency = r.get("urgency", "unassessed")
        by_urgency[urgency] = by_urgency.get(urgency, 0) + 1
        total_cost_used += r.get("cost_units_used", 0)
        total_cost_max += r.get("max_cost_units", sum(STAGE_COST_UNITS.values()))
        last_stage = r.get("last_stage")
        if last_stage in stage_reach:
            stage_reach[last_stage] += 1

    savings_pct = (
        round(100 * (total_cost_max - total_cost_used) / total_cost_max, 1)
        if total_cost_max else 0
    )

    return {
        "total_patients": total,
        "by_urgency": by_urgency,
        "stage_reach": stage_reach,
        "cost_units_used": total_cost_used,
        "cost_units_if_all_full_pipeline": total_cost_max,
        "estimated_resource_savings_pct": savings_pct,
    }


@router.get("/optimize")
def optimize_resources(
    blood_slots: int = 0, mri_slots: int = 0, pet_slots: int = 0,
    session: Session = Depends(get_session),
):
    """Diagnostic resource optimizer: given a limited number of slots for
    the next-tier test this week, rank the patients actually awaiting that
    stage by risk and return who gets a slot vs. who's waitlisted. This is
    the operational-research counterpart to the per-patient escalation
    logic — it answers "we only have N MRI slots this week, who should get
    them?" rather than just "should this one patient escalate?".
    """
    slots_by_stage = {"blood": blood_slots, "mri": mri_slots, "pet": pet_slots}
    patients = session.exec(select(Patient)).all()

    waiting = {"blood": [], "mri": [], "pet": []}
    for p in patients:
        r = p.last_result or {}
        last_stage = r.get("last_stage")
        stage_results = r.get("stage_results") or []
        if not last_stage or not stage_results:
            continue
        escalated = stage_results[-1].get("escalated")
        if not escalated:
            continue
        nxt = _next_stage(last_stage)
        if nxt in waiting:
            waiting[nxt].append({
                "id": p.id,
                "external_id": p.external_id,
                "name": p.name,
                "risk_probability": r.get("final_risk_probability"),
                "urgency": r.get("urgency"),
                "waiting_since": p.last_evaluated_at,
            })

    result = {}
    for stage, candidates in waiting.items():
        candidates.sort(key=lambda c: -(c["risk_probability"] or 0))
        slots = slots_by_stage[stage]
        result[stage] = {
            "stage_label": STAGE_LABELS[stage],
            "slots_available": slots,
            "candidates_waiting": len(candidates),
            "scheduled": candidates[:slots] if slots > 0 else [],
            "waitlisted": candidates[slots:] if slots > 0 else candidates,
        }
    return result
