from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OpportunityCreate(BaseModel):
    type: str
    title: str
    company: str

    company_website: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None

    location: Optional[str] = None
    work_mode: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[str] = None
    experience: Optional[str] = None
    eligibility: Optional[str] = None
    duration: Optional[str] = None
    deadline: Optional[datetime] = None


class OpportunityResponse(BaseModel):
    id: int
    professional_id: int
    type: str
    title: str
    company: str

    company_website: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None

    location: Optional[str] = None
    work_mode: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[str] = None
    experience: Optional[str] = None
    eligibility: Optional[str] = None
    duration: Optional[str] = None
    deadline: Optional[datetime] = None
    status: str
    created_at: datetime

    # Candidate's interest/shortlist status
    interest_status: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )