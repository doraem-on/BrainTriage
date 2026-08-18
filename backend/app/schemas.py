from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CognitiveIntake(BaseModel):
    mmse_score: float = Field(ge=0, le=30)
    ses: float = Field(ge=1, le=5)


class PatientCreate(BaseModel):
    external_id: str
    name: str
    age: float
    sex: str = "unspecified"
    education_years: Optional[float] = None
    cognitive: CognitiveIntake


class PatientRead(BaseModel):
    id: int
    external_id: str
    name: str
    age: float
    sex: str
    education_years: Optional[float]
    created_at: datetime
    last_result: Optional[dict] = None
    last_evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StageSubmit(BaseModel):
    stage: str  # "blood" | "mri" | "pet"
    data: dict
