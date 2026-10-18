from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# Create / Update Student Profile
# =========================================================

class StudentProfileCreate(BaseModel):
    # -----------------------------------------------------
    # Email belongs to the User table.
    #
    # It is included here because the Personal Information
    # form also allows the student to update their email.
    # -----------------------------------------------------

    email: Optional[str] = None

    # -----------------------------------------------------
    # Basic Personal Information
    # -----------------------------------------------------

    full_name: str

    phone: Optional[str] = None

    location: Optional[str] = None

    headline: Optional[str] = None

    # -----------------------------------------------------
    # Social Links
    # -----------------------------------------------------

    linkedin: Optional[str] = None

    github: Optional[str] = None

    website: Optional[str] = None

    # -----------------------------------------------------
    # About
    # -----------------------------------------------------

    about: Optional[str] = None


# =========================================================
# Student Profile Response
# =========================================================

class StudentProfileResponse(BaseModel):
    # -----------------------------------------------------
    # Profile Identification
    # -----------------------------------------------------

    id: int

    user_id: int

    # -----------------------------------------------------
    # Basic Personal Information
    # -----------------------------------------------------

    full_name: str

    phone: Optional[str] = None

    location: Optional[str] = None

    headline: Optional[str] = None

    # -----------------------------------------------------
    # Social Links
    # -----------------------------------------------------

    linkedin: Optional[str] = None

    github: Optional[str] = None

    website: Optional[str] = None

    # -----------------------------------------------------
    # About
    # -----------------------------------------------------

    about: Optional[str] = None

    # -----------------------------------------------------
    # Profile Photo Information
    # -----------------------------------------------------

    profile_photo_name: Optional[str] = None

    profile_photo_type: Optional[str] = None

    profile_photo_size: Optional[int] = None

    # -----------------------------------------------------
    # Profile Photo URL
    # -----------------------------------------------------

    profile_photo_url: Optional[str] = None

    # -----------------------------------------------------
    # Allow SQLAlchemy model → Pydantic conversion
    # -----------------------------------------------------

    model_config = ConfigDict(
        from_attributes=True
    )