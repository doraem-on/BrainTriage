from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, JSON, Column


class Patient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)  # clinician-facing MRN-style ID
    name: str
    age: float
    sex: str = "unspecified"
    education_years: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # raw intake data per stage, kept as JSON so we don't need a wide table
    cognitive_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    blood_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    mri_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    pet_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # latest pipeline output, cached so the dashboard/queue doesn't recompute on every list call
    last_result: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    last_evaluated_at: Optional[datetime] = None


class AssessmentHistory(SQLModel, table=True):
    """One row per pipeline run, so we can chart risk trajectory over time."""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient.id", index=True)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_stage: str
    final_risk_probability: float
    predicted_class: str
    urgency: str
    result: dict = Field(sa_column=Column(JSON))
