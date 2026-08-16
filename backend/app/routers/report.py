import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from sqlmodel import Session

from app.database import get_session
from app.models import Patient
from app.ml.features import STAGE_LABELS

router = APIRouter(prefix="/api/patients", tags=["report"])

URGENCY_COLOR_HEX = {
    "critical": "#d03b3b",
    "high": "#ec835a",
    "moderate": "#fab219",
    "low": "#0ca30c",
}


@router.get("/{patient_id}/report")
def download_report(patient_id: int, session: Session = Depends(get_session)):
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")
    if not patient.last_result:
        raise HTTPException(status_code=400, detail="patient has not been evaluated yet")

    result = patient.last_result
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=10)
    body = styles["BodyText"]

    story = [
        Paragraph("BrainTriage — Diagnostic Pathway Summary", title_style),
        Paragraph(
            "Synthetic-data research demo. Not a validated clinical diagnostic device.",
            ParagraphStyle("note", parent=body, textColor=colors.HexColor("#898781"), fontSize=8),
        ),
        Spacer(1, 6 * mm),
        Paragraph(f"Patient: <b>{patient.name}</b> (ID: {patient.external_id})", body),
        Paragraph(f"Age: {patient.age}  |  Sex: {patient.sex}", body),
        Paragraph(f"Report generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body),
        Spacer(1, 6 * mm),
        Paragraph("Overall Assessment", h2),
        Paragraph(
            f"Predicted class: <b>{result['predicted_class']}</b>  |  "
            f"Final risk probability: <b>{result['final_risk_probability']:.0%}</b>  |  "
            f"Urgency: <font color='{URGENCY_COLOR_HEX.get(result['urgency'], '#000000')}'><b>{result['urgency'].upper()}</b></font>",
            body,
        ),
        Paragraph(f"Recommendation: {result['recommendation']}", body),
        Paragraph(
            f"Pipeline stopped after: {STAGE_LABELS.get(result['last_stage'], result['last_stage'])} "
            f"(reached PET: {'yes' if result['reached_pet'] else 'no'})",
            body,
        ),
        Paragraph(
            f"Diagnostic resource units used: {result['cost_units_used']} / {result['max_cost_units']} "
            f"({result['cost_units_saved']} units saved vs. running the full pipeline)",
            body,
        ),
        Spacer(1, 4 * mm),
        Paragraph("Stage-by-Stage Results", h2),
    ]

    table_data = [["Stage", "Risk Prob.", "P(CN)", "P(MCI)", "P(AD)", "Escalated?"]]
    for s in result["stage_results"]:
        cp = s["class_probabilities"]
        table_data.append([
            STAGE_LABELS.get(s["stage"], s["stage"]),
            f"{s['risk_probability']:.0%}",
            f"{cp.get('CN', 0):.0%}",
            f"{cp.get('MCI', 0):.0%}",
            f"{cp.get('AD', 0):.0%}",
            "—" if s["escalated"] is None else ("Yes" if s["escalated"] else "No"),
        ])
    t = Table(table_data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0efec")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c3c2b7")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fcfcfb")]),
    ]))
    story.append(t)

    last_stage_result = result["stage_results"][-1]
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        f"Top contributing factors at {STAGE_LABELS.get(last_stage_result['stage'])} stage",
        h2,
    ))
    contrib_data = [["Feature", "Value", "Direction of contribution"]]
    for c in last_stage_result["top_contributors"]:
        direction = "↑ increases risk" if c["contribution"] > 0 else "↓ decreases risk"
        contrib_data.append([c["label"], f"{c['value']:.2f}", direction])
    ct = Table(contrib_data, hAlign="LEFT")
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0efec")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c3c2b7")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(ct)

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="braintriage_{patient.external_id}.pdf"'},
    )
