from pydantic import BaseModel, ConfigDict
from typing import Optional


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

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    is_current: bool

    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )