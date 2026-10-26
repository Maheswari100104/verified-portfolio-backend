
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExperienceCreate(BaseModel):
    company: str
    position: str

    employment_type: Optional[str] = None
    location: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    is_current: bool = False

    description: Optional[str] = None


class ExperienceUpdate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None

    employment_type: Optional[str] = None
    location: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    is_current: Optional[bool] = None

    description: Optional[str] = None


class ExperienceResponse(BaseModel):
    id: int
    student_profile_id: int

    company: str
    position: str

    employment_type: Optional[str] = None
    location: Optional[str] = None

    # PostgreSQL DATE values are parsed as Python date objects.
    # Pydantic serializes them as YYYY-MM-DD strings in JSON.
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    is_current: bool

    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )
