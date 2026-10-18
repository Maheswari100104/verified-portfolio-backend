from datetime import datetime

from pydantic import BaseModel, ConfigDict


# =========================================================
# Student → Create Endorsement Request
# =========================================================

class EndorsementCreate(BaseModel):
    mentor_id: int

    # skill or project
    item_type: str

    # ID of the skill/project
    item_id: int

    # Name displayed to mentor
    item_name: str

    # Optional message from student
    message: str | None = None


# =========================================================
# Mentor → Update Endorsement
# =========================================================

class EndorsementUpdate(BaseModel):
    # pending / endorsed / rejected
    status: str

    # Optional mentor comment
    mentor_comment: str | None = None


# =========================================================
# Student Information
# =========================================================

class EndorsementStudent(BaseModel):
    id: int
    name: str
    email: str
    headline: str


# =========================================================
# Endorsement Response
# =========================================================

class EndorsementResponse(BaseModel):
    id: int

    student_id: int
    mentor_id: int

    item_type: str
    item_id: int
    item_name: str

    message: str | None = None

    mentor_comment: str | None = None

    status: str

    is_endorsed: bool

    created_at: datetime
    updated_at: datetime

    student: EndorsementStudent

    model_config = ConfigDict(
        from_attributes=True
    )