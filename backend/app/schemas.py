from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CognitiveIntake(BaseModel):
    moca_score: float = Field(ge=0, le=30)
    mmse_score: float = Field(ge=0, le=30)
    cdr_global: float
    cdr_sob: float = Field(ge=0, le=18)
    family_history: int = Field(ge=0, le=1)
    memory_complaint: int = Field(ge=0, le=1)


class BloodIntake(BaseModel):
    apoe4_alleles: int = Field(ge=0, le=2)
    abeta42_40_ratio: float
    p_tau181: float
    nfl: float
    gfap: float


class MriIntake(BaseModel):
    hippocampal_volume: float
    entorhinal_thickness: float
    whole_brain_volume: float
    ventricular_volume: float
    wmh_volume: float


class PetIntake(BaseModel):
    amyloid_suvr: float
    tau_suvr: float
    fdg_suvr: float


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
