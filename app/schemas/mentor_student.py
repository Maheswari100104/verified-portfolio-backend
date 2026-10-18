from pydantic import BaseModel, ConfigDict


# =========================================================
# Student → Mentor Request
# =========================================================

class MentorRequestCreate(BaseModel):
    mentor_id: int


# =========================================================
# Mentor–Student Response
# =========================================================

class MentorStudentResponse(BaseModel):
    id: int

    mentor_id: int
    student_id: int

    # Student information
    student_name: str | None = None
    student_email: str | None = None

    status: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )