from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# Skill Level
# =========================================================

SkillLevel = Literal[
    "Beginner",
    "Intermediate",
    "Advanced",
    "Expert",
]


# =========================================================
# Predefined Skill Response
# =========================================================

class SkillResponse(BaseModel):
    id: int
    name: str
    category: str

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# Student Skill Create
# =========================================================

class StudentSkillCreate(BaseModel):
    student_profile_id: int

    skill_id: Optional[int] = None

    custom_skill_name: Optional[str] = None

    level: SkillLevel = "Intermediate"


# =========================================================
# Student Skill Update
# =========================================================

class StudentSkillUpdate(BaseModel):
    level: Optional[SkillLevel] = None


# =========================================================
# Student Skill Response
# =========================================================

class StudentSkillResponse(BaseModel):
    id: int

    student_profile_id: int

    skill_id: Optional[int] = None

    custom_skill_name: Optional[str] = None

    level: SkillLevel

    model_config = ConfigDict(
        from_attributes=True
    )