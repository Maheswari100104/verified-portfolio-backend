from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# Education Verification Response
# =========================================================

class EducationVerificationResponse(BaseModel):
    status: str

    message: Optional[str] = None

    checked_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# Education Create
# =========================================================

class EducationCreate(BaseModel):
    institution: str
    degree: str

    field_of_study: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    is_current: bool = False

    grade: Optional[str] = None
    description: Optional[str] = None


# =========================================================
# Education Update
# =========================================================

class EducationUpdate(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None

    field_of_study: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    is_current: Optional[bool] = None

    grade: Optional[str] = None
    description: Optional[str] = None


# =========================================================
# Education Response
# =========================================================

class EducationResponse(BaseModel):
    id: int
    student_profile_id: int

    institution: str
    degree: str

    field_of_study: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    is_current: bool

    grade: Optional[str] = None
    description: Optional[str] = None

    verification: Optional[
        EducationVerificationResponse
    ] = None

    model_config = ConfigDict(
        from_attributes=True
    )