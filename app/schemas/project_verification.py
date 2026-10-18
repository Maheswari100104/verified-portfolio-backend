from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# Student → Submit Project for Verification
# =========================================================

class ProjectVerificationCreate(BaseModel):
    project_id: int

    # Mentor selected by the student
    mentor_id: int

    # Optional message from student to mentor
    comment: str | None = None


# =========================================================
# Mentor → Verify / Reject Project
# =========================================================

class ProjectVerificationUpdate(BaseModel):
    # Mentor can either verify or reject
    status: Literal["verified", "rejected"]

    # Mentor rating for this specific project
    # 1 = Very Poor
    # 2 = Needs Improvement
    # 3 = Average
    # 4 = Good
    # 5 = Excellent
    rating: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    # Mentor's written feedback
    feedback: str | None = None

    # Optional comment/update
    comment: str | None = None


# =========================================================
# Student Information
# =========================================================

class VerificationStudentInfo(BaseModel):
    id: int

    name: str

    email: str

    headline: str = ""


# =========================================================
# Project Information
# =========================================================

class VerificationProjectInfo(BaseModel):
    id: int

    title: str

    # Description can be empty/null in the database
    description: str | None = None

    technologies: list[str] = Field(
        default_factory=list
    )

    github: str | None = None

    live_demo: str | None = None

    image: str | None = None

    start_date: str | None = None

    end_date: str | None = None

    is_current: bool = False


# =========================================================
# Project Verification Response
# =========================================================

class ProjectVerificationResponse(BaseModel):
    id: int

    project_id: int

    student_id: int

    mentor_id: int | None = None

    status: str

    # =====================================================
    # Mentor Rating
    # =====================================================

    rating: int | None = None

    # =====================================================
    # Mentor Feedback
    # =====================================================

    feedback: str | None = None

    # =====================================================
    # Student's Message to Mentor
    # =====================================================

    comment: str | None = None

    is_verified: bool

    verified_at: datetime | None = None

    created_at: datetime

    updated_at: datetime

    # -----------------------------------------------------
    # Student
    # -----------------------------------------------------

    student: VerificationStudentInfo

    # -----------------------------------------------------
    # Project
    # -----------------------------------------------------

    project: VerificationProjectInfo

    model_config = ConfigDict(
        from_attributes=True
    )