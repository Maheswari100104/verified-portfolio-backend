from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OpportunityInterestResponse(BaseModel):
    id: int
    opportunity_id: int
    student_id: int

    # Student information
    student_name: Optional[str] = None
    email: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None

    # Student skills
    skills: list[str] = []

    # Public portfolio
    public_slug: Optional[str] = None

    # Interest information
    status: str
    ai_match_percentage: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)