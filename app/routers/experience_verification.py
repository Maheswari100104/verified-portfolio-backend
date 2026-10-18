from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.experience import Experience
from app.models.experience_verification import ExperienceVerification

from app.schemas.experience_verification import (
    ExperienceVerificationCreate,
    ExperienceVerificationUpdate,
    ExperienceVerificationResponse,
)


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/experience-verification",
    tags=["Experience Verification"],
)


# =========================================================
# Helper
# Safely Convert Date → String
# =========================================================

def safe_date_to_string(value):
    """
    Convert a date/datetime value to a string safely.

    Handles:
    - None
    - date
    - datetime
    - string
    """

    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


# =========================================================
# Helper
# Build Complete Response
# =========================================================

def build_verification_response(
    verification: ExperienceVerification,
    db: Session,
):
    # =====================================================
    # Find Student
    # =====================================================

    student = (
        db.query(User)
        .filter(
            User.id == verification.student_id,
            User.role == "student",
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    # =====================================================
    # Find Student Profile
    # =====================================================

    profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == student.id
        )
        .first()
    )

    student_data = {
        "id": student.id,

        "name": (
            profile.full_name
            if profile and profile.full_name
            else "Student"
        ),

        "email": student.email,

        "headline": (
            profile.headline
            if profile and profile.headline
            else None
        ),
    }

    # =====================================================
    # Find Experience
    # =====================================================

    experience = (
        db.query(Experience)
        .filter(
            Experience.id == verification.experience_id
        )
        .first()
    )

    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found.",
        )

    # =====================================================
    # Experience Data
    # =====================================================

    experience_data = {
        "id": experience.id,

        "company": experience.company,

        "position": experience.position,

        "employment_type":
            experience.employment_type,

        "location":
            experience.location,

        "start_date":
            safe_date_to_string(
                experience.start_date
            ),

        "end_date":
            safe_date_to_string(
                experience.end_date
            ),

        "is_current":
            experience.is_current,

        "description":
            experience.description,
    }

    # =====================================================
    # Final Response
    # =====================================================

    return {
        "id": verification.id,

        "experience_id":
            verification.experience_id,

        "student_id":
            verification.student_id,

        "mentor_id":
            verification.mentor_id,

        "status":
            verification.status,

        "rating":
            verification.rating,

        "feedback":
            verification.feedback,

        "comment":
            verification.comment,

        "is_verified":
            verification.is_verified,

        "verified_at":
            verification.verified_at,

        "created_at":
            verification.created_at,

        "updated_at":
            verification.updated_at,

        "student":
            student_data,

        "experience":
            experience_data,
    }


# =========================================================
# Student → Request Experience Verification
# =========================================================

@router.post(
    "/request",
    response_model=ExperienceVerificationResponse,
)
def create_experience_verification_request(
    request: ExperienceVerificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Student Only
    # =====================================================

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only students can request "
                "experience verification."
            ),
        )

    # =====================================================
    # Find Experience
    # =====================================================

    experience = (
        db.query(Experience)
        .join(
            StudentProfile,
            Experience.student_profile_id
            == StudentProfile.id,
        )
        .filter(
            Experience.id == request.experience_id,
            StudentProfile.user_id == current_user.id,
        )
        .first()
    )

    if not experience:
        raise HTTPException(
            status_code=404,
            detail=(
                "Experience not found or "
                "does not belong to you."
            ),
        )

    # =====================================================
    # Validate Mentor
    #
    # IMPORTANT:
    # No MentorStudent connection is required.
    # The student can send the request directly to
    # any active IT Professional / Mentor.
    # =====================================================

    mentor = (
        db.query(User)
        .filter(
            User.id == request.mentor_id,
            User.role == "mentor",
            User.is_active == True,
        )
        .first()
    )

    if not mentor:
        raise HTTPException(
            status_code=404,
            detail=(
                "Selected IT professional / mentor "
                "was not found or is inactive."
            ),
        )

    # =====================================================
    # Prevent Student Selecting Themselves
    # =====================================================

    if mentor.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "You cannot select yourself "
                "as a mentor."
            ),
        )

    # =====================================================
    # Check Existing Pending Verification
    # =====================================================

    existing = (
        db.query(ExperienceVerification)
        .filter(
            ExperienceVerification.experience_id
            == experience.id,

            ExperienceVerification.student_id
            == current_user.id,

            ExperienceVerification.status
            == "pending",
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A verification request for "
                "this experience is already pending."
            ),
        )

    # =====================================================
    # Create Verification Request
    # =====================================================

    verification = ExperienceVerification(
        experience_id=experience.id,

        student_id=current_user.id,

        # Selected mentor
        mentor_id=mentor.id,

        status="pending",

        rating=None,

        feedback=None,

        comment=(
            request.comment.strip()
            if request.comment
            else None
        ),

        is_verified=False,

        verified_at=None,
    )

    db.add(verification)

    # =====================================================
    # Save
    # =====================================================

    try:
        db.commit()
        db.refresh(verification)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create experience "
                "verification request."
            ),
        )

    return build_verification_response(
        verification,
        db,
    )


# =========================================================
# Student → View My Experience Verification Requests
# =========================================================

@router.get(
    "/my-requests",
    response_model=list[
        ExperienceVerificationResponse
    ],
)
def get_my_experience_verification_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # Student Only
    # =====================================================

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only students can view "
                "their experience verification requests."
            ),
        )

    # =====================================================
    # Get Requests
    # =====================================================

    verifications = (
        db.query(ExperienceVerification)
        .filter(
            ExperienceVerification.student_id
            == current_user.id
        )
        .order_by(
            ExperienceVerification.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # Build Responses
    # =====================================================

    return [
        build_verification_response(
            verification,
            db,
        )
        for verification in verifications
    ]


# =========================================================
# IT Professional → View Verification Requests
# =========================================================

@router.get(
    "/requests",
    response_model=list[
        ExperienceVerificationResponse
    ],
)
def get_experience_verification_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # IT Professional / Mentor Only
    # =====================================================

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can view "
                "experience verification requests."
            ),
        )

    # =====================================================
    # Get Requests Assigned To This Mentor
    # =====================================================

    verifications = (
        db.query(ExperienceVerification)
        .filter(
            ExperienceVerification.mentor_id
            == current_user.id,

            ExperienceVerification.status
            == "pending",
        )
        .order_by(
            ExperienceVerification.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # Build Responses
    # =====================================================

    return [
        build_verification_response(
            verification,
            db,
        )
        for verification in verifications
    ]


# =========================================================
# IT Professional → View Single Verification
# =========================================================

@router.get(
    "/requests/{verification_id}",
    response_model=ExperienceVerificationResponse,
)
def get_experience_verification_request(
    verification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # IT Professional Only
    # =====================================================

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can view "
                "experience verification requests."
            ),
        )

    # =====================================================
    # Find Verification
    # =====================================================

    verification = (
        db.query(ExperienceVerification)
        .filter(
            ExperienceVerification.id
            == verification_id,

            ExperienceVerification.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail=(
                "Experience verification request "
                "not found."
            ),
        )

    return build_verification_response(
        verification,
        db,
    )


# =========================================================
# IT Professional → Verify / Reject
# =========================================================

@router.put(
    "/requests/{verification_id}",
    response_model=ExperienceVerificationResponse,
)
def update_experience_verification(
    verification_id: int,
    request: ExperienceVerificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # =====================================================
    # IT Professional Only
    # =====================================================

    if current_user.role != "mentor":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only IT professionals can process "
                "experience verification requests."
            ),
        )

    # =====================================================
    # Validate Status
    # =====================================================

    status = request.status.strip().lower()

    if status not in [
        "verified",
        "rejected",
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Status must be either "
                "'verified' or 'rejected'."
            ),
        )

    # =====================================================
    # Validate Rating
    # =====================================================

    if request.rating is not None:

        if request.rating < 1 or request.rating > 5:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Rating must be between "
                    "1 and 5."
                ),
            )

    # =====================================================
    # Find Verification
    # =====================================================

    verification = (
        db.query(ExperienceVerification)
        .filter(
            ExperienceVerification.id
            == verification_id,

            ExperienceVerification.mentor_id
            == current_user.id,
        )
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail=(
                "Experience verification request "
                "not found."
            ),
        )

    # =====================================================
    # Only Pending Can Be Processed
    # =====================================================

    if verification.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "This experience verification request "
                "has already been processed."
            ),
        )

    # =====================================================
    # Update Status
    # =====================================================

    verification.status = status

    # =====================================================
    # Verification Flag
    # =====================================================

    verification.is_verified = (
        status == "verified"
    )

    # =====================================================
    # Rating
    # =====================================================

    verification.rating = request.rating

    # =====================================================
    # Feedback
    # =====================================================

    if request.feedback:
        verification.feedback = (
            request.feedback.strip()
        )
    else:
        verification.feedback = None

    # =====================================================
    # Verified At
    # =====================================================

    if status == "verified":
        verification.verified_at = (
            datetime.now(timezone.utc)
        )
    else:
        verification.verified_at = None

    # =====================================================
    # Updated At
    # =====================================================

    verification.updated_at = (
        datetime.now(timezone.utc)
    )

    # =====================================================
    # Save
    # =====================================================

    try:
        db.commit()
        db.refresh(verification)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to update experience "
                "verification request."
            ),
        )

    return build_verification_response(
        verification,
        db,
    )