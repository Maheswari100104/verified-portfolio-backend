from datetime import datetime

from pydantic import BaseModel, ConfigDict


# =========================================================
# Mentor Profile Base
# =========================================================

class MentorProfileBase(BaseModel):

    # -----------------------------------------------------
    # Basic Details
    # -----------------------------------------------------

    full_name: str

    phone: str | None = None

    # -----------------------------------------------------
    # Mentor Type
    # teacher / trainer
    # -----------------------------------------------------

    mentor_type: str = "teacher"

    # -----------------------------------------------------
    # Professional Details
    # -----------------------------------------------------

    institution: str | None = None

    institution_email: str | None = None

    department: str | None = None

    designation: str | None = None

    specialization: str | None = None

    location: str | None = None

    # -----------------------------------------------------
    # About
    # -----------------------------------------------------

    about: str | None = None


# =========================================================
# Create Mentor Profile
# =========================================================

class MentorProfileCreate(
    MentorProfileBase
):
    pass


# =========================================================
# Update Mentor Profile
# =========================================================

class MentorProfileUpdate(BaseModel):

    # -----------------------------------------------------
    # Basic Details
    # -----------------------------------------------------

    full_name: str | None = None

    phone: str | None = None

    # -----------------------------------------------------
    # Mentor Type
    # -----------------------------------------------------

    mentor_type: str | None = None

    # -----------------------------------------------------
    # Professional Details
    # -----------------------------------------------------

    institution: str | None = None

    institution_email: str | None = None

    department: str | None = None

    designation: str | None = None

    specialization: str | None = None

    location: str | None = None

    # -----------------------------------------------------
    # About
    # -----------------------------------------------------

    about: str | None = None


# =========================================================
# Mentor Profile Response
# =========================================================

class MentorProfileResponse(
    MentorProfileBase
):

    # -----------------------------------------------------
    # Primary Key
    # -----------------------------------------------------

    id: int

    # -----------------------------------------------------
    # User Relationship
    # -----------------------------------------------------

    user_id: int

    # =====================================================
    # Profile Photo Information
    # =====================================================

    profile_photo_name: str | None = None

    profile_photo_type: str | None = None

    profile_photo_size: int | None = None

    # =====================================================
    # Verification Document Information
    # =====================================================

    verification_document_name: str | None = None

    verification_document_type: str | None = None

    verification_document_size: int | None = None

    # =====================================================
    # Verification Status
    # =====================================================

    verification_status: str

    # =====================================================
    # OCR
    # =====================================================

    ocr_extracted_text: str | None = None

    # =====================================================
    # AI Verification
    # =====================================================

    ai_verification_score: float | None = None

    ai_verification_result: str | None = None

    ai_verified: bool

    # =====================================================
    # Final Verification
    # =====================================================

    verified_at: datetime | None = None

    verified_by: int | None = None

    # =====================================================
    # Timestamps
    # =====================================================

    created_at: datetime

    updated_at: datetime

    # =====================================================
    # SQLAlchemy → Pydantic
    # =====================================================

    model_config = ConfigDict(
        from_attributes=True
    )

    # =========================================================
# Mentor List Response
# =========================================================
#
# Used when students browse available mentors.
#
# =========================================================

class MentorListResponse(BaseModel):

    # -----------------------------------------------------
    # Mentor User ID
    # -----------------------------------------------------

    id: int

    # -----------------------------------------------------
    # Mentor Information
    # -----------------------------------------------------

    name: str

    email: str

    specialization: str | None = None

    designation: str | None = None

    institution: str | None = None

    department: str | None = None

    location: str | None = None

    mentor_type: str

    about: str | None = None

    # -----------------------------------------------------
    # Mentor Verification
    # -----------------------------------------------------

    verification_status: str

    ai_verified: bool

    model_config = ConfigDict(
        from_attributes=True
    )