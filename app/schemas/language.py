from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# Create Language
# =========================================================

class LanguageCreate(BaseModel):

    student_profile_id: int

    language: str

    proficiency: str


# =========================================================
# Update Language
# =========================================================

class LanguageUpdate(BaseModel):

    language: Optional[str] = None

    proficiency: Optional[str] = None


# =========================================================
# Language Response
# =========================================================

class LanguageResponse(BaseModel):

    id: int

    student_profile_id: int

    language: str

    proficiency: str

    # SQLAlchemy → Pydantic
    model_config = ConfigDict(
        from_attributes=True
    )