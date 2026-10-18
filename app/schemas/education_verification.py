from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# EDUCATION VERIFICATION RESPONSE
# =========================================================

class EducationVerificationResponse(BaseModel):
    status: str

    message: Optional[str] = None

    checked_at: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# CREATE EDUCATION
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
# UPDATE EDUCATION
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
# EDUCATION RESPONSE
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

    # -------------------------------------------------------
    # Verification
    # -------------------------------------------------------

    verification: Optional[
        EducationVerificationResponse
    ] = None

    model_config = ConfigDict(
        from_attributes=True
    )