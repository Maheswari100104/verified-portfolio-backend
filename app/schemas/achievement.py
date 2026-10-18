from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# Create Achievement
# =========================================================

class AchievementCreate(BaseModel):

    student_profile_id: int

    title: str

    organization: str

    achievement_date: Optional[str] = None

    category: Optional[str] = None

    description: Optional[str] = None

    certificate_url: Optional[str] = None


# =========================================================
# Update Achievement
# =========================================================

class AchievementUpdate(BaseModel):

    title: Optional[str] = None

    organization: Optional[str] = None

    achievement_date: Optional[str] = None

    category: Optional[str] = None

    description: Optional[str] = None

    certificate_url: Optional[str] = None


# =========================================================
# Achievement Response
# =========================================================

class AchievementResponse(BaseModel):

    id: int

    student_profile_id: int

    title: str

    organization: str

    achievement_date: Optional[str] = None

    category: Optional[str] = None

    description: Optional[str] = None

    certificate_url: Optional[str] = None

    # =====================================================
    # Uploaded Proof File
    # =====================================================

    certificate_file_name: Optional[str] = None

    certificate_file_type: Optional[str] = None

    certificate_file_size: Optional[int] = None

    certificate_file_url: Optional[str] = None

    # -----------------------------------------------------
    # SQLAlchemy → Pydantic
    # -----------------------------------------------------

    model_config = ConfigDict(
        from_attributes=True
    )