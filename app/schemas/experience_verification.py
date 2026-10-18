from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# Student → Request Experience Verification
# =========================================================

class ExperienceVerificationCreate(BaseModel):
    experience_id: int

    mentor_id: int
    # Optional message from student to IT Professional
    comment: Optional[str] = None


# =========================================================
# IT Professional → Update Verification
# =========================================================

class ExperienceVerificationUpdate(BaseModel):
    # pending / verified / rejected
    status: str

    # Optional rating from 1 to 5
    rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
    )

    # IT Professional feedback
    feedback: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# Experience Information
# =========================================================

class ExperienceVerificationExperience(BaseModel):
    id: int

    company: str
    position: str

    employment_type: Optional[str] = None
    location: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    is_current: bool = False

    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# Student Information
# =========================================================

class ExperienceVerificationStudent(BaseModel):
    id: int

    name: str
    email: str

    headline: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# Response
# =========================================================

class ExperienceVerificationResponse(BaseModel):
    id: int

    experience_id: int

    student_id: int

    mentor_id: Optional[int] = None

    status: str

    rating: Optional[int] = None

    feedback: Optional[str] = None

    comment: Optional[str] = None

    is_verified: bool

    verified_at: Optional[datetime] = None

    created_at: datetime

    updated_at: datetime

    student: Optional[
        ExperienceVerificationStudent
    ] = None

    experience: Optional[
        ExperienceVerificationExperience
    ] = None

    model_config = ConfigDict(
        from_attributes=True
    )